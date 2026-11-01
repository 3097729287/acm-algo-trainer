"""Durable daily-reward outbox; no network, personal databases or official submissions."""
import datetime as dt
import json
import unittest
from unittest.mock import patch
import test_training as fixtures
import gameplay

class GameplayTests(unittest.TestCase):
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown
    accept=fixtures.ServiceTests.accept

    def test_claim_outbox_is_atomic_and_survives_midnight_and_lost_response(self):
        task=next(t for t in self.service.daily_tasks(goal_tasks=[])['tasks'] if t['lane']=='ac')
        self.accept()
        self.service.claim_daily_task(task['id'])
        self.service.claim_daily_task(task['id'])
        rows=self.service.connection.execute("SELECT * FROM account_preferences WHERE key LIKE 'sticker-eligible:%'").fetchall()
        self.assertEqual(len(rows),1)
        day=self.clock().date().isoformat()
        self.clock.advance(days=2)
        calls=[]
        def interrupted(*args,**kwargs):
            calls.append(args[-1]);raise gameplay.ServiceError(503,'isolated lost response')
        with patch.object(gameplay,'_request',side_effect=interrupted):
            with self.assertRaises(gameplay.ServiceError):gameplay._grant_pending(self.service)
        with patch.object(gameplay,'_request',side_effect=lambda *args,**kwargs:calls.append(args[-1]) or {'saved':True}):
            gameplay._grant_pending(self.service)
            gameplay._grant_pending(self.service)
        self.assertEqual(len(calls),2)
        self.assertEqual(calls[0],calls[1])
        self.assertEqual(calls[1]['day'],day)
        self.assertEqual(self.service.connection.execute("SELECT COUNT(*) FROM account_preferences WHERE key LIKE 'sticker-grant:%'").fetchone()[0],1)

    def test_uncompleted_and_sample_results_cannot_create_a_reward(self):
        task=next(t for t in self.service.daily_tasks(goal_tasks=[])['tasks'] if t['lane']=='ac')
        with self.assertRaises(gameplay.ServiceError):self.service.claim_daily_task(task['id'])
        with patch.object(gameplay,'_request') as network:
            gameplay._grant_pending(self.service)
            network.assert_not_called()
        self.assertEqual([gameplay.rarity({'xp':x}) for x in [10,30,60,100]],['common','rare','epic','legendary'])

    def test_a_switched_account_cannot_receive_an_old_owners_outbox(self):
        task=next(t for t in self.service.daily_tasks(goal_tasks=[])['tasks'] if t['lane']=='ac')
        self.accept();self.service.claim_daily_task(task['id'])
        previous=self.service._ranking_profile()
        changed={**previous,'user_id':'different-isolated-owner'}
        with patch.object(self.service,'_ranking_profile',side_effect=[previous,changed]):
            with self.assertRaises(gameplay.ServiceError) as issue:gameplay._grant_pending(self.service)
        self.assertEqual(issue.exception.status,409)
        self.assertEqual(self.service.connection.execute("SELECT COUNT(*) FROM account_preferences WHERE key LIKE 'sticker-grant:%'").fetchone()[0],0)

