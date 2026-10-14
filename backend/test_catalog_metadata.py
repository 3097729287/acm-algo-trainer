import json
from pathlib import Path
import unittest
from catalog_metadata import supplement
from contest_names import normalize_row, contest_name


class CatalogMetadataTests(unittest.TestCase):
    def test_all_bundled_rows_have_classification_and_rating(self):
        root=Path(__file__).resolve().parents[1]
        rows=json.loads((root/'data/library/problems.json').read_text(encoding='utf8'))
        for entry in rows:
            row=entry['encoded']
            self.assertIsInstance(row.get('difficulty'),int,row['id'])
            self.assertTrue(row.get('tags') or row.get('knowledgeCategories'),row['id'])
            self.assertEqual((entry['raw']['状态'],entry['raw']['日期']),('未做',''))

    def test_subject_model_does_not_invent_an_algorithm(self):
        row=supplement({'id':'fixture','source':'remote','tags':[]},'# Task\nGiven a sequence of integers, maximize its score.')
        self.assertIn('数学',row['knowledgeCategories'])
        self.assertNotIn('线性 DP',row['tags'])
        self.assertTrue(row['difficultyEstimated'])
        self.assertEqual(row['difficultyConfidence'],'LOW')

    def test_existing_official_rating_is_preserved(self):
        row=supplement({'id':'fixture','tags':['贪心'],'difficulty':1400,'difficultyEstimated':False},'')
        self.assertEqual(row['difficulty'],1400)
        self.assertFalse(row['difficultyEstimated'])

    def test_naming_keeps_identity_and_template_prefix(self):
        row=normalize_row({'id':'old::A','contest':'牛客周赛 Round 165','title':'[ICPC 2019 Yinchuan R] Girls Band Party'})
        self.assertEqual(row['id'],'old::A')
        self.assertEqual(row['contest'],'周赛 165')
        self.assertEqual(row['title'],'Girls Band Party')
        self.assertEqual(normalize_row({'title':'[模板] 最短路','contest':'模板题'})['title'],'[模板] 最短路')
        self.assertEqual(contest_name('“海康威视杯” 2022年第十四届四川省大学生程序设计大赛（热身赛）'),'四川省赛 2022（热身赛）')
        self.assertEqual(contest_name('第 45 届国际大学生程序设计竞赛（ICPC）亚洲区域赛（南京）'),'ICPC 2020 南京区域赛')
        self.assertNotEqual(contest_name('2023年ICPC新疆赛区'), contest_name('2023年CCPC新疆赛区'))


if __name__=='__main__':unittest.main()
