"""Terminal receipt retries are local and monotonic; no real browser or site."""
import hashlib
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock,patch

from connected_browser import ConnectedBrowserBridge
from external_browser import ExternalBrowserBridge
import test_reviews as review_fixtures
import test_training as training_fixtures
from training import TrainingService,iso

URL='https://ac.nowcoder.com/acm/problem/21992'
REMOTE='85470511'


def saved(verdict='CE',remote=REMOTE):
    return {'id':'official-'+hashlib.sha256(('ac.nowcoder.com/'+remote).encode()).hexdigest(),
            'scope':'official','mode':'submit','verdict':verdict,'finishedAt':'2026-11-10T10:00:00Z',
            'message':'原站确认提交 #'+remote,'code':'int main(){}'}


class TerminalReceiptRetryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.now=100.0
        self.clock=patch('time.monotonic',side_effect=lambda:self.now);self.clock.start()
        self.addCleanup(self.clock.stop);self.addCleanup(self.temp.cleanup)

    def bridge(self,kind,callback):
        browser=Mock();pending=Mock(return_value=True)
        if kind=='external':
            bridge=ExternalBrowserBridge(Path(self.temp.name)/'never-opened',browser_process=browser,
                on_receipt=callback,on_pending=pending)
            bridge.sessions['job']={'sessionId':'job','platform':'牛客','problem':'21992','originalUrl':URL,'url':URL,
                'code':'int main(){}','language':'cpp17','created':self.now,'status':'judging',
                'attempted':True,'submissionId':REMOTE,'autoClose':True,'acceptedAt':'2026-11-10T09:59:00Z','target':'owned'}
        else:
            bridge=ConnectedBrowserBridge('http://127.0.0.1:1',on_receipt=callback,on_pending=pending,clock=lambda:self.now)
            bridge.sessions['job']={'sessionId':'job','platform':'牛客','problem':'21992','originalUrl':URL,'url':URL,
                'code':'int main(){}','language':'cpp17','createdAt':self.now,'status':'judging',
                'ownerVerified':True,'attempted':True,'submissionId':REMOTE,'autoClose':True,'acceptedAt':'2026-11-10T09:59:00Z'}
        return bridge,browser,pending

    @staticmethod
    def terminal(bridge,verdict='CE',message=None):
        value={'status':'finished','verdict':verdict,'submissionId':REMOTE,'attempted':True}
        if message is not None:value['message']=message
        if isinstance(bridge,ConnectedBrowserBridge):
            bridge._update(bridge.sessions['job'],value);bridge._persist('job')
        else:bridge._update('job',value)

    def test_status_retries_frozen_terminal_without_another_remote_event(self):
        for kind in ('connected','external'):
            for verdict in ('CE','WA','AC'):
                with self.subTest(kind=kind,verdict=verdict):
                    callback=Mock(side_effect=[None,saved(verdict)])
                    bridge,browser,pending=self.bridge(kind,callback);self.terminal(bridge,verdict)
                    self.assertEqual(bridge.status('job')['status'],'judging')
                    self.now+=1
                    value=bridge.status('job')
                    self.assertEqual((value['status'],value['verdict']),('finished',verdict))
                    self.assertEqual(value['submission']['id'],saved(verdict)['id'])
                    self.assertEqual(value['message'],'原站本次提交 #'+REMOTE+'：'+verdict)
                    for _ in range(3):bridge.status('job')
                    self.assertEqual(callback.call_count,2);self.assertEqual(pending.call_count,1)
                    self.assertEqual(browser.mock_calls,[]);self.assertNotIn('_terminalReceipt',value)

    def test_late_judging_or_different_sid_cannot_erase_the_terminal_to_be_saved(self):
        for kind in ('connected','external'):
            with self.subTest(kind=kind):
                callback=Mock(side_effect=[None,saved()]);bridge,_,_=self.bridge(kind,callback);self.terminal(bridge)
                late={'status':'judging','submissionId':'85470529','attempted':True}
                if kind=='connected':bridge._update(bridge.sessions['job'],late)
                else:bridge._update('job',late,inspection=True)
                self.now+=1;value=bridge.status('job')
                self.assertEqual((value['status'],value['submissionId'],value['verdict']),('finished',REMOTE,'CE'))
                self.assertEqual(callback.call_args.args[1]['submissionId'],REMOTE)

    def test_concurrent_local_status_retries_save_only_once(self):
        for kind in ('connected','external'):
            with self.subTest(kind=kind):
                entered=threading.Event();release=threading.Event();attempts=[]
                def callback(*_args):
                    attempts.append(1)
                    if len(attempts)==1:return None
                    entered.set();self.assertTrue(release.wait(2));return saved()
                bridge,_,_=self.bridge(kind,callback);self.terminal(bridge);self.now+=1
                first=threading.Thread(target=bridge.status,args=('job',));first.start();self.assertTrue(entered.wait(2))
                others=[threading.Thread(target=bridge.status,args=('job',)) for _ in range(8)]
                for worker in others:worker.start()
                for worker in others:worker.join(1)
                release.set();first.join(2)
                self.assertEqual(len(attempts),2);self.assertEqual(bridge.status('job')['status'],'finished')

    def test_invalid_local_saved_row_does_not_replace_the_official_terminal(self):
        for kind in ('connected','external'):
            with self.subTest(kind=kind):
                callback=Mock(side_effect=[{**saved(),'scope':'local'},saved()]);bridge,_,_=self.bridge(kind,callback)
                self.terminal(bridge);self.assertEqual(bridge.status('job')['status'],'judging')
                self.now+=1;self.assertEqual(bridge.status('job')['status'],'finished')

    def test_external_display_ack_closes_an_owned_page_only_once_under_concurrency(self):
        bridge,browser,_=self.bridge('external',Mock(return_value=saved()));self.terminal(bridge)
        entered=threading.Event();release=threading.Event()
        def close(_target):entered.set();self.assertTrue(release.wait(2));return True
        browser.close_page.side_effect=close
        first=threading.Thread(target=bridge.acknowledge,args=('job',));first.start();self.assertTrue(entered.wait(2))
        others=[threading.Thread(target=bridge.acknowledge,args=('job',)) for _ in range(8)]
        for worker in others:worker.start()
        for worker in others:worker.join(1)
        release.set();first.join(2);self.assertTrue(bridge.acknowledge('job')['closed'])
        browser.close_page.assert_called_once_with('owned')

    def test_recovery_terminal_retry_is_local_and_never_starts_another_query_worker(self):
        for kind in ('connected','external'):
            with self.subTest(kind=kind):
                callback=Mock(side_effect=[None,saved()]);bridge,_,_=self.bridge(kind,callback)
                bridge.sessions['job'].update(readOnlyRestore=True,prepared=True)
                self.terminal(bridge);self.now+=1
                with patch('threading.Thread') as worker:value=bridge.retry_recovery('job')
                self.assertEqual(value['status'],'finished');worker.assert_not_called()

    def test_saved_terminal_restores_original_message_after_a_local_retry(self):
        for kind in ('connected','external'):
            with self.subTest(kind=kind):
                bridge,_,_=self.bridge(kind,Mock(side_effect=[None,saved()]))
                self.terminal(bridge,message='本次提交结果：CE');self.now+=1
                self.assertEqual(bridge.status('job')['message'],'本次提交结果：CE')

    def test_manual_ajax_acceptance_without_submitted_requires_original_owned_observer_proof(self):
        from test_official_pending_recovery import OldPage,binding
        for change in ('valid','wrong_sid','wrong_owner','wrong_binding','wrong_source','bare_terminal','not_manual'):
            with self.subTest(change=change):
                callback=Mock(return_value=saved());bridge,_,_=self.bridge('external',callback)
                session=bridge.sessions['job'];session.update(attempted=False,status='awaiting_submit',_manualWindow=True,autoClose=False)
                session.pop('submissionId')
                record={'sessionId':'job','submissionId':REMOTE,'url':URL,'code':session['code']}
                page=OldPage(record);value={'sessionId':'job','status':'judging','attempted':True,'submissionId':REMOTE,
                    'receiptBinding':binding(),'submittedCode':session['code']}
                if change=='wrong_sid':page.proof['submissionId']='85470529'
                if change=='wrong_owner':page.proof['ownerMatches']=False
                if change=='wrong_binding':value['receiptBinding']['query']['subTagId']='1'
                if change=='wrong_source':value['submittedCode']='different source'
                if change=='bare_terminal':value.update(status='finished',verdict='CE')
                if change=='not_manual':session['_manualWindow']=False
                bridge._event('job',{'name':'__tbReceipt','payload':json.dumps(value)},page)
                if change!='valid':
                    self.assertFalse(session['attempted']);self.assertNotIn('submissionId',session);callback.assert_not_called();continue
                self.assertTrue(session['attempted']);self.assertEqual(session['submissionId'],REMOTE);callback.assert_not_called()
                terminal={**value,'status':'finished','verdict':'CE'}
                for altered in ({**terminal,'submissionId':'85470529'},
                                {**terminal,'receiptBinding':{**binding(),'owner':'999'}}):
                    bridge._event('job',{'name':'__tbReceipt','payload':json.dumps(altered)},page)
                callback.assert_not_called()
                bridge._event('job',{'name':'__tbReceipt','payload':json.dumps(terminal)},page)
                self.assertEqual(bridge.status('job')['status'],'finished');callback.assert_called_once()
                self.assertFalse(bridge.acknowledge('job')['closed'])


class DurableReviewReceiptTests(unittest.TestCase):
    setUp=training_fixtures.ServiceTests.setUp
    tearDown=training_fixtures.ServiceTests.tearDown
    seed=review_fixtures.ReviewTests.seed
    due=review_fixtures.ReviewTests.due
    open=review_fixtures.ReviewTests.open
    receipt=review_fixtures.ReviewTests.receipt

    def test_restart_reads_only_exact_completed_review_receipt_without_another_grant_or_write(self):
        self.seed();self.clock.advance(days=1);task=self.open()
        session={'id':'fixture::A','url':self.assets.problem('fixture::A')['url'],'code':'independent rewrite',
            'language':'cpp17','reviewId':task['id'],'sessionId':'review-job'}
        answer={'status':'finished','submissionId':REMOTE,'verdict':'AC','acceptedAt':iso(self.clock())}
        saved_row=self.service.record_official(session,answer)
        self.assertEqual(self.service.workspace()['reviews']['tasks'],[])
        self.service.close();self.service=TrainingService(self.library,self.db,self.assets,self.judge,self.clock,self.root/'backups')
        restored={**session,'readOnlyRestore':True,'_training':self.service}
        def snapshot():return {table:[tuple(row) for row in self.service.connection.execute('SELECT * FROM '+table)]
                               for table in ('submissions','drafts','account_preferences','training')}
        before=snapshot()
        with patch.object(self.service,'review_task',side_effect=AssertionError('must not request a new grant')):
            for _ in range(3):self.assertEqual(self.service.record_official(restored,answer)['id'],saved_row['id'])
            for change in ({'code':'different source'},{'language':'python3'},{'contestId':'another-contest'},
                           {'reviewId':'another-review'},{'_training':object()}):
                with self.subTest(change=list(change)):
                    self.assertIsNone(self.service.record_official({**restored,**change},answer))
            self.assertIsNone(self.service.record_official(restored,{**answer,'acceptedAt':'2020-01-01T00:00:00Z'}))
            self.assertIsNone(self.service.record_official(restored,{**answer,'verdict':'WA'}))
            with self.assertRaises(AssertionError):self.service.record_official(session,answer)
        self.assertEqual(snapshot(),before)


if __name__=='__main__':unittest.main()
