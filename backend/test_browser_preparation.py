import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import uuid
from unittest.mock import patch

from browser_bridge import BrowserBridge
from browser_preparation import BrowserPreparation, LOGIN_URLS
from browser_sessions import DOMAINS
from training import ServiceError
import test_backend as api_fixtures


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tb-preparation-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'manifest.json').write_text('{}')
        self.cached, self.requested, self.opened = {}, [], []
        store = SimpleNamespace(snapshot=lambda platform: copy.deepcopy(self.cached.get(platform)),
                                request=self.requested.append, requests=lambda: [])
        self.now = 0
        self.bridge = BrowserBridge('http://127.0.0.1:1', session_store=store, clock=lambda:self.now)
        self.profiles = []
        self.preparation = BrowserPreparation(self.bridge, self.root, profiles=lambda:self.profiles,
                                             opener=lambda *args:self.opened.append(args))

    def connect(self, states=None):
        client = str(uuid.uuid4())
        key = self.bridge.register_browser({'clientId':client,'protocol':3,'extensionVersion':'0.10.8'})['key']
        self.bridge.browser_queue({'clientId':client,'loginStates':states or {}}, key)
        return client, key

    def cache_logins(self):
        self.cached.update({platform:{'loginState':'logged_in','cookies':[{'name':'fixture','value':'PRIVATE-COOKIE','path':'/'}]}
                            for platform in DOMAINS})

    def test_missing_extension_and_login_have_separate_states(self):
        value = self.preparation.snapshot()
        self.assertFalse(value['extension']['installed'])
        self.assertFalse(value['ready'])
        self.assertEqual({p['state'] for p in value['platforms']}, {'not_synced'})
        with self.assertRaises(ServiceError) as rejected:
            self.preparation.check_submission('https://codeforces.com/contest/1/problem/A')
        self.assertEqual(rejected.exception.status, 412)

    def test_connected_metadata_never_exposes_cookies_or_capabilities(self):
        self.cache_logins()
        self.connect({platform:'logged_in' for platform in DOMAINS})
        value = self.preparation.snapshot()
        self.assertTrue(value['ready'])
        self.assertTrue(value['extension']['installed'])
        text = json.dumps(value)
        self.assertNotIn('PRIVATE-COOKIE', text)
        self.assertNotIn('cookies', text)
        self.assertNotIn(next(iter(self.bridge.clients.values())), text)

    def test_closed_browser_is_installed_and_cached_logins_remain_usable(self):
        self.cache_logins()
        self.connect({platform:'logged_in' for platform in DOMAINS})
        self.profiles.append((self.root / 'msedge.exe', 'Default'))
        self.now = 20
        value = self.preparation.snapshot()
        self.assertTrue(value['extension']['installed'])
        self.assertFalse(value['extension']['connected'])
        self.assertTrue(value['ready'])

    def test_empty_or_expired_cache_requests_refresh_instead_of_demanding_login(self):
        self.cache_logins()
        self.connect({platform:'logged_in' for platform in DOMAINS})
        self.cached['Codeforces']['cookies'] = [{'name':'expired','value':'old','expirationDate':1}]
        self.cached['AtCoder']['cookies'] = []
        self.now = 20  # No live browser remains to validate the original session.
        self.profiles.append((self.root / 'msedge.exe', 'Default'))
        states = {p['platform']:p['state'] for p in self.preparation.snapshot()['platforms']}
        self.assertEqual(states['Codeforces'], 'unknown')
        self.assertEqual(states['AtCoder'], 'unknown')
        self.preparation.check_submission('https://atcoder.jp/contests/abc100/tasks/abc100_a')
        self.assertIn('AtCoder', self.requested)

    def test_unknown_login_does_not_pretend_logged_out_or_block_original_validation(self):
        self.cache_logins(); self.connect()
        self.assertEqual(self.preparation.snapshot()['platforms'][0]['state'], 'unknown')
        self.preparation.check_submission('https://codeforces.com/contest/1/problem/A')

    def test_cf_original_browser_login_survives_empty_replay_cookie_cache(self):
        self.cached['Codeforces'] = {'cookies':[]}
        client, key = self.connect({'Codeforces':'logged_in'})
        self.bridge.browser_queue({'clientId':client,'platforms':['Codeforces'],
                                   'loginStates':{'Codeforces':'logged_in'}}, key)
        self.assertEqual(self.preparation.snapshot()['platforms'][0]['state'], 'logged_in')
        self.preparation.check_submission('https://codeforces.com/contest/1/problem/A')

    def test_cf_unknown_original_page_does_not_become_logged_out_from_empty_cache(self):
        self.cached['Codeforces'] = {'cookies':[]}
        client, key = self.connect()
        self.bridge.browser_queue({'clientId':client,'platforms':['Codeforces']}, key)
        self.assertEqual(self.preparation.snapshot()['platforms'][0]['state'], 'unknown')
        self.preparation.check_submission('https://codeforces.com/contest/1/problem/A')

    def test_cf_stale_logged_out_hint_is_rechecked_by_live_original_browser(self):
        self.cached['Codeforces'] = {'cookies':[]}
        self.connect({'Codeforces':'logged_out'})
        self.preparation.check_submission('https://codeforces.com/contest/1/problem/A')

    def test_atcoder_live_login_is_independent_of_replay_cache(self):
        url = 'https://atcoder.jp/contests/abc100/tasks/abc100_a'
        for state in ('logged_in', 'unknown', 'logged_out'):
            with self.subTest(state=state):
                self.cached['AtCoder'] = {'cookies': []}
                self.now += 10  # Previous profile's heartbeat has expired.
                client, key = self.connect({'AtCoder': state})
                # Make this the browser that owns the open AtCoder page.
                for previous in self.bridge.client_platforms:
                    self.bridge.client_platforms[previous] = set()
                self.bridge.browser_queue({'clientId':client, 'platforms':['AtCoder'],
                                           'loginStates':{'AtCoder':state}}, key)
                states = {p['platform']:p['state'] for p in self.preparation.snapshot()['platforms']}
                self.assertEqual(states['AtCoder'], state)
                self.preparation.check_submission(url)

    def test_all_four_logins_are_recognized_without_any_tabs_or_windows(self):
        client, key = self.connect()
        self.bridge.browser_queue({'clientId':client,'hasWindow':False,'platforms':[],
                                   'loginStates':{p:'logged_in' for p in DOMAINS}}, key)
        self.assertTrue(self.preparation.snapshot()['ready'])
        self.assertEqual(self.opened, [])

    def test_desktop_restart_uses_persisted_login_metadata_without_a_browser(self):
        self.cache_logins()
        self.profiles.append((self.root / 'msedge.exe', 'Default'))
        self.assertFalse(self.preparation.snapshot()['extension']['connected'])
        self.assertTrue(self.preparation.snapshot()['ready'])

    def test_all_four_stale_or_missing_snapshots_can_refresh_at_submission(self):
        self.profiles.append((self.root / 'msedge.exe', 'Default'))
        urls = ['https://codeforces.com/contest/1/problem/A',
                'https://atcoder.jp/contests/abc100/tasks/abc100_a',
                'https://ac.nowcoder.com/acm/contest/127263/B',
                'https://www.luogu.com.cn/problem/B4536']
        for cached in (None, {'cookies':[], 'loginState':'logged_out'}):
            for platform, url in zip(DOMAINS, urls):
                with self.subTest(platform=platform, cached=cached):
                    self.cached[platform] = cached
                    self.preparation.check_submission(url)
                    self.assertEqual(self.requested[-1], platform)

    def test_atcoder_can_validate_in_live_browser_before_cookie_sync(self):
        self.connect({'AtCoder':'logged_out'})
        self.preparation.check_submission('https://atcoder.jp/contests/abc100/tasks/abc100_a')

    def test_explicit_actions_use_fixed_extension_path_and_original_login_urls(self):
        self.preparation.action({'action':'open-folder'})
        self.assertEqual(self.opened[-1][1], self.root)
        for platform, url in LOGIN_URLS.items():
            self.preparation.action({'action':'open-login','browser':'edge','platform':platform})
            self.assertEqual(self.opened[-1][1], url)
        for body in ({'action':'open-folder','path':'C:/'}, {'action':'open-login','browser':'edge','platform':'other'},
                     {'action':'open-extensions','browser':'other'}, {'action':'other'}):
            with self.assertRaises(ServiceError): self.preparation.action(body)
        with patch('browser_preparation.wake_browser'):
            self.assertTrue(self.preparation.action({'action':'refresh'})['checking'])
        self.assertEqual(set(self.requested), set(DOMAINS))


class PreparationAPITests(unittest.TestCase):
    setUp = api_fixtures.BackendTests.setUp
    tearDown = api_fixtures.BackendTests.tearDown
    request = api_fixtures.BackendTests.request

    def test_status_actions_keep_token_and_origin_guards(self):
        opened = []
        bridge = BrowserBridge('http://127.0.0.1:1')
        self.server.browser_preparation = BrowserPreparation(bridge, self.root, profiles=lambda:[],
                                                           opener=lambda *args:opened.append(args))
        status, value = self.request('/api/browser-preparation')
        self.assertEqual(status, 200)
        self.assertTrue(value['available'])
        body = {'action':'open-login','browser':'edge','platform':'AtCoder'}
        for headers in ({'X-TB-Token':'bad'}, {'Origin':'https://evil.example'}):
            self.assertEqual(self.request('/api/browser-preparation', body, headers)[0], 403)
        self.assertFalse(opened)
        self.assertEqual(self.request('/api/browser-preparation', body)[0], 200)
        self.assertEqual(opened[0][1], LOGIN_URLS['AtCoder'])

    def test_missing_preparation_does_not_dispatch_official_code(self):
        dispatched = []
        self.server.official_submitter = lambda *args:dispatched.append(args)
        bridge = BrowserBridge('http://127.0.0.1:1')
        self.server.browser_preparation = BrowserPreparation(bridge, self.root, profiles=lambda:[])
        self.assertEqual(self.request('/api/official/submit', {'id':'fixture::A','code':'int main(){}'})[0], 412)
        self.assertFalse(dispatched)
