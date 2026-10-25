from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from legacy_cleanup import identify, prepare, retire, finish_install


class LegacyCleanupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.old, self.app = self.root/'TB-old', self.root/'TB-current'
        self.old.mkdir(); self.app.mkdir()
        self.files = {'TB新版.exe': b'official test executable', '_internal/runtime.dll': b'known runtime',
                      'frontend/dist/app.js': b'known frontend', 'VERSION': b'1.3.4'}
        for name, content in self.files.items():
            target = self.old/name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(content)
        hashes = {name: hashlib.sha256(value).hexdigest() for name,value in self.files.items()}
        self.catalog = {'versions': {'1.3.4': {'TB新版.exe': hashes['TB新版.exe']}},
                        'files': {name: [sha] for name,sha in hashes.items()}}

    def tearDown(self): self.temp.cleanup()

    def test_only_known_old_program_is_removed_after_online_wal_backup(self):
        state = self.old/'state'; state.mkdir()
        db = sqlite3.connect(state/'tb-personal.sqlite3')
        db.execute('PRAGMA journal_mode=WAL'); db.execute('CREATE TABLE drafts (code TEXT)')
        db.execute('INSERT INTO drafts VALUES (?)', ('private unsynced draft',)); db.commit()
        (self.old/'my-code.cpp').write_text('private source')
        (self.old/'frontend/dist/app.js').write_bytes(b'user modification')
        try:
            result = retire(identify(self.old,self.app,self.catalog),self.app,self.catalog)
            self.assertEqual(result['status'], 'retired')
            self.assertFalse((self.old/'TB新版.exe').exists())
            self.assertTrue((self.old/'my-code.cpp').exists())
            self.assertEqual((self.old/'frontend/dist/app.js').read_bytes(), b'user modification')
            self.assertTrue((state/'tb-personal.sqlite3').exists())
            with closing(sqlite3.connect(Path(result['backup'])/'state/tb-personal.sqlite3')) as restored:
                self.assertEqual(restored.execute('SELECT code FROM drafts').fetchone()[0], 'private unsynced draft')
        finally: db.close()

    def test_running_old_program_current_program_and_admin_are_preserved(self):
        self.assertIsNone(identify(self.app,self.app,self.catalog))
        item = identify(self.old,self.app,self.catalog)
        self.assertEqual(retire(item,self.app,self.catalog,running=[self.old/'TB新版.exe'])['status'], 'running')
        self.assertTrue((self.old/'TB新版.exe').exists())
        (self.old/'TB管理员版.exe').write_bytes(b'private administrator')
        self.assertIsNone(identify(self.old,self.app,self.catalog))

    def test_backup_failure_or_unknown_executable_never_removes_old_program(self):
        item = identify(self.old,self.app,self.catalog)
        with patch('legacy_cleanup.preserve', side_effect=OSError('locked')):
            with self.assertRaises(OSError): retire(item,self.app,self.catalog)
        self.assertTrue((self.old/'TB新版.exe').exists())
        (self.old/'TB新版.exe').write_bytes(b'unknown app with same name')
        self.assertIsNone(identify(self.old,self.app,self.catalog))

    def test_fresh_directory_automatically_migrates_state_and_never_overwrites_existing_database(self):
        state = self.old/'state'; state.mkdir()
        with closing(sqlite3.connect(state/'tb-personal.sqlite3')) as db:
            db.execute('CREATE TABLE records (code TEXT)'); db.execute("INSERT INTO records VALUES ('private draft')"); db.commit()
        (state/'login.dat').write_bytes(b'protected original credentials')
        with patch('legacy_cleanup.load_catalog',return_value=self.catalog), patch('legacy_cleanup.discover',return_value=([self.old],[],{})):
            prepare(self.app)
            self.assertEqual((self.app/'state/login.dat').read_bytes(), b'protected original credentials')
            with closing(sqlite3.connect(self.app/'state/tb-personal.sqlite3')) as db:
                self.assertEqual(db.execute('SELECT code FROM records').fetchone()[0], 'private draft')
            original = (self.app/'state/tb-personal.sqlite3').read_bytes()
            prepare(self.app)
            self.assertEqual((self.app/'state/tb-personal.sqlite3').read_bytes(), original)

    def test_installer_retirement_migrates_before_removing_old_entry(self):
        state = self.old/'state'; state.mkdir()
        with closing(sqlite3.connect(state/'tb-personal.sqlite3')) as db:
            db.execute('CREATE TABLE drafts (code TEXT)')
            db.execute("INSERT INTO drafts VALUES ('unsynced')"); db.commit()
        with patch('legacy_cleanup.load_catalog', return_value=self.catalog), patch('legacy_cleanup.discover', return_value=([self.old], [], {})):
            result = finish_install(self.app)
        self.assertEqual(result[0]['status'], 'retired')
        self.assertFalse((self.old/'TB新版.exe').exists())
        with closing(sqlite3.connect(self.app/'state/tb-personal.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT code FROM drafts').fetchone()[0], 'unsynced')
        self.assertTrue((state/'tb-personal.sqlite3').exists())

    def test_installer_migration_failure_and_running_old_program_are_safe(self):
        with patch('legacy_cleanup.prepare', side_effect=OSError('busy')):
            with self.assertRaises(OSError): finish_install(self.app)
        self.assertTrue((self.old/'TB新版.exe').exists())
        with patch('legacy_cleanup.load_catalog', return_value=self.catalog), patch('legacy_cleanup.discover', return_value=([self.old], [self.old/'TB新版.exe'], {})):
            self.assertEqual(finish_install(self.app)[0]['status'], 'running')
        self.assertTrue((self.old/'TB新版.exe').exists())
