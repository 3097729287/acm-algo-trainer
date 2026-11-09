"""One 1.6.11 transport keeps each complete approved public profile intact."""
from contextlib import closing
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_compact_bundle import build
from build_public_library_update import build as row_build
from compact_update import apply,load,select,sha,BaseMismatch,PUBLIC_SEED,PUBLIC_IDENTITY,PUBLIC_DESCRIPTOR
from library import LibraryDatabase
from seed_identity import describe
from test_library import record


class PreservedPublicProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.target=LibraryDatabase(self.root/'target.sqlite3')
        self.target.import_records([record(title='Reviewed current target')],{}, {})
        self.target_sha=sha(self.target.path)
        self.package=self.root/'package'
        self.write_program(self.package,'1.6.12',b'new public executable fixture')
        self.install_profile(self.package,self.target.path,None)
        info={'schema':1,'version':'1.6.12','commit':'1'*40,'publicLibrarySha256':self.target_sha}
        for name in ('BUILD-INFO.json','resources/BUILD-INFO.json'):self.write(self.package/name,json.dumps(info).encode())
        self.bases=[]
        for index in range(8):
            seed=LibraryDatabase(self.root/('seed-'+str(index)+'.sqlite3'))
            seed.import_records([record(title='Original public seed '+str(index))],{}, {})
            rows=self.root/('rows-'+str(index));row_build([seed.path],self.target.path,rows)
            base=self.root/('base-'+str(index));self.write_program(base,'1.6.11',b'old public executable fixture')
            self.install_profile(base,seed.path,rows);self.bases.append(base)
        full=self.root/'base-full';self.write_program(full,'1.6.11',b'old public executable fixture')
        self.install_profile(full,self.target.path,None);self.bases.append(full)
        self.bundle=self.root/'update.zip'
        self.canonical_before=self.snapshot(self.package)
        build(self.package,self.bases,self.bundle,self.root,preserve_existing_public_profiles=True)
        with zipfile.ZipFile(self.bundle) as archive:self.value=load(archive,'1.6.12')

    def write(self,path,data):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)

    def write_program(self,path,version,executable):
        self.write(path/'VERSION',(version+'\n').encode());self.write(path/'ToBe.exe',executable)
        self.write(path/'_internal/runtime.bin',b'unchanged runtime anchor')
        self.write(path/'resources/unrelated.json',b'new other resource' if version=='1.6.12' else b'old other resource')
        # This name is deliberately outside every preserved combination.
        self.write(path/'resources/public-library-update-other.sqlite3.gz',b'new unrelated resource' if version=='1.6.12' else b'old unrelated resource')

    def install_profile(self,path,seed,rows):
        self.write(path/PUBLIC_SEED,seed.read_bytes())
        self.write(path/PUBLIC_IDENTITY,json.dumps(describe(seed)).encode())
        if rows is None:
            descriptor={'schema':1,'mode':'complete-seed','targetSeedSha256':self.target_sha}
            self.write(path/PUBLIC_DESCRIPTOR,json.dumps(descriptor).encode())
        else:
            descriptor=json.loads((rows/'public-library-update.json').read_text('utf8'))
            self.write(path/PUBLIC_DESCRIPTOR,(rows/'public-library-update.json').read_bytes())
            self.write(path/'resources'/descriptor['payload'],(rows/descriptor['payload']).read_bytes())

    def snapshot(self,path):
        return {p.relative_to(path).as_posix():p.read_bytes() for p in path.rglob('*') if p.is_file()}

    def app(self,index,name='app'):
        path=self.root/name;shutil.copytree(self.bases[index],path)
        private=path/'state/tb-personal.sqlite3';private.parent.mkdir()
        with closing(sqlite3.connect(private)) as db,db:
            db.execute('CREATE TABLE unknown_private_rows(id INTEGER PRIMARY KEY,value BLOB)')
            db.execute('INSERT INTO unknown_private_rows VALUES(7,?)',(b'draft\x00\xff, account and submission fixture',))
        return path

    def rewrite(self,value):
        with zipfile.ZipFile(self.bundle) as archive:
            members={name:archive.read(name) for name in archive.namelist() if name!='compact.json'}
        destination=self.root/('modified-'+str(len(list(self.root.glob('modified-*.zip'))))+'.zip')
        with zipfile.ZipFile(destination,'x') as archive:
            archive.writestr('compact.json',json.dumps(value))
            for name,data in members.items():archive.writestr(name,data)
        return destination

    def assert_rejected_without_writes(self,app,bundle=None,error=ValueError):
        before=self.snapshot(app)
        with self.assertRaises(error):apply(bundle or self.bundle,app,'1.6.12')
        self.assertEqual(self.snapshot(app),before)
        self.assertFalse((app/'cache').exists())

    def test_all_nine_layouts_apply_without_changing_public_profile_or_private_bytes(self):
        policy=self.value['preservedPublicProfiles']
        self.assertEqual(len(policy['combinations']),9)
        for index,combination in enumerate(policy['combinations']):
            with self.subTest(layout=index):
                app=self.app(index,'success-'+str(index));before=self.snapshot(app)
                self.assertTrue(apply(self.bundle,app,'1.6.12')['ok'])
                for name in combination:self.assertEqual((app/name).read_bytes(),before[name])
                self.assertEqual((app/'state/tb-personal.sqlite3').read_bytes(),before['state/tb-personal.sqlite3'])
                self.assertEqual((app/'VERSION').read_bytes(),b'1.6.12\n')
                self.assertEqual((app/'resources/unrelated.json').read_bytes(),b'new other resource')
                self.assertEqual((app/'resources/public-library-update-other.sqlite3.gz').read_bytes(),b'new unrelated resource')
                info=json.loads((app/'BUILD-INFO.json').read_text('utf8'))
                self.assertNotIn('publicLibrarySha256',info)
                self.assertEqual(info['publicLibraryTargetSha256'],self.target_sha)
        self.assertEqual(self.snapshot(self.package),self.canonical_before)

    def test_each_layout_rolls_back_every_original_byte_at_each_replacement(self):
        for index in range(9):
            for position in range(len(select(self.bases[index],self.value)[0])):
                with self.subTest(layout=index,replacement=position):
                    app=self.app(index,'rollback-'+str(index)+'-'+str(position));before=self.snapshot(app)
                    with self.assertRaises(OSError):apply(self.bundle,app,'1.6.12',fail_after=position)
                    for name,data in before.items():self.assertEqual((app/name).read_bytes(),data)
                    self.assertFalse((app/'BUILD-INFO.json').exists())

    def test_unknown_and_mixed_approved_files_are_rejected_before_any_write(self):
        app=self.app(0,'unknown');(app/PUBLIC_SEED).write_bytes(b'unknown seed rebuild')
        self.assert_rejected_without_writes(app,error=BaseMismatch)
        app=self.app(0,'mixed')
        (app/PUBLIC_IDENTITY).write_bytes((self.bases[1]/PUBLIC_IDENTITY).read_bytes())
        self.assert_rejected_without_writes(app,error=BaseMismatch)

    def test_shape_extra_paths_write_overlap_duplicates_and_excess_combinations_are_rejected(self):
        bad=[]
        for name in ('state/tb-personal.sqlite3','resources/../outside','resources/other.json','data/other.sqlite3'):
            value=deepcopy(self.value);combination=value['preservedPublicProfiles']['combinations'][0]
            combination.pop(next(path for path in combination if path.endswith('.gz')))
            combination[name]='0'*64;bad.append(value)
        value=deepcopy(self.value);value['files'][PUBLIC_DESCRIPTOR]=deepcopy(value['files']['VERSION']);bad.append(value)
        value=deepcopy(self.value);value['preservedPublicProfiles']['combinations'][1]=deepcopy(value['preservedPublicProfiles']['combinations'][0]);bad.append(value)
        value=deepcopy(self.value);value['preservedPublicProfiles']['combinations'].append(deepcopy(value['preservedPublicProfiles']['combinations'][0]));bad.append(value)
        value=deepcopy(self.value);value['preservedPublicProfiles']['combinations']=[];bad.append(value)
        value=deepcopy(self.value);value['preservedPublicProfiles']['unexpected']=True;bad.append(value)
        value=deepcopy(self.value);value['preservedPublicProfiles']['targetSeedSha256']='bad';bad.append(value)
        for index,value in enumerate(bad):
            with self.subTest(case=index):self.assert_rejected_without_writes(self.app(0,'shape-'+str(index)),self.rewrite(value))

    def test_actual_descriptor_payload_and_target_must_agree_even_when_every_hash_matches(self):
        for index,field in enumerate(('payload','payloadSha256','targetSeedSha256','payloadBytes')):
            app=self.app(0,'binding-'+str(index));value=deepcopy(self.value)
            path=app/PUBLIC_DESCRIPTOR;descriptor=json.loads(path.read_text('utf8'))
            descriptor[field]=1 if field=='payloadBytes' else '0'*64
            path.write_text(json.dumps(descriptor),encoding='utf8')
            value['preservedPublicProfiles']['combinations'][0][PUBLIC_DESCRIPTOR]=sha(path)
            self.assert_rejected_without_writes(app,self.rewrite(value),BaseMismatch)

    def test_corrupt_gzip_and_missing_gzip_are_rejected_before_any_write(self):
        for index,missing in enumerate((False,True)):
            app=self.app(0,'gzip-'+str(index))
            combination=self.value['preservedPublicProfiles']['combinations'][0]
            payload=next(name for name in combination if name.endswith('.gz'))
            if missing:(app/payload).unlink()
            else:(app/payload).write_bytes(b'corrupt existing public gzip')
            self.assert_rejected_without_writes(app,error=BaseMismatch)

    def test_seed_is_hashed_once_when_selecting_among_nine_combinations(self):
        app=self.app(7);seen=[]
        def counted(path):seen.append(Path(path));return sha(path)
        with patch('compact_update.sha',side_effect=counted):select(app,self.value)
        self.assertEqual(seen.count(app/PUBLIC_SEED),1)

    def test_builder_rejects_changed_public_target_and_other_installed_versions(self):
        descriptor=self.bases[0]/PUBLIC_DESCRIPTOR
        value=json.loads(descriptor.read_text('utf8'));value['targetSeedSha256']='0'*64
        descriptor.write_text(json.dumps(value),encoding='utf8')
        with self.assertRaisesRegex(ValueError,'different target'):
            build(self.package,self.bases,self.root/'bad-target.zip',self.root,preserve_existing_public_profiles=True)
        (self.bases[0]/'VERSION').write_text('1.6.10\n')
        with self.assertRaisesRegex(ValueError,'one payload per installed version'):
            build(self.package,self.bases,self.root/'bad-version.zip',self.root,preserve_existing_public_profiles=True)
        self.assertFalse((self.root/'bad-target.zip').exists());self.assertFalse((self.root/'bad-version.zip').exists())

    def test_default_builder_keeps_the_legacy_manifest_without_optional_policy(self):
        bundle=self.root/'legacy-default.zip'
        build(self.package,[self.bases[8]],bundle,self.root)
        with zipfile.ZipFile(bundle) as archive:value=load(archive,'1.6.12')
        self.assertNotIn('preservedPublicProfiles',value)
        self.assertIn(PUBLIC_DESCRIPTOR,value['files'])
        self.assertTrue(apply(bundle,self.app(8),'1.6.12')['ok'])

    def test_old_row_overlay_preservation_mode_remains_independent(self):
        profile=self.root/'legacy-row-profile';shutil.copytree(self.package,profile)
        (profile/PUBLIC_DESCRIPTOR).write_bytes((self.bases[0]/PUBLIC_DESCRIPTOR).read_bytes())
        descriptor=json.loads((profile/PUBLIC_DESCRIPTOR).read_text('utf8'))
        shutil.copyfile(self.bases[0]/'resources'/descriptor['payload'],profile/'resources'/descriptor['payload'])
        bundle=self.root/'legacy-overlay.zip'
        build(profile,[self.bases[0]],bundle,self.root,preserve_public_seed=True)
        with zipfile.ZipFile(bundle) as archive:value=load(archive,'1.6.12')
        self.assertNotIn('preservedPublicProfiles',value)
        self.assertEqual(value['publicLibrary']['mode'],'public-row-overlay')
        app=self.app(0);before=(app/PUBLIC_SEED).read_bytes()
        self.assertTrue(apply(bundle,app,'1.6.12')['ok'])
        self.assertEqual((app/PUBLIC_SEED).read_bytes(),before)
        with self.assertRaisesRegex(ValueError,'one public preservation mode'):
            build(profile,[self.bases[0]],self.root/'both-modes.zip',self.root,preserve_public_seed=True,preserve_existing_public_profiles=True)


if __name__=='__main__':unittest.main()
