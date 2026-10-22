"""Public snapshots stay fast, current, independent and free of session secrets."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from knowledge import KnowledgeAnalysisCache
from library import LibraryDatabase
from persistence import load_document, save_document
from store import Store
from test_library import record


class LoadingCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tb-loading-')
        self.root = Path(self.temp.name)
        self.library = LibraryDatabase(self.root / 'library.sqlite3')
        self.library.import_records([record()], {}, {})
        self.store = self.open()

    def open(self):
        return Store(data_file=self.root / 'absent.md', library_file=self.library.path)

    def tearDown(self):
        self.temp.cleanup()

    def test_warm_reads_do_not_reclassify_and_do_not_share_mutable_rows(self):
        original = self.store.data()
        with patch.object(self.store, '_encode_record', side_effect=AssertionError('reclassified')):
            changed = self.store.data()
            changed['rows'][0]['title'] = 'Consumer mutation'
            changed['rows'][0]['knowledgeAnalysis']['tags'].append('bad')
            self.assertEqual(self.store.data(), original)
            self.store.token = 'new-account-session'
            self.assertEqual(self.store.data()['token'], 'new-account-session')

    def test_restart_reuses_public_snapshot_and_does_not_rewrite_url_index(self):
        self.store.data()
        signature = self.library.content_signature()
        cached = load_document(self.library.path.with_name('tb-catalog-cache.json'), {})
        self.assertNotIn('token', json.loads(cached['catalog']))
        self.assertNotIn('today', json.loads(cached['catalog']))
        restarted = self.open()
        self.assertEqual(self.library.content_signature(), signature)
        with patch.object(restarted, '_encode_record', side_effect=AssertionError('reclassified')):
            self.assertEqual(restarted.data()['rows'][0]['title'], 'Fixture')

    def test_import_and_external_wal_commit_invalidate_immediately(self):
        self.store.data()
        imported = record('custom::A', 'Imported')
        imported[1]['url'] = 'https://codeforces.com/contest/2/problem/A'
        self.library.import_records([imported], {}, {})
        self.assertEqual(len(self.store.data()['rows']), 2)
        with closing(sqlite3.connect(self.library.path)) as writer:
            writer.execute('PRAGMA journal_mode=WAL')
            encoded = json.loads(writer.execute("SELECT encoded FROM problems WHERE id='fixture::A'").fetchone()[0])
            encoded['title'] = 'Updated in WAL'
            writer.execute('UPDATE problems SET encoded=? WHERE id=?', (json.dumps(encoded), 'fixture::A'))
            writer.commit()
            self.assertEqual(self.store.data()['rows'][0]['title'], 'Updated in WAL')

    def test_analysis_changes_invalidate_and_corrupt_disk_cache_is_ignored(self):
        self.store.knowledge_analysis = KnowledgeAnalysisCache(self.root / 'analysis.json')
        before = self.store.data()['revision']
        row = self.store.data()['rows'][0]
        self.store.knowledge_analysis.enrich(row, algorithm_evidence={'tags': ['前缀和'], 'source': 'fixture'})
        self.assertNotEqual(self.store.data()['revision'], before)
        cached = load_document(self.library.path.with_name('tb-catalog-cache.json'), {})
        cached['catalog'] = '{broken'
        save_document(self.library.path.with_name('tb-catalog-cache.json'), cached)
        self.assertEqual(self.open().data()['rows'][0]['title'], 'Fixture')

    def test_parallel_readers_build_once_and_presence_never_loads_bodies(self):
        with patch.object(self.store, '_encode_record', wraps=self.store._encode_record) as encode:
            with ThreadPoolExecutor(max_workers=4) as pool:
                rows = list(pool.map(lambda _: self.store.data(), range(4)))
            self.assertEqual(encode.call_count, 1)
            self.assertTrue(all(result['revision'] == rows[0]['revision'] for result in rows))
        with patch.object(self.library, 'solution', side_effect=AssertionError('body loaded')):
            self.assertTrue(self.library.has_solution('fixture::A'))

    def test_lecture_relations_are_loaded_with_one_query(self):
        from lecture_library import LectureLibrary
        lectures = LectureLibrary(self.store, self.root)
        with patch.object(self.store.library, 'connection', wraps=self.store.library.connection) as connections:
            lectures.snapshot()
        self.assertLessEqual(connections.call_count, 3)

    def test_new_statement_evidence_refreshes_only_the_changed_problem(self):
        imported = record('custom::A')
        imported[1]['url'] = 'https://codeforces.com/contest/2/problem/A'
        self.library.import_records([imported], {}, {})
        self.store.knowledge_analysis = KnowledgeAnalysisCache(self.root / 'analysis.json')
        before = self.store.data()
        self.store.knowledge_analysis.enrich(before['rows'][0], algorithm_evidence={'tags': ['前缀和'], 'source': 'fixture'})
        with patch.object(self.store, '_encode_record', wraps=self.store._encode_record) as encode:
            after = self.store.data()
            self.assertEqual(encode.call_count, 1)
            self.assertIn('前缀和', after['rows'][0]['tags'])
            self.assertEqual(after['rows'][1], before['rows'][1])
            self.store.data()
            self.assertEqual(encode.call_count, 1)


if __name__ == '__main__':
    unittest.main()
