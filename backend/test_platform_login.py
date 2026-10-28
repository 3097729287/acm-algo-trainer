"""Authenticated identity boundaries and sequential login setup, no real browser."""
import sys
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'desktop'))
from platform_login import PlatformLogins, SITES, valid_identity
from backend import LocalServer
import test_training as fixtures


class LoginSequenceTests(unittest.TestCase):
    def setUp(self):
        self.owner=object();self.current=self.owner
        self.browser=Mock()
        self.browser.new_page.side_effect=lambda url:{'id':url,'url':url}
        self.bridge=SimpleNamespace(browser=self.browser,stopping=threading.Event())
        self.bound=[]
        self.logins=PlatformLogins(self.bridge,lambda:self.current,lambda owner,site,handle:self.bound.append((owner,site,handle)) or True)
        self.logins.owner=self.owner

    def test_only_authenticated_owner_on_exact_first_party_https_is_accepted(self):
        value={'platform':'Codeforces','url':'https://codeforces.com/','state':'logged_in','owner':'fixture.owner'}
        self.assertEqual(valid_identity(value,'Codeforces'),'fixture.owner')
        for delta in [{'url':'https://codeforces.com.evil.invalid/'},{'url':'http://codeforces.com/'},{'url':'https://other@codeforces.com/'},
                      {'url':'https://codeforces.com:9443/'},{'platform':'AtCoder'},{'state':'unknown'},{'owner':'bad owner'}]:
            self.assertIsNone(valid_identity({**value,**delta},'Codeforces'))
        self.assertFalse(self.logins._accept(self.owner,'Codeforces',{**value,'state':'unknown'}))
        self.assertTrue(self.logins._accept(self.owner,'Codeforces',value))
        self.assertTrue(self.logins._accept(self.owner,'Codeforces',value))
        self.assertEqual(len(self.bound),1)

    def test_missing_logins_open_one_at_a_time_and_closing_one_stops_the_queue(self):
        with patch.object(self.logins,'_probe',return_value=False),patch.object(self.logins,'_wait_login',return_value=False):
            self.logins._prepare(self.owner)
        self.browser.new_page.assert_called_once_with(SITES['Codeforces'][2])

    def test_existing_confirmed_logins_do_not_open_visible_login_pages(self):
        with patch.object(self.logins,'_probe',return_value=True):self.logins._prepare(self.owner)
        self.browser.new_page.assert_not_called()

    def test_next_platform_is_not_opened_before_the_previous_login_completes(self):
        waited=[]
        def complete(owner,platform,target):
            waited.append(platform)
            self.assertEqual(self.browser.new_page.call_count,len(waited))
            return platform=='牛客'
        with patch.object(self.logins,'_probe',side_effect=[True,True,False,False]),patch.object(self.logins,'_wait_login',side_effect=complete):
            self.logins._prepare(self.owner)
        self.assertEqual(waited,['牛客','洛谷'])
        self.assertEqual([call.args[0] for call in self.browser.new_page.call_args_list],[SITES['牛客'][2],SITES['洛谷'][2]])

    def test_account_switch_discards_late_identity_and_pending_popups(self):
        def changed(*_):self.current=object();return False
        with patch.object(self.logins,'_probe',side_effect=changed):self.logins._prepare(self.owner)
        self.browser.new_page.assert_not_called()
        self.assertFalse(self.logins._accept(self.owner,'洛谷',{'platform':'洛谷','url':SITES['洛谷'][1],'state':'logged_in','owner':'42'}))
        self.assertEqual(self.bound,[])


class AutoBindingTests(unittest.TestCase):
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown

    def test_empty_binding_is_saved_but_a_different_configured_owner_is_preserved(self):
        state={'settings':{'accounts':{'codeforces':'','atcoder':'already','nowcoder':'','luogu':''}}}
        def configure(body):state['settings']['accounts'].update(body['accounts']);return state
        extension=SimpleNamespace(snapshot=lambda:state,configure=Mock(side_effect=configure))
        server=SimpleNamespace(training=self.service,accounts=None,store=SimpleNamespace(extensions=extension),official_sync=Mock())
        self.assertTrue(LocalServer.bind_browser_account(server,self.service,'Codeforces','fixture_owner'))
        self.assertTrue(LocalServer.bind_browser_account(server,self.service,'Codeforces','FIXTURE_OWNER'))
        self.assertFalse(LocalServer.bind_browser_account(server,self.service,'AtCoder','other'))
        self.assertFalse(LocalServer.bind_browser_account(server,object(),'洛谷','42'))
        self.assertFalse(LocalServer.bind_browser_account(server,self.service,'洛谷','0'))
        extension.configure.assert_called_once()
        server.official_sync.request_refresh.assert_called_once()


if __name__=='__main__':unittest.main()
