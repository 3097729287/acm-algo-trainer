"""Private machine management access; never uploads the testing workspace."""
from __future__ import annotations

import base64
import json
import re
import threading
import time
from urllib.error import HTTPError,URLError
from urllib.request import Request
from urllib.parse import quote

from leaderboard import default_endpoint,service_opener,validate_endpoint
from persistence import load_document,save_document
from training import ServiceError
from translation_config import _crypt


class AdminRanking:
    def __init__(self,state_dir,endpoint=None,crypt=_crypt,opener=None):
        self.endpoint=validate_endpoint(default_endpoint() if endpoint is None else endpoint)
        self.path=state_dir/'admin-ranking-session.json'
        self.credential_path=state_dir/'admin-service-credential.json'
        self.crypt=crypt
        self.opener=opener or service_opener(self.endpoint)
        self.lock=threading.RLock()
        self.session=None
        self.avatar_cache={}
        self.connection_error=''
        self.retry_at=0
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
        headers={'Content-Type':'application/json','Accept':'application/json','User-Agent':'TB admin','X-TB-State-Protocol':'1','X-TB-Chunk-Protocol':'2'}
        if session:headers.update({'X-TB-User':session['account']['userId'],'Authorization':'Bearer '+session['token']})
        request=Request(self.endpoint+path,data=json.dumps(body).encode() if body is not None else None,headers=headers,method=method)
        try:
            maximum=16_065_568 if method=='GET' and path.startswith('/v1/avatars/') else 262144
            with self.opener.open(request,timeout=8) as response:raw=response.read(maximum+1)
            if len(raw)>maximum:raise ValueError()
            value=json.loads(raw)
            if not isinstance(value,dict):raise ValueError()
            return value
        except HTTPError as error:
            if error.code in (401,403):self._forget()
            raise ServiceError(error.code if error.code in (400,401,403,409,429) else 503,
                               {401:'管理员连接已失效',403:'管理员权限不可用',429:'请求过于频繁，请稍后重试'}.get(error.code,'管理员服务请求失败')) from None
        except (URLError,TimeoutError,OSError,ValueError):
            raise ServiceError(503,'管理员服务连接或响应异常') from None

    def _forget(self):
        self.session=None
        self.avatar_cache.clear()
        save_document(self.path,'')

    def snapshot(self):
        with self.lock:
            if self.session and self.session.get('expiresAt',0)<=time.time():self._forget()
            if not self.session and time.monotonic()>=self.retry_at:
                self._connect()
            return {'loginId':'admin','authenticated':self.session is not None,'configured':bool(self.endpoint),
                    **({'error':self.connection_error} if self.connection_error else {})}

    def provision(self,password):
        """Maintenance-only setup, outside public builds and browser APIs."""
        if not isinstance(password,str) or not 8<=len(password)<=128:raise ValueError('Invalid management credential')
        with self.lock:
            value={'endpoint':self.endpoint,'loginId':'admin','password':password}
            save_document(self.credential_path,base64.b64encode(self.crypt(json.dumps(value).encode())).decode('ascii'))
            self.retry_at=0

    def _connect(self):
        try:
            encoded=load_document(self.credential_path,'')
            if not encoded:raise ServiceError(503,'管理员连接尚未配置')
            value=json.loads(self.crypt(base64.b64decode(encoded,validate=True),decrypt=True))
            if value.get('endpoint')!=self.endpoint or value.get('loginId')!='admin':raise ValueError()
            self.login({'password':value['password']})
            self.connection_error=''
        except (ServiceError,ValueError,KeyError,TypeError):
            self.connection_error='管理员服务暂时无法连接'
            self.retry_at=time.monotonic()+5

    def connect(self):
        with self.lock:
            self.retry_at=0
            return self.snapshot()

    def _require_session(self):
        if not self.snapshot()['authenticated']:raise ServiceError(503,self.connection_error or '管理员服务暂时无法连接')

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
            self.connection_error=''
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
                return {'period':period,'entries':[],'self':None,'configured':bool(self.endpoint),'status':'error','isAdmin':False,'notice':self.connection_error}
            value=self._remote('GET','/v1/leaderboard?period='+period,session=self.session)
            if value.get('isAdmin') is not True:
                self._forget()
                raise ServiceError(403,'管理员权限已失效')
            owner=self.session['account']['userId']
            entries=[item for item in value.get('entries',[]) if item.get('userId')!=owner and item.get('isAdmin') is not True]
            return dict(value,entries=entries,self=None,configured=True,status='ready',hasSnapshot=True,socialAvailable=False)

    def avatar(self,user_id,expected_hash):
        import hashlib
        from preferences import validate_avatar
        if (not isinstance(user_id,str) or not re.fullmatch(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}',user_id)
                or not isinstance(expected_hash,str) or not re.fullmatch(r'[0-9a-f]{64}',expected_hash)):
            raise ServiceError(400,'头像查询参数无效')
        with self.lock:
            self._require_session()
            key=(self.session['account']['userId'],user_id,expected_hash)
            if key in self.avatar_cache:return dict(self.avatar_cache[key])
            value=self._remote('GET','/v1/avatars/'+user_id,session=self.session)
            validate_avatar(value.get('avatarData'))
            digest=hashlib.sha256(value['avatarData'].encode()).hexdigest() if value.get('avatarData') else None
            if value.get('avatarHash')!=digest:raise ServiceError(502,'头像校验失败')
            result={'avatarData':value.get('avatarData'),'avatarHash':digest}
            if digest==expected_hash:
                if len(self.avatar_cache)>=100:self.avatar_cache.pop(next(iter(self.avatar_cache)))
                self.avatar_cache[key]=result
                while sum(len(item['avatarData']) for item in self.avatar_cache.values())>32*1024*1024:
                    self.avatar_cache.pop(next(iter(self.avatar_cache)))
            return dict(result)

    def delete(self,body):
        with self.lock:
            self._require_session()
            if (set(body)!={'userId','period','confirmation'} or body.get('period') not in ('daily','weekly','total')
                    or body.get('confirmation')!='delete' or body.get('userId') is not None and not isinstance(body['userId'],str)):
                raise ServiceError(400,'删除范围或确认无效')
            return self._remote('POST','/v1/admin/leaderboard/delete',body,self.session)

    def search_accounts(self,query):
        with self.lock:
            self._require_session()
            if not isinstance(query,str) or not 4<=len(query)<=80 or not re.fullmatch(r'[A-Za-z0-9_-]+',query):
                raise ServiceError(400,'请输入完整登录号或公开 ID')
            value=self._remote('GET','/v1/admin/accounts?q='+quote(query,safe=''),session=self.session)
            entries=value.get('accounts')
            if not isinstance(entries,list) or len(entries)>1:raise ServiceError(503,'管理员服务响应异常')
            result=[]
            for row in entries:
                if (not isinstance(row,dict) or not isinstance(row.get('userId'),str)
                        or not re.fullmatch(r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}',row['userId'],re.I)
                        or not isinstance(row.get('loginId'),str) or not re.fullmatch(r'[a-z0-9_]{4,32}',row['loginId'])
                        or not isinstance(row.get('nickname'),str) or type(row.get('protected')) is not bool):
                    raise ServiceError(503,'管理员服务响应异常')
                # Do not forward arbitrary server fields (especially secrets).
                result.append({key:row.get(key) for key in ('userId','loginId','nickname','createdAt','protected')})
            return {'accounts':result}

    def _account_action(self,body,action):
        with self.lock:
            self._require_session()
            if (not isinstance(body,dict) or set(body)!={'userId','loginId','confirmation'} or body.get('confirmation')!=action
                    or not isinstance(body.get('userId'),str) or not re.fullmatch(r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}',body['userId'],re.I)
                    or not isinstance(body.get('loginId'),str) or not re.fullmatch(r'[a-z0-9_]{4,32}',body['loginId'])):
                raise ServiceError(400,'账号或操作确认无效')
            if body['userId']==self.session['account']['userId'] or body['loginId']=='admin':raise ServiceError(403,'不能修改管理员账号')
            route='delete' if action=='delete-account' else 'reset-password'
            value=self._remote('POST','/v1/admin/accounts/'+route,body,self.session)
            flag='deleted' if action=='delete-account' else 'sessionsRevoked'
            if value.get('ok') is not True or value.get('userId')!=body['userId'] or value.get('loginId')!=body['loginId'] or value.get(flag) is not True:
                raise ServiceError(503,'管理员服务响应异常')
            return {'ok':True,'userId':body['userId'],'loginId':body['loginId'],flag:True}

    def delete_account(self,body):return self._account_action(body,'delete-account')
    def reset_password(self,body):return self._account_action(body,'reset-password')
