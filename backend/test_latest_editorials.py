"""The requested recent rounds have independent, portable detailed editorials."""
import base64
import re
import unittest

from library import LibraryDatabase
from paths import LIBRARY_SEED

SCOPE = {
    '周赛 165': 'ABCDEF', '周赛 164': 'ABCDEFG', '周赛 163': 'ABCDEFG',
    '周赛 162': 'ABCDEF',
    'Div.3 1125': 'BCDEFG', 'Div.3 1122': 'BCDEF', 'Div.3 1119': 'CDEFG',
    'Div.2 1127': 'BCD', 'Div.2 1124': 'BCD', 'Div.2 1123': 'BCDEF1',
    'Div.4 1090': 'CDEFG', 'Div.4 1074': 'CDEFG', 'Div.4 1062': 'CDEFG',
    'ABC 479': 'CDEF', 'ABC 478': 'CDEF', 'ABC 477': 'CDEFG',
}


class LatestEditorialTests(unittest.TestCase):
    def test_requested_rounds_have_distinct_explanations_and_identical_verified_code(self):
        library = LibraryDatabase(LIBRARY_SEED, readonly=True)
        count = 0
        for contest, letters in SCOPE.items():
            for letter in re.findall(r'[A-Z][0-9]?', letters):
                identity = contest + '::' + letter
                with self.subTest(problem=identity):
                    default = library.solution(identity)
                    detailed = library.solution(identity, 'detailed')
                    self.assertIsNotNone(default)
                    self.assertIsNotNone(detailed)
                    self.assertNotEqual(default['markdown'], detailed['markdown'])
                    # Reviewed derivations can be clearer without being longer.
                    # Keep substantial, distinct prose, identical code and images.
                    self.assertGreater(len(detailed['markdown']), 300)
                    self.assertGreater(len(default['markdown']), 300)
                    code = lambda text: [part.strip() for part in re.findall(r'```(?:cpp|c\+\+)\s*\n(.*?)```', text, re.S)]
                    self.assertTrue(code(default['markdown']))
                    self.assertEqual(code(default['markdown']), code(detailed['markdown']))
                    for target in re.findall(r'!\[[^\]]*\]\(([^)]+)\)', detailed['markdown']):
                        if not target.startswith(('https://', 'http://', 'data:')):
                            self.assertIn(target, detailed['images'])
                            self.assertTrue(base64.b64decode(detailed['images'][target].split(',', 1)[1]))
                    count += 1
        self.assertEqual(count, 81)


if __name__ == '__main__':
    unittest.main()
