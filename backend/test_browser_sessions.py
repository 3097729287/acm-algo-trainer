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

    def test_first_party_partition_survives_encrypted_restart_but_other_partitions_do_not(self):
        for platform, domain in [('Codeforces','codeforces.com'),('AtCoder','atcoder.jp'),('牛客','nowcoder.com'),('洛谷','luogu.com.cn')]:
            with self.subTest(platform=platform):
                self.store.request(platform)
                request = next(r for r in self.store.requests() if r['platform'] == platform)
                cookie = {**self.body['cookies'][0], 'domain':domain}
                self.store.accept({**request,'clientId':'fixture-profile','loginState':'logged_in','cookies':[
                    {**cookie,'name':'first-party','partitionKey':{'topLevelSite':'https://'+domain,'hasCrossSiteAncestor':False}},
                    {**cookie,'name':'other-site','partitionKey':{'topLevelSite':'https://evil.test','hasCrossSiteAncestor':False}},
                    {**cookie,'name':'embedded','partitionKey':{'topLevelSite':'https://'+domain,'hasCrossSiteAncestor':True}},
                    {**cookie,'name':'malformed','partitionKey':{'topLevelSite':123}}]})
                restored = BrowserSessions(self.path).snapshot(platform)
                self.assertEqual([c['name'] for c in restored['cookies']], ['first-party'])
                self.assertEqual(restored['loginState'], 'logged_in')

    def test_login_proof_persists_but_another_profile_cannot_change_it(self):
        self.store.accept({**self.body,'clientId':'owner','loginState':'unknown'})
        self.store.update_login_states('owner', {'洛谷':'logged_in'})
        self.store.update_login_states('other', {'洛谷':'logged_out'})
        self.assertEqual(BrowserSessions(self.path).snapshot('洛谷')['loginState'], 'logged_in')
        self.store.update_login_states('owner', {'洛谷':'logged_out'})
        self.assertEqual(BrowserSessions(self.path).snapshot('洛谷')['loginState'], 'logged_out')

    def test_logged_in_profile_wins_even_without_an_open_site_tab(self):
        bridge = BrowserBridge('http://127.0.0.1:1', session_store=self.store)
        guest, signed = str(uuid.uuid4()), str(uuid.uuid4())
        keys = {c:bridge.register_browser({'clientId':c,'protocol':3})['key'] for c in (guest,signed)}
        bridge.browser_queue({'clientId':guest,'hasWindow':True,'platforms':['洛谷'],
                              'loginStates':{'洛谷':'logged_out'}}, keys[guest])
        answer = bridge.browser_queue({'clientId':signed,'hasWindow':False,'platforms':[],
                                       'loginStates':{'洛谷':'logged_in'}}, keys[signed])
        self.assertEqual(bridge._session_client('洛谷'), signed)
        self.assertEqual(answer['sync'][0]['platform'], '洛谷')
        with self.assertRaises(ServiceError):
            bridge.sync_browser({**self.body,'clientId':guest}, keys[guest])
        bridge.sync_browser({**self.body,'clientId':signed,'loginState':'logged_in'}, keys[signed])
        self.assertEqual(self.store.snapshot('洛谷')['clientId'], signed)

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

    def test_cf_and_atcoder_use_real_browser_with_an_existing_window(self):
        from types import SimpleNamespace
        started = []
        bridge = BrowserBridge('http://127.0.0.1:1', session_store=self.store)
        bridge.runner = SimpleNamespace(start=started.append)
        client = str(uuid.uuid4())
        key = bridge.register_browser({'clientId':client, 'protocol':3})['key']
        bridge.browser_queue({'clientId':client, 'hasWindow':True, 'platforms':['Codeforces']}, key)
        cf = bridge.submit('https://codeforces.com/contest/123/problem/A', 'int main(){}', 'CF')
        ac = bridge.submit('https://atcoder.jp/contests/abc100/tasks/abc100_a', 'int main(){}', 'AC')
        lg = bridge.submit('https://www.luogu.com.cn/problem/B4536', 'int main(){}', 'LG')
        queue = bridge.browser_queue({'clientId':client, 'hasWindow':True}, key)
        self.assertEqual(started, [lg['sessionId']])
        self.assertEqual(queue['mode'], 'hybrid')
        self.assertEqual([job['sessionId'] for job in queue['jobs']], [cf['sessionId'], ac['sessionId']])
        session = bridge.sessions[cf['sessionId']]
        self.assertFalse(session['attempted'])
        self.assertNotIn('dispatchedAt', session)

    def test_cookie_change_requests_fresh_sync_without_queuing_a_submission(self):
        bridge = BrowserBridge('http://127.0.0.1:1', session_store=self.store)
        client = str(uuid.uuid4())
        key = bridge.register_browser({'clientId':client,'protocol':3})['key']
        self.store.finish('洛谷')
        answer = bridge.browser_queue({'clientId':client,'syncPlatforms':['Codeforces']}, key)
        self.assertEqual([item['platform'] for item in answer['sync']], ['Codeforces'])
        self.assertEqual(answer['jobs'], [])
        nonce = answer['sync'][0]['nonce']
        bridge.sync_browser({'clientId':client,'platform':'Codeforces','nonce':nonce,
                             'cookies':[],'userAgent':'Fixture browser'}, key)
        answer = bridge.browser_queue({'clientId':client,'syncPlatforms':['Codeforces']}, key)
        self.assertNotEqual(answer['sync'][0]['nonce'], nonce)
        with self.assertRaises(ServiceError):
            bridge.browser_queue({'clientId':client,'syncPlatforms':['unrelated.example']}, key)

    def test_atcoder_never_switches_transport_after_a_submission_checkpoint(self):
        from types import SimpleNamespace
        bridge = BrowserBridge('http://127.0.0.1:1', session_store=self.store)
        bridge.runner = SimpleNamespace(start=lambda unused: None)
        ac = bridge.submit('https://atcoder.jp/contests/abc100/tasks/abc100_a', 'int main(){}', 'AC')
        client = str(uuid.uuid4())
        key = bridge.register_browser({'clientId': client, 'protocol': 3})['key']
        bridge.browser_queue({'clientId': client, 'hasWindow': True, 'platforms': ['AtCoder']}, key)
        session = bridge.sessions[ac['sessionId']]
        session.update(dispatchedAt=0, attempted=True)
        self.assertFalse(bridge.route_to_browser(ac['sessionId'], before_click=True))
        self.assertNotIn('transport', session)
        session['attempted'] = False
        self.assertTrue(bridge.route_to_browser(ac['sessionId'], before_click=True))
        self.assertEqual(session['transport'], 'browser')

    def test_atcoder_uses_native_when_no_browser_claims_the_job(self):
        from types import SimpleNamespace
        now, started = [0], []
        bridge = BrowserBridge('http://127.0.0.1:1', session_store=self.store, clock=lambda: now[0])
        bridge.runner = SimpleNamespace(start=started.append)
        client = str(uuid.uuid4())
        key = bridge.register_browser({'clientId': client, 'protocol': 3})['key']
        bridge.browser_queue({'clientId': client, 'hasWindow': True, 'platforms': ['AtCoder']}, key)
        ac = bridge.submit('https://atcoder.jp/contests/abc100/tasks/abc100_a', 'int main(){}', 'AC')
        self.assertEqual(started, [])
        now[0] = 4
        bridge.status(ac['sessionId'])
        self.assertEqual(started, [ac['sessionId']])
        self.assertFalse(bridge.sessions[ac['sessionId']]['attempted'])

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
