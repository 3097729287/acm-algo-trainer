"""A retired official URL must not survive an already-completed default migration."""
import os
import unittest
from unittest.mock import patch

import test_training as fixtures
from leaderboard import upgraded_default_endpoint
from training import TrainingService

OLD = 'https://tb-leaderboard.fsxxxg.workers.dev'
CURRENT = 'https://47.82.84.74'


class EndpointMigrationTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    tearDown = fixtures.ServiceTests.tearDown

    def reopen(self, endpoint):
        self.service.start_training('fixture::A')
        self.service.save_draft('fixture::A', '// preserved local draft')
        self.service.connection.execute('UPDATE ranking_profile SET endpoint=?', (endpoint,))
        previous = self.service._ranking_profile()
        path = self.service.db_path
        self.service.close()
        self.service = TrainingService(self.library, path, assets=self.assets, judge=self.judge,
                                       clock=self.clock, backup_dir=self.root / 'backups')
        return previous

    def test_retired_address_is_fixed_even_after_original_migration_marker(self):
        with patch('leaderboard.default_endpoint', return_value=CURRENT):
            before = self.reopen(OLD)
            after = self.service._ranking_profile()
            self.assertEqual(after['endpoint'], CURRENT)
            for key in ('user_id', 'auth_token', 'nickname', 'created_at'):
                self.assertEqual(after[key], before[key])
            self.assertEqual(self.service.connection.execute('SELECT code FROM drafts').fetchone()[0], '// preserved local draft')
            self.assertEqual(self.service.connection.execute('SELECT COUNT(*) FROM training').fetchone()[0], 1)

    def test_custom_address_is_retained(self):
        with patch('leaderboard.default_endpoint', return_value=CURRENT):
            self.reopen('https://custom.example')
            self.assertEqual(self.service._ranking_profile()['endpoint'], 'https://custom.example')

    def test_offline_and_explicit_service_overrides_do_not_trigger_migration(self):
        with patch.dict(os.environ, {'TB_OFFLINE': '1'}):
            self.assertEqual(upgraded_default_endpoint(OLD), OLD)
        with patch.dict(os.environ, {'TB_OFFLINE': '0', 'TB_LEADERBOARD_URL': 'https://custom.example'}):
            self.assertEqual(upgraded_default_endpoint(OLD), OLD)
        with patch('leaderboard.default_endpoint', return_value=CURRENT):
            self.assertEqual(upgraded_default_endpoint(OLD + '/'), CURRENT)
            self.assertEqual(upgraded_default_endpoint(OLD + '.untrusted.example'), OLD + '.untrusted.example')


if __name__ == '__main__':
    unittest.main()
