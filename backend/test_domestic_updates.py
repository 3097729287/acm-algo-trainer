import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from software_updates import (DOMESTIC_FEED, DOMESTIC_ROOT, SoftwareUpdates,
                              ReleaseRedirect, domestic_release_info, trusted_url)
from test_software_updates import idle

DATA = b'verified domestic update fixture'


def manifest(delta=True):
    version = '1.3.6'
    name = f'TB-Update-1.3.5-to-{version}-win64.zip' if delta else f'TB-Setup-{version}-win64.exe'
    return {'schema': 1, 'channel': 'stable', 'releases': [{'version': version, 'notes': '版本说明',
            'assets': [{'name': name, 'size': len(DATA), 'sha256': hashlib.sha256(DATA).hexdigest(),
                        'url': f'{DOMESTIC_ROOT}/assets/{version}/{name}'}]}]}


class DomesticUpdateTests(unittest.TestCase):
    def test_default_channel_checks_and_downloads_without_any_github_request(self):
        with tempfile.TemporaryDirectory() as root:
            opener = Mock()
            opener.open.side_effect = [io.BytesIO(json.dumps(manifest()).encode()), io.BytesIO(DATA)]
            service = SoftwareUpdates(Path(root)/'state', current='1.3.5', opener=opener, offline=False)
            service.launcher = Mock()
            try:
                service.start()
                self.assertEqual(idle(service)['status'], 'ready')
                self.assertEqual(service.snapshot()['channel'], 'domestic')
                self.assertEqual(service.installer.read_bytes(), DATA)
                urls = [call.args[0].full_url for call in opener.open.call_args_list]
                self.assertEqual(urls[0], DOMESTIC_FEED)
                self.assertTrue(all(url.startswith(DOMESTIC_ROOT+'/') for url in urls))
            finally: service.close()

    def test_current_version_and_full_installer_when_no_matching_delta(self):
        self.assertIsNone(domestic_release_info(manifest(), '1.3.6'))
        self.assertEqual(domestic_release_info(manifest(False), '1.3.5')['kind'], 'installer')
        payload = manifest(False)
        payload['releases'][0]['assets'] += manifest()['releases'][0]['assets']
        self.assertEqual(domestic_release_info(payload, '1.3.5')['kind'], 'delta')

    def test_malformed_metadata_and_cross_host_redirect_cannot_supply_an_update(self):
        base = manifest()
        for change in ({'url': 'https://github.com/fake.zip'}, {'sha256': 'a'*63}, {'size': True}):
            value = copy.deepcopy(base); value['releases'][0]['assets'][0].update(change)
            with self.assertRaises(ValueError): domestic_release_info(value, '1.3.5')
        for url in (DOMESTIC_FEED+'?x=1', DOMESTIC_FEED+'#x', DOMESTIC_ROOT+'/../secrets/key',
                    'http://47.82.84.74/updates/stable/manifest-v1.json', 'https://47.82.84.74.evil.example/updates/x'):
            self.assertFalse(trusted_url(url))
        from urllib.request import Request
        with self.assertRaises(ValueError):
            ReleaseRedirect().redirect_request(Request(DOMESTIC_FEED), None, 302, '', {}, 'https://github.com/release')

    def test_corrupt_domestic_download_preserves_current_program(self):
        with tempfile.TemporaryDirectory() as root:
            opener = Mock(); opener.open.side_effect = [io.BytesIO(json.dumps(manifest()).encode()), io.BytesIO(b'corrupt')]
            service = SoftwareUpdates(Path(root)/'state', current='1.3.5', opener=opener, offline=False)
            service.launcher = Mock()
            try:
                service.start()
                self.assertEqual(idle(service)['status'], 'error')
                self.assertIsNone(service.installer)
                service.launcher.assert_not_called()
            finally: service.close()
