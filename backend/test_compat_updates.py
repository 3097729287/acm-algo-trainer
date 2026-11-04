"""Execute the unmodified original 1.4 validators and replacement code."""
import hashlib,json,tempfile,unittest,zipfile,sys
from pathlib import Path
from types import ModuleType
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_update_patch import prepare_compat14,write_compat14
from upgrade_layout import prepare_loader

class OriginalUpdateTests(unittest.TestCase):
    def test_original_legacy_and_rebranded_updaters_apply_one_cumulative_program_update(self):
        for old,legacy in [('1.4.0',True),('1.4.17',False)]:
            with self.subTest(old=old),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);package=root/'new';package.mkdir()
                payloads={'VERSION':b'1.5.2\n','ToBe.exe':b'MZ-current-native','ToBeLoader.exe':b'MZ-current-loader','resources/virtual_contest.js':b'original form adapter','_internal/runtime.dll':b'new runtime','data/library.sqlite3':b'public seed','frontend/dist/index.html':b'new interface'}
                for name,data in payloads.items():target=package/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
                target=root/'installed';(target/'state').mkdir(parents=True);(target/'state/private.sqlite3').write_bytes(b'private identity and drafts');(target/'VERSION').write_text(old+'\n')
                (target/'_internal').mkdir();(target/'_internal/runtime.dll').write_bytes(b'old runtime')
                (target/('TB新版.exe' if legacy else 'ToBe.exe')).write_bytes(b'old executable')
                original=ModuleType('original_updater');exec(compile((ROOT/'backend/fixtures/updaters'/('updater-'+old+'.py.txt')).read_text('utf8'),old,'exec'),original.__dict__)
                payload=prepare_compat14(package,root/'payload.zip',legacy=legacy)
                artifact=write_compat14(payload,old)
                with zipfile.ZipFile(artifact['path']) as archive:
                    inspected=original.inspect_patch(archive,target,'1.5.2');self.assertEqual(inspected['fromVersion'],old);self.assertEqual(archive.testzip(),None)
                    self.assertTrue(all(not name.startswith('compiler/') for name in inspected['files']))
                original.apply_patch_file(artifact['path'],artifact['sha256'],'1.5.2',target)
                self.assertEqual((target/'VERSION').read_text().strip(),'1.5.2');self.assertEqual((target/'state/private.sqlite3').read_bytes(),b'private identity and drafts')
                self.assertEqual((target/'_internal/runtime.dll').read_bytes(),b'new runtime')
                if legacy:self.assertEqual((target/'resources/legacy-upgrade/ToBe.exe').read_bytes(),payloads['ToBe.exe'])
                else:
                    self.assertTrue(prepare_loader(target));self.assertEqual((target/'ToBeLoader.exe').read_bytes(),payloads['ToBeLoader.exe'])
                    self.assertFalse(prepare_loader(target))
                # Rewriting this owned current candidate only changes the small
                # ZIP suffix; a second version has no duplicate update.json.
                other='1.4.1' if legacy else '1.4.34';write_compat14(payload,other)
                with zipfile.ZipFile(payload['path']) as archive:
                    self.assertEqual(archive.namelist().count('update.json'),1);self.assertEqual(json.loads(archive.read('update.json'))['fromVersion'],other);self.assertIsNone(archive.testzip())

    def test_wrong_versions_are_rejected_before_private_files_can_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);package=root/'new';package.mkdir()
            for name in ('ToBe.exe','ToBeLoader.exe','VERSION'):(package/name).write_bytes(b'1.5.2\n' if name=='VERSION' else b'MZfixture')
            payload=prepare_compat14(package,root/'payload.zip',legacy=True)
            for version in ['1.3.9','1.4.37','1.4.14','../../state']:
                with self.assertRaises(ValueError):write_compat14(payload,version)
