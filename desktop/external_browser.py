"""Visible original-site forms in an isolated Edge/Chrome profile, no extension.

The browser owns login, CSRF and verification. One explicit TB intent may click
one native submit control. The same adapter observes only that attempt's receipt.
No cookies are exported or copied from a user's everyday browser profile.
"""
from __future__ import annotations

import datetime as dt
from contextvars import copy_context
import json
import queue
import logging
import os
import re
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
                '--no-first-run', '--no-default-browser-check', '--disable-background-mode', '--mute-audio', *startup],
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
        protocol = self.request('/json/protocol')
        command = next((command for domain in protocol.get('domains', []) if domain.get('domain') == 'Target'
                        for command in domain.get('commands', []) if command.get('name') == 'createTarget'), {})
        if not any(parameter.get('name') == 'windowState' for parameter in command.get('parameters', [])):
            raise ServiceError(503, '当前浏览器不支持后台提交窗口，请更新 Edge 或 Chrome 后重试')
        version=self.request('/json/version')
        page=DevToolsPage(version['webSocketDebuggerUrl'],lambda *_:None)
        try:
            target=page.call('Target.createTarget',{'url':'about:blank','newWindow':True,'background':True,'windowState':'minimized'})['targetId']
            for blank in self.bootstrap_targets:
                page.call('Target.closeTarget',{'targetId':blank})
            self.bootstrap_targets.clear()
            return next(item for item in self.request('/json/list') if item.get('id')==target)
        finally:
            page.close()

    def present_page(self, identity, page, visible, *, activate=False):
        version=self.request('/json/version')
        browser=DevToolsPage(version['webSocketDebuggerUrl'],lambda *_:None)
        marker='[ToBe-'+uuid.uuid4().hex+'] '
        original=None
        try:
            window=browser.call('Browser.getWindowForTarget',{'targetId':identity})
            processes=browser.call('SystemInfo.getProcessInfo')['processInfo']
            pid=next((item['id'] for item in processes if item.get('type')=='browser'),None)
            if type(pid) is not int or pid<=0:return False
            if visible and activate and window.get('bounds',{}).get('windowState')=='minimized':
                browser.call('Browser.setWindowBounds',{'windowId':window['windowId'],'bounds':{'windowState':'normal'}})
            # A short-lived title tag binds a Win32 handle to this exact target,
            # even when several submissions share the browser PID and bounds.
            original=page.evaluate('(()=>{const value=document.title;document.title='+json.dumps(marker)+'+value;return value;})()')
            if not isinstance(original,str):return False
            if visible and activate:page.call('Page.bringToFront')
            if os.name=='nt':
                from browser_presentation import present_window
                return present_window(pid,marker,visible,activate=activate)
            if not visible:browser.call('Browser.setWindowBounds',{'windowId':window['windowId'],'bounds':{'windowState':'minimized'}})
            return True
        finally:
            if isinstance(original,str):
                try:page.evaluate('if(document.title==='+json.dumps(marker+original)+')document.title='+json.dumps(original))
                except Exception:pass
            browser.close()

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

    def __init__(self, profile, guard=None, on_receipt=None, on_pending=None, browser_process=None, on_status=None, recovery_current=None):
        self.browser = browser_process or BrowserProcess(profile)
        self.guard, self.on_receipt, self.on_pending = guard, on_receipt, on_pending
        self.on_status = on_status
        self.recovery_current = recovery_current
        self.lock = threading.RLock()
        self.sessions, self.clients = {}, {}
        self.stopping = threading.Event()
        self.source = page_source()

    def restore_pending(self, records, owner=None):
        """Queue persisted numbered receipts. This entry point cannot submit."""
        for record in records:
            try:
                target=submission_target(record['url'])
                identity=record['sessionId'];remote=str(record['submissionId'])
                if not isinstance(identity,str) or not identity or not remote.isdecimal() or int(remote)<=0:
                    continue
                if not isinstance(record.get('code'),str) or not record['code'].strip():continue
                accepted=dt.datetime.fromisoformat(record['acceptedAt'])
                if accepted.tzinfo is None or accepted.timestamp()<=0:continue
                metadata=record.get('metadata') or {}
                if metadata.get('_invalid'):continue
                with self.lock:
                    if identity in self.sessions or sum(s['status'] not in self.terminal for s in self.sessions.values())>=8:
                        continue
                    self.sessions[identity]=dict(target,sessionId=identity,originalUrl=record['url'],url=record['url'],
                        code=record['code'],language=metadata.get('language') or 'cpp17',created=time.monotonic(),
                        submissionId=remote,acceptedAt=record['acceptedAt'],status='judging',attempted=True,
                        intent=False,dispatched=True,autoClose=True,readOnlyRestore=True,transport='external',
                        _guardAuthorization=(id(owner),metadata.get('contestId')),_restoreOwner=owner,
                        _restoreRecord=dict(record),message='正在恢复查询原提交 #'+remote+'，不会重新发送代码。')
                threading.Thread(target=self._run_restore,args=(identity,),name='tb-recover-receipt',daemon=True).start()
            except (ValueError,KeyError,TypeError):
                continue

    def _run_restore(self, identity):
        from official_recovery import legacy_nowcoder_proof,nowcoder_binding,source_hash
        page=None
        try:
            if self.stopping.is_set():return
            with self.lock:session=dict(self.sessions[identity]);record=session['_restoreRecord']
            if self.recovery_current and not self.recovery_current(session.get('_restoreOwner')):
                raise ValueError('Account changed')
            if session['platform']!='牛客':
                raise ValueError('No verified recovery protocol')
            self.browser.ensure(background=True)
            metadata=record.get('metadata') or {}
            binding=nowcoder_binding(metadata.get('receiptBinding'),record['url'])
            known=bool(binding and metadata.get('codeSha256')==source_hash(record['code']))
            target=None;proof=None
            for candidate in self.browser.request('/json/list'):
                if candidate.get('type','page')!='page' or candidate.get('url')!=record['url']:
                    continue
                page=DevToolsPage(candidate['webSocketDebuggerUrl'],lambda *_:None)
                try:proof=legacy_nowcoder_proof(page,record)
                finally:page.close();page=None
                if proof:
                    if known and proof['binding']!=binding:raise ValueError('Saved binding changed')
                    if metadata.get('language') in ('cpp17','python3') and metadata['language']!=proof['language']:raise ValueError('Saved language changed')
                    binding=proof['binding'];target=candidate;break
            if not known and not proof:
                raise ValueError('Legacy ownership proof unavailable')
            if self.stopping.is_set():return
            if not target:
                target=self.browser.new_submission_page()
            with self.lock:
                live=self.sessions[identity]
                live.update(receiptBinding=binding,_recoveryVerified=True,target=target['id'],
                            _resumeTarget=target['id'],_resumeNavigate=not bool(proof),
                            language=(proof or {}).get('language') or metadata.get('language') or 'cpp17')
                snapshot=dict(live)
            if self.on_pending and not self.on_pending(identity,snapshot):
                raise ValueError('Recovery binding not durably saved')
            self._run(identity)
        except Exception:
            self._update(identity,{'status':'unconfirmed','attempted':True,
                'message':'原提交编号已保留，暂时无法核验原站账号或连接；请保持 ToBe 专用原站页面登录后重查，不会重交。'})
        finally:
            if page:page.close()

    def retry_recovery(self, identity, *, visible=False):
        with self.lock:
            session=self.sessions.get(identity)
            if not session or not session.get('readOnlyRestore'):
                raise ServiceError(404,'没有找到原提交恢复会话')
            if self.recovery_current and not self.recovery_current(session.get('_restoreOwner')):
                raise ServiceError(403,'请先恢复该提交所属账号')
            if visible:
                session.update(explicitVisible=True,_manualWindow=True,autoClose=False)
            if session['status']=='unconfirmed':
                session.update(status='judging',intent=False,dispatched=True,created=time.monotonic())
                threading.Thread(target=self._run_restore,args=(identity,),name='tb-recheck-recovery',daemon=True).start()
            return self.status(identity)

    def _open(self, url, code, title, intent, language='cpp17'):
        authorization = self.guard(url) if self.guard else None
        target = submission_target(url)
        with self.lock:
            completed = [key for key, item in self.sessions.items() if item['status'] in self.terminal and not (item['status']=='unconfirmed' and item.get('attempted'))]
            for key in completed[:-20]:
                del self.sessions[key]
            # Never replay an attempt merely because a request/focus repeats.
            for session in self.sessions.values():
                if session['originalUrl'] == url and session['code'] == code and session.get('language','cpp17') == language and (session['status'] not in self.terminal or session['status']=='unconfirmed' and session.get('attempted')):
                    if session.get('_guardAuthorization') != authorization:
                        raise ServiceError(409, '已有其它账号或比赛上下文的原站会话，请先处理该会话再提交')
                    if intent and not session.get('attempted') and not session.get('dispatching'):
                        session['intent'] = True
                        session['dispatched'] = False
                        session['autoClose'] = not session.get('_manualWindow', False)
                        session['retry'] = session.get('retry', 0) + 1
                    if not intent:
                        session['_manualWindow'] = True
                        session['autoClose'] = False
                    session['focus'] = session['status'] in ('needs_login', 'needs_verification')
                    session['explicitVisible'] = not intent
                    if session['status']=='unconfirmed' and session.get('target'):
                        # Reconnect to the same owned page only to query its
                        # numbered receipt. The prior click is never re-armed.
                        session.update(status='judging' if session.get('submissionId') else 'submitted',intent=False,dispatched=True,
                                       created=time.monotonic(),_resumeTarget=session['target'],message='正在重新查询原站本次提交记录，不会重复发送代码。')
                        context=copy_context()
                        worker=self._run_restore if session.get('readOnlyRestore') else self._run
                        threading.Thread(target=context.run,args=(worker,session['sessionId']),name='tb-recheck-submit',daemon=True).start()
                    elif session['status']=='unconfirmed' and session.get('readOnlyRestore'):
                        session.update(status='judging',created=time.monotonic(),intent=False,dispatched=True)
                        threading.Thread(target=self._run_restore,args=(session['sessionId'],),name='tb-recheck-recovery',daemon=True).start()
                    return self.status(session['sessionId'])
            if sum(item['status'] not in self.terminal for item in self.sessions.values()) >= 8:
                raise ServiceError(409, '请先处理已有的浏览器提交，再打开新的提交页')
            if intent and any(item['originalUrl'] == url and item.get('attempted') and (item['status'] not in self.terminal or item['status']=='unconfirmed') for item in self.sessions.values()):
                raise ServiceError(409, '本题已有提交正在等待回执，请先核对该次结果')
            identity = uuid.uuid4().hex
            session = dict(target, sessionId=identity, code=code, title=title, language=language, intent=intent, autoClose=bool(intent),
                           status='loading', attempted=False, retry=1 if intent else 0, created=time.monotonic(),
                            transport='external', message='正在后台打开原站提交页…' if intent else '正在打开浏览器原站提交页…', focus=False, explicitVisible=not intent,
                            _guardAuthorization=authorization, _manualWindow=not intent)
            self.sessions[identity] = session
        # The pre-click guard must see the same account/contest authorization
        # as the initial guard. Each worker gets its own context copy.
        context = copy_context()
        threading.Thread(target=context.run, args=(self._run, identity), name='tb-visible-submit', daemon=True).start()
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
                    {'code', 'title', 'intent', 'created', 'focus', 'originalUrl', 'target', 'dispatching', 'dispatched', 'awaitingLogin', 'explicitVisible', '_guardAuthorization', '_manualWindow', '_resumeTarget', '_resumeNavigate', '_restoreRecord', '_restoreOwner', '_recoveryVerified', 'receiptBinding'}}
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
            if session.get('readOnlyRestore') and status=='error':status='unconfirmed';value={**value,'status':status}
            allowed = {'loading', 'ready', 'submitted', 'judging', 'finished', 'error',
                       'needs_login', 'needs_verification', 'awaiting_submit', 'unconfirmed'}
            if status not in allowed:
                return
            remote = str(value.get('submissionId') or '')
            previous = str(session.get('submissionId') or '')
            if remote and previous and remote != previous:
                return  # Once accepted, a different SID cannot finish this job.
            if status in ('judging', 'finished') and session.get('platform') == 'Codeforces':
                if not session.get('attempted') or not remote.isdecimal() or int(remote) <= 0:
                    return
                baseline = [int(item) for item in (session.get('baseline') or []) if str(item).isdecimal()]
                if session.get('baselineKnown') and any(int(remote) <= old for old in baseline):
                    return
                if status == 'finished' and value.get('verdict') not in ('AC', 'WA', 'TLE', 'MLE', 'RE', 'CE', 'OLE'):
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
            for key in ('status', 'message', 'submissionId', 'verdict', 'verdictDetail', 'attempted',
                        'baseline', 'baselineKnown', 'baselineOwner', 'compiler', 'acceptedAt', 'receiptBinding'):
                if key in value:
                    if key=='attempted' and session.get('readOnlyRestore'):continue
                    if key=='receiptBinding':
                        from official_recovery import nowcoder_binding
                        binding=nowcoder_binding(value[key],session.get('originalUrl',''))
                        if binding:session[key]=binding
                        continue
                    if key == 'attempted' and inspection and session.get('attempted') and not value[key]:
                        continue  # An inspection begun before the click may finish after it.
                    session[key] = value[key]
            session['updatedAt'] = dt.datetime.now(dt.timezone.utc).isoformat()
            if session.get('attempted'):
                session.setdefault('acceptedAt', session['updatedAt'])
            if status == 'needs_login' and (session.get('readOnlyRestore') or session.get('intent') and not session.get('dispatched')):
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
                    session.update(status='unconfirmed' if session.get('readOnlyRestore') else 'judging',
                                   message='原回执校验或保存尚未完成，编号已保留，请重新查询；不会重交。' if session.get('readOnlyRestore') else '回执已取得，正在重试保存…')
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
                   'originalUrl', 'attempted', 'baseline', 'baselineKnown', 'baselineOwner', 'submissionId', 'retry',
                   'readOnlyRestore','receiptBinding','acceptedAt')}
        context['nativeFormOnly'] = True
        context['resumeAfterLogin'] = bool(session.get('readOnlyRestore') or session.get('intent') and not session.get('dispatched'))
        callback = """value => new Promise(resolve => {
          const n = (window.__tbAckSeq = (window.__tbAckSeq || 0) + 1);
          (window.__tbAcks ||= {})[n] = () => { delete window.__tbAcks[n]; resolve(); };
          window.__tbReceipt(JSON.stringify({...value, ack:n}));
        })"""
        return (self.source + ';' if install else '') + 'tbOfficialPage(' + json.dumps(context, ensure_ascii=True) + ',' + json.dumps(action) + ',' + callback + ')'

    def _run(self, identity):
        page = None
        presentation = None
        try:
            with self.lock:
                resume_target=self.sessions[identity].pop('_resumeTarget',None)
                resume_navigate=self.sessions[identity].pop('_resumeNavigate',False)
            if resume_target:
                target=next((item for item in self.browser.request('/json/list') if item.get('id')==resume_target),None)
                if not target:
                    self._update(identity,{'status':'unconfirmed','message':'原提交页面已关闭；提交编号已保留，请在原站核对，勿重复提交。'})
                    return
            else:
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
                explicit=self.sessions[identity].get('explicitVisible',False)
            if hasattr(self.browser,'present_page'):
                try:
                    if self.browser.present_page(target['id'],page,explicit,activate=False):presentation=(explicit,False)
                except Exception:
                    logging.getLogger('tb.visible-submit').debug('Initial browser presentation deferred')
            if resume_target and not resume_navigate:
                page.evaluate(self.source+';true')
            else:
                page.call('Page.navigate', {'url': url})
            # Submit keeps TB in front. Explicit inspection/login requests and
            # verification transitions can reveal this session's own window.
            while not self.stopping.is_set():
                page.wake.clear()
                with self.lock:
                    session = dict(self.sessions[identity])
                    if session['status'] in self.terminal:
                        return
                if session.get('readOnlyRestore') and self.recovery_current and not self.recovery_current(session.get('_restoreOwner')):
                    self._update(identity,{'status':'unconfirmed','message':'账号已切换，原提交保留待原账号恢复查询，不会重交。'})
                    return
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
                    state = page.evaluate(self._script(session, 'inspect', install=False))
                    self._update(identity, state, inspection=True)
                    with self.lock:
                        live = self.sessions[identity]
                        visible=bool(live.get('explicitVisible') or live['status'] in ('needs_login','needs_verification'))
                        activate=live['status'] in ('needs_login','needs_verification')
                        focus=live.pop('focus',False)
                        resume = live.get('awaitingLogin') and (live.get('readOnlyRestore') or live.get('intent') and not live.get('dispatched')) and isinstance(state, dict) and state.get('loggedIn')
                        if resume:
                            live.update(awaitingLogin=False,status='judging' if live.get('readOnlyRestore') else 'loading',
                                        message='登录成功，正在返回本题查询原提交，不会重交。' if live.get('readOnlyRestore') else '登录成功，正在返回本题并填入代码…')
                        dispatch = not live.get('readOnlyRestore') and live.get('intent') and live['status'] == 'ready' and not live.get('attempted') and not live.get('dispatching') and not live.get('dispatched')
                        if dispatch:
                            live.update(dispatching=True, dispatched=True, intent=False)
                            session = dict(live)
                    if (visible,activate)!=presentation or focus:
                        try:
                            if hasattr(self.browser,'present_page'):
                                if self.browser.present_page(target['id'],page,visible,activate=activate):presentation=(visible,activate)
                            elif visible and activate:page.call('Page.bringToFront')
                        except Exception:
                            # Focus/OS restrictions cannot consume the durable
                            # pre-click checkpoint or prevent its one dispatch.
                            logging.getLogger('tb.visible-submit').debug('Browser presentation deferred')
                    if resume:
                        page.call('Page.navigate', {'url': session['url']})
                        continue
                    if dispatch:
                        if self.guard:
                            authorization = self.guard(session['originalUrl'])
                            if authorization != session.get('_guardAuthorization'):
                                raise ServiceError(403, '原站会话的账号或比赛授权已变化，未发送提交')
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
            with self.lock:attempted=self.sessions.get(identity,{}).get('attempted')
            self._update(identity, {'status':'unconfirmed' if attempted else 'error', 'message':'浏览器未能连接，已有提交请先核对原站记录；代码已保留。'})
        finally:
            if page:
                with self.lock:session=self.sessions.get(identity,{})
                if (hasattr(self.browser,'present_page') and not session.get('explicitVisible')
                        and session.get('status') not in ('needs_login','needs_verification')):
                    try:self.browser.present_page(target['id'],page,False,activate=False)
                    except Exception:pass
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
            saved=session.get('submission')
            remote=str(session.get('submissionId') or '')
            if (not session.get('attempted') or not remote.isdecimal() or int(remote)<=0
                    or not isinstance(saved,dict) or saved.get('scope')!='official' or saved.get('mode')!='submit'
                    or not saved.get('finishedAt') or saved.get('verdict')!=session.get('verdict')
                    or not isinstance(saved.get('id'),str) or not re.fullmatch(r'official-[0-9a-f]{64}',saved['id'])
                    or not isinstance(saved.get('message'),str) or not re.match(r'^原站确认提交 #'+remote+r'(?:\s|$)',saved['message'])):
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
        if action == 'open-contest':
            import re
            url=body.get('url')
            if set(body)!={'action','url'} or not isinstance(url,str) or not re.fullmatch(r'https://ac\.nowcoder\.com/acm/contest/[1-9]\d*',url):
                raise ServiceError(400,'牛客比赛原站地址无效')
            self.bridge.browser.new_page(url)
            return {'opened':True}
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
