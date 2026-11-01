"""Retained isolated fixtures: bin-only retirement, capacity failure and links."""
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import uuid

import system_recycle
from update_backups import retire_directory

ROOT=Path(__file__).resolve().parents[1]


def retained_fixture(prefix):
    root=ROOT/'.backups/next-150/recycle-test-fixtures'/(prefix+'-'+uuid.uuid4().hex)
    root.mkdir(parents=True)
    return SimpleNamespace(name=str(root),cleanup=lambda:None)


def fixture_recycler(root):
    def retain(path):
        path=Path(path)
        assert path.resolve().is_relative_to(root.resolve())
        destination=root/'retained-fixture';destination.mkdir(exist_ok=True)
        path.rename(destination/(uuid.uuid4().hex+'-'+path.name))
        return True
    return retain


class RecyclePolicyTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(retained_fixture('policy').name)
        self.source=self.root/'discardable.txt';self.source.write_bytes(b'isolated test evidence')

    def test_low_or_unknown_quota_retains_original_without_calling_shell(self):
        for capacity in [(32*1024**2,20*1024**2),OSError('quota unknown')]:
            with patch('system_recycle.IS_WINDOWS',True),patch('system_recycle._capacity',side_effect=capacity if isinstance(capacity,Exception) else None,return_value=capacity),patch('system_recycle._shell_recycle') as shell:
                self.assertFalse(system_recycle.recycle(self.source));shell.assert_not_called()
                self.assertEqual(self.source.read_bytes(),b'isolated test evidence')

    def test_shell_failure_has_no_permanent_delete_fallback(self):
        with patch('system_recycle.IS_WINDOWS',True),patch('system_recycle._capacity',return_value=(1024**3,0)),patch('system_recycle._receipts',return_value=set()),patch('system_recycle._shell_recycle',side_effect=OSError('fixture failure')),patch('pathlib.Path.unlink',side_effect=AssertionError('permanent deletion')),patch('shutil.rmtree',side_effect=AssertionError('permanent deletion')):
            self.assertFalse(system_recycle.recycle(self.source))
            self.assertTrue(self.source.exists())

    def test_managed_retirement_uses_bin_only_and_rejects_unknown_capacity(self):
        with patch('update_backups.recycle_directory',return_value=False) as recycle,patch('shutil.rmtree',side_effect=AssertionError('permanent deletion')),patch('pathlib.Path.unlink',side_effect=AssertionError('permanent deletion')):
            self.assertFalse(retire_directory(self.source));recycle.assert_called_once_with(self.source)
        self.assertTrue(self.source.exists())

    def test_shell_receives_only_the_verified_path_and_links_are_preserved(self):
        with patch('system_recycle.IS_WINDOWS',True),patch('system_recycle._capacity',return_value=(1024**3,0)),patch('system_recycle._receipts',side_effect=[set(),{'new system receipt'}]),patch('system_recycle._shell_recycle',side_effect=fixture_recycler(self.root)) as shell:
            self.assertTrue(system_recycle.recycle(self.source));shell.assert_called_once_with(self.source)
        self.assertTrue(system_recycle.SHELL_FLAGS&0x80000)
        self.assertTrue(system_recycle.SHELL_FLAGS&0x100000)
        with patch('system_recycle._plain',return_value=False),patch('system_recycle._shell_recycle') as shell:
            with self.assertRaises(ValueError):system_recycle._size(self.root)
            shell.assert_not_called()

    def test_disappearance_alone_is_not_reported_as_verified_recycling(self):
        with patch('system_recycle.IS_WINDOWS',True),patch('system_recycle._capacity',return_value=(1024**3,0)),patch('system_recycle._receipts',return_value=set()),patch('system_recycle.time.monotonic',side_effect=[0,4]),patch('system_recycle._shell_recycle',side_effect=fixture_recycler(self.root)) as shell:
            with self.assertLogs('tb.recycle',level='WARNING'):
                self.assertFalse(system_recycle.recycle(self.source))
            shell.assert_called_once()


if __name__=='__main__':unittest.main()
