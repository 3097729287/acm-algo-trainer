"""Independent admin authentication; never uploads the local testing workspace."""
from __future__ import annotations

import base64
import json
import re
import threading
import time
from urllib.error import HTTPError,URLError
from urllib.request import Request

from leaderboard import default_endpoint,service_opener,validate_endpoint
from persistence import load_document,save_document
from training import ServiceError
from translation_config import _crypt


class AdminRanking:
    def __init__(self,state_dir,endpoint=None,crypt=_crypt,opener=None):
        self.endpoint=validate_endpoint(default_endpoint() if endpoint is None else endpoint)
        self.path=state_dir/'admin-ranking-session.json'
        self.crypt=crypt
        self.opener=opener or service_opener(self.endpoint)
        self.lock=threading.RLock()
        self.session=None
        encoded=load_document(self.path,'')
        if encoded:
            try:
                value=json.loads(crypt(base64.b64decode(encoded,validate=True),decrypt=True))
                if (value.get('endpoint')==self.endpoint and type(value.get('expiresAt')) is int and value['expiresAt']>time.time()
                        and value.get('account',{}).get('loginId')=='admin' and value['account'].get('isAdmin') is True
                        and isinstance(value.get('token'),str) and re.fullmatch(r'[A-Za-z0-9_-]{32,200}',value['token'])
                        and isinstance(value['account'].get('userId'),str) and re.fullmatch(r'[A-Za-z0-9_-]{1,100}',value['account']['userId'])):
                    self.session=value
            except Exception:pass  # Another Windows user's DPAPI data is not reusable.

    def _remote(self,method,path,body=None,session=None):
        if not self.endpoint:raise ServiceError(503,'管理员服务未连接')
        headers={'Content-Type':'application/json','Accept':'application/json','User-Agent':'TB admin','X-TB-State-Protocol':'1'}
        if session:headers.update({'X-TB-User':session['account']['userId'],'Authorization':'Bearer '+session['token']})
        request=Request(self.endpoint+path,data=json.dumps(body).encode() if body is not None else None,headers=headers,method=method)
        try:
            with self.opener.open(request,timeout=8) as response:raw=response.read(262145)
            if len(raw)>262144:raise ValueError()
            value=json.loads(raw)
            if not isinstance(value,dict):raise ValueError()
            return value
        except HTTPError as error:
            if error.code in (401,403):self._forget()
            raise ServiceError(error.code if error.code in (400,401,403,409,429) else 503,
                               {401:'admin 登录已失效或密码不正确',403:'admin 账号没有管理员权限',429:'请求过于频繁，请稍后重试'}.get(error.code,'管理员服务请求失败')) from None
        except (URLError,TimeoutError,OSError,ValueError):
            raise ServiceError(503,'管理员服务连接或响应异常') from None

    def _forget(self):
        self.session=None
        save_document(self.path,'')

    def snapshot(self):
        with self.lock:
            if self.session and self.session.get('expiresAt',0)<=time.time():self._forget()
            return {'loginId':'admin','authenticated':self.session is not None,'configured':bool(self.endpoint)}

    def login(self,body):
        with self.lock:
            if set(body)!={'password'} or not isinstance(body['password'],str) or not 8<=len(body['password'])<=128:
                raise ServiceError(400,'请填写 admin 账号密码')
            value=self._remote('POST','/v1/accounts/login',{'loginId':'admin','password':body['password']})
            account=value.get('account',{})
            if (account.get('loginId')!='admin' or account.get('isAdmin') is not True
                    or not isinstance(account.get('userId'),str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',account['userId'])
                    or not isinstance(value.get('token'),str) or not re.fullmatch(r'[A-Za-z0-9_-]{32,200}',value['token'])
                    or type(value.get('expiresAt')) is not int or value['expiresAt']<=time.time()):
                self._forget()
                raise ServiceError(403,'仅已授权的 admin 账号可管理公共排行榜')
            candidate={key:value[key] for key in ('account','token','expiresAt')}
            candidate['endpoint']=self.endpoint
            # Verify the server's management role independently of local UI state.
            check=self._remote('GET','/v1/leaderboard?period=daily',session=candidate)
            if check.get('isAdmin') is not True:
                self._forget()
                raise ServiceError(403,'admin 账号没有排行榜管理权限')
            protected=base64.b64encode(self.crypt(json.dumps(candidate).encode())).decode('ascii')
            save_document(self.path,protected)
            self.session=candidate
            return self.snapshot()

    def logout(self):
        with self.lock:
            try:
                if self.session:self._remote('POST','/v1/accounts/logout',{},self.session)
            finally:self._forget()
            return self.snapshot()

    def rankings(self,period):
        if period not in ('daily','weekly','total'):raise ServiceError(400,'排行榜周期无效')
        with self.lock:
            if not self.snapshot()['authenticated']:
                return {'period':period,'entries':[],'self':None,'configured':False,'status':'unconfigured','isAdmin':False,'notice':'使用 admin 账号登录管理员控制'}
            value=self._remote('GET','/v1/leaderboard?period='+period,session=self.session)
            if value.get('isAdmin') is not True:
                self._forget()
                raise ServiceError(403,'管理员权限已失效')
            return dict(value,configured=True,status='ready',hasSnapshot=True,socialAvailable=False)

    def delete(self,body):
        with self.lock:
            if not self.snapshot()['authenticated']:raise ServiceError(401,'请先登录 admin 账号')
            if (set(body)!={'userId','period','confirmation'} or body.get('period') not in ('daily','weekly','total')
                    or body.get('confirmation')!='delete' or body.get('userId') is not None and not isinstance(body['userId'],str)):
                raise ServiceError(400,'删除范围或确认无效')
            return self._remote('POST','/v1/admin/leaderboard/delete',body,self.session)
