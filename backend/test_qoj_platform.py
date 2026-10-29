"""QOJ local browser integration; disposable snapshots, no live OJ requests."""
import json
from pathlib import Path
import sys
import tempfile
import threading
import uuid
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'desktop'))
from browser_sessions import BrowserSessions, DOMAINS
from browser_preparation import BrowserPreparation
from browser_bridge import BrowserBridge
from external_browser import ExternalBrowserPreparation
from platform_login import PlatformLogins, valid_identity, AUTOMATIC_SITES
from silent_submit import PROFILE_NAMES
from official_bridge import submission_target
from contest_categories import matches_shelf
from training import ServiceError

class QojPlatformTests(unittest.TestCase):
    def test_profile_and_canonical_global_id(self):
        self.assertEqual(PROFILE_NAMES['QOJ'],'tb-qoj')
        self.assertEqual(len(set(PROFILE_NAMES.values())),len(PROFILE_NAMES))
        target=submission_target('https://qoj.ac/problem/18307')
        self.assertEqual(target['platform'],'QOJ');self.assertEqual(target['problem'],'18307')
        for bad in ['https://qoj.ac/contest/3767/problem/A','https://qoj.ac/contest/3767/problem/18307','https://contest.ucup.ac/problem/18307','https://qoj.ac/problem/18307?contest_id=3767']:
            with self.assertRaises(ValueError):submission_target(bad)

    def test_session_scope_roundtrip_and_foreign_cookie_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'isolated.fixture';crypt=lambda data,decrypt=False:data
            store=BrowserSessions(path,crypt=crypt);store.request('QOJ');request=store.requests()[0]
            self.assertEqual(request['domains'],['qoj.ac'])
            cookie={'name':'session','value':'synthetic','domain':'.qoj.ac','path':'/','secure':True}
            for domain in ['qoj.ac.evil.test','ucup.ac','codeforces.com']:
                with self.assertRaises(ServiceError):store.accept({**request,'cookies':[{**cookie,'domain':domain}]})
            store.accept({**request,'loginState':'logged_in','cookies':[cookie,{**cookie,'name':'embedded','partitionKey':{'topLevelSite':'https://other.test'}}]})
            restored=BrowserSessions(path,crypt=crypt).snapshot('QOJ')
            self.assertEqual(restored['loginState'],'logged_in');self.assertEqual(len(restored['cookies']),1)

    def test_qoj_local_identity_does_not_bind_public_service_or_join_startup(self):
        owner=object();bind=Mock();bridge=SimpleNamespace(stopping=threading.Event())
        logins=PlatformLogins(bridge,lambda:owner,bind);logins.owner=owner
        value={'platform':'QOJ','url':'https://qoj.ac/','state':'logged_in','owner':'fixture_owner'}
        self.assertTrue(logins._accept(owner,'QOJ',value));bind.assert_not_called()
        self.assertEqual(logins.snapshot()['platforms']['QOJ']['owner'],'fixture_owner')
        self.assertNotIn('QOJ',AUTOMATIC_SITES)
        for change in [{'url':'https://qoj.ac.evil.test/'},{'url':'http://qoj.ac/'},{'url':'https://other@qoj.ac/'},{'state':'unknown'},{'owner':'has.dot'}]:
            self.assertIsNone(valid_identity({**value,**change},'QOJ'))

    def test_external_preparation_explicit_login(self):
        browser=SimpleNamespace(preferred='edge',new_page=Mock())
        bridge=SimpleNamespace(browser=browser,lock=threading.RLock(),sessions={})
        preparation=ExternalBrowserPreparation(bridge)
        with patch('external_browser.browsers',return_value={'edge':'fixture','chrome':None}):
            item=next(p for p in preparation.snapshot()['platforms'] if p['platform']=='QOJ')
            self.assertEqual(item['loginUrl'],'https://qoj.ac/login')
            self.assertTrue(preparation.action({'action':'open-login','platform':'QOJ','browser':'edge'})['opened'])
        browser.new_page.assert_called_once_with('https://qoj.ac/login','edge')

    def test_unused_qoj_does_not_block_old_platform_readiness(self):
        cached=lambda p:None if p=='QOJ' else {'loginState':'logged_in','cookies':[{'value':'synthetic'}]}
        bridge=SimpleNamespace(lock=threading.RLock(),clock=lambda:0,client_seen={},client_versions={},_session_client=lambda p:None,session_store=SimpleNamespace(snapshot=cached))
        with tempfile.TemporaryDirectory() as directory:
            preparation=BrowserPreparation(bridge,directory,profiles=lambda:[('fixture','Default')])
            state=preparation.snapshot();self.assertTrue(state['ready'])
            self.assertEqual({p['platform'] for p in state['platforms']},set(DOMAINS))
            self.assertEqual(next(p for p in state['platforms'] if p['platform']=='QOJ')['state'],'not_synced')

    def test_series_and_source_platform_both_match(self):
        for platform in ['QOJ','Codeforces','牛客','洛谷']:
            row={'platform':platform,'contest':'ICPC 2026 西安区域赛','series':'XCPC'}
            self.assertTrue(matches_shelf(row,platform));self.assertTrue(matches_shelf(row,'XCPC'))
            self.assertFalse(matches_shelf(row,'AtCoder'))

    def test_all_five_platform_refreshes_keep_nonce_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            store=BrowserSessions(Path(directory)/'fixture',crypt=lambda data,decrypt=False:data)
            bridge=BrowserBridge('http://127.0.0.1:1',session_store=store);client=str(uuid.uuid4())
            key=bridge.register_browser({'clientId':client,'protocol':3})['key']
            body={'clientId':client,'syncPlatforms':list(DOMAINS),'loginStates':dict.fromkeys(DOMAINS,'logged_in')}
            answer=bridge.browser_queue(body,key)
            request=next(r for r in answer['sync'] if r['platform']=='QOJ')
            self.assertEqual(request['domains'],['qoj.ac']);self.assertTrue(request['nonce'])
            for bad in [list(DOMAINS)+['QOJ'],['NotAPlatform']]:
                with self.assertRaises(ServiceError):bridge.browser_queue({**body,'syncPlatforms':bad},key)

if __name__=='__main__':unittest.main()
