"""Protocol-4 transport contracts, without cookies, a browser or a real OJ."""
from contextvars import ContextVar
import datetime as dt
import json
from pathlib import Path
import sys
import threading
import time
import unittest
import uuid
from unittest.mock import Mock,patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'desktop'))
from connected_browser import ConnectedBrowserBridge
from connected_preparation import ConnectedPreparation
from training import ServiceError


class ConnectedBrowserTests(unittest.TestCase):
    def setUp(self):
        self.owner=object();self.now=0;self.saved=[];self.pending=[];self.scope=ContextVar('scope',default='ordinary')
        self.bridge=ConnectedBrowserBridge('http://127.0.0.1:12345',clock=lambda:self.now,
            guard=lambda _url:(id(self.owner),self.scope.get()),current_owner=lambda:self.owner,
            expected_owner=lambda _platform:'12345',on_identity=lambda owner,_platform,_handle:owner is self.owner,
            on_pending=lambda sid,value:self.pending.append(value) or True,on_receipt=self.save)
        self.url='https://ac.nowcoder.com/acm/problem/21992'
        self.client,self.key=self.connect()

    def save(self,sid,value):
        self.saved.append(value)
        return {'id':'official-'+'a'*64,'mode':'submit','scope':'official','verdict':value['verdict'],
            'message':'原站确认提交 #'+value['submissionId'],'finishedAt':'2026-11-10T00:00:00+00:00'}

    def connect(self,owner='12345'):
        client=str(uuid.uuid4());key=self.bridge.register_browser({'clientId':client,'protocol':4,'browser':'chrome','extensionVersion':'1.6.2'})['key']
        self.queue(client,key,owner)
        return client,key

    def queue(self,client=None,key=None,owner='12345'):
        return self.bridge.browser_queue({'clientId':client or self.client,'hasWindow':True,'identities':{'牛客':self.proof(owner)}},key or self.key)

    def proof(self,owner='12345'):
        return {'platform':'牛客','state':'logged_in','owner':owner,'url':self.url}

    def create(self,manual=False):
        value=(self.bridge.open if manual else self.bridge.submit)(self.url,'int main(){}','isolated')
        self.sid=value['sessionId'];self.secret=self.bridge.sessions[self.sid]['capability']
        return value

    def exchange(self,event=None,**body):
        if event is not None:body['event']={'ownerProof':self.proof(),**event}
        return self.bridge.exchange({'sessionId':self.sid,'clientId':self.client,'pageUrl':self.url,**body},self.secret)

    def dispatch(self):
        self.create();self.exchange(claim=True);self.exchange({'status':'ready'})
        answer=self.exchange();self.assertEqual(answer['action'],'submit')
        return answer

    def finish(self,verdict='CE'):
        self.exchange({'status':'submitted','attempted':True})
        return self.exchange({'status':'finished','submissionId':'85470511','verdict':verdict})

    def test_old_protocol_and_session_exports_are_rejected(self):
        for protocol in (None,2,3):
            with self.assertRaises(ServiceError):self.bridge.register_browser({'clientId':str(uuid.uuid4()),'protocol':protocol})
        with self.assertRaises(ServiceError):self.bridge.sync_browser({},'anything')
        with self.assertRaises(ServiceError):self.bridge.browser_queue({'clientId':self.client,'cookies':[]},self.key)
        self.assertIsNone(self.bridge.session_store);self.assertIsNone(self.bridge.runner)

    def test_no_connector_never_launches_a_second_login(self):
        self.now=20
        with patch('webbrowser.open') as opened:
            self.assertEqual(self.create()['status'],'needs_browser')
            with self.assertRaises(ServiceError):ConnectedPreparation(self.bridge,'.',opener=Mock(),waker=lambda:False).check_submission(self.url)
            self.assertEqual(opened.mock_calls,[])

    def test_only_fixed_client_can_claim_and_disconnect_never_switches(self):
        self.dispatch();other,other_key=self.connect('67890')
        with self.assertRaises(ServiceError):self.exchange(clientId=other,claim=True)
        self.now=15;self.queue(other,other_key,'67890')
        self.assertEqual(self.bridge.status(self.sid)['status'],'needs_browser')
        self.assertEqual(self.bridge.sessions[self.sid]['preferredClient'],self.client)
        self.assertEqual(self.queue(other,other_key,'67890')['jobs'],[])

    def test_background_connector_binds_a_waiting_submit_once_without_a_normal_window(self):
        self.now=20;self.create();session=self.bridge.sessions[self.sid]
        self.assertFalse(session['intent']);self.assertIsNone(session['preferredClient'])
        client=str(uuid.uuid4());key=self.bridge.register_browser({'clientId':client,'protocol':4,'backgroundWindows':True})['key']
        body={'clientId':client,'hasWindow':False,'backgroundWindows':True,'identities':{'牛客':self.proof()}}
        jobs=self.bridge.browser_queue(body,key)['jobs']
        self.assertEqual([job['sessionId'] for job in jobs],[self.sid]);self.assertTrue(session['intent'])
        self.assertEqual(session['status'],'loading');self.client,self.key=client,key
        self.exchange({'status':'ready'});self.assertEqual(self.exchange()['action'],'submit')
        self.exchange({'status':'submitted','attempted':True})
        other,other_key=self.connect();self.assertEqual(self.queue(other,other_key)['jobs'],[])
        self.assertEqual(session['preferredClient'],client);self.assertEqual(self.exchange()['action'],'inspect')

    def test_legacy_connector_still_needs_a_normal_window_and_wait_is_bounded(self):
        self.now=20;self.create();session=self.bridge.sessions[self.sid]
        client=str(uuid.uuid4());key=self.bridge.register_browser({'clientId':client,'protocol':4})['key']
        body={'clientId':client,'hasWindow':False,'identities':{'牛客':self.proof()}}
        self.assertEqual(self.bridge.browser_queue(body,key)['jobs'],[]);self.assertIsNone(session['preferredClient'])
        self.now+=21;self.assertEqual(self.bridge.status(self.sid)['status'],'error');self.assertFalse(session['attempted'])
        self.assertEqual(self.bridge.browser_queue({**body,'hasWindow':True},key)['jobs'],[])
        self.assertEqual(session['status'],'error')

    def test_delayed_connector_cannot_bind_another_account_or_rearm_a_dispatch(self):
        self.now=20;self.create();session=self.bridge.sessions[self.sid];original=self.owner
        self.owner=object();client,key=self.connect();self.assertEqual(self.queue(client,key)['jobs'],[])
        self.assertIsNone(session['preferredClient']);self.owner=original
        for field,value in (('dispatchedAt',self.now),('attempted',True)):
            with self.subTest(field=field):
                session.pop('dispatchedAt',None);session['attempted']=False;session[field]=value
                self.assertEqual(self.queue(client,key)['jobs'],[]);self.assertIsNone(session['preferredClient'])

    def test_exact_owner_and_task_page_required_before_any_native_click(self):
        self.create();self.exchange({'status':'ready','ownerProof':self.proof('67890')})
        self.assertEqual(self.bridge.status(self.sid)['status'],'needs_login')
        self.assertEqual(self.exchange()['action'],'inspect')
        self.exchange({'status':'ready'})
        self.assertEqual(self.exchange(pageUrl='https://ac.nowcoder.com/acm/problem/216116')['action'],'inspect')
        self.assertEqual(self.exchange()['action'],'submit')

    def test_first_verified_owner_is_pinned_even_without_a_public_account_binding(self):
        self.bridge.expected_owner=lambda _:None
        self.create();self.exchange({'status':'ready'})
        self.assertEqual(self.bridge.sessions[self.sid]['expectedOwner'],'12345')
        self.exchange();
        with self.assertRaises(ServiceError):self.exchange({'status':'submitted','attempted':True,'ownerProof':self.proof('67890')})

    def test_one_command_after_repeated_or_concurrent_ready_messages(self):
        self.create();self.exchange({'status':'ready'});answers=[]
        threads=[threading.Thread(target=lambda:answers.append(self.exchange())) for _ in range(6)]
        for thread in threads:thread.start()
        for thread in threads:thread.join()
        self.assertEqual(sum(answer.get('action')=='submit' for answer in answers),1)
        self.exchange({'status':'submitted','attempted':True})
        self.exchange({'status':'ready','attempted':False},inspection=True)
        self.assertTrue(self.bridge.sessions[self.sid]['attempted'])
        self.assertEqual(self.exchange()['action'],'inspect')

    def test_captured_team_context_rechecked_without_losing_worker_scope(self):
        token=self.scope.set('team-one')
        try:self.create()
        finally:self.scope.reset(token)
        self.exchange({'status':'ready'})
        self.assertEqual(self.exchange()['action'],'submit')
        with self.assertRaises(ServiceError):self.bridge.submit(self.url,'int main(){}','another-context')

    def test_expired_guard_blocks_dispatch_even_with_a_ready_browser(self):
        self.create();self.exchange({'status':'ready'})
        self.bridge.guard=lambda _url:(_ for _ in ()).throw(ServiceError(403,'Expired'))
        with self.assertRaises(ServiceError):self.exchange()
        self.assertFalse(self.bridge.sessions[self.sid].get('attempted'))

    def test_actual_preclick_ack_rechecks_owner_and_expiry_after_slow_form_wait(self):
        self.dispatch()
        with self.assertRaises(ServiceError):self.exchange({'status':'submitted','attempted':True,'ownerProof':self.proof('67890')})
        self.assertFalse(self.bridge.sessions[self.sid]['attempted'])
        self.bridge.guard=lambda _url:(_ for _ in ()).throw(ServiceError(403,'Expired during native lock'))
        with self.assertRaises(ServiceError):self.exchange({'status':'submitted','attempted':True})
        self.assertFalse(self.bridge.sessions[self.sid]['attempted'])

    def test_lost_query_after_checkpoint_keeps_original_and_accepts_late_wa(self):
        self.dispatch();self.exchange({'status':'submitted','attempted':True})
        self.exchange({'status':'error','message':'network interruption'})
        self.assertEqual(self.bridge.status(self.sid)['status'],'unconfirmed')
        self.assertEqual(self.exchange()['action'],'inspect')
        self.exchange({'status':'judging','submissionId':'85470558'})
        self.exchange({'status':'finished','submissionId':'85470511','verdict':'AC'})
        self.assertEqual(self.saved,[])
        self.exchange({'status':'finished','submissionId':'85470558','verdict':'WA'})
        self.assertEqual(self.saved[0]['verdict'],'WA')

    def test_terminal_ce_saved_once_and_no_close_before_exact_display_ack(self):
        self.dispatch();answer=self.finish()
        self.assertFalse(answer['closeOwned']);self.assertFalse(self.bridge.status(self.sid).get('windowClosed',False))
        self.exchange({'status':'finished','submissionId':'85470511','verdict':'CE'})
        self.assertEqual(len(self.saved),1)
        self.assertTrue(self.bridge.acknowledge(self.sid)['displayAcknowledged'])
        self.assertTrue(self.exchange()['closeOwned'])
        self.exchange(closed=True)
        self.assertTrue(self.bridge.status(self.sid)['windowClosed'])
        self.assertEqual(self.queue()['jobs'],[])

    def test_failed_persistence_and_wrong_or_local_row_never_close_page(self):
        self.dispatch();self.bridge.on_receipt=lambda *_:None;self.finish()
        self.assertFalse(self.bridge.acknowledge(self.sid).get('displayAcknowledged'))
        self.assertFalse(self.exchange().get('closeOwned'))
        self.bridge.on_receipt=lambda *_:{'id':'samples-result','scope':'local','mode':'run','verdict':'CE','finishedAt':'today','message':'local'}
        self.exchange({'status':'finished','submissionId':'85470511','verdict':'CE'})
        self.assertFalse(self.bridge.acknowledge(self.sid).get('displayAcknowledged'))

    def test_manual_page_is_never_closed_and_is_not_requeued(self):
        self.create(manual=True);self.exchange({'status':'loading','attempted':False});self.exchange({'status':'ready'})
        self.assertEqual(self.exchange()['action'],'inspect')
        self.bridge.submit(self.url,'int main(){}','same');self.exchange({'status':'ready'});self.exchange();self.finish()
        self.assertFalse(self.bridge.acknowledge(self.sid).get('displayAcknowledged'))
        answer=self.exchange();self.assertTrue(answer['stop']);self.assertFalse(answer['closeOwned'])
        self.exchange(released=True);self.assertEqual(self.queue()['jobs'],[])

    def test_stale_preclick_inspection_never_rearms_a_dispatched_command(self):
        self.dispatch();self.exchange({'status':'loading','attempted':False},inspection=True)
        self.exchange({'status':'ready'})
        self.assertEqual(self.exchange()['action'],'inspect')
        self.exchange({'status':'loading','attempted':False})
        self.exchange({'status':'ready'})
        self.assertEqual(self.exchange()['action'],'submit')

    def test_login_home_only_navigates_back_after_matching_owner_without_a_post(self):
        self.create();self.exchange({'status':'needs_login','attempted':False})
        answer=self.exchange({'status':'loading','loggedIn':True},pageUrl='https://ac.nowcoder.com/')
        self.assertEqual(answer['navigate'],self.url)
        self.assertFalse(self.bridge.sessions[self.sid]['attempted'])
        wrong=self.exchange({'status':'loading','loggedIn':True,'ownerProof':self.proof('67890')},pageUrl='https://ac.nowcoder.com/')
        self.assertNotIn('navigate',wrong)

    def test_account_switch_rejects_old_capability_and_return_restores_same_task(self):
        self.dispatch();original=self.owner;self.owner=object()
        with self.assertRaises(ServiceError):self.exchange()
        self.owner=original;self.assertEqual(self.exchange()['action'],'inspect')
        self.assertEqual(len(self.bridge.sessions),1)

    def test_startup_metadata_and_refresh_never_create_a_login_tab(self):
        preparation=ConnectedPreparation(self.bridge,'.',opener=Mock())
        self.assertEqual(preparation.action({'action':'startup-logins'})['mode'],'tabs')
        self.assertEqual(preparation.action({'action':'refresh'})['mode'],'tabs')
        self.assertEqual(self.bridge.sessions,{})

    def test_page_read_uses_bounded_chunks_and_no_javascript_rpc(self):
        page=self.bridge.page(self.url,self.owner,'牛客');s=self.bridge.sessions[page.identity];results=[]
        thread=threading.Thread(target=lambda:results.append(page.request('read',timeout=1)));thread.start()
        while not s.get('controlRequest'):time.sleep(.001)
        def exchange(event=None):return self.bridge.exchange({'sessionId':page.identity,'clientId':self.client,'pageUrl':self.url,**({'event':event} if event else {})},s['capability'])
        command=exchange()['context']['controlCommand']
        for index,text in ((1,'second'),(0,'first')):
            exchange({'controlCommand':command,'value':{'identity':self.proof(),'url':self.url,'ready':'complete'},'htmlPart':{'index':index,'total':2,'text':text}})
        thread.join();self.assertEqual(results[0]['html'],'firstsecond')
        with self.assertRaises(ValueError):page.request('evaluate')
        page.close();self.assertTrue(exchange()['closeOwned'])

    def test_page_start_command_is_sent_once_and_preserved_after_uncertain_result(self):
        page=self.bridge.page(self.url,self.owner,'牛客');s=self.bridge.sessions[page.identity]
        s['command']=1;s['controlRequest']={'kind':'virtual','context':{'action':'start'}}
        body={'sessionId':page.identity,'clientId':self.client,'pageUrl':self.url}
        self.assertEqual(self.bridge.exchange(body,s['capability'])['action'],'control')
        self.assertNotIn('action',self.bridge.exchange(body,s['capability']))
        page.close(keep=True);self.assertFalse(self.bridge.exchange(body,s['capability'])['closeOwned'])

    def test_http_legacy_session_endpoint_rejected_without_consuming_secrets(self):
        from backend import Handler
        from http.server import ThreadingHTTPServer
        from urllib.request import Request,urlopen
        from urllib.error import HTTPError
        from browser_bridge import EXTENSION_ID,EXTENSION_ORIGIN
        from types import SimpleNamespace
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.frontend_origins=set();server.store=SimpleNamespace(token='fixture-only');server.browser_bridge=self.bridge
        threading.Thread(target=server.serve_forever,daemon=True).start()
        try:
            request=Request('http://127.0.0.1:'+str(server.server_port)+'/api/browser/session',b'not-json',{'Content-Type':'application/json','Origin':EXTENSION_ORIGIN,'X-TB-Browser-Client':EXTENSION_ID})
            with self.assertRaises(HTTPError) as raised:urlopen(request,timeout=2)
            self.assertEqual(raised.exception.code,410)
            raised.exception.close()
        finally:server.shutdown();server.server_close()

    def test_static_main_checks_fresh_owner_and_deduplicates_vp_commands(self):
        import subprocess
        from test_official_v4 import NODE
        result=subprocess.run([NODE,str(Path(__file__).resolve().parents[1]/'desktop/tests/connected_control.mjs')],text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_frozen_assembled_bundle_opens_the_shipped_hyphen_directory_without_building(self):
        import tempfile
        from browser_extension_bundle import build
        from connected_preparation import connector_bundle_path
        with tempfile.TemporaryDirectory(prefix='tb-v4-frozen-') as temporary:
            package=Path(temporary)/'package';shipped=build(package/'browser-extension')
            before={p.name:p.read_bytes() for p in shipped.iterdir()}
            manifest=json.loads((shipped/'manifest.json').read_text('utf-8'))
            self.assertTrue(all((shipped/name).is_file() for rule in manifest['content_scripts'] for name in rule['js']))
            self.assertFalse((package/'browser_extension').exists())
            opened=[]
            with patch.object(sys,'frozen',True,create=True),patch.object(sys,'executable',str(package/'ToBe.exe')),patch('browser_extension_bundle.build',side_effect=AssertionError('Frozen must not generate source assets')) as generator:
                runtime_root=Path(sys.executable).resolve().parent
                found=connector_bundle_path(runtime_root,package/'state'/'training.sqlite3',18765)
                preparation=ConnectedPreparation(self.bridge,found,opener=opened.append)
                self.assertEqual(preparation.snapshot()['extensionPath'],str(shipped))
                preparation.action({'action':'open-folder'});self.assertEqual(opened,[str(shipped)])
                generator.assert_not_called()
            self.assertEqual(before,{p.name:p.read_bytes() for p in shipped.iterdir()})
            self.assertFalse((package/'state').exists())

    def test_frozen_missing_bundle_fails_closed_without_generating_or_launching(self):
        import tempfile
        from connected_preparation import connector_bundle_path
        with tempfile.TemporaryDirectory(prefix='tb-v4-frozen-missing-') as temporary:
            package=Path(temporary)
            with patch.object(sys,'frozen',True,create=True),patch('browser_extension_bundle.build',side_effect=AssertionError('No frozen fallback')) as generator:
                path=connector_bundle_path(package,package/'state'/'training.sqlite3',18765)
                self.assertEqual(path,package/'browser-extension')
                preparation=ConnectedPreparation(self.bridge,path,opener=Mock())
                with self.assertRaises(ServiceError):preparation.action({'action':'open-folder'})
                preparation.opener.assert_not_called()
                generator.assert_not_called()
            self.assertEqual(list(package.iterdir()),[])


class ConnectedTeamGuardTests(unittest.TestCase):
    import test_training as fixtures
    import test_team_workbench as team_fixtures
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown
    room=team_fixtures.TeamWorkbenchTests.room

    def test_real_training_guard_keeps_team_context_for_dispatch_and_preclick(self):
        import backend
        from types import SimpleNamespace,MethodType
        from team_workbench import authorized,current_authorized_contest
        contest=self.room();self.library.rows[3]['url']=self.library.rows[0]['url']
        server=SimpleNamespace(training=self.service,store=self.library,accounts=None,official_session_lock=threading.RLock(),official_sessions={})
        guard=MethodType(backend.LocalServer.validate_official_url,server)
        bridge=ConnectedBrowserBridge('http://127.0.0.1:12345',guard=guard,current_owner=lambda:server.training,expected_owner=lambda _:'fixture')
        client=str(uuid.uuid4());key=bridge.register_browser({'clientId':client,'protocol':4})['key']
        proof={'platform':'Codeforces','url':self.library.rows[0]['url'],'state':'logged_in','owner':'fixture'}
        bridge.browser_queue({'clientId':client,'hasWindow':True,'identities':{'Codeforces':proof}},key)
        with self.assertRaises(ServiceError):bridge.submit(self.library.rows[0]['url'],'int main(){}','no context')
        with authorized(self.service,contest['id']):value=bridge.submit(self.library.rows[0]['url'],'int main(){}','authorized team')
        s=bridge.sessions[value['sessionId']]
        def exchange(event=None):return bridge.exchange({'sessionId':s['sessionId'],'clientId':client,'pageUrl':s['url'],**({'event':{'ownerProof':proof,**event}} if event else {})},s['capability'])
        self.assertIsNone(current_authorized_contest(self.service))
        with patch.object(self.service,'assert_official_allowed',wraps=self.service.assert_official_allowed) as check:
            exchange({'status':'ready'});self.assertEqual(exchange()['action'],'submit')
            self.assertTrue(exchange({'status':'submitted','attempted':True})['ack'])
            self.assertTrue(all(call.args==('fixture::A',contest['id']) for call in check.call_args_list))
        self.assertIsNone(current_authorized_contest(self.service))


class ConnectedPendingRecoveryTests(unittest.TestCase):
    import test_training as fixtures
    from test_official_pending_recovery import PendingRecoveryTests
    setUp=fixtures.ServiceTests.setUp
    tearDown=fixtures.ServiceTests.tearDown
    pending=PendingRecoveryTests.pending
    restart=PendingRecoveryTests.restart

    def test_logged_out_legacy_page_proves_original_closure_but_new_owner_must_match(self):
        import backend
        from official_recovery import legacy_nowcoder_proof
        from test_official_pending_recovery import OldPage
        original=self.pending();self.restart();record=self.service.official_pending()[0]
        old_page=OldPage(record,lambda page:page.proof.update(ownerMatches=False))
        self.assertIsNone(legacy_nowcoder_proof(old_page,record))
        server=object.__new__(backend.LocalServer);server.training=self.service
        server.official_sessions={};server.official_pending_receipts={};server.official_session_lock=threading.RLock()
        bridge=ConnectedBrowserBridge('http://127.0.0.1:12345',current_owner=lambda:server.training,
            on_pending=server.record_official_pending,on_receipt=server.record_official_receipt,
            legacy_proof=lambda value:legacy_nowcoder_proof(old_page,value,require_current_owner=False))
        server.official_restorer=bridge.restore_pending;server.official_status=bridge.status
        with patch('connected_browser.threading.Thread'):server.begin_official_recovery()
        bridge._prepare_recovery(original['sessionId']);s=bridge.sessions[original['sessionId']]
        self.assertTrue(s['prepared']);self.assertEqual(s['expectedOwner'],'12345')
        client=str(uuid.uuid4());key=bridge.register_browser({'clientId':client,'protocol':4})['key']
        proof={'platform':'牛客','url':original['url'],'state':'logged_in','owner':'67890'}
        bridge.browser_queue({'clientId':client,'hasWindow':True,'identities':{'牛客':proof}},key)
        body={'sessionId':s['sessionId'],'clientId':client,'pageUrl':original['url']}
        event={'status':'finished','submissionId':original['submissionId'],'verdict':'CE','ownerProof':proof}
        bridge.exchange({**body,'event':event},s['capability'])
        self.assertEqual(len(self.service.official_pending()),1);self.assertEqual(self.service.submissions()['submissions'],[])
        event['ownerProof']={**proof,'owner':'12345'}
        bridge.exchange({**body,'event':event},s['capability'])
        rows=self.service.submissions()['submissions'];self.assertEqual([(row['verdict'],row['code']) for row in rows],[('CE',original['code'])])
        self.assertEqual(self.service.official_pending(),[])

    def test_real_sqlite_restart_queries_original_sid_and_preserves_new_draft(self):
        import backend
        original=self.pending(known=True);other=self.pending('900002','other source',known=True)
        self.service.save_draft('fixture::A','current unsent source');self.restart()
        server=object.__new__(backend.LocalServer);server.training=self.service
        server.official_sessions={};server.official_pending_receipts={};server.official_session_lock=threading.RLock()
        bridge=ConnectedBrowserBridge('http://127.0.0.1:12345',current_owner=lambda:server.training,
            on_pending=server.record_official_pending,on_receipt=server.record_official_receipt)
        server.official_restorer=bridge.restore_pending;server.official_status=bridge.status
        with patch('connected_browser.threading.Thread'):server.begin_official_recovery()
        bridge._prepare_recovery(original['sessionId'])
        client=str(uuid.uuid4());key=bridge.register_browser({'clientId':client,'protocol':4})['key']
        proof={'platform':'牛客','url':original['url'],'state':'logged_in','owner':'12345'}
        bridge.browser_queue({'clientId':client,'hasWindow':True,'identities':{'牛客':proof}},key)
        s=bridge.sessions[original['sessionId']]
        body={'sessionId':s['sessionId'],'clientId':client,'pageUrl':original['url']}
        self.assertEqual(bridge.exchange(body,s['capability'])['action'],'inspect')
        self.assertTrue(s['readOnlyRestore']);self.assertFalse(s['intent'])
        bridge.exchange({**body,'event':{'ownerProof':proof,'status':'finished','submissionId':original['submissionId'],'verdict':'CE'}},s['capability'])
        rows=self.service.submissions()['submissions'];self.assertEqual(len(rows),1)
        self.assertEqual((rows[0]['verdict'],rows[0]['code'],rows[0]['submittedAt']),('CE',original['code'],original['acceptedAt']))
        self.assertEqual(self.service.problem('fixture::A')['draft'],'current unsent source')
        self.assertEqual([r['submissionId'] for r in self.service.official_pending()],[other['submissionId']])


if __name__=='__main__':unittest.main()
