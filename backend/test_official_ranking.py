import datetime as dt
import time
import unittest
from unittest.mock import patch

import test_training as fixtures


class OfficialRankingTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    tearDown = fixtures.ServiceTests.tearDown
    accept = fixtures.ServiceTests.accept
    completed = fixtures.ServiceTests.completed

    def test_first_official_only_retry_receipts_and_earlier_correction(self):
        self.library.rows[0]['url'] = 'https://codeforces.com/contest/123/problem/A'
        self.library.rows[1]['url'] = 'https://codeforces.com/problemset/problem/123/A'
        self.completed('fixture::C')
        self.completed('fixture::D', mode='run')
        self.accept('fixture::E', verdict='WA')
        with patch.object(self.service.leaderboard, 'invalidate') as sync:
            self.accept('fixture::A', submission_id=8101)
            sync.assert_called_once()
        self.clock.advance(minutes=1)
        self.accept('fixture::B', submission_id=8102)
        events = self.service._ranking_events('fixture')
        self.assertEqual(len(events), 1)
        self.assertEqual(set(events[0]), {'eventId', 'problemKey', 'acceptedAt', 'difficulty', 'scope'})
        self.assertEqual(events[0]['scope'], 'official')
        self.service._ranking_receipts('fixture', events)
        self.assertEqual(self.service._ranking_events('fixture'), [])
        self.assertEqual(len(self.service._ranking_events('other-server')), 1)
        self.clock.value -= dt.timedelta(days=1)
        self.accept('fixture::A', submission_id=8103)
        corrected = self.service._ranking_events('fixture')
        self.assertEqual(corrected[0]['eventId'], events[0]['eventId'])
        self.assertLess(corrected[0]['acceptedAt'], events[0]['acceptedAt'])

    def test_server_must_ack_official_scope_before_receipts_are_persisted(self):
        self.accept()
        with self.service._write() as db:
            db.execute("UPDATE ranking_profile SET endpoint='https://fixture.example'")
        profile = self.service._ranking_profile()
        answers = [{'userId': profile['user_id']}, {}, {'processed': 1, 'scope': 'local-reviewed'}]
        with patch.object(self.service.leaderboard, '_request', side_effect=answers):
            self.service.leaderboard._sync()
        self.assertEqual(self.service.leaderboard.snapshot()['status'], 'error')
        self.assertEqual(len(self.service._ranking_events(profile['endpoint'])), 1)

    def test_ranking_xp_is_an_authoritative_total_not_a_repeatable_claim(self):
        with self.service._write() as db:
            db.execute("UPDATE ranking_profile SET endpoint='https://fixture.example'")
        profile = self.service._ranking_profile()
        original = self.service.insights()['growth']['xp']
        value = {'userId': profile['user_id'], 'totalXp': 600, 'awards': []}
        for _ in range(3):
            self.service._ranking_rewards(profile, value)
        growth = self.service.insights()['growth']
        self.assertEqual(growth['xp'], original + 600)
        self.assertEqual(growth['rankingXp'], 600)
        self.assertEqual(growth['level'], (original + 600) // 500 + 1)
        with self.assertRaises(RuntimeError):
            self.service._ranking_rewards(profile, {**value, 'userId': 'another-identity'})
        with self.assertRaises(RuntimeError):
            self.service._ranking_rewards(profile, {**value, 'totalXp': -1})
        self.service.close()
        with patch('leaderboard.LeaderboardClient.queue_sync'):
            self.service = fixtures.TrainingService(self.library, self.db, self.assets, self.judge, self.clock, self.root / 'backups')
        self.assertEqual(self.service.insights()['growth']['rankingXp'], 600)
        # Changing servers must not add two replicas of the same reward history.
        with self.service._write() as db:
            db.execute("UPDATE ranking_profile SET endpoint='https://other-fixture.example'")
        self.assertEqual(self.service.insights()['growth']['rankingXp'], 0)
        profile = self.service._ranking_profile()
        self.service._ranking_rewards(profile, {**value, 'totalXp': 100})
        self.assertEqual(self.service.insights()['growth']['rankingXp'], 100)

    def test_admin_forwarding_does_not_accept_a_client_supplied_role(self):
        from training import ServiceError
        with self.assertRaises(ServiceError) as caught:
            self.service.leaderboard.admin_delete({'userId': None, 'period': 'daily', 'confirmation': 'delete', 'isAdmin': True})
        self.assertEqual(caught.exception.status, 400)

    def ranking_answers(self, failed_period=None, failed_rewards=False):
        def answer(profile, method, path, data=None):
            if path == '/v1/profile':
                return {'userId': profile['user_id']}
            if path == '/v1/rewards':
                if failed_rewards:
                    raise RuntimeError('排行榜服务响应超时，后台将自动重试')
                return {'userId': profile['user_id'], 'totalXp': 0, 'awards': []}
            period = path.split('period=')[1]
            if period == failed_period:
                raise RuntimeError('排行榜服务响应超时，后台将自动重试')
            return {'period': period, 'entries': [] if period == 'daily' else [{'userId': profile['user_id'], 'count': 2}],
                    'self': {'userId': profile['user_id'], 'count': 0 if period == 'daily' else 2}}

        return answer

    def test_failed_weekly_board_preserves_empty_daily_and_loads_total(self):
        with self.service._write() as db:
            db.execute("UPDATE ranking_profile SET endpoint='https://fixture.example'")
        client = self.service.leaderboard
        client.last_attempt = time.monotonic()
        with patch.object(client, '_request', side_effect=self.ranking_answers(failed_period='weekly')):
            client._sync()
        with patch.object(client, 'queue_sync'):
            daily, weekly, total = [client.rankings(period) for period in ('daily', 'weekly', 'total')]
        self.assertEqual(daily['status'], 'error')
        self.assertTrue(daily['hasSnapshot'])
        self.assertEqual(daily['entries'], [])
        self.assertEqual(daily['self']['count'], 0)
        self.assertFalse(weekly['hasSnapshot'])
        self.assertTrue(total['hasSnapshot'])
        self.assertEqual(total['entries'][0]['count'], 2)
        self.assertIsNone(self.service._ranking_profile()['last_synced_at'])

        with patch.object(client, '_request', side_effect=self.ranking_answers()):
            client._sync()
        self.assertEqual(client.snapshot()['status'], 'ready')
        self.assertEqual(client.snapshot()['error'], '')
        self.assertIsNotNone(self.service._ranking_profile()['last_synced_at'])

    def test_failed_rewards_do_not_discard_new_boards_or_mark_full_sync(self):
        with self.service._write() as db:
            db.execute("UPDATE ranking_profile SET endpoint='https://fixture.example'")
        client = self.service.leaderboard
        with patch.object(client, '_request', side_effect=self.ranking_answers(failed_rewards=True)):
            client._sync()
        self.assertEqual(client.snapshot()['status'], 'error')
        self.assertTrue(all(client.rankings(period)['hasSnapshot'] for period in ('daily', 'weekly', 'total')))
        self.assertEqual(client.rankings('daily')['entries'], [])
        self.assertIsNone(self.service._ranking_profile()['last_synced_at'])

    def test_empty_snapshot_expires_at_the_beijing_day_boundary(self):
        with self.service._write() as db:
            db.execute("UPDATE ranking_profile SET endpoint='https://fixture.example'")
        client = self.service.leaderboard
        with patch.object(client, '_request', side_effect=self.ranking_answers()):
            client._sync()
        self.assertTrue(client.rankings('daily')['hasSnapshot'])
        self.clock.advance(days=1)
        with patch.object(client, 'queue_sync') as retry:
            self.assertFalse(client.rankings('daily')['hasSnapshot'])
            retry.assert_called_once()


if __name__ == '__main__':
    unittest.main()
