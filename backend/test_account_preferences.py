import json
import unittest
from unittest.mock import patch

from preferences import read_preferences, save_preferences
from training import ServiceError
import test_training as fixtures


class AccountPreferencesTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    tearDown = fixtures.ServiceTests.tearDown

    def test_favorites_views_and_navigation_survive_restart(self):
        value = {'theme': 'dark', 'favorites': ['fixture::A'],
                 'views': [{'id': 'saved', 'name': '复习', 'query': 'A'}],
                 'navLabels': {'mine': '训练'}, 'navGroups': {}, 'navOrder': ['mine', 'library']}
        self.assertIsNone(read_preferences(self.service)['preferences'])
        result = save_preferences(self.service, {'preferences': value})
        self.assertEqual(result['preferences'], value)
        self.service.close()
        from training import TrainingService
        self.service = TrainingService(self.library, self.db, self.assets, self.judge, self.clock, self.root/'backups')
        self.assertEqual(read_preferences(self.service), result)

    def test_unchanged_preferences_do_not_back_up_or_write_on_polls(self):
        value = {'favorites': ['fixture::A'], 'navLabels': {}}
        first = save_preferences(self.service, {'preferences': value})
        changes = self.service.connection.total_changes
        with patch.object(self.service, '_backup') as backup:
            self.assertEqual(save_preferences(self.service, {'preferences': value}), first)
            self.assertEqual(read_preferences(self.service), first)
            backup.assert_not_called()
        self.assertEqual(self.service.connection.total_changes, changes)

    def test_device_credentials_and_invalid_preference_data_are_rejected(self):
        for value in ({'apiKey': 'private'}, {'fullscreen': True}, {'favorites': 'wrong'},
                      {'navLabels': []}, {'readerWidth': float('nan')}, {'favorites': ['x'*140000]}):
            with self.subTest(value=list(value)):
                with self.assertRaises(ServiceError):
                    save_preferences(self.service, {'preferences': value})
        self.assertIsNone(read_preferences(self.service)['preferences'])

    def test_saved_preferences_are_account_database_rows_without_credentials(self):
        value = {'favorites': ['fixture::B'], 'seenAchievements': ['official-1']}
        save_preferences(self.service, {'preferences': value})
        row = self.service.connection.execute('SELECT key,value,updated_at FROM account_preferences').fetchone()
        self.assertEqual(row['key'], 'ui')
        self.assertEqual(json.loads(row['value']), value)
        self.assertTrue(row['updated_at'].endswith('Z'))

    def test_stale_ui_saves_preserve_individually_read_achievements(self):
        save_preferences(self.service, {'preferences': {'seenAchievements': ['official-1'], 'theme': 'dark'}})
        result = save_preferences(self.service, {'preferences': {'seenAchievements': ['streak-3'], 'theme': 'light'}})
        self.assertEqual(result['preferences']['seenAchievements'], ['official-1', 'streak-3'])
        result = save_preferences(self.service, {'preferences': {'theme': 'dark'}})
        self.assertEqual(result['preferences']['seenAchievements'], ['official-1', 'streak-3'])
        self.assertEqual(result['preferences']['theme'], 'dark')
        with self.assertRaises(ServiceError):
            save_preferences(self.service, {'preferences': {'seenAchievements': [{'id': 'official-1'}]}})

    def test_read_acknowledgements_union_across_two_computers(self):
        from account_sync import baselines, merge_states
        def state(ids, stamp, theme='dark'):
            return {'tables': {'account_preferences': [{'key': 'ui', 'value': json.dumps({'seenAchievements': ids, 'theme': theme}), 'updated_at': stamp}]}, 'publicAccounts': {}}
        original = state(['official-1'], '2026-10-15T00:00:00Z')
        remote = state(['official-1', 'official-10'], '2026-10-16T12:00:00Z', 'light')
        local = state(['official-1', 'streak-3'], '2026-10-16T10:00:00Z')
        merged = merge_states(remote, local, baselines(original))
        preferences = json.loads(merged['tables']['account_preferences'][0]['value'])
        self.assertEqual(set(preferences['seenAchievements']), {'official-1', 'official-10', 'streak-3'})
        self.assertEqual(preferences['theme'], 'light')
        again = merge_states(merged, local, baselines(original))
        self.assertEqual(again['tables']['account_preferences'], merged['tables']['account_preferences'])


if __name__ == '__main__':
    unittest.main()
