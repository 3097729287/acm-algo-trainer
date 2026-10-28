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


if __name__=='__main__':unittest.main()
