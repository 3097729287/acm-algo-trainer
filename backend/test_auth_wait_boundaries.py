"""Real local HTTP fixtures for auth barriers; never production accounts."""
import threading
import time
import unittest
import json
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import patch

import accounts as A
from account_sync import AccountStateSync
from training import ServiceError
import test_accounts as fixtures

class AuthWaitBoundaries(unittest.TestCase):
    setUp=fixtures.AccountTests.setUp;tearDown=fixtures.AccountTests.tearDown
    start=fixtures.AccountTests.start;stop=fixtures.AccountTests.stop;call=fixtures.AccountTests.call
    signup=fixtures.AccountTests.signup;login=fixtures.AccountTests.login

    def test_explicit_registration_is_not_held_by_a_stale_restore_writer(self):
        self.signup();self.login();self.stop();self.start()
        started=threading.Event();release=threading.Event()
        def stalled(sync):started.set();release.wait(5)
        with patch.object(AccountStateSync,'initialize',stalled),patch.object(A,'ACCOUNT_WAIT_SECONDS',.15,create=True):
            self.assertTrue(self.call('/api/account?background=1')[1]['restoring']);self.assertTrue(started.wait(2))
            try:
                with ThreadPoolExecutor(1) as pool:
                    future=pool.submit(self.signup,'account_b','isolated B')
                    try:
                        status,value=future.result(timeout=1)
                        self.assertEqual(status,503,value)
                    finally:release.set()
            finally:release.set();self.server.accounts.restore_worker.join(3)
        self.assertIsNone(self.server.accounts.session,'A cancelled late restore cannot activate the old account')
        self.assertFalse(self.call('/api/account')[1]['authenticated'],'A plain poll cannot restart a superseded identity')

    def test_restore_without_local_sync_metadata_has_a_total_network_budget(self):
        self.signup();self.login();self.stop();self.start();accounts=self.server.accounts
        with self.server.training.lock:self.server.training.connection.execute('DELETE FROM account_sync_meta')
        budgets=[]
        def unavailable(*args,**kwargs):
            budgets.append(accounts.restore_time_remaining())
            raise A.AccountConnectionUnavailable(503,'isolated network unavailable')
        with patch.object(accounts,'_remote',side_effect=unavailable):
            self.call('/api/account?background=1');accounts.restore_worker.join(3)
        self.assertEqual(len(budgets),1)
        self.assertIsNotNone(budgets[0]);self.assertGreater(budgets[0],0);self.assertLessEqual(budgets[0],10)
        self.assertIsNone(accounts.session)

    def test_retired_resource_drain_does_not_block_the_next_account_operation(self):
        accounts=self.server.accounts;started=threading.Event();release=threading.Event()
        def close():started.set();release.wait(3)
        accounts.retired_services.append(SimpleNamespace(close=close))
        begin=time.monotonic()
        try:
            accounts._drain_retired()
            self.assertLess(time.monotonic()-begin,.5)
            self.assertTrue(started.wait(1))
        finally:release.set()

    def test_untrusted_request_cannot_cancel_a_saved_restore(self):
        self.signup();self.login();self.stop();self.start()
        started=threading.Event();release=threading.Event()
        original=AccountStateSync.initialize
        def stalled(sync):
            started.set();release.wait(3);return original(sync)
        with patch.object(AccountStateSync,'initialize',stalled):
            self.call('/api/account?background=1');self.assertTrue(started.wait(2))
            epoch=self.server.accounts.restore_epoch
            try:
                for nickname in ('B', 'B'*32000):
                    status,value=self.call('/api/account/register',{'loginId':'untrusted_b','nickname':nickname,'password':'fixture-password'},token='wrong')
                    self.assertEqual(status,403,value)
                    self.assertIn('会话已失效',value['error'])
                    self.assertEqual(self.server.accounts.restore_epoch,epoch)
            finally:release.set();self.server.accounts.restore_worker.join(4)
        self.assertIsNotNone(self.server.accounts.session)

    def test_rejected_incomplete_body_cannot_hold_an_auth_request_open(self):
        connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=3)
        begin=time.monotonic()
        try:
            connection.putrequest('POST','/api/account/register')
            connection.putheader('X-TB-Token','wrong')
            connection.putheader('Content-Length','64000')
            connection.endheaders()
            connection.send(b'x')  # The rest of this rejected body never arrives.
            response=connection.getresponse()
            self.assertEqual(response.status,403)
            self.assertIn('会话已失效',json.loads(response.read())['error'])
            self.assertLess(time.monotonic()-begin,2)
            self.assertIsNone(self.server.accounts.session)
        finally:
            connection.close()

    def test_verified_login_sync_failure_reconnects_without_replaying_password_post(self):
        self.signup()
        self.server.training.save_draft('fixture::A','private pre-login draft')
        accounts=self.server.accounts
        remote=accounts._remote;calls=[]
        def observed(method,path,*args,**kwargs):
            calls.append((method,path));return remote(method,path,*args,**kwargs)
        with patch.object(accounts,'_remote',side_effect=observed):
            with patch.object(AccountStateSync,'initialize',side_effect=A.AccountConnectionUnavailable(503,'isolated timeout')):
                status,value=self.login()
            self.assertEqual(status,200,value);self.assertFalse(value['authenticated'])
            self.assertIn('尚未同步',value['error']);self.assertIsNone(accounts.session)
            self.assertIsNotNone(accounts.saved);self.assertEqual(self.call('/api/workspace')[0],401)
            # A retry is a credential/state GET, not another password POST.
            self.call('/api/account?background=1&retry=1');accounts.restore_worker.join(5)
        self.assertEqual(calls.count(('POST','/v1/accounts/login')),1)
        self.assertTrue(self.call('/api/account?background=1')[1]['authenticated'])
        self.assertEqual(self.server.training.problem('fixture::A')['draft'],'private pre-login draft')
        from persistence import load_document
        protected=load_document(accounts.session_path,'')
        self.assertNotIn('fixture-password',protected)
        self.assertNotIn(accounts.session['token'],protected)

    def test_protocol_rejection_never_becomes_a_pending_verified_login(self):
        self.signup()
        with patch.object(AccountStateSync,'initialize',side_effect=ServiceError(426,'upgrade required')):
            status,_=self.login()
        self.assertEqual(status,426)
        self.assertIsNone(self.server.accounts.session);self.assertIsNone(self.server.accounts.saved)
        self.assertEqual(self.call('/api/workspace')[0],401)

    def test_total_http_budget_bounds_a_trickling_response(self):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                raw=json.dumps({'message':'x'*80}).encode()
                self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers()
                try:
                    for byte in raw:
                        self.wfile.write(bytes([byte]));self.wfile.flush();time.sleep(.025)
                except (BrokenPipeError,ConnectionResetError,OSError):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True
        worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
        accounts=self.server.accounts
        try:
            with patch.object(accounts,'endpoint',f'http://127.0.0.1:{server.server_port}'):
                begin=time.monotonic()
                with self.assertRaises(A.AccountConnectionUnavailable):accounts._remote('GET','/slow',timeout=.15)
                self.assertLess(time.monotonic()-begin,.65)
        finally:server.shutdown();server.server_close();worker.join(2)

    def test_registration_lost_ack_is_not_replayed_and_reports_an_uncertain_result(self):
        accounts=self.server.accounts
        with patch.object(accounts,'_remote',side_effect=A.AccountConnectionUnavailable(503,'isolated dropped acknowledgement')) as remote:
            status,value=self.signup()
        self.assertEqual(status,503);self.assertIn('先尝试',value['error'])
        self.assertEqual(remote.call_count,1)
        self.assertIsNone(accounts.saved);self.assertIsNone(accounts.session)

    def test_bad_auth_payload_is_a_structured_error_and_does_not_unlock(self):
        for response in ({'ok':True},{'account':{'userId':'not-an-owner','loginId':'account_a'}}):
            with self.subTest(response=response),patch.object(self.server.accounts,'_remote',return_value=response):
                status,value=self.login()
                self.assertEqual(status,503);self.assertIn('校验失败',value['error'])
                self.assertIsNone(self.server.accounts.session)

    def test_new_explicit_account_request_cancels_a_late_first_login(self):
        self.signup()
        started=threading.Event();release=threading.Event()
        def stalled(sync):started.set();release.wait(5)
        with patch.object(AccountStateSync,'initialize',stalled),patch.object(A,'ACCOUNT_WAIT_SECONDS',.15):
            with ThreadPoolExecutor(2) as pool:
                old=pool.submit(self.login)
                try:
                    self.assertTrue(started.wait(2))
                    self.assertEqual(self.signup('account_b','B')[0],503)
                finally:release.set()
                self.assertEqual(old.result(timeout=2)[0],503)
        self.assertIsNone(self.server.accounts.session)
        self.assertIsNone(self.server.accounts.saved)

    def test_cas_retry_does_not_replace_a_draft_saved_during_the_remote_get(self):
        with patch.object(AccountStateSync,'start'):
            self.signup();self.login()
        sync=self.server.accounts.state_sync
        service=self.server.training
        service.save_draft('fixture::A','first synchronized version');sync.flush()
        remote=sync._call('GET','/v1/accounts/state')
        remote['state']['tables']['account_preferences'].append({'key':'remote-preserve','value':'true','updated_at':'2026-10-29T12:00:00Z'})
        sync._call('PUT','/v1/accounts/state',{'revision':remote['revision'],'state':remote['state']})
        service.save_draft('fixture::A','local version before reconnect')
        with self.assertRaises(ServiceError) as caught:sync.flush()
        self.assertEqual(caught.exception.status,409)
        self.assertTrue(sync.needs_reconnect);self.assertTrue(sync.snapshot()['recoverable'])
        self.assertEqual(sync.snapshot()['attention'],'')
        # Force real object downloads after initialize captures the local
        # journal; negotiate's root GET itself precedes that capture.
        with service.lock:service.connection.execute('DELETE FROM account_sync_objects')
        started=threading.Event();release=threading.Event()
        original=self.server.accounts._remote
        def held(method,path,*args,**kwargs):
            if method=='GET' and path.startswith('/v2/accounts/state/objects/'):started.set();release.wait(5)
            return original(method,path,*args,**kwargs)
        with patch.object(self.server.accounts,'_remote',side_effect=held),ThreadPoolExecutor(1) as pool:
            pending=pool.submit(sync.flush)
            try:
                self.assertTrue(started.wait(2))
                service.save_draft('fixture::A','newest draft typed while downloading')
            finally:release.set()
            # The held request is released above; allow the real loopback object
            # downloads to finish on slower runners before asserting the 409.
            with self.assertRaises(ServiceError) as caught:pending.result(timeout=10)
            self.assertEqual(caught.exception.status,409)
        self.assertEqual(service.problem('fixture::A')['draft'],'newest draft typed while downloading')
        sync.flush()
        self.assertEqual(service.problem('fixture::A')['draft'],'newest draft typed while downloading')
        self.assertEqual(service.connection.execute("SELECT value FROM account_preferences WHERE key='remote-preserve'").fetchone()[0],'true')
        cloud=sync._call('GET','/v1/accounts/state')['state']
        self.assertEqual(cloud['tables']['drafts'][0]['code'],'newest draft typed while downloading')

    def test_a_draft_written_during_capture_stays_pending_until_its_own_upload(self):
        with patch.object(AccountStateSync,'start'):
            self.signup();self.login()
        sync=self.server.accounts.state_sync;service=self.server.training
        service.save_draft('fixture::A','snapshot before concurrent edit')
        original=sync.chunks.canonicalize;changed=False
        def concurrent(state):
            nonlocal changed
            value=original(state)
            if not changed:
                changed=True;service.save_draft('fixture::A','new code after snapshot capture')
            return value
        with patch.object(sync.chunks,'canonicalize',side_effect=concurrent):answer=sync.flush()
        self.assertTrue(answer['pending'],'A newer edit must not be acknowledged by the older upload')
        self.assertEqual(service.problem('fixture::A')['draft'],'new code after snapshot capture')
        sync.flush()
        cloud=sync._call('GET','/v1/accounts/state')['state']
        self.assertEqual(cloud['tables']['drafts'][0]['code'],'new code after snapshot capture')

    def test_background_errors_back_off_without_replaying_authentication(self):
        with patch.object(AccountStateSync,'start'):
            self.signup();self.login()
        sync=self.server.accounts.state_sync;clock=[0.0];calls=[]
        class Wake:
            def wait(self,seconds):clock[0]+=seconds
            def clear(self):pass
        class Stop:
            def is_set(self):return clock[0]>=20
        def failed():
            calls.append(clock[0]);raise A.AccountConnectionUnavailable(503,'isolated network unavailable')
        sync.pending=True
        with patch.object(sync,'wake',Wake()),patch.object(sync,'stop',Stop()),patch.object(sync,'flush',side_effect=failed),patch('account_sync.time.monotonic',side_effect=lambda:clock[0]):
            sync._loop()
        self.assertGreaterEqual(len(calls),3);self.assertLessEqual(len(calls),4)
        gaps=[b-a for a,b in zip(calls,calls[1:])]
        self.assertTrue(all(later>earlier for earlier,later in zip(gaps,gaps[1:])),gaps)
        self.assertTrue(sync.snapshot()['recoverable']);self.assertEqual(sync.snapshot()['attention'],'')

    def test_fast_close_does_not_wait_for_an_unpublished_login_writer(self):
        accounts=self.server.accounts;started=threading.Event();release=threading.Event()
        def writer():
            with accounts.lock:started.set();release.wait(3)
        worker=threading.Thread(target=writer);worker.start();self.assertTrue(started.wait(2))
        try:
            begin=time.monotonic();accounts.close(wait=False)
            self.assertLess(time.monotonic()-begin,.5)
            with self.assertRaises(ServiceError):accounts._check_account_operation()
        finally:release.set();worker.join(3)

if __name__=='__main__':unittest.main()
