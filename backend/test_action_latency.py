"""Durable rewards and queued synchronization without redundant critical work."""
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from account_sync import AccountStateSync
import test_training as fixtures


class ClaimLatencyTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    tearDown = fixtures.ServiceTests.tearDown
    completed = fixtures.ServiceTests.completed
    accept = fixtures.ServiceTests.accept

    def test_claim_reuses_current_verified_evidence_and_remains_idempotent(self):
        self.accept()
        self.library.library = SimpleNamespace(content_signature=lambda: 1)
        with patch.object(self.service, '_evidence', wraps=self.service._evidence) as evidence:
            self.service.daily_tasks(goal_tasks=[])
            result = self.service.claim_daily_task('solve-1')
            self.assertEqual(evidence.call_count, 1)
        self.assertEqual(result['awardedXp'], 25)
        self.assertEqual(self.service.claim_daily_task('solve-1')['awardedXp'], 0)
        self.assertEqual(self.service.connection.execute("SELECT awarded_xp FROM daily_missions WHERE id='solve-1'").fetchone()[0], 25)

    def test_new_official_receipts_invalidate_evidence_immediately(self):
        self.library.library = SimpleNamespace(content_signature=lambda: 1)
        self.assertEqual(self.service.daily_tasks(goal_tasks=[])['claimable'], 0)
        self.accept()
        self.assertEqual(self.service.claim_daily_task('solve-1')['awardedXp'], 25)

    def test_post_commit_notification_never_waits_on_training_or_catalog_locks(self):
        sync = AccountStateSync.__new__(AccountStateSync)
        sync.status_lock = threading.Lock(); sync.wake = threading.Event(); sync.pending = False
        class ForbiddenLock:
            def __enter__(self): raise AssertionError('Committed HTTP response waited on a training lock')
        sync.service = SimpleNamespace(lock=ForbiddenLock())
        sync.notify_write()
        self.assertTrue(sync.pending)
        self.assertTrue(sync.wake.is_set())
