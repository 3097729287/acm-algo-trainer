"""Existing immutable resource bytes are not loaded again during seed merge."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from library import LibraryDatabase
from public_assets import read_asset


class SeedAssetReuseTests(unittest.TestCase):
    def test_upgrade_keeps_cached_assets_and_imports_new_verified_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);seed=LibraryDatabase(root/'seed.sqlite3');live=LibraryDatabase(root/'live.sqlite3')
            old=b'old immutable fixture';new=b'new immutable fixture';a=hashlib.sha256(old).hexdigest();b=hashlib.sha256(new).hexdigest()
            with seed.connection() as db:db.execute('INSERT INTO statement_assets VALUES(?,?,?)',(a,'application/pdf',old))
            live.merge_seed(seed.path)
            with seed.connection() as db:db.execute('INSERT INTO statement_assets VALUES(?,?,?)',(b,'application/pdf',new))
            live.merge_seed(seed.path)
            self.assertEqual(read_asset(live,a,root/'cache.sqlite3'),('application/pdf',old))
            self.assertEqual(read_asset(live,b,root/'cache.sqlite3'),('application/pdf',new))
            self.assertFalse(live.merge_seed(seed.path))

    def test_reused_bytes_still_fail_read_integrity_if_the_local_cache_is_corrupt(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);seed=LibraryDatabase(root/'seed.sqlite3');live=LibraryDatabase(root/'live.sqlite3')
            raw=b'public immutable fixture';sha=hashlib.sha256(raw).hexdigest()
            with seed.connection() as db:db.execute('INSERT INTO statement_assets VALUES(?,?,?)',(sha,'application/pdf',raw))
            live.merge_seed(seed.path)
            with live.connection() as db:db.execute('UPDATE statement_assets SET data=? WHERE sha256=?',(b'corrupted',sha))
            with seed.connection() as db:db.execute("INSERT INTO library_meta VALUES('revision-extra','next')")
            live.merge_seed(seed.path)
            with self.assertRaises(ValueError):read_asset(live,sha,root/'cache.sqlite3')


if __name__=='__main__':unittest.main()
