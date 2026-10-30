"""Visible original-site forms in an isolated Edge/Chrome profile, no extension.

The browser owns login, CSRF and verification. One explicit TB intent may click
one native submit control. The same adapter observes only that attempt's receipt.
No cookies are exported or copied from a user's everyday browser profile.
"""
from __future__ import annotations

import datetime as dt
import json
import queue
import logging
import os
from pathlib import Path
import socket
import subprocess
import threading
import time
import uuid
from urllib.parse import urlsplit
from urllib.request import build_opener, ProxyHandler

from official_bridge import LOGIN_HOSTS, page_source, submission_target
from training import ServiceError


def browsers():
    roots = [Path(os.environ.get(key, 'C:/')) for key in ('PROGRAMFILES(X86)', 'PROGRAMFILES', 'LOCALAPPDATA')]
    return {name: next((root / relative for root in roots if (root / relative).is_file()), None)
            for name, relative in (('edge', 'Microsoft/Edge/Application/msedge.exe'),
                                   ('chrome', 'Google/Chrome/Application/chrome.exe'))}


class BrowserProcess:
    def __init__(self, profile):
        from persistence import load_document
        self.root = Path(profile).resolve()
        self.preference = self.root.parent / 'managed-browser.json'
        self.preferred = load_document(self.preference, 'edge')
        if self.preferred not in ('edge', 'chrome'):
            self.preferred = 'edge'
        # Retain legacy profile files. A new interactive profile avoids
        # reattaching to a still-open browser launched with the old port-zero
        # flags; existing encrypted first-party login memory is restored below.
        self.profile = self.root / ('interactive-' + self.preferred)
        self.lock = threading.Lock()
        self.process = None
        self.port = None
        self.memory_endpoint = None
        self.bootstrap_targets = set()
        self.opener = build_opener(ProxyHandler({}))

    def request(self, path, method='GET'):
        from urllib.request import Request
        with self.opener.open(Request(f'http://127.0.0.1:{self.port}{path}', method=method), timeout=3) as reply:
            return json.loads(reply.read(2_000_000))

    def _memory(self, version, restore=False):
        endpoint = version.get('webSocketDebuggerUrl')
        if not endpoint or endpoint == self.memory_endpoint:
            return
        from browser_login_memory import BrowserLoginMemory
        memory = BrowserLoginMemory(self.root.parent, self.preferred)
        page = DevToolsPage(endpoint, lambda *_: None)
        if restore:
            memory.restore(page)
        self.memory_endpoint = endpoint
        def remember():
            try:
                while True:
                    memory.capture(page)
                    time.sleep(1)
            except Exception:
                pass
            finally:
                page.close()
                if self.memory_endpoint == endpoint:
                    self.memory_endpoint = None
        threading.Thread(target=remember, name='tb-remember-login', daemon=True).start()

    def _active(self, active):
        lines = active.read_text().splitlines()
        self.port = int(lines[0])
        version = self.request('/json/version')
        # An old ephemeral port can be reused by an unrelated browser process.
        if len(lines) < 2 or urlsplit(version.get('webSocketDebuggerUrl', '')).path != lines[1]:
            raise ValueError('Browser profile no longer owns this endpoint')
        return version

    def _recover(self, executable, active):
        from browser_endpoint import candidates
        for pid, port in candidates(self.profile, executable):
            try:
                self.port=port
                version=self.request('/json/version')
                endpoint=urlsplit(version['webSocketDebuggerUrl'])
                if endpoint.hostname not in ('127.0.0.1','localhost') or endpoint.port!=port:continue
                page=DevToolsPage(version['webSocketDebuggerUrl'],lambda *_:None)
                try:owned=any(item.get('type')=='browser' and item.get('id')==pid for item in page.call('SystemInfo.getProcessInfo')['processInfo'])
                finally:page.close()
                if not owned:continue
                active.write_text(str(port)+'\n'+endpoint.path,encoding='utf-8')
                self._memory(version)
                return True
            except (OSError,ValueError,KeyError,IndexError):pass
        self.port=None
        return False

    def ensure(self, browser=None, *, background=False):
        with self.lock:
            browser = browser or self.preferred
            if browser != self.preferred:
                self.preferred, self.port = browser, None
                self.profile = self.root / ('interactive-' + browser)
            if self.port:
                try:
                    version = self._active(self.profile / 'DevToolsActivePort')
                    self._memory(version)
                    return
                except (OSError, ValueError):
                    self.port = None
            executable = browsers().get(browser)
            if not executable:
                available = [(name, path) for name, path in browsers().items() if path]
                if available:
                    self.preferred, executable = available[0]
                    self.profile = self.root / ('interactive-' + self.preferred)
            if not executable:
                raise ServiceError(503, '未找到 Microsoft Edge 或 Google Chrome，请安装后重试')
            self.profile.mkdir(parents=True, exist_ok=True)
            from persistence import save_document
            save_document(self.preference, self.preferred)
            active = self.profile / 'DevToolsActivePort'
            # Reattach only to this dedicated profile, never the default one.
            if active.is_file():
                try:
                    version = self._active(active)
                    self._memory(version)
                    return
                except (OSError, ValueError, IndexError):
                    self.port = None
                    active.unlink(missing_ok=True)
            if self._recover(executable,active):
                return
            # Port zero enables Chromium's automation mode. Use an ordinary
            # visible browser with a loopback port and verify its process
            # before saving the endpoint for later profile-owned reattachment.
            with socket.socket() as reservation:
                reservation.bind(('127.0.0.1', 0))
                self.port = reservation.getsockname()[1]
            startup = ['--no-startup-window'] if background else ['--new-window', 'about:blank']
            self.process = subprocess.Popen([str(executable), '--user-data-dir=' + str(self.profile),
                '--remote-debugging-port=' + str(self.port), '--remote-debugging-address=127.0.0.1',
                '--no-first-run', '--no-default-browser-check', '--disable-background-mode', *startup],
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            deadline = time.monotonic() + 12
            recovered_launcher=False
            while time.monotonic() < deadline:
                if not recovered_launcher and self.process.poll() is not None:
                    recovered_launcher=True
                    if self._recover(executable,active):return
                try:
                    version = self.request('/json/version')
                    endpoint = urlsplit(version['webSocketDebuggerUrl'])
                    if endpoint.hostname not in ('127.0.0.1', 'localhost') or endpoint.port != self.port:
                        raise ValueError('Browser endpoint is not owned by this launch')
                    inspector = DevToolsPage(version['webSocketDebuggerUrl'], lambda *_:None)
                    try:
                        owned = any(item.get('type') == 'browser' and item.get('id') == self.process.pid
                                    for item in inspector.call('SystemInfo.getProcessInfo')['processInfo'])
                    finally:
                        inspector.close()
                    if owned:
                        active.write_text(str(self.port) + '\n' + endpoint.path, encoding='utf-8')
                        self._memory(version, restore=True)
                        self.bootstrap_targets = {item['id'] for item in self.request('/json/list') if item.get('type') == 'page' and item.get('url') == 'about:blank'}
                        return
                except (OSError, ValueError, IndexError):
                    pass
                time.sleep(.1)
            self.port = None
            raise ServiceError(503, '浏览器尚未启动，请检查弹出的浏览器窗口后重试')

    def close_page(self, identity):
        version=self.request('/json/version')
        page=DevToolsPage(version['webSocketDebuggerUrl'],lambda *_:None)
        try:
            return page.call('Target.closeTarget',{'targetId':identity}).get('success',False)
        finally:
            page.close()

    def new_submission_page(self):
        # Each submission owns one window; never close a login or unrelated tab.
        self.ensure(background=True)
        version=self.request('/json/version')
        page=DevToolsPage(version['webSocketDebuggerUrl'],lambda *_:None)
        try:
            target=page.call('Target.createTarget',{'url':'about:blank','newWindow':True,'background':True})['targetId']
            for blank in self.bootstrap_targets:
                page.call('Target.closeTarget',{'targetId':blank})
            self.bootstrap_targets.clear()
            return next(item for item in self.request('/json/list') if item.get('id')==target)
        finally:
            page.close()

    def new_probe_page(self, url):
        """Create an invisible, disposable target in the managed profile.

        Older Chromium builds without hidden targets simply defer the check;
        a background tab or minimized window still causes a visible flash.
        """
        self.ensure(background=True)
        protocol=self.request('/json/protocol')
        command=next((command for domain in protocol.get('domains',[]) if domain.get('domain')=='Target'
                      for command in domain.get('commands',[]) if command.get('name')=='createTarget'),{})
        if not any(p.get('name')=='hidden' for p in command.get('parameters',[])):
            return None
        version=self.request('/json/version')
        page=DevToolsPage(version['webSocketDebuggerUrl'],lambda *_:None)
        try:
            identity=page.call('Target.createTarget',{'url':url,'hidden':True,'background':True})['targetId']
            return {'id':identity,'url':url,'webSocketDebuggerUrl':f'ws://127.0.0.1:{self.port}/devtools/page/{identity}', '_controller':page}
        except BaseException:
            page.close()
            raise

    def new_page(self, url='about:blank', browser=None):
        from urllib.parse import quote
        self.ensure(browser)
        return self.request('/json/new?' + quote(url, safe=''), 'PUT')


class DevToolsPage:
    def __init__(self, endpoint, on_event):
        import websocket
        parsed = urlsplit(endpoint)
        if parsed.scheme != 'ws' or parsed.hostname not in ('127.0.0.1', 'localhost'):
            raise ValueError('Browser control must remain on loopback')
        self.socket = websocket.create_connection(endpoint, timeout=2, suppress_origin=True,
                                                   http_no_proxy=['127.0.0.1', 'localhost'])
        self.sequence = 0
        self.on_event = on_event
        self.lock = threading.Lock()
        self.pending = {}
        self.events = queue.Queue()
        self.closed = threading.Event()
        self.wake = threading.Event()
        threading.Thread(target=self._receive, name='tb-devtools-reader', daemon=True).start()
        threading.Thread(target=self._events, name='tb-devtools-events', daemon=True).start()

    def _receive(self):
        from websocket import WebSocketTimeoutException
        try:
            while not self.closed.is_set():
                try:
                    value = json.loads(self.socket.recv())
                except (TimeoutError, WebSocketTimeoutException):
                    continue
                if value.get('method') == 'Runtime.bindingCalled':
                    self.events.put(value.get('params', {}))
                    self.wake.set()
                elif value.get('method') in ('Page.domContentEventFired', 'Page.frameNavigated', 'Runtime.executionContextsCleared'):
                    self.wake.set()
                elif 'id' in value:
                    with self.lock:
                        waiter = self.pending.get(value['id'])
                        if waiter:
                            waiter[1].append(value)
                            waiter[0].set()
        except Exception:
            pass  # Navigation/closure wakes callers below instead of hanging.
        finally:
            self.closed.set()
            self.wake.set()
            with self.lock:
                for ready, _ in self.pending.values():
                    ready.set()
            self.events.put(None)

    def _events(self):
        while True:
            event = self.events.get()
            if event is None:
                return
            try:
                self.on_event(event, self)
            except Exception:
                logging.getLogger('tb.visible-submit').exception('Browser event delivery failed')

    def send(self, method, params=None):
        with self.lock:
            if self.closed.is_set():
                raise OSError('Browser connection closed')
            self.sequence += 1
            self.socket.send(json.dumps({'id': self.sequence, 'method': method, 'params': params or {}}))
            return self.sequence

    def call(self, method, params=None, timeout=8):
        ready, replies = threading.Event(), []
        with self.lock:
            if self.closed.is_set():
                raise OSError('Browser connection closed')
            self.sequence += 1
            identity = self.sequence
            self.pending[identity] = (ready, replies)
            try:
                self.socket.send(json.dumps({'id': identity, 'method': method, 'params': params or {}}))
            except Exception:
                self.pending.pop(identity, None)
                raise
        try:
            if not ready.wait(timeout):
                raise TimeoutError('Browser response timed out')
            if not replies:
                raise OSError('Browser connection closed')
            value = replies[0]
            if 'error' in value:
                raise RuntimeError(value['error'].get('message', 'Browser command failed'))
            return value.get('result', {})
        finally:
            with self.lock:
                self.pending.pop(identity, None)

    def evaluate(self, expression):
        result = self.call('Runtime.evaluate', {'expression': expression, 'returnByValue': True})
        return result.get('result', {}).get('value')

    def close(self):
        self.closed.set()
        self.wake.set()
        self.socket.close()
        with self.lock:
            for ready, _ in self.pending.values():
                ready.set()
        self.events.put(None)


class ExternalBrowserBridge:
    transport = 'external'
    terminal = {'finished', 'closed', 'error', 'unconfirmed'}

    def __init__(self, profile, guard=None, on_receipt=None, on_pending=None, browser_process=None, on_status=None):
        self.browser = browser_process or BrowserProcess(profile)
        self.guard, self.on_receipt, self.on_pending = guard, on_receipt, on_pending
        self.on_status = on_status
        self.lock = threading.RLock()
        self.sessions, self.clients = {}, {}
        self.stopping = threading.Event()
        self.source = page_source()

    def _open(self, url, code, title, intent, language='cpp17'):
        if self.guard:
            self.guard(url)
        target = submission_target(url)
        with self.lock:
            completed = [key for key, item in self.sessions.items() if item['status'] in self.terminal]
            for key in completed[:-20]:
                del self.sessions[key]
            # Never replay an attempt merely because a request/focus repeats.
            for session in self.sessions.values():
                if session['originalUrl'] == url and session['code'] == code and session.get('language','cpp17') == language and session['status'] not in self.terminal:
                    if intent and not session.get('attempted') and not session.get('dispatching'):
                        session['intent'] = True
                        session['dispatched'] = False
                        session['autoClose'] = True
                        session['retry'] = session.get('retry', 0) + 1
                    session['focus'] = True
                    return self.status(session['sessionId'])
            if sum(item['status'] not in self.terminal for item in self.sessions.values()) >= 8:
                raise ServiceError(409, '请先处理已有的浏览器提交，再打开新的提交页')
            if intent and any(item['originalUrl'] == url and item.get('attempted') and item['status'] not in self.terminal for item in self.sessions.values()):
                raise ServiceError(409, '本题已有提交正在等待回执，请先核对该次结果')
            identity = uuid.uuid4().hex
            session = dict(target, sessionId=identity, code=code, title=title, language=language, intent=intent, autoClose=bool(intent),
                           status='loading', attempted=False, retry=1 if intent else 0, created=time.monotonic(),
                           transport='external', message='正在后台打开原站提交页…' if intent else '正在打开浏览器原站提交页…', focus=not intent)
            self.sessions[identity] = session
        threading.Thread(target=self._run, args=(identity,), name='tb-visible-submit', daemon=True).start()
        return self.status(identity)

    def open(self, url, code, title, language='cpp17'):
        return self._open(url, code, title, False, language)

    def submit(self, url, code, title, language='cpp17'):
        return self._open(url, code, title, True, language)

    def status(self, identity):
        with self.lock:
            session = self.sessions.get(identity)
            if not session:
                raise ServiceError(404, '没有找到本次浏览器提交')
            result = {key: value for key, value in session.items() if key not in
                    {'code', 'title', 'intent', 'created', 'focus', 'originalUrl', 'target', 'dispatching', 'dispatched', 'awaitingLogin'}}
            if result['status'] == 'finished' and self.on_receipt and not result.get('receiptSaved'):
                result['status'] = 'judging'
            return result

    def _update(self, identity, value, inspection=False):
        if not isinstance(value, dict):
            return
        with self.lock:
            session = self.sessions.get(identity)
            if not session or session['status'] in ('finished', 'closed'):
                return
            status = value.get('status')
            allowed = {'loading', 'ready', 'submitted', 'judging', 'finished', 'error',
                       'needs_login', 'needs_verification', 'awaiting_submit', 'unconfirmed'}
            if status not in allowed:
                return
            if session.get('attempted') and status in ('ready', 'loading', 'awaiting_submit'):
                return
            if session.get('submissionId') and status == 'submitted':
                return
            if (not inspection and status == 'loading' and value.get('attempted') is False
                    and session.get('dispatching') and not session.get('attempted')):
                # The adapter explicitly stopped before its durable click
                # checkpoint (for example a Turnstile token expired while the
                # personal-history snapshot was loading). Keep the original
                # intent pending until inspection reports a ready form again.
                session.update(intent=True, dispatched=False, dispatching=False)
            changed = any(session.get(key) != value[key] for key in
                          ('status', 'message', 'submissionId', 'verdict', 'attempted') if key in value)
            if status in ('needs_login', 'needs_verification') and session.get('status') != status:
                session['focus'] = True
            for key in ('status', 'message', 'submissionId', 'verdict', 'attempted',
                        'baseline', 'baselineKnown', 'baselineOwner', 'compiler', 'acceptedAt'):
                if key in value:
                    if key == 'attempted' and inspection and session.get('attempted') and not value[key]:
                        continue  # An inspection begun before the click may finish after it.
                    session[key] = value[key]
            session['updatedAt'] = dt.datetime.now(dt.timezone.utc).isoformat()
            if session.get('attempted'):
                session.setdefault('acceptedAt', session['updatedAt'])
            if status == 'needs_login' and session.get('intent') and not session.get('dispatched'):
                session['awaitingLogin'] = True
            if status == 'error' or status in ('needs_login', 'needs_verification') and (session.get('attempted') or session.get('dispatched')):
                session['intent'] = False
            if status in ('needs_login', 'needs_verification', 'error'):
                session['dispatching'] = False
            snapshot = dict(session)
        if snapshot.get('submissionId') and self.on_pending:
            self.on_pending(identity, snapshot)
        if status == 'finished' and self.on_receipt:
            try:
                saved = self.on_receipt(identity, snapshot)
            except Exception:
                saved = False
            if not saved:
                with self.lock:
                    session.update(status='judging', message='回执已取得，正在重试保存…')
            else:
                with self.lock:
                    session['receiptSaved']=True
                    if isinstance(saved, dict):
                        session['submission'] = saved.get('submission', saved)
        if self.on_status and changed:
            try:
                self.on_status(self.status(identity))
            except Exception:
                logging.getLogger('tb.visible-submit').debug('Desktop status push unavailable', exc_info=True)

    def _event(self, identity, event, page):
        if event.get('name') != '__tbReceipt':
            return
        value = json.loads(event.get('payload', '{}'))
        if value.get('sessionId') != identity:
            return
        self._update(identity, value)
        # Acknowledge the pre-click checkpoint only after the state was stored.
        ack = value.get('ack')
        if type(ack) is int and ack > 0:
            with self.lock:
                if self.sessions.get(identity, {}).get('status') == 'closed':
                    return  # A cancelled pre-click checkpoint must not click.
            page.send('Runtime.evaluate', {'expression': f'window.__tbAcks?.[{ack}]?.()'})

    def _script(self, session, action, install=True):
        context = {key: session.get(key) for key in ('sessionId', 'platform', 'problem', 'code', 'language',
                   'originalUrl', 'attempted', 'baseline', 'baselineKnown', 'baselineOwner', 'submissionId', 'retry')}
        context['nativeFormOnly'] = True
        context['resumeAfterLogin'] = bool(session.get('intent') and not session.get('dispatched'))
        callback = """value => new Promise(resolve => {
          const n = (window.__tbAckSeq = (window.__tbAckSeq || 0) + 1);
          (window.__tbAcks ||= {})[n] = () => { delete window.__tbAcks[n]; resolve(); };
          window.__tbReceipt(JSON.stringify({...value, ack:n}));
        })"""
        return (self.source + ';' if install else '') + 'tbOfficialPage(' + json.dumps(context, ensure_ascii=True) + ',' + json.dumps(action) + ',' + callback + ')'

    def _run(self, identity):
        page = None
        try:
            target = self.browser.new_submission_page() if hasattr(self.browser,'new_submission_page') else self.browser.new_page()
            page = DevToolsPage(target['webSocketDebuggerUrl'], lambda event, connection: self._event(identity, event, connection))
            page.call('Runtime.enable')
            page.call('Runtime.addBinding', {'name': '__tbReceipt'})
            page.call('Page.enable')
            # Install once per document, including native login redirects.
            # Polls no longer transmit and parse the entire platform adapter.
            page.call('Page.addScriptToEvaluateOnNewDocument', {'source': self.source})
            with self.lock:
                self.sessions[identity]['target'] = target['id']
                url = self.sessions[identity]['url']
            page.call('Page.navigate', {'url': url})
            # Submit keeps TB in front. Explicit inspection/login requests and
            # verification transitions can reveal this session's own window.
            while not self.stopping.is_set():
                page.wake.clear()
                with self.lock:
                    session = dict(self.sessions[identity])
                    if session['status'] in self.terminal:
                        return
                    focus = self.sessions[identity].pop('focus', False)
                if time.monotonic() - session['created'] > 900:
                    self._update(identity, {'status': 'unconfirmed' if session.get('attempted') else 'error',
                                           'message': '等待原站回执超时；请在浏览器核对本次提交，勿重复发送。'})
                    return
                try:
                    current = page.evaluate('location.href')
                    host = (urlsplit(current or '').hostname or '').lower()
                    if host not in LOGIN_HOSTS[session['platform']]:
                        if current not in ('about:blank', None):
                            self._update(identity, {'status':'error', 'message':'页面已离开支持的原站，自动操作已停止。'})
                        page.wake.wait(.4)
                        continue
                    if focus:
                        page.call('Page.bringToFront')
                    state = page.evaluate(self._script(session, 'inspect', install=False))
                    self._update(identity, state, inspection=True)
                    with self.lock:
                        live = self.sessions[identity]
                        resume = live.get('awaitingLogin') and live.get('intent') and not live.get('dispatched') and isinstance(state, dict) and state.get('loggedIn')
                        if resume:
                            live.update(awaitingLogin=False, status='loading', message='登录成功，正在返回本题并填入代码…')
                        dispatch = live.get('intent') and live['status'] == 'ready' and not live.get('attempted') and not live.get('dispatching') and not live.get('dispatched')
                        if dispatch:
                            live.update(dispatching=True, dispatched=True, intent=False)
                            session = dict(live)
                    if resume:
                        page.call('Page.navigate', {'url': session['url']})
                        continue
                    if dispatch:
                        if self.guard:
                            self.guard(session['originalUrl'])
                        page.evaluate(self._script(session, 'submit', install=False))
                except Exception:
                    # Navigation destroys the old execution context. The next
                    # inspection reinstalls observers using the durable attempt.
                    try:
                        targets = self.browser.request('/json/list')
                        if not any(item.get('id') == target['id'] for item in targets):
                            self._update(identity, {'status':'unconfirmed' if session.get('attempted') else 'error',
                                                   'message':'提交标签页已关闭，请核对原站记录。'})
                            return
                    except (OSError, ValueError):
                        self._update(identity, {'status':'unconfirmed' if session.get('attempted') else 'error',
                                               'message':'浏览器连接已断开，请核对原站记录后重试。'})
                        return
                page.wake.wait(1.5 if session.get('attempted') else (.15 if time.monotonic() - session['created'] < 30 else .6))
        except Exception:
            logging.getLogger('tb.visible-submit').exception('Visible browser session failed')
            self._update(identity, {'status':'error', 'message':'浏览器未能连接，请重新打开提交页；代码已保留。'})
        finally:
            if page:
                page.close()

    def acknowledge(self, identity):
        with self.lock:
            session=self.sessions.get(identity)
            if not session:
                raise ServiceError(404,'没有找到本次提交')
            if session.get('windowClosed'):
                return {'closed':True}
            if session.get('status')!='finished' or not session.get('receiptSaved') or not session.get('autoClose'):
                return {'closed':False}
            target=session.get('target')
        if not target:
            return {'closed':False}
        closed=self.browser.close_page(target)
        if closed:
            with self.lock:
                session['windowClosed']=True
        return {'closed':bool(closed)}

    def close(self, identity):
        with self.lock:
            for key, session in self.sessions.items():
                if identity is None or identity == key:
                    session.update(status='closed', intent=False)
        # User's browser/tab stays open for inspection.
        return {'closed': True}

    def on_closing(self, *args):
        self.stopping.set()


class ExternalBrowserPreparation:
    def __init__(self, bridge, logins=None):
        self.bridge, self.logins = bridge, logins

    def snapshot(self):
        available = browsers()
        identities = self.logins.snapshot() if self.logins else {'platforms': {}}
        return {'available': True, 'mode': 'external', 'ready': any(available.values()), 'preferredBrowser': self.bridge.browser.preferred,
                'loginSequenceBusy': identities.get('busy', False),
                'browsers': [{'id': key, 'available': bool(path)} for key, path in available.items()],
                'platforms': [{'platform': key, 'state': 'browser_owned', **identities['platforms'].get(key, {}), 'loginUrl': url} for key, url in {
                    'Codeforces':'https://codeforces.com/enter', 'AtCoder':'https://atcoder.jp/login',
                    '牛客':'https://ac.nowcoder.com/login', '洛谷':'https://www.luogu.com.cn/auth/login', 'QOJ':'https://qoj.ac/login'}.items()]}

    def check_submission(self, url):
        submission_target(url)
        if not any(browsers().values()):
            raise ServiceError(503, '请安装 Edge 或 Chrome 后使用浏览器提交')

    def action(self, body):
        action = body.get('action')
        if action == 'startup-logins':
            if set(body) != {'action'} or self.logins is None:
                raise ServiceError(400, '平台登录准备无效')
            return self.logins.start()
        if action == 'refresh':
            return self.snapshot()
        if action == 'open-login':
            entry = next((item for item in self.snapshot()['platforms'] if item['platform'] == body.get('platform')), None)
            if entry is None or body.get('browser', 'edge') not in ('edge', 'chrome'):
                raise ServiceError(400, '请选择支持的平台和浏览器')
            browser = body.get('browser', self.bridge.browser.preferred)
            with self.bridge.lock:
                if browser != self.bridge.browser.preferred:
                    active = [session for session in self.bridge.sessions.values() if session['status'] not in self.bridge.terminal]
                    if any(session.get('attempted') or session.get('dispatching') for session in active):
                        raise ServiceError(409, '请先取得当前提交的回执，再切换浏览器')
                    # A login in Chrome must not leave Submit reusing an older
                    # unlogged Edge tab. Cancel only jobs that never clicked.
                    self.bridge.close(None)
                self.bridge.browser.new_page(entry['loginUrl'], browser)
            return {'opened': True}
        raise ServiceError(400, '浏览器操作无效')
