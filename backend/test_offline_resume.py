"""Only protected, previously verified accounts may continue local offline work."""
import json
import time
import unittest
from unittest.mock import patch
from urllib.error import URLError

from account_sync import AccountStateSync
from accounts import AccountConnectionUnavailable
import test_accounts as fixtures
from training import ServiceError


class OfflineResumeTests(unittest.TestCase):
    setUp = fixtures.AccountTests.setUp
    tearDown = fixtures.AccountTests.tearDown
    start = fixtures.AccountTests.start
    stop = fixtures.AccountTests.stop
    call = fixtures.AccountTests.call
    signup = fixtures.AccountTests.signup
    login = fixtures.AccountTests.login

    def saved_account(self):
        self.assertEqual(self.signup()[0], 200)
        self.assertEqual(self.login()[0], 200)
        self.server.training.save_draft('fixture::A', 'durable independent code')
        self.server.accounts.sync_pending(wait=True)
        self.stop(); self.start()

    def test_first_login_has_no_offline_access_lease(self):
        with patch.object(self.server.accounts.opener, 'open', side_effect=URLError('isolated disconnected fixture')):
            self.assertFalse(self.call('/api/account')[1]['authenticated'])
            self.assertEqual(self.login()[0], 503)
        self.assertIsNone(self.server.accounts.session)
        self.assertEqual(self.call('/api/workspace')[0], 401)

    def test_outage_restores_only_existing_verified_workspace_and_writes_locally(self):
        self.saved_account()
        started = time.monotonic()
        with patch.object(self.server.accounts.opener, 'open', side_effect=URLError('isolated disconnected fixture')), patch.object(AccountStateSync, 'start'):
            status, value = self.call('/api/account')
        self.assertLess(time.monotonic()-started, 3)
        self.assertEqual(status, 200, value)
        self.assertTrue(value['authenticated'])
        self.assertTrue(value['sync']['offline'])
        self.assertEqual(value['sync']['status'], 'offline')
        self.assertEqual(self.call('/api/workspace')[0], 200)
        self.assertEqual(self.call('/api/problem?id=fixture::A')[1]['draft'], 'durable independent code')
        self.assertEqual(self.call('/api/draft', {'id': 'fixture::A', 'code': 'offline changed code'})[0], 200)
        self.assertEqual(self.server.training.problem('fixture::A')['draft'], 'offline changed code')

    def test_reconnect_fetches_and_merges_remote_changes_before_uploading(self):
        self.saved_account()
        with patch.object(self.server.accounts, '_remote', side_effect=AccountConnectionUnavailable(503, 'offline fixture')), patch.object(AccountStateSync, 'start'):
            self.assertTrue(self.call('/api/account')[1]['authenticated'])
        sync = self.server.accounts.state_sync
        sync.service.save_draft('fixture::A', 'offline changed code')
        # A remote edit of another preference must survive reconnection.
        sync.chunks.negotiate()
        sync.chunks.answer = None
        remote = sync._call('GET', '/v1/accounts/state')
        remote['state']['tables']['account_preferences'].append({'key':'fixture-remote','value':'true','updated_at':'2026-10-29T12:00:00Z'})
        sync._call('PUT', '/v1/accounts/state', {'revision':remote['revision'], 'state':remote['state']})
        calls = []
        original = sync.accounts._remote
        def trace(method, path, *args, **kwargs):
            calls.append((method, path))
            return original(method, path, *args, **kwargs)
        with patch.object(sync.accounts, '_remote', side_effect=trace): sync.flush()
        self.assertFalse(sync.needs_reconnect)
        roots = [method for method, path in calls if path.endswith('/accounts/state')]
        self.assertEqual(roots[0], 'GET')
        self.assertIn('PUT', roots)
        self.assertEqual(sync.service.problem('fixture::A')['draft'], 'offline changed code')
        row = sync.service.connection.execute("SELECT value FROM account_preferences WHERE key='fixture-remote'").fetchone()
        self.assertEqual(row[0], 'true')
        cloud = sync._call('GET', '/v1/accounts/state')['state']
        self.assertEqual(cloud['tables']['drafts'][0]['code'], 'offline changed code')

    def test_expired_missing_owner_or_metadata_never_qualifies_for_offline(self):
        self.saved_account()
        original = dict(self.server.accounts.saved)
        original_registry = dict(self.server.accounts.registry)
        for mutation in ('expired', 'owner', 'metadata'):
            with self.subTest(mutation=mutation):
                self.server.accounts.saved = dict(original)
                self.server.accounts.registry = dict(original_registry)
                if mutation == 'expired': self.server.accounts.saved['expiresAt'] = int(time.time())-1
                if mutation == 'owner': self.server.accounts.registry['activeOwner'] = 'another-account'
                if mutation == 'metadata':
                    self.server.training.connection.execute('DELETE FROM account_sync_meta')
                with patch.object(self.server.accounts, '_remote', side_effect=AccountConnectionUnavailable(503,'offline fixture')), patch.object(AccountStateSync, 'start'):
                    self.assertFalse(self.call('/api/account')[1]['authenticated'])
                self.assertEqual(self.call('/api/workspace')[0], 401)

    def test_known_revocation_upgrade_and_corrupt_responses_never_unlock(self):
        self.saved_account()
        saved = dict(self.server.accounts.saved)
        for error in (ServiceError(401,'revoked'), ServiceError(426,'upgrade required'), ServiceError(503,'invalid state checksum')):
            with self.subTest(status=error.status):
                self.server.accounts.saved = dict(saved)
                with patch.object(self.server.accounts, '_remote', side_effect=error), patch.object(AccountStateSync, 'start'):
                    self.assertFalse(self.call('/api/account')[1]['authenticated'])
                self.assertEqual(self.call('/api/workspace')[0], 401)

    def test_revocation_on_reconnect_locks_access_but_preserves_offline_code(self):
        self.saved_account()
        with patch.object(self.server.accounts, '_remote', side_effect=AccountConnectionUnavailable(503,'offline fixture')), patch.object(AccountStateSync, 'start'):
            self.assertTrue(self.call('/api/account')[1]['authenticated'])
        sync = self.server.accounts.state_sync
        sync.service.save_draft('fixture::A', 'code saved during the offline lease')
        with patch.object(self.server.accounts, '_remote', side_effect=ServiceError(401, 'revoked')):
            with self.assertRaises(ServiceError): sync.flush()
        self.assertIsNone(self.server.accounts.session)
        self.assertEqual(self.call('/api/workspace')[0], 401)
        self.assertEqual(sync.service.problem('fixture::A')['draft'], 'code saved during the offline lease')


if __name__ == '__main__': unittest.main()
