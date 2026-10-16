"""Every bundled default editorial has a portable, independent detailed version."""
import base64
import re
import unittest

from library import LibraryDatabase
from paths import LIBRARY_SEED


class CompleteEditorialTests(unittest.TestCase):
    def test_all_default_editorials_have_detailed_content(self):
        library = LibraryDatabase(LIBRARY_SEED, readonly=True)
        with library.connection() as db:
            identities = [row[0] for row in db.execute('SELECT problem_id FROM solutions')]
        self.assertGreaterEqual(len(identities), 809)
        for identity in identities:
            with self.subTest(problem=identity):
                default = library.solution(identity)
                detailed = library.solution(identity, 'detailed')
                self.assertIsNotNone(detailed)
                self.assertNotEqual(default['markdown'], detailed['markdown'])
                code = lambda text: [part.strip() for part in re.findall(
                    r'```(?:cpp|c\+\+)\s*\n(.*?)```', text, re.S)]
                default_code, detailed_code = code(default['markdown']), code(detailed['markdown'])
                self.assertTrue(default_code)
                # An older detailed article also includes a short annotated excerpt.
                # Its complete reference program must still match the default version.
                for program in default_code:
                    self.assertIn(program, detailed_code)
                for target in re.findall(r'!\[[^\]]*\]\(([^)]+)\)', detailed['markdown']):
                    if not target.startswith(('https://', 'http://', 'data:')):
                        self.assertIn(target, detailed['images'])
                        self.assertTrue(base64.b64decode(detailed['images'][target].split(',', 1)[1]))


if __name__ == '__main__':
    unittest.main()
