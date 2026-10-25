import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from statement_cleanup import clean_statement, clean_statement_markdown
from library import LibraryDatabase
from public_platforms import statement
from store import Store

NOTICE='在学术版与题目总版内发帖、回复需要达到 [受信任的用户](https://www.luogu.com.cn/discuss) 的权限，在洛谷经常做题、参与比赛即可快速达到该权限等级。'


class StatementCleanupTests(unittest.TestCase):
    def test_notice_removed_empty_heading_removed_required_background_untouched(self):
        text='# Hello,World!\n\n## 题目背景\n\n'+NOTICE+'\n\n## 题目描述\n\n输出 `Hello,World!`。'
        self.assertEqual(clean_statement_markdown(text),'# Hello,World!\n\n## 题目描述\n\n输出 `Hello,World!`。')
        story='# 授权\n\n## 题目背景\n\n有 n 个用户，每人的权限等级是 ai，统计能访问文档的用户数量。\n\n## 输入格式\n\n$n, a_i$'
        self.assertEqual(clean_statement_markdown(story),story)
        mixed='# 题目\n\n## 题目背景\n\n'+NOTICE+'\n\n树有 n 个节点，相邻节点可通行。\n\n## 描述\n\n求最短路。'
        self.assertIn('## 题目背景\n\n树有 n 个节点',clean_statement_markdown(mixed))

    def test_code_samples_translation_and_read_write_boundary(self):
        code='```text\n'+NOTICE+'\n\n第二段\n```'
        self.assertEqual(clean_statement_markdown(code),code)
        value={'id':'x','markdown':NOTICE+'\n\n## 描述\n\n输出1。','samples':[{'input':'','output':'1\n'}],'limits':{'timeMs':1000},'translation':{'markdown':NOTICE+'\n\n描述','kind':'site'}}
        cleaned=clean_statement(value)
        self.assertEqual(value['samples'],cleaned['samples']);self.assertEqual(value['limits'],cleaned['limits'])
        self.assertNotIn(NOTICE,cleaned['translation']['markdown'])
        with TemporaryDirectory() as folder:
            db=LibraryDatabase(Path(folder)/'library.sqlite3')
            with db.connection() as connection:connection.execute('INSERT INTO statements VALUES (?,?)',('x',json.dumps(value)))
            self.assertNotIn(NOTICE,db.statement('x')['markdown'])
            db.save_statement('x',value)
            with db.connection() as connection:self.assertNotIn(NOTICE,connection.execute('SELECT content FROM statements').fetchone()[0])

    def test_luogu_open_makes_only_one_network_request(self):
        class Client:
            def __init__(self):self.calls=[]
            def json(self,url,headers=None):
                self.calls.append(url)
                if '/_lfe/tags' in url:raise AssertionError('Optional tag lookup blocked the statement')
                return {'data':{'problem':{'pid':'B2002','tags':[1],'content':{'background':NOTICE,'description':'输出 Hello,World!'},'samples':[['','Hello,World!']]}}}
        client=Client();value=statement(client,'B2002','Hello,World!','https://www.luogu.com.cn/problem/B2002')
        self.assertEqual(len(client.calls),1);self.assertNotIn(NOTICE,value['markdown']);self.assertEqual(value['samples'][0]['input'],'')

    def test_single_problem_view_does_not_build_full_catalogue(self):
        class FakeLibrary:
            def rows(self):return [{'id':'a','url':'https://example.com/a','title':'old'},{'id':'alias','url':'https://example.com/a'}]
        store=Store.__new__(Store);store.library=FakeLibrary();store.extensions=None
        store.row=lambda identity:{'id':identity};store.encode_row=lambda row:dict(row,title='fresh',url='https://example.com/a')
        with patch.object(store,'data',side_effect=AssertionError('full catalog rebuilt')):
            rows=store.problem_catalog('a')
        self.assertEqual(next(row for row in rows if row['id']=='a')['title'],'fresh')
        self.assertEqual({row['id'] for row in rows},{'a','alias'})
