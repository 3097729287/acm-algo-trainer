"""Opening existing history preserves authority without copying its payloads."""
from pathlib import Path
import sqlite3
import unittest
from unittest.mock import patch

from test_loading_cache import LoadingCacheTests
from training import TrainingService


class RetainedStartupTests(unittest.TestCase):
    setUp=LoadingCacheTests.setUp
    tearDown=LoadingCacheTests.tearDown
    open=LoadingCacheTests.open

    def test_existing_history_opens_without_full_catalog_or_recovery_copy(self):
        path=self.root/'personal.sqlite3'
        service=TrainingService(self.store,path,account_provider=lambda _:None)
        service.connection.execute("INSERT INTO training(id,active_at,accepted_at) VALUES('fixture::A','2026-10-01T00:00:00Z','2026-10-01T00:00:00Z')")
        service.connection.execute("INSERT INTO drafts VALUES('fixture::A','','retained code','2026-10-01T00:00:00Z')")
        service.close()
        with patch.object(TrainingService,'_backup',side_effect=AssertionError('copied existing history')),patch.object(TrainingService,'_library',side_effect=AssertionError('decoded whole catalog')):
            resumed=TrainingService(self.store,path,account_provider=lambda _:None)
        try:
            self.assertEqual(resumed.connection.execute('SELECT code FROM drafts').fetchone()[0],'retained code')
            self.assertIsNone(resumed.connection.execute('SELECT accepted_at FROM training').fetchone()[0],'A stale local acceptance still gets removed')
        finally:resumed.close()

    def test_missing_schema_cannot_migrate_when_recovery_is_paused(self):
        path=self.root/'old.sqlite3'
        with sqlite3.connect(path) as db:db.execute('CREATE TABLE retained(code TEXT)');db.execute("INSERT INTO retained VALUES('original')")
        with patch.object(TrainingService,'_backup',return_value=None):
            with self.assertRaisesRegex(Exception,'迁移备份'):TrainingService(self.store,path,account_provider=lambda _:None)
        with sqlite3.connect(path) as db:
            self.assertEqual(db.execute('SELECT code FROM retained').fetchone()[0],'original')
            self.assertFalse(db.execute("SELECT 1 FROM sqlite_master WHERE name='training'").fetchone())
