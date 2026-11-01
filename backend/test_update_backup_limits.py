"""Regression: failed automatic installs must never fill a user's disk."""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

from update_backups import backup,sources,_owned,retire_directory
from update_errors import UpdateStorageError
from software_updates import SoftwareUpdates
from training import ServiceError

class UpdateBackupLimitTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='tb-update-space-');self.state=Path(self.temp.name)/'state';self.state.mkdir()
        self.database=self.state/'personal.sqlite3';self.db=sqlite3.connect(self.database,isolation_level=None)
        self.db.execute('PRAGMA journal_mode=WAL');self.db.execute('CREATE TABLE drafts(id TEXT PRIMARY KEY,code TEXT)');self.db.execute("INSERT INTO drafts VALUES('one','private code in WAL')")
    def tearDown(self):self.db.close();self.temp.cleanup()
    def destination(self,index):return self.state/'backups'/('before-update-'+str(index))
    def test_one_hundred_failed_install_attempts_and_restart_reuse_one_verified_backup(self):
        package=Path(self.temp.name)/'installer.exe';package.write_bytes(b'synthetic never executed')
        release={'version':'1.4.36','sha256':hashlib.sha256(package.read_bytes()).hexdigest(),'name':package.name,'size':package.stat().st_size,'kind':'installer','releaseUrl':'https://47.82.84.74/updates/stable/index.html','notes':''}
        service=SoftwareUpdates(self.state,current='1.4.31',offline=True);service.installer=package;service.release=release;service.status='ready';service.launcher=Mock(side_effect=ValueError('isolated preparation failure'))
        try:
            for _ in range(100):
                with self.assertRaises(ServiceError):service.install(retry=True)
                self.assertEqual(service.status,'install-error');self.assertFalse(service.snapshot()['installDeferred'])
            self.assertEqual(len(list((self.state/'backups').iterdir())),1)
            other=SoftwareUpdates(self.state,current='1.4.31',offline=True);other.installer=package;other.release=release;other.status='ready';other.launcher=service.launcher
            try:
                with self.assertRaises(ServiceError):other.install()
            finally:other.close()
            owned=_owned(self.state/'backups');self.assertEqual(len(owned),1)
            with closing(sqlite3.connect(owned[0][0]/'personal.sqlite3')) as copied:self.assertEqual(copied.execute('SELECT code FROM drafts').fetchone()[0],'private code in WAL')
        finally:service.close()
    def test_later_draft_change_is_backed_up_instead_of_reusing_stale_data(self):
        first=backup(self.state,self.destination(1),context='same-update');self.db.execute("UPDATE drafts SET code='new draft'")
        second=backup(self.state,self.destination(2),context='same-update');self.assertNotEqual(first,second)
        with closing(sqlite3.connect(second/'personal.sqlite3')) as db:self.assertEqual(db.execute('SELECT code FROM drafts').fetchone()[0],'new draft')
    def test_concurrent_requests_reuse_one_complete_generation(self):
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=6) as workers:
            copies=list(workers.map(lambda index:backup(self.state,self.destination(index),context='parallel-update'),range(24)))
        self.assertEqual(len(set(copies)),1);self.assertEqual(len(_owned(self.state/'backups')),1)
    def test_failed_retirement_caps_at_three_generations_without_deleting_any(self):
        with patch('update_backups.retire_directory',return_value=False):
            for i in range(3):self.db.execute('UPDATE drafts SET code=?',(str(i),));backup(self.state,self.destination(i),context='same')
            self.db.execute("UPDATE drafts SET code='fourth'")
            with self.assertRaises(UpdateStorageError):backup(self.state,self.destination(4),context='same')
        self.assertFalse(self.destination(4).exists());self.assertEqual(len(_owned(self.state/'backups')),3)
    def test_only_verified_owned_generation_can_be_retired_and_two_are_kept(self):
        retired=Path(self.temp.name)/'retained-verification-evidence';retired.mkdir()
        def retain(path):path.rename(retired/path.name);return True
        with patch('update_backups.retire_directory',side_effect=retain):
            for i in range(6):self.db.execute('UPDATE drafts SET code=?',(str(i),));backup(self.state,self.destination(i),context='same')
        self.assertEqual(len(_owned(self.state/'backups')),2);self.assertEqual(len(list(retired.iterdir())),4)
    def test_verified_old_copies_are_recycled_and_active_generations_stay_bounded(self):
        retained=Path(self.temp.name)/'simulated-recycle';retained.mkdir()
        def recycle_copy(path):
            self.assertTrue(path.resolve().is_relative_to(Path(self.temp.name).resolve()))
            target=retained/path.name;self.assertTrue(target.resolve().is_relative_to(retained.resolve()))
            path.rename(target);return True
        with patch('update_backups.recycle_directory',side_effect=recycle_copy) as recycle:
            for i in range(12):self.db.execute('UPDATE drafts SET code=?',(str(i),));backup(self.state,self.destination(i),context='same')
        self.assertEqual(recycle.call_count,10);self.assertEqual(len(list(retained.iterdir())),10)
        self.assertEqual(len(_owned(self.state/'backups')),2)
        self.assertEqual({p.name for p in (self.state/'backups').iterdir()},{'before-update-10','before-update-11'})
        self.assertEqual(self.db.execute('SELECT code FROM drafts').fetchone()[0],'11')
    def test_recycle_failure_never_tries_permanent_removal(self):
        path=self.destination('retired')
        path.mkdir(parents=True);(path/'keep.cpp').write_text('preserved','utf-8')
        with patch('update_backups.shutil.rmtree',side_effect=AssertionError('permanent removal forbidden')) as remove,patch('update_backups.recycle_directory',return_value=False) as recycle:
            self.assertFalse(retire_directory(path))
        recycle.assert_called_once_with(path);remove.assert_not_called();self.assertEqual((path/'keep.cpp').read_text('utf-8'),'preserved')
    def test_backup_with_unrecorded_file_is_never_retired(self):
        first=backup(self.state,self.destination(1),context='same')
        (first/'manual-code.cpp').write_text('keep unique manual code','utf-8')
        for i in range(2,4):self.db.execute('UPDATE drafts SET code=?',(str(i),));backup(self.state,self.destination(i),context='same')
        self.db.execute("UPDATE drafts SET code='fourth'")
        with self.assertRaises(UpdateStorageError):backup(self.state,self.destination(4),context='same')
        self.assertEqual((first/'manual-code.cpp').read_text('utf-8'),'keep unique manual code')
    def test_legacy_backup_budget_blocks_new_writes_and_never_removes_old_copies(self):
        legacy=self.destination('legacy');legacy.mkdir(parents=True);old=legacy/'private.sqlite3';old.write_bytes(b'preserve unknown legacy copy')
        expected=self.database.stat().st_size+Path(str(self.database)+'-wal').stat().st_size+1024**2
        with patch('update_backups.MAX_BYTES',expected+old.stat().st_size-1):
            with self.assertRaises(UpdateStorageError):backup(self.state,self.destination('new'),context='same')
        self.assertEqual(old.read_bytes(),b'preserve unknown legacy copy');self.assertFalse(self.destination('new').exists())
    def test_low_disk_is_rejected_before_creating_a_backup_directory(self):
        with patch('update_backups.shutil.disk_usage',return_value=SimpleNamespace(free=1024,total=1024**4)):
            with self.assertRaises(UpdateStorageError):backup(self.state,self.destination('low'))
        self.assertFalse((self.state/'backups').exists())
    def test_other_migration_backups_do_not_consume_the_software_update_budget(self):
        original=self.state/'backups/library-before-schema-upgrade.sqlite3';original.parent.mkdir()
        with original.open('wb') as file:file.write(b'preserved original recovery');file.truncate(4*1024**2)
        with patch('update_backups.MAX_BYTES',2*1024**2):
            copied=backup(self.state,self.destination('update'))
        self.assertTrue((copied/'personal.sqlite3').is_file());self.assertEqual(original.stat().st_size,4*1024**2)
    def test_only_obsolete_known_downloads_are_retired(self):
        from software_updates import _retire_downloads
        directory=Path(self.temp.name)/'cache/updates';directory.mkdir(parents=True)
        old=directory/'ToBe-Setup-1.4.35-win64.exe';old.write_bytes(b'obsolete installer')
        protected=['ToBe-Setup-1.4.36-win64.exe','ToBe-Update-1.4.36-to-1.4.37-win64.zip','unique-code.cpp']
        for name in protected:(directory/name).write_bytes(b'keep')
        with patch('update_backups.recycle_directory',return_value=False) as recycle,patch.object(Path,'unlink',side_effect=AssertionError('permanent removal forbidden')):
            _retire_downloads(directory,'1.4.36')
        recycle.assert_called_once_with(old);self.assertTrue(old.exists());self.assertTrue(all((directory/name).read_bytes()==b'keep' for name in protected))
    def test_download_cache_limit_blocks_network_before_new_partial_files(self):
        directory=Path(self.temp.name)/'cache/updates';directory.mkdir(parents=True)
        (directory/'ToBe-Setup-1.4.99-win64.exe').write_bytes(b'retained future candidate')
        service=SoftwareUpdates(self.state,current='1.4.31',offline=True,opener=Mock())
        service.release={'name':'ToBe-Setup-1.4.36-win64.exe','size':1024,'sha256':'0'*64,'url':'https://47.82.84.74/updates/assets/1.4.36/ToBe-Setup-1.4.36-win64.exe'}
        try:
            with patch('software_updates.MAX_DOWNLOAD_CACHE',1024):service._download()
            self.assertEqual(service.error_code,'storage');service.opener.open.assert_not_called();self.assertEqual(len(list(directory.iterdir())),1)
        finally:service.close()
    def test_backup_names_are_case_insensitively_excluded_and_never_recursive(self):
        for name in ['Backup','BACKUPS','backups']:
            p=self.state/name/'nested';p.mkdir(parents=True,exist_ok=True);(p/'old.sqlite3').write_bytes(b'not a live database')
        self.assertEqual(sources(self.state),[self.database])
        target=backup(self.state,self.destination('one'));self.assertEqual(set(p.name for p in target.iterdir()),{'.update-proof','personal.sqlite3'})
    def test_junctions_are_not_followed_and_make_old_backup_ineligible_for_retirement(self):
        from update_backups import _valid
        outside=Path(self.temp.name)/'outside';outside.mkdir();sentinel=outside/'private.sqlite3';sentinel.write_bytes(b'private external file')
        def link(target):
            if os.name=='nt':
                import _winapi
                _winapi.CreateJunction(str(outside),str(target))
            else:target.symlink_to(outside,target_is_directory=True)
        link(self.state/'linked-account')
        self.assertEqual(sources(self.state),[self.database])
        first=backup(self.state,self.destination(1),context='same');proof=_owned(self.state/'backups')[0][1]
        link(first/'manual-link')
        self.assertFalse(_valid(first,proof));self.assertEqual(sentinel.read_bytes(),b'private external file')
    def test_corrupted_backup_is_never_reused(self):
        first=backup(self.state,self.destination(1),context='same');(first/'personal.sqlite3').write_bytes(b'corrupted fixture')
        second=backup(self.state,self.destination(2),context='same');self.assertNotEqual(first,second)
        with closing(sqlite3.connect(second/'personal.sqlite3')) as db:self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
    def test_source_document_database_is_not_overwritten_by_backup_manifest(self):
        from persistence import save_document,load_document
        save_document(self.state/'private-preferences.json',{'private':'keep'})
        copied=backup(self.state,self.destination(1));self.assertEqual(load_document(copied/'private-preferences.json',{}),{'private':'keep'})
    def test_low_space_download_preserves_existing_partial_and_does_not_open_network(self):
        service=SoftwareUpdates(self.state,current='1.4.35',offline=True,opener=Mock());service.release={'name':'ToBe-Setup-1.4.36-win64.exe','size':1024,'sha256':'0'*64,'url':'https://47.82.84.74/updates/assets/1.4.36/ToBe-Setup-1.4.36-win64.exe'}
        directory=self.state.parent/'cache/updates';directory.mkdir(parents=True);partial=directory/'ToBe-Setup-1.4.36-win64.download';partial.write_bytes(b'retained partial')
        try:
            with patch('update_backups.shutil.disk_usage',return_value=SimpleNamespace(free=1024,total=1024**4)):service._download()
            self.assertEqual(service.error_code,'storage');service.opener.open.assert_not_called();self.assertEqual(partial.read_bytes(),b'retained partial');self.assertEqual(len(list(directory.iterdir())),1)
        finally:service.close()
