import copy
from collections import Counter
import json
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest

from translation import TranslationService,bundled_translation,protect,validate_translation


class ReviewedCorrectionTests(unittest.TestCase):
    def test_constructive_gcd_is_complete_offline_and_keeps_touching_formulas(self):
        problem=json.loads((Path(__file__).parent/'fixtures/translations/disgusting-gcd-constructive.json').read_text(encoding='utf8'))
        translated=bundled_translation(problem)
        self.assertIsNotNone(translated)
        self.assertIn('你的力量所剩不多',translated['markdown'])
        self.assertIn('每组测试用例',translated['markdown'])
        self.assertIn('在第二个样例中',translated['markdown'])
        self.assertEqual(Counter(protect(problem['markdown'])[1].values()),Counter(protect(translated['markdown'])[1].values()))
        validate_translation(problem['markdown'],translated['markdown'])
        self.assertIsNone(bundled_translation(dict(problem,markdown=problem['markdown']+' source updated')))

    def test_rhythmic_string_works_offline_and_preserves_the_original(self):
        problem=json.loads((Path(__file__).parent/'fixtures/translations/rhythmic-string.json').read_text(encoding='utf8'))
        before=copy.deepcopy(problem)
        translated=bundled_translation(problem)
        self.assertIsNotNone(translated)
        self.assertNotIn('defaultLanguage',translated)
        self.assertIn('有节奏',translated['markdown'])
        immutable=lambda text:Counter(span for span in protect(text)[1].values() if not span.isspace() and span not in ('# ','## ','- '))
        self.assertEqual(immutable(problem['markdown']),immutable(translated['markdown']))
        validate_translation(problem['markdown'],translated['markdown'])
        assets=SimpleNamespace(lock=threading.RLock(),_cached=lambda _:problem)
        with tempfile.TemporaryDirectory() as temporary:
            service=TranslationService(assets,Path(temporary),provider=lambda _:self.fail('No translation API should be used'))
            self.assertEqual(service.translate(problem['id'])['markdown'],translated['markdown'])
        self.assertEqual(problem,before)
        self.assertIsNone(bundled_translation(dict(problem,markdown=problem['markdown']+' revised')))
        self.assertIsNone(bundled_translation(dict(problem,url='https://codeforces.com/contest/2283/problem/A')))
