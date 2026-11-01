import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from update_artifacts import prepare_tree,_owned
from update_errors import UpdateStorageError

class UpdateArtifactTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory(prefix='tb-update-artifacts-');self.root=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def specs(self,value=b'isolated helper bytes'):
        return {'ToBe.exe':(value,hashlib.sha256(value).hexdigest())}
    def test_one_hundred_helper_preparations_reuse_one_verified_tree(self):
        copies=[prepare_tree(self.root,'helper','same-package',self.specs()) for _ in range(100)]
        self.assertEqual(len(set(copies)),1);self.assertEqual(len(_owned(self.root,'helper')),1)
    def test_old_verified_trees_are_retired_but_unknown_files_are_preserved(self):
        for i in range(8):prepare_tree(self.root,'helper',str(i),self.specs(str(i).encode()))
        self.assertEqual(len(_owned(self.root,'helper')),2)
        first=prepare_tree(self.root,'helper','manual',self.specs());(first/'unique.cpp').write_bytes(b'private manual code')
        prepare_tree(self.root,'helper','after-0',self.specs())
        with self.assertRaises(UpdateStorageError):prepare_tree(self.root,'helper','after-1',self.specs())
        self.assertEqual((first/'unique.cpp').read_bytes(),b'private manual code')
    def test_byte_budget_and_low_space_do_not_create_new_trees(self):
        with patch('update_artifacts.MAX_BYTES',1):
            with self.assertRaises(UpdateStorageError):prepare_tree(self.root,'helper','large',self.specs())
        with patch('update_artifacts.require_space',side_effect=UpdateStorageError('fixture low space')):
            with self.assertRaises(UpdateStorageError):prepare_tree(self.root,'helper','low',self.specs())
        self.assertEqual(list(self.root.iterdir()),[])
    def test_active_helper_is_preserved_and_another_copy_is_not_created(self):
        first=prepare_tree(self.root,'helper','same',self.specs())
        with patch('update_artifacts._active',return_value=True):
            with self.assertRaises(UpdateStorageError):prepare_tree(self.root,'helper','same',self.specs())
        self.assertTrue((first/'ToBe.exe').is_file());self.assertEqual(len(_owned(self.root,'helper')),1)
