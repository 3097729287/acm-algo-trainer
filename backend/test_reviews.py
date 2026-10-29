"""Official receipts, isolated draft contexts, adaptive intervals and daily load."""
import datetime as dt
import json
import unittest
from unittest.mock import patch

import test_training as fixtures
from training import TrainingService, ServiceError, iso, UTC
from reviews import ReviewScheduler, interval_after_pass, reward_totals


class ReviewTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    tearDown = fixtures.ServiceTests.tearDown

    def receipt(self, identity='fixture::A', verdict='AC', review_id=None, **extra):
        accepted_at = extra.pop('acceptedAt', iso(self.clock()))
        return self.service.record_official({'id': identity, 'url': self.assets.problem(identity)['url'],
            'code': 'independent rewrite', **({'reviewId': review_id} if review_id else {}), **extra},
            {'status':'finished', 'verdict':verdict, 'submissionId':str(fixtures._next_official_id()), 'acceptedAt':accepted_at})

    def due(self, identity='fixture::A'):
        return next(r for r in self.service.workspace()['reviews']['tasks'] if r['problemId'] == identity)

    def seed(self, identity='fixture::A'):
        self.receipt(identity, verdict='WA')
        self.clock.advance(seconds=1)
        return self.receipt(identity)

    def open(self, identity='fixture::A'):
        task = self.due(identity)
        self.service.problem(identity, review_id=task['id'])
        return task

    def state(self, identity='fixture::A'):
        return next(json.loads(r[0]) for r in self.service.connection.execute("SELECT value FROM account_preferences WHERE key LIKE 'review-state:%'") if json.loads(r[0])['key'] == identity)

    def test_clean_basic_language_pass_preserves_draft_and_receipt_without_a_review(self):
        row=self.library.rows[0]
        row['url']='https://www.luogu.com.cn/problem/P1001'
        self.assertNotIn('reviewTrivial',row)
        problem=dict(self.assets.problem(row['id']),url=row['url'])
        with patch.object(self.assets,'problem',return_value=problem):
            receipt=self.receipt()
        self.service.save_draft(row['id'],'saved accepted code')
        self.clock.advance(days=7)
        self.assertEqual(self.service.review_plan()['tasks'],[])
        self.assertEqual(self.service.problem(row['id'])['draft'],'saved accepted code')
        self.assertEqual(self.service.connection.execute('SELECT code FROM submissions WHERE id=?',(receipt['id'],)).fetchone()[0],'independent rewrite')

    def test_first_review_uses_next_beijing_day_not_fixed_week_or_24_hours(self):
        self.clock.value = dt.datetime(2026,10,8,15,58,tzinfo=UTC)
        self.seed()
        self.assertEqual(self.service.review_plan()['tasks'], [])
        self.clock.advance(minutes=3)
        self.assertEqual(self.due()['due'], '2026-10-09')
        self.assertEqual(self.service.start_training('fixture::A')['reviewTask']['id'], self.due()['id'])

    def test_basic_language_exercise_with_a_real_wa_is_also_reviewed(self):
        row=self.library.rows[0]
        row['url']='https://www.luogu.com.cn/problem/P1001'
        problem=dict(self.assets.problem(row['id']),url=row['url'])
        with patch.object(self.assets,'problem',return_value=problem):self.seed()
        self.clock.advance(days=1)
        self.assertEqual(self.due()['problemId'],row['id'])

    def test_review_code_is_separate_across_rounds_languages_and_restart(self):
        self.service.save_draft('fixture::A', 'yesterday complete code', language='python3')
        original = self.seed()
        self.clock.advance(days=1)
        task = self.open()
        fresh = self.service.problem('fixture::A', review_id=task['id'])
        self.assertEqual((fresh['draft'], fresh['draftSavedAt'], fresh['submissions']), ('',None,[]))
        self.assertEqual(fresh['draftLanguage'], 'python3')
        self.service.save_draft('fixture::A', 'review attempt', language='python3', review_id=task['id'])
        self.receipt(review_id=task['id'])
        self.assertEqual(self.service.workspace()['reviews']['tasks'], [])
        self.assertEqual(self.service.problem('fixture::A')['draft'], 'yesterday complete code')
        due = self.state()['due']
        self.clock.advance(days=10)
        next_task = self.open()
        self.assertNotEqual(task['id'], next_task['id'])
        self.assertLess(due, iso(self.clock()))
        self.assertEqual(self.service.problem('fixture::A',review_id=next_task['id'])['draft'], '')
        self.service.close()
        self.service = TrainingService(self.library,self.db,self.assets,self.judge,self.clock,self.root/'backups')
        self.assertEqual(self.service.problem('fixture::A',review_id=task['id'])['draft'], 'review attempt')
        self.assertEqual(self.service.problem('fixture::A')['draft'], 'yesterday complete code')
        self.assertEqual(self.due()['id'], next_task['id'])
        self.assertIsNotNone(self.service.submission(original['id']))

    def test_independent_retrieval_spaces_out_and_failure_shortens_interval(self):
        clean = interval_after_pass(5,1800,1600)
        hard = interval_after_pass(5,2100,1600)
        failed = interval_after_pass(5,1800,1600,2)
        self.assertGreater(clean[1], hard[1])
        self.assertGreater(clean[1], failed[1])
        self.assertEqual(interval_after_pass(30,1800,1600,assisted=True)[1],1)
        self.seed();self.clock.advance(days=1);task=self.open()
        self.receipt(verdict='WA',review_id=task['id'])
        first = self.service.workspace()
        self.assertEqual(first['reviews']['tasks'][0]['id'],task['id'])
        self.assertEqual(self.state()['lapses'],1)
        self.service.workspace();self.assertEqual(self.state()['lapses'],1)
        self.clock.advance(minutes=4);self.receipt(review_id=task['id'])
        self.service.workspace()
        self.assertEqual(self.state()['successes'],1)
        self.assertEqual(self.state()['lapses'],1)

    def test_old_solution_read_does_not_taint_fresh_review_but_current_read_does(self):
        self.service.mark_solution_seen('fixture::A');self.clock.advance(minutes=1);self.seed()
        self.clock.advance(days=1);task=self.open();self.clock.advance(minutes=10)
        receipt=self.receipt(review_id=task['id'])
        self.assertFalse(self.service.connection.execute('SELECT solution_seen FROM submissions WHERE id=?',(receipt['id'],)).fetchone()[0])
        self.service.workspace();self.assertEqual(self.state()['successes'],1)
        self.clock.advance(days=10);task=self.open();self.clock.advance(minutes=1)
        self.service.mark_solution_seen('fixture::A');self.clock.advance(minutes=1)
        self.receipt(verdict='WA',review_id=task['id'])
        self.clock.advance(seconds=1)
        self.receipt(review_id=task['id']);self.service.workspace()
        self.assertEqual(self.state()['successes'],0)
        self.assertEqual(self.state()['due'],(self.clock().date()+dt.timedelta(days=1)).isoformat())

    def test_easy_task_stops_after_first_clean_review_unknown_difficulty_does_not(self):
        for i in range(5):
            self.library.rows[i].update(difficulty=2000,platform='Codeforces',difficultySource='Codeforces 官方 rating',difficultyEstimated=False)
            self.receipt('fixture::'+chr(65+i))
            self.service.remove_training('fixture::'+chr(65+i))
        self.library.rows[5]['difficulty']=1400
        self.library.rows[6]['difficulty']=None
        self.seed('fixture::F');self.seed('fixture::G')
        self.clock.advance(days=1)
        easy=self.open('fixture::F');unknown=self.open('fixture::G')
        self.receipt('fixture::F',review_id=easy['id']);self.receipt('fixture::G',review_id=unknown['id'])
        self.service.workspace()
        self.assertTrue(self.state('fixture::F')['parked'])
        self.assertIsNone(self.state('fixture::F')['due'])
        self.assertIsNotNone(self.state('fixture::G')['due'])
        self.clock.advance(days=1);self.receipt('fixture::F',verdict='WA');self.service.workspace()
        self.assertFalse(self.state('fixture::F')['parked'])

    def test_large_backlog_caps_day_defers_new_goals_and_does_not_refill(self):
        from goals import Goals
        for row in self.library.rows:self.seed(row['id'])
        self.clock.advance(days=1)
        first=self.service.review_plan()
        self.assertLessEqual(len(first['tasks']),8)
        self.assertLessEqual(first['minutes'],first['dailyMinutes'])
        self.assertTrue(first['reviewOnly'])
        scheduled={r['id'] for r in first['tasks']}
        Goals(self.service).save({'title':'Practice','deadline':'2026-11-30','dailyMinutes':90,'totalProblems':30})
        workspace=self.service.workspace()
        self.assertEqual(workspace['goalTasks'],[])
        self.assertEqual(workspace['goals']['goals'][0]['dailyTask']['target'],0)
        task=first['tasks'][0];self.service.problem(task['problemId'],review_id=task['id'])
        self.clock.advance(minutes=10);self.receipt(task['problemId'],review_id=task['id'])
        remaining={r['id'] for r in self.service.review_plan()['tasks']}
        self.assertEqual(remaining,scheduled-{task['id']})
        self.clock.advance(days=1)
        self.assertTrue(self.service.review_plan()['tasks'])

    def test_samples_and_unbound_or_early_receipts_do_not_complete_review(self):
        self.seed();self.clock.advance(days=1);task=self.open()
        result=self.service.submit('fixture::A','AC',mode='run',review_id=task['id'])
        self.judge.release.set()
        self.receipt() # ordinary practice receipt is distinct from the review
        self.assertEqual(self.due()['id'],task['id'])
        self.receipt(review_id=task['id'],acceptedAt='2026-10-08T00:00:00Z')
        self.assertEqual(self.due()['id'],task['id'])
        self.assertTrue(self.service.submission(result['submission']['id']))

    def test_context_validation_and_removed_training_preserve_journal(self):
        self.seed();self.clock.advance(days=1);task=self.open()
        for identity,review_id,contest in [('fixture::B',task['id'],None),('fixture::A','bad',None),('fixture::A',task['id'],'fake')]:
            with self.assertRaises(ServiceError):
                self.service.review_task(identity,review_id,contest,open_task=True)
        self.service.save_draft('fixture::A','preserve review',review_id=task['id'])
        self.service.remove_training('fixture::A')
        self.assertEqual(self.service.review_plan()['tasks'],[])
        self.assertEqual(self.service.problem('fixture::A',review_id=task['id'])['draft'],'preserve review')

    def test_session_binding_survives_pending_restore_and_duplicate_result(self):
        self.seed();self.clock.advance(days=1);task=self.open()
        with self.service.lock,self.service._write() as db:
            ReviewScheduler(self.service).session(db,'native-session',task['id'])
        record=self.receipt(sessionId='native-session')
        self.assertEqual(self.service.workspace()['reviews']['tasks'],[])
        self.assertEqual(self.service.problem('fixture::A',review_id=task['id'])['submissions'][0]['id'],record['id'])
        state=self.state()
        self.service.workspace();self.assertEqual(self.state(),state)

    def test_clean_first_pass_and_other_verdicts_do_not_create_next_day_reviews(self):
        self.receipt()
        for letter,verdict in zip('BCDE',['CE','TLE','RE','MLE']):
            self.receipt('fixture::'+letter,verdict=verdict)
            self.receipt('fixture::'+letter)
        self.clock.advance(days=1)
        self.assertEqual(self.service.review_plan()['tasks'],[])
        self.assertEqual(reward_totals(self.service),{'xp':0,'count':0})

    def test_wa_without_ac_is_due_tomorrow_and_later_ac_does_not_move_anchor(self):
        self.clock.value=dt.datetime(2026,10,8,15,58,tzinfo=UTC)
        self.receipt(verdict='WA')
        self.assertEqual(self.service.review_plan()['tasks'],[])
        self.clock.advance(minutes=3)
        task=self.due()
        self.assertEqual(task['due'],'2026-10-09')
        self.receipt()
        self.assertEqual(self.due()['id'],task['id'])
        self.clock.advance(days=1)
        self.assertEqual(self.due()['id'],task['id'])

    def test_clean_legacy_plan_leaves_queue_but_preserves_old_review_draft(self):
        self.receipt()
        scheduler=ReviewScheduler(self.service)
        old={'id':'a'*32,'problemId':'fixture::A','problemKey':'fixture::A','due':'2026-10-09','openedAt':None,'completedAt':None,'failures':[],'processed':[]}
        with self.service._write() as db:scheduler.save(db,'review-task:'+old['id'],old)
        self.clock.advance(days=1)
        self.service.save_draft('fixture::A','old review code',review_id=old['id'])
        self.assertEqual(self.service.review_plan()['tasks'],[])
        self.assertEqual(self.service.problem('fixture::A',review_id=old['id'])['draft'],'old review code')

    def test_next_day_reward_is_immediate_once_and_survives_restart(self):
        self.seed();self.clock.advance(days=1);task=self.open()
        before=self.service.insights()['growth']['xp']
        self.clock.advance(minutes=1)
        result=self.receipt(review_id=task['id'])
        self.assertEqual(result['reviewRewardXp'],20)
        growth=self.service.insights()['growth']
        self.assertEqual((growth['reviewXp'],growth['rewardedReviews']),(20,1))
        self.assertEqual(growth['xp'],before+20)
        self.receipt(review_id=task['id'])
        self.assertEqual(reward_totals(self.service),{'xp':20,'count':1})
        self.service.close()
        self.service=TrainingService(self.library,self.db,self.assets,self.judge,self.clock,self.root/'backups')
        self.assertEqual(self.service.submission(result['id'])['submission']['reviewRewardXp'],20)
        self.assertEqual(self.service.insights()['growth']['reviewXp'],20)

    def test_sample_and_unbound_accept_do_not_receive_review_reward(self):
        self.seed();self.clock.advance(days=1);task=self.open()
        self.service.submit('fixture::A','AC',mode='run',review_id=task['id'])
        self.judge.release.set()
        self.receipt()
        self.assertEqual(reward_totals(self.service)['xp'],0)
        self.assertEqual(self.due()['id'],task['id'])

    def test_assisted_clean_review_is_not_queued_again_tomorrow(self):
        self.seed();self.clock.advance(days=1);task=self.open()
        self.clock.advance(minutes=1);self.service.mark_solution_seen('fixture::A')
        self.clock.advance(minutes=1);self.receipt(review_id=task['id'])
        self.service.workspace()
        self.assertGreaterEqual((dt.date.fromisoformat(self.state()['due'])-self.clock().date()).days,2)
        self.clock.advance(days=1)
        self.assertEqual(self.service.review_plan()['tasks'],[])


if __name__=='__main__':unittest.main()
