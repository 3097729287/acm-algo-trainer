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
    def test_shared_editorial_figures_roundtrip_without_rewriting_source_or_motion_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);seed=LibraryDatabase(root/'seed.sqlite3');seed.import_records([record()],{}, {})
            source=seed.export_source(root/'source')
            gif=base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')
            uri='data:image/gif;base64,'+base64.b64encode(gif).decode();sha=hashlib.sha256(gif).hexdigest()
            originals=[]
            for name in ('solutions.json','detailed_solutions.json'):
                path=source/name;rows=json.loads(path.read_text('utf8'))
                if not rows:rows=[{'problem_id':'fixture::A','markdown':'![Animation](process.gif)','source_path':'verified.md','images':{}}]
                rows[0]['images']={'process.gif':uri,'same-process.gif':uri}
                path.write_text(json.dumps(rows,ensure_ascii=False),'utf8');originals.append((path,path.read_bytes()))
            built=LibraryDatabase.from_source(source,root/'rebuilt.sqlite3')
            with built.connection() as db:
                self.assertEqual(db.execute('SELECT count(*) FROM statement_assets').fetchone()[0],1)
                self.assertEqual(bytes(db.execute('SELECT data FROM statement_assets WHERE sha256=?',(sha,)).fetchone()[0]),gif)
                for table in ('solutions','detailed_solutions'):
                    images=json.loads(db.execute('SELECT images FROM '+table).fetchone()[0]);self.assertEqual(images['process.gif'],'tb-asset:'+sha)
            for variant in ('default','detailed'):
                self.assertEqual(built.solution('fixture::A',variant)['images'],{'process.gif':uri,'same-process.gif':uri})
            for path,before in originals:self.assertEqual(path.read_bytes(),before)
            again=LibraryDatabase.from_source(built.export_source(root/'portable-source'),root/'again.sqlite3')
            self.assertEqual(again.solution('fixture::A')['images'],built.solution('fixture::A')['images'])
            with again.connection() as db:db.execute('DELETE FROM statement_assets WHERE sha256=?',(sha,))
            for variant in ('default','detailed'):
                with self.assertRaisesRegex(ValueError,'Missing offline statement asset'):
                    again.solution('fixture::A',variant)

    def test_inline_source_figures_are_stored_once_without_changing_source_or_rendered_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);seed=LibraryDatabase(root/'seed.sqlite3');seed.import_records([record()],{}, {})
            source=seed.export_source(root/'source');rows=load_statements(source)
            gif=base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')
            uri='data:image/gif;base64,'+base64.b64encode(gif).decode();sha=hashlib.sha256(gif).hexdigest()
            rows[0]['content']['images']={'source.gif':uri}
            rows[0]['content']['translation']={'kind':'site','markdown':'原样图 ![图](translated.gif)。','images':{'translated.gif':uri}}
            file=source/'statements.json';file.write_text(json.dumps(rows,ensure_ascii=False),encoding='utf8');before=file.read_bytes()
            built=LibraryDatabase.from_source(source,root/'rebuilt.sqlite3')
            self.assertEqual(file.read_bytes(),before)
            with built.connection() as db:
                self.assertEqual(db.execute('SELECT count(*) FROM statement_assets').fetchone()[0],1)
                self.assertEqual(bytes(db.execute('SELECT data FROM statement_assets WHERE sha256=?',(sha,)).fetchone()[0]),gif)
                stored=json.loads(db.execute('SELECT content FROM statements').fetchone()[0])
                self.assertEqual(stored['images']['source.gif'],'tb-asset:'+sha)
                self.assertEqual(stored['translation']['images']['translated.gif'],'tb-asset:'+sha)
            actual=built.statement(rows[0]['problem_id'])
            self.assertEqual(actual['images'],rows[0]['content']['images'])
            self.assertEqual(actual['translation']['images'],rows[0]['content']['translation']['images'])

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
