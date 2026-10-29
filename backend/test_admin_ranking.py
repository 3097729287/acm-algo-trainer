import io
import json
from pathlib import Path
import tempfile
import time
import unittest
from urllib.error import HTTPError
from admin_ranking import AdminRanking
from persistence import load_document
from training import ServiceError
import test_training as fixtures


class Opener:
    def __init__(self):self.calls=[];self.is_admin=True;self.login_id='admin';self.reject=False
    def open(self,request,timeout):
        self.calls.append((request.full_url,request.method,json.loads(request.data) if request.data else None,dict(request.header_items())))
        if self.reject:raise HTTPError(request.full_url,403,'denied',{},None)
        if request.full_url.endswith('/login'):
            value={'account':{'userId':'admin-fixture','loginId':self.login_id,'isAdmin':self.is_admin},'token':'fixture-token-'+'x'*40,'expiresAt':int(time.time())+3600}
        elif 'leaderboard?' in request.full_url:value={'isAdmin':self.is_admin,'period':'daily','entries':[]}
        elif request.full_url.endswith('/delete'):value={'removed':1}
        else:value={'ok':True}
        return io.BytesIO(json.dumps(value).encode())


class AdminRankingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.opener=Opener()
        self.crypt=lambda value,decrypt=False:value[::-1]
        self.service=AdminRanking(self.root,endpoint='http://127.0.0.1:12345',crypt=self.crypt,opener=self.opener)
    def tearDown(self):self.temp.cleanup()
    def login(self):return self.service.login({'password':'fixture-only-password'})

    def test_admin_identity_role_and_secret_persistence_are_independent(self):
        self.assertFalse(self.service.snapshot()['authenticated'])
        self.assertTrue(self.login()['authenticated'])
        self.assertEqual(self.opener.calls[0][2],{'loginId':'admin','password':'fixture-only-password'})
        self.assertEqual(self.opener.calls[0][3]['X-tb-chunk-protocol'],'2')
        encoded=load_document(self.service.path,'')
        self.assertNotIn('fixture-only-password',encoded)
        self.assertNotIn('fixture-token',encoded)
        restored=AdminRanking(self.root,endpoint=self.service.endpoint,crypt=self.crypt,opener=self.opener)
        self.assertTrue(restored.snapshot()['authenticated'])
        self.assertTrue(restored.rankings('daily')['isAdmin'])
        self.assertTrue(all(item[0].endswith('/v1/accounts/login') or '/v1/leaderboard?' in item[0] for item in self.opener.calls))

    def test_an_admin_display_name_cannot_grant_a_role(self):
        self.opener.is_admin=False
        with self.assertRaises(ServiceError):self.login()
        self.assertFalse(self.service.snapshot()['authenticated'])
        self.opener.is_admin=True;self.opener.login_id='another-admin'
        with self.assertRaises(ServiceError):self.login()
        self.assertFalse(self.service.snapshot()['authenticated'])

    def test_destructive_requests_require_authenticated_admin_and_explicit_scope(self):
        body={'userId':None,'period':'weekly','confirmation':'delete'}
        with self.assertRaises(ServiceError):self.service.delete(body)
        self.login()
        with self.assertRaises(ServiceError):self.service.delete(dict(body,confirmation=''))
        self.assertEqual(self.service.delete(body),{'removed':1})
        headers=self.opener.calls[-1][3]
        self.assertEqual(headers['X-tb-user'],'admin-fixture')
        self.assertTrue(headers['Authorization'].startswith('Bearer fixture-token'))

    def test_revocation_and_logout_clear_persisted_management_sessions(self):
        self.login();self.opener.reject=True
        with self.assertRaises(ServiceError):self.service.rankings('daily')
        self.assertFalse(self.service.snapshot()['authenticated'])
        self.assertEqual(load_document(self.service.path,''),'')
        self.opener.reject=False;self.login();self.service.logout()
        self.assertFalse(self.service.snapshot()['authenticated'])

    def test_logout_clears_local_management_credentials_when_remote_is_unavailable(self):
        self.login()
        class Offline:
            def open(self,*args,**kwargs):raise TimeoutError()
        self.service.opener=Offline()
        with self.assertRaises(ServiceError):self.service.logout()
        self.assertFalse(self.service.snapshot()['authenticated'])
        self.assertEqual(load_document(self.service.path,''),'')

    def test_account_management_uses_authenticated_scoped_calls_and_never_forwards_secret_fields(self):
        target={'userId':'11111111-1111-4111-8111-111111111111','loginId':'fixture_user','nickname':'fixture','createdAt':'2026-10-29','protected':False}
        delegate=self.opener.open
        def opener(request,timeout):
            if '/v1/admin/accounts' not in request.full_url:return delegate(request,timeout)
            self.opener.calls.append((request.full_url,request.method,json.loads(request.data) if request.data else None,dict(request.header_items())))
            if request.method=='GET':value={'accounts':[{**target,'password_hash':'forbidden-fixture-field','password':'forbidden-fixture-field'}]}
            else:value={'ok':True,'userId':target['userId'],'loginId':target['loginId'],('deleted' if request.full_url.endswith('/delete') else 'sessionsRevoked'):True,'password':'forbidden-fixture-field'}
            return io.BytesIO(json.dumps(value).encode())
        self.opener.open=opener
        with self.assertRaises(ServiceError):self.service.search_accounts('fixture_user')
        self.login()
        result=self.service.search_accounts('fixture_user')
        self.assertEqual(result,{'accounts':[target]})
        self.assertNotIn('password',json.dumps(result))
        for method,action,flag in [(self.service.delete_account,'delete-account','deleted'),(self.service.reset_password,'reset-password','sessionsRevoked')]:
            body={key:target[key] for key in ('userId','loginId')};body['confirmation']=action
            self.assertTrue(method(body)[flag])
            with self.assertRaises(ServiceError):method(dict(body,confirmation=''))
            with self.assertRaises(ServiceError):method(dict(body,loginId='admin'))
        self.assertTrue(all('Authorization' in call[3] for call in self.opener.calls if '/v1/admin/accounts' in call[0]))


class UserEditionBoundaryTests(unittest.TestCase):
    setUp=fixtures.HTTPTests.setUp
    tearDown=fixtures.HTTPTests.tearDown
    request=fixtures.HTTPTests.request

    def test_management_routes_are_unavailable_in_the_user_edition(self):
        self.assertEqual(self.request('GET','/api/admin/session')[0],404)
        self.assertEqual(self.request('POST','/api/admin/session',{'password':'fixture-only-password'})[0],404)
        self.assertEqual(self.request('POST','/api/leaderboard/admin/delete',{'userId':None,'period':'daily','confirmation':'delete'})[0],403)
        self.assertFalse(self.request('GET','/api/leaderboard')[1].get('isAdmin',False))
        self.assertEqual(self.request('GET','/api/admin/accounts?q=fixture_user')[0],404)
        for path in ('delete','reset-password'):
            self.assertEqual(self.request('POST','/api/admin/accounts/'+path,{'userId':'11111111-1111-4111-8111-111111111111','loginId':'fixture_user','confirmation':'delete-account'})[0],404)


class AdminAccountRoutingTests(unittest.TestCase):
    setUp=fixtures.HTTPTests.setUp
    tearDown=fixtures.HTTPTests.tearDown
    request=fixtures.HTTPTests.request

    def test_private_routes_forward_exact_target_and_keep_local_write_token_guard(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        self.server.admin_mode=True
        self.server.admin_rankings=SimpleNamespace(search_accounts=Mock(return_value={'accounts':[]}),
            delete_account=Mock(return_value={'ok':True,'deleted':True}),reset_password=Mock(return_value={'ok':True,'sessionsRevoked':True}))
        self.assertEqual(self.request('GET','/api/admin/accounts?q=fixture_user'),(200,{'accounts':[]}))
        self.server.admin_rankings.search_accounts.assert_called_once_with('fixture_user')
        body={'userId':'11111111-1111-4111-8111-111111111111','loginId':'fixture_user','confirmation':'delete-account'}
        self.assertEqual(self.request('POST','/api/admin/accounts/delete',body,token='wrong')[0],403)
        self.server.admin_rankings.delete_account.assert_not_called()
        self.assertEqual(self.request('POST','/api/admin/accounts/delete',body)[0],200)
        self.server.admin_rankings.delete_account.assert_called_once_with(body)
        body={**body,'confirmation':'reset-password'}
        self.assertEqual(self.request('POST','/api/admin/accounts/reset-password',body)[0],200)
        self.server.admin_rankings.reset_password.assert_called_once_with(body)
