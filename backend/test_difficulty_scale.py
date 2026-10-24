import json
from pathlib import Path
import unittest
from difficulty import normalize_practice_difficulty, OYSTER_URL

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
