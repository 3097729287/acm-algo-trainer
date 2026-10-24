"""Reveal eligibility follows real replay lifecycle in disposable personal state."""
import unittest
import test_training as fixtures
from training import TrainingService


class ReplayDifficultyTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    tearDown = fixtures.ServiceTests.tearDown

    def start_replay(self, name='ICPC 2026 测试邀请赛'):
        for row in self.library.rows:
            row.update(contest=name, series='XCPC')
        plan = self.service.preview_replay({'contest': name, 'duration': 1})['plan']
        return self.service.start_contest({'ids': [s['id'] for s in plan['slots']], 'duration': 1})['contest']

    def revealed(self):
        return self.service.workspace()['completedReplayContests']

    def test_running_cancelled_and_practice_do_not_reveal(self):
        self.service.start_training('fixture::A')
        self.assertEqual(self.revealed(), [])
        contest = self.start_replay()
        self.assertEqual(self.revealed(), [])
        # Even a real-looking AC fixture must not grant completion on cancellation.
        self.service.record_official({'id': 'fixture::A', 'contestId': contest['id'],
            'code': 'fixture', 'url': self.assets.problem('fixture::A')['url']},
            {'status': 'finished', 'submissionId': '991811', 'verdict': 'AC'})
        self.service.cancel_contest(contest['id'])
        self.assertEqual(self.revealed(), [])

    def test_finish_reveals_only_original_event_not_user_title(self):
        contest = self.start_replay()
        self.service.connection.execute('UPDATE contests SET name=? WHERE id=?', ('自定义标题', contest['id']))
        self.service.connection.commit()
        finished = self.service.finish_contest(contest['id'])
        self.assertEqual(finished['workspace']['completedReplayContests'], ['ICPC 2026 测试邀请赛'])
        self.assertEqual(finished['contest']['accepted'], 0, 'Completion does not require solving every problem')

    def test_expiry_is_completion_and_warmup_stays_separate(self):
        self.start_replay('ICPC 2026 测试邀请赛（热身赛）')
        self.clock.advance(minutes=2)
        self.assertEqual(self.revealed(), ['ICPC 2026 测试邀请赛（热身赛）'])

    def test_deleted_history_and_restart_preserve_finished_reveal(self):
        contest = self.start_replay()
        self.service.finish_contest(contest['id'])
        self.service.delete_contests(contest['id'])
        self.assertEqual(self.service.workspace()['contests'], [])
        self.assertEqual(self.revealed(), ['ICPC 2026 测试邀请赛'])
        self.service.close()
        self.service = TrainingService(self.library, self.db, self.assets, self.judge, self.clock, self.root/'backups')
        self.assertEqual(self.revealed(), ['ICPC 2026 测试邀请赛'])
        other = TrainingService(self.library, self.root/'other-user.sqlite3', self.assets, self.judge, self.clock, self.root/'other-backups')
        try:
            self.assertEqual(other.workspace()['completedReplayContests'], [])
        finally:
            other.close()

    def test_finished_mixed_mock_does_not_reveal_replay(self):
        plan = self.service.preview_contest({'count': 3, 'duration': 1, 'min': 0, 'max': 3000})['plan']
        contest = self.service.start_contest({'ids': [s['id'] for s in plan['slots']], 'duration': 1})['contest']
        self.service.finish_contest(contest['id'])
        self.assertEqual(self.revealed(), [])


if __name__ == '__main__':
    unittest.main()
