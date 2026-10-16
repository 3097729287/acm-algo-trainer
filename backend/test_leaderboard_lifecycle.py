"""Ranking timers must respect the personal SQLite shutdown barrier."""
import threading
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


if __name__ == '__main__':
    unittest.main()
