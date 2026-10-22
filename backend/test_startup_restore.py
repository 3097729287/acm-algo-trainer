"""Startup optimization preserves authentication and account isolation."""
import unittest
from unittest.mock import patch

import test_accounts as fixtures
from account_sync import AccountStateSync


class StartupRestoreTests(unittest.TestCase):
    setUp = fixtures.AccountTests.setUp
    tearDown = fixtures.AccountTests.tearDown
    start = fixtures.AccountTests.start
    stop = fixtures.AccountTests.stop
    call = fixtures.AccountTests.call
    signup = fixtures.AccountTests.signup
    login = fixtures.AccountTests.login

    def test_unchanged_resume_validates_state_once_without_replacing_personal_tables(self):
        self.signup()
        self.assertEqual(self.login()[0],200)
        self.server.training.save_draft('fixture::A','startup draft')
        self.server.accounts.sync_pending(wait=True)
        self.stop()
        self.start()
        calls=[]
        revisions=[]
        original=self.server.accounts._remote
        def remote(method,path,*args,**kwargs):
            calls.append((method,path))
            if method == 'GET' and path == '/v1/accounts/state': revisions.append(kwargs.get('state_revision'))
            return original(method,path,*args,**kwargs)
        with patch.object(self.server.accounts,'_remote',side_effect=remote), patch.object(AccountStateSync,'start'), patch.object(AccountStateSync,'_apply',side_effect=AssertionError('unchanged tables must not be replaced')):
            status,value=self.call('/api/account')
        self.assertEqual(status,200,value)
        self.assertTrue(value['authenticated'])
        self.assertEqual([call for call in calls if call[0]=='GET'],[('GET','/v1/accounts/state')])
        self.assertTrue(revisions[0] > 0)
        self.assertEqual(self.server.training.problem('fixture::A')['draft'],'startup draft')

    def test_revoked_saved_credential_never_exposes_local_workspace(self):
        self.signup()
        self.login()
        self.server.training.save_draft('fixture::A','protected draft')
        self.stop()
        self.start()
        from training import ServiceError
        with patch.object(self.server.accounts,'_remote',side_effect=ServiceError(401,'revoked')):
            status,value=self.call('/api/account')
        self.assertEqual(status,200)
        self.assertFalse(value['authenticated'])
        self.assertEqual(self.call('/api/workspace')[0],401)

    def test_pending_local_draft_resumes_by_revision_and_uploads_before_authentication(self):
        self.signup(); self.login()
        self.server.training.save_draft('fixture::A', 'previously synchronized')
        self.server.accounts.sync_pending(wait=True)
        self.stop(); self.start()
        self.server.training.save_draft('fixture::A', 'pending local draft')
        calls=[]
        original=self.server.accounts._remote
        def remote(method,path,*args,**kwargs):
            answer=original(method,path,*args,**kwargs)
            if path == '/v1/accounts/state':
                calls.append((method,answer.get('unchanged'),kwargs.get('state_revision')))
                self.assertIsNone(self.server.accounts.session)
            return answer
        with patch.object(self.server.accounts,'_remote',side_effect=remote), patch.object(AccountStateSync,'start'):
            status,value=self.call('/api/account')
        self.assertEqual(status,200,value)
        self.assertTrue(value['authenticated'])
        self.assertEqual([item[0] for item in calls],['GET','PUT'])
        self.assertTrue(calls[0][1])
        self.assertGreater(calls[0][2],0)
        cloud=self.server.accounts.state_sync._call('GET','/v1/accounts/state')['state']
        self.assertEqual(cloud['tables']['drafts'][0]['code'],'pending local draft')
        self.assertEqual(self.server.training.problem('fixture::A')['draft'],'pending local draft')

    def test_pending_resume_upload_failure_preserves_draft_and_keeps_authentication_locked(self):
        self.signup(); self.login(); self.stop(); self.start()
        self.server.training.save_draft('fixture::A','unflushed local code')
        original=self.server.accounts._remote
        from training import ServiceError
        def remote(method,path,*args,**kwargs):
            if method == 'PUT' and path == '/v1/accounts/state':
                raise ServiceError(503,'fixture upload unavailable')
            return original(method,path,*args,**kwargs)
        with patch.object(self.server.accounts,'_remote',side_effect=remote), patch.object(AccountStateSync,'start'):
            status,value=self.call('/api/account')
        self.assertEqual(status,200,value)
        self.assertFalse(value['authenticated'])
        self.assertEqual(self.call('/api/workspace')[0],401)
        self.assertEqual(self.server.training.problem('fixture::A')['draft'],'unflushed local code')
        with patch.object(AccountStateSync,'start'):
            self.assertTrue(self.call('/api/account')[1]['authenticated'])
