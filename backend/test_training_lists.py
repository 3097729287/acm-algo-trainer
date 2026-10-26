"""Public list persistence and canonical imports, always in disposable state."""
import copy
import importlib.util
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from library import LibraryDatabase
from test_library import record
from store import Store

spec = importlib.util.spec_from_file_location('import_luogu_training', Path(__file__).resolve().parents[1] / 'scripts/import_luogu_training.py')
IMPORTER = importlib.util.module_from_spec(spec)
spec.loader.exec_module(IMPORTER)


class TrainingListTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tb-training-lists-')
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def lists(self, database, values):
        with database.connection() as db:
            db.executemany('INSERT OR REPLACE INTO training_lists VALUES (?,?)',
                           [(value['id'], json.dumps(value)) for value in values])

    def test_lists_roundtrip_and_seed_upgrade_preserve_local_changes(self):
        seed = LibraryDatabase(self.root / 'seed.sqlite3')
        seed.import_records([record()], {}, {})
        self.lists(seed, [{'id': 'first', 'title': 'before', 'problems': []}, {'id': 'edited', 'title': 'before', 'problems': []}])
        seed.export_source(self.root / 'source')
        rebuilt = LibraryDatabase.from_source(self.root / 'source', self.root / 'rebuilt.sqlite3')
        self.assertEqual(seed.training_lists(), rebuilt.training_lists())
        live = LibraryDatabase(self.root / 'live.sqlite3')
        live.merge_seed(seed.path)
        self.lists(live, [{'id': 'edited', 'title': 'local edit', 'problems': []}, {'id': 'private-import', 'problems': []}])
        self.lists(seed, [{'id': 'first', 'title': 'after', 'problems': []}, {'id': 'edited', 'title': 'upstream', 'problems': []}, {'id': 'new', 'problems': []}])
        live.merge_seed(seed.path)
        values = {item['id']: item for item in live.training_lists()}
        self.assertEqual(values['first']['title'], 'after')
        self.assertEqual(values['edited']['title'], 'local edit')
        self.assertIn('private-import', values)
        self.assertIn('new', values)
        self.assertFalse(live.merge_seed(seed.path), 'second merge is a no-op')
        self.assertEqual(live.solution('fixture::A')['markdown'], record()[2]['markdown'])

    def test_old_seed_and_schema_migration(self):
        old = LibraryDatabase(self.root / 'old.sqlite3')
        old.import_records([record()], {}, {})
        with old.connection() as db:
            db.execute('DROP TABLE training_lists')
            db.execute("UPDATE library_meta SET value='4' WHERE key='schema'")
        self.assertEqual(LibraryDatabase(old.path, readonly=True).training_lists(), [])
        live = LibraryDatabase(self.root / 'live.sqlite3')
        live.merge_seed(old.path)
        self.assertEqual(live.training_lists(), [])
        migrated = LibraryDatabase(old.path)
        self.assertEqual(migrated.metadata()['schema'], '5')
        self.assertEqual(migrated.rows()[0]['id'], 'fixture::A')
        self.assertTrue(list((self.root / 'backups').glob('*schema-migration*.sqlite3')))

    def test_training_membership_extends_visibility_without_rewriting_problem(self):
        seed = LibraryDatabase(self.root / 'seed.sqlite3')
        raw, encoded, solution, statement = record()
        encoded.update(source='remote', contest='Other contest', catalogHidden=True, catalogNotice='previous policy')
        seed.import_records([(raw, encoded, None, None)], {}, {})
        before = seed.find('fixture::A')
        self.lists(seed, [{'id': 'list', 'problems': [{'problemId': 'fixture::A', 'url': encoded['url']}]}])
        store = Store(library_file=seed.path, data_file=self.root / 'missing.md', data_root=self.root)
        self.assertFalse(store.data()['rows'][0].get('catalogHidden'))
        self.assertEqual(seed.find('fixture::A'), before)

    def test_embedded_sections_and_public_link_boundaries(self):
        description = '''## 动态规划
### 背包
[first](https://www.luogu.com.cn/problem/P1001)
[duplicate](/problem/P1001)
[chapter](https://www.luogu.com.cn/training/12)
[返回主题单](https://www.luogu.com.cn/training/99)
[other](https://example.org/problem/P9999)
```
/problem/P9998
```
### 树形 DP
[second](/problem/CF1A)
'''
        problems, children = IMPORTER.description_links(description, 'luogu-10')
        self.assertEqual(problems, {'P1001': ['动态规划', '背包'], 'CF1A': ['动态规划', '树形 DP']})
        self.assertEqual(children, ['luogu-12'])

    def test_read_api_uses_sqlite_and_keeps_local_origin_guard(self):
        import backend
        database = LibraryDatabase(self.root / 'api.sqlite3')
        database.import_records([record()], {}, {})
        values = [{'id': 'list', 'title': 'Public list', 'problems': [{'problemId': 'fixture::A'}]}]
        self.lists(database, values)
        server = backend.create_server(require_account=False, training_file=self.root / 'personal.sqlite3',
                                       library_file=database.path, data_root=self.root,
                                       data_file=self.root / 'missing.md', integration_auto_start=False)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
            connection.request('GET', '/api/training-lists')
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertEqual(json.loads(response.read()), {'lists': values, 'tags': {}})
            connection.close()
            connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
            connection.request('GET', '/api/training-lists', headers={'Origin': 'https://example.com'})
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertIsNone(response.getheader('Access-Control-Allow-Origin'), 'foreign pages cannot read the API response')
            response.read()
            connection.close()
            self.assertEqual(server.training.workspace()['summary']['total'], 0)
            raw, encoded, _, _ = record('standalone::A')
            encoded.update(source='luogu-training', contest='Training collection', url='https://www.luogu.com.cn/problem/P1001')
            raw.update(_id=encoded['id'], _url=encoded['url'])
            database.import_records([(raw, encoded, None, None)], {}, {})
            self.assertNotIn('Training collection', [event['name'] for event in server.training.replay_events()['events']])
            from training import ServiceError
            with self.assertRaises(ServiceError):
                server.training.preview_replay({'contest': 'Training collection'})
        finally:
            server.shutdown()
            server.server_close()
            thread.join(2)

    def test_import_reuses_known_urls_and_mirrors_and_preserves_existing_rows(self):
        source = self.root / 'source'
        source.mkdir()
        old = {'id': 'original', 'url': 'https://codeforces.com/contest/1/problem/A', 'raw': {'retained': True}, 'encoded': {'retained': True}}
        IMPORTER.dump(source / 'problems.json', [old])
        collection = {'source': 'https://www.luogu.com.cn/training/list', 'collectedAt': '2026-10-24T00:00:00Z',
                      'categories': [{'key': 'test'}], 'tags': {}, 'errors': [],
                      'lists': [{'id': 'luogu-1', 'categories': ['test'], 'officialProblemCount': 3,
                                 'problems': [{'pid': 'CF1A'}, {'pid': 'P1001'}, {'pid': 'P1001'}, {'pid': 'P9999999'}]}],
                      'problems': {'CF1A': {'name': 'Theatre Square', 'difficulty': 1}, 'P1001': {'name': 'A+B', 'difficulty': 0}}}
        with patch.object(IMPORTER, 'ROOT', self.root):
            IMPORTER.apply(copy.deepcopy(collection), source, self.root / 'backup')
            result = json.loads((source / 'problems.json').read_text('utf8'))
            self.assertEqual(len(result), 2)
            self.assertIn(old, result)
            new = next(row for row in result if row['id'] != 'original')
            self.assertIsNone(new['encoded']['difficulty'], 'unrated remains unknown')
            imported = json.loads((source / 'training_lists.json').read_text('utf8'))[0]['problems']
            self.assertEqual(imported[0]['problemId'], 'original')
            self.assertEqual(imported[1]['problemId'], imported[2]['problemId'])
            self.assertIsNone(imported[3]['problemId'])
            IMPORTER.apply(copy.deepcopy(collection), source, self.root / 'backup-again')
            self.assertEqual(json.loads((source / 'problems.json').read_text('utf8')), result)


if __name__ == '__main__':
    unittest.main()
