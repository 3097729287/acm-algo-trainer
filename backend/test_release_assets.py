"""Exercise owner-only builds and reject private artifacts before upload."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_release
from release_assets import is_admin_asset, public_release_files


class ReleaseAssetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tb-release-boundary-')
        self.stage = Path(self.temp.name).resolve()
        self.public = self.stage / 'release'
        self.public.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def test_admin_build_is_private_and_leaves_public_user_package_unchanged(self):
        user = self.public / build_release.PACKAGE
        (user / 'resources').mkdir(parents=True)
        (user / 'TB新版.exe').write_bytes(b'fixture executable')
        for name in ['BUILD-INFO.json', 'resources/BUILD-INFO.json']:
            (user / name).write_text('{"edition":"user"}', encoding='utf8')
        original = build_release.manifest(user)
        with redirect_stdout(io.StringIO()):
            build_release.admin_assemble(SimpleNamespace(stage=self.stage))
        private = self.stage / 'private-admin'
        packages = list(private.glob('TB-Admin-*-win64.zip'))
        self.assertEqual(len(packages), 1)
        with zipfile.ZipFile(packages[0]) as package:
            info = next(name for name in package.namelist() if name.endswith('/BUILD-INFO.json'))
            self.assertEqual(json.loads(package.read(info))['edition'], 'admin')
            self.assertTrue(any(name.endswith('/TB管理员版.exe') for name in package.namelist()))
        self.assertEqual(build_release.manifest(user), original)
        self.assertFalse(any(is_admin_asset(path.name) for path in self.public.iterdir()))
        self.assertTrue((private / 'ADMIN-RELEASE-MANIFEST.json').is_file())

    def test_admin_installer_outputs_to_private_build_directory(self):
        with patch.object(build_release.subprocess, 'run') as invoke:
            build_release.admin_installer(SimpleNamespace(stage=self.stage, inno=Path('ISCC.exe'), webview2=Path('WebView.exe')))
        args = invoke.call_args.args[0]
        self.assertIn('/DOutputDir=' + str(self.stage / 'private-admin'), args)
        self.assertTrue(any(arg.startswith('/DPackageDir=' + str(self.stage / 'private-admin')) for arg in args))
        self.assertNotIn('/DOutputDir=' + str(self.public), args)

    def test_upload_allows_only_public_assets_and_matching_checksum_names(self):
        name = 'TB-Setup-1.3.4-win64.exe'
        (self.public / name).write_bytes(b'user setup')
        (self.public / 'SHA256SUMS.txt').write_text('a' * 64 + '  ' + name + '\n', encoding='utf8')
        self.assertEqual({p.name for p in public_release_files(self.public)}, {name, 'SHA256SUMS.txt'})
        (self.public / 'TB-Admin-1.3.4-win64.zip').write_bytes(b'private')
        with self.assertRaisesRegex(ValueError, 'Administrator'):
            public_release_files(self.public)

    def test_upload_rejects_leftover_admin_checksum_without_private_binary(self):
        (self.public / 'SHA256SUMS.txt').write_text('b' * 64 + '  TB-Admin-Setup-1.3.4-win64.exe\n', encoding='utf8')
        with self.assertRaisesRegex(ValueError, 'Non-public checksum'):
            public_release_files(self.public)

    def test_upload_rejects_admin_metadata_with_an_ordinary_filename(self):
        (self.public / 'BUILD-INFO.json').write_text('{"edition":"admin"}', encoding='utf8')
        with self.assertRaisesRegex(ValueError, 'Administrator build metadata'):
            public_release_files(self.public)

    def test_admin_matching_covers_manifests_paths_and_localized_names(self):
        for name in ['ADMIN-RELEASE-MANIFEST.json', 'TB-Admin-Setup-1.3.4-win64.exe', 'folder/TB-Admin-1.3.4-win64.zip', 'TB管理员版.exe']:
            self.assertTrue(is_admin_asset(name), name)
        self.assertFalse(is_admin_asset('TB-Setup-1.3.4-win64.exe'))


if __name__ == '__main__':
    unittest.main()
