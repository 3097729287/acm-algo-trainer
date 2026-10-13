"""Per-submission capabilities for the user's ordinary browser; no cookie access."""
from __future__ import annotations

import datetime as dt
import secrets
import threading
import time
import uuid
import webbrowser
from urllib.parse import urlencode, urlsplit

from official_bridge import submission_target, LOGIN_HOSTS
from training import ServiceError

EXTENSION_ID = 'blgkmkjbdekeoenepgnajpeafofccbjm'
EXTENSION_ORIGIN = 'chrome-extension://' + EXTENSION_ID
TERMINAL = {'finished', 'error', 'closed'}
STATES = TERMINAL | {'loading', 'needs_browser', 'needs_login', 'needs_verification', 'ready', 'submitted', 'judging', 'unconfirmed'}
VERDICTS = {'AC', 'WA', 'TLE', 'MLE', 'RE', 'CE', 'OLE'}


class BrowserBridge:
    def __init__(self, base_url, guard=None, on_receipt=None, on_pending=None, opener=None, clock=None, session_store=None):
        self.base_url = base_url.rstrip('/')
        self.guard, self.on_receipt, self.on_pending = guard, on_receipt, on_pending
        self.opener, self.clock = opener or webbrowser.open, clock or time.monotonic
        self.sessions = {}
        self.clients = {}
        self.lock = threading.RLock()
        self.session_store, self.runner = session_store, None
        self.client_protocols = {}
        self.sync_client = None
        self.client_seen = {}
        self.client_windows = {}
        self.client_platforms = {}
        self.client_versions = {}
        self.client_login_states = {}

    def register_browser(self, body):
        # The HTTP layer requires the bundled extension's exact browser origin.
        # This capability only exposes jobs already created by a TB submit click.
        client = body.get('clientId')
        if not isinstance(client, str) or len(client) != 36:
            raise ServiceError(400, '浏览器连接标识无效')
        try:
            uuid.UUID(client)
        except ValueError:
            raise ServiceError(400, '浏览器连接标识无效')
        with self.lock:
            self.clients.setdefault(client, secrets.token_urlsafe(32))
            protocol = body.get('protocol', 1)
            self.client_protocols[client] = protocol if isinstance(protocol, int) and protocol in (1, 2, 3) else 1
            version = body.get('extensionVersion', '')
            self.client_versions[client] = version if isinstance(version, str) and len(version) <= 32 else ''
            return {'key': self.clients[client], 'mode': 'silent' if self.session_store else 'tabs'}

    def sync_browser(self, body, capability):
        with self.lock:
            expected = self.clients.get(body.get('clientId'))
            if not expected or not secrets.compare_digest(expected, capability):
                raise ServiceError(403, '浏览器后台连接已失效')
        if self.session_store is None:
            raise ServiceError(404, '未启用登录同步')
        return self.session_store.accept(body)

    def browser_queue(self, body, capability):
        client = body.get('clientId')
        with self.lock:
            expected = self.clients.get(client)
            if not expected or not secrets.compare_digest(expected, capability):
                raise ServiceError(403, '浏览器后台连接已失效')
            self.client_seen[client] = self.clock()
            self.client_windows[client] = body.get('hasWindow', True) is True
            self.client_platforms[client] = {p for p in body.get('platforms', []) if isinstance(p, str) and p in LOGIN_HOSTS} if isinstance(body.get('platforms', []), list) else set()
            states = body.get('loginStates', {})
            if not isinstance(states, dict) or set(states) - LOGIN_HOSTS.keys() or any(s not in ('logged_in', 'logged_out', 'unknown') for s in states.values()):
                raise ServiceError(400, '浏览器登录状态无效')
            self.client_login_states[client] = dict(states)
            refresh = body.get('syncPlatforms', [])
            if not isinstance(refresh, list) or len(refresh) > 4 or any(not isinstance(p, str) or p not in LOGIN_HOSTS for p in refresh):
                raise ServiceError(400, '浏览器登录刷新范围无效')
            sync = []
            if self.session_store:
                if self.client_protocols.get(client, 0) >= 2 and (self.sync_client is None or self.clock() - self.client_seen.get(self.sync_client, -10) > 6):
                    self.sync_client = client
                if client == self.sync_client:
                    for platform in set(refresh):
                        self.session_store.request(platform)
                sync = self.session_store.requests() if client == self.sync_client else []
            jobs = []
            for session in self.sessions.values():
                self._expire(session)
                if self.session_store and session.get('transport') != 'browser':
                    continue
                preferred = session.get('preferredClient')
                if self.session_store and preferred and not session.get('claimed') and session.get('dispatchedAt') is None and self.clock() - self.client_seen.get(preferred, -10) > 6:
                    session['preferredClient'] = self._browser_client(session['platform'])
                    session.pop('browserClient', None)
                if self.session_store and (not self.client_windows[client] or session.get('preferredClient') not in (None, client)):
                    continue
                if session['status'] in TERMINAL or session.get('browserClient') not in (None, client):
                    continue
                # Assign once even when two browser profiles poll concurrently.
                session['browserClient'] = client
                jobs.append({'sessionId': session['sessionId'], 'key': session['capability']})
            # Older protocol-2 connectors already handle tab jobs. New clients
            # can synchronize cookies and process a fallback job in one tick.
            if self.session_store:
                if self.client_protocols.get(client) == 2 and sync:
                    return {'jobs': [], 'mode': 'silent', 'sync': sync}
                return {'jobs': jobs, 'mode': 'hybrid' if jobs else 'silent', 'sync': sync}
            return {'jobs': jobs}

    def _browser_client(self, platform):
        eligible = [client for client, at in self.client_seen.items()
                    if self.clock() - at <= 6 and self.client_windows.get(client)
                    and self.client_protocols.get(client, 0) >= 2]
        return next((client for client in eligible if platform in self.client_platforms.get(client, set())),
                    self.sync_client if self.sync_client in eligible else next(iter(eligible), None))

    def route_to_browser(self, identity, before_click=False):
        """Reuse the browser session before a protected native form can click."""
        with self.lock:
            session = self.sessions[identity]
            client = self._browser_client(session['platform'])
            if not client or session.get('browserTried') or session['platform'] not in ('Codeforces', 'AtCoder') or session.get('attempted') or session.get('submissionId'):
                return False
            if not session.get('intent') and not (before_click and session.get('dispatchedAt') is not None):
                return False
            if session.get('dispatchedAt') is not None and not before_click:
                return False
            session.pop('dispatchedAt', None)
            session.update(transport='browser', preferredClient=client, claimed=False, intent=True,
                           status='loading', preparingAt=self.clock(), routedAt=self.clock(), browserTried=True,
                           message='正在使用浏览器现有登录后台提交 ' + session['platform'] + '。')
            return True

    def _expire(self, session):
        if session['status'] in TERMINAL:
            return
        now = self.clock()
        if self.runner and session.get('transport') == 'browser' and not session.get('claimed') and session.get('dispatchedAt') is None and now - session.get('routedAt', now) > 3:
            # Protocol-2 connectors cannot report whether a browser window
            # exists. If no tab claims the job, keep browser-closed submission
            # working through the native runner without replaying a dispatch.
            session.update(transport='silent', status='loading', preparingAt=now,
                           message='浏览器未接收任务，正在使用后台登录会话。')
            session.pop('browserClient', None)
            self.runner.start(session['sessionId'])
        if session.get('dispatchedAt') is not None and not session.get('submissionId') and now - session['dispatchedAt'] > 45:
            session.update(status='unconfirmed', intent=False,
                           message='暂未确认原站受理，仍在后台查询结果；请先核对原站记录，避免重复提交。')
        elif session.get('claimed') and now - session.get('lastSeen', now) > 90:
            session.update(status='unconfirmed' if session.get('dispatchedAt') is not None else 'error', intent=False,
                           message='浏览器连接已中断，请打开原站核对提交记录后再重试。')
        elif not session.get('claimed') and now - session['createdAt'] > 12:
            session.update(status='needs_browser', message='尚未同步浏览器登录。首次使用请启用最新版 TB 浏览器连接扩展，随后可关闭浏览器静默提交。')
        elif session.get('claimed') and session['status'] == 'loading' and now - session.get('preparingAt', session['createdAt']) > 40:
            session.update(status='error', intent=False, message='原站提交接口准备超时，尚未发送代码。请重试；若原站要求验证，请在浏览器完成。')
        if now - session['createdAt'] > 900:
            session.update(status='error', intent=False,
                           message='等待原站结果超时，请在浏览器核对提交记录。')

    def _open(self, url, code, title, intent):
        from insights import canonical_url
        target = submission_target(url)
        if not isinstance(code, str) or not code.strip() or len(code.encode('utf-8')) > 65536:
            raise ServiceError(400, '请先输入不超过 64 KiB 的待提交代码')
        if self.guard:
            self.guard(url)
        with self.lock:
            for item in self.sessions.values():
                self._expire(item)
            session = next((s for s in self.sessions.values() if s['status'] not in TERMINAL | {'unconfirmed'}
                            and canonical_url(s['originalUrl']) == canonical_url(url)), None)
            if session and intent and (session.get('dispatchedAt') is not None or session.get('intent')):
                raise ServiceError(409, '这道题已有提交正在处理，请先核对本次提交结果。')
            if session and session['code'] != code:
                session.update(status='closed', intent=False)
                session = None
            if session is None:
                if sum(s['status'] not in TERMINAL for s in self.sessions.values()) >= 8:
                    raise ServiceError(409, '已有多个浏览器提交等待处理，请先查看结果。')
                identity = 'official-' + uuid.uuid4().hex
                session = {**target, 'sessionId': identity, 'code': code, 'title': str(title),
                           'status': 'loading', 'message': '正在连接已登录的浏览器。', 'intent': intent,
                           'attempted': False, 'baseline': [], 'baselineKnown': False, 'baselineOwner': '',
                           'capability': secrets.token_urlsafe(32), 'createdAt': self.clock(), 'command': 0}
                self.sessions[identity] = session
            else:
                session.update(intent=intent)
                if intent:
                    session.update(status='loading', message='正在后台准备原站提交。', preparingAt=self.clock())
            session['navigateTo'] = session['loginUrl'] if not intent and session['status'] == 'needs_login' else session['url']
            fragment = urlencode({'session': session['sessionId'], 'key': session['capability']})
        if intent and self.runner:
            # Original-site verification can be tied to the actual browser.
            # Prefer its background tab when it is already running.
            if not (session.get('transport') == 'browser' or self.route_to_browser(session['sessionId'])):
                self.runner.start(session['sessionId'])
        elif not intent:
            # Browser jobs must reveal their own tab. A separate original-site
            # page has a different form/verification token and cannot unblock it.
            direct = self.runner and session.get('transport') != 'browser' and session['status'] != 'needs_browser'
            self.opener(session['navigateTo'] if direct else self.base_url + '/browser-connect.html#' + fragment)
        return self.status(session['sessionId'])

    def submit(self, url, code, title):
        return self._open(url, code, title, True)

    def open(self, url, code, title):
        return self._open(url, code, title, False)

    def status(self, identity):
        with self.lock:
            session = self.sessions.get(identity)
            if not session:
                raise ServiceError(404, '没有找到本次浏览器提交')
            self._expire(session)
            return {key: session[key] for key in ('sessionId', 'platform', 'url', 'status', 'message',
                    'submissionId', 'verdict', 'acceptedAt', 'compiler') if key in session}

    def _authenticate(self, identity, capability):
        session = self.sessions.get(identity)
        if not session or not isinstance(capability, str) or not secrets.compare_digest(session['capability'], capability):
            raise ServiceError(403, '浏览器连接已失效，请从 TB 重新打开')
        return session

    def exchange(self, body, capability):
        """Only the bundled extension can call this route, using this job's secret."""
        with self.lock:
            original = self._authenticate(body.get('sessionId'), capability)['originalUrl']
        # Do not hold the bridge lock while entering training/storage locks.
        if self.guard:
            self.guard(original)
        answer = self._exchange(body, capability)
        self._persist(body.get('sessionId'))
        if answer.get('stop') and self.status(body.get('sessionId'))['status'] not in TERMINAL:
            return {'ack': True}
        return answer

    def _exchange(self, body, capability):
        with self.lock:
            session = self._authenticate(body.get('sessionId'), capability)
            self._expire(session)
            if body.get('claim'):
                session.update(claimed=True, lastSeen=self.clock())
                if session['status'] == 'needs_browser':
                    session['status'] = 'loading'
                mode = 'silent' if self.session_store and session.get('transport') != 'browser' else 'tabs'
                return {'url': session['navigateTo'], 'sessionId': session['sessionId'], 'status': session['status'], 'mode': mode}
            page = urlsplit(str(body.get('pageUrl', '')))
            if page.scheme != 'https' or page.hostname not in LOGIN_HOSTS[session['platform']] or page.port not in (None, 443) or page.username or page.password:
                raise ServiceError(403, '只接受本次竞赛平台的浏览器页面')
            session['lastSeen'] = self.clock()
            value = body.get('event')
            if isinstance(value, dict):
                self._update(session, value)
            if session['status'] in TERMINAL:
                return {'stop': True, 'status': session['status']}
            if isinstance(value, dict):
                return {'ack': True}
            action = 'inspect'
            if session.get('intent') and session['status'] == 'ready' and session.get('dispatchedAt') is None:
                action = 'submit'
                session.update(intent=False, dispatchedAt=self.clock(), status='submitted',
                               message='正在操作原站提交表单，尚未确认受理。')
                session['command'] += 1
            context = {k: session.get(k) for k in ('sessionId', 'platform', 'problem', 'code', 'originalUrl',
                       'attempted', 'baseline', 'baselineKnown', 'baselineOwner', 'submissionId')}
            return {'context': context, 'action': action, 'command': session['command']}

    def _update(self, session, value):
        if session['status'] in TERMINAL or value.get('status') not in STATES:
            return
        status = value['status']
        remote_id = str(value.get('submissionId', session.get('submissionId', '')))
        if status in ('judging', 'finished'):
            if session.get('dispatchedAt') is None or not remote_id.isascii() or not remote_id.isdigit() or int(remote_id) <= 0:
                return
            if session.get('submissionId') and remote_id != session['submissionId']:
                return
            if status == 'finished' and value.get('verdict') not in VERDICTS:
                return
        if session.get('submissionId') and status in ('loading', 'ready', 'submitted'):
            return
        if (status == 'loading' and value.get('attempted') is False
                and session.get('dispatchedAt') is not None and not session.get('attempted')):
            # Verification can expire while the form is being prepared. Only a
            # confirmed pre-click wait may resume the original submit intent.
            session.pop('dispatchedAt', None)
            session['intent'] = True
        if session.get('dispatchedAt') is not None and status in ('ready', 'loading'):
            return
        if status in ('needs_browser', 'needs_login', 'needs_verification', 'error'):
            session['intent'] = False
            if value.get('attempted') is False:
                session.pop('dispatchedAt', None)
                session['attempted'] = False
        for key in ('status', 'message', 'compiler', 'attempted', 'baseline', 'baselineKnown', 'baselineOwner'):
            if key in value:
                item = value[key]
                if key in ('message', 'compiler', 'baselineOwner'):
                    if not isinstance(item, str):
                        continue
                    item = item[:500]
                if key in ('attempted', 'baselineKnown') and not isinstance(item, bool):
                    continue
                if key == 'baseline':
                    if not isinstance(item, list) or len(item) > 1000 or any(not isinstance(v, str) or not v.isascii() or not v.isdigit() for v in item):
                        continue
                session[key] = item
        if status in ('judging', 'finished'):
            session['submissionId'] = remote_id
            session.setdefault('acceptedAt', dt.datetime.now(dt.timezone.utc).isoformat())
        if status == 'finished':
            session['verdict'] = value['verdict']

    def _persist(self, identity):
        with self.lock:
            session = self.sessions[identity]
            snapshot = dict(session)
        if snapshot.get('submissionId') and not snapshot.get('pendingSaved') and self.on_pending:
            if self.on_pending(identity, snapshot) is not None:
                with self.lock:
                    session['pendingSaved'] = True
        if snapshot['status'] == 'finished' and self.on_receipt and not snapshot.get('saved'):
            saved = self.on_receipt(identity, snapshot)
            with self.lock:
                if saved is not False:
                    session['saved'] = True
                    return
                session.update(status='judging', message='结果保存失败，正在重试。')

    def close(self, identity=None):
        # Leaving a workbench does not discard a pending official result.
        return self.status(identity) if identity else {'status': 'ready'}

    def on_closing(self):
        if self.runner:
            self.runner.stop()
        with self.lock:
            for session in self.sessions.values():
                if session['status'] not in TERMINAL:
                    session.update(status='closed', intent=False)
