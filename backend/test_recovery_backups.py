"""Recovery copies include WAL data and retain only verified automatic tiers."""
from contextlib import closing
import datetime as dt
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from test_recycle_policy import retained_fixture,fixture_recycler

from recovery_backups import snapshot, preview, prune, verify


class RecoveryBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = retained_fixture('recovery-limits')
        self.root = Path(self.temp.name)
        self.recycler=patch('recovery_backups.recycle',side_effect=fixture_recycler(self.root));self.recycler.start();self.addCleanup(self.recycler.stop)
        self.path = self.root / 'personal.sqlite3'
        self.db = sqlite3.connect(self.path, isolation_level=None)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('CREATE TABLE drafts(id TEXT PRIMARY KEY,code TEXT)')
        self.db.execute("INSERT INTO drafts VALUES('one','private draft with WAL')")
        self.directory = self.root / 'backups'
        self.now = dt.datetime(2026, 10, 29, tzinfo=dt.timezone.utc)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_online_snapshot_restores_committed_wal_and_exact_code(self):
        path = snapshot(self.db, self.path, self.directory, now=self.now)
        self.assertTrue(verify(path))
        metadata = json.loads(Path(str(path) + '.recovery.json').read_text('utf8'))
        self.assertTrue(verify(path, metadata['sha256']))
        with closing(sqlite3.connect(path)) as restored:
            self.assertEqual(restored.execute('SELECT * FROM drafts').fetchall(), [('one', 'private draft with WAL')])

    def test_daily_weekly_recent_limits_exclude_manual_and_unknown_files(self):
        manual = snapshot(self.db, self.path, self.directory, manual=True, now=self.now-dt.timedelta(days=100))
        old = self.directory / 'personal.sqlite3.legacy.bak'
        old.write_bytes(b'legacy recovery untouched')
        for i in range(45):
            self.db.execute('UPDATE drafts SET code=?', ('version ' + str(i),))
            snapshot(self.db, self.path, self.directory, now=self.now-dt.timedelta(days=44-i))
        plan = preview(self.directory, now=self.now)
        self.assertLessEqual(plan['count'], 14)
        self.assertLessEqual(plan['retainedCount'], 14)
        self.assertEqual(plan['retire'], [])
        self.assertTrue(manual.is_file())
        self.assertEqual(old.read_bytes(), b'legacy recovery untouched')
        dates = {item['created'].date() for item in plan['files']}
        self.assertIn(self.now.date(), dates)
        self.assertIn((self.now-dt.timedelta(days=1)).date(), dates)
        self.assertTrue(any((self.now.date()-day).days >= 14 for day in dates), 'Keep a weekly recovery point')

    def test_byte_budget_keeps_two_readable_points_and_preview_is_read_only(self):
        for i in range(8):
            snapshot(self.db, self.path, self.directory, now=self.now+dt.timedelta(seconds=i))
        before = {path.name for path in self.directory.iterdir()}
        policy = {'familyBytes': 1, 'rootBytes': 1}
        plan = preview(self.directory, policy=policy, now=self.now+dt.timedelta(seconds=9))
        self.assertEqual(before, {path.name for path in self.directory.iterdir()})
        self.assertEqual(plan['retainedCount'], 2)
        self.assertTrue(plan['overBudget'], 'Two required recovery points take precedence over an impossible budget')
        prune(self.directory, policy=policy, now=self.now+dt.timedelta(seconds=9))
        self.assertEqual(len(list(self.directory.glob('*.bak'))), 2)
        self.assertTrue(all(verify(path) for path in self.directory.glob('*.bak')))

    def test_same_filename_in_distinct_accounts_preserves_each_family(self):
        other = self.root / 'account-b' / self.path.name
        other.parent.mkdir()
        with closing(sqlite3.connect(other, isolation_level=None)) as db:
            db.execute('CREATE TABLE drafts(id TEXT PRIMARY KEY,code TEXT)')
            db.execute("INSERT INTO drafts VALUES('two','other private account')")
            for i in range(4):
                snapshot(self.db, self.path, self.directory, now=self.now+dt.timedelta(seconds=i))
                snapshot(db, other, self.directory, now=self.now+dt.timedelta(seconds=i))
        prune(self.directory, policy={'rootBytes': 1})
        families = {}
        for item in preview(self.directory)['files']:
            families.setdefault(item['sourceKey'], []).append(item)
        self.assertEqual(sorted(map(len, families.values())), [2, 2])

    def test_insufficient_valid_recovery_points_never_trigger_cleanup(self):
        for i in range(3):
            path = snapshot(self.db, self.path, self.directory, now=self.now+dt.timedelta(seconds=i))
        # A readable metadata file alone is not a verified restore point.
        path.write_bytes(b'corrupt')
        manifest = Path(str(path) + '.recovery.json')
        value = json.loads(manifest.read_text('utf8')); value['bytes'] = path.stat().st_size
        manifest.write_text(json.dumps(value), 'utf8')
        # Keep all when a second required recovery point has also disappeared.
        earliest = min(self.directory.glob('*.bak'))
        earliest.rename(self.root/'missing-required-recovery-fixture')
        plan = preview(self.directory, policy={'rootBytes': 1})
        self.assertEqual(plan['retire'], [])

    def test_failed_recycle_keeps_required_files_and_pauses_new_automatic_copies(self):
        for i in range(4):snapshot(self.db,self.path,self.directory,now=self.now+dt.timedelta(seconds=i))
        old={p.name:p.read_bytes() for p in self.directory.glob('*.bak')}
        with patch('recovery_backups.recycle',return_value=False):
            prune(self.directory,policy={'rootBytes':1})
            self.assertIsNone(snapshot(self.db,self.path,self.directory,policy={'rootBytes':1}))
            with patch('recovery_backups._records',side_effect=AssertionError('repeated paused attempt')):
                self.assertIsNone(snapshot(self.db,self.path,self.directory))
        self.assertEqual(old,{p.name:p.read_bytes() for p in self.directory.glob('*.bak')})

    def test_failed_partial_is_retained_and_not_repeated_automatically(self):
        with patch('recovery_backups._checksum',side_effect=OSError('isolated checksum fault')),patch('recovery_backups.recycle',return_value=False):
            with self.assertRaises(OSError):snapshot(self.db,self.path,self.directory)
        partials=list(self.directory.glob('*.partial'));self.assertEqual(len(partials),1)
        self.assertIsNone(snapshot(self.db,self.path,self.directory))
        restored=snapshot(self.db,self.path,self.directory,retry=True)
        self.assertTrue(verify(restored));self.assertTrue(partials[0].is_file())


if __name__ == '__main__': unittest.main()
