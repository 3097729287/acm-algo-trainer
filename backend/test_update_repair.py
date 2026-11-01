import hashlib
from contextlib import closing
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import Mock
import zipfile

from software_updates import SoftwareUpdates,DOMESTIC_ROOT,domestic_release_info
from training import ServiceError
from update_errors import UpdateBaseMismatch
from update_patch import inspect_patch

def sha(data):return hashlib.sha256(data).hexdigest()

class UpdateRepairTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name);self.app=self.root/'app';self.app.mkdir()
        self.state=self.root/'state';self.state.mkdir()
        self.private=self.state/'tb-personal.sqlite3'
        with closing(sqlite3.connect(self.private)) as db:
            db.execute('CREATE TABLE identity (code TEXT)');db.execute('INSERT INTO identity VALUES (?)',('private draft',))
            db.commit()
        (self.app/'VERSION').write_text('1.4.31')
        self.panel=self.app/'frontend/dist/assets/AccountPanel.js';self.panel.parent.mkdir(parents=True)
        self.panel.write_bytes(b'modified installed file')
        stream=io.BytesIO()
        manifest={'schema':1,'fromVersion':'1.4.31','version':'1.4.34','base':{'VERSION':sha(b'1.4.31'),'frontend/dist/assets/AccountPanel.js':sha(b'original file')},'files':{'VERSION':sha(b'1.4.34'),'frontend/dist/assets/AccountPanel.js':sha(b'original file')},'changed':['VERSION']}
        with zipfile.ZipFile(stream,'w') as archive:archive.writestr('update.json',json.dumps(manifest));archive.writestr('files/VERSION',b'1.4.34')
        self.delta=stream.getvalue();self.installer=b'trusted full installer fixture - never executed'
        self.assets=[self.asset('ToBe-Update-1.4.31-to-1.4.34-win64.zip',self.delta),self.asset('ToBe-Setup-1.4.34-win64.exe',self.installer)]
        self.opener=Mock();self.downloads=[]
        def opened(request,**kwargs):
            self.downloads.append(request.full_url)
            return io.BytesIO(self.delta if request.full_url.endswith('.zip') else self.installer)
        self.opener.open.side_effect=opened
        self.service=SoftwareUpdates(self.state,current='1.4.31',opener=self.opener,offline=False)
        self.service.release=self.release(self.assets)
        self.service.launcher=Mock()
        def preflight(path,digest,version):
            if path.suffix=='.zip':
                with zipfile.ZipFile(path) as archive:inspect_patch(archive,self.app,version)
        self.service.preparer=preflight
    def tearDown(self):self.service.close();self.temp.cleanup()
    def asset(self,name,data):return {'name':name,'url':f'{DOMESTIC_ROOT}/assets/1.4.34/{name}','sha256':sha(data),'size':len(data)}
    def release(self,assets):return domestic_release_info({'schema':1,'channel':'stable','releases':[{'version':'1.4.34','assets':assets}]},'1.4.31')
    def settle(self):
        deadline=time.monotonic()+5
        while self.service.snapshot()['status']=='downloading':
            if time.monotonic()>deadline:self.fail(self.service.snapshot())
            time.sleep(.01)
        return self.service.snapshot()
    def ready(self):self.service.download();self.assertEqual(self.settle()['status'],'ready')
    def test_modified_program_uses_verified_full_installer_without_touching_private_data(self):
        before=sha(self.private.read_bytes());original=self.panel.read_bytes();self.ready()
        self.assertEqual(self.service.install()['status'],'downloading')
        self.assertEqual(self.settle()['status'],'ready');self.assertTrue(self.service.snapshot()['repairing'])
        self.assertEqual(self.service.snapshot()['updateKind'],'installer')
        self.assertFalse((self.state/'backups').exists(),'Baseline preflight precedes personal backup')
        self.assertEqual(self.service.install()['status'],'installing')
        self.assertEqual(self.service.launcher.call_args.args[0].suffix,'.exe')
        self.service.launcher.assert_called_once();self.assertEqual(len(self.downloads),2)
        self.assertEqual(self.panel.read_bytes(),original);self.assertEqual(sha(self.private.read_bytes()),before)
        copies=list((self.state/'backups').glob('*/tb-personal.sqlite3'));self.assertEqual(len(copies),1)
        with closing(sqlite3.connect(copies[0])) as db:self.assertEqual(db.execute('SELECT code FROM identity').fetchone()[0],'private draft')
    def test_missing_old_frontend_asset_also_falls_back(self):
        self.panel.replace(self.panel.with_suffix('.preserved'))
        self.ready();self.service.install();self.assertEqual(self.settle()['updateKind'],'installer');self.assertFalse(self.panel.exists())
    def test_full_only_release_supports_legacy_clients_with_no_delta(self):
        self.assertEqual(self.release(self.assets[1:])['kind'],'installer')
    def test_fallback_metadata_must_be_same_version_owned_https_and_have_hash(self):
        for field,value in [('url','https://example.com/fake.exe'),('sha256',''),('size',False)]:
            assets=[dict(item) for item in self.assets];assets[1][field]=value
            with self.assertRaises(ValueError):self.release(assets)
    def test_corrupt_full_fallback_never_reaches_launcher(self):
        self.ready();self.installer=b'corrupt bytes';self.service.install()
        self.assertEqual(self.settle()['status'],'error');self.service.launcher.assert_not_called();self.assertEqual((self.app/'VERSION').read_text(),'1.4.31')
    def test_missing_fallback_is_explicit_repair_status_not_busy(self):
        self.service.release=self.release(self.assets[:1]);self.ready()
        with self.assertRaises(ServiceError):self.service.install()
        state=self.service.snapshot();self.assertEqual(state['status'],'repair-required');self.assertFalse(state['installDeferred']);self.assertEqual(state['errorCode'],'base-mismatch')
        self.service.launcher.assert_not_called()
    def test_other_preparation_failure_stops_repeated_ready_installation(self):
        self.ready();self.service.preparer=Mock(side_effect=ValueError('untrusted path'))
        with self.assertRaises(ServiceError):self.service.install()
        self.assertEqual(self.service.snapshot()['status'],'install-error');self.assertFalse(self.service.snapshot()['installDeferred'])
        with self.assertRaises(ServiceError):self.service.install()
        self.assertEqual(self.service.preparer.call_count,1);self.service.launcher.assert_not_called()
    def test_busy_guard_retains_verified_package_without_backup_or_redownload(self):
        self.ready();self.service.guard=Mock(side_effect=ServiceError(409,'fixture submission pending'))
        with self.assertRaises(ServiceError):self.service.install()
        state=self.service.snapshot();self.assertEqual(state['status'],'ready');self.assertTrue(state['installDeferred']);self.assertFalse((self.state/'backups').exists());self.assertEqual(len(self.downloads),1)
    def test_verified_cached_package_is_reused(self):
        self.ready();self.service.status='available';self.service.download();self.assertEqual(self.settle()['status'],'ready');self.assertEqual(len(self.downloads),1)

if __name__=='__main__':unittest.main()
