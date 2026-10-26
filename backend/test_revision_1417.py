"""Cold catalogue, readable statements and private list labels use disposable state."""
from contextlib import closing
import gzip
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from library import LibraryDatabase
from persistence import load_document
from statement_cleanup import clean_statement
from store import Store
from test_nonblocking_loading import record
from test_training import Library, Assets, Judge, Clock
from training import TrainingService, ServiceError, _LIBRARY_VIEW
from training_list_tags import read_tags, save_tags, PREFIX
from response_cache import GzipJSON


class ReadableStatementTests(unittest.TestCase):
    def test_placeholder_uses_site_translation_and_restores_numbered_samples(self):
        source={'markdown':'# リモコン\n\n## 题目描述\n\n[problemUrl]: https://example.com/problem\n',
                'statementAvailable':True,'samples':[], 'translation':{'kind':'site','provider':'原站中文',
                'markdown':'# 遥控器\n\n求从 A 调整到 B 的最少按键次数。\n\n样例 $1$:\n\n输入：\n```\n7 34\n```\n\n输出：\n```\n5\n```'}}
        value=clean_statement(source)
        self.assertTrue(value['statementAvailable'])
        self.assertIn('最少按键',value['markdown'])
        self.assertEqual(value['samples'],[{'name':'样例 1','input':'7 34','output':'5'}])
        self.assertEqual(source['samples'],[])
        self.assertEqual(clean_statement(value),value)

    def test_japanese_only_is_unavailable_but_foreign_title_is_not_a_language_filter(self):
        source={'markdown':'# リモコン\n\nあなたはこの問題を解いてください。整数を出力してください。','samples':[]}
        value=clean_statement(source)
        self.assertFalse(value['statementAvailable']);self.assertEqual(value['statementLanguage'],'ja')
        self.assertEqual(clean_statement(value),value)
        english=clean_statement({'markdown':'# リモコン\n\nRead two integers and print their sum.','samples':[]})
        self.assertTrue(english['statementAvailable'])

    def test_placeholder_and_reference_only_pages_do_not_become_available(self):
        for body in ['# Empty\n\n## Input\n\n## Output', '# Empty\n\n[problemUrl]: https://example.com/a']:
            result=clean_statement({'markdown':body,'statementAvailable':True,'samples':[]})
            self.assertFalse(result['statementAvailable']);self.assertIsNone(result['markdown'])
        text='Print the following code exactly.\n```\n#include <iostream>\n```'
        self.assertEqual(clean_statement({'markdown':text,'samples':[]})['markdown'],text)


class Catalogue1417Tests(unittest.TestCase):
    def test_compressed_cache_token_and_external_import_invalidation(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder);library=LibraryDatabase(path/'library.sqlite3')
            records=[]
            for i in range(180):
                raw,encoded,solution,statement=record(str(i),cached=True)
                encoded['title']='Distinct problem '+str(i)+' details '*20
                records.append((raw,encoded,solution,statement))
            library.import_records(records,{},{});store=Store(data_file=path/'missing.md',library_file=library.path)
            first=store.data_response_bytes(compact=True,compressed=True)
            self.assertIsInstance(first,GzipJSON)
            self.assertEqual(len(json.loads(gzip.decompress(first))['rows']),180)
            self.assertLess(len(store._data_json),50000)
            self.assertLess(len(store._compact_json),50000)
            stored=load_document(path/'tb-catalog-cache.json',{})
            self.assertIn('catalogGzip',stored);self.assertNotIn('token',json.dumps(stored))
            store.token='new-session'
            self.assertEqual(json.loads(store.data_response_bytes(compact=True))['token'],'new-session')
            with closing(sqlite3.connect(library.path)) as writer:
                writer.execute('PRAGMA journal_mode=WAL')
                row=json.loads(writer.execute('SELECT encoded FROM problems WHERE id=?',('loading::0',)).fetchone()[0])
                row['title']='External import'
                writer.execute('UPDATE problems SET encoded=? WHERE id=?',(json.dumps(row),'loading::0'));writer.commit()
                values=json.loads(store.data_response_bytes(compact=True))['rows']
                self.assertEqual(next(row for row in values if row['id']=='loading::0')['title'],'External import')
            with patch.object(library,'rows',side_effect=AssertionError('full metadata decode')):
                identities=library.identity_rows()
            self.assertEqual(len(identities),180)
            self.assertNotIn('knowledgeAnalysis',identities[0])


class PrivateTagTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name);self.library=Library()
        self.service=TrainingService(self.library,self.path/'personal.sqlite3',Assets(self.library),Judge(),Clock(),self.path/'backups')
    def tearDown(self):self.service.close();self.temp.cleanup()

    def test_labels_roundtrip_reverse_index_external_changes_and_deletions(self):
        save_tags(self.service,{'listId':'list','tags':[' 复习 ','数组','数组']},{'list'})
        self.assertEqual(read_tags(self.service,'数组')['listIds'],['list'])
        with closing(sqlite3.connect(self.path/'personal.sqlite3')) as writer:
            writer.execute('UPDATE account_preferences SET value=? WHERE key=?',(json.dumps(['考前']),PREFIX+'list'));writer.commit()
        self.assertEqual(read_tags(self.service,'数组')['listIds'],[])
        self.assertEqual(read_tags(self.service)['tags'],{'list':['考前']})
        save_tags(self.service,{'listId':'list','tags':[]},{'list'})
        self.assertEqual(read_tags(self.service)['tags'],{})
        self.assertEqual(self.service.connection.execute('SELECT value FROM account_preferences WHERE key=?',(PREFIX+'list',)).fetchone()[0],'[]')
        other=TrainingService(self.library,self.path/'other.sqlite3',Assets(self.library),Judge(),Clock(),self.path/'other-backups')
        try:self.assertEqual(read_tags(other)['tags'],{})
        finally:other.close()

    def test_invalid_list_and_tags_are_rejected(self):
        for body in [{'listId':'unknown','tags':['x']},{'listId':'list','tags':['x'*25]},{'listId':'list','tags':['bad\nlabel']}]:
            with self.assertRaises(ServiceError):save_tags(self.service,body,{'list'})

    def test_contest_start_during_problem_read_promotes_to_complete_catalogue(self):
        plan=self.service.preview_contest({'count':2,'duration':120,'min':1000,'max':2100})['plan']
        self.service.start_contest({'ids':[slot['id'] for slot in plan['slots']],'duration':plan['duration'],'previewId':plan['previewId']})
        token=_LIBRARY_VIEW.set((self.service,[self.library.rows[0]],{'problemOnly':True}))
        try:
            with self.service.lock:self.service._context('fixture::A',None)
            self.assertEqual(len(self.service._library()),8)
            self.assertNotIn('problemOnly',_LIBRARY_VIEW.get()[2])
        finally:_LIBRARY_VIEW.reset(token)

if __name__=='__main__':unittest.main()
