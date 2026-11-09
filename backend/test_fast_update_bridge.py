"""Reject mirror substitution and preserve the public-only release boundary."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_update_bootstrap_native import trusted_asset
from release_assets import public_release_files


class FastUpdateBridgeTests(unittest.TestCase):
    def setUp(self):
        name = 'ToBe-Compact-Update-1.6.7-to-1.6.11-win64.zip'
        self.asset = {
            'name': name, 'url': 'https://47.82.84.74/updates/assets/1.6.11/' + name,
            'size': 4671854, 'sha256': '72f9a33edc0adcc0f3e8a13987ee82f89ae9a1de304fbf234b7c132984f4c73e',
        }
        self.sources = {
            'repository': '3097729287/acm-algo-trainer',
            'commit': 'd54ac2e65143b240d2f559588de6bcb8ed17123b',
            **{key: self.asset[key] for key in ('name', 'size', 'sha256')},
            'urls': ['https://cdn.jsdelivr.net/gh/3097729287/acm-algo-trainer@d54ac2e65143b240d2f559588de6bcb8ed17123b/' + name],
        }

    def test_legacy_primary_and_bound_public_mirror_are_supported(self):
        self.assertEqual(trusted_asset(self.asset, '1.6.11'), self.asset)
        self.asset['downloadSources'] = self.sources
        checked = trusted_asset(self.asset, '1.6.11')
        self.assertEqual(checked, self.asset)
        self.sources['urls'].append('https://example.invalid/file')
        self.assertEqual(len(checked['downloadSources']['urls']), 1)

    def test_cdn_cannot_change_asset_identity_or_owner(self):
        mutations = [
            ('name', 'ToBe-Compact-Update-1.6.6-to-1.6.11-win64.zip'),
            ('size', 1), ('size', True), ('sha256', 'a' * 64),
            ('repository', 'other-owner/acm-algo-trainer'),
            ('repository', '3097729287/acm-algo-trainer-extra'),
            ('commit', 'main'), ('commit', 'a' * 39),
        ]
        for key, value in mutations:
            with self.subTest(key=key, value=value):
                asset = copy.deepcopy(self.asset)
                asset['downloadSources'] = {**self.sources, key: value}
                with self.assertRaises(ValueError):
                    trusted_asset(asset, '1.6.11')

    def test_only_exact_official_https_pinned_url_is_allowed(self):
        url = self.sources['urls'][0]
        substitutions = [
            url.replace('https:', 'http:'),
            url.replace('cdn.jsdelivr.net', 'testingcf.jsdelivr.net'),
            url.replace('cdn.jsdelivr.net', 'cdn.jsdelivr.net.evil.invalid'),
            url.replace('cdn.jsdelivr.net', 'user:pass@cdn.jsdelivr.net'),
            url.replace('cdn.jsdelivr.net', 'cdn.jsdelivr.net:8443'),
            url.replace(self.sources['commit'], 'main'),
            url.replace('/ToBe-', '/../ToBe-'),
            url + '?redirect=1', url + '#unused',
        ]
        for changed in substitutions:
            with self.subTest(url=changed):
                asset = {**self.asset, 'downloadSources': {**self.sources, 'urls': [changed]}}
                with self.assertRaises(ValueError):
                    trusted_asset(asset, '1.6.11')

    def test_second_source_is_the_same_pinned_owned_public_file(self):
        cdn = self.sources['urls'][0]
        raw = 'https://raw.githubusercontent.com/3097729287/acm-algo-trainer/' + self.sources['commit'] + '/' + self.asset['name']
        paired = {**self.asset, 'downloadSources': {**self.sources, 'urls': [cdn, raw]}}
        self.assertEqual(trusted_asset(paired, '1.6.11')['downloadSources']['urls'], [cdn, raw])
        for urls in ([raw], [raw, cdn], [cdn, cdn], [cdn, raw, raw],
                     [cdn, raw.replace('/3097729287/', '/other-owner/')],
                     [cdn, raw.replace(self.sources['commit'], 'main')],
                     [cdn, raw.replace(self.asset['name'], 'another.zip')],
                     [cdn, raw + '?token=forbidden'],
                     [cdn, raw.replace('https:', 'http:')]):
            with self.subTest(urls=urls):
                with self.assertRaises(ValueError):
                    trusted_asset({**self.asset, 'downloadSources': {**self.sources, 'urls': urls}}, '1.6.11')

    def test_malformed_binding_cannot_be_silently_discarded(self):
        for sources in [None, {}, [], {**self.sources, 'extra': 'unexpected'}, {k: v for k, v in self.sources.items() if k != 'sha256'}]:
            with self.subTest(sources=sources):
                with self.assertRaises(ValueError):
                    trusted_asset({**self.asset, 'downloadSources': sources}, '1.6.11')

    def test_full_installer_does_not_inherit_compact_mirror_permission(self):
        name = 'ToBe-Full-Setup-1.6.11-win64.exe'
        asset = {**self.asset, 'name': name, 'url': 'https://47.82.84.74/updates/assets/1.6.11/' + name}
        sources = {**self.sources, 'name': name, 'urls': [self.sources['urls'][0].rsplit('/', 1)[0] + '/' + name]}
        with self.assertRaises(ValueError):
            trusted_asset({**asset, 'downloadSources': sources}, '1.6.11')

    def test_fast_release_metadata_and_checksum_keep_private_assets_out(self):
        with tempfile.TemporaryDirectory(prefix='tb-fast-release-boundary-') as directory:
            root = Path(directory)
            metadata = root / 'FAST-UPDATE-BUILD-INFO.json'
            metadata.write_text('{"edition":"user"}', encoding='utf8')
            (root / 'FAST-UPDATE-SOURCE-MANIFEST.json').write_text('{}', encoding='utf8')
            name = 'ToBe-Setup-1.6.11-win64.exe'
            (root / name).write_bytes(b'public bridge fixture')
            checksums = root / 'FAST-SHA256SUMS.txt'
            checksums.write_text('a' * 64 + '  ' + name + '\n', encoding='utf8')
            self.assertEqual(len(public_release_files(root)), 4)
            metadata.write_text('{"adminMode":true}', encoding='utf8')
            with self.assertRaisesRegex(ValueError, 'Administrator build metadata'):
                public_release_files(root)
            metadata.write_text('{"edition":"user"}', encoding='utf8')
            checksums.write_text('b' * 64 + '  ToBe-Admin-Setup-1.6.11-win64.exe\n', encoding='utf8')
            with self.assertRaisesRegex(ValueError, 'Non-public checksum'):
                public_release_files(root)


if __name__ == '__main__':
    unittest.main()
