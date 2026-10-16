from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from training import TrainingService
from test_training import Library, Clock


class EarnedExperienceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tb-earned-xp-')
        self.root = Path(self.temp.name)
        self.library, self.clock = Library(), Clock()
        self.library.rows[0].update(url='https://ac.nowcoder.com/acm/contest/141721/E', difficulty=1900)
        self.service = TrainingService(self.library, self.root / 'personal.sqlite3', clock=self.clock,
                                       backup_dir=self.root / 'backups')

    def tearDown(self):
        self.service.close()
        self.temp.cleanup()

    def accept(self, row, identity):
        stamp = self.clock().isoformat()
        self.service.connection.execute('INSERT INTO submissions(id,problem_id,mode,code,submitted_at,finished_at,verdict,scope) VALUES(?,?,?,?,?,?,?,?)',
                                        (identity, row['id'], 'submit', 'fixture', stamp, stamp, 'AC', 'official'))

    def assert_xp_components(self, base, achievement):
        growth = self.service.insights()['growth']
        self.assertEqual(growth['totalXp'], base + achievement)
        self.assertEqual(growth['achievementXp'], achievement)
        self.assertEqual(growth['missionXp'], 0)
        self.assertEqual(growth['rankingXp'], 0)
        self.assertEqual(self.service.connection.execute('SELECT SUM(awarded_xp) FROM official_first_xp_awards').fetchone()[0], base)
        self.assertEqual(self.service.connection.execute('SELECT COUNT(*) FROM official_first_xp_awards').fetchone()[0], 1)
        claims = [tuple(row) for row in self.service.connection.execute('SELECT * FROM achievement_xp_claims ORDER BY achievement_id')]
        self.assertEqual(sum(row[2] for row in claims), achievement)
        repeated = self.service.insights()['growth']
        self.assertEqual(repeated['totalXp'], growth['totalXp'])
        self.assertEqual(repeated['newAchievementXp'], 0)
        self.assertEqual([tuple(row) for row in self.service.connection.execute('SELECT * FROM achievement_xp_claims ORDER BY achievement_id')], claims)

    def test_upgrade_preserves_published_reward_after_difficulty_reassessment(self):
        self.accept(self.library.rows[0], 'historical-ac')
        self.service.connection.executescript('DROP TABLE official_first_xp_awards; DROP TABLE official_xp_state;')
        self.service.close()
        self.service = TrainingService(self.library, self.root / 'personal.sqlite3', clock=self.clock,
                                       backup_dir=self.root / 'backups')
        self.assert_xp_components(300,125)
        self.library.rows[0]['difficulty'] = None
        self.assert_xp_components(300,125)
        self.assertEqual(self.service.connection.execute('SELECT awarded_xp FROM official_first_xp_awards').fetchone()[0], 300)

    def test_new_awards_use_current_difficulty_and_stay_frozen_on_restart(self):
        self.accept(self.library.rows[0], 'new-ac')
        self.assert_xp_components(200,125)
        self.library.rows[0]['difficulty'] = 1000
        self.assert_xp_components(200,125)
        self.service.close()
        self.service = TrainingService(self.library, self.root / 'personal.sqlite3', clock=self.clock,
                                       backup_dir=self.root / 'backups')
        self.assert_xp_components(200,125)

    def test_unrated_task_awards_once_after_rating_becomes_available(self):
        self.library.rows[0].update(url='https://example.com/unrated', difficulty=None)
        self.accept(self.library.rows[0], 'unrated-ac')
        self.assert_xp_components(0,25)
        self.library.rows[0]['difficulty'] = 1500
        self.assert_xp_components(150,65)
        self.library.rows[0]['difficulty'] = 2300
        self.assert_xp_components(150,205)

    def test_reading_unchanged_experience_does_not_create_more_backups(self):
        self.accept(self.library.rows[0], 'new-ac')
        self.service.insights()
        records = [dict(row) for row in self.service.connection.execute('SELECT * FROM submissions')]
        with patch.object(self.service, '_backup') as backup:
            self.assertEqual(self.service._first_acceptance_xp(self.library.rows, records), 200)
            self.assertEqual(self.service._first_acceptance_xp(self.library.rows, records), 200)
            backup.assert_not_called()


if __name__ == '__main__':
    unittest.main()
