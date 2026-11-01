from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from legacy_cleanup import identify, prepare, retire, finish_install
from test_recycle_policy import retained_fixture,fixture_recycler


class LegacyCleanupTests(unittest.TestCase):
    def setUp(self):
        self.temp = retained_fixture('legacy')
        self.root = Path(self.temp.name)
        recycler=patch('legacy_cleanup.recycle_directory',side_effect=fixture_recycler(self.root))
        self.recycled=recycler.start();self.addCleanup(recycler.stop)
        capacity=patch('legacy_cleanup.can_recycle',return_value=True);capacity.start();self.addCleanup(capacity.stop)
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

    def test_failed_recycling_does_not_repeat_backups_on_poll_or_restart(self):
        item=identify(self.old,self.app,self.catalog)
        with patch('legacy_cleanup.recycle_directory',return_value=False) as recycle:
            first=retire(item,self.app,self.catalog)
            for _ in range(25):self.assertEqual(retire(item,self.app,self.catalog)['status'],'retained')
            self.assertEqual(recycle.call_count,1)
            self.assertEqual(len(list((self.app/'state/backups/legacy-programs').iterdir())),1)
            self.assertEqual(retire(item,self.app,self.catalog,retry=True)['backup'],first['backup'])
            self.assertEqual(recycle.call_count,2)
            self.assertEqual(len(list((self.app/'state/backups/legacy-programs').iterdir())),1)
        self.assertTrue((self.old/'TB新版.exe').exists())

    def test_unknown_bin_capacity_prevents_backup_creation_and_preserves_old_data(self):
        with patch('legacy_cleanup.can_recycle',return_value=False),patch('legacy_cleanup.preserve') as preserve:
            self.assertEqual(retire(identify(self.old,self.app,self.catalog),self.app,self.catalog)['status'],'retained')
            preserve.assert_not_called()
        self.assertTrue((self.old/'TB新版.exe').exists())

    def test_linked_recovery_directory_is_not_reused_and_original_is_retained(self):
        state=self.old/'state';state.mkdir();(state/'draft.cpp').write_text('unsynced draft')
        item=identify(self.old,self.app,self.catalog)
        with patch('legacy_cleanup.recycle_directory',return_value=False):
            first=retire(item,self.app,self.catalog)
        linked_directory=Path(first['backup'])/'state'
        with patch('legacy_cleanup.linked',side_effect=lambda path:Path(path)==linked_directory),patch('legacy_cleanup.recycle_directory') as recycle:
            with self.assertRaisesRegex(ValueError,'Linked legacy backup'):
                retire(item,self.app,self.catalog,retry=True)
            recycle.assert_not_called()
        self.assertEqual((state/'draft.cpp').read_text(),'unsynced draft')
        self.assertTrue((self.old/'TB新版.exe').exists())

    def test_explicit_retry_reuses_unchanged_backup_and_captures_new_committed_wal(self):
        state=self.old/'state';state.mkdir()
        db=sqlite3.connect(state/'personal.sqlite3');db.execute('PRAGMA journal_mode=WAL')
        db.execute('CREATE TABLE drafts(code TEXT)');db.execute("INSERT INTO drafts VALUES('first')");db.commit()
        item=identify(self.old,self.app,self.catalog)
        try:
            with patch('legacy_cleanup.recycle_directory',return_value=False):
                first=retire(item,self.app,self.catalog)
                self.assertEqual(retire(item,self.app,self.catalog,retry=True)['backup'],first['backup'])
                db.execute("UPDATE drafts SET code='second committed in WAL'");db.commit()
                self.assertEqual(retire(item,self.app,self.catalog)['backup'],first['backup'],'Automatic retry remains suppressed')
                second=retire(item,self.app,self.catalog,retry=True)
            self.assertNotEqual(first['backup'],second['backup'])
            for result,expected in [(first,'first'),(second,'second committed in WAL')]:
                with closing(sqlite3.connect(Path(result['backup'])/'state/personal.sqlite3')) as check:
                    self.assertEqual(check.execute('SELECT code FROM drafts').fetchone()[0],expected)
            self.assertEqual(len(list((self.app/'state/backups/legacy-programs').iterdir())),2)
        finally:db.close()

    def test_one_hundred_blocked_recycles_reuse_one_private_snapshot_without_permanent_fallback(self):
        state=self.old/'state';state.mkdir();(state/'draft.cpp').write_text('unique private draft')
        with patch('legacy_cleanup.recycle_directory',return_value=False),patch.object(Path,'unlink',side_effect=AssertionError('No permanent removal')):
            for _ in range(100):
                result=retire(identify(self.old,self.app,self.catalog),self.app,self.catalog)
                self.assertEqual(result['status'],'retained')
        self.assertEqual(len(list((self.app/'state/backups/legacy-programs').glob('*/complete.json'))),1)
        self.assertTrue((self.old/'TB新版.exe').exists());self.assertEqual((state/'draft.cpp').read_text(),'unique private draft')

    def test_oversized_legacy_snapshot_stops_before_creating_a_backup(self):
        from update_errors import UpdateStorageError
        with patch('legacy_cleanup.require_space',side_effect=UpdateStorageError('insufficient fixture space')):
            with self.assertRaises(UpdateStorageError):retire(identify(self.old,self.app,self.catalog),self.app,self.catalog)
        self.assertFalse((self.app/'state/backups/legacy-programs').exists());self.assertTrue((self.old/'TB新版.exe').exists())

    def test_legacy_size_and_total_recovery_budget_keep_originals_without_new_copies(self):
        from update_errors import UpdateStorageError
        state=self.old/'state';state.mkdir();draft=state/'draft.cpp';draft.write_text('first draft')
        item=identify(self.old,self.app,self.catalog)
        with patch('legacy_cleanup.LEGACY_RECOVERY_LIMIT',1):
            with self.assertRaises(UpdateStorageError):retire(item,self.app,self.catalog)
        self.assertFalse((self.app/'state/backups/legacy-programs').exists())
        with patch('legacy_cleanup.recycle_directory',return_value=False):
            first=retire(item,self.app,self.catalog,retry=True)
        parent=Path(first['backup']).parent
        occupied=sum(path.stat().st_size for path in parent.rglob('*') if path.is_file())
        draft.write_text('new committed draft')
        needed=draft.stat().st_size+1024**2
        with patch('legacy_cleanup.LEGACY_RECOVERY_LIMIT',occupied+needed-1):
            with self.assertRaises(UpdateStorageError):retire(item,self.app,self.catalog,retry=True)
        self.assertEqual(len(list(parent.iterdir())),1)
        self.assertEqual(draft.read_text(),'new committed draft')
        self.assertEqual((Path(first['backup'])/'state/draft.cpp').read_text(),'first draft')
        self.assertTrue(item['executable'].exists())

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
