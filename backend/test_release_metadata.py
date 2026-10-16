import hashlib
import json
import logging
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'desktop'))
import release_metadata
import update_patch


class ReleaseMetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.app = self.root / 'app'
        (self.app / 'resources').mkdir(parents=True)
        (self.app / 'state').mkdir()
        self.private = self.app / 'state' / 'tb-personal.sqlite3'
        self.private.write_bytes(b'private database, drafts, identities untouched')
        self.private_bytes = self.private.read_bytes()
        self.private_mtime = self.private.stat().st_mtime_ns
        (self.app / 'VERSION').write_text('1.1.0', encoding='utf-8')
        self.old = {'BUILD-INFO.json': b'{"version":"1.0.20","baseCommit":"old"}',
                    'SOURCE-MANIFEST.json': b'{"old.py":"old-hash"}'}
        for name, value in self.old.items():
            (self.app / name).write_bytes(value)
        self.manifest = json.dumps({'desktop/launch.py': 'b' * 64}).encode()
        self.build = {'version': '1.1.0', 'commit': 'a' * 40,
                      'sourceManifest': 'SOURCE-MANIFEST.json',
                      'sourceManifestSha256': hashlib.sha256(self.manifest).hexdigest()}
        self.resources()
        self.frozen = patch.object(sys, 'frozen', True, create=True)
        self.frozen.start()

    def resources(self):
        (self.app / 'resources' / 'BUILD-INFO.json').write_text(json.dumps(self.build), encoding='utf-8')
        (self.app / 'resources' / 'SOURCE-MANIFEST.json').write_bytes(self.manifest)

    def tearDown(self):
        self.frozen.stop()
        self.assertEqual(self.private.read_bytes(), self.private_bytes)
        self.assertEqual(self.private.stat().st_mtime_ns, self.private_mtime)
        self.assertFalse(list(self.app.glob('.tb-release-metadata-*')))
        self.temp.cleanup()

    def assert_old(self):
        for name, value in self.old.items():
            self.assertEqual((self.app / name).read_bytes(), value)

    def assert_current(self):
        for name in self.old:
            self.assertEqual((self.app / name).read_bytes(), (self.app / 'resources' / name).read_bytes())

    def test_frozen_refreshes_old_metadata_and_is_idempotent(self):
        result = release_metadata.refresh_release_metadata(self.app)
        self.assertEqual(result['status'], 'updated')
        self.assert_current()
        times = {name: (self.app / name).stat().st_mtime_ns for name in self.old}
        self.assertEqual(release_metadata.refresh_release_metadata(self.app), {'status': 'current'})
        self.assertEqual(times, {name: (self.app / name).stat().st_mtime_ns for name in self.old})

    def test_development_execution_never_replaces_metadata(self):
        with patch.object(sys, 'frozen', False):
            self.assertEqual(release_metadata.refresh_release_metadata(self.app), {'status': 'source'})
        self.assert_old()

    def test_missing_legacy_root_files_are_created(self):
        for name in self.old:
            (self.app / name).unlink()
        self.assertEqual(release_metadata.refresh_release_metadata(self.app)['status'], 'updated')
        self.assert_current()

    def test_bad_version_commit_digest_and_filename_log_without_overwriting(self):
        for field, bad in [('version', '1.0.20'), ('commit', 'unknown'), ('commit', 'a' * 39),
                           ('commit', 12), ('sourceManifestSha256', '0' * 64),
                           ('sourceManifest', '../state/tb-personal.sqlite3')]:
            with self.subTest(field=field, bad=bad):
                original = self.build[field]
                self.build[field] = bad
                self.resources()
                with self.assertLogs(release_metadata.LOG, level=logging.WARNING):
                    self.assertEqual(release_metadata.refresh_release_metadata(self.app)['status'], 'error')
                self.assert_old()
                self.build[field] = original
        self.resources()

    def test_invalid_or_oversized_resources_are_rejected_before_writes(self):
        cases = [('BUILD-INFO.json', b'{'), ('SOURCE-MANIFEST.json', b'[]'),
                 ('BUILD-INFO.json', b'x' * (release_metadata.LIMITS['BUILD-INFO.json'] + 1)),
                 ('SOURCE-MANIFEST.json', b'x' * (release_metadata.LIMITS['SOURCE-MANIFEST.json'] + 1))]
        for name, data in cases:
            with self.subTest(name=name, size=len(data)):
                self.resources()
                (self.app / 'resources' / name).write_bytes(data)
                with self.assertLogs(release_metadata.LOG, level=logging.WARNING):
                    self.assertEqual(release_metadata.refresh_release_metadata(self.app)['status'], 'error')
                self.assert_old()

    def test_external_source_directory_junction_is_not_followed(self):
        # Windows junctions do not require symlink privilege. Other platforms
        # exercise the same linked-directory guard with a directory symlink.
        outside = self.root / 'outside'
        (self.app / 'resources').rename(outside)
        link = self.app / 'resources'
        if os.name == 'nt':
            import _winapi
            _winapi.CreateJunction(str(outside), str(link))
        else:
            link.symlink_to(outside, target_is_directory=True)
        before = {path.name: path.read_bytes() for path in outside.iterdir()}
        try:
            with self.assertLogs(release_metadata.LOG, level=logging.WARNING):
                self.assertEqual(release_metadata.refresh_release_metadata(self.app)['status'], 'error')
            self.assert_old()
            self.assertEqual(before, {path.name: path.read_bytes() for path in outside.iterdir()})
        finally:
            if os.name == 'nt':
                link.rmdir()
            else:
                link.unlink()

    def test_external_destination_link_is_not_overwritten(self):
        outside = self.root / 'outside'
        outside.mkdir()
        outside_file = outside / 'BUILD-INFO.json'
        outside_file.write_bytes(b'external file must remain intact')
        destination = self.app / 'BUILD-INFO.json'
        destination.unlink()
        junction = False
        try:
            destination.symlink_to(outside_file)
        except OSError:
            if os.name != 'nt':
                raise
            import _winapi
            _winapi.CreateJunction(str(outside), str(destination))
            junction = True
        try:
            with self.assertLogs(release_metadata.LOG, level=logging.WARNING):
                self.assertEqual(release_metadata.refresh_release_metadata(self.app)['status'], 'error')
            self.assertEqual(outside_file.read_bytes(), b'external file must remain intact')
            self.assertEqual((self.app / 'SOURCE-MANIFEST.json').read_bytes(), self.old['SOURCE-MANIFEST.json'])
            self.assertTrue(destination.is_junction() if junction else destination.is_symlink())
        finally:
            if junction:
                destination.rmdir()
            else:
                destination.unlink()

    def test_second_replace_failure_restores_both_old_files(self):
        real_replace = os.replace
        def replace(source, destination):
            if Path(destination).name == 'BUILD-INFO.json':
                raise OSError('isolated simulated second-file write failure')
            return real_replace(source, destination)
        with patch.object(release_metadata.os, 'replace', side_effect=replace):
            with self.assertLogs(release_metadata.LOG, level=logging.WARNING):
                self.assertEqual(release_metadata.refresh_release_metadata(self.app)['status'], 'error')
        self.assert_old()

    def test_legacy_updater_accepts_resource_delta_then_new_entry_refreshes_roots(self):
        (self.app / 'VERSION').write_bytes(b'1.0.20')
        old = {'VERSION': b'1.0.20'}
        new = {'VERSION': b'1.1.0', **{'resources/' + name: (self.app / 'resources' / name).read_bytes() for name in self.old}}
        for name in self.old:
            (self.app / 'resources' / name).unlink()
        hashes = lambda values: {name: hashlib.sha256(value).hexdigest() for name, value in values.items()}
        manifest = {'schema': 1, 'fromVersion': '1.0.20', 'version': '1.1.0',
                    'base': hashes(old), 'files': hashes(new), 'changed': sorted(new)}
        package = self.root / 'legacy-to-new.zip'
        with zipfile.ZipFile(package, 'w') as archive:
            archive.writestr('update.json', json.dumps(manifest))
            for name, value in new.items():
                archive.writestr('files/' + name, value)
        old_allowlist = update_patch.ROOT_FILES - set(self.old)
        with patch.object(update_patch, 'ROOT_FILES', old_allowlist):
            for name in self.old:
                with self.assertRaises(ValueError):
                    update_patch.safe_name(name)
            update_patch.apply_patch_file(package, update_patch.digest(package), '1.1.0', self.app)
        self.assert_old()
        self.assertEqual(release_metadata.refresh_release_metadata(self.app)['status'], 'updated')
        self.assert_current()


if __name__ == '__main__':
    unittest.main()
