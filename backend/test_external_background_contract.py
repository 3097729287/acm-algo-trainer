"""Background windows and exact durable-result closing, without a browser/OJ."""
import copy
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from external_browser import BrowserProcess, ExternalBrowserBridge
from training import ServiceError


def saved(remote='101', verdict='AC'):
    return {'id': 'official-' + 'a' * 64, 'scope': 'official', 'mode': 'submit',
            'verdict': verdict, 'finishedAt': '2026-11-09T00:00:00Z',
            'message': '原站确认提交 #' + remote}


class BackgroundContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tb-background-contract-')
        self.profile = Path(self.temp.name) / 'profile'

    def tearDown(self):
        self.temp.cleanup()

    def bridge(self, on_receipt=None):
        browser = Mock()
        bridge = ExternalBrowserBridge(self.profile, browser_process=browser, on_receipt=on_receipt)
        return bridge, browser

    def test_new_window_is_minimized_at_creation_and_old_protocol_fails_closed(self):
        browser = BrowserProcess(self.profile)
        browser.ensure = Mock()
        protocol = {'domains': [{'domain': 'Target', 'commands': [{'name': 'createTarget',
                     'parameters': [{'name': 'windowState'}]}]}]}
        browser.request = Mock(side_effect=lambda path: protocol if path == '/json/protocol'
            else [{'id': 'owned', 'webSocketDebuggerUrl': 'ws://fixture/page'}] if path == '/json/list'
            else {'webSocketDebuggerUrl': 'ws://fixture/browser'})
        inspector = Mock()
        inspector.call.return_value = {'targetId': 'owned'}
        with patch('external_browser.DevToolsPage', return_value=inspector):
            self.assertEqual(browser.new_submission_page()['id'], 'owned')
        browser.ensure.assert_called_once_with(background=True)
        inspector.call.assert_called_once_with('Target.createTarget', {
            'url': 'about:blank', 'newWindow': True, 'background': True, 'windowState': 'minimized'})
        browser.request = Mock(return_value={'domains': []})
        with patch('external_browser.DevToolsPage') as created, self.assertRaises(ServiceError):
            browser.new_submission_page()
        created.assert_not_called()

    def test_manual_display_does_not_activate_or_restore_through_cdp(self):
        browser = BrowserProcess(self.profile)
        browser.request = Mock(return_value={'webSocketDebuggerUrl': 'ws://fixture/browser'})
        inspector = Mock()
        inspector.call.side_effect = [{'windowId': 4, 'bounds': {'windowState': 'minimized'}},
                                      {'processInfo': [{'type': 'browser', 'id': 123}]}]
        page = Mock()
        page.evaluate.return_value = 'Owned page'
        with patch('external_browser.DevToolsPage', return_value=inspector), \
                patch('browser_presentation.present_window', return_value=True) as present:
            self.assertTrue(browser.present_page('owned', page, True, activate=False))
        self.assertFalse(present.call_args.kwargs['activate'])
        page.call.assert_not_called()
        self.assertFalse(any(c.args[0] == 'Browser.setWindowBounds' for c in inspector.call.call_args_list))

    def test_pending_submit_never_requests_focus_and_manual_open_is_retained(self):
        bridge, _browser = self.bridge()
        url = 'https://codeforces.com/contest/123/problem/A'
        with patch('external_browser.threading.Thread'):
            value = bridge.submit(url, 'int main(){}', 'isolated')
            live = bridge.sessions[value['sessionId']]
            self.assertFalse(live['focus'])
            bridge.submit(url, 'int main(){}', 'isolated')
            self.assertFalse(live['focus'])
            bridge.open(url, 'int main(){}', 'isolated')
            self.assertFalse(live['focus'])
            self.assertFalse(live['autoClose'])
            bridge.submit(url, 'int main(){}', 'isolated')
            self.assertFalse(live['autoClose'], 'A manual page is never automatically destroyed')
            bridge._update(value['sessionId'], {'status': 'needs_login', 'attempted': False})
            self.assertTrue(live['focus'])
            self.assertNotIn('_manualWindow', bridge.status(value['sessionId']))

    def test_cf_old_sid_before_click_or_before_watermark_never_finishes(self):
        persist = Mock(return_value=saved('102'))
        bridge, browser = self.bridge(persist)
        bridge.sessions['s'] = {'status': 'loading', 'platform': 'Codeforces',
            'sessionId': 's', 'attempted': False, 'autoClose': True, 'target': 'owned',
            'baselineKnown': True, 'baseline': ['100', '101']}
        for attempted, remote in [(False, '102'), (True, '101'), (True, '99')]:
            bridge.sessions['s']['attempted'] = attempted
            before = copy.deepcopy(bridge.sessions['s'])
            bridge._update('s', {'status': 'finished', 'submissionId': remote, 'verdict': 'AC'})
            self.assertEqual(bridge.sessions['s'], before)
        persist.assert_not_called()
        browser.close_page.assert_not_called()

    def test_sid_is_immutable_and_only_matching_persisted_receipt_can_close(self):
        bridge, browser = self.bridge(lambda *_: saved('102'))
        bridge.sessions['s'] = {'status': 'submitted', 'platform': 'Codeforces',
            'sessionId': 's', 'attempted': True, 'autoClose': True, 'target': 'owned',
            'baselineKnown': True, 'baseline': ['101']}
        bridge._update('s', {'status': 'judging', 'submissionId': '102'})
        bridge._update('s', {'status': 'finished', 'submissionId': '103', 'verdict': 'AC'})
        self.assertEqual(bridge.status('s')['status'], 'judging')
        bridge._update('s', {'status': 'finished', 'submissionId': '102', 'verdict': 'AC'})
        browser.close_page.assert_not_called()
        self.assertTrue(bridge.acknowledge('s')['closed'])
        self.assertTrue(bridge.acknowledge('s')['closed'])
        browser.close_page.assert_called_once_with('owned')

    def test_failed_save_missing_record_or_mismatched_record_never_closes(self):
        for record in [False, True, saved('999'), {**saved(), 'scope': 'local'},
                       {**saved(), 'verdict': 'WA'}, {**saved(), 'finishedAt': None},
                       {**saved(), 'id': 1}, {**saved(), 'message': 1}]:
            bridge, browser = self.bridge(lambda *_args, value=record: value)
            bridge.sessions['s'] = {'status': 'submitted', 'sessionId': 's',
                'attempted': True, 'autoClose': True, 'target': 'owned'}
            bridge._update('s', {'status': 'finished', 'submissionId': '101', 'verdict': 'AC'})
            self.assertFalse(bridge.acknowledge('s')['closed'])
            browser.close_page.assert_not_called()

    def test_worker_only_activates_for_login_and_does_not_close_on_finish(self):
        bridge, browser = self.bridge(lambda *_: saved())
        browser.new_submission_page.return_value = {'id': 'owned', 'webSocketDebuggerUrl': 'ws://fixture/page'}
        browser.present_page.return_value = True
        states = iter([{'status': 'needs_login', 'attempted': False},
                       {'status': 'ready'}, {'status': 'ready'},
                       {'status': 'finished', 'submissionId': '101', 'verdict': 'AC'}])
        page = Mock()
        def evaluate(script):
            if script == 'location.href':
                return 'https://codeforces.com/contest/123/submit'
            if ', "submit",' in script or ',"submit",' in script:
                bridge._update('s', {'status': 'submitted', 'attempted': True,
                    'baselineKnown': True, 'baseline': [], 'baselineOwner': 'fixture'})
                return {'status': 'loading'}
            return next(states)
        page.evaluate.side_effect = evaluate
        bridge.sessions['s'] = {'sessionId': 's', 'platform': 'Codeforces', 'problem': 'A',
            'originalUrl': 'https://codeforces.com/contest/123/problem/A',
            'url': 'https://codeforces.com/contest/123/submit', 'code': 'int main(){}',
            'status': 'loading', 'attempted': False, 'intent': True, 'dispatched': False,
            'explicitVisible': False, 'autoClose': True, 'created': time.monotonic()}
        with patch('external_browser.DevToolsPage', return_value=page):
            bridge._run('s')
        self.assertEqual(bridge.status('s')['status'], 'finished')
        activated = [c for c in browser.present_page.call_args_list if c.kwargs['activate']]
        self.assertEqual(len(activated), 1)
        self.assertTrue(activated[0].args[2])
        browser.close_page.assert_not_called()

    def test_uncertain_attempt_reconnects_only_same_page_and_never_rearms(self):
        bridge, browser = self.bridge()
        url='https://ac.nowcoder.com/acm/problem/16570'
        with patch('external_browser.threading.Thread') as thread:
            first=bridge.submit(url,'int main(){}','isolated')
            live=bridge.sessions[first['sessionId']]
            live.update(status='unconfirmed',attempted=True,submissionId='101',target='owned',intent=False)
            value=bridge.submit(url,'int main(){}','isolated')
            self.assertEqual(value['sessionId'],first['sessionId'])
            self.assertEqual(value['submissionId'],'101')
            self.assertFalse(live['intent'])
            self.assertTrue(live['dispatched'])
            self.assertEqual(live['_resumeTarget'],'owned')
            self.assertEqual(thread.call_count,2)
            bridge.submit(url,'int main(){}','isolated')
            self.assertEqual(thread.call_count,2,'Repeated recheck has only one worker')
            with self.assertRaises(ServiceError):
                bridge.submit(url,'changed source','isolated')
        live.update(status='judging')
        browser.request.return_value=[]
        bridge._run(first['sessionId'])
        self.assertEqual(bridge.status(first['sessionId'])['status'],'unconfirmed')
        browser.new_submission_page.assert_not_called()
        browser.close_page.assert_not_called()

    def test_recheck_attaches_existing_page_without_navigation_or_submit(self):
        bridge,browser=self.bridge(lambda *_:saved('101','WA'))
        target={'id':'owned','webSocketDebuggerUrl':'ws://fixture/owned'}
        browser.request.return_value=[target]
        url='https://ac.nowcoder.com/acm/problem/16570'
        bridge.sessions['s']={'sessionId':'s','platform':'牛客','originalUrl':url,'url':url,'code':'int main(){}',
            'status':'judging','submissionId':'101','attempted':True,'intent':False,'dispatched':True,
            'created':time.monotonic(),'target':'owned','_resumeTarget':'owned','autoClose':True}
        page=Mock()
        def evaluate(script):
            if script.endswith(';true'):return True
            if script=='location.href':return url
            self.assertIn(',"inspect",',script)
            return {'status':'finished','submissionId':'101','verdict':'WA'}
        page.evaluate.side_effect=evaluate
        with patch('external_browser.DevToolsPage',return_value=page):bridge._run('s')
        self.assertEqual(bridge.status('s')['status'],'finished')
        self.assertFalse(any(call.args[0]=='Page.navigate' for call in page.call.call_args_list))
        browser.new_submission_page.assert_not_called()
        browser.close_page.assert_not_called()
        self.assertTrue(bridge.acknowledge('s')['closed'])


if __name__ == '__main__':
    unittest.main()
