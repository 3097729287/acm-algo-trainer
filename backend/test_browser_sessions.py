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

    def test_cf_uses_real_browser_while_other_platforms_remain_native(self):
        from types import SimpleNamespace
        started = []
        bridge = BrowserBridge('http://127.0.0.1:1', session_store=self.store)
        bridge.runner = SimpleNamespace(start=started.append)
        client = str(uuid.uuid4())
        key = bridge.register_browser({'clientId':client, 'protocol':3})['key']
        bridge.browser_queue({'clientId':client, 'hasWindow':True, 'platforms':['Codeforces']}, key)
        cf = bridge.submit('https://codeforces.com/contest/123/problem/A', 'int main(){}', 'CF')
        ac = bridge.submit('https://atcoder.jp/contests/abc100/tasks/abc100_a', 'int main(){}', 'AC')
        queue = bridge.browser_queue({'clientId':client, 'hasWindow':True}, key)
        self.assertEqual(started, [ac['sessionId']])
        self.assertEqual(queue['mode'], 'hybrid')
        self.assertEqual([job['sessionId'] for job in queue['jobs']], [cf['sessionId']])
        session = bridge.sessions[cf['sessionId']]
        self.assertFalse(session['attempted'])
        self.assertNotIn('dispatchedAt', session)

    def test_native_cf_never_switches_transport_after_checkpoint(self):
        from types import SimpleNamespace
        bridge = BrowserBridge('http://127.0.0.1:1', session_store=self.store)
        bridge.runner = SimpleNamespace(start=lambda _:None)
        cf = bridge.submit('https://codeforces.com/contest/123/problem/A', 'int main(){}', 'CF')
        client = str(uuid.uuid4())
        key = bridge.register_browser({'clientId':client, 'protocol':3})['key']
        bridge.browser_queue({'clientId':client, 'hasWindow':True}, key)
        session = bridge.sessions[cf['sessionId']]
        session.update(dispatchedAt=0, attempted=True)
        self.assertFalse(bridge.route_to_browser(cf['sessionId'], before_click=True))
        self.assertNotIn('transport', session)
        session['attempted'] = False
        self.assertFalse(bridge.route_to_browser(cf['sessionId']))
        self.assertTrue(bridge.route_to_browser(cf['sessionId'], before_click=True))

    def test_closed_browser_keeps_native_and_sync_owner_can_recover(self):
        from types import SimpleNamespace
        now = [0]
        started = []
        bridge = BrowserBridge('http://127.0.0.1:1', session_store=self.store, clock=lambda:now[0])
        bridge.runner = SimpleNamespace(start=started.append)
        first, second = str(uuid.uuid4()), str(uuid.uuid4())
        keys = {client:bridge.register_browser({'clientId':client, 'protocol':3})['key'] for client in (first,second)}
        bridge.browser_queue({'clientId':first, 'hasWindow':False}, keys[first])
        cf = bridge.submit('https://codeforces.com/contest/123/problem/A', 'int main(){}', 'CF')
        self.assertEqual(started, [cf['sessionId']])
        now[0] = 7
        queue = bridge.browser_queue({'clientId':second, 'hasWindow':True}, keys[second])
        self.assertEqual(bridge.sync_client, second)
        self.assertTrue(queue['sync'])
        self.assertTrue(bridge.route_to_browser(cf['sessionId']))
        self.assertEqual(bridge.sessions[cf['sessionId']]['preferredClient'], second)

    def test_legacy_connector_without_window_falls_back_once_without_dispatch(self):
        from types import SimpleNamespace
        now, started = [0], []
        bridge = BrowserBridge('http://127.0.0.1:1', session_store=self.store, clock=lambda:now[0])
        bridge.runner = SimpleNamespace(start=started.append)
        client=str(uuid.uuid4())
        key=bridge.register_browser({'clientId':client,'protocol':2})['key']
        bridge.browser_queue({'clientId':client},key)
        cf=bridge.submit('https://codeforces.com/contest/123/problem/A','int main(){}','CF')
        self.assertFalse(started)
        now[0]=4
        bridge.status(cf['sessionId'])
        self.assertEqual(started,[cf['sessionId']])
        self.assertEqual(bridge.sessions[cf['sessionId']]['transport'],'silent')
        self.assertNotIn('dispatchedAt',bridge.sessions[cf['sessionId']])
        self.assertFalse(bridge.route_to_browser(cf['sessionId']))

    def test_legacy_cf_job_cannot_starve_other_platform_login_sync(self):
        from types import SimpleNamespace
        bridge=BrowserBridge('http://127.0.0.1:1',session_store=self.store)
        bridge.runner=SimpleNamespace(start=lambda _:None)
        client=str(uuid.uuid4())
        key=bridge.register_browser({'clientId':client,'protocol':2})['key']
        bridge.browser_queue({'clientId':client},key)
        bridge.submit('https://codeforces.com/contest/123/problem/A','int main(){}','CF')
        queue=bridge.browser_queue({'clientId':client},key)
        self.assertEqual(queue['mode'],'silent')
        self.assertFalse(queue['jobs'])
        self.assertEqual(queue['sync'][0]['platform'],'洛谷')

    def test_failed_post_navigation_keeps_checkpoint_and_queries_without_replay(self):
        from silent_submit import navigation_failure
        bridge=BrowserBridge('http://127.0.0.1:1',session_store=self.store)
        cf=bridge.submit('https://codeforces.com/contest/123/problem/A','int main(){}','CF')
        session=bridge.sessions[cf['sessionId']]
        session.update(dispatchedAt=bridge.clock(),attempted=True)
        client=str(uuid.uuid4())
        key=bridge.register_browser({'clientId':client,'protocol':3})['key']
        bridge.browser_queue({'clientId':client,'hasWindow':True},key)
        value=navigation_failure(session)
        bridge.exchange({'sessionId':cf['sessionId'],'pageUrl':session['url'],'event':value},session['capability'])
        self.assertEqual(bridge.status(cf['sessionId'])['status'],'unconfirmed')
        self.assertTrue(session['attempted'])
        self.assertIn('dispatchedAt',session)
        self.assertFalse(bridge.route_to_browser(cf['sessionId'],before_click=True))
        self.assertEqual(bridge.exchange({'sessionId':cf['sessionId'],'pageUrl':session['url']},session['capability'])['action'],'inspect')
