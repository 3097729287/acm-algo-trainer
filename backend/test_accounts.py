"""Account gate and migration against a disposable real HTTP account service."""
import http.client
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch

import backend
from library import LibraryDatabase
from test_library import record
from test_training import Assets, Judge
from persistence import location


class AccountTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tb-accounts-')
        self.root = Path(self.temp.name)
        script = Path(__file__).resolve().parents[1] / 'server/leaderboard/tests/local-server.mjs'
        self.service = subprocess.Popen(['node', str(script)], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        text=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        self.endpoint = json.loads(self.service.stdout.readline())['endpoint']
        database = LibraryDatabase(self.root / 'library.sqlite3')
        database.import_records([record()], {}, {})
        self.library_file = database.path
        self.judge = Judge()
        self.start()

    def start(self):
        self.server = backend.create_server(training_file=self.root / 'tb-personal.sqlite3', library_file=self.library_file,
            data_root=self.root, data_file=self.root / 'absent.md', integration_auto_start=False, assets=Assets(None),
            judge=self.judge, account_endpoint=self.endpoint, backup_dir=self.root / 'backups')
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(3)

    def tearDown(self):
        self.judge.release.set()
        self.stop()
        self.service.terminate()
        self.service.wait(timeout=10)
        self.service.stdout.close()
        self.service.stderr.close()
        self.temp.cleanup()

    def call(self, path, body=None, token=None, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=15)
        values = {'Content-Type': 'application/json', 'X-TB-Token': token if token is not None else self.server.store.token}
        values.update(headers or {})
        connection.request('GET' if body is None else 'POST', path, body=None if body is None else json.dumps(body).encode(), headers=values)
        response = connection.getresponse()
        value = json.loads(response.read())
        status = response.status
        connection.close()
        return status, value

    def signup(self, login='account_a', nickname='账号甲'):
        return self.call('/api/account/register', {'loginId': login, 'nickname': nickname, 'password': 'fixture-password'})

    def login(self, login='account_a', password='fixture-password'):
        return self.call('/api/account/login', {'loginId': login, 'password': password})

    def test_whole_application_requires_login_and_retains_local_origin_guards(self):
        status, bootstrap = self.call('/api/account')
        self.assertEqual(status, 200)
        self.assertFalse(bootstrap['authenticated'])
        for path in ('data', 'workspace', 'profile', 'submissions', 'hub', 'lectures', 'translation/settings', 'software-update', 'browser/setup'):
            self.assertEqual(self.call('/api/' + path)[0], 401, path)
        self.assertEqual(self.call('/api/draft', {'id': 'fixture::A', 'code': 'private'})[0], 401)
        self.assertEqual(self.signup()[0], 200)
        self.assertEqual(self.call('/api/data')[0], 401, 'Registration must still require login')
        self.assertEqual(self.login(password='wrong-password')[0], 401)
        old_token = bootstrap['token']
        self.assertEqual(self.login()[0], 200)
        self.assertEqual(self.call('/api/data')[0], 200)
        self.assertEqual(self.call('/api/training/start', {'id': 'fixture::A'}, token=old_token)[0], 403)
        self.assertEqual(self.call('/api/account/logout', {}, headers={'Origin': 'https://untrusted.example'})[0], 403)
        self.assertEqual(self.call('/api/account/forgot-password', {})[0], 404)
        self.assertEqual(self.call('/api/account/logout', {})[0], 200)
        self.assertEqual(self.call('/api/data')[0], 401)

    def test_existing_drafts_are_preserved_and_account_switch_isolates_personal_data(self):
        base = self.server.training
        base.start_training('fixture::A')
        base.save_draft('fixture::A', 'old private draft')
        self.assertEqual(self.signup()[0], 200)
        _, a = self.login()
        self.assertTrue(a['usesOriginalWorkspace'])
        self.assertEqual(self.call('/api/problem?id=fixture::A')[1]['draft'], 'old private draft')
        self.assertEqual(base.legacy_token(), '', 'Session token must not be stored in ranking_profile')
        self.assertEqual(self.call('/api/account/logout', {})[0], 200)
        self.assertEqual(self.signup('account_b', '账号乙')[0], 200)
        _, b = self.login('account_b')
        self.assertNotEqual(a['account']['userId'], b['account']['userId'])
        self.assertFalse(b['usesOriginalWorkspace'])
        self.assertEqual(self.call('/api/workspace')[1]['summary']['total'], 0)
        self.assertEqual(self.call('/api/draft', {'id': 'fixture::A', 'code': 'account B draft'})[0], 200)
        self.assertEqual(self.call('/api/account/logout', {})[0], 200)
        self.assertEqual(self.login()[0], 200)
        self.assertEqual(self.call('/api/problem?id=fixture::A')[1]['draft'], 'old private draft')
        self.assertEqual(self.call('/api/profile')[1]['profile']['nickname'], '账号甲')

    def test_password_change_remembered_login_and_encrypted_token(self):
        self.signup(); self.login()
        token = self.server.accounts.session['token']
        local_token = self.server.store.token
        database, _ = location(self.server.accounts.session_path)
        with sqlite3.connect(database) as db:
            saved = json.dumps(db.execute('SELECT * FROM documents').fetchall())
        db.close()
        self.assertNotIn(token, saved)
        self.assertNotIn('fixture-password', saved)
        self.stop(); self.start()
        self.assertTrue(self.call('/api/account')[1]['authenticated'])
        self.assertEqual(self.call('/api/account/password', {'oldPassword': 'incorrect-password', 'newPassword': 'new-fixture-password'})[0], 400)
        local_token = self.server.store.token
        status, value = self.call('/api/account/password', {'oldPassword': 'fixture-password', 'newPassword': 'new-fixture-password'})
        self.assertEqual(status, 200)
        self.assertEqual(self.server.store.token, local_token)
        self.assertNotEqual(self.server.accounts.session['token'], token)
        self.call('/api/account/logout', {})
        self.assertEqual(self.login()[0], 401)
        self.assertEqual(self.login(password='new-fixture-password')[0], 200)
        self.assertEqual(self.call('/api/profile', {'nickname': '新昵称'})[1]['profile']['displayName'], '新昵称')

    def test_public_account_metadata_never_exposes_shared_session_token(self):
        self.signup(); self.login()
        secret = self.server.accounts.session['token']
        for path in ('account', 'data', 'workspace', 'profile', 'leaderboard'):
            _, value = self.call('/api/' + path)
            self.assertNotIn(secret, json.dumps(value))
            self.assertNotIn('fixture-password', json.dumps(value))

    def test_account_backups_work_in_long_windows_directories(self):
        from training import TrainingService
        folder = self.root / ('long-account-directory-' + 'x' * 70)
        with patch('toolutil.BACKUP_ROOT', str(self.root / 'backups')):
            service = TrainingService(self.server.store, folder / 'tb-personal.sqlite3', assets=Assets(None), judge=self.judge)
            try:
                service.save_draft('fixture::A', 'private draft in long directory')
                self.assertEqual(service.problem('fixture::A')['draft'], 'private draft in long directory')
                self.assertTrue(list((self.root / 'backups').rglob('*.bak')))
            finally:
                service.close()


if __name__ == '__main__':
    unittest.main()
