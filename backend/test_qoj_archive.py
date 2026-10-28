import base64
import hashlib
import json
from pathlib import Path
import unittest
from translation import needs_translation


class QojArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(__file__).resolve().parents[1]
        cls.coverage=json.loads((root/'backend/resources/qoj-2025-coverage.json').read_text('utf8'))
        cls.problems={p['id']:p['encoded'] for p in json.loads((root/'data/library/problems.json').read_text('utf8'))}
        cls.statements={p['problem_id']:p['content'] for p in json.loads((root/'data/library/statements.json').read_text('utf8')) if p['problem_id'].startswith('xcpc-qoj::')}

    def test_three_complete_rosters_keep_source_identity_without_guessing_metadata(self):
        for event in ('jinan','zhengzhou','chongqing'):
            rows=[p for p in self.coverage['problems'] if p['event']==event]
            self.assertEqual(len(rows),13)
            self.assertEqual({p['index'] for p in rows},set('ABCDEFGHIJKLM'))
            for item in rows:
                p=self.problems[item['problemId']]
                self.assertEqual((p['problem'],p['title'],p['url']),(item['index'],item['title'],f"https://qoj.ac/problem/{item['id']}"))
                self.assertEqual(p['contestProblemCount'],13);self.assertEqual(p['eventYear'],2025)
                self.assertIsNone(p['difficulty']);self.assertEqual(p['tags'],[])
                self.assertEqual(p['source'],'xcpc-qoj')

    def test_original_pages_and_copyable_samples_are_offline_and_complete(self):
        self.assertEqual(sum(p['pages'] for p in self.coverage['problems']),65)
        self.assertEqual(sum(p['samples'] for p in self.coverage['problems']),57)
        for proof in self.coverage['problems']:
            s=self.statements[proof['problemId']]
            self.assertEqual(s['sourcePdfSha256'],proof['statementSha256'])
            self.assertEqual((s['pageCount'],len(s['images'])),(proof['pages'],proof['pages']))
            for data in s['images'].values():
                self.assertTrue(base64.b64decode(data.split(',',1)[1],validate=True).startswith(b'\x89PNG\r\n\x1a\n'))
            self.assertEqual(len(s['samples']),proof['samples'])
            digest=hashlib.sha256(json.dumps(s['samples'],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
            self.assertEqual(digest,proof['sampleSha256'])
            self.assertFalse(needs_translation(s))
            self.assertGreater(s['limits']['timeMs'],0);self.assertGreater(s['limits']['memoryMb'],0)

    def test_cryptography_and_vertical_samples_keep_large_integer_bytes(self):
        s=self.statements['xcpc-qoj::15032']['samples'][0]
        self.assertIn('1000000007 1000000009',s['input'])
        self.assertEqual(s['output'],'2\n3\n994996658310742016\nbroken message\nbroken message')
        s=self.statements['xcpc-qoj::15425']['samples'][0]
        self.assertIn('104857601998244353 1145141919810 3141592653589793 27182818284590452',s['input'])
        self.assertEqual(s['output'],'41\n35\n35\n6\n377005672062684')


if __name__=='__main__':unittest.main()
