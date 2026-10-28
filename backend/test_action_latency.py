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

    def test_idle_time_does_not_redecode_verified_receipts(self):
        self.accept()
        self.library.library = SimpleNamespace(content_signature=lambda: 1)
        self.service.daily_tasks(goal_tasks=[])
        cached = self.service._daily_evidence_cache
        self.service._daily_evidence_cache = (cached[0] - 60, *cached[1:])
        with patch.object(self.service, '_evidence', side_effect=AssertionError('Unchanged evidence was decoded again')):
            self.assertEqual(self.service.claim_daily_task('ac-chain:0')['awardedXp'], 25)

    def test_claim_uses_one_catalog_and_one_review_receipt_verification(self):
        import daily_chains
        self.accept()
        with patch.object(self.library, 'data', wraps=self.library.data) as catalog, \
                patch.object(daily_chains, '_completed_reviews', wraps=daily_chains._completed_reviews) as reviews:
            result = self.service.claim_daily_task('ac-chain:0')
        self.assertEqual(result['awardedXp'], 25)
        self.assertEqual(catalog.call_count, 1)
        self.assertEqual(reviews.call_count, 1)
        self.assertEqual(result['dailyTasks']['tasks'][0]['target'], 2)

    def test_library_metadata_change_invalidates_daily_evidence(self):
        self.accept()
        signature = [1]
        self.library.library = SimpleNamespace(content_signature=lambda: signature[0])
        self.service.daily_tasks(goal_tasks=[])
        signature[0] = 2
        with patch.object(self.service, '_evidence', wraps=self.service._evidence) as evidence:
            self.assertEqual(self.service.claim_daily_task('ac-chain:0')['awardedXp'], 25)
        self.assertEqual(evidence.call_count, 1)

    def test_claim_reuses_current_verified_evidence_and_remains_idempotent(self):
        self.accept()
        self.library.library = SimpleNamespace(content_signature=lambda: 1)
        with patch.object(self.service, '_evidence', wraps=self.service._evidence) as evidence:
            self.service.daily_tasks(goal_tasks=[])
            result = self.service.claim_daily_task('ac-chain:0')
            self.assertEqual(evidence.call_count, 1)
        self.assertEqual(result['awardedXp'], 25)
        self.assertEqual(self.service.claim_daily_task('ac-chain:0')['awardedXp'], 0)
        self.assertEqual(self.service.connection.execute("SELECT awarded_xp FROM daily_missions WHERE id='ac-chain:0'").fetchone()[0], 25)

    def test_new_official_receipts_invalidate_evidence_immediately(self):
        self.library.library = SimpleNamespace(content_signature=lambda: 1)
        self.assertEqual(self.service.daily_tasks(goal_tasks=[])['claimable'], 0)
        self.accept()
        self.assertEqual(self.service.claim_daily_task('ac-chain:0')['awardedXp'], 25)

    def test_post_commit_notification_never_waits_on_training_or_catalog_locks(self):
        sync = AccountStateSync.__new__(AccountStateSync)
        sync.status_lock = threading.Lock(); sync.wake = threading.Event(); sync.pending = False
        class ForbiddenLock:
            def __enter__(self): raise AssertionError('Committed HTTP response waited on a training lock')
        sync.service = SimpleNamespace(lock=ForbiddenLock())
        sync.notify_write()
        self.assertTrue(sync.pending)
        self.assertTrue(sync.wake.is_set())
