"""Public patches are online, bounded and preserve edits/private records."""
import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
import sys
sys.path[:0]=[str(Path(__file__).resolve().parent/'common'),str(Path(__file__).resolve().parents[1]/'desktop')]

import content_updates as C
from library import LibraryDatabase
from store import Store
from test_library import record

class ContentUpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='tb-content-test-');self.root=Path(self.temp.name)
        seed=LibraryDatabase(self.root/'seed.sqlite3');seed.import_records([record()],{}, {})
        live=LibraryDatabase(self.root/'library.sqlite3');live.merge_seed(seed.path)
        self.store=Store(library_file=live.path,data_file=self.root/'missing.md',data_root=self.root)
        with live.connection() as db:
            db.execute('CREATE TABLE private_draft(code TEXT)');db.execute('INSERT INTO private_draft VALUES (?)',('unique private code',))
        with live.connection() as db:entry=dict(db.execute('SELECT id,url,raw,encoded FROM problems').fetchone())
        encoded=json.loads(entry['encoded']);encoded['title']='Revised public title';encoded['difficulty']=1200;entry['encoded']=json.dumps(encoded)
        raw=json.loads(entry['raw']);raw['题名']=encoded['title'];entry['raw']=json.dumps(raw)
        self.packet={'schema':1,'revision':2026102901,'minClientVersion':'1.4.29','tables':{'problems':[entry]}}

    def tearDown(self):self.temp.cleanup()

    def test_authoring_builder_and_client_use_the_same_cumulative_format(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('content_builder',Path(__file__).resolve().parents[1]/'scripts/build_content_update.py')
        builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
        # Existing lessons and their associations remain usable through a
        # supported round-trip without appearing in the public patch.
        lesson={'id':'stable-lesson','title':'Stable lesson','markdown':'# Stable foundation'}
        for path in (self.root/'seed.sqlite3',self.store.library.path):
            with LibraryDatabase(path).connection() as db:
                db.execute('INSERT INTO lectures VALUES(?,?,?)',(lesson['id'],json.dumps(lesson),C.digest(lesson)))
                db.execute('INSERT INTO problem_lectures VALUES(?,?,?,?)',('fixture::A',lesson['id'],'required',0))
        C.apply(self.store,self.packet,'1.4.29')
        output=self.root/'public-patch'
        report=builder.build(self.root/'seed.sqlite3',self.store.library.path,2026102902,'1.4.29',output)
        self.assertEqual(report['counts'],{'problems':1})
        manifest=json.loads((output/'manifest-v1.json').read_text())
        packed=(output/(manifest['sha256']+'.json.gz')).read_bytes()
        self.assertEqual(manifest['size'],len(packed))
        self.assertNotIn(b'unique private code',gzip.decompress(packed))
        opener=Mock();opener.open.side_effect=[io.BytesIO(json.dumps(manifest).encode()),io.BytesIO(packed)]
        service=C.ContentUpdates(self.store,current='1.4.29',opener=opener,offline=False)
        self.assertTrue(service.check());self.assertEqual(service.snapshot()['revision'],2026102902)
        self.assertEqual(self.store.library.lecture_entries()[lesson['id']],lesson)
        self.assertEqual(self.store.library.references('fixture::A'),[(lesson['id'],'required')])

    def test_builder_refuses_new_changed_or_deleted_lesson_bodies(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('content_builder',Path(__file__).resolve().parents[1]/'scripts/build_content_update.py')
        builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
        path=self.store.library.path
        with self.store.library.connection() as db:
            db.execute('INSERT INTO lectures VALUES(?,?,?)',('new-lesson','{"markdown":"New foundation"}','new'))
        output=self.root/'incomplete-patch'
        with self.assertRaisesRegex(ValueError,'lectures.*program update'):
            builder.build(self.root/'seed.sqlite3',path,2026102902,'1.4.29',output)
        self.assertFalse((output/'manifest-v1.json').exists())
        with LibraryDatabase(self.root/'seed.sqlite3').connection() as db:
            db.execute('INSERT INTO lectures VALUES(?,?,?)',('new-lesson','{"markdown":"Old foundation"}','old'))
        with self.assertRaisesRegex(ValueError,'lectures.*program update'):
            builder.build(self.root/'seed.sqlite3',path,2026102902,'1.4.29',output)
        with self.store.library.connection() as db:db.execute('DELETE FROM lectures')
        with self.assertRaisesRegex(ValueError,'lectures.*program update'):
            builder.build(self.root/'seed.sqlite3',path,2026102902,'1.4.29',output)

    def test_builder_refuses_new_or_changed_lesson_relations(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('content_builder',Path(__file__).resolve().parents[1]/'scripts/build_content_update.py')
        builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
        for path in (self.root/'seed.sqlite3',self.store.library.path):
            with LibraryDatabase(path).connection() as db:
                db.execute('INSERT INTO lectures VALUES(?,?,?)',('same-lesson','{"markdown":"Same foundation"}','same'))
        with self.store.library.connection() as db:
            db.execute('INSERT INTO problem_lectures VALUES(?,?,?,?)',('fixture::A','same-lesson','required',0))
        output=self.root/'incomplete-patch'
        with self.assertRaisesRegex(ValueError,'problem_lectures.*program update'):
            builder.build(self.root/'seed.sqlite3',self.store.library.path,2026102902,'1.4.29',output)
        self.assertFalse((output/'manifest-v1.json').exists())
        with LibraryDatabase(self.root/'seed.sqlite3').connection() as db:
            db.execute('INSERT INTO problem_lectures VALUES(?,?,?,?)',('fixture::A','same-lesson','optional',1))
        with self.assertRaisesRegex(ValueError,'problem_lectures.*program update'):
            builder.build(self.root/'seed.sqlite3',self.store.library.path,2026102902,'1.4.29',output)

    def test_online_merge_backup_idempotence_and_private_rows(self):
        self.assertTrue(C.apply(self.store,self.packet,'1.4.29'))
        self.assertFalse(C.apply(self.store,self.packet,'1.4.29'))
        with self.store.library.connection() as db:
            self.assertEqual(db.execute('SELECT code FROM private_draft').fetchone()[0],'unique private code')
        self.assertEqual(self.store.library.find('fixture::A')['encoded']['title'],'Revised public title')
        snapshots=[json.loads(path.read_text('utf8')) for path in (self.root/'backups').glob('*.recovery.json')]
        backups=[self.root/'backups'/item['file'] for item in snapshots if item['label']=='before-content-update'];self.assertEqual(len(backups),1)
        self.assertEqual(LibraryDatabase(backups[0],readonly=True).find('fixture::A')['encoded']['title'],'Fixture')

    def test_local_public_edits_win_and_bad_references_roll_back(self):
        with self.store.library.connection() as db:
            db.execute("UPDATE problems SET encoded=json_set(encoded,'$.title','My imported edit')")
        C.apply(self.store,self.packet,'1.4.29')
        self.assertEqual(self.store.library.find('fixture::A')['encoded']['title'],'My imported edit')
        packet=copy.deepcopy(self.packet);packet['revision']+=1
        packet['tables']['solutions']=[{'problem_id':'missing::A','markdown':'Public','source_path':'source.md','images':'{}','digest':'x'}]
        import sqlite3
        with self.assertRaises(sqlite3.IntegrityError):C.apply(self.store,packet,'1.4.29')
        self.assertEqual(int(self.store.library.metadata()['content_update_revision']),self.packet['revision'])

    def test_only_fixed_public_tables_and_original_identities_allowed(self):
        for table in ('submissions','drafts','accounts','account_preferences'):
            packet=copy.deepcopy(self.packet);packet['tables'][table]=[]
            with self.assertRaises(ValueError):C.apply(self.store,packet,'1.4.29')
        packet=copy.deepcopy(self.packet);packet['tables']['problems'][0]['id']='different'
        with self.assertRaises(ValueError):C.apply(self.store,packet,'1.4.29')
        packet=copy.deepcopy(self.packet);packet['minClientVersion']='1.5.0'
        with self.assertRaises(ValueError):C.apply(self.store,packet,'1.4.29')

    def test_verified_feed_applies_without_installing_or_closing(self):
        raw=json.dumps(self.packet).encode();packed=gzip.compress(raw,mtime=0);sha=hashlib.sha256(packed).hexdigest()
        manifest={'schema':1,'revision':self.packet['revision'],'minClientVersion':'1.4.29','sha256':sha,'size':len(packed)}
        opener=Mock();opener.open.side_effect=[io.BytesIO(json.dumps(manifest).encode()),io.BytesIO(packed)]
        callback=Mock();service=C.ContentUpdates(self.store,current='1.4.29',opener=opener,offline=False,on_applied=callback)
        self.assertTrue(service.check());callback.assert_called_once();self.assertEqual(service.snapshot()['status'],'current')
        self.assertEqual(opener.open.call_args_list[1].args[0].full_url,C.ROOT+'/'+sha+'.json.gz')
        # Neither a process launcher nor a personal DB is involved.
        with self.store.library.connection() as db:self.assertEqual(db.execute('SELECT code FROM private_draft').fetchone()[0],'unique private code')

    def test_corrupt_or_truncated_download_never_changes_the_library(self):
        manifest={'schema':1,'revision':self.packet['revision'],'minClientVersion':'1.4.29','sha256':'a'*64,'size':3}
        opener=Mock();opener.open.side_effect=[io.BytesIO(json.dumps(manifest).encode()),io.BytesIO(b'bad'),OSError('fallback unavailable')]
        service=C.ContentUpdates(self.store,current='1.4.29',opener=opener,offline=False)
        self.assertFalse(service.check());self.assertEqual(service.status,'error')
        self.assertEqual(self.store.library.find('fixture::A')['encoded']['title'],'Fixture')
        self.assertNotIn('content_update_revision',self.store.library.metadata())

    def test_download_sources_cannot_cross_into_other_repositories_or_paths(self):
        from urllib.request import Request
        self.assertTrue(C.trusted(C.ROOT+'/manifest-v1.json'))
        self.assertTrue(C.trusted(C.GITHUB+'/'+'a'*64+'.json.gz'))
        for url in (C.ROOT+'/manifest-v1.json?token=x',C.ROOT+'/../secret',C.GITHUB.replace('acm-algo-trainer','other')+'/manifest-v1.json','http://47.82.84.74/updates/content/manifest-v1.json'):
            self.assertFalse(C.trusted(url))
        with self.assertRaises(ValueError):C.Redirect().redirect_request(Request(C.ROOT+'/manifest-v1.json'),None,302,'',{},C.GITHUB+'/manifest-v1.json')

if __name__=='__main__':unittest.main()
