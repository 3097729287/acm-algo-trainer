"""Installer transaction boundaries, retained private state and recovery."""
import hashlib
from contextlib import closing
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from compact_update import apply,BaseMismatch,document,exclusive,public_path,trim_recoveries


def digest(data):return hashlib.sha256(data).hexdigest()


class CompactUpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.app=self.root/'app';self.app.mkdir()
        self.old={'ToBe.exe':b'isolated old application, never executed','VERSION':b'1.6.6\n','frontend/dist/index.html':b'old page'}
        self.new={'ToBe.exe':b'isolated new application, never executed','VERSION':b'1.6.8\n','frontend/dist/index.html':b'new page','resources/new.json':b'{"reviewed":true}'}
        for name,data in self.old.items():p=self.app/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        self.private=self.app/'state/tb-personal.sqlite3';self.private.parent.mkdir()
        with closing(sqlite3.connect(self.private)) as db,db:
            db.execute('CREATE TABLE records(kind TEXT PRIMARY KEY,value TEXT)')
            db.executemany('INSERT INTO records VALUES(?,?)',[('account','retained identity'),('draft','中文代码😀'),('submission','real history fixture'),('training','saved plan')])
        self.custom=self.app/'frontend/dist/custom-owned.txt';self.custom.write_text('keep local file',encoding='utf-8')
        self.deepseek_private={
            'cache/tb-deepseek-webview2/owner-A/ToBeDeepSeek/Cookies':b'isolated persistent cookie marker',
            'cache/tb-deepseek-webview2/owner-A/ToBeDeepSeek/Local Storage/leveldb/fixture':b'isolated persistent local storage marker'}
        for name,data in self.deepseek_private.items():
            target=self.app/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        self.private_before=self.private.read_bytes();self.bundle=self.root/'compact.zip';self.make_bundle()

    def make_bundle(self,*,unsafe=False,corrupt=False):
        payloads={};files={};raws={}
        for name,data in self.new.items():
            sha=digest(data);key='payloads/'+sha+'.bin';payloads[key]={'sha256':sha,'bytes':len(data)};raws[key]=data
            files[name]={'sha256':sha,'bytes':len(data),'variants':[{'format':'literal','payload':key}]}
        if unsafe:files['state/tb-personal.sqlite3']=files.pop('resources/new.json')
        value={'schema':1,'version':'1.6.8','anchors':{'ToBe.exe':[digest(self.old['ToBe.exe']),digest(self.new['ToBe.exe'])]},'files':files,'payloads':payloads}
        with zipfile.ZipFile(self.bundle,'w',zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('compact.json',json.dumps(value))
            for index,(name,data) in enumerate(raws.items()):archive.writestr(name,b'x'*len(data) if corrupt and index==0 else data)

    def assert_private(self):
        self.assertEqual(self.private.read_bytes(),self.private_before);self.assertEqual(self.custom.read_text(encoding='utf-8'),'keep local file')
        for name,data in self.deepseek_private.items():self.assertEqual((self.app/name).read_bytes(),data)

    def test_check_is_read_only_and_success_replaces_only_managed_program_files(self):
        value=apply(self.bundle,self.app,'1.6.8',check=True);self.assertTrue(value['compatible'])
        for name,data in self.old.items():self.assertEqual((self.app/name).read_bytes(),data)
        result=apply(self.bundle,self.app,'1.6.8');self.assertTrue(result['ok'])
        for name,data in self.new.items():self.assertEqual((self.app/name).read_bytes(),data)
        self.assert_private()
        self.assertEqual(apply(self.bundle,self.app,'1.6.8')['changedFiles'],0)

    def test_failure_at_each_replacement_restores_the_whole_original_program(self):
        for position in range(len(self.new)):
            with self.subTest(position=position):
                with self.assertRaises(OSError):apply(self.bundle,self.app,'1.6.8',fail_after=position)
                for name,data in self.old.items():self.assertEqual((self.app/name).read_bytes(),data)
                self.assertFalse((self.app/'resources/new.json').exists());self.assert_private()

    def test_unrecognized_baseline_requires_full_installer_without_modification(self):
        (self.app/'ToBe.exe').write_bytes(b'unknown rebuild')
        with self.assertRaises(BaseMismatch):apply(self.bundle,self.app,'1.6.8')
        self.assertEqual((self.app/'VERSION').read_bytes(),self.old['VERSION']);self.assert_private()

    def test_corrupt_payload_is_rejected_before_the_first_replacement(self):
        self.make_bundle(corrupt=True)
        with self.assertRaises(ValueError):apply(self.bundle,self.app,'1.6.8')
        for name,data in self.old.items():self.assertEqual((self.app/name).read_bytes(),data)
        self.assert_private()

    def test_payload_cannot_change_private_state_or_escape_public_root(self):
        self.make_bundle(unsafe=True)
        with self.assertRaises(ValueError):apply(self.bundle,self.app,'1.6.8')
        for name in ['state/tb-personal.sqlite3','resources/../../outside','resources/CON','/resources/new.json','compiler/../state/data']:
            with self.subTest(path=name),self.assertRaises(ValueError):public_path(self.app,name)
        self.assert_private()

    def test_interrupted_commit_is_restored_before_retrying_verified_update(self):
        cache=self.app/'cache/updates';cache.mkdir(parents=True);folder=cache/'compact-interrupted';folder.mkdir()
        for name,data in self.old.items():p=folder/'old'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        journal={'status':'applying','version':'1.6.8','previous':{k:digest(v) for k,v in self.old.items()},'new':{k:digest(self.new[k]) for k in self.old}}
        document(folder/'journal.json',journal);document(cache/'compact-active.json',{'folder':str(folder)})
        (self.app/'ToBe.exe').write_bytes(self.new['ToBe.exe'])
        with self.assertRaises(BaseMismatch):apply(self.bundle,self.app,'1.6.8',check=True)
        result=apply(self.bundle,self.app,'1.6.8');self.assertTrue(result['ok']);self.assert_private()
        self.assertEqual(json.loads((folder/'journal.json').read_text())['status'],'rolled-back')

    def test_another_installer_cannot_reenter_the_live_transaction(self):
        cache=self.app/'cache/updates';cache.mkdir(parents=True)
        with exclusive(cache/'compact-update.lock'):
            with self.assertRaises(OSError):apply(self.bundle,self.app,'1.6.8')
        self.assert_private()

    def test_unchanged_compiler_inventory_is_not_rehashed_or_copied_at_runtime(self):
        compiler=self.app/'compiler/large-unchanged-compiler.dll';compiler.parent.mkdir()
        compiler.write_bytes(b'unchanged compiler fixture')
        with zipfile.ZipFile(self.bundle) as archive:
            members={name:archive.read(name) for name in archive.namelist()}
        value=json.loads(members['compact.json'])
        value['files']['compiler/large-unchanged-compiler.dll']={'sha256':digest(compiler.read_bytes()),'bytes':compiler.stat().st_size,'variants':[],'unchanged':True}
        members['compact.json']=json.dumps(value).encode()
        with zipfile.ZipFile(self.bundle,'w') as archive:
            for name,data in members.items():archive.writestr(name,data)
        from compact_update import sha
        def bounded(path):
            self.assertNotEqual(Path(path),compiler,'unchanged compiler must stay outside update I/O')
            return sha(path)
        with patch('compact_update.sha',side_effect=bounded):self.assertTrue(apply(self.bundle,self.app,'1.6.8')['ok'])
        self.assertEqual(compiler.read_bytes(),b'unchanged compiler fixture');self.assert_private()

    def test_recovery_retirement_keeps_two_verified_copies_and_unknown_files(self):
        cache=self.app/'cache/updates';cache.mkdir(parents=True)
        for index in range(4):
            folder=cache/f'compact-fixture-{index}';(folder/'old').mkdir(parents=True)
            data=str(index).encode();(folder/'old/ToBe.exe').write_bytes(data)
            document(folder/'journal.json',{'status':'complete','version':'1.6.8','previous':{'ToBe.exe':digest(data)}})
        (cache/'compact-fixture-0/manual.cpp').write_text('keep an unrecorded file')
        retired=[]
        def retain(path):
            retired.append(path.name);path.rename(self.root/('retained-'+path.name));return True
        with patch('compact_update.recycle_recovery',side_effect=retain):trim_recoveries(self.app,cache)
        self.assertEqual(retired,['compact-fixture-1'])
        self.assertTrue((cache/'compact-fixture-0/manual.cpp').is_file())
        self.assertTrue((cache/'compact-fixture-2').is_dir());self.assertTrue((cache/'compact-fixture-3').is_dir())


if __name__=='__main__':unittest.main()
