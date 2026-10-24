"""Independent detailed explanations survive source rebuilds and library upgrades."""
import hashlib
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import backend
from library import LibraryDatabase
from paths import LIBRARY_SEED
from test_library import record


def add_detail(database, identity, markdown):
    with database.connection() as db:
        db.execute('INSERT OR REPLACE INTO detailed_solutions VALUES (?,?,?,?,?)',
                   (identity, markdown, 'fixture-detailed.md', '{}', hashlib.sha256(markdown.encode()).hexdigest()))


class DetailedSolutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tb-detailed-solutions-')
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_source_roundtrip_keeps_both_versions_independent(self):
        original = LibraryDatabase(self.root / 'original.sqlite3')
        original.import_records([record()], {}, {})
        default = original.solution('fixture::A')
        add_detail(original, 'fixture::A', '# Detailed\n\nA step-by-step example.')
        source = original.export_source(self.root / 'source')
        rebuilt = LibraryDatabase.from_source(source, self.root / 'rebuilt.sqlite3')
        self.assertEqual(rebuilt.solution('fixture::A'), default)
        self.assertEqual(rebuilt.solution('fixture::A', 'detailed'), original.solution('fixture::A', 'detailed'))
        self.assertIsNone(rebuilt.solution('missing', 'detailed'))
        self.assertEqual(rebuilt.check()['detailed_solutions'], 1)
        # Old text seeds remain buildable without inventing a detailed version.
        (source / 'detailed_solutions.json').unlink()
        old = LibraryDatabase.from_source(source, self.root / 'old-source.sqlite3')
        self.assertEqual(old.solution('fixture::A'), default)
        self.assertIsNone(old.solution('fixture::A', 'detailed'))
        self.assertEqual(old.metadata()['schema'], '5')

    def test_upgrade_adds_details_and_protects_each_locally_edited_version(self):
        seed = LibraryDatabase(self.root / 'seed.sqlite3')
        seed.import_records([record(), record('fixture::B'), record('fixture::C')], {}, {})
        live = LibraryDatabase(self.root / 'live.sqlite3')
        live.merge_seed(seed.path)
        live.import_records([record(markdown='My default explanation')], {}, {})
        for identity in ('fixture::A', 'fixture::B', 'fixture::C'):
            add_detail(seed, identity, 'First detailed explanation')
        live.merge_seed(seed.path)
        self.assertEqual(live.solution('fixture::A')['markdown'], 'My default explanation')
        self.assertEqual(live.solution('fixture::A', 'detailed')['markdown'], 'First detailed explanation')
        add_detail(live, 'fixture::B', 'My detailed explanation')
        for identity in ('fixture::A', 'fixture::B', 'fixture::C'):
            add_detail(seed, identity, 'Improved detailed explanation')
        live.merge_seed(seed.path)
        self.assertEqual(live.solution('fixture::A')['markdown'], 'My default explanation')
        self.assertEqual(live.solution('fixture::B', 'detailed')['markdown'], 'My detailed explanation')
        self.assertEqual(live.solution('fixture::C', 'detailed')['markdown'], 'Improved detailed explanation')
        self.assertFalse(live.merge_seed(seed.path))

    def test_schema_three_backup_includes_committed_wal_and_old_seeds_still_merge(self):
        path = self.root / 'old.sqlite3'
        database = LibraryDatabase(path)
        database.import_records([record()], {}, {})
        with closing(sqlite3.connect(path)) as writer:
            writer.execute('DROP TABLE detailed_solutions')
            writer.execute("UPDATE library_meta SET value='3' WHERE key='schema'")
            writer.commit()
            writer.execute('PRAGMA journal_mode=WAL')
            writer.execute("UPDATE solutions SET markdown='Committed WAL explanation'")
            writer.commit()
            migrated = LibraryDatabase(path)
            backups = list((self.root / 'backups').glob('*schema-migration*.sqlite3'))
            self.assertEqual(len(backups), 1)
            saved = LibraryDatabase(backups[0], readonly=True)
            self.assertEqual(saved.solution('fixture::A')['markdown'], 'Committed WAL explanation')
            self.assertIsNone(saved.solution('fixture::A', 'detailed'))
            target = LibraryDatabase(self.root / 'target.sqlite3')
            target.merge_seed(saved.path)
            self.assertEqual(target.solution('fixture::A'), saved.solution('fixture::A'))
            self.assertEqual(migrated.metadata()['schema'], '5')
            self.assertEqual(migrated.check()['detailed_solutions'], 0)

    def test_store_preserves_original_body_and_resolves_details_by_canonical_problem(self):
        with patch.dict('os.environ', {'TB_OFFLINE': '1'}):
            server = backend.create_server(require_account=False, training_file=self.root / 'personal.sqlite3',
                                           integration_auto_start=False)
        try:
            identity = 'Div.2 1112::C'
            expected = LibraryDatabase(LIBRARY_SEED, readonly=True).solution(identity)
            value = server.store.solution(identity)
            for field in ('markdown', 'images', 'digest', 'path'):
                self.assertEqual(value[field], expected[field])
            self.assertIn('第三个样例', value['detailedSolution']['markdown'])
            self.assertNotEqual(value['detailedSolution']['markdown'], value['markdown'])
            # Model a missing detailed version explicitly: the bundled archive
            # now includes one for every problem with a default editorial.
            default_only = server.store.solution('Div.2 1112::B')['markdown']
            with server.store.library.connection() as db:
                db.execute('DELETE FROM detailed_solutions WHERE problem_id=?', ('Div.2 1112::B',))
            self.assertIsNone(server.store.solution('Div.2 1112::B')['detailedSolution'])
            self.assertEqual(server.store.solution('Div.2 1112::B')['markdown'], default_only)
            alias = {'_id': 'remote:cf:2250::C', '_url': 'https://codeforces.com/problemset/problem/2250/C'}
            with patch.object(server.store, 'row', return_value=alias):
                self.assertEqual(server.store.solution(alias['_id']), value)
            # A future problem may receive its detailed explanation first.
            with server.store.library.connection() as db:
                db.execute('DELETE FROM solutions WHERE problem_id=?', (identity,))
            self.assertEqual(server.store.solution(identity)['markdown'], '')
            self.assertEqual(server.store.solution(identity)['detailedSolution'], value['detailedSolution'])
            self.assertTrue(next(row for row in server.store.data()['rows'] if row['id'] == identity)['solutionAvailable'])
        finally:
            server.server_close()


if __name__ == '__main__':
    unittest.main()
