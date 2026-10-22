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


class UserEditionBoundaryTests(unittest.TestCase):
    setUp=fixtures.HTTPTests.setUp
    tearDown=fixtures.HTTPTests.tearDown
    request=fixtures.HTTPTests.request

    def test_management_routes_are_unavailable_in_the_user_edition(self):
        self.assertEqual(self.request('GET','/api/admin/session')[0],404)
        self.assertEqual(self.request('POST','/api/admin/session',{'password':'fixture-only-password'})[0],404)
        self.assertEqual(self.request('POST','/api/leaderboard/admin/delete',{'userId':None,'period':'daily','confirmation':'delete'})[0],403)
        self.assertFalse(self.request('GET','/api/leaderboard')[1].get('isAdmin',False))
