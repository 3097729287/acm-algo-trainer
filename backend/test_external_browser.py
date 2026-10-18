"""Visible transport state ordering; no browser or real account is opened."""
from pathlib import Path
import tempfile
import unittest
from external_browser import ExternalBrowserBridge


class VisibleTransportTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='tb-visible-state-')
        self.bridge=ExternalBrowserBridge(Path(self.temporary.name)/'profile')
        self.bridge.sessions['fixture']={'sessionId':'fixture','status':'submitted','attempted':True,'intent':False}

    def tearDown(self):
        self.bridge.on_closing()
        self.temporary.cleanup()

    def test_late_inspection_cannot_erase_the_pre_click_checkpoint(self):
        self.bridge._update('fixture',{'status':'needs_login','attempted':False},inspection=True)
        self.assertTrue(self.bridge.sessions['fixture']['attempted'])

    def test_explicit_native_rejection_can_clear_the_attempt(self):
        self.bridge._update('fixture',{'status':'error','attempted':False,'message':'Rejected by the site'})
        self.assertFalse(self.bridge.sessions['fixture']['attempted'])
        self.assertFalse(self.bridge.sessions['fixture']['intent'])

    def test_final_receipt_is_saved_once_despite_a_late_inspection(self):
        receipts=[]
        self.bridge.on_receipt=lambda identity,value:receipts.append(value) or True
        answer={'status':'finished','submissionId':'123','verdict':'AC'}
        self.bridge._update('fixture',answer)
        self.bridge._update('fixture',answer,inspection=True)
        self.assertEqual(len(receipts),1)
        self.assertEqual(self.bridge.status('fixture')['verdict'],'AC')
