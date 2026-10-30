import base64
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from library import LibraryDatabase,source_fingerprint
from statement_seed import checksum,load_statements
from test_library import record


class OriginalAssetTests(unittest.TestCase):
    def test_shared_original_bytes_roundtrip_and_old_public_seed_upgrade(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);seed=LibraryDatabase(root/'seed.sqlite3');seed.import_records([record()],{}, {})
            gif=base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')
            uri='data:image/gif;base64,'+base64.b64encode(gif).decode()
            value={'id':'fixture::A','url':'https://qoj.ac/problem/1','markdown':'Look at ![original](original.gif).',
                   'samples':[{'input':'1','output':'2'}], 'images':{'original.gif':uri,'same-original.gif':uri},
                   'translation':{'kind':'site','markdown':'保留原有中文。'}}
            seed.save_statement('fixture::A',value)
            with seed.connection() as db:
                self.assertEqual(db.execute('SELECT count(*) FROM statement_assets').fetchone()[0],1)
                self.assertNotIn('base64',db.execute('SELECT content FROM statements').fetchone()[0])
                self.assertEqual(bytes(db.execute('SELECT data FROM statement_assets').fetchone()[0]),gif)
            self.assertEqual(seed.statement('fixture::A')['images']['original.gif'],uri)
            source=seed.export_source(root/'source');built=LibraryDatabase.from_source(source,root/'rebuilt.sqlite3')
            self.assertEqual(built.statement('fixture::A')['images'],value['images'])
            legacy=LibraryDatabase(root/'old.sqlite3');legacy.import_records([record()],{}, {})
            live=LibraryDatabase(root/'live.sqlite3');live.merge_seed(legacy.path)
            live.save_statement('fixture::A',value)
            with live.connection() as db:
                db.execute('CREATE TABLE private_code(code TEXT)');db.execute('INSERT INTO private_code VALUES (?)',('my draft',))
            live.merge_seed(built.path,fingerprint='new-public-seed')
            self.assertEqual(live.statement('fixture::A')['translation']['markdown'],'保留原有中文。')
            with live.connection() as db:self.assertEqual(db.execute('SELECT code FROM private_code').fetchone()[0],'my draft')

    def test_asset_source_hashes_and_newer_content_conflicts_are_enforced(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);seed=LibraryDatabase(root/'seed.sqlite3');seed.import_records([record()],{}, {})
            source=seed.export_source(root/'source');rows=load_statements(source);old=rows[0]['content'];identity=rows[0]['problem_id']
            patch={'schema':1,'statements':[{'problem_id':identity,'beforeSha256':checksum(old),'content':dict(old,id=identity,markdown='Verified new statement.')}]}
            folder=source/'statement-patches';folder.mkdir();file=folder/'part-0001.json'
            first=source_fingerprint(source);file.write_text(json.dumps(patch),'utf8')
            self.assertNotEqual(first,source_fingerprint(source))
            self.assertEqual(load_statements(source)[0]['content']['markdown'],'Verified new statement.')
            rows[0]['content']['markdown']='Another content session changed this body.'
            (source/'statements.json').write_text(json.dumps(rows),'utf8')
            with self.assertRaisesRegex(ValueError,'conflicts with newer content'):load_statements(source)


if __name__=='__main__':unittest.main()
