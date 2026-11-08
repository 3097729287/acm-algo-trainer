"""The unchanged compact installer keeps and authenticates its public base."""
from contextlib import closing
import json,shutil,sqlite3,sys,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common'),str(ROOT/'scripts'),str(ROOT/'desktop')]
from library import LibraryDatabase
from test_library import record
from seed_identity import describe
from build_public_library_update import build as build_rows
from build_compact_bundle import build
from build_public_row_profile import build as build_profile
from compact_update import apply,load,BaseMismatch
from public_library_update import merge_public_seed

class PublicRowBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.base=self.root/'old';self.target=self.root/'new'
        for package,version in ((self.base,'1.6.9'),(self.target,'1.6.11')):
            (package/'data').mkdir(parents=True);(package/'resources').mkdir();(package/'_internal').mkdir()
            (package/'VERSION').write_text(version);(package/'ToBe.exe').write_bytes(b'isolated native fixture')
            (package/'_internal/base_library.zip').write_bytes(b'isolated runtime fixture')
            library=LibraryDatabase(package/'data/library.sqlite3');library.import_records([record(title='old' if package==self.base else 'new')],{}, {})
            (package/'resources/library-seed-identity.json').write_text(json.dumps(describe(library.path)))
        rows=build_rows([self.base/'data/library.sqlite3'],self.target/'data/library.sqlite3',self.root/'rows')
        for name in ('public-library-update.json',rows['descriptor']['payload']):shutil.copyfile(self.root/'rows'/name,self.target/'resources'/name)
        self.bundle=self.root/'compact.zip';build(self.target,[self.base],self.bundle,self.root/'unused-tool',preserve_public_seed=True)
    def test_old_installer_preserves_base_and_new_runtime_matches_the_full_seed(self):
        seed=self.base/'data/library.sqlite3';identity=self.base/'resources/library-seed-identity.json'
        original=(seed.read_bytes(),identity.read_bytes())
        private=LibraryDatabase(self.root/'private.sqlite3');private.merge_seed(seed)
        reference=LibraryDatabase(self.root/'reference.sqlite3');reference.merge_seed(seed);reference.merge_seed(self.target/'data/library.sqlite3')
        with zipfile.ZipFile(self.bundle) as archive:
            manifest=load(archive,'1.6.11')
            self.assertNotIn('data/library.sqlite3',manifest['files']);self.assertNotIn('resources/library-seed-identity.json',manifest['files'])
            self.assertIn('data/library.sqlite3',manifest['anchors']);self.assertIn('resources/library-seed-identity.json',manifest['anchors'])
        self.assertTrue(apply(self.bundle,self.base,'1.6.11')['ok'])
        self.assertEqual((seed.read_bytes(),identity.read_bytes()),original)
        self.assertTrue(merge_public_seed(private,seed,descriptor=self.base/'resources/public-library-update.json',cache=self.root/'cache'))
        self.assertEqual(private.rows(),reference.rows())
    def test_changed_installed_public_seed_fails_before_replacing_programs(self):
        seed=self.base/'data/library.sqlite3'
        with closing(sqlite3.connect(seed)) as db,db:db.execute("UPDATE problems SET url='changed locally'")
        before=seed.read_bytes()
        with self.assertRaises(BaseMismatch):apply(self.bundle,self.base,'1.6.11')
        self.assertEqual((self.base/'VERSION').read_text(),'1.6.9');self.assertEqual(seed.read_bytes(),before)
    def test_interrupted_program_replacement_restores_program_and_preserves_seed(self):
        seed=self.base/'data/library.sqlite3';before=seed.read_bytes()
        with self.assertRaises(OSError):apply(self.bundle,self.base,'1.6.11',fail_after=0)
        self.assertEqual((self.base/'VERSION').read_text(),'1.6.9');self.assertEqual(seed.read_bytes(),before)
        self.assertTrue(apply(self.bundle,self.base,'1.6.11')['ok'])
    def test_baseline_specific_profile_keeps_full_build_immutable_and_reports_actual_seed_mode(self):
        full=self.root/'full-installer';shutil.copytree(self.target,full)
        info={'version':'1.6.11','sourceCommit':'reviewed-fixture','publicLibrarySha256':describe(full/'data/library.sqlite3')['sha256']}
        for name in ('BUILD-INFO.json','resources/BUILD-INFO.json'):(full/name).write_text(json.dumps(info))
        (full/'resources/public-library-update.json').write_text(json.dumps({'schema':1,'mode':'complete-seed','targetSeedSha256':info['publicLibrarySha256']}))
        old_payload=next((full/'resources').glob('public-library-update-*.sqlite3.gz'));old_payload.unlink()
        before=(full/'BUILD-INFO.json').read_bytes();profile=self.root/'baseline-profile'
        result=build_profile(full,self.root/'rows',profile)
        self.assertEqual((full/'BUILD-INFO.json').read_bytes(),before)
        generated=json.loads((profile/'BUILD-INFO.json').read_text())
        self.assertNotIn('publicLibrarySha256',generated);self.assertEqual(generated['publicLibraryTargetSha256'],info['publicLibrarySha256'])
        self.assertEqual(generated['publicLibraryMode'],'preserved-base-with-public-row-update')
        self.assertTrue(result['privateStateReadOrWritten'] is False)
        bundle=self.root/'profile-compact.zip';build(profile,[self.base],bundle,self.root/'unused-tool',preserve_public_seed=True)
        self.assertTrue(apply(bundle,self.base,'1.6.11')['ok'])
if __name__=='__main__':unittest.main()
