"""Performance caches must preserve content, isolation, invalidation and bounds."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import gzip
import http.client
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from response_cache import CompressedResponses
from statement_cleanup import clean_statement_markdown,_cached_markdown
import test_backend as api_fixtures
import test_loading_cache as loading_fixtures


class CompressionSafetyTests(unittest.TestCase):
    def test_parallel_identical_bytes_compress_once_and_sessions_remain_distinct(self):
        cache=CompressedResponses()
        first=b'{"token":"first","rows":['+b'123,'*10000+b'0]}'
        second=first.replace(b'first',b'other')
        with patch('response_cache.gzip.compress',wraps=gzip.compress) as compress:
            with ThreadPoolExecutor(max_workers=4) as pool:
                bodies=list(pool.map(cache.compress,[first]*8))
            self.assertEqual(compress.call_count,1)
            self.assertTrue(all(gzip.decompress(body)==first for body in bodies))
            self.assertEqual(gzip.decompress(cache.compress(second)),second)
            self.assertEqual(compress.call_count,2)

    def test_memory_and_entry_limits_are_enforced(self):
        cache=CompressedResponses(max_bytes=4096,max_entries=2)
        for value in range(20):
            raw=(str(value)*500).encode()
            self.assertEqual(gzip.decompress(cache.compress(raw)),raw)
            self.assertLessEqual(cache._bytes,4096)
            self.assertLessEqual(len(cache._items),2)
        raw=b'large'*4096
        self.assertEqual(gzip.decompress(cache.compress(raw)),raw)
        self.assertNotIn(raw,cache._items)
        cache.clear();self.assertEqual(cache._bytes,0)


class CatalogueByteSafetyTests(unittest.TestCase):
    setUp=loading_fixtures.LoadingCacheTests.setUp
    tearDown=loading_fixtures.LoadingCacheTests.tearDown
    open=loading_fixtures.LoadingCacheTests.open

    def test_cached_bytes_change_with_token_date_and_external_sqlite_commit(self):
        self.store.data()
        first=self.store.data_response_bytes(compact=True)
        self.assertIs(first,self.store.data_response_bytes(compact=True))
        self.store.token='new-account-session'
        second=json.loads(self.store.data_response_bytes(compact=True))
        self.assertEqual(second['token'],'new-account-session')
        with closing(sqlite3.connect(self.library.path)) as writer:
            writer.execute('PRAGMA journal_mode=WAL')
            row=json.loads(writer.execute('SELECT encoded FROM problems').fetchone()[0])
            row['title']='Fresh external content'
            writer.execute('UPDATE problems SET encoded=?',(json.dumps(row),))
            writer.commit()
            self.assertEqual(json.loads(self.store.data_response_bytes(compact=True))['rows'][0]['title'],'Fresh external content')
        import store
        real_date=store.dt.date
        with patch.object(store.dt,'date') as date:
            date.today.return_value=real_date(2030,1,2)
            self.assertEqual(json.loads(self.store.data_response_bytes(compact=True))['today'],'2030-01-02')


class StaticAssetSafetyTests(unittest.TestCase):
    setUp=api_fixtures.BackendTests.setUp
    tearDown=api_fixtures.BackendTests.tearDown

    def read(self,path,headers=None):
        connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        try:
            connection.request('GET',path,headers=headers or {})
            response=connection.getresponse()
            return response.status,dict(response.getheaders()),response.read()
        finally:connection.close()

    def test_index_revalidates_and_changed_content_gets_a_new_validator(self):
        self.server.dist_dir=self.root/'frontend';self.server.dist_dir.mkdir()
        index=self.server.dist_dir/'index.html';index.write_text('first',encoding='utf-8')
        status,headers,body=self.read('/')
        self.assertEqual((status,body),(200,b'first'))
        self.assertEqual(headers['Cache-Control'],'no-cache')
        self.assertEqual(self.read('/',{'If-None-Match':headers['ETag']})[0],304)
        index.write_text('other',encoding='utf-8')
        status,changed,body=self.read('/',{'If-None-Match':headers['ETag']})
        self.assertEqual((status,body),(200,b'other'))
        self.assertNotEqual(changed['ETag'],headers['ETag'])

    def test_only_hashed_assets_are_immutable(self):
        self.server.dist_dir=self.root/'frontend';assets=self.server.dist_dir/'assets';assets.mkdir(parents=True)
        for name in ['index-0123ABcd.js','plain.js']:(assets/name).write_text('export {}',encoding='utf-8')
        self.assertIn('immutable',self.read('/assets/index-0123ABcd.js')[1]['Cache-Control'])
        self.assertEqual(self.read('/assets/plain.js')[1]['Cache-Control'],'no-cache')


class StatementCacheSafetyTests(unittest.TestCase):
    def test_cached_prose_keeps_samples_and_changes_invalidate_by_content(self):
        first='# [模板] 求和\n\n## 样例\n\n```text\n广告\n1 2\n```\n'
        result=clean_statement_markdown(first)
        self.assertIn('广告\n1 2',result)
        self.assertEqual(clean_statement_markdown(first),result)
        self.assertIn('3 4',clean_statement_markdown(first.replace('1 2','3 4')))
        self.assertEqual(clean_statement_markdown(['not','text']),['not','text'])
        for i in range(80):clean_statement_markdown('Public statement '+str(i))
        self.assertLessEqual(_cached_markdown.cache_info().currsize,64)

if __name__=='__main__':unittest.main()
