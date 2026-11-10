"""Explicit submit wakes one existing browser profile; no OJ or user browser."""
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import Mock, patch
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'desktop'))
from connected_browser import ConnectedBrowserBridge
from connected_preparation import ConnectedPreparation
from silent_browser import wake_browser
from training import ServiceError


class ConnectedAutostartTests(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.bridge = ConnectedBrowserBridge('http://127.0.0.1:12345', clock=lambda: self.now)
        self.waker = Mock(return_value=True)
        self.preparation = ConnectedPreparation(self.bridge, '.', opener=Mock(),
            waker=self.waker, clock=lambda: self.now, profiles=lambda: [])
        self.url = 'https://ac.nowcoder.com/acm/problem/21992'

    def test_submit_wakes_without_waiting_for_the_account_guard_or_opening_a_login(self):
        self.preparation.check_submission(self.url)
        self.waker.assert_called_once_with()
        self.assertEqual(self.bridge.sessions, {})
        self.assertEqual(self.preparation.opener.mock_calls, [])
        pending=self.bridge.submit(self.url,'int main(){}','isolated')
        self.assertEqual(pending['status'],'loading')
        self.assertFalse(self.bridge.sessions[pending['sessionId']]['attempted'])

    def test_idle_metadata_and_refresh_never_wake_a_browser(self):
        self.preparation.snapshot()
        self.preparation.action({'action': 'refresh'})
        self.preparation.action({'action': 'startup-logins'})
        self.waker.assert_not_called()
        self.assertEqual(self.bridge.sessions, {})

    def test_an_already_connected_browser_is_reused_without_another_launch(self):
        client = str(uuid.uuid4())
        key = self.bridge.register_browser({'clientId': client, 'protocol': 4})['key']
        self.bridge.browser_queue({'clientId': client, 'hasWindow': True}, key)
        self.preparation.check_submission(self.url)
        self.waker.assert_not_called()

    def test_repeated_and_concurrent_clicks_do_not_accumulate_browser_processes(self):
        threads = [threading.Thread(target=self.preparation.check_submission, args=(self.url,)) for _ in range(16)]
        for thread in threads:thread.start()
        for thread in threads:thread.join(timeout=1)
        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.waker.assert_called_once_with()
        self.now = 11
        self.preparation.check_submission(self.url)
        self.assertEqual(self.waker.call_count, 2)

    def test_unknown_or_ambiguous_registration_never_falls_back_to_another_login(self):
        self.waker.return_value = False
        with self.assertRaises(ServiceError):self.preparation.check_submission(self.url)
        self.assertEqual(self.bridge.sessions, {})
        self.assertEqual(self.preparation.opener.mock_calls, [])

    def test_registered_closed_browser_does_not_repeat_first_time_setup_instructions(self):
        profiles = Mock(return_value=[(Path('C:/test/msedge.exe'), 'Default')])
        preparation = ConnectedPreparation(self.bridge, '.', opener=Mock(),
            waker=self.waker, clock=lambda: self.now, profiles=profiles)
        first = preparation.snapshot()
        self.assertTrue(first['extension']['installed'])
        self.assertFalse(first['extension']['connected'])
        self.assertFalse(first['manualLoadRequired'])
        self.assertTrue(first['ready'])
        preparation.snapshot()
        profiles.assert_called_once_with()
        self.waker.assert_not_called()

    def test_invalid_original_site_never_launches_a_browser(self):
        with self.assertRaises(ValueError):self.preparation.check_submission('https://example.com/login')
        self.waker.assert_not_called()

    def test_silent_wake_uses_only_the_unique_registered_profile_without_login_or_debug_flags(self):
        executable = Path('C:/test/msedge.exe')
        with patch.dict('os.environ', {'TB_OFFLINE': '0'}), \
             patch('silent_browser.registered_browsers', return_value=[(executable, 'Profile 2')]), \
             patch('silent_browser.subprocess.Popen') as launched:
            self.assertTrue(wake_browser(unique=True))
            arguments = launched.call_args.args[0]
            self.assertEqual(arguments, [str(executable), '--no-startup-window', '--profile-directory=Profile 2'])
            self.assertEqual(launched.call_args.kwargs['startupinfo'].wShowWindow, 0)
        with patch.dict('os.environ', {'TB_OFFLINE': '0'}), \
             patch('silent_browser.registered_browsers', return_value=[(executable, 'Default'), (executable, 'Profile 2')]), \
             patch('silent_browser.subprocess.Popen') as launched:
            self.assertFalse(wake_browser(unique=True))
            launched.assert_not_called()


if __name__ == '__main__':unittest.main()
