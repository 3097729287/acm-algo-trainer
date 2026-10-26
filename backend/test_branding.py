"""The rename must retain legacy update metadata and private-edition boundaries."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest

from software_updates import domestic_release_info, release_info, trusted_url, DOMESTIC_ROOT, RELEASES
from app_brand import executable
from update_patch import safe_name


class BrandingCompatibilityTests(unittest.TestCase):
    def test_new_and_legacy_asset_names_use_the_same_strict_sources(self):
        for brand in ('ToBe', 'TB'):
            name = f'{brand}-Setup-1.4.14-win64.exe'
            url = f'{DOMESTIC_ROOT}/assets/1.4.14/{name}'
            asset = {'name': name, 'size': 100, 'sha256': hashlib.sha256(b'fixture').hexdigest(), 'url': url}
            payload = {'schema': 1, 'channel': 'stable', 'releases': [{'version': '1.4.14', 'assets': [asset]}]}
            self.assertTrue(trusted_url(url))
            self.assertEqual(domestic_release_info(payload, '1.4.13')['name'], name)
            damaged = copy.deepcopy(payload)
            damaged['releases'][0]['assets'][0]['url'] = url.replace('/assets/', '/private/')
            with self.assertRaises(ValueError): domestic_release_info(damaged, '1.4.13')
            github = {'tag_name': 'v1.4.14', 'assets': [{'name': name, 'state': 'uploaded', 'size': 100,
                      'digest': 'sha256:' + asset['sha256'], 'browser_download_url': f'{RELEASES}/download/v1.4.14/{name}'}]}
            self.assertEqual(release_info(github, '0.9.3')['name'], name)

    def test_helper_resolves_new_and_old_executables_without_relocating_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'TB新版.exe').write_bytes(b'legacy')
            self.assertEqual(executable(root).name, 'TB新版.exe')
            (root/'ToBe.exe').write_bytes(b'current')
            self.assertEqual(executable(root).name, 'ToBe.exe')
        self.assertEqual(safe_name('ToBe.exe'), 'ToBe.exe')
        self.assertEqual(safe_name('TB新版.exe'), 'TB新版.exe')
        with self.assertRaises(ValueError): safe_name('ToBe管理员版.exe')
        with self.assertRaises(ValueError): safe_name('state/ToBe.exe')


if __name__ == '__main__': unittest.main()
