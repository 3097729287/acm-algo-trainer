"""All bundled Wiki problem links resolve without inventing judge evidence."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
from insights import canonical_url
from contest_scope import excluded

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from import_wiki_examples import collect,prepare

class WikiExampleTests(unittest.TestCase):
    def test_all_bundled_links_reuse_or_add_one_exact_catalogue_identity(self):
        _,entries=collect()
        manifest=json.loads((ROOT/'backend/resources/wiki-examples.json').read_text(encoding='utf-8'))
        problems=json.loads((ROOT/'data/library/problems.json').read_text(encoding='utf-8'))
        rows={row['id']:row for row in problems}
        self.assertEqual(manifest['wikiSha256'],hashlib.sha256((ROOT/'backend/resources/oi-wiki.sqlite3').read_bytes()).hexdigest())
        self.assertEqual(set(entries),{item['identity'] for item in manifest['entries']})
        self.assertEqual(len(entries),110)
        for item in manifest['entries']:
            row=rows[item['problemId']]
            self.assertEqual(canonical_url(row['url']),item['identity'])
            self.assertTrue(item['references'])
            if row['encoded'].get('wikiExample'):
                self.assertIsNone(row['encoded']['difficulty'])
                self.assertFalse(row['encoded']['catalogStatementReady'])
                self.assertFalse(row['encoded']['catalogReplayReady'])
                self.assertFalse(excluded(row),'Explicit Wiki examples remain visible under the requested catalogue scope')
                self.assertEqual(row['encoded']['difficultyConfidence'],'UNKNOWN')
                self.assertTrue(row['encoded']['knowledgeReviewRequired'])
        _,added,rebuilt=prepare()
        self.assertEqual(added,[])
        self.assertEqual(rebuilt,manifest,'Repeated indexing must not duplicate or rewrite catalogue identities')

    def test_query_based_judges_keep_distinct_problems_and_same_problem_aliases(self):
        for first,second in [
            ('https://poj.org/problem?id=1','https://poj.org/problem?id=2'),
            ('https://acm.hdu.edu.cn/showproblem.php?pid=1','https://acm.hdu.edu.cn/showproblem.php?pid=2'),
            ('https://onlinejudge.org/index.php?problem=1','https://onlinejudge.org/index.php?problem=2')]:
            self.assertNotEqual(canonical_url(first),canonical_url(second))
        self.assertEqual(canonical_url('https://uva.onlinejudge.org/index.php?option=com_onlinejudge&problem=4222'),canonical_url('http://onlinejudge.org/index.php?problem=4222&Itemid=8'))
        self.assertEqual(canonical_url('https://codeforces.com/gym/100963/problem/j'),'codeforces.com/gym/100963/problem/J')
