"""Visible transport state ordering; no browser or real account is opened."""
from pathlib import Path
import tempfile
import unittest
import json
from types import SimpleNamespace
from unittest.mock import patch
from external_browser import ExternalBrowserBridge, ExternalBrowserPreparation
from training import ServiceError


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

    def test_closed_checkpoint_is_not_acknowledged_into_a_native_click(self):
        self.bridge.close('fixture')
        page=SimpleNamespace(send=lambda *_:self.fail('Cancelled job must not acknowledge a click'))
        self.bridge._event('fixture',{'name':'__tbReceipt','payload':json.dumps({'sessionId':'fixture','status':'submitted','attempted':True,'ack':1})},page)

    def test_changing_login_browser_retires_only_unattempted_tabs(self):
        preparation=ExternalBrowserPreparation(self.bridge)
        self.bridge.sessions['fixture'].update(status='needs_login',attempted=False)
        with patch.object(self.bridge.browser,'new_page') as opened:
            preparation.action({'action':'open-login','platform':'AtCoder','browser':'chrome'})
        opened.assert_called_once_with('https://atcoder.jp/login','chrome')
        self.assertEqual(self.bridge.sessions['fixture']['status'],'closed')
        self.bridge.sessions['fixture'].update(status='judging',attempted=True)
        with patch.object(self.bridge.browser,'new_page') as opened, self.assertRaises(ServiceError) as issue:
            preparation.action({'action':'open-login','platform':'AtCoder','browser':'chrome'})
        self.assertEqual(issue.exception.status,409)
        opened.assert_not_called()
