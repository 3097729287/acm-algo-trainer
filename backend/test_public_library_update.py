"""Public row deltas match full upgrades while protecting private edits and rows."""
from contextlib import closing
import base64,hashlib,json,shutil,sqlite3,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from library import LibraryDatabase
from public_library_update import merge_public_seed
from build_public_library_update import build,CONTENT
from test_library import record

class PublicLibraryUpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.base=LibraryDatabase(self.root/'base.sqlite3')
        lectures={name:{'id':name,'markdown':name+' public course'} for name in ('old','keep')}
        self.base.import_records([record(),record('fixture::B')],lectures,{'fixture::A':[('old','main')],'fixture::B':[('keep','support')]})
        with self.base.connection() as source,closing(sqlite3.connect(self.root/'target.sqlite3')) as destination:source.backup(destination)
        self.target=LibraryDatabase(self.root/'target.sqlite3')
        self.target.import_records([record(title='New public title',markdown='New public explanation.'),record('fixture::C'),record('fixture::D')],{'new':{'id':'new','markdown':'new course'}},{'fixture::A':[],'fixture::C':[('new','main')]})
        with self.target.connection() as db:db.execute("DELETE FROM lectures WHERE id='old'")
        gif=base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')
        self.uri='data:image/gif;base64,'+base64.b64encode(gif).decode()
        self.target.save_statement('fixture::A',{'markdown':'Verified new ![picture](a.gif).','samples':[{'input':'1','output':'2'}],'images':{'a.gif':self.uri}})
        self.result=build([self.base.path],self.target.path,self.root/'payload')
        self.descriptor=self.root/'payload/public-library-update.json'
        self.live=self.make_live(self.root/'live.sqlite3')
    def make_live(self,path):
        live=LibraryDatabase(path);live.merge_seed(self.base.path)
        with live.connection() as db:
            db.execute('CREATE TABLE private_code(code TEXT)');db.execute("INSERT INTO private_code VALUES('owner draft remains')")
            db.execute("UPDATE solutions SET markdown='my independent annotated solution' WHERE problem_id='fixture::A'")
        return live
    def rows(self,library):
        with library.connection() as db:
            return {table:db.execute('SELECT * FROM '+table+' ORDER BY 1,2').fetchall() for table in [*CONTENT,'problem_lectures','bundled_items']}
    def test_public_delta_matches_full_merge_and_keeps_private_edits_links_and_course_membership(self):
        reference=self.make_live(self.root/'reference.sqlite3');reference.merge_seed(self.target.path)
        self.assertTrue(merge_public_seed(self.live,self.base.path,descriptor=self.descriptor,cache=self.root/'cache'))
        self.assertEqual(self.rows(self.live),self.rows(reference))
        with self.live.connection() as db:
            self.assertEqual(db.execute('SELECT code FROM private_code').fetchone()[0],'owner draft remains')
            self.assertEqual(db.execute("SELECT markdown FROM solutions WHERE problem_id='fixture::A'").fetchone()[0],'my independent annotated solution')
            self.assertIsNotNone(db.execute("SELECT 1 FROM lectures WHERE id='keep'").fetchone())
            self.assertIsNone(db.execute("SELECT 1 FROM lectures WHERE id='old'").fetchone())
        self.assertEqual(self.live.statement('fixture::A')['images']['a.gif'],self.uri)
        before=self.live.path.read_bytes()
        self.assertFalse(merge_public_seed(self.live,self.base.path,descriptor=self.descriptor,cache=self.root/'cache'))
        self.assertEqual(self.live.path.read_bytes(),before)
    def test_corrupt_transport_is_rejected_before_private_writes(self):
        payload=self.root/'payload'/self.result['descriptor']['payload'];payload.write_bytes(b'bad transport')
        before=self.live.path.read_bytes()
        with self.assertRaisesRegex(ValueError,'checksum'):merge_public_seed(self.live,self.base.path,descriptor=self.descriptor,cache=self.root/'cache')
        self.assertEqual(self.live.path.read_bytes(),before)
    def test_full_target_identity_with_old_physical_seed_needs_no_backup_or_mutation(self):
        self.live.merge_seed(self.target.path)
        self.assertEqual(self.live.metadata()['bundled_sha256'],self.result['targetSeedSha256'])
        before=self.live.path.read_bytes();files=set(self.root.rglob('*'))
        with patch.object(self.live,'backup',side_effect=AssertionError('A current target needs no recovery copy')) as backup, \
             patch.object(self.live,'merge_seed',side_effect=AssertionError('A current target must not merge the old seed')) as merge, \
             patch('public_library_update.unpack',side_effect=AssertionError('A current target needs no extracted overlay')):
            self.assertFalse(merge_public_seed(self.live,self.base.path,descriptor=self.descriptor,cache=self.root/'no-op-cache'))
        backup.assert_not_called();merge.assert_not_called()
        self.assertEqual(self.live.path.read_bytes(),before)
        self.assertEqual(set(self.root.rglob('*')),files)
        with self.live.connection() as db:
            self.assertEqual(db.execute('SELECT code FROM private_code').fetchone()[0],'owner draft remains')
            self.assertEqual(db.execute("SELECT markdown FROM solutions WHERE problem_id='fixture::A'").fetchone()[0],'my independent annotated solution')
    def test_composition_identity_stays_a_no_backup_no_mutation_operation(self):
        self.assertTrue(merge_public_seed(self.live,self.base.path,descriptor=self.descriptor,cache=self.root/'cache'))
        before=self.live.path.read_bytes();files=set(self.root.rglob('*'))
        with patch.object(self.live,'backup',side_effect=AssertionError('Composition already applied')) as backup, \
             patch.object(self.live,'merge_seed',side_effect=AssertionError('Composition already applied')) as merge, \
             patch('public_library_update.unpack',side_effect=AssertionError('Composition already applied')):
            self.assertFalse(merge_public_seed(self.live,self.base.path,descriptor=self.descriptor,cache=self.root/'cache'))
        backup.assert_not_called();merge.assert_not_called()
        self.assertEqual(self.live.path.read_bytes(),before)
        self.assertEqual(set(self.root.rglob('*')),files)
    def test_old_base_applies_one_partial_merge_and_preserves_unknown_private_table_in_recovery(self):
        private=b'isolated unknown private payload\x00\xff'
        with self.live.connection() as db:
            db.execute('CREATE TABLE local_extensions(id INTEGER PRIMARY KEY,payload BLOB)')
            db.execute('INSERT INTO local_extensions VALUES(7,?)',(private,))
        with patch.object(self.live,'merge_seed',wraps=self.live.merge_seed) as merge, \
             patch.object(self.live,'backup',wraps=self.live.backup) as backup:
            self.assertTrue(merge_public_seed(self.live,self.base.path,descriptor=self.descriptor,cache=self.root/'cache'))
        self.assertEqual(merge.call_count,1);self.assertEqual(backup.call_count,1)
        self.assertEqual(merge.call_args.kwargs['_partial'],self.result['descriptor']['membership'])
        self.assertEqual(merge.call_args.args[0].name,self.result['descriptor']['databaseSha256']+'.sqlite3')
        self.assertEqual(self.live.find('fixture::A')['encoded']['title'],'New public title')
        recoveries=list((self.root/'backups').glob('*.sqlite3'))
        self.assertEqual(len(recoveries),1)
        for path in (self.live.path,recoveries[0]):
            with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
                self.assertEqual(db.execute('SELECT payload FROM local_extensions WHERE id=7').fetchone()[0],private)
                self.assertEqual(db.execute('SELECT code FROM private_code').fetchone()[0],'owner draft remains')
    def test_unknown_state_identity_keeps_both_strict_merge_and_recovery_steps(self):
        private=b'unknown state retains private rows\x00\xfe'
        with self.live.connection() as db:
            db.execute("UPDATE library_meta SET value=? WHERE key='bundled_sha256'",('f'*64,))
            db.execute('CREATE TABLE local_extensions(payload BLOB)')
            db.execute('INSERT INTO local_extensions VALUES(?)',(private,))
        with patch.object(self.live,'merge_seed',wraps=self.live.merge_seed) as merge, \
             patch.object(self.live,'backup',wraps=self.live.backup) as backup:
            self.assertTrue(merge_public_seed(self.live,self.base.path,descriptor=self.descriptor,cache=self.root/'cache'))
        self.assertEqual(merge.call_count,2);self.assertEqual(backup.call_count,2)
        self.assertEqual(merge.call_args_list[0].args[0],self.base.path)
        self.assertNotIn('_partial',merge.call_args_list[0].kwargs)
        self.assertEqual(merge.call_args_list[1].kwargs['_partial'],self.result['descriptor']['membership'])
        recoveries=list((self.root/'backups').glob('*.sqlite3'))
        self.assertEqual(len(recoveries),2)
        for path in (self.live.path,*recoveries):
            with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
                self.assertEqual(db.execute('SELECT payload FROM local_extensions').fetchone()[0],private)
                self.assertEqual(db.execute('SELECT code FROM private_code').fetchone()[0],'owner draft remains')
    def test_target_marker_does_not_bypass_an_unrecognized_installed_seed(self):
        self.live.merge_seed(self.target.path)
        other=LibraryDatabase(self.root/'unrecognized.sqlite3');other.import_records([record('other::A')],{}, {})
        before=self.live.path.read_bytes()
        with self.assertRaisesRegex(ValueError,'installed public base'):
            merge_public_seed(self.live,other.path,descriptor=self.descriptor,cache=self.root/'cache')
        self.assertEqual(self.live.path.read_bytes(),before)
    def test_target_marker_does_not_bypass_corrupt_transport_validation(self):
        self.live.merge_seed(self.target.path)
        (self.descriptor.parent/self.result['descriptor']['payload']).write_bytes(b'corrupt transport remains rejected')
        before=self.live.path.read_bytes()
        with self.assertRaisesRegex(ValueError,'checksum'):
            merge_public_seed(self.live,self.base.path,descriptor=self.descriptor,cache=self.root/'cache')
        self.assertEqual(self.live.path.read_bytes(),before)
    def test_unrecognized_installed_seed_is_not_silently_replaced(self):
        other=LibraryDatabase(self.root/'other.sqlite3');other.import_records([record('other::A')],{}, {})
        before=self.live.path.read_bytes()
        with self.assertRaisesRegex(ValueError,'installed public base'):merge_public_seed(self.live,other.path,descriptor=self.descriptor,cache=self.root/'cache')
        self.assertEqual(self.live.path.read_bytes(),before)
    def test_source_with_private_tables_is_never_published(self):
        with self.target.connection() as db:db.execute('CREATE TABLE drafts(code TEXT)');db.execute("INSERT INTO drafts VALUES('private source fixture')")
        with self.assertRaisesRegex(ValueError,'public-only'):build([self.base.path],self.target.path,self.root/'rejected')
    def test_fresh_full_seed_uses_the_normal_merge_without_an_overlay(self):
        self.assertTrue(merge_public_seed(self.live,self.target.path,descriptor=self.descriptor,cache=self.root/'cache'))
        self.assertFalse((self.root/'cache').exists())
    def test_full_installer_marker_supersedes_old_overlay_and_rejects_wrong_seed(self):
        self.descriptor.write_text(json.dumps({'schema':1,'mode':'complete-seed','targetSeedSha256':self.result['targetSeedSha256']}))
        # A full install deliberately ignores an obsolete transport left from
        # a prior compact installation, even if that old file is corrupt.
        (self.descriptor.parent/self.result['descriptor']['payload']).write_bytes(b'obsolete row payload')
        before=self.live.path.read_bytes()
        with self.assertRaisesRegex(ValueError,'complete public seed'):merge_public_seed(self.live,self.base.path,descriptor=self.descriptor)
        self.assertEqual(self.live.path.read_bytes(),before)
        self.assertTrue(merge_public_seed(self.live,self.target.path,descriptor=self.descriptor,cache=self.root/'cache'))
        self.assertFalse((self.root/'cache').exists())
    def test_cache_filename_collision_preserves_the_existing_private_file(self):
        cache=self.root/'collision';cache.mkdir();private=cache/(self.result['descriptor']['databaseSha256']+'.sqlite3')
        collision=self.make_live(private)
        self.assertTrue(merge_public_seed(collision,self.base.path,descriptor=self.descriptor,cache=cache))
        with collision.connection() as db:self.assertEqual(db.execute('SELECT code FROM private_code').fetchone()[0],'owner draft remains')
        self.assertTrue(list(cache.glob('*-recovered-*.sqlite3')))
    def test_old_inline_image_is_reused_without_shipping_its_bytes_again(self):
        base=LibraryDatabase(self.root/'inline-base.sqlite3');base.import_records([record()],{}, {})
        statement={'markdown':'Original figure','images':{'a.gif':self.uri},'samples':[{'input':'1','output':'2'}]}
        with base.connection() as db:db.execute('INSERT OR REPLACE INTO statements VALUES(?,?)',('fixture::A',json.dumps(statement)))
        with base.connection() as source,closing(sqlite3.connect(self.root/'inline-target.sqlite3')) as destination:source.backup(destination)
        target=LibraryDatabase(self.root/'inline-target.sqlite3');target.save_statement('fixture::A',statement)
        result=build([base.path],target.path,self.root/'inline-payload')
        self.assertEqual(result['descriptor']['rowCounts']['statement_assets'],0)
        self.assertEqual(len(result['descriptor']['baseInlineAssets'][result['descriptor']['baseSeeds'][0]]),1)
        live=LibraryDatabase(self.root/'inline-live.sqlite3');live.merge_seed(base.path)
        self.assertTrue(merge_public_seed(live,base.path,descriptor=self.root/'inline-payload/public-library-update.json',cache=self.root/'inline-cache'))
        self.assertEqual(live.statement('fixture::A')['images']['a.gif'],self.uri)
        self.assertEqual(base.statement('fixture::A')['images']['a.gif'],self.uri)
    def test_superset_delta_matches_full_merges_from_different_released_contents(self):
        with self.base.connection() as source,closing(sqlite3.connect(self.root/'second-base.sqlite3')) as destination:source.backup(destination)
        second=LibraryDatabase(self.root/'second-base.sqlite3');second.import_records([record(title='Other released title')],{}, {'fixture::B':[]})
        result=build([self.base.path,second.path],self.target.path,self.root/'multi-payload')
        for index,base in enumerate((self.base,second)):
            with self.subTest(base=index):
                live=LibraryDatabase(self.root/('multi-live-'+str(index)+'.sqlite3'));live.merge_seed(base.path)
                reference=LibraryDatabase(self.root/('multi-reference-'+str(index)+'.sqlite3'));reference.merge_seed(base.path);reference.merge_seed(self.target.path)
                self.assertTrue(merge_public_seed(live,base.path,descriptor=self.root/'multi-payload/public-library-update.json',cache=self.root/('multi-cache-'+str(index))))
                self.assertEqual(self.rows(live),self.rows(reference))
        self.assertEqual(len(result['descriptor']['baseSeeds']),2)
    def test_missing_declared_inline_asset_fails_before_private_writes(self):
        value=json.loads(self.descriptor.read_text('utf8'));value['baseInlineAssets'][value['baseSeeds'][0]]=[{'sha256':'0'*64,'mime':'image/png','bytes':10}]
        self.descriptor.write_text(json.dumps(value));before=self.live.path.read_bytes()
        with self.assertRaisesRegex(ValueError,'inline public resource is missing'):merge_public_seed(self.live,self.base.path,descriptor=self.descriptor,cache=self.root/'cache')
        self.assertEqual(self.live.path.read_bytes(),before)
    def test_old_editorial_inline_image_is_reused_by_both_variants(self):
        digest=hashlib.sha256(base64.b64decode(self.uri.split(',',1)[1])).hexdigest()
        for library in (self.base,self.target):
            with library.connection() as db:
                for table in ('solutions','detailed_solutions'):
                    db.execute('INSERT OR REPLACE INTO '+table+' VALUES(?,?,?,?,?)',('fixture::A','![Figure](a.gif)','reviewed.md',json.dumps({'a.gif':self.uri}),'reviewed-markdown-digest'))
        with self.target.connection() as db:
            db.execute('INSERT OR IGNORE INTO statement_assets VALUES(?,?,?)',(digest,'image/gif',base64.b64decode(self.uri.split(',',1)[1])))
            for table in ('solutions','detailed_solutions'):
                db.execute('UPDATE '+table+' SET images=? WHERE problem_id=?',(json.dumps({'a.gif':'tb-asset:'+digest}),'fixture::A'))
        result=build([self.base.path],self.target.path,self.root/'editorial-payload')
        self.assertEqual(result['descriptor']['rowCounts']['statement_assets'],0)
        live=LibraryDatabase(self.root/'editorial-live.sqlite3');live.merge_seed(self.base.path)
        reference=LibraryDatabase(self.root/'editorial-reference.sqlite3');reference.merge_seed(self.base.path);reference.merge_seed(self.target.path)
        self.assertTrue(merge_public_seed(live,self.base.path,descriptor=self.root/'editorial-payload/public-library-update.json',cache=self.root/'editorial-cache'))
        self.assertEqual(self.rows(live),self.rows(reference))
        for variant in ('default','detailed'):self.assertEqual(live.solution('fixture::A',variant)['images']['a.gif'],self.uri)
    def test_multiple_fetched_overrides_are_preserved_independently_in_both_merge_paths(self):
        # An earlier fetched statement must not replace the table-wide row
        # lookup with its own JSON dictionary and overwrite later overrides.
        for path in (self.base.path,self.target.path):
            library=LibraryDatabase(path)
            library.save_statement('fixture::A',{'markdown':'bundled A','samples':[]})
            library.save_statement('fixture::B',{'markdown':'bundled B','samples':[]})
        # Make both rows part of the public delta while keeping a different
        # original in the fetched private cache.
        self.target.save_statement('fixture::A',{'markdown':'updated bundled A','samples':[]})
        self.target.save_statement('fixture::B',{'markdown':'updated bundled B','samples':[]})
        build([self.base.path],self.target.path,self.root/'overrides-payload')
        for name,partial in (('full',False),('partial',True)):
            with self.subTest(merge=name):
                live=LibraryDatabase(self.root/('override-'+name+'.sqlite3'));live.merge_seed(self.base.path)
                with live.connection() as db:
                    for pid in ('fixture::A','fixture::B'):
                        db.execute('UPDATE statements SET content=? WHERE problem_id=?',(json.dumps({'markdown':'fetched '+pid,'samples':[],'privateNote':'keep independent metadata'}),pid))
                if partial:merge_public_seed(live,self.base.path,descriptor=self.root/'overrides-payload/public-library-update.json',cache=self.root/'overrides-cache')
                else:live.merge_seed(self.target.path)
                for pid in ('fixture::A','fixture::B'):
                    value=live.statement(pid);self.assertEqual(value['markdown'],'fetched '+pid);self.assertEqual(value['privateNote'],'keep independent metadata')
if __name__=='__main__':unittest.main()
