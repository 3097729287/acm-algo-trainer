import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'desktop'))
from browser_sessions import BrowserSessions
from browser_bridge import BrowserBridge
from training import ServiceError


@unittest.skipUnless(os.name == 'nt', 'Windows DPAPI')
class BrowserSessionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'login.dpapi'
        self.store = BrowserSessions(self.path)
        self.store.request('洛谷')
        self.body = {**self.store.requests()[0], 'userAgent': 'Fixture browser', 'cookies': [
            {'name': '_uid', 'value': 'PRIVATE_FIXTURE_ONLY', 'domain': '.luogu.com.cn', 'path': '/', 'secure': True, 'httpOnly': True}]}

    def test_encrypted_restart_empty_logout_and_expiry(self):
        self.store.accept(self.body)
        self.assertNotIn(b'PRIVATE_FIXTURE_ONLY', self.path.read_bytes())
        restored = BrowserSessions(self.path)
        self.assertEqual(restored.snapshot('洛谷')['cookies'][0]['value'], 'PRIVATE_FIXTURE_ONLY')
        self.store.finish('洛谷'); self.store.request('洛谷')
        self.store.accept({**self.body, **self.store.requests()[0], 'cookies': []})
        self.assertEqual(BrowserSessions(self.path).snapshot('洛谷')['cookies'], [])
        with patch('browser_sessions.time.time', return_value=10**12):
            self.assertIsNone(restored.snapshot('洛谷'))

    def test_wrong_domain_or_nonce_rejected_without_writing(self):
        for change in ({'nonce': 'wrong'}, {'cookies': [{**self.body['cookies'][0], 'domain': 'luogu.com.cn.evil.test'}]}, {'cookies': [{**self.body['cookies'][0], 'domain': 'mail.google.com'}]}):
            with self.assertRaises(ServiceError): self.store.accept({**self.body, **change})
        self.assertFalse(self.path.exists())

    def test_completed_or_expired_request_is_refreshed(self):
        original = self.body['nonce']
        self.store.accept(self.body)
        self.assertFalse(self.store.request('洛谷').is_set())
        self.assertNotEqual(self.store.requests()[0]['nonce'], original)
        nonce = self.store.requests()[0]['nonce']
        with patch('browser_sessions.time.monotonic', return_value=10**12):
            self.store.request('洛谷')
            self.assertNotEqual(self.store.requests()[0]['nonce'], nonce)

    def test_capability_sync_never_queues_submission_in_browser(self):
        bridge = BrowserBridge('http://127.0.0.1:1', session_store=self.store)
        client = str(uuid.uuid4())
        registration = bridge.register_browser({'clientId': client, 'protocol': 2})
        self.assertEqual(registration['mode'], 'silent')
        bridge.submit('https://www.luogu.com.cn/problem/B4536', 'int main(){}', 'fixture')
        answer = bridge.browser_queue({'clientId': client}, registration['key'])
        self.assertEqual(answer['jobs'], [])
        self.assertNotIn('cookies', json.dumps(answer))
        with self.assertRaises(ServiceError): bridge.sync_browser({**self.body,'clientId':client}, 'bad')
        bridge.sync_browser({**self.body,'clientId':client}, registration['key'])
