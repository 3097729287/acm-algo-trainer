"""Synthetic tiny SQLite profiles; actual builder/applier, never a real app."""
from pathlib import Path
import hashlib,json,sqlite3,sys,tempfile,unittest,zipfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('scripts','desktop','backend')]
from build_compact_bundle import build
from compact_update import apply,load,PUBLIC_SEED,PUBLIC_IDENTITY,PUBLIC_DESCRIPTOR
from seed_identity import describe

def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

class CompactProfileVersionTests(unittest.TestCase):
    def setUp(self):
        # Retain these tiny cases and any failure; never delete another test's
        # evidence or place artificial private rows in a public/native stage.
        self.root=Path(tempfile.mkdtemp(prefix='ToBe-compact-versions-test-'))
        self.target=self.package('target','1.6.13',new=True)
        self.scratch=patch.object(tempfile,'tempdir',str(self.root));self.scratch.start()
    def tearDown(self):self.scratch.stop()
    def package(self,name,version,new=False):
        folder=self.root/name;folder.mkdir();(folder/'data').mkdir();(folder/'resources').mkdir()
        (folder/'VERSION').write_text(version,encoding='utf8')
        (folder/'ToBe.exe').write_bytes(b'new synthetic core' if new else b'old synthetic core')
        with sqlite3.connect(folder/PUBLIC_SEED) as db:
            db.execute('CREATE TABLE public_fixture(id INTEGER PRIMARY KEY,value TEXT)')
            db.execute("INSERT INTO public_fixture VALUES(1,'public test content')")
        seed=sha(folder/PUBLIC_SEED)
        (folder/PUBLIC_IDENTITY).write_text(json.dumps(describe(folder/PUBLIC_SEED)),encoding='utf8')
        (folder/PUBLIC_DESCRIPTOR).write_text(json.dumps({'schema':1,'mode':'complete-seed','targetSeedSha256':seed}),encoding='utf8')
        for name in ('BUILD-INFO.json','resources/BUILD-INFO.json'):
            (folder/name).write_text(json.dumps({'version':version,'publicLibrarySha256':seed}),encoding='utf8')
        return folder
    def bundle(self,bases,name='compact.zip'):
        output=self.root/name
        return output,build(self.target,bases,output,self.root/'unused-bsdiff-tool',preserve_existing_public_profiles=True)

    def test_each_approved_single_version_builds_and_applies_without_private_or_seed_changes(self):
        for version in ('1.6.11','1.6.12'):
            with self.subTest(version=version):
                base=self.package('base-'+version,version);private=base/'state/tb-personal.sqlite3';private.parent.mkdir()
                with sqlite3.connect(private) as db:
                    db.execute('CREATE TABLE unknown_private(id INTEGER PRIMARY KEY,value BLOB)')
                    db.execute('INSERT INTO unknown_private VALUES(7,?)',(b'unit fixture only\x00\xff',))
                prior={name:sha(base/name) for name in (PUBLIC_SEED,PUBLIC_IDENTITY,PUBLIC_DESCRIPTOR)}
                private_hash=sha(private);output,result=self.bundle([base],version+'.zip')
                self.assertEqual(result['fromVersion'],version)
                with zipfile.ZipFile(output) as archive:manifest=load(archive,'1.6.13')
                self.assertEqual(manifest['preservedPublicProfiles']['combinations'],[prior])
                self.assertFalse(set(prior)&set(manifest['files']))
                self.assertFalse(any(name.startswith('state/') for name in manifest['files']))
                self.assertTrue(apply(output,base,'1.6.13')['ok'])
                self.assertEqual((base/'ToBe.exe').read_bytes(),b'new synthetic core')
                self.assertEqual({name:sha(base/name) for name in prior},prior)
                self.assertEqual(sha(private),private_hash)
                with sqlite3.connect(private) as db:self.assertEqual(db.execute('SELECT * FROM unknown_private').fetchall(),[(7,b'unit fixture only\x00\xff')])

    def test_mixed_approved_versions_still_refuse_before_output(self):
        with self.assertRaisesRegex(ValueError,'one payload per installed version'):
            self.bundle([self.package('a','1.6.11'),self.package('b','1.6.12')])
        self.assertFalse((self.root/'compact.zip').exists())

    def test_other_single_versions_including_target_still_refuse(self):
        for version in ('1.6.10','1.6.13','2.0.0'):
            with self.subTest(version=version),self.assertRaisesRegex(ValueError,'single-version approved'):
                self.bundle([self.package('base-'+version,version)],version+'.zip')
            self.assertFalse((self.root/(version+'.zip')).exists())

    def test_112_descriptor_target_is_still_bound_to_the_canonical_seed(self):
        base=self.package('base','1.6.12');path=base/PUBLIC_DESCRIPTOR
        descriptor=json.loads(path.read_text('utf8'));descriptor['targetSeedSha256']='0'*64
        path.write_text(json.dumps(descriptor),encoding='utf8')
        with self.assertRaisesRegex(ValueError,'different target'):self.bundle([base])
        self.assertFalse((self.root/'compact.zip').exists())

    def test_112_cannot_exceed_the_existing_nine_combination_limit(self):
        bases=[]
        for index in range(10):
            base=self.package('base-'+str(index),'1.6.12')
            # Different byte identities with equal parsed complete descriptors
            # are still ten distinct hash-pinned public combinations.
            path=base/PUBLIC_DESCRIPTOR;path.write_text((' '*index)+path.read_text('utf8'),encoding='utf8')
            bases.append(base)
        with self.assertRaisesRegex(ValueError,'Invalid preserved public profiles'):self.bundle(bases)
        self.assertFalse((self.root/'compact.zip').exists())

if __name__=='__main__':unittest.main()
