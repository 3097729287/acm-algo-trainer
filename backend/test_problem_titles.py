import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from contest_names import normalize_row
from library import LibraryDatabase
from problem_titles import problem_title
from statement_cleanup import clean_statement_markdown


class ProblemTitleTests(unittest.TestCase):
    def test_repeated_source_labels_and_mathematical_titles(self):
        cases = {
            '[入门赛 #53] 买牛奶': '买牛奶',
            '[NOIP 2017 普及组] 成绩': '成绩',
            '【深基2.例5】苹果采购': '苹果采购',
            '[模板] [NOI2026] 最短路 (Easy Version)': '最短路 (Easy Version)',
            '「YLLOI-R4-T2」听妈妈的话': '听妈妈的话',
            '[a,b] 区间求和': '[a,b] 区间求和',
            '[1,n] 的排列': '[1,n] 的排列',
            '[括号序列]': '[括号序列]',
            '$a_i$ 与数组': '$a_i$ 与数组',
        }
        for original, expected in cases.items():
            with self.subTest(original=original):
                self.assertEqual(problem_title(original), expected)
                self.assertEqual(problem_title(expected), expected)
                self.assertEqual(normalize_row({'title': original})['title'], expected)

    def test_old_database_reads_and_future_imports_keep_identity_and_source(self):
        raw = {'题名': '[入门赛 #53] 买牛奶', '场次': '入门赛 53', '题号': 'A'}
        encoded = {'id': 'stable::A', 'title': raw['题名'], 'url': 'https://example.test/problem/A'}
        with TemporaryDirectory() as folder:
            library = LibraryDatabase(Path(folder) / 'library.sqlite3')
            with library.connection() as db:
                db.execute('INSERT INTO problems VALUES (?,?,?,?)', (encoded['id'], encoded['url'], json.dumps(raw), json.dumps(encoded)))
            for entry in [library.find(encoded['id']), library.catalog()[0]]:
                self.assertEqual(entry['encoded']['title'], '买牛奶')
                self.assertEqual(entry['encoded']['id'], encoded['id'])
                self.assertEqual(entry['raw']['场次'], raw['场次'])
                self.assertEqual(entry['raw']['题名'], '买牛奶')
            with library.connection() as db:
                self.assertEqual(json.loads(db.execute('SELECT encoded FROM problems').fetchone()[0])['title'], encoded['title'])
            library.import_records([(raw, encoded, None, None)], {}, {})
            with library.connection() as db:
                saved = json.loads(db.execute('SELECT encoded FROM problems').fetchone()[0])
                self.assertEqual(saved['title'], '买牛奶')
                self.assertEqual(saved['originalTitle'], raw['题名'])
                self.assertEqual(saved['id'], encoded['id'])
                self.assertEqual(saved['url'], encoded['url'])

    def test_advertising_sections_remove_posters_and_retain_hints_and_code(self):
        original = '# [入门赛 #53] 买牛奶\n\n## 描述\n\n买 n 盒牛奶。\n\n## 提示\n\n需要使用整数。\n\n### 广告\n\n洛谷出品的算法教材，官方网店绝赞热卖中！\n\n![教材](https://example.test/book.png)\n\n## 样例\n\n```text\n## 广告\n![数据](sample.png)\n```\n\n## 提示\n\n注意 n=0。'
        result = clean_statement_markdown(original)
        self.assertTrue(result.startswith('# 买牛奶\n'))
        self.assertNotIn('book.png', result)
        self.assertNotIn('洛谷出品', result)
        self.assertIn('需要使用整数。', result)
        self.assertIn('注意 n=0。', result)
        self.assertIn('```text\n## 广告\n![数据](sample.png)\n```', result)
        self.assertEqual(clean_statement_markdown(result), result)
        story = '# 广告\n\n## 题目描述\n\n有 n 个广告牌，每个广告牌宽 ai，求总宽度。'
        self.assertEqual(clean_statement_markdown(story), story)

    def test_ad_paragraph_and_following_image_do_not_remove_real_diagram(self):
        text = '# 题目\n\n## 描述\n\n参考下图。\n\n![图示](diagram.png)\n\n洛谷出品的算法教材，官方网店绝赞热卖中。\n\n![广告](book.png)\n\n## 输入格式\n\n输入 n。'
        result = clean_statement_markdown(text)
        self.assertIn('diagram.png', result)
        self.assertNotIn('book.png', result)
        self.assertIn('输入 n。', result)


if __name__ == '__main__':
    unittest.main()
