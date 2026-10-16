import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'desktop'))
from update_patch import apply_patch_file, digest, safe_name
from software_updates import release_info, RELEASES, SoftwareUpdates
from unittest.mock import Mock
from test_software_updates import idle


class PatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.app = self.root / 'app'
        self.old = {'VERSION': b'1.0.13', 'TB新版.exe': b'old app', '_internal/runtime.dll': b'unchanged DLL', 'frontend/dist/old.js': b'obsolete'}
        self.new = {'VERSION': b'1.0.14', 'TB新版.exe': b'new app', '_internal/runtime.dll': b'unchanged DLL', 'frontend/dist/new.js': b'new UI'}
        for name, value in self.old.items():
            p = self.app / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(value)
        (self.app / 'state').mkdir()
        (self.app / 'state/private.sqlite3').write_bytes(b'personal WAL and code untouched')

    def tearDown(self):
        self.temp.cleanup()

    def package(self, mutate=None):
        hashes = lambda values: {name: hashlib.sha256(value).hexdigest() for name, value in values.items()}
        manifest = {'schema': 1, 'fromVersion': '1.0.13', 'version': '1.0.14', 'base': hashes(self.old), 'files': hashes(self.new)}
        manifest['changed'] = sorted(name for name in self.new if manifest['files'][name] != manifest['base'].get(name))
        if mutate: mutate(manifest)
        path = self.root / 'patch.zip'
        with zipfile.ZipFile(path, 'w') as z:
            z.writestr('update.json', json.dumps(manifest))
            for name in manifest['changed']: z.writestr('files/' + name, self.new.get(name, b'bad'))
        return path

    def test_only_changes_downloaded_and_unchanged_dll_private_state_retained(self):
        path = self.package()
        with zipfile.ZipFile(path) as z: self.assertNotIn('files/_internal/runtime.dll', z.namelist())
        result = apply_patch_file(path, digest(path), '1.0.14', self.app)
        self.assertEqual(result['replaced'], 3)
        for name, value in self.new.items(): self.assertEqual((self.app / name).read_bytes(), value)
        self.assertFalse((self.app / 'frontend/dist/old.js').exists())
        self.assertEqual((self.app / 'state/private.sqlite3').read_bytes(), b'personal WAL and code untouched')

    def test_failure_rolls_back_replacements_and_added_files(self):
        path = self.package()
        with self.assertRaises(OSError): apply_patch_file(path, digest(path), '1.0.14', self.app, fail_after=1)
        for name, value in self.old.items(): self.assertEqual((self.app / name).read_bytes(), value)
        self.assertFalse((self.app / 'frontend/dist/new.js').exists())

    def test_build_provenance_updates_with_program_and_preserves_personal_state(self):
        for name in ('BUILD-INFO.json', 'SOURCE-MANIFEST.json'):
            self.old[name] = json.dumps({'commit': 'old-build', 'file': name}).encode()
            self.new[name] = json.dumps({'commit': 'new-build', 'file': name}).encode()
            (self.app / name).write_bytes(self.old[name])
        path = self.package()
        with zipfile.ZipFile(path) as archive:
            for name in ('BUILD-INFO.json', 'SOURCE-MANIFEST.json'):
                self.assertIn('files/' + name, archive.namelist())
        apply_patch_file(path, digest(path), '1.0.14', self.app)
        for name, value in self.new.items():
            self.assertEqual((self.app / name).read_bytes(), value)
        self.assertEqual((self.app / 'state/private.sqlite3').read_bytes(), b'personal WAL and code untouched')

    def test_build_provenance_rolls_back_with_failed_program_update(self):
        for name in ('BUILD-INFO.json', 'SOURCE-MANIFEST.json'):
            self.old[name] = b'{"commit":"old-build"}'
            self.new[name] = b'{"commit":"new-build"}'
            (self.app / name).write_bytes(self.old[name])
        path = self.package()
        with self.assertRaises(OSError):
            apply_patch_file(path, digest(path), '1.0.14', self.app, fail_after=1)
        for name, value in self.old.items():
            self.assertEqual((self.app / name).read_bytes(), value)

    def test_provenance_allowlist_does_not_allow_private_or_unknown_metadata(self):
        for name in ('state/BUILD-INFO.json', 'cache/SOURCE-MANIFEST.json', 'runtime-source-manifest.json', 'BUILD-INFO.json/extra', 'SOURCE-MANIFEST.json:private', 'accounts.json'):
            with self.subTest(name=name):
                self.new[name] = b'{"private":"must not be replaced"}'
                path = self.package()
                with self.assertRaises(ValueError):
                    apply_patch_file(path, digest(path), '1.0.14', self.app)
                for old_name, value in self.old.items():
                    self.assertEqual((self.app / old_name).read_bytes(), value)
                self.assertEqual((self.app / 'state/private.sqlite3').read_bytes(), b'personal WAL and code untouched')
                del self.new[name]

    def test_tampering_wrong_base_and_private_paths_rejected_before_writes(self):
        path = self.package()
        with self.assertRaises(ValueError): apply_patch_file(path, '0'*64, '1.0.14', self.app)
        (self.app / '_internal/runtime.dll').write_bytes(b'local modification')
        with self.assertRaises(ValueError): apply_patch_file(path, digest(path), '1.0.14', self.app)
        self.assertEqual((self.app / 'VERSION').read_bytes(), b'1.0.13')
        for name in ('../state/x', 'state/tb-personal.sqlite3', 'cache/x', 'frontend/dist/../../state/x', '_internal/x:stream', 'C:/x', '_internal/x\\a'):
            with self.assertRaises(ValueError): safe_name(name)

    def test_skipped_versions_follow_an_intermediate_delta_without_full_download(self):
        latest={'tag_name':'v1.0.15','assets':[]}
        name='TB-Update-1.0.13-to-1.0.14-win64.zip'
        middle={'tag_name':'v1.0.14','assets':[{'name':name,'state':'uploaded','size':100,'digest':'sha256:'+'a'*64,'browser_download_url':RELEASES+'/download/v1.0.14/'+name}]}
        opener=Mock();opener.open.side_effect=[io.BytesIO(json.dumps(latest).encode()),io.BytesIO(json.dumps([latest,middle]).encode())]
        service=SoftwareUpdates(self.root/'state',current='1.0.13',opener=opener,offline=False)
        try:
            service.check();result=idle(service)
            self.assertEqual(result['latestVersion'],'1.0.14')
            self.assertEqual(result['updateKind'],'delta')
            self.assertEqual(result['status'],'available')
            self.assertEqual(opener.open.call_count,2)
        finally:service.close()

    def test_new_updater_selects_exact_delta_and_never_silently_downloads_setup(self):
        name = 'TB-Update-1.0.13-to-1.0.14-win64.zip'
        asset = {'name': name, 'state': 'uploaded', 'size': 100, 'digest': 'sha256:'+'a'*64, 'browser_download_url': RELEASES+'/download/v1.0.14/'+name}
        release = {'tag_name': 'v1.0.14', 'assets': [asset]}
        self.assertEqual(release_info(release, '1.0.13')['kind'], 'delta')
        with self.assertRaises(ValueError): release_info(release, '1.0.13.0')
        release['assets'] = []
        with self.assertRaises(ValueError): release_info(release, '1.0.13')
