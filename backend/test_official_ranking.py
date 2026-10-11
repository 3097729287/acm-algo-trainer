import datetime as dt
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


if __name__ == '__main__':
    unittest.main()
