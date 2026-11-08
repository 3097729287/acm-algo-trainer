import json
from pathlib import Path
import unittest
from difficulty import normalize_practice_difficulty, round_difficulty, OYSTER_URL

class DifficultyScaleTests(unittest.TestCase):
    def test_all_public_ratings_use_hundreds(self):
        root=Path(__file__).resolve().parents[1]
        rows=json.loads((root/'data/library/problems.json').read_text('utf-8'))
        for item in rows:
            value=item['encoded'].get('difficulty')
            if value is not None: self.assertEqual(value % 100,0,item['id'])

    def test_rounding_preserves_source_native_and_unknown(self):
        row={'difficulty':1350,'nativeDifficulty':4,'difficultySource':'provider band','difficultyEstimated':True}
        result=normalize_practice_difficulty(row)
        self.assertEqual(result['difficulty'],1400)
        self.assertEqual(result['difficultyBeforeRounding'],1350)
        self.assertEqual(result['nativeDifficulty'],4)
        self.assertEqual(row['difficulty'],1350)
        self.assertIsNone(normalize_practice_difficulty({'difficulty':None})['difficulty'])
        self.assertEqual(normalize_practice_difficulty(result),result)

    def test_official_nowcoder_values_remain_auditable_after_display_rounding(self):
        row={'difficulty':1105,'difficultySource':'牛客公开题库数值评级','difficultyEstimated':False,'difficultyEvidence':['https://ac.nowcoder.com/acm/problem/18929','原站难度 1105，非通过人数']}
        value=round_difficulty(row)
        self.assertEqual(value['difficulty'],1100)
        self.assertEqual(value['difficultyBeforeRounding'],1105)
        self.assertEqual(value['difficultySource'],row['difficultySource'])
        self.assertEqual(value['difficultyEvidence'],row['difficultyEvidence'])
        self.assertFalse(value['difficultyEstimated']);self.assertEqual(row['difficulty'],1105)

    def test_review_overrides_stale_team_estimate_but_not_official_rating(self):
        row={'url':OYSTER_URL,'difficulty':1400,'difficultyEstimated':True}
        self.assertEqual(normalize_practice_difficulty(row)['difficulty'],1000)
        row.update(difficultyEstimated=False,difficultySource='Codeforces 官方 rating')
        self.assertEqual(normalize_practice_difficulty(row)['difficulty'],1400)

    def test_reviewed_oyster_greedy_against_exhaustive_choices(self):
        for budget in range(81):
            for single in range(1,8):
                for dozen in range(1,20):
                    greedy=budget//single if dozen>=12*single else budget//dozen*12+(budget%dozen)//single
                    exact=max(12*packs+(budget-dozen*packs)//single for packs in range(budget//dozen+1))
                    self.assertEqual(greedy,exact)

    def test_frozen_atcoder_models_keep_unofficial_provenance_and_missing_values(self):
        root=Path(__file__).resolve().parents[1]
        review=json.loads((root/'content-updates/20261108-metadata/atcoder-models.json').read_text('utf8'))
        metadata=json.loads((root/'backend/resources/public-problem-metadata.json').read_text('utf8'))
        for task,native,rating in [('abc396_e',1379,1600),('abc292_h',2248,2200),('arc100_c',2111,2100)]:
            value=metadata[f'https://atcoder.jp/contests/{task.split("_")[0]}/tasks/{task}']
            self.assertEqual(value['nativeDifficulty'],native)
            self.assertEqual(value['difficulty'],rating)
            self.assertTrue(value['difficultyEstimated'])
            self.assertIn('AtCoder Problems',value['difficultySource'])
            self.assertIn('模型估算',value['difficultySource'])
            self.assertIn(review['source'],value['difficultyEvidence'])
            self.assertIn('原始数据 SHA-256: '+review['sha256'],value['difficultyEvidence'])
        self.assertIsNone(review['selected']['practice2_j'])
        self.assertIsNone(review['selected']['joi2007ho_a'])
        self.assertNotIn('difficulty',review['selected']['dp_v'])
