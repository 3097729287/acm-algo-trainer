"""Published ratings retain their provenance and reviewed algorithms survive overlays."""
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import unittest

import backend
from knowledge import enrich_row

ROOT=Path(__file__).resolve().parents[1]

class MetadataReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit=json.loads((ROOT/'backend/resources/metadata-review-1423.json').read_text(encoding='utf8'))
        ids={r['id'] for key in ('official','estimated','knowledgeReviews') for r in cls.audit.get(key,[])}
        ids.update(r['primaryId'] for r in cls.audit['official'] if r.get('sourceKind') in ('official-identical-statement','official-reviewed-statement'))
        cls.problems={p['id']:p for p in json.loads((ROOT/'data/library/problems.json').read_text(encoding='utf8')) if p['id'] in ids}
        cls.statements={p['problem_id']:p['content'] for p in json.loads((ROOT/'data/library/statements.json').read_text(encoding='utf8')) if p['problem_id'] in ids}
        cls.overlay=json.loads((ROOT/'backend/resources/public-problem-metadata.json').read_text(encoding='utf8'))
        cls.solutions={p['problem_id']:p['markdown'] for p in json.loads((ROOT/'data/library/solutions.json').read_text(encoding='utf8')) if p['problem_id'] in ids}
        cls.retired={p['id']:p for p in json.loads((ROOT/'backend/resources/excluded-xcpc.json').read_text('utf8'))['problems']}

    def retained(self, identity):
        if identity in self.problems:return True
        # Historical evidence is retained, while the user removed these public
        # tasks. Absence is allowed only with explicit foreign/WF provenance.
        from contest_scope import excluded
        self.assertIn(identity,self.retired)
        entry=self.retired[identity]
        self.assertTrue(excluded({k:entry[k] for k in ('contest','originalTitle')}))
        return False

    def test_verified_scores_and_estimates_never_lose_their_distinction(self):
        seen=set()
        for kind in ('official','estimated'):
            for review in self.audit[kind]:
                self.assertNotIn(review['id'],seen);seen.add(review['id'])
                if not self.retained(review['id']):continue
                p=self.problems[review['id']];row=p['encoded']
                self.assertEqual(row['difficulty'],review['rating'])
                self.assertEqual(row['difficultyEstimated'],kind=='estimated')
                self.assertEqual(self.overlay[p['url']]['difficulty'],review['rating'])
                lo,hi=row['difficultyBand'];self.assertLessEqual(lo,row['difficulty']);self.assertLessEqual(row['difficulty'],hi)
                if kind=='official':
                    self.assertEqual([lo,hi],[review['rating']]*2)
                    self.assertIn('codeforces.com/',review['source'])
                else:
                    self.assertTrue(re.fullmatch('[0-9a-f]{64}',review['editorialSha256']))
                    self.assertTrue(review['reason'])
                    self.assertTrue(row['difficultyReviewed'])
                    self.assertEqual(row['difficultyReviewSha256'],review['editorialSha256'])
                    if review.get('sourceKind') in ('published-editorial','published-reference','self-reviewed-statement'):
                        proof=next(x for x in self.audit['knowledgeReviews'] if x['id']==review['id'])
                        self.assertEqual(proof['source'],review['source'])
                        self.assertEqual(proof['editorialSha256'],review['editorialSha256'])
                    elif review['id'] in self.solutions:
                        self.assertEqual(hashlib.sha256(self.solutions[review['id']].encode('utf8')).hexdigest(),review['editorialSha256'])

    def test_independent_algorithm_estimates_bind_to_the_actual_statement(self):
        estimates={x['id']:x for x in self.audit['estimated']}
        for proof in self.audit.get('knowledgeReviews',[]):
            if proof.get('sourceKind')!='self-reviewed-statement':continue
            pid=proof['id']
            if not self.retained(pid):continue
            row=self.problems[pid];statement=self.statements[pid]
            self.assertTrue(statement['statementAvailable'])
            digest=hashlib.sha256(statement['markdown'].encode('utf8')).hexdigest()
            self.assertEqual(proof['statementSha256'],digest)
            self.assertEqual(proof['editorialSha256'],digest)
            self.assertEqual(proof['source'],row['url'])
            self.assertTrue(proof['reason'] and proof['reviewed'])
            self.assertTrue(row['encoded']['difficultyEstimated'])
            self.assertEqual(row['encoded']['difficultyReviewKind'],'self-reviewed-statement')
            self.assertEqual(estimates[pid]['statementSha256'],digest)

    def test_reviewed_techniques_survive_encoding_and_remove_superseded_labels(self):
        for review in self.audit['estimated']:
            if not self.retained(review['id']):continue
            row=enrich_row(self.problems[review['id']]['encoded'])
            self.assertTrue(set(review['tags'])<=set(row['tags']),review['id'])
            self.assertTrue(row['tags'],review['id'])
        tree=enrich_row(self.problems['练习赛 152::E']['encoded'])
        self.assertNotIn('LCA',tree['tags'],'the reviewed subtree-count DP does not use LCA')

    def test_official_mirrors_bind_to_identical_full_statements_not_just_names(self):
        def canonical(markdown):
            return re.sub(r'\s+','',unicodedata.normalize('NFKC','\n'.join(markdown.splitlines()[1:])))
        for review in self.audit['official']:
            if review.get('sourceKind')!='official-identical-statement':continue
            if not self.retained(review['id']) or not self.retained(review['primaryId']):continue
            original=self.statements[review['id']];primary=self.statements[review['primaryId']]
            for statement in (original,primary):
                self.assertTrue(statement['statementAvailable'])
                self.assertIn('## Input',statement['markdown']);self.assertIn('## Output',statement['markdown'])
            self.assertEqual(original['limits'],primary['limits'])
            self.assertEqual(canonical(original['markdown']),canonical(primary['markdown']))
            self.assertEqual(hashlib.sha256(canonical(original['markdown']).encode()).hexdigest(),review['statementSha256'])
            self.assertEqual(hashlib.sha256(original['markdown'].encode()).hexdigest(),review['originalMarkdownSha256'])
            self.assertEqual(hashlib.sha256(primary['markdown'].encode()).hexdigest(),review['primaryMarkdownSha256'])
            self.assertEqual(review['samplesIdentical'],original.get('samples')==primary.get('samples'))
            self.assertEqual(review['source'],self.problems[review['primaryId']]['url'])

    def test_luogu_cf_references_bind_to_explicit_original_indices_and_api_records(self):
        from rating_evidence import evidence
        public=json.loads((ROOT/'backend/resources/official-cf-references.json').read_text(encoding='utf8'))
        self.assertEqual(public['source'],'https://codeforces.com/api/problemset.problems')
        for review in self.audit['official']:
            if review.get('sourceKind')!='official-index-reference':continue
            p=self.problems[review['id']];row=p['encoded']
            match=re.fullmatch(r'https://www\.luogu\.com\.cn/problem/CF([1-9][0-9]*)([A-Z][0-9]?)',p['url'])
            self.assertIsNotNone(match)
            record=public['records']['CF'+match[1]+match[2]]
            self.assertEqual((record['contestId'],record['index'],record['rating']),(int(match[1]),match[2],review['rating']))
            encoded=json.dumps(record,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf8')
            self.assertEqual(hashlib.sha256(encoded).hexdigest(),review['primaryRecordSha256'])
            self.assertEqual(review['mirrorUrl'],p['url'])
            self.assertEqual(review['primaryReference'],row['difficultyOfficialReference'])
            self.assertEqual(review['source'],row['difficultyOfficialReference']['source'])
            self.assertEqual(review['metadataSource'],public['source'])
            self.assertEqual(evidence(row)['kind'],'official-cf')
            self.assertEqual([evidence(row)['lower'],evidence(row)['upper']],[review['rating']]*2)
        self.assertEqual(self.problems['luogu-training-CF1000E']['encoded']['difficulty'],2100)

    def test_reviewed_mirrors_allow_only_the_six_verified_clarification_differences(self):
        from statement_equivalence import REVIEWED_PAIRS,canonical_reviewed_statement,canonical_samples
        decisions=[r for r in self.audit['official'] if r.get('sourceKind')=='official-reviewed-statement']
        self.assertEqual({r['id'] for r in decisions},set(REVIEWED_PAIRS))
        for proof in decisions:
            pid=proof['id'];primary_id,cid,letter=REVIEWED_PAIRS[pid]
            self.assertEqual(proof['primaryId'],primary_id)
            self.assertEqual(proof['source'],f'https://codeforces.com/contest/{cid}/problem/{letter}')
            if not self.retained(pid) or not self.retained(primary_id):continue
            a,b=self.statements[pid],self.statements[primary_id]
            self.assertTrue(a['statementAvailable'] and b['statementAvailable'])
            self.assertEqual(a['limits'],b['limits'])
            self.assertEqual(canonical_samples(a.get('samples')),canonical_samples(b.get('samples')))
            text=canonical_reviewed_statement(pid,a['markdown'])
            self.assertEqual(text,canonical_reviewed_statement(pid,b['markdown']))
            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),proof['statementSha256'])
            self.assertEqual(hashlib.sha256(a['markdown'].encode()).hexdigest(),proof['originalMarkdownSha256'])
            self.assertEqual(hashlib.sha256(b['markdown'].encode()).hexdigest(),proof['primaryMarkdownSha256'])
            self.assertNotEqual(text,canonical_reviewed_statement(pid,a['markdown']+'\nAll input values must be even.'))
        with self.assertRaises(ValueError):
            canonical_reviewed_statement('unreviewed','Hacks are forbidden in this problem.')

    def test_world_final_tags_do_not_spill_across_page_boundaries(self):
        expectations={
            'remote:codeforces:101471::B':({'枚举','折半枚举','位运算'},{'并查集','二分图匹配','二分查找','扫描线'}),
            'remote:codeforces:101471::I':({'Floyd','DFS'},{'期望与概率'}),
            'remote:codeforces:101471::L':({'扫描线','平衡树'},{'KMP','哈希'}),
            'remote:codeforces:102482::E':({'BFS','计算几何'},{'凸包','双指针'}),
            'remote:codeforces:102511::E':({'拓扑排序','BFS'},{'扫描线','字典树','二分查找'}),
            'remote:codeforces:102511::H':({'功能图','树形 DP','差分'},{'期望与概率'}),
            'remote:codeforces:103409::C':({'虚树','分块','LCA'},{'AC自动机'}),
            'remote:codeforces:103409::J':({'后缀树','后缀数组'},{'后缀自动机'}),
            'remote:codeforces:103415::F':({'多项式插值','递推'},{'图论'}),
            'remote:codeforces:103428::A':({'模拟'},{'树形 DP'}),
            'remote:codeforces:104373::K':({'并查集','Kruskal'},{'LCT','Link-Cut Tree'}),
            'remote:codeforces:103446::I':({'背包 DP','滚动数组'},{'计算几何'}),
            'remote:codeforces:103446::H':({'Kruskal重构树','倍增'},{'期望与概率'}),
            'remote:nowcoder:21592::H':({'博弈论','模拟'},{'计算几何'}),
            'remote:nowcoder:21592::I':({'树形 DP','最短路'},{'LCT','树链剖分'}),
            'remote:codeforces:103430::I':({'费用流','离散化'},{'模拟'}),
            'remote:codeforces:103430::N':({'模拟'},{'博弈论'}),
            'remote:codeforces:104013::E':({'欧拉路径','DFS'},{'并查集'}),
            'remote:codeforces:106225::E':({'前缀和','计算几何'},{'BFS'}),
            'remote:codeforces:106225::H':({'博弈论','递推'},{'矩阵运算','分治优化 DP'}),
            'remote:codeforces:106225::L':({'前缀和','DFS'},{'后缀数组','KMP'}),
            'remote:codeforces:104772::M':({'双指针','贪心'},{'线性 DP'}),
            'remote:codeforces:105537::L':({'状压 DP','位运算'},{'后缀数组','后缀自动机'}),
            'remote:codeforces:104059::F':({'平面图','BFS'},{'计算几何','扫描线'}),
            'remote:codeforces:104466::J':({'置换环','线段树'},{'期望与概率'}),
            'ABC 481::A':({'枚举','模拟'},{'计算几何'}),
            'ABC 481::C':({'哈希','模拟'},{'计算几何'}),
            'remote:codeforces:104666::E':({'计算几何','扫描线'},{'GCD','ST 表','分治'}),
            'remote:codeforces:104666::K':({'计算几何','线段相交'},{'GCD','ST 表'}),
        }
        for identity,(present,absent) in expectations.items():
            if not self.retained(identity):continue
            row=enrich_row(self.problems[identity]['encoded'])
            self.assertTrue(present<=set(row['tags']),identity)
            self.assertFalse(absent&set(row['tags']),identity)
            if identity in ('ABC 481::A','ABC 481::C'):
                self.assertNotIn('计算几何',row['knowledgeCategories'],identity)

if __name__=='__main__':unittest.main()
