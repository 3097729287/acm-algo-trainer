"""Independent cloud-sync edge audit; only disposable connections and payloads."""
import base64
import copy
import datetime as dt
import gzip
import hashlib
import json
import sqlite3
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from account_sync import AccountStateSync, baselines, clean_profile, encoded, merge_states
from achievement_rewards import award_achievement_xp
from progression import ac_achievements
from training import ServiceError


OWNER = '10000000-0000-4000-8000-000000000001'


def state(tables=None):
    return {'format': 'tb-account-state-v1', 'tables': tables or {}, 'publicAccounts': {}}


def envelope(value, **overrides):
    raw = encoded(value).encode('utf8')
    return {'revision': 1, 'state': {'format': 'tb-account-state-gzip-v1',
        'payload': base64.b64encode(gzip.compress(raw)).decode('ascii'),
        'sha256': hashlib.sha256(raw).hexdigest(), 'uncompressedBytes': len(raw), **overrides}}


class SyncIndependentReviewTests(unittest.TestCase):
    def decoder(self, response):
        sync = object.__new__(AccountStateSync)
        sync.session = {'userId': OWNER, 'token': 'old', 'endpoint': 'https://fixture.example'}
        sync.accounts = SimpleNamespace(_remote=lambda *args, **kwargs: copy.deepcopy(response))
        return sync

    def test_sync_schema_accepts_earned_ac_milestones_without_known_date(self):
        connection = sqlite3.connect(':memory:', isolation_level=None)
        try:
            service = SimpleNamespace(connection=connection, lock=threading.RLock())
            AccountStateSync(SimpleNamespace(), service, {'userId': OWNER, 'endpoint': 'https://fixture.example'})
            result = award_achievement_xp(connection, ac_achievements({'known-official-ac': None}), now='2026-10-15T00:00:00Z')
            self.assertEqual(result['xp'], 25)
            self.assertIsNone(connection.execute('SELECT unlocked_at FROM achievement_xp_claims').fetchone()[0])
        finally:
            connection.close()

    def test_merge_undated_and_dated_achievement_keeps_real_earliest_date(self):
        def evidence(stamp):
            return state({'achievement_xp_claims': [{'achievement_id': 'official-1', 'unlocked_at': stamp,
                          'awarded_xp': 25, 'claimed_at': '2026-10-15T00:00:00Z'}]})
        result = merge_states(evidence(None), evidence('2026-10-14T00:00:00Z'))
        self.assertEqual(result['tables']['achievement_xp_claims'][0]['unlocked_at'], '2026-10-14T00:00:00Z')
        self.assertIsNone(merge_states(evidence(None), evidence(None))['tables']['achievement_xp_claims'][0]['unlocked_at'])

    def test_remote_deletion_is_not_resurrected_by_unchanged_offline_copy(self):
        previous = state({'drafts': [{'problem_id': 'A', 'context': '', 'code': 'original', 'saved_at': '2026-10-14'}]})
        removed = state({'drafts': []})
        merged = merge_states(removed, previous, baselines(previous))
        self.assertEqual(merged['tables']['drafts'], [])

    def test_competing_draft_edits_keep_losing_source_in_recovery(self):
        previous = state({'drafts': [{'problem_id': 'A', 'context': '', 'code': 'base', 'saved_at': '2026-10-13'}]})
        local, remote = copy.deepcopy(previous), copy.deepcopy(previous)
        local['tables']['drafts'][0].update(code='offline local code', saved_at='2026-10-14')
        remote['tables']['drafts'][0].update(code='newer remote code', saved_at='2026-10-15')
        result = merge_states(remote, local, baselines(previous))
        self.assertEqual(result['tables']['drafts'][0]['code'], 'newer remote code')
        self.assertTrue(any('offline local code' in row['data'] for row in result['tables']['account_sync_conflicts']))

    def test_public_profile_capture_strips_credential_fields_at_both_levels(self):
        value = {'platform': 'codeforces', 'handle': 'fixture', 'cookie': 'private-cookie', 'auth_token': 'private-token',
                 'solved': [{'url': 'https://codeforces.com/contest/1/problem/A', 'acceptedAt': None,
                             'cookie': 'nested-cookie', 'secret': 'nested-token'}],
                 'history': [], 'activity': []}
        result = clean_profile(value)
        self.assertNotIn('private', encoded(result))
        self.assertNotIn('nested', encoded(result))
        self.assertEqual(result['solved'][0]['url'], value['solved'][0]['url'])

    def test_compressed_download_rejects_wrong_checksum_and_wrong_declared_length(self):
        for overrides in ({'sha256': '0' * 64}, {'uncompressedBytes': 1}):
            with self.assertRaises(ServiceError) as rejected:
                self.decoder(envelope(state(), **overrides))._call('GET', '/v1/accounts/state')
            self.assertEqual(rejected.exception.status, 503)

    def test_compressed_download_rejects_unknown_private_table(self):
        with self.assertRaises(ServiceError):
            self.decoder(envelope(state({'ranking_profile': [{'auth_token': 'must-not-apply'}]})))._call('GET', '/v1/accounts/state')

    def test_gzip_read_has_a_hard_decoded_byte_limit(self):
        limits = []
        class GuardedStream:
            def __init__(self, **kwargs): pass
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                limits.append(limit)
                return b''
        with patch('account_sync.gzip.GzipFile', GuardedStream):
            with self.assertRaises(ServiceError):
                self.decoder(envelope(state()))._call('GET', '/v1/accounts/state')
        self.assertEqual(limits, [64 * 1024 * 1024 + 1])

    def test_late_old_token_rejection_retries_only_rotated_same_owner_session(self):
        sync = self.decoder({'account': {'userId': OWNER}})
        calls = []
        def remote(method, path, body, session, **kwargs):
            calls.append(session['token'])
            if session['token'] == 'old':
                sync.session = {**sync.session, 'token': 'replacement'}
                raise ServiceError(401, 'old token was replaced')
            return {'account': {'userId': OWNER}}
        sync.accounts._remote = remote
        self.assertEqual(sync._call('GET', '/v1/accounts/me')['account']['userId'], OWNER)
        self.assertEqual(calls, ['old', 'replacement'])


if __name__ == '__main__':
    unittest.main()
