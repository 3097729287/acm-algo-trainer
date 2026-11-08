"""Verify audited editions and keep legacy paired articles independent."""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import unittest

from library import LibraryDatabase
from paths import LIBRARY_SEED


class CompleteEditorialTests(unittest.TestCase):
    def test_all_default_editorials_have_detailed_content(self):
        library = LibraryDatabase(os.environ.get('TB_CHECK_LIBRARY', LIBRARY_SEED), readonly=True)
        root=Path(__file__).resolve().parents[1]
        reviewed=json.loads((root/'data/nowcoder-editorials/reviewed.json').read_text('utf8'))
        with library.connection() as db:
            identities = [row[0] for row in db.execute('SELECT problem_id FROM solutions')]
        self.assertGreaterEqual(len(identities), 809)
        self.assertLessEqual(set(reviewed),set(identities))
        for identity in identities:
            with self.subTest(problem=identity):
                default = library.solution(identity)
                detailed = library.solution(identity, 'detailed')
                # The independently validated Nowcoder delivery has 936 normal
                # articles and 52 detailed articles. Its reviewed per-problem
                # ledger is the edition contract; never synthesize a second
                # copy or silently drop an edition to pass a historical rule.
                if identity in reviewed:
                    proof=reviewed[identity];variants=list(proof['articles'])
                    row=library.find(identity)['encoded']
                    self.assertEqual(row['editorialVariants'],variants)
                    self.assertTrue(row['solutionAvailable'])
                    self.assertEqual(row['detailedSolutionAvailable'],'detailed' in variants)
                    for variant,path in proof['articles'].items():
                        article=library.solution(identity,variant)
                        self.assertIsNotNone(article)
                        self.assertEqual(article['markdown'],(root/path).read_text('utf8'))
                        programs=re.findall(r'^```(?:cpp|cxx|c\+\+|python|python3|py)\s*\n(.*?)^```',article['markdown'],re.M|re.S)
                        self.assertTrue(any(hashlib.sha256(code.encode()).hexdigest()==proof['programSha256'] for code in programs))
                    if 'detailed' not in variants:
                        self.assertIsNone(detailed)
                        continue
                # The contest author's explicit user instruction keeps this
                # sign-in problem in the default edition only. Do not invent a
                # second article just to satisfy the general two-version rule.
                if identity=='remote:codeforces:2278::A':
                    row=library.find(identity)
                    self.assertEqual(row['encoded']['editorialVariants'],['default'])
                    self.assertFalse(row['encoded']['detailedSolutionAvailable'])
                    self.assertIsNone(detailed)
                    self.assertTrue(re.findall(r'```(?:cpp|c\+\+)\s*\n(.*?)```',default['markdown'],re.S))
                    continue
                self.assertIsNotNone(detailed)
                self.assertNotEqual(default['markdown'], detailed['markdown'])
                code = lambda text: [part.strip() for part in re.findall(
                    r'```(?:cpp|c\+\+|python|python3)\s*\n(.*?)```', text, re.S)]
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
