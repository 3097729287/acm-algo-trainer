"""Visible deduplication preserves underlying alias content and code."""
from pathlib import Path
import tempfile
import unittest

from catalog_identity import unique_catalog_rows
from library import LibraryDatabase
from store import Store
from test_library import record


class CatalogIdentityTests(unittest.TestCase):
    def test_aliases_merge_by_original_url_never_by_problem_title(self):
        rows = [dict(id='remote:A', url='https://codeforces.com/problemset/problem/123/A', source='remote', tags=['模拟']),
                dict(id='archive:A', url='https://codeforces.com/contest/123/problem/A', source='archive', tags=['枚举'], solutionAvailable=True),
                dict(id='different:A', title='Same title', url='https://codeforces.com/contest/124/problem/A', tags=[])]
        result = unique_catalog_rows(rows)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['id'], 'archive:A')
        self.assertEqual(set(result[0]['aliasIds']), {'remote:A', 'archive:A'})
        self.assertEqual(result[0]['tags'], ['模拟', '枚举'])
        self.assertNotIn('aliasIds', rows[1], 'Caller metadata is immutable')
        self.assertEqual(len(unique_catalog_rows([{'id': 'A', 'title': 'Same'}, {'id': 'B', 'title': 'Same'}])), 2)

    def test_store_hides_duplicate_rows_without_removing_either_editorial(self):
        with tempfile.TemporaryDirectory(prefix='tb-alias-catalog-') as directory:
            root = Path(directory)
            library = LibraryDatabase(root / 'library.sqlite3')
            library.import_records([record('original::A', markdown='Original text.'), record('remote::A', markdown='Other imported text.')], {}, {})
            store = Store(data_file=root / 'absent.md', library_file=library.path)
            row = store.data()['rows'][0]
            self.assertEqual(len(store.data()['rows']), 1)
            self.assertEqual(set(row['aliasIds']), {'original::A', 'remote::A'})
            self.assertEqual(library.check()['problems'], 2)
            self.assertEqual(library.solution('original::A')['markdown'], 'Original text.')
            self.assertEqual(library.solution('remote::A')['markdown'], 'Other imported text.')


if __name__ == '__main__':
    unittest.main()
