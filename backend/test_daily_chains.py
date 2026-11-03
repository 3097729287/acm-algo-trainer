"""Daily claim progression, real review evidence and learning-only duration."""
import datetime as dt
import json
import unittest
import uuid

import test_training as fixtures
from daily_chains import threshold
from training import ServiceError, TrainingService, iso
from usage import record, learning_seconds, snapshot as usage_snapshot


class DailyChainTests(unittest.TestCase):
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown
    accept=fixtures.ServiceTests.accept

    def tasks(self):return self.service.daily_tasks(goal_tasks=[])
    def lane(self,lane):return next(task for task in self.tasks()['tasks'] if task['lane']==lane)

    def study(self,minutes,learning=True):
        session=str(uuid.uuid4())
        for sequence in range(1,minutes+1):
            self.clock.advance(seconds=60)
            record(self.service,{'sessionId':session,'sequence':sequence,'seconds':60,'learning':learning})

    def test_ac_thresholds_advance_only_on_claim_and_duplicate_claim_does_not_skip(self):
        self.assertEqual([threshold(step) for step in range(12)],[1,2,3,5,10,20,30,50,100,200,300,500])
        first=self.lane('ac')
        with self.assertRaises(ServiceError):self.service.claim_daily_task(first['id'])
        for letter in 'ABCDE':self.accept('fixture::'+letter)
        self.accept('fixture::A')
        for target in (1,2,3,5):
            current=self.lane('ac');self.assertEqual(current['target'],target)
            self.assertTrue(current['completed'])
            claimed=self.service.claim_daily_task(current['id'])
            self.assertGreater(claimed['awardedXp'],0)
            again=self.service.claim_daily_task(current['id'])
            self.assertEqual(again['awardedXp'],0)
            self.assertEqual(again['dailyTasks']['tasks'][0]['id'],claimed['dailyTasks']['tasks'][0]['id'])
        self.assertEqual((self.lane('ac')['target'],self.lane('ac')['progress']),(10,5))

    def test_learning_requires_learning_heartbeats_and_ignores_duplicates_and_overlaps(self):
        task=self.lane('learning');day=self.tasks()['date']
        self.study(5,learning=False)
        self.assertEqual((self.lane('learning')['progress'],learning_seconds(self.service,day)),(0,0))
        self.study(5)
        self.assertEqual(self.lane('learning')['progress'],5)
        body={'sessionId':str(uuid.uuid4()),'sequence':1,'seconds':60,'learning':True}
        record(self.service,body);record(self.service,body)
        self.assertEqual(learning_seconds(self.service,day),300)
        self.service.claim_daily_task(task['id'])
        self.assertEqual((self.lane('learning')['target'],self.lane('learning')['progress']),(15,5))
        self.assertEqual(usage_snapshot(self.service)['totalSeconds'],600)

    def test_review_stops_at_actual_daily_plan_then_becomes_fresh_random_task(self):
        for letter in 'AB':
            self.accept('fixture::'+letter,verdict='WA');self.accept('fixture::'+letter)
        self.clock.advance(days=1)
        self.assertEqual(self.tasks()['reviewLimit'],2)
        self.assertEqual(self.lane('review')['target'],1)
        for letter,target in [('A',1),('B',2)]:
            plan=self.service.review_plan()
            task=next(item for item in plan['tasks'] if item['problemId']=='fixture::'+letter)
            self.service.problem(task['problemId'],review_id=task['id'])
            self.clock.advance(minutes=1)
            self.accept(task['problemId'],review_id=task['id'])
            current=self.lane('review')
            self.assertEqual((current['target'],current['progress']),(target,target))
            self.service.claim_daily_task(current['id'])
        value=self.tasks()
        self.assertEqual(value['reviewLimit'],2)
        self.assertEqual(value['tasks'][1]['lane'],'review-random')
        self.assertFalse(value['tasks'][1]['completed'],'a new random task must not reuse old events')
        self.assertEqual(len(value['tasks']),6)

    def test_no_review_day_starts_random_lane_and_lower_tasks_settle(self):
        value=self.tasks()
        self.assertEqual(value['reviewLimit'],0)
        self.assertEqual(value['tasks'][1]['lane'],'review-random')
        original=[task['id'] for task in value['tasks'][3:]]
        for letter in 'ABCDEFGH':self.accept('fixture::'+letter)
        for task in self.tasks()['tasks'][3:]:
            if task['completed']:
                self.service.claim_daily_task(task['id'])
        current=self.tasks()
        self.assertEqual([task['id'] for task in current['tasks'][3:]],original)
        for task in current['tasks'][3:]:
            row=self.service.connection.execute('SELECT claimed_at FROM daily_missions WHERE day=? AND id=?',(current['date'],task['id'])).fetchone()
            self.assertEqual(task['claimed'],bool(row['claimed_at']))

    def review_day(self, letters='ABCDE'):
        from goals import Goals
        Goals(self.service).save({'title':'隔离复习预算','kind':'custom','deadline':'2027-01-01',
                                 'dailyMinutes':720,'totalProblems':5,'currentRating':1000,'targetRating':2000})
        for letter in letters:
            self.accept('fixture::'+letter,verdict='WA');self.accept('fixture::'+letter)
        self.clock.advance(days=1)
        self.assertEqual(self.tasks()['reviewLimit'],len(letters))

    def finish_review(self, letter):
        task=next(item for item in self.service.review_plan()['tasks'] if item['problemId']=='fixture::'+letter)
        self.service.problem(task['problemId'],review_id=task['id']);self.clock.advance(minutes=1)
        self.accept(task['problemId'],review_id=task['id'])

    def test_cancelled_pending_review_lowers_daily_target_keeps_passes_and_restores_on_undo(self):
        self.review_day()
        for letter in 'ABC':
            self.finish_review(letter);self.service.claim_daily_task(self.lane('review')['id'])
        self.finish_review('D')
        self.assertEqual((self.lane('review')['progress'],self.lane('review')['target']),(4,5))
        before=list(self.service.connection.execute('SELECT * FROM submissions ORDER BY id'))
        reward=self.service.insights()['growth']['missionXp']
        cancelled=self.service.remove_training('fixture::E')['cancelledReviewId']
        self.assertEqual((self.lane('review')['progress'],self.lane('review')['target']),(4,4))
        self.assertTrue(self.lane('review')['completed'])
        self.service.remove_training('fixture::E')
        self.assertEqual(self.tasks()['reviewLimit'],4,'Repeated cancellation only removes one pending problem')
        self.assertEqual(self.service.insights()['growth']['missionXp'],reward)
        self.assertEqual(list(self.service.connection.execute('SELECT * FROM submissions ORDER BY id')),before)
        self.service.start_training('fixture::E',restore_review_id=cancelled)
        self.assertEqual((self.lane('review')['progress'],self.lane('review')['target']),(4,5))
        self.service.remove_training('fixture::E')
        identity=self.lane('review')['id'];claim=self.service.claim_daily_task(identity)
        self.assertGreater(claim['awardedXp'],0)
        self.assertEqual(self.service.claim_daily_task(identity)['awardedXp'],0)
        self.assertEqual(self.tasks()['reviewCompleted'],4)

    def test_bulk_clear_reduces_only_pending_daily_reviews_without_erasing_completed_evidence(self):
        self.review_day('ABC');self.finish_review('A')
        self.service.clear_training(['fixture::B','fixture::C'])
        current=self.tasks()
        self.assertEqual((current['reviewLimit'],current['reviewCompleted']),(1,1))
        self.assertEqual((self.lane('review')['progress'],self.lane('review')['target']),(1,1))
        self.service.clear_training(['fixture::A'])
        self.assertEqual((self.tasks()['reviewLimit'],self.tasks()['reviewCompleted']),(1,1))

    def test_cancel_every_pending_review_starts_random_lane_without_fake_review_completion(self):
        self.review_day('AB')
        for letter in 'AB':self.service.remove_training('fixture::'+letter)
        current=self.tasks()
        self.assertEqual((current['reviewLimit'],current['reviewCompleted']),(0,0))
        self.assertEqual(current['tasks'][1]['lane'],'review-random')
        self.assertFalse(current['tasks'][1]['completed'])
        self.assertNotIn('rewardSticker',current['tasks'][1])

    def test_cancelled_daily_limit_survives_restart_and_claimed_rewards_are_unchanged(self):
        self.review_day('AB');self.finish_review('A')
        identity=self.lane('review')['id'];self.service.claim_daily_task(identity);reward=self.service.insights()['growth']['missionXp']
        self.service.remove_training('fixture::B')
        self.assertEqual(self.tasks()['reviewLimit'],1)
        self.service.close();self.service=TrainingService(self.library,self.db,self.assets,self.judge,self.clock,self.root/'backups')
        self.assertEqual((self.tasks()['reviewLimit'],self.tasks()['reviewCompleted']),(1,1))
        self.assertEqual(self.service.insights()['growth']['missionXp'],reward)
        self.assertEqual(self.service.claim_daily_task(identity)['awardedXp'],0)

    def test_restart_and_midnight_keep_old_rewards_and_reset_only_daily_counters(self):
        self.accept();task=self.lane('ac')
        self.service.claim_daily_task(task['id'])
        value=self.tasks();self.assertEqual(value['tasks'][0]['target'],2)
        before=self.service.insights()['growth']['missionXp']
        self.service.close()
        self.service=TrainingService(self.library,self.db,self.assets,self.judge,self.clock,self.root/'backups')
        self.assertEqual(self.lane('ac')['target'],2)
        self.clock.advance(days=1)
        self.assertEqual((self.lane('ac')['target'],self.lane('ac')['progress']),(1,0))
        self.assertEqual(self.service.insights()['growth']['missionXp'],before)
        with self.assertRaises(ServiceError):self.service.claim_daily_task(task['id'],value['date'])

    def test_legacy_claimed_ac_tier_is_retained_without_being_paid_again(self):
        day=self.tasks()['date']
        with self.service._write() as db:
            db.execute('INSERT INTO daily_missions(day,id,definition,claimed_at,awarded_xp) VALUES(?,?,?,?,?)',
                (day,'solve-3',json.dumps({'id':'solve-3','version':2,'kind':'solve','target':3,'xp':60}),iso(self.clock()),60))
        self.assertEqual(self.lane('ac')['target'],5)
        self.assertEqual(self.service.insights()['growth']['missionXp'],60)

    def test_learning_midnight_attributes_each_part_to_its_beijing_date(self):
        self.clock.value=dt.datetime(2026,10,8,16,0,20,tzinfo=dt.timezone.utc)
        record(self.service,{'sessionId':str(uuid.uuid4()),'sequence':1,'seconds':60,'learning':True})
        self.assertEqual(learning_seconds(self.service,'2026-10-08'),40)
        self.assertEqual(learning_seconds(self.service,'2026-10-09'),20)


    def test_exactly_one_fixed_daily_reward_is_a_sticker_and_the_other_two_keep_xp(self):
        fixed=[task for task in self.tasks()['tasks'] if task['lane']=='fixed']
        self.assertEqual(len(fixed),3)
        stickers=[task for task in fixed if task.get('rewardSticker')]
        self.assertEqual(len(stickers),1)
        self.assertEqual(stickers[0]['xp'],0)
        self.assertTrue(all(task['xp']>0 for task in fixed if not task.get('rewardSticker')))
        self.assertEqual(stickers[0]['id'],next(task['id'] for task in self.tasks()['tasks'] if task['lane']=='fixed' and task.get('rewardSticker')))
        self.accept();self.service.claim_daily_task(self.lane('ac')['id'])
        self.assertEqual(self.service.connection.execute("SELECT COUNT(*) FROM account_preferences WHERE key LIKE 'sticker-eligible:%'").fetchone()[0],0)

    def test_issued_fixed_tasks_do_not_move_when_level_unlocks_more_content(self):
        from unittest.mock import patch
        with patch.object(self.service,'navigation',return_value={'level':1}):
            before=[task for task in self.tasks()['tasks'] if task['lane']=='fixed']
            self.assertTrue(all(task['kind']!='platforms' for task in before))
        with patch.object(self.service,'navigation',return_value={'level':6}):
            after=[task for task in self.tasks()['tasks'] if task['lane']=='fixed']
        self.assertEqual(before,after)

    def test_real_review_completion_issues_at_most_two_sticker_followups_per_day(self):
        from unittest.mock import patch
        with patch('daily_chains.CHALLENGES',[]),patch('daily_chains.EXPLORATIONS',[]):
            self.accept(verdict='WA');self.clock.advance(days=1)
            task=next(iter(self.service.review_plan()['tasks']))
            self.service.problem('fixture::A',review_id=task['id'])
            self.service.record_official({'id':'fixture::A','url':self.assets.problem('fixture::A')['url'],'code':'fresh rewrite','reviewId':task['id']},
                {'status':'finished','verdict':'AC','submissionId':str(fixtures._next_official_id()),'acceptedAt':iso(self.clock())})
            self.service.claim_daily_task(self.lane('review')['id'])
            for slot in ('review-0','review-1'):
                followup=self.lane('review-random')
                self.assertEqual(followup['stickerSlot'],slot)
                self.assertEqual(followup['xp'],0)
                self.study(followup['target']+1)
                self.assertTrue(self.lane('review-random')['completed'])
                self.service.claim_daily_task(followup['id'])
            third=self.lane('review-random')
            self.assertNotIn('rewardSticker',third)
            self.assertGreater(third['xp'],0)
            rows=[json.loads(row[0]) for row in self.service.connection.execute("SELECT definition FROM daily_missions WHERE day=?",(self.tasks()['date'],))]
            self.assertEqual(sum(row.get('stickerSlot','').startswith('review-') for row in rows),2)


if __name__=='__main__':unittest.main()
