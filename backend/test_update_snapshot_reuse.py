from contextlib import closing
import json,sqlite3,tempfile,unittest
from pathlib import Path
from update_backups import backup,reusable_state_snapshot
from library import LibraryDatabase
from test_library import record
from unittest.mock import patch

class SnapshotReuseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.state=Path(self.tmp.name)/'state';self.state.mkdir()
        self.library=LibraryDatabase(self.state/'tb-library.sqlite3')
        self.library.import_records([record()],{},{})
        with closing(sqlite3.connect(self.library.path)) as db,db:
            db.execute('CREATE TABLE unknown_personal_table(id INTEGER PRIMARY KEY,value TEXT)')
            db.execute("INSERT INTO unknown_personal_table VALUES(1,'private unknown content')")
        self.saved=backup(self.state,self.state/'backups/before-update-fixture',context='fixture')

    def test_identical_whole_database_reuses_verified_updater_copy(self):
        with self.library.connection() as db:
            self.assertEqual(reusable_state_snapshot(self.library.path,connection=db),self.saved/self.library.path.name)
        with patch('recovery_backups.snapshot',side_effect=AssertionError('duplicate whole database copy')):
            self.assertEqual(self.library.backup(),self.saved/self.library.path.name)
        self.assertEqual(len(list((self.state/'backups').iterdir())),1)

    def test_unknown_local_row_change_never_reuses_an_older_copy(self):
        with closing(sqlite3.connect(self.library.path)) as db,db:db.execute("UPDATE unknown_personal_table SET value='new private content'")
        self.assertIsNone(reusable_state_snapshot(self.library.path))
        fresh=self.library.backup();self.assertNotEqual(fresh,self.saved/self.library.path.name)
        with closing(sqlite3.connect(fresh)) as db:self.assertEqual(db.execute('SELECT value FROM unknown_personal_table').fetchone()[0],'new private content')

    def test_wal_commits_are_not_ignored_even_if_main_database_bytes_match(self):
        with closing(sqlite3.connect(self.library.path,isolation_level=None)) as db:
            db.execute('PRAGMA journal_mode=WAL');db.execute("UPDATE unknown_personal_table SET value='pending committed WAL'")
            self.assertIsNone(reusable_state_snapshot(self.library.path,connection=db))

    def test_modified_recovery_copy_is_not_reused(self):
        path=self.saved/self.library.path.name
        with path.open('r+b') as stream:stream.seek(200);stream.write(b'corrupt fixture')
        self.assertIsNone(reusable_state_snapshot(self.library.path))

if __name__=='__main__':unittest.main()
