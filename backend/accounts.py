"""Registered TB accounts. Passwords are forwarded over TLS and never persisted."""
from __future__ import annotations

import base64
import json
import re
import secrets
import threading
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener

from leaderboard import NoRedirect, validate_endpoint, default_endpoint
from persistence import load_document, save_document
from training import ServiceError
from translation_config import _crypt


class Accounts:
    def __init__(self, server, training_factory, endpoint=None, crypt=_crypt):
        self.server, self.factory, self.crypt = server, training_factory, crypt
        self.lock = threading.RLock()
        self.base = server.training
        self.root = server.state_dir
        self.endpoint = validate_endpoint(endpoint if endpoint is not None else self.base._ranking_profile()['endpoint'] or default_endpoint())
        self.session_path = self.root / 'account-session.json'
        self.registry_path = self.root / 'account-workspaces.json'
        self.registry = load_document(self.registry_path, {})
        self.services = {str(self.base.db_path): self.base}
        self.session = None
        self.saved = None
        self.closed = False
        self.error = ''
        self.last_login = load_document(self.root / 'account-login.json', '')
        encoded = load_document(self.session_path, '')
        if encoded:
            try:
                self.saved = json.loads(crypt(base64.b64decode(encoded, validate=True), decrypt=True))
                if self.saved.get('endpoint') != self.endpoint or self.saved.get('expiresAt', 0) <= time.time():
                    self.saved = None
                    save_document(self.session_path, '')
            except Exception:
                self.saved = None
                self.error = '本机登录凭据无法读取，请重新登录'

    def _remote(self, method, path, body=None, session=None):
        if self.closed:
            raise ServiceError(503, 'TB 正在关闭')
        if not self.endpoint:
            raise ServiceError(503, '账号服务尚未配置，请连接账号服务后重试')
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'User-Agent': 'TB/0.10.4'}
        if session:
            headers.update({'X-TB-User': session['userId'], 'Authorization': 'Bearer ' + session['token']})
        payload = json.dumps(body, ensure_ascii=False).encode('utf-8') if body is not None else None
        try:
            with build_opener(NoRedirect()).open(Request(self.endpoint + path, data=payload, method=method, headers=headers), timeout=8) as response:
                raw = response.read(262145)
            if len(raw) > 262144:
                raise ValueError()
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise ValueError()
            return result
        except HTTPError as issue:
            try:
                message = json.loads(issue.read(4096)).get('error')
            except (ValueError, UnicodeError):
                message = None
            safe = message if isinstance(message, str) and len(message) <= 180 and not any(ord(c) < 32 for c in message) else '账号服务暂时无法完成请求'
            if issue.code == 401 and session and self.session and self.session['token'] == session['token']:
                self.invalidate(session['token'])
            raise ServiceError(issue.code, safe) from None
        except (URLError, TimeoutError, OSError, ValueError):
            raise ServiceError(503, '账号服务连接失败，请检查网络后重试') from None

    def credentials(self, owner):
        # An immutable snapshot avoids taking the account lock under a training
        # lock. Background ranking work can never acquire another user's token.
        current = self.session
        if current and current['userId'] == owner and current['expiresAt'] > time.time():
            return {'user_id': owner, 'auth_token': current['token'], 'endpoint': current['endpoint']}
        return None

    def require(self):
        if self.closed or not self.session or self.session['expiresAt'] <= time.time():
            raise ServiceError(401, '请先登录账号')

    def invalidate(self, token=None):
        # Ignore a late 401 from a session replaced by a password change/login.
        with self.lock:
            if token and (not self.session or self.session['token'] != token):
                return
            self.session = self.saved = None
            save_document(self.session_path, '')
            self.error = '登录已失效，请重新登录'
            self.server.store.token = secrets.token_urlsafe(32)

    def snapshot(self):
        with self.lock:
            if self.session and self.session['expiresAt'] <= time.time():
                self.invalidate()
            if not self.session and self.saved:
                try:
                    result = self._remote('GET', '/v1/accounts/me', session=self.saved)
                    value = {**self.saved, 'account': result['account']}
                    self._activate(value)
                    self.error = ''
                except ServiceError as issue:
                    self.error = issue.message
                    if issue.status == 401:
                        self.invalidate()
            return {'required': True, 'authenticated': bool(self.session), 'token': self.server.store.token,
                    'account': self.session['account'] if self.session else None,
                    'usesOriginalWorkspace': bool(self.session) and self.server.training.db_path == self.base.db_path,
                    'lastLoginId': self.last_login, 'error': self.error if not self.session else ''}

    def _assert_idle(self):
        current = self.server.training
        with current.lock:
            if current.workspace().get('activeContest'):
                raise ServiceError(409, '请先结束正在进行的模拟赛，再退出或切换账号')
            if current.connection.execute('SELECT 1 FROM submissions WHERE finished_at IS NULL LIMIT 1').fetchone():
                raise ServiceError(409, '请等待本地评测结束，再退出或切换账号')
            if current.connection.execute('SELECT 1 FROM official_pending LIMIT 1').fetchone():
                raise ServiceError(409, '请先确认待处理的原站提交结果，再退出或切换账号')
        bridge = getattr(self.server, 'browser_bridge', None)
        if bridge:
            with bridge.lock:
                if any(s.get('status') in {'loading', 'submitted', 'judging', 'unconfirmed'} for s in bridge.sessions.values()):
                    raise ServiceError(409, '请等待原站提交结束，再退出或切换账号')

    def _personal_path(self, owner):
        if str(uuid.UUID(owner)) != owner:
            raise ServiceError(503, '账号响应无效')
        base_owner = self.registry.get('originalOwner')
        original = self.base._ranking_profile()
        if not base_owner and (original['user_id'] == owner or self.registry.get('registeredOwner') == owner):
            base_owner = owner
        if not base_owner and not self.registry.get('registeredOwner'):
            with self.base.lock:
                empty = not any(self.base.connection.execute(f'SELECT 1 FROM {table} LIMIT 1').fetchone()
                                for table in ('training', 'drafts', 'submissions', 'contests', 'goals', 'daily_missions'))
            if empty:
                base_owner = owner
        if base_owner == owner:
            self.registry['originalOwner'] = owner
            save_document(self.registry_path, self.registry)
            return self.base.db_path
        return self.root / 'accounts' / owner / 'tb-personal.sqlite3'

    def _activate(self, value, rotate=True):
        account = value.get('account', {})
        owner = account.get('userId')
        if not isinstance(owner, str) or not isinstance(value.get('token'), str) or not re.fullmatch(r'[A-Za-z0-9_-]{32,200}', value['token']):
            raise ServiceError(503, '账号响应无效')
        if type(value.get('expiresAt')) is not int or value['expiresAt'] <= time.time():
            raise ServiceError(401, '登录已失效，请重新登录')
        candidate = {**value, 'userId': owner, 'endpoint': self.endpoint}
        protected = base64.b64encode(self.crypt(json.dumps(candidate, ensure_ascii=False).encode('utf-8'))).decode('ascii')
        path = self._personal_path(owner)
        service = self.services.get(str(path))
        if service is None:
            service = self.factory(path)
            self.services[str(path)] = service
        service.account_provider = self.credentials
        service.bind_account(account, self.endpoint)
        self.server.training = service
        self.session = candidate
        self.saved = None
        self.last_login = account['loginId']
        save_document(self.root / 'account-login.json', self.last_login)
        save_document(self.session_path, protected)
        if rotate:
            self.server.store.token = secrets.token_urlsafe(32)
        self.error = ''
        service.leaderboard.invalidate()

    def register(self, body):
        with self.lock:
            if self.session:
                raise ServiceError(409, '请先退出当前账号')
            if set(body) != {'loginId', 'nickname', 'password'}:
                raise ServiceError(400, '请填写昵称、登录号和密码')
            legacy = None
            if not self.registry.get('originalOwner') and not self.registry.get('registeredOwner'):
                profile = self.base._ranking_profile()
                legacy = {'userId': profile['user_id'], 'token': self.base.legacy_token()}
            value = self._remote('POST', '/v1/accounts/register', body, legacy)
            if not self.registry.get('originalOwner') and not self.registry.get('registeredOwner'):
                self.registry['registeredOwner'] = value['account']['userId']
                save_document(self.registry_path, self.registry)
            self.last_login = value['account']['loginId']
            save_document(self.root / 'account-login.json', self.last_login)
            return {'registered': True, 'loginId': self.last_login}

    def login(self, body):
        with self.lock:
            if set(body) != {'loginId', 'password'}:
                raise ServiceError(400, '请填写登录号和密码')
            if self.session:
                raise ServiceError(409, '请先退出当前账号')
            value = self._remote('POST', '/v1/accounts/login', body)
            if self._personal_path(value['account']['userId']) != self.server.training.db_path:
                self._assert_idle()
            self._activate(value)
            return self.snapshot()

    def logout(self):
        with self.lock:
            self.require()
            self._assert_idle()
            # A failed revocation does not pretend logout succeeded. Retrying
            # is safe; a session already revoked by another client is also fine.
            try:
                self._remote('POST', '/v1/accounts/logout', {}, self.session)
            except ServiceError as issue:
                if issue.status != 401:
                    raise
            self.invalidate()
            self.error = ''
            bridge = getattr(self.server, 'browser_bridge', None)
            if bridge:
                bridge.close(None)
                with bridge.lock:
                    bridge.clients.clear()
            return self.snapshot()

    def change_password(self, body):
        with self.lock:
            self.require()
            if set(body) != {'oldPassword', 'newPassword'}:
                raise ServiceError(400, '请填写原密码和新密码')
            value = self._remote('POST', '/v1/accounts/password', body, self.session)
            self._activate(value, rotate=False)
            return self.snapshot()

    def rename(self, nickname):
        self.require()
        value = self._remote('PUT', '/v1/profile', {'nickname': nickname}, self.session)
        current = self.session
        self._activate({**current, 'account': {**current['account'], 'nickname': value['nickname'], 'displayName': value['nickname']}}, rotate=False)
        return self.server.training.profile()

    def close(self):
        with self.lock:
            self.closed = True
            self.session = self.saved = None
            services = tuple(self.services.values())
        # Ranking completion may report a 401 through invalidate(), so never
        # hold the account lock while joining its executor.
        for service in services:
            service.close()
