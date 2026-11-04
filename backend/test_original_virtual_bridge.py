"""Desktop VP account boundaries; fake browser targets, never an OJ registration."""
import datetime as dt
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from virtual_contest import VirtualContest
from virtual_contests import virtual_spec
from training import ServiceError

class VirtualBridgeTests(unittest.TestCase):
    def make(self,platform='Codeforces',states=None):
        owner=object();current=Mock(return_value=owner)
        browser=SimpleNamespace(new_probe_page=Mock(return_value={'id':'owned-probe','webSocketDebuggerUrl':'ws://isolated'}),new_page=Mock(),close_page=Mock())
        bridge=SimpleNamespace(browser=browser,stopping=threading.Event())
        spec=virtual_spec([{'url':'https://codeforces.com/contest/2278/problem/A'}],120) if platform=='Codeforces' else virtual_spec([{'url':'https://qoj.ac/problem/1','contestId':'2644'}],300)
        identity={'platform':platform,'url':spec['registrationUrl'],'state':'logged_in','owner':'isolated_handle'}
        queue=iter(states or [{'state':'ready'},{'state':'confirmed','startedMs':dt.datetime.now(dt.timezone.utc).timestamp()*1000}])
        def evaluate(script):
            if script.startswith('(()=>{'):return identity
            if '"action": "start"' in script:return {'state':'dispatched'}
            return next(queue)
        page=SimpleNamespace(evaluate=Mock(side_effect=evaluate),close=Mock())
        bind=Mock(return_value=True)
        native=VirtualContest(bridge,current,bind,page_factory=lambda _:page,timeout=2)
        return owner,spec,native,browser,page,bind,current

    def test_cf_clicks_once_and_returns_only_a_confirmed_provider_clock(self):
        owner,spec,native,browser,page,bind,_=self.make()
        result=native(spec,owner)
        self.assertTrue(result['confirmed']);self.assertEqual(result['contestId'],'2278')
        self.assertEqual(sum('"action": "start"' in call.args[0] for call in page.evaluate.call_args_list),1)
        browser.close_page.assert_called_once_with('owned-probe');page.close.assert_called_once()
        self.assertTrue(all(call.args==(owner,'Codeforces','isolated_handle') for call in bind.call_args_list))

    def test_qoj_entry_and_confirmation_are_distinct_native_actions(self):
        owner,spec,native,browser,page,bind,_=self.make('QOJ',[{'state':'ready','intentKey':'qoj-entry'},{'state':'ready','intentKey':'qoj-confirm'},{'state':'confirmed','startedMs':dt.datetime.now(dt.timezone.utc).timestamp()*1000}])
        self.assertTrue(native(spec,owner)['confirmed']);bind.assert_not_called()
        self.assertEqual(sum('"action": "start"' in call.args[0] for call in page.evaluate.call_args_list),2)

    def test_switching_the_training_account_stops_before_any_original_action(self):
        owner,spec,native,browser,page,bind,current=self.make()
        current.side_effect=[owner,object()]
        with self.assertRaisesRegex(ServiceError,'账号已切换'):native(spec,owner)
        self.assertEqual(page.evaluate.call_count,0);browser.close_page.assert_called_once()

    def test_wrong_binding_and_unverified_duration_never_start(self):
        owner,spec,native,browser,page,bind,_=self.make();bind.return_value=False
        with self.assertRaisesRegex(ServiceError,'绑定不一致'):native(spec,owner)
        self.assertFalse(any('"action": "start"' in call.args[0] for call in page.evaluate.call_args_list))
        owner,spec,native,browser,page,bind,_=self.make('QOJ',[{'state':'duration-mismatch'}])
        with self.assertRaisesRegex(ServiceError,'时长'):native(spec,owner)
        self.assertFalse(any('"action": "start"' in call.args[0] for call in page.evaluate.call_args_list))
