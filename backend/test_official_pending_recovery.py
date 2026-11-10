"""Restarted real SQLite/HTTP services; browser/provider calls stay isolated."""
import copy
import hashlib
from pathlib import Path
import sys
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
from urllib.parse import quote

import backend
import test_training as fixtures
from training import TrainingService,iso
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'desktop'))
from external_browser import ExternalBrowserBridge
from official_recovery import legacy_nowcoder_proof,nowcoder_binding,source_hash


URL='https://ac.nowcoder.com/acm/problem/21992'


def binding(url=URL):
    return {'version':1,'platform':'牛客','owner':'12345',
        'identity':{'kind':'global','problemId':url.rsplit('/',1)[-1],'questionId':'308955','originalUrl':url},
        'origin':'https://ac.nowcoder.com','statusPath':'/nccommon/status','query':{'tagId':'4','subTagId':'0'}}


class OldPage:
    def __init__(self,record,changes=None):
        self.record=record
        self.proof={'sessionId':record['sessionId'],'submissionId':record['submissionId'],'ownerMatches':True,
            'currentUrl':record['url'],'problemId':record['url'].rsplit('/',1)[-1],'questionId':'308955','binding':binding(record['url'])}
        self.context={'sessionId':record['sessionId'],'url':record['url'],'language':'cpp17','sourceHash':source_hash(record['code'])}
        if changes:changes(self)
        self.closed=False

    def evaluate(self,_script):return copy.deepcopy(self.proof)
    def close(self):self.closed=True
    def call(self,method,params):
        if method=='Runtime.evaluate':return {'result':{'objectId':'poll'}}
        if method=='Runtime.callFunctionOn':return {'result':{'value':copy.deepcopy(self.context)}}
        assert method=='Runtime.getProperties'
        if params['objectId']=='poll':return {'internalProperties':[{'name':'[[Scopes]]','value':{'objectId':'scopes'}}]}
        if params['objectId']=='scopes':return {'result':[{'name':'0','value':{'objectId':'scope'}}]}
        return {'result':[{'name':'ctx','value':{'objectId':'context'}}]}


class PendingRecoveryTests(unittest.TestCase):
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown

    def pending(self,sid='900001',code='int main(){return 1;}',url=URL,known=False):
        self.library.rows[0].update(url=url,platform='牛客')
        record={'sessionId':'old-'+sid,'submissionId':sid,'problemId':'fixture::A','url':url,'code':code,
                'platform':'牛客','acceptedAt':iso(self.clock()),'language':'cpp17'}
        if known:
            record['receiptBinding']=binding(url);self.assertTrue(self.service.save_official_pending(record))
        else:
            identity=hashlib.sha256((record['sessionId']+':'+sid).encode()).hexdigest()
            self.service.connection.execute('INSERT INTO official_pending VALUES(?,?,?,?,?,?,?,?)',
                (identity,record['sessionId'],sid,'fixture::A',url,code,'牛客',record['acceptedAt']))
        return record

    def server_bridge(self):
        server=object.__new__(backend.LocalServer);server.training=self.service
        server.official_sessions={};server.official_pending_receipts={};server.official_session_lock=threading.RLock()
        browser=Mock();browser.request.return_value=[]
        bridge=ExternalBrowserBridge(self.root/'unused-pure-profile',browser_process=browser,
            on_pending=server.record_official_pending,on_receipt=server.record_official_receipt,
            recovery_current=lambda owner:server.training is owner)
        server.official_restorer=bridge.restore_pending;server.official_status=bridge.status
        return server,bridge,browser

    def restart(self):
        self.service.close();self.service=TrainingService(self.library,self.db,self.assets,self.judge,self.clock,self.root/'backups')

    def test_fast_terminal_before_http_registration_is_saved_and_acknowledgeable_once(self):
        from reviews import reward_totals
        self.library.rows[0].update(url=URL,platform='牛客')
        for index,verdict in enumerate(('CE','WA','AC')):
            with self.subTest(verdict=verdict):
                server,bridge,browser=self.server_bridge();identity='fast-'+verdict;remote=str(85470511+index)
                bridge.sessions[identity]={'sessionId':identity,'status':'judging','attempted':True,'platform':'牛客',
                    'originalUrl':URL,'url':URL,'code':'int main(){}','language':'cpp17','target':'owned',
                    'acceptedAt':iso(self.clock()),'submissionId':remote,'autoClose':True}
                answer={'status':'finished','submissionId':remote,'verdict':verdict}
                with patch('official_bridge.time.monotonic',return_value=100):
                    bridge._update(identity,answer)
                    self.assertEqual(bridge.status(identity)['status'],'judging')
                server.record_official_pending(identity,{**bridge.sessions[identity],'status':'judging'})
                self.assertEqual(server.official_pending_receipts[identity]['status'],'finished')
                context={'id':'fixture::A','url':URL,'code':'int main(){}','language':'cpp17'}
                with patch.object(self.service,'record_official',wraps=self.service.record_official) as write:
                    saved=server.register_official_session(identity,context,{'status':'judging'})
                    before=reward_totals(self.service)
                    with patch('official_bridge.time.monotonic',return_value=101):
                        value=bridge.status(identity)
                    self.assertEqual((value['status'],value['verdict']),('finished',verdict))
                    self.assertEqual(value['submission']['id'],saved['id'])
                    for _ in range(3):self.assertEqual(server.record_official_receipt(identity,answer)['id'],saved['id'])
                    self.assertEqual(write.call_count,1);self.assertEqual(reward_totals(self.service),before)
                self.assertEqual(self.service.official_pending(),[])
                browser.close_page.return_value=True
                self.assertTrue(bridge.acknowledge(identity)['closed']);self.assertTrue(bridge.acknowledge(identity)['closed'])
                browser.close_page.assert_called_once_with('owned');browser.new_submission_page.assert_not_called()

    def test_concurrent_backend_receipt_replays_do_not_repeat_persistence(self):
        self.library.rows[0].update(url=URL,platform='牛客');server,_,_=self.server_bridge()
        server.register_official_session('job',{'id':'fixture::A','url':URL,'code':'int main(){}'}, {})
        answer={'status':'finished','submissionId':'85470511','verdict':'CE'}
        entered=threading.Event();release=threading.Event();result=[];original=self.service.record_official
        def save(*args):entered.set();self.assertTrue(release.wait(2));return original(*args)
        with patch.object(self.service,'record_official',side_effect=save) as write:
            first=threading.Thread(target=lambda:result.append(server.record_official_receipt('job',answer)))
            second=threading.Thread(target=lambda:result.append(server.record_official_receipt('job',answer)))
            first.start();self.assertTrue(entered.wait(2));second.start();release.set();first.join(2);second.join(2)
            self.assertEqual(write.call_count,1)
        self.assertEqual(len(result),2);self.assertEqual(result[0]['id'],result[1]['id'])
        self.assertEqual(self.service.submissions()['total'],1)

    def test_old_journal_restarts_proves_original_page_and_saves_only_original_sid(self):
        original=self.pending();other=self.pending('900002','another source')
        self.service.save_draft('fixture::A','unsent current input')
        self.restart();server,bridge,browser=self.server_bridge()
        with patch('external_browser.threading.Thread'):
            server.begin_official_recovery()
        record=self.service.official_pending()[0];page=OldPage(record)
        browser.request.return_value=[{'id':'owned','type':'page','url':URL,'webSocketDebuggerUrl':'ws://fixture/owned'}]
        bridge._run=Mock(side_effect=lambda identity:bridge._update(identity,{'status':'finished','submissionId':original['submissionId'],'verdict':'CE'}))
        with patch('external_browser.DevToolsPage',return_value=page):bridge._run_restore(original['sessionId'])
        browser.new_submission_page.assert_not_called();browser.close_page.assert_not_called()
        rows=self.service.submissions()['submissions'];self.assertEqual(len(rows),1)
        self.assertEqual((rows[0]['verdict'],rows[0]['code'],rows[0]['submittedAt']),('CE',original['code'],original['acceptedAt']))
        self.assertEqual(self.service.problem('fixture::A')['draft'],'unsent current input')
        self.assertEqual([r['submissionId'] for r in self.service.official_pending()],[other['submissionId']])
        self.assertTrue(bridge.status(original['sessionId'])['receiptSaved'])

    def test_verified_metadata_survives_restart_and_queries_fresh_owned_page(self):
        original=self.pending(known=True);self.restart();server,bridge,browser=self.server_bridge()
        with patch('external_browser.threading.Thread'):server.begin_official_recovery()
        browser.new_submission_page.return_value={'id':'new-owned','webSocketDebuggerUrl':'ws://fixture/new'}
        bridge._run=Mock()
        bridge._run_restore(original['sessionId'])
        session=bridge.sessions[original['sessionId']]
        self.assertFalse(session['intent']);self.assertTrue(session['attempted']);self.assertTrue(session['_resumeNavigate'])
        self.assertEqual(session['url'],URL);self.assertEqual(session['submissionId'],original['submissionId'])
        browser.new_submission_page.assert_called_once();bridge._run.assert_called_once_with(original['sessionId'])
        self.assertEqual(self.service.official_pending()[0]['metadata']['receiptBinding'],binding())
        self.assertNotIn('receiptBinding',bridge.status(original['sessionId']))
        self.assertNotIn('_restoreRecord',bridge.status(original['sessionId']))

    def test_legacy_mismatch_preserves_pending_and_never_queries_or_creates_a_page(self):
        original=self.pending();record=self.service.official_pending()[0]
        changes=[lambda p:p.proof.update(ownerMatches=False),lambda p:p.proof.update(submissionId='900099'),
            lambda p:p.proof.update(sessionId='different-session'),lambda p:p.proof.update(questionId='999'),
            lambda p:p.proof['binding']['query'].update(tagId='1'),lambda p:p.proof['binding']['query'].update(subTagId='1'),
            lambda p:p.proof['binding'].update(origin='https://evil.test'),lambda p:p.context.update(sourceHash='0'*64),
            lambda p:p.context.update(language='javascript'),lambda p:p.context.update(url=URL+'0')]
        for change in changes:
            with self.subTest(change=change):
                server,bridge,browser=self.server_bridge()
                with patch('external_browser.threading.Thread'):server.begin_official_recovery()
                browser.request.return_value=[{'id':'owned','url':URL,'webSocketDebuggerUrl':'ws://fixture/owned'}]
                bridge._run=Mock()
                with patch('external_browser.DevToolsPage',return_value=OldPage(record,change)):bridge._run_restore(original['sessionId'])
                self.assertEqual(bridge.status(original['sessionId'])['status'],'unconfirmed')
                bridge._run.assert_not_called();browser.new_submission_page.assert_not_called()
                self.assertEqual(len(self.service.official_pending()),1);self.assertEqual(self.service.submissions()['total'],0)

    def test_query_failure_retry_keeps_original_source_sid_and_single_worker(self):
        original=self.pending(known=True);server,bridge,browser=self.server_bridge()
        with patch('external_browser.threading.Thread'):server.begin_official_recovery()
        browser.ensure.side_effect=OSError('isolated disconnect');bridge._run_restore(original['sessionId'])
        self.assertEqual(bridge.status(original['sessionId'])['status'],'unconfirmed')
        with patch('external_browser.threading.Thread') as worker:
            bridge.retry_recovery(original['sessionId']);bridge.retry_recovery(original['sessionId'])
            worker.assert_called_once()
        self.assertEqual(bridge.sessions[original['sessionId']]['code'],original['code'])
        self.assertEqual(len(self.service.official_pending()),1)
        self.assertFalse(bridge.sessions[original['sessionId']]['intent'])

    def test_account_switch_stops_before_accessing_browser(self):
        original=self.pending(known=True);server,bridge,browser=self.server_bridge()
        with patch('external_browser.threading.Thread'):server.begin_official_recovery()
        server.training=object();bridge._run_restore(original['sessionId'])
        browser.ensure.assert_not_called();browser.new_submission_page.assert_not_called()
        self.assertEqual(len(self.service.official_pending()),1)

    def test_shutdown_never_starts_a_recovery_browser(self):
        original=self.pending(known=True);server,bridge,browser=self.server_bridge()
        with patch('external_browser.threading.Thread'):server.begin_official_recovery()
        bridge.stopping.set();bridge._run_restore(original['sessionId'])
        browser.ensure.assert_not_called();browser.new_submission_page.assert_not_called()
        self.assertEqual(len(self.service.official_pending()),1)

    def test_existing_final_record_is_not_changed_or_rewarded_by_recovery(self):
        from reviews import reward_totals
        original=self.pending(known=True)
        old=self.service.record_official({'id':'fixture::A','url':URL,'code':'older source','language':'python3'},
            {'status':'finished','submissionId':original['submissionId'],'verdict':'AC','acceptedAt':original['acceptedAt']})
        before=[tuple(r) for r in self.service.connection.execute('SELECT * FROM submissions')]
        rewards=reward_totals(self.service)
        server,bridge,browser=self.server_bridge()
        with patch('external_browser.threading.Thread'):server.begin_official_recovery()
        bridge.sessions[original['sessionId']]['_recoveryVerified']=True
        bridge._update(original['sessionId'],{'status':'finished','submissionId':original['submissionId'],'verdict':'WA'})
        self.assertEqual([tuple(r) for r in self.service.connection.execute('SELECT * FROM submissions')],before)
        self.assertEqual(self.service.submission(old['id'])['submission']['language'],'python3')
        self.assertEqual(len(self.service.official_pending()),1)
        self.assertEqual(reward_totals(self.service),rewards)
        self.assertEqual(bridge.status(original['sessionId'])['status'],'unconfirmed')

    def test_binding_is_immutable_and_no_schema_migration_is_needed(self):
        record=self.pending(known=True);schema=[tuple(r) for r in self.service.connection.execute("SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name")]
        self.assertFalse(self.service.save_official_pending({**record,'receiptBinding':{**binding(),'owner':'999'}}))
        self.restart()
        self.assertEqual(self.service.official_pending()[0]['metadata']['receiptBinding'],binding())
        self.assertEqual([tuple(r) for r in self.service.connection.execute("SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name")],schema)

    def test_repeated_pending_poll_is_read_only_and_invalid_metadata_stays_blocking(self):
        record=self.pending(known=True)
        with patch.object(self.service,'_write',side_effect=AssertionError('unchanged polling must not write')):
            self.assertTrue(self.service.save_official_pending(record))
        self.service.connection.execute("UPDATE account_preferences SET value='invalid-json' WHERE key LIKE 'official-pending:%'")
        rows=self.service.official_pending(URL)
        self.assertEqual(len(rows),1);self.assertTrue(rows[0]['metadata']['_invalid'])
        server,bridge,browser=self.server_bridge()
        with patch('external_browser.threading.Thread') as worker:server.begin_official_recovery();worker.assert_not_called()
        self.assertEqual(bridge.sessions,{})
        browser.ensure.assert_not_called()


class PendingRecoveryHTTPTests(unittest.TestCase):
    setUp=fixtures.HTTPTests.setUp
    tearDown=fixtures.HTTPTests.tearDown
    request=fixtures.HTTPTests.request

    def test_normal_reads_attach_recovery_and_submit_can_only_recheck_old_sid(self):
        service=self.server.training;identity='周赛 164::A';old_row=service._row
        def row(key):return {**old_row(key),'url':URL,'platform':'牛客'}
        native=ExternalBrowserBridge(self.root/'unused-profile',browser_process=Mock())
        native._run_restore=Mock()
        self.server.official_restorer=native.restore_pending;self.server.official_status=native.status
        self.server.official_rechecker=native.retry_recovery
        self.server.official_submitter=Mock();self.server.official_opener=Mock()
        record={'sessionId':'legacy-http','submissionId':'900003','problemId':identity,'url':URL,'platform':'牛客',
            'code':'original immutable source','acceptedAt':iso(self.clock()),'language':'cpp17','receiptBinding':binding()}
        service.save_official_pending(record)
        with patch.object(service,'_row',side_effect=row),patch.object(service._asset_library(),'problem',return_value={**fixtures.Assets(None).problem(identity),'url':URL}):
            self.assertEqual(self.request('GET','/api/workspace')[0],200)
            status,problem=self.request('GET','/api/problem?id='+quote(identity))
            self.assertEqual(status,200);self.assertTrue(problem['officialRecovery']['readOnlyRestore'])
            for code in ('current edited code',''):
                status,value=self.request('POST','/api/official/submit',{'id':identity,'code':code,'language':'python3'})
                self.assertEqual(status,200);self.assertEqual(value['submissionId'],'900003')
            self.server.official_submitter.assert_not_called();self.server.official_opener.assert_not_called()
            self.assertEqual(service.official_pending()[0]['code'],record['code'])
            self.assertEqual(service.submissions()['total'],0)
