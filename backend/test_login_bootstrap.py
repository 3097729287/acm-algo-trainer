"""A slow cloud restore must not hide login feedback or software updates."""
import threading
import time
import unittest
from unittest.mock import patch

import test_accounts as fixtures
from training import ServiceError


class LoginBootstrapTests(unittest.TestCase):
    setUp = fixtures.AccountTests.setUp
    tearDown = fixtures.AccountTests.tearDown
    start = fixtures.AccountTests.start
    stop = fixtures.AccountTests.stop
    call = fixtures.AccountTests.call
    signup = fixtures.AccountTests.signup
    login = fixtures.AccountTests.login

    def test_cloud_wait_is_background_and_has_one_restore_without_authentication_leak(self):
        self.signup(); self.login(); self.stop(); self.start()
        started, release = threading.Event(), threading.Event()
        original = self.server.accounts._remote
        calls = []
        def remote(method, path, *args, **kwargs):
            if path in ('/v1/accounts/state', '/v2/accounts/state') and method == 'GET':
                calls.append(path); started.set()
                self.assertTrue(release.wait(8))
            return original(method, path, *args, **kwargs)
        with patch.object(self.server.accounts, '_remote', side_effect=remote):
            try:
                status, value = self.call('/api/account?background=1')
                self.assertEqual(status, 200)
                self.assertFalse(value['authenticated'])
                self.assertTrue(value['restoring'])
                self.assertTrue(started.wait(3))
                begin = time.monotonic()
                for _ in range(3):
                    self.assertTrue(self.call('/api/account?background=1')[1]['restoring'])
                    self.assertEqual(self.call('/api/software-update')[0], 200)
                    self.assertEqual(self.call('/')[0], 404)
                self.assertLess(time.monotonic() - begin, 2)
                self.assertEqual(len(calls), 1)
                self.assertIsNone(self.server.accounts.session)
            finally:
                release.set()
            self.server.accounts.restore_worker.join(5)
        self.assertTrue(self.call('/api/account?background=1')[1]['authenticated'])

    def test_failed_restore_keeps_credentials_for_explicit_retry_and_revocation_stays_locked(self):
        self.signup(); self.login(); self.stop(); self.start()
        accounts = self.server.accounts
        with patch.object(accounts, '_remote', side_effect=ServiceError(503, '网络暂时不可用')) as remote:
            self.call('/api/account?background=1')
            accounts.restore_worker.join(5)
            value = self.call('/api/account?background=1')[1]
            self.assertFalse(value['restoring'])
            self.assertFalse(value['authenticated'])
            self.assertIn('网络', value['error'])
            self.assertIsNotNone(accounts.saved)
            self.assertEqual(remote.call_count, 1)
        with patch.object(accounts, '_remote', side_effect=ServiceError(401, 'revoked')):
            self.call('/api/account?background=1&retry=1')
            accounts.restore_worker.join(5)
        self.assertFalse(self.call('/api/account?background=1')[1]['authenticated'])
        self.assertIsNone(accounts.saved)
        self.assertEqual(self.call('/api/workspace')[0], 401)
