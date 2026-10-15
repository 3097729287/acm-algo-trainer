import hashlib
from contextlib import closing
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import Mock
from urllib.error import HTTPError

from software_updates import SoftwareUpdates, RELEASES, release_info, version_tuple, trusted_url
from training import ServiceError


DATA = b'isolated installer fixture, never executed'


def release(version='0.10.0'):
    name = f'TB-Setup-{version}-win64.exe'
    return {'tag_name': 'v' + version, 'draft': False, 'prerelease': False, 'body': 'Official release notes',
            'assets': [{'name': name, 'state': 'uploaded', 'size': len(DATA),
                        'digest': 'sha256:' + hashlib.sha256(DATA).hexdigest(),
                        'browser_download_url': RELEASES + '/download/v' + version + '/' + name}]}


def idle(service):
    deadline = time.monotonic() + 5
    while service.snapshot()['status'] in {'checking', 'downloading'}:
        if time.monotonic() > deadline:
            raise AssertionError('Updater fixture timed out')
        time.sleep(.01)
    return service.snapshot()


def wait_for(service, status):
    deadline = time.monotonic() + 3
    while service.snapshot()['status'] != status:
        if time.monotonic() > deadline:
            raise AssertionError(service.snapshot())
        time.sleep(.01)
    return service.snapshot()


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.state = Path(self.temp.name) / 'state'
        self.state.mkdir()
        self.opener = Mock()
        self.service = SoftwareUpdates(self.state, current='0.9.3', opener=self.opener, offline=False)
        self.service.launcher = Mock()

    def tearDown(self):
        self.service.close()
        self.temp.cleanup()

    def prepare(self, data=DATA):
        self.opener.open.side_effect = [io.BytesIO(json.dumps(release()).encode()), io.BytesIO(data)]
        self.service.check()
        self.assertEqual(idle(self.service)['status'], 'available')
        self.service.download()
        return idle(self.service)

    def test_shared_proxy_quota_uses_one_verified_direct_metadata_request(self):
        def exhausted_proxy(request, **kwargs):
            request.set_proxy('127.0.0.1:7897', 'https')
            raise HTTPError('https://api.github.com', 403, 'rate limit exceeded',
                            {'X-RateLimit-Remaining': '0'}, io.BytesIO(b'quota'))
        self.opener.open.side_effect = exhausted_proxy
        self.service.direct_opener = Mock()
        self.service.direct_opener.open.return_value = io.BytesIO(json.dumps(release()).encode())
        self.service.check()
        self.assertEqual(idle(self.service)['status'], 'available')
        self.service.direct_opener.open.assert_called_once()
        self.assertEqual(self.service.direct_opener.open.call_args.args[0].full_url,
                         'https://api.github.com/repos/3097729287/acm-algo-trainer/releases/latest')
        self.assertEqual(self.service.direct_opener.open.call_args.args[0].host, 'api.github.com')

    def test_unrelated_forbidden_response_does_not_change_network_route(self):
        self.opener.open.side_effect = HTTPError('https://api.github.com', 403, 'forbidden',
                                                {'X-RateLimit-Remaining': '10'}, io.BytesIO(b'forbidden'))
        self.service.direct_opener = Mock()
        self.service.check()
        self.assertEqual(idle(self.service)['status'], 'error')
        self.service.direct_opener.open.assert_not_called()

    def test_stable_version_comparison_and_reject_untrusted_or_incomplete_release(self):
        self.assertGreater(version_tuple('v0.10.0'), version_tuple('0.9.99'))
        self.assertIsNone(release_info(release('0.9.3'), '0.10.0'))
        for tag in ('v0.10.0-rc.1', 'latest', 'v00.10.0'):
            value = release(); value['tag_name'] = tag
            with self.assertRaises(ValueError): release_info(value, '0.9.3')
        for change in ({'digest': None}, {'size': 0}, {'browser_download_url': 'https://evil.example/setup.exe'}):
            value = release(); value['assets'][0].update(change)
            with self.assertRaises(ValueError): release_info(value, '0.9.3')
        value = release(); value['prerelease'] = True
        with self.assertRaises(ValueError): release_info(value, '0.9.3')
        for url in ('http://github.com/file', 'https://github.com.evil.example/file', 'https://user@github.com/file'):
            self.assertFalse(trusted_url(url))

    def test_download_hash_and_size_failures_never_allow_install(self):
        self.assertEqual(self.prepare(DATA[:-1])['status'], 'error')
        self.assertIsNone(self.service.installer)
        with self.assertRaises(ServiceError): self.service.install()
        self.service.launcher.assert_not_called()
        self.assertFalse(list(Path(self.temp.name).rglob('*.download')))

    def test_tampered_download_cannot_install(self):
        self.assertEqual(self.prepare()['status'], 'ready')
        self.service.installer.write_bytes(b'changed')
        with self.assertRaises(ServiceError): self.service.install()
        self.service.launcher.assert_not_called()

    def test_install_online_backup_includes_wal_and_keeps_identity_and_code(self):
        db = sqlite3.connect(self.state / 'tb-personal.sqlite3')
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('CREATE TABLE records (identity TEXT, code TEXT)')
        db.execute('INSERT INTO records VALUES (?, ?)', ('fixture-private-identity', 'int main(){} // 草稿'))
        db.commit()
        try:
            self.assertEqual(self.prepare()['status'], 'ready')
            self.assertEqual(self.service.install()['status'], 'installing')
            self.service.launcher.assert_called_once()
            backup = next((self.state / 'backups').glob('*/tb-personal.sqlite3'))
            with closing(sqlite3.connect(backup)) as restored:
                self.assertEqual(restored.execute('SELECT * FROM records').fetchall(), db.execute('SELECT * FROM records').fetchall())
        finally: db.close()

    def test_preferences_persist_offline_has_no_requests_and_guard_keeps_desktop_open(self):
        self.service.configure({'autoCheck': False})
        other = SoftwareUpdates(self.state, offline=True, opener=self.opener)
        try:
            self.assertFalse(other.snapshot()['autoCheck'])
            other.start(); other.check()
            self.opener.open.assert_not_called()
        finally: other.close()
        self.prepare()
        self.service.guard = Mock(side_effect=ServiceError(409, 'pending official receipt'))
        with self.assertRaises(ServiceError): self.service.install()
        self.service.launcher.assert_not_called()
        self.assertEqual(self.service.snapshot()['status'], 'ready')

    def test_startup_always_checks_and_downloads_even_when_daily_preference_is_off(self):
        self.service.configure({'autoCheck': False})
        self.opener.open.side_effect = [io.BytesIO(json.dumps(release()).encode()), io.BytesIO(DATA)]
        self.service.start()
        state = wait_for(self.service, 'ready')
        self.assertTrue(state['startupCheckRequired'])
        self.assertTrue(state['automatic'])
        self.assertFalse(state['autoCheck'])
        self.assertEqual(self.opener.open.call_count, 2)
        self.service.start()
        self.assertEqual(self.opener.open.call_count, 2, 'Starting twice must not create another update job')
        self.service.launcher.assert_not_called()  # The UI must first finish its draft-save barrier.
        self.assertEqual(self.service.install()['status'], 'installing')
        self.service.launcher.assert_called_once()

    def test_startup_on_current_version_checks_once_without_downloading(self):
        self.opener.open.return_value = io.BytesIO(json.dumps(release('0.9.3')).encode())
        self.service.start()
        self.assertTrue(wait_for(self.service, 'current')['automatic'])
        self.assertEqual(self.opener.open.call_count, 1)
        self.service.launcher.assert_not_called()

    def test_automatic_bad_download_never_reaches_install(self):
        self.opener.open.side_effect = [io.BytesIO(json.dumps(release()).encode()), io.BytesIO(DATA[:-1])]
        self.service.start()
        self.assertIn('校验失败', wait_for(self.service, 'error')['error'])
        self.assertIsNone(self.service.installer)
        self.service.launcher.assert_not_called()

    def test_guard_wait_does_not_backup_repeatedly_and_can_continue_without_redownload(self):
        self.prepare()
        self.service.guard = Mock(side_effect=ServiceError(409, '模拟赛进行中'))
        for _ in range(2):
            with self.assertRaises(ServiceError): self.service.install()
        self.assertFalse((self.state / 'backups').exists())
        self.service.guard.side_effect = None
        self.assertEqual(self.service.install()['status'], 'installing')
        self.assertEqual(self.opener.open.call_count, 2)
        self.service.launcher.assert_called_once()

    def test_update_backup_includes_other_accounts_and_skips_old_backups(self):
        account = self.state / 'accounts' / 'fixture-user' / 'tb-personal.sqlite3'
        account.parent.mkdir(parents=True)
        with closing(sqlite3.connect(account)) as db:
            db.execute('CREATE TABLE drafts (code TEXT)')
            db.execute('INSERT INTO drafts VALUES (?)', ('account-private-draft',))
            db.commit()
        old = self.state / 'backups' / 'old'
        old.mkdir(parents=True)
        (old / 'broken.sqlite3').write_bytes(b'old unused backup')
        self.prepare(); self.service.install()
        copies = list((self.state / 'backups').glob('before-update-*/accounts/fixture-user/tb-personal.sqlite3'))
        self.assertEqual(len(copies), 1)
        with closing(sqlite3.connect(copies[0])) as db:
            self.assertEqual(db.execute('SELECT code FROM drafts').fetchone()[0], 'account-private-draft')
        self.assertFalse(list((self.state / 'backups').glob('before-update-*/backups')))


if __name__ == '__main__':
    unittest.main()
