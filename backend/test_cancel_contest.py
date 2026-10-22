"""Cancelling a training arrangement retains real work and grants no completion."""
from pathlib import Path
import tempfile
import unittest

from test_training import Assets, Clock, Judge, Library
from training import TrainingService, ServiceError


class CancelContestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tb-cancel-contest-')
        self.root = Path(self.temp.name)
        self.library = Library()
        self.clock = Clock()
        self.service = TrainingService(self.library, self.root/'personal.sqlite3', Assets(self.library), Judge(), self.clock, self.root/'backups')

    def tearDown(self):
        self.service.close()
        self.temp.cleanup()

    def start(self):
        plan = self.service.preview_contest({'count': 4, 'duration': 120, 'min': 1000, 'max': 2100})['plan']
        return self.service.start_contest({'ids': [slot['id'] for slot in plan['slots']], 'duration': 120})['contest']

    def test_cancel_restores_training_arrangement_and_keeps_drafts_accessible(self):
        for row in self.library.rows:
            self.service.start_training(row['id'])
        before = {row['id']: row['activeAt'] for row in self.service.workspace()['training']}
        self.clock.advance(minutes=1)
        contest = self.start()
        identity = contest['slots'][0]['id']
        self.service.save_draft(identity, 'print(42)', contest['id'], 'python3')
        result = self.service.cancel_contest(contest['id'])
        self.assertTrue(result['cancelled'])
        self.assertIsNone(result['workspace']['activeContest'])
        self.assertEqual(result['workspace']['contests'], [])
        self.assertEqual({row['id']: row['activeAt'] for row in result['workspace']['training']}, before)
        self.assertEqual(self.service.connection.execute('SELECT COUNT(*) FROM training WHERE mock_due<>0').fetchone()[0], 0)
        problem = self.service.problem(identity)
        self.assertEqual((problem['draft'], problem['draftLanguage']), ('print(42)', 'python3'))
        self.assertTrue(self.service.cancel_contest(contest['id'])['cancelled'], 'Duplicate click is idempotent')
        self.assertEqual(self.service.insights({})['summary']['completedContests'], 0)

    def test_newly_arranged_training_is_removed_but_code_and_real_receipts_remain(self):
        contest = self.start()
        identity = contest['slots'][0]['id']
        self.service.save_draft(identity, '// preserved code', contest['id'])
        # A fixture receipt, never an actual submission to an original site.
        session = {'id': identity, 'url': self.service.assets.problem(identity)['url'], 'code': '// official code', 'contestId': contest['id']}
        receipt = {'status': 'finished', 'submissionId': '12345', 'verdict': 'AC'}
        self.service.record_official(session, receipt)
        result = self.service.cancel_contest(contest['id'])
        self.assertEqual(result['workspace']['training'], [])
        self.assertEqual(self.service.problem(identity)['draft'], '// preserved code')
        self.assertEqual(self.service.submissions()['total'], 1)
        self.assertEqual(self.service.insights({})['summary']['completedContests'], 0)
        self.assertEqual(self.service.connection.execute('SELECT COUNT(*) FROM drafts').fetchone()[0], 1)

    def test_invalid_identifier_is_a_client_error(self):
        for value in (None, '', [], {}, 12):
            with self.subTest(value=value), self.assertRaises(ServiceError) as error:
                self.service.cancel_contest(value)
            self.assertEqual(error.exception.status, 400)


if __name__ == '__main__':
    unittest.main()
