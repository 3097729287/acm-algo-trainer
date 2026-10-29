"""Registered TB accounts. Passwords are forwarded over TLS and never persisted."""
from __future__ import annotations

import base64
from contextlib import closing, contextmanager, nullcontext
import json
import logging
import re
import secrets
import sqlite3
import threading
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request

from leaderboard import service_opener, validate_endpoint, default_endpoint
from persistence import load_document, save_document
from training import ServiceError
from translation_config import _crypt


class AccountConnectionUnavailable(ServiceError):
    """Transport/service outage, distinct from invalid credentials or content."""
    connection_unavailable = True


class Accounts:
    def __init__(self, server, training_factory, endpoint=None, crypt=_crypt):
        self.server, self.factory, self.crypt = server, training_factory, crypt
        self.lock = threading.RLock()
        self.requests = threading.Condition()
        self.active_requests = 0
        self.changing_account = False
        self.waiting_changes = 0
        original = server.training
        self.original_db_path = original.db_path
        self.legacy_owner = original._ranking_profile()['user_id']
        self.legacy_secret = original.legacy_token()
        self.root = server.state_dir
        self.endpoint = validate_endpoint(endpoint if endpoint is not None else original._ranking_profile()['endpoint'] or default_endpoint())
        self.opener = service_opener(self.endpoint)
        self.session_path = self.root / 'account-session.json'
        self.registry_path = self.root / 'account-workspaces.json'
        self.registry = load_document(self.registry_path, {})
        self.services = {str(original.db_path): original}
        self.retired_services = []
        self.retired_syncs = []
        self.session = None
        self.state_sync = None
        self.saved = None
        self.closed = False
        self.closing = False
        self.restore_lock = threading.Lock()
        self.restore_worker = None
        self.restore_retry_at = 0
        self.network_context = threading.local()
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

    @contextmanager
    def request_context(self, changing=False):
        """Allow concurrent work for one account; drain it before switching."""
        with self.requests:
            if changing:
                self.waiting_changes += 1
            try:
                self.requests.wait_for(lambda: not self.changing_account and
                    (self.active_requests == 0 if changing else self.waiting_changes == 0))
                if changing:
                    self.changing_account = True
                else:
                    self.active_requests += 1
            finally:
                if changing:
                    self.waiting_changes -= 1
        try:
            with self.lock if changing else nullcontext():
                yield
        finally:
            with self.requests:
                if changing:
                    self.changing_account = False
                else:
                    self.active_requests -= 1
                self.requests.notify_all()
            # Joining a ranking job under the account writer lock can deadlock
            # with a late 401. Drain retired workspaces only after releasing it.
            self._drain_retired()

    def _drain_retired(self):
        with self.lock:
            services, self.retired_services = self.retired_services, []
            syncs, self.retired_syncs = self.retired_syncs, []
        for sync in syncs:
            sync.close()
        for service in services:
            service.close()

    def _remote(self, method, path, body=None, session=None, *, invalidate=True, maximum=262144, timeout=8, state_revision=None):
        if self.closed:
            raise ServiceError(503, 'ToBe 正在关闭')
        if not self.endpoint:
            raise ServiceError(503, '账号服务尚未配置，请连接账号服务后重试')
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'User-Agent': 'TB/1.0.20', 'X-TB-State-Protocol': '1', 'X-TB-Chunk-Protocol': '2'}
        if session:
            headers.update({'X-TB-User': session['userId'], 'Authorization': 'Bearer ' + session['token']})
        if type(state_revision) is int and state_revision > 0:
            headers['X-TB-State-Revision'] = str(state_revision)
        payload = json.dumps(body, ensure_ascii=False).encode('utf-8') if body is not None else None
        remaining = self.restore_time_remaining()
        if remaining is not None:
            if remaining <= 0:
                raise AccountConnectionUnavailable(503, '账号服务连接超时，本机数据已保留')
            timeout = min(timeout, remaining)
        try:
            with self.opener.open(Request(self.endpoint + path, data=payload, method=method, headers=headers), timeout=timeout) as response:
                raw = response.read(maximum + 1)
            if len(raw) > maximum:
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
            if invalidate and issue.code == 401 and session and self.session and self.session['token'] == session['token']:
                self.invalidate(session['token'])
            error_type = AccountConnectionUnavailable if issue.code in (502, 503, 504) else ServiceError
            raise error_type(issue.code, safe) from None
        except (URLError, TimeoutError, OSError) as issue:
            cause = getattr(issue, 'reason', issue)
            logging.getLogger('tb.accounts').warning('Account connection failed: %s %s', method, type(cause).__name__)
            raise AccountConnectionUnavailable(503, '账号服务连接失败，请检查网络后重试') from None
        except ValueError:
            # A reachable service returning corrupt JSON is not an offline lease.
            raise ServiceError(503, '账号服务响应校验失败，本机数据已保留') from None

    def restore_time_remaining(self):
        deadline = getattr(getattr(self, 'network_context', None), 'deadline', None)
        return max(0, deadline - time.monotonic()) if deadline is not None else None

    @contextmanager
    def _restoration_deadline(self):
        previous = getattr(self.network_context, 'deadline', None)
        self.network_context.deadline = time.monotonic() + 2
        try:
            yield
        finally:
            self.network_context.deadline = previous

    def credentials(self, owner):
        # An immutable snapshot avoids taking the account lock under a training
        # lock. Background ranking work can never acquire another user's token.
        current = self.session
        if (current and current['userId'] == owner and current['expiresAt'] > time.time()
                and not (self.state_sync and self.state_sync.needs_reconnect)):
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
            if self.state_sync:
                self.state_sync.stop.set()
                self.state_sync.wake.set()
            save_document(self.session_path, '')
            self.error = '登录已失效或账号已在另一台电脑登录，请重新登录'
            self.server.store.token = secrets.token_urlsafe(32)

    def snapshot(self, *, background=False, retry=False):
        if background:
            # The login screen must never wait behind cloud I/O or an account
            # writer. Only a fully activated session can expose a workspace.
            with self.restore_lock:
                if (not self.closed and not self.closing and
                        self.server.software_updates.status not in {'ready', 'installing'} and
                        (not self.session and self.saved or self.session and self.session['expiresAt'] <= time.time()) and
                        not (self.restore_worker and self.restore_worker.is_alive()) and
                        (retry or time.monotonic() >= self.restore_retry_at)):
                    self.restore_worker = threading.Thread(target=self._restore, name='tb-account-restore', daemon=True)
                    self.restore_worker.start()
                restoring = bool(self.restore_worker and self.restore_worker.is_alive())
            return self._status(restoring=restoring)
        with self.lock:
            if self.session and self.session['expiresAt'] <= time.time():
                self.invalidate()
            if not self.session and self.saved:
                try:
                    # The authenticated state GET in initialize validates the
                    # saved credential too. Avoid a second serial TLS request;
                    # never expose the workspace before that validation.
                    self._activate(self.saved, allow_offline=True)
                    self.error = ''
                except ServiceError as issue:
                    self.error = issue.message
                    if issue.status == 401:
                        self.invalidate()
            return self._status()

    def _status(self, *, restoring=False):
        current = self.session
        authenticated = bool(current and current['expiresAt'] > time.time() and not self.closed)
        return {'required': True, 'authenticated': authenticated, 'token': self.server.store.token,
                'account': current['account'] if authenticated else None,
                'usesOriginalWorkspace': authenticated and self.server.training.db_path == self.original_db_path,
                'lastLoginId': self.last_login, 'error': self.error if not authenticated else '',
                'restoring': restoring and not authenticated,
                'sync': self.state_sync.snapshot() if authenticated and self.state_sync else None}

    def _restore(self):
        try:
            with self.request_context(changing=True):
                if not self.closed:
                    self.snapshot()
        except Exception as issue:
            # Do not expose remote payloads, credentials or private paths.
            logging.getLogger('tb.accounts').warning('Saved account restoration failed: %s', type(issue).__name__)
            self.error = '登录恢复未完成，本机数据已保留，请重试或使用账号密码登录'
        finally:
            self.restore_retry_at = time.monotonic() + 30

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
        if not base_owner and (self.legacy_owner == owner or self.registry.get('registeredOwner') == owner):
            base_owner = owner
        if not base_owner and not self.registry.get('registeredOwner'):
            # The original workspace need not remain a live service after an
            # account switch. A short read-only check preserves claim rules.
            with closing(sqlite3.connect(self.original_db_path.as_uri() + '?mode=ro', uri=True)) as connection:
                empty = not any(connection.execute(f'SELECT 1 FROM {table} LIMIT 1').fetchone()
                                for table in ('training', 'drafts', 'submissions', 'contests', 'goals', 'daily_missions'))
            if empty:
                base_owner = owner
        if base_owner == owner:
            self.registry['originalOwner'] = owner
            save_document(self.registry_path, self.registry)
            return self.original_db_path
        return self.root / 'accounts' / owner / 'tb-personal.sqlite3'

    def _local_resume_path(self, value):
        """Only a DPAPI-restored, synchronized, same-account workspace qualifies."""
        if value is not self.saved or value.get('endpoint') != self.endpoint:
            return None
        owner = value.get('account', {}).get('userId')
        if self.registry.get('activeOwner') != owner:
            return None
        try:
            if str(uuid.UUID(owner)) != owner or type(value.get('expiresAt')) is not int or value['expiresAt'] <= time.time():
                return None
            path = (self.original_db_path if self.registry.get('originalOwner') == owner else
                    self.root / 'accounts' / owner / 'tb-personal.sqlite3')
            if not path.is_file(): return None
            with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)) as db:
                profile = db.execute('SELECT user_id FROM ranking_profile WHERE singleton=1').fetchone()
                row = db.execute('SELECT value FROM account_sync_meta WHERE id=1').fetchone()
                meta = json.loads(row[0]) if row else {}
            if (not profile or profile[0] != owner or meta.get('owner') != owner
                or meta.get('endpoint') != self.endpoint or type(meta.get('revision')) is not int
                or meta['revision'] <= 0 or not re.fullmatch(r'[a-f0-9]{64}', str(meta.get('syncedHash') or ''))
                or not isinstance(meta.get('baseline'), dict) or not meta.get('lastSyncedAt')):
                return None
            return path
        except (TypeError, ValueError, OSError, sqlite3.Error):
            return None

    def _activate(self, value, rotate=True, allow_offline=False):
        if self.closed or self.closing or self.server.software_updates.status == 'installing':
            raise ServiceError(503, 'ToBe 正在关闭')
        account = value.get('account', {})
        owner = account.get('userId')
        if not isinstance(owner, str) or not isinstance(value.get('token'), str) or not re.fullmatch(r'[A-Za-z0-9_-]{32,200}', value['token']):
            raise ServiceError(503, '账号响应无效')
        if type(value.get('expiresAt')) is not int or value['expiresAt'] <= time.time():
            raise ServiceError(401, '登录已失效，请重新登录')
        candidate = {**value, 'userId': owner, 'endpoint': self.endpoint}
        protected = base64.b64encode(self.crypt(json.dumps(candidate, ensure_ascii=False).encode('utf-8'))).decode('ascii')
        local_path = self._local_resume_path(value) if allow_offline else None
        path = local_path or self._personal_path(owner)
        service = self.services.get(str(path))
        if service is None:
            service = self.factory(path)
            self.services[str(path)] = service
        service.account_provider = self.credentials
        from account_sync import AccountStateSync
        old_sync = self.state_sync
        if self.session and self.session['userId'] == owner and old_sync and old_sync.service is service:
            old_sync.session = candidate
            state_sync = old_sync
        else:
            state_sync = AccountStateSync(self, service, candidate)
            try:
                with self._restoration_deadline() if local_path else nullcontext():
                    state_sync.initialize()
            except ServiceError as issue:
                if not local_path or not getattr(issue, 'connection_unavailable', False):
                    raise
                state_sync.resume_local()
        if self.closed or self.closing or self.server.software_updates.status == 'installing':
            raise ServiceError(503, 'ToBe 正在关闭')
        service.bind_account(account, self.endpoint)
        self.server.training = service
        self.state_sync = state_sync
        self.registry['activeOwner'] = owner
        save_document(self.registry_path, self.registry)
        self.saved = None
        self.last_login = account['loginId']
        save_document(self.root / 'account-login.json', self.last_login)
        save_document(self.session_path, protected)
        if rotate:
            self.server.store.token = secrets.token_urlsafe(32)
        self.error = ''
        # Fresh authentication still requires merging. A saved verified lease
        # may expose only its existing local workspace during a transport outage.
        self.session = candidate
        service.leaderboard.invalidate()
        state_sync.start()
        receipts=getattr(self.server,'official_sync',None)
        if receipts is not None:
            receipts.request_refresh()
        if old_sync and old_sync is not state_sync:
            old_sync.stop.set()
            old_sync.wake.set()
            self.retired_syncs.append(old_sync)
        for key, previous in list(self.services.items()):
            if previous is not service:
                previous.account_provider = lambda owner: None
                self.retired_services.append(previous)
                del self.services[key]

    def register(self, body):
        with self.lock:
            if self.session:
                raise ServiceError(409, '请先退出当前账号')
            if set(body) != {'loginId', 'nickname', 'password'}:
                raise ServiceError(400, '请填写昵称、登录号和密码')
            legacy = None
            if not self.registry.get('originalOwner') and not self.registry.get('registeredOwner'):
                legacy = {'userId': self.legacy_owner, 'token': self.legacy_secret}
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
        self.sync_pending(wait=True)
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

    def close(self,*,wait=True):
        self.closing = True
        self.closed = True
        syncs=list(self.retired_syncs)
        if self.state_sync and self.state_sync not in syncs:syncs.append(self.state_sync)
        # Every edit is already committed locally. Do not start a new cloud
        # upload during exit, especially on a slow or disconnected network.
        for sync in syncs:
            sync.stop.set();sync.wake.set()
        worker = self.restore_worker
        if worker and worker is not threading.current_thread():
            worker.join(timeout=.2)
        for sync in syncs:sync.close()
        def finish():
            # An in-flight restore/sync owns its service until its cancelled
            # response returns. Never close SQLite beneath that operation.
            if worker and worker is not threading.current_thread():worker.join()
            # A restore may have published its sync just before closing was
            # requested. Include it after the restore writer has drained.
            for current in [*self.retired_syncs,self.state_sync]:
                if current is not None and current not in syncs:
                    current.close();syncs.append(current)
            for sync in syncs:
                with sync.operation:pass
            self._drain_retired()
            with self.lock:
                self.session = self.saved = None
                services = tuple(self.services.values())
            for service in services:service.close()
        busy=bool(worker and worker.is_alive())
        for sync in syncs:
            acquired=sync.operation.acquire(blocking=False)
            if acquired:sync.operation.release()
            else:busy=True
        if busy and not wait:
            threading.Thread(target=finish,name='tb-local-close',daemon=True).start()
        else:finish()

    def sync_pending(self, wait=False):
        current = self.state_sync
        if not self.session or current is None or current.session['token'] != self.session['token']:
            return {'status': 'offline', 'pending': False, 'error': '', 'lastSyncedAt': None}
        return current.flush(wait=wait)

    def queue_sync(self):
        current, session = self.state_sync, self.session
        if current and session and current.session['token'] == session['token']:
            current.notify_write()
