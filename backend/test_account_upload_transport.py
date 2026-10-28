"""Large account uploads retain bounded transport without weakening reads."""
import base64
import gzip
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from account_sync import AccountStateSync
from training import ServiceError


class AccountUploadTransportTests(unittest.TestCase):
    def sync(self, remote):
        sync = object.__new__(AccountStateSync)
        sync.accounts = SimpleNamespace(_remote=remote)
        sync.chunks = SimpleNamespace(enabled=False)
        sync.session = {'token': 'original'}
        return sync

    def test_upload_has_room_for_slow_uplink_without_changing_snapshot(self):
        remote = Mock(return_value={'revision': 3})
        sync = self.sync(remote)
        state = {'format': 'tb-account-state-v1', 'tables': {'drafts': [
            {'code': 'retained source\n' * 100000}]}, 'publicAccounts': {}}
        self.assertEqual(sync._call('PUT', '/v1/accounts/state', {'revision': 2, 'state': state}), {'revision': 3})
        envelope = remote.call_args.args[2]['state']
        restored = json.loads(gzip.decompress(base64.b64decode(envelope['payload'])))
        self.assertEqual(restored, state)
        self.assertGreater(remote.call_args.kwargs['timeout'], 120)
        self.assertEqual(remote.call_count, 1)
        sync._call('GET', '/v1/accounts/state', cached_revision=3)
        self.assertEqual(remote.call_args.kwargs['timeout'], 20)
        self.assertEqual(remote.call_args.kwargs['state_revision'], 3)

    def test_rotated_session_retry_keeps_upload_budget_and_network_failure_does_not_replay(self):
        sync = self.sync(Mock())
        seen = []
        def remote(method, path, body, session, **options):
            seen.append((session['token'], options['timeout']))
            if len(seen) == 1:
                sync.session = {'token': 'replacement'}
                raise ServiceError(401, 'rotated')
            return {'revision': 1}
        sync.accounts._remote = remote
        body = {'revision': 0, 'state': {'format': 'tb-account-state-v1', 'tables': {}, 'publicAccounts': {}}}
        self.assertEqual(sync._call('PUT', '/v1/accounts/state', body)['revision'], 1)
        self.assertEqual(seen, [('original', 150), ('replacement', 150)])
        sync.accounts._remote = Mock(side_effect=ServiceError(503, 'unavailable'))
        with self.assertRaises(ServiceError): sync._call('PUT', '/v1/accounts/state', body)
        self.assertEqual(sync.accounts._remote.call_count, 1)
