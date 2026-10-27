import unittest
import test_training as fixtures
from preferences import read_preferences,save_preferences
from training import ServiceError

class DifficultyPreferenceTests(unittest.TestCase):
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown

    def test_exclusive_display_choice_roundtrips_and_rejects_bad_values_atomically(self):
        for mode in ['number','text','number']:
            saved=save_preferences(self.service,{'preferences':{'difficultyDisplay':mode,'favorites':['fixture::A']}})
            self.assertEqual(saved['preferences']['difficultyDisplay'],mode)
            self.assertEqual(read_preferences(self.service),saved)
        for mode in ['both',None,False,900]:
            with self.assertRaises(ServiceError):save_preferences(self.service,{'preferences':{'difficultyDisplay':mode}})
        self.assertEqual(read_preferences(self.service)['preferences'],{'difficultyDisplay':'number','favorites':['fixture::A']})
