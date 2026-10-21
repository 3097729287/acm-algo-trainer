"""Replay receipts and training ownership, all in disposable databases."""
import json
import unittest
from unittest.mock import patch

import test_training as fixtures
from training import ServiceError


class ReplayWorkflowTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    tearDown = fixtures.ServiceTests.tearDown

    def start(self, replay=True):
        plan = self.service.preview_contest({'count': 3, 'duration': 120, 'min': 1000, 'max': 2100})['plan']
        if replay:
            plan['constraints']['strategy'] = 'replay'
        return self.service.start_contest({'ids': [slot['id'] for slot in plan['slots']], 'duration': 120})['contest']

    def receipt(self, contest, verdict='AC', number='88001', accepted_at=None):
        identity = contest['slots'][0]['id']
        session = {'id': identity, 'contestId': contest['id'], 'code': 'fixture source', 'url': self.assets.problem(identity)['url']}
        return self.service.record_official(session, dict(status='finished', verdict=verdict, submissionId=number, acceptedAt=accepted_at))

    def test_replay_uses_official_evidence_and_keeps_solution_lock(self):
        contest = self.start()
        identity = contest['slots'][0]['id']
        self.service.assert_official_allowed(identity, contest['id'])
        with self.assertRaises(ServiceError):
            self.service.assert_solution_unlocked(identity)
        self.receipt(contest, 'WA')
        self.clock.advance(minutes=5)
        result = self.receipt(contest, number='88002')
        self.assertEqual(result['scope'], 'official')
        current = self.service.contest(contest['id'])['contest']
        self.assertEqual(current['accepted'], 1)
        self.assertEqual(current['penalty'], 25)
        self.service.finish_contest(contest['id'])
        training = self.service.connection.execute('SELECT * FROM training WHERE id=?', (identity,)).fetchone()
        self.assertFalse(training['mock_due'])
        self.assertTrue(training['accepted_at'])

    def test_all_timed_modes_allow_browser_receipts_in_their_own_context(self):
        contest = self.start(replay=False)
        identity = contest['slots'][0]['id']
        self.service.assert_official_allowed(identity, contest['id'])
        with self.assertRaises(ServiceError) as issue:
            self.service.assert_official_allowed(identity)  # No side-practice escape.
        self.assertEqual(issue.exception.status, 403)
        with self.assertRaises(ServiceError):
            self.service.assert_solution_unlocked(identity)
        self.receipt(contest, 'WA')
        self.clock.advance(minutes=5)
        self.receipt(contest, number='88002')
        current = self.service.contest(contest['id'])['contest']
        self.assertEqual(current['accepted'], 1)
        self.assertEqual(current['penalty'], 25)
        self.service.finish_contest(contest['id'])
        self.assertFalse(self.service.connection.execute('SELECT mock_due FROM training WHERE id=?', (identity,)).fetchone()[0])

    def test_replay_cannot_queue_the_legacy_local_submit(self):
        contest=self.start()
        with patch.object(self.service,'_enqueue') as queue, self.assertRaises(ServiceError) as issue:
            self.service.submit(contest['slots'][0]['id'],'fixture source',contest_id=contest['id'])
        self.assertEqual(issue.exception.status,409)
        queue.assert_not_called()

    def test_late_receipt_is_counted_by_acceptance_time(self):
        contest = self.start()
        self.clock.advance(minutes=5)
        accepted = self.clock().isoformat()
        self.clock.advance(minutes=2)
        self.service.finish_contest(contest['id'])
        self.clock.advance(minutes=10)
        self.receipt(contest, accepted_at=accepted)
        self.assertEqual(self.service.contest(contest['id'])['contest']['accepted'], 1)
        self.receipt(contest, number='88003')
        rows = self.service.connection.execute('SELECT contest_id FROM submissions ORDER BY rowid').fetchall()
        self.assertEqual(rows[0][0], contest['id'])
        self.assertIsNone(rows[1][0])

    def test_delete_replay_removes_exclusive_training_but_preserves_code(self):
        contest = self.start()
        first, second = [slot['id'] for slot in contest['slots'][:2]]
        self.service.save_draft(first, 'saved contest source', contest['id'])
        self.service.finish_contest(contest['id'])
        self.service.start_training(second)  # An explicit separate join survives.
        result = self.service.delete_contests(contest['id'])
        self.assertEqual(result['removedTraining'], 2)
        self.assertEqual(self.service.connection.execute('SELECT code FROM drafts WHERE problem_id=?', (first,)).fetchone()[0], 'saved contest source')
        self.assertEqual(self.service.connection.execute('SELECT active FROM training WHERE id=?', (first,)).fetchone()[0], 0)
        self.assertEqual(self.service.connection.execute('SELECT active FROM training WHERE id=?', (second,)).fetchone()[0], 1)
        self.assertEqual(self.service.delete_contests(contest['id'])['removedTraining'], 0)

    def test_repeated_autosaves_keep_durable_data_without_recopying_entire_history(self):
        self.service.start_training('fixture::A')
        with patch.object(self.service, '_backup', wraps=self.service._backup) as backups:
            for index in range(20):
                self.service.save_draft('fixture::A', 'saved source ' + str(index))
        self.assertEqual(backups.call_count, 0)
        self.assertEqual(self.service.problem('fixture::A')['draft'], 'saved source 19')

    def test_receipt_after_replay_deletion_preserves_history_without_rejoining_training(self):
        contest=self.start()
        accepted=self.clock().isoformat()
        self.clock.advance(minutes=1)
        self.service.finish_contest(contest['id'])
        self.service.delete_contests(contest['id'])
        self.receipt(contest,accepted_at=accepted)
        identity=contest['slots'][0]['id']
        row=self.service.connection.execute('SELECT active,accepted_at FROM training WHERE id=?',(identity,)).fetchone()
        self.assertFalse(row['active']);self.assertTrue(row['accepted_at'])
