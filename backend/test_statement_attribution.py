import unittest
from statement_cleanup import clean_statement_markdown, clean_statement
import hashlib

class AttributionTests(unittest.TestCase):
    def test_repository_only_background_and_source_pointer_are_removed(self):
        original='# osu!mania\n\n来源：[洛谷原题](https://www.luogu.com.cn/problem/P1)\n\n## 题目背景\n\n本题目来自仓库 https://github.com/example/problem/tree/main\n\n## 题目描述\n\n音乐游戏有四种模式。\n\n::align{center}\n\n![游戏界面](picture.png)\n\n::align{left}\n\n## 样例\n\n```text\n1 2\n```'
        result=clean_statement_markdown(original)
        self.assertNotIn('来源：',result);self.assertNotIn('来自仓库',result);self.assertNotIn('## 题目背景',result)
        self.assertNotIn('::align',result);self.assertIn('![游戏界面](picture.png)',result)
        self.assertIn('音乐游戏有四种模式。',result);self.assertIn('```text\n1 2\n```',result)
    def test_meaningful_background_is_not_removed_with_its_source_line(self):
        result=clean_statement_markdown('## 题目背景\n\n本题来自仓库 https://github.com/example/problem\n\n一条道路连接两个城市，每次只能向右移动。\n\n## 输入\n\n一个整数。')
        self.assertIn('## 题目背景',result);self.assertIn('每次只能向右移动',result)
        self.assertNotIn('本题来自仓库',result)
    def test_explanation_with_repository_url_and_code_fences_survives(self):
        original='## 题目背景\n\n本题来自仓库 https://github.com/example/problem ，请使用树上的路径定义操作。\n\n```text\n来源：https://example.com\n::align{left}\n```'
        self.assertEqual(clean_statement_markdown(original),original)
    def test_cleaning_is_idempotent(self):
        original='# task\n\n来源：https://example.com/task\n\n## 题意\n\n求和。'
        result=clean_statement_markdown(original);self.assertEqual(result,clean_statement_markdown(result))

class BundledTranslationTests(unittest.TestCase):
    def test_cleanup_rebases_only_the_exact_matching_bundled_source(self):
        original='# Task\n\nSource: https://example.com/problem\n\n## Description\n\nFind the sum.'
        value={'markdown':original,'translation':{'kind':'bundled','markdown':'求和。',
               'sourceHash':hashlib.sha256(original.encode('utf8')).hexdigest()}}
        result=clean_statement(value)
        self.assertNotIn('Source:',result['markdown'])
        self.assertEqual(result['translation']['sourceHash'],hashlib.sha256(result['markdown'].encode('utf8')).hexdigest())
        self.assertEqual(value['markdown'],original)
        self.assertEqual(result['translation']['markdown'],'求和。')
    def test_stale_or_nonbundled_translation_hash_is_never_renewed(self):
        original='Source: https://example.com/task\n\nCalculate the sum.'
        for kind,checksum in [('bundled','0'*64),('machine',hashlib.sha256(original.encode('utf8')).hexdigest())]:
            result=clean_statement({'markdown':original,'translation':{'kind':kind,'markdown':'求和。','sourceHash':checksum}})
            self.assertEqual(result['translation']['sourceHash'],checksum)

if __name__=='__main__':unittest.main()
