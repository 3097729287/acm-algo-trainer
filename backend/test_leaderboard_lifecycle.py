"""Ranking timers must respect the personal SQLite shutdown barrier."""
import threading
import time
import unittest
from unittest.mock import patch

import test_training as fixtures


class LeaderboardLifecycleTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    tearDown = fixtures.ServiceTests.tearDown

    def test_late_timer_callback_and_snapshot_do_not_read_closed_sqlite(self):
        client = self.service.leaderboard
        timer = threading.Timer(60, client.queue_sync)
        timer.daemon = True
        client.retry_timer = timer
        timer.start()
        self.service.close()
        with patch.object(self.service, '_ranking_profile', side_effect=AssertionError('Closed SQLite read')):
            self.assertEqual(timer.function()['status'], 'closed')
            self.assertEqual(client.snapshot()['status'], 'closed')
        timer.join(1)
        self.assertFalse(timer.is_alive())
        self.assertIsNone(client.retry_timer)

    def test_triggered_callback_and_close_serialize_their_database_access(self):
        client = self.service.leaderboard
        entered, release, closing = threading.Event(), threading.Event(), threading.Event()
        errors = []
        original = self.service._ranking_profile

        def read_profile():
            entered.set()
            if not release.wait(3):
                raise AssertionError('Test did not release profile read')
            return original()

        def callback():
            try:
                client.queue_sync()
            except BaseException as error:
                errors.append(error)

        def close():
            closing.set()
            try:
                self.service.close()
            except BaseException as error:
                errors.append(error)

        with patch.object(self.service, '_ranking_profile', side_effect=read_profile):
            timer = threading.Thread(target=callback)
            timer.start()
            self.assertTrue(entered.wait(3))
            closer = threading.Thread(target=close)
            closer.start()
            self.assertTrue(closing.wait(3))
            release.set()
            timer.join(3)
            closer.join(3)
        self.assertFalse(timer.is_alive())
        self.assertFalse(closer.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(client.queue_sync()['status'], 'closed')

    def test_slow_network_cannot_delay_close_or_write_after_sqlite_closes(self):
        client=self.service.leaderboard
        entered,release=threading.Event(),threading.Event()
        profile={'endpoint':'http://127.0.0.1:1','auth_token':'fixture','user_id':'fixture'}
        def request(*_):
            entered.set();release.wait(3)
            return {'userId':'fixture'}
        original=self.service._ranking_profile
        with patch.object(self.service,'_ranking_profile',return_value=profile),patch.object(client,'_request',side_effect=request),patch.object(self.service,'_ranking_events',side_effect=AssertionError('late SQL access')) as events:
            client.worker=threading.Thread(target=client._sync,daemon=True);client.worker.start()
            self.assertTrue(entered.wait(2))
            started=time.monotonic();self.service.close()
            self.assertLess(time.monotonic()-started,.5)
            release.set();client.worker.join(2)
            events.assert_not_called()
        self.assertFalse(client.worker.is_alive())


if __name__ == '__main__':
    unittest.main()
