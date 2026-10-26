import json
from pathlib import Path
import unittest
from catalog_metadata import supplement
from contest_names import normalize_row, contest_name


class CatalogMetadataTests(unittest.TestCase):
    def test_all_bundled_rows_have_auditable_difficulty_or_explicit_unknown(self):
        root=Path(__file__).resolve().parents[1]
        rows=json.loads((root/'data/library/problems.json').read_text(encoding='utf8'))
        for entry in rows:
            row=entry['encoded']
            if row.get('difficulty') is None:
                self.assertTrue(row.get('difficultySource'), row['id'])
                self.assertIn(row.get('difficultyConfidence'), ('UNKNOWN', 'LOW'))
            else:
                self.assertIsInstance(row['difficulty'], int, row['id'])
                self.assertTrue(row.get('difficultySource'), row['id'])
                self.assertIn('difficultyEstimated', row, row['id'])
            if row.get('source') == 'luogu-training' and not row.get('tags'):
                self.assertTrue(row.get('knowledgeReviewRequired'), row['id'])
                self.assertEqual(row.get('knowledgeCategories'), [], 'missing original tags must not invent an algorithm')
            elif row.get('source') != 'xcpc-codeforces':
                self.assertTrue(row.get('tags') or row.get('knowledgeCategories'),row['id'])
            self.assertEqual((entry['raw']['状态'],entry['raw']['日期']),('未做',''))

    def test_subject_model_does_not_invent_an_algorithm(self):
        row=supplement({'id':'fixture','source':'remote','tags':[]},'# Task\nGiven a sequence of integers, maximize its score.')
        self.assertIn('数学',row['knowledgeCategories'])
        self.assertNotIn('线性 DP',row['tags'])
        self.assertIsNone(row.get('difficulty'))

    def test_low_acceptance_does_not_create_extreme_or_fictitious_rating(self):
        from difficulty import nowcoder
        row = {'contest': '周赛 166', 'url': 'https://ac.nowcoder.com/acm/contest/1/F'}
        self.assertIsNone(nowcoder(row, {'acceptedCount': 0}, 1000)['difficulty'])
        value = nowcoder(row, {'acceptedCount': 30}, 1000)
        self.assertLess(value['difficulty'], 2300)
        self.assertTrue(value['difficultyEstimated'])
        self.assertEqual(value['difficultyConfidence'], 'LOW')

    def test_reviewed_weekly_tasks_keep_algorithm_evidence(self):
        from difficulty import nowcoder
        for letter, expected in (('E', 1900), ('F', 2100)):
            value = nowcoder({'url': 'https://ac.nowcoder.com/acm/contest/141721/' + letter})
            self.assertEqual(value['difficulty'], expected)
            self.assertTrue(value['difficultyEstimated'])
            self.assertEqual(value['difficultyConfidence'], 'MEDIUM')
            self.assertGreater(len(value['difficultyEvidence']), 1)

    def test_existing_official_rating_is_preserved(self):
        row=supplement({'id':'fixture','tags':['贪心'],'difficulty':1400,'difficultyEstimated':False},'')
        self.assertEqual(row['difficulty'],1400)
        self.assertFalse(row['difficultyEstimated'])

    def test_naming_keeps_identity_and_removes_source_prefixes(self):
        row=normalize_row({'id':'old::A','contest':'牛客周赛 Round 165','title':'[ICPC 2019 Yinchuan R] Girls Band Party'})
        self.assertEqual(row['id'],'old::A')
        self.assertEqual(row['contest'],'周赛 165')
        self.assertEqual(row['title'],'Girls Band Party')
        self.assertEqual(normalize_row({'title':'[模板] 最短路','contest':'模板题'})['title'],'最短路')
        self.assertEqual(contest_name('“海康威视杯” 2022年第十四届四川省大学生程序设计大赛（热身赛）'),'四川省赛 2022（热身赛）')
        self.assertEqual(contest_name('第 45 届国际大学生程序设计竞赛（ICPC）亚洲区域赛（南京）'),'ICPC 2020 南京区域赛')
        self.assertNotEqual(contest_name('2023年ICPC新疆赛区'), contest_name('2023年CCPC新疆赛区'))
        self.assertNotEqual(contest_name('2024 ICPC Asia Taiwan Online Programming Contest'), contest_name('2024 ICPC Asia Japan Online First-Round Contest'))
        variant = normalize_row({'contest': 'ICPC 2026 南昌邀请赛', 'contestVariant': 'Gym 106554'})
        self.assertEqual(normalize_row(variant)['contest'], variant['contest'])


if __name__=='__main__':unittest.main()
