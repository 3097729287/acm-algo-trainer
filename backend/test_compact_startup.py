"""Restarted list reads avoid the full analysis tree without trusting stale data."""
from contextlib import closing
import copy
import json
import sqlite3
import unittest
from unittest.mock import patch

import catalog_snapshot
from knowledge import KnowledgeAnalysisCache
from persistence import load_document, save_document
from test_library import record
from test_loading_cache import LoadingCacheTests


class CompactStartupTests(unittest.TestCase):
    setUp=LoadingCacheTests.setUp
    tearDown=LoadingCacheTests.tearDown
    open=LoadingCacheTests.open

    def cache(self):
        return self.library.path.with_name('tb-catalog-compact-cache.json')

    def test_restart_reads_only_projected_metadata_and_appends_its_own_session(self):
        self.store.data_response_bytes(compact=True)
        cached=load_document(self.cache(),{})
        public=json.loads(catalog_snapshot.unpack(catalog_snapshot.from_document(cached)))
        self.assertNotIn('token',public)
        self.assertNotIn('today',public)
        self.assertNotIn('knowledgeAnalysis',public['rows'][0])
        restarted=self.open()
        restarted.token='another-real-session'
        with patch.object(restarted,'data',side_effect=AssertionError('full analysis decoded')):
            received=json.loads(restarted.data_response_bytes(compact=True))
            training=restarted.training_data()
        self.assertEqual(received['token'],'another-real-session')
        self.assertEqual(received['rows'],training['rows'])
        self.assertIsNone(restarted._data_json)
        received['rows'][0]['title']='consumer changed it'
        self.assertEqual(restarted.training_data()['rows'][0]['title'],'Fixture')
        self.assertIn('knowledgeAnalysis',restarted.data()['rows'][0])

    def test_external_wal_and_analysis_changes_cannot_reuse_old_rows(self):
        self.store.data_response_bytes(compact=True)
        restarted=self.open()
        with closing(sqlite3.connect(self.library.path)) as writer:
            writer.execute('PRAGMA journal_mode=WAL')
            row=json.loads(writer.execute('SELECT encoded FROM problems').fetchone()[0])
            row['title']='Committed in WAL'
            writer.execute('UPDATE problems SET encoded=?',(json.dumps(row),))
            writer.commit()
            self.assertEqual(json.loads(restarted.data_response_bytes(compact=True))['rows'][0]['title'],'Committed in WAL')
        restarted.knowledge_analysis=KnowledgeAnalysisCache(self.root/'analysis.json')
        row=restarted.data()['rows'][0]
        restarted.knowledge_analysis.enrich(row,algorithm_evidence={'tags':['前缀和'],'source':'fixture'})
        fresh=json.loads(restarted.data_response_bytes(compact=True))
        self.assertIn('前缀和',fresh['rows'][0]['tags'])

    def test_changed_extensions_and_imports_invalidate_persistent_projection(self):
        self.store.data_response_bytes(compact=True)
        imported=record('custom::A','Imported')
        imported[1]['url']='https://codeforces.com/contest/2/problem/A'
        self.library.import_records([imported],{}, {})
        self.assertEqual(len(json.loads(self.open().data_response_bytes(compact=True))['rows']),2)
        restarted=self.open()
        original=restarted._content_signature
        with patch.object(restarted,'_content_signature',side_effect=lambda:(original(),'changed-extension')):
            with patch.object(restarted,'_catalog_rows',wraps=restarted._catalog_rows) as rows:
                self.assertEqual(len(json.loads(restarted.data_response_bytes(compact=True))['rows']),2)
                self.assertEqual(rows.call_count,1)

    def test_corrupt_or_secret_containing_optional_cache_falls_back_to_sqlite(self):
        self.store.data_response_bytes(compact=True)
        valid=load_document(self.cache(),{})
        public=json.loads(catalog_snapshot.unpack(catalog_snapshot.from_document(valid)))
        bad_documents=[{'signature':valid['signature']},
                       {'signature':valid['signature'],'catalog':'{broken'},
                       {'signature':valid['signature'],'catalogGzip':'H4sIbroken'}]
        for mutate in ('token','today','unknown-row-field'):
            value=copy.deepcopy(public)
            if mutate=='unknown-row-field':value['rows'][0]['privateDraft']='must not appear'
            else:value[mutate]='must not appear'
            bad_documents.append({'signature':valid['signature'],'catalog':json.dumps(value)})
        for damaged in bad_documents:
            with self.subTest(damaged=tuple(damaged)):
                save_document(self.cache(),damaged)
                restarted=self.open()
                result=json.loads(restarted.data_response_bytes(compact=True))
                self.assertEqual(result['rows'][0]['title'],'Fixture')
                self.assertNotIn('privateDraft',result['rows'][0])
                self.assertEqual(result['token'],restarted.token)

    def test_projection_revision_and_per_problem_refresh_keep_addition_chronology(self):
        self.store.data_response_bytes(compact=True)
        restarted=self.open()
        with patch('catalog_payload.REVISION','another-reviewed-projection'):
            with patch.object(restarted,'_catalog_rows',wraps=restarted._catalog_rows) as rows:
                restarted.data_response_bytes(compact=True)
                self.assertEqual(rows.call_count,1,'A changed projection cannot reuse an old compact document')
        self.store.knowledge_analysis=KnowledgeAnalysisCache(self.root/'new-analysis.json')
        self.store.data_response_bytes(compact=True)
        row=self.store.data()['rows'][0]
        self.store.knowledge_analysis.enrich(row,algorithm_evidence={'tags':['前缀和'],'source':'fixture'})
        fresh={**row,'schoolTraining':True,'url':'https://codeforces.com/gym/728862/problem/A'}
        with patch.object(self.store,'_encode_record',return_value=fresh):
            updated=self.store.training_data()['rows'][0]
        self.assertEqual(updated['catalogAddedAt'],'2026-11-01T07:38:58Z')


if __name__=='__main__':unittest.main()
