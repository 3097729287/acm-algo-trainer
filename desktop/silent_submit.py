"""No-window official submission using WebView2 and browser-synced site sessions."""
import json
import logging
import queue
import threading
import time
from urllib.parse import urlsplit

from official_bridge import OfficialBridge, LOGIN_HOSTS, page_source
from silent_browser import wake_browser
from browser_sessions import live_cookies
PROFILE_NAMES = {'Codeforces':'tb-cf','AtCoder':'tb-atcoder','牛客':'tb-nowcoder','洛谷':'tb-luogu','QOJ':'tb-qoj'}


def navigation_failure(session):
    attempted = bool(session.get('attempted'))
    return {'sessionId': session['sessionId'], 'status': 'unconfirmed' if attempted else 'error',
            'attempted': attempted, 'message': '提交后连接中断，正在核对原站记录，请勿重复提交。' if attempted else '原站页面加载失败，请检查网络后重试。'}


def bootstrap(session):
    context = {k: session.get(k) for k in ('sessionId', 'platform', 'originalUrl', 'problem', 'code', 'attempted', 'baseline', 'baselineKnown', 'baselineOwner', 'submissionId')}
    return page_source() + ';(' + r'''function(ctx){
      if(window!==window.top)return;
      const pending=new Map();let command='';
      const report=value=>{
        for(const k of ['attempted','baseline','baselineKnown','baselineOwner','submissionId'])if(k in value)ctx[k]=value[k];
        if(value.status==='submitted'&&value.attempted)return new Promise((resolve,reject)=>{
          const id=crypto.randomUUID(),timer=setTimeout(()=>{pending.delete(id);reject(new Error('ToBe 未确认提交，尚未发送代码。'))},10000);
          pending.set(id,ok=>{clearTimeout(timer);pending.delete(id);ok?resolve():reject(new Error('ToBe 连接中断，尚未发送代码。'))});
          chrome.webview.postMessage(JSON.stringify({value,requestId:id}));
        });
        chrome.webview.postMessage(JSON.stringify({value}));
      };
      window.__tbSilentAck=(id,ok)=>pending.get(id)?.(ok);
      tbOfficialPage(ctx,'observe',report);
      window.__tbSilentCommand=packet=>{
        Object.assign(ctx,packet.context);
        if(packet.action==='submit'){
          const id=ctx.sessionId+':'+packet.command;if(command===id)return;command=id;
        }
        try{
          const value=tbOfficialPage(ctx,packet.action,report);
          if(value?.status&&packet.action!=='submit')report({sessionId:ctx.sessionId,...value});
        }catch{report({sessionId:ctx.sessionId,status:'error',message:'原站页面解析失败，尚未确认提交，请重试。'})}
      };
    }''' + ')(' + json.dumps(context, ensure_ascii=True) + ');'


class SilentSubmitter(OfficialBridge):
    def __init__(self, window, bridge, store, wake=wake_browser, native_setup=None):
        super().__init__(window)
        self.bridge, self.store, self.wake = bridge, store, wake
        self.sessions = bridge.sessions
        self.threads = {}
        self.messages = {}
        self.native_setup = native_setup

    def start(self, identity):
        with self.lock:
            if self.threads.get(identity, None) and self.threads[identity].is_alive():
                return
            thread = threading.Thread(target=self._run, args=(identity,), daemon=True)
            self.threads[identity] = thread
            thread.start()

    def _event(self, identity, value):
        session = self.sessions[identity]
        return self.bridge.exchange({'sessionId': identity, 'pageUrl': session['url'], 'event': value}, session['capability'])

    def _run(self, identity):
        session = self.sessions[identity]
        messages = self.messages[identity] = queue.Queue()
        try:
            self.bridge.exchange({'sessionId': identity, 'claim': True}, session['capability'])
            cached = self.store.snapshot(session['platform'])
            event = self.store.request(session['platform'])
            usable = bool(live_cookies(cached)) and cached.get('loginState') != 'logged_out'
            if not event.wait(1.5 if usable else 1):
                if self.stopping.is_set():
                    return
                if not usable:
                    self.wake()
                    event.wait(12)
            snapshot = self.store.snapshot(session['platform'])
            self.store.finish(session['platform'])
            if self.bridge.route_to_browser(identity):
                return
            if snapshot is None:
                self._event(identity, {'status': 'needs_browser', 'attempted': False,
                    'message': '未收到本平台的登录会话，尚未发送代码。请在浏览器确认已启用最新版 ToBe 连接扩展，重新检测后再提交。'})
                return
            self._ui(lambda: self._attach_silent(identity, snapshot))
            next_inspect = 0
            while not self.stopping.is_set():
                try:
                    packet = messages.get(timeout=.2)
                    if packet.get('tick'):
                        next_inspect = 0
                    value = packet.get('value')
                    if isinstance(value, dict) and value.get('sessionId') == identity:
                        if value.get('status') in ('needs_login', 'needs_verification', 'error') and self.bridge.route_to_browser(identity, before_click=value.get('attempted') is False):
                            return
                        answer = self._event(identity, value)
                        if value.get('status') == 'ready':
                            next_inspect = 0
                        if packet.get('requestId'):
                            self._eval('window.__tbSilentAck?.(' + json.dumps(packet['requestId']) + ',' + json.dumps(answer.get('ack') is True) + ')', identity=identity)
                except queue.Empty:
                    pass
                status = self.bridge.status(identity)['status']
                if session.get('manual') and session.get('transport') == 'browser':
                    return
                if status in ('closed', 'finished', 'error', 'needs_login', 'needs_verification', 'needs_browser'):
                    return
                if time.monotonic() >= next_inspect:
                    answer = self.bridge.exchange({'sessionId': identity, 'pageUrl': session['url']}, session['capability'])
                    if answer.get('context'):
                        self._eval('window.__tbSilentCommand?.(' + json.dumps(answer, ensure_ascii=True) + ')', identity=identity)
                    next_inspect = time.monotonic() + (.25 if status == 'loading' else 1)
        except Exception:
            # A lost connection after the dispatch checkpoint cannot prove that
            # the original site rejected the code. Keep its receipt poll alive
            # and never invite an automatic duplicate submit.
            logging.exception('Silent submission failed: platform=%s', session['platform'])
            self._event(identity, navigation_failure(session))
        finally:
            try:
                self._ui(lambda: self._release_silent(identity))
            except Exception:
                pass
            with self.lock:
                self.threads.pop(identity, None)
                self.messages.pop(identity, None)

    def _message(self, identity, packet):
        # WebView callbacks can arrive while its panel is being disposed. Do
        # not retain a finished queue or resurrect a completed worker for them.
        with self.lock:
            messages = self.messages.get(identity)
        if messages is not None:
            messages.put(packet)

    def _release_silent(self, identity):
        entry = self.views.pop(identity, None)
        if entry:
            self.main_window.native.Controls.Remove(entry['panel'])
            entry['panel'].Dispose()

    def _attach_silent(self, identity, snapshot):
        import System.Windows.Forms as Forms
        from System import Action, String, DateTime, DateTimeKind
        from System.Threading.Tasks import Task
        from Microsoft.Web.WebView2.WinForms import WebView2, CoreWebView2CreationProperties
        from Microsoft.Web.WebView2.Core import CoreWebView2CookieSameSiteKind
        form, session = self.main_window.native, self.sessions[identity]
        panel = Forms.Panel()
        panel.Dock, panel.Visible = Forms.DockStyle.Fill, False
        view = WebView2()
        view.Dock = Forms.DockStyle.Fill
        props = CoreWebView2CreationProperties()
        props.UserDataFolder = form.browser.user_data_folder
        props.ProfileName = PROFILE_NAMES[session['platform']]
        props.set_IsInPrivateModeEnabled(False)
        view.CreationProperties = props
        panel.Controls.Add(view)
        form.Controls.Add(panel)
        panel.Visible = False
        self.views[identity] = {'panel': panel, 'view': view}

        def initialized(_, args):
            if not args.IsSuccess:
                logging.error('Silent WebView initialization: %s', args.InitializationException)
                self._message(identity, {'value': {'sessionId': identity, 'status': 'error', 'attempted': False, 'message': 'WebView2 后台组件初始化失败。'}})
                return
            core = view.CoreWebView2
            if self.native_setup:
                self.native_setup(view)
            core.Settings.AreDevToolsEnabled = core.Settings.IsStatusBarEnabled = False
            if snapshot.get('userAgent'):
                core.Settings.UserAgent = snapshot['userAgent']
            manager = core.CookieManager
            # Only this app's OJ cookies are replaced. Never read or alter the
            # user's actual browser profile, password store or unrelated sites.
            manager.DeleteAllCookies()
            for item in snapshot['cookies']:
                cookie = manager.CreateCookie(item['name'], item['value'], item['domain'], item['path'])
                cookie.IsSecure, cookie.IsHttpOnly = bool(item.get('secure')), bool(item.get('httpOnly'))
                cookie.SameSite = {'strict': CoreWebView2CookieSameSiteKind.Strict, 'lax': CoreWebView2CookieSameSiteKind.Lax,
                                   'no_restriction': getattr(CoreWebView2CookieSameSiteKind, 'None')}[item.get('sameSite') if item.get('sameSite') in ('strict', 'lax', 'no_restriction') else 'lax']
                if item.get('expirationDate'):
                    cookie.Expires = DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc).AddSeconds(float(item['expirationDate']))
                manager.AddOrUpdateCookie(cookie)
            def navigation(_, event):
                target = urlsplit(str(event.Uri))
                if target.scheme != 'https' or target.hostname not in LOGIN_HOSTS[session['platform']]:
                    event.Cancel = True
                    value = navigation_failure(session)
                    if not value['attempted']:
                        value['message'] = '已停止离开原站的提交跳转，尚未发送代码。'
                    self._message(identity, {'value': value})
            def popup(_, event):
                event.Handled = True
            def message(_, event):
                try:
                    target = urlsplit(str(event.Source))
                    if target.scheme == 'https' and target.hostname in LOGIN_HOSTS[session['platform']]:
                        self._message(identity, json.loads(str(event.TryGetWebMessageAsString())))
                except (ValueError, TypeError):
                    pass
            core.NavigationStarting += navigation
            core.NewWindowRequested += popup
            core.WebMessageReceived += message
            def parsed(_, event):
                self._message(identity, {'tick': True})
            recovering = [False]
            def loaded(_, event):
                if event.IsSuccess:
                    parsed(_, event)
                elif str(event.WebErrorStatus) != 'OperationCanceled':
                    value = navigation_failure(session)
                    self._message(identity, {'value': value})
                    if value['attempted'] and not recovering[0] and not self.stopping.is_set() and session['platform'] in ('Codeforces', 'AtCoder'):
                        recovering[0] = True
                        suffix = '/my' if session['platform'] == 'Codeforces' else '/submissions/me'
                        core.Navigate(session['url'].split('?')[0].removesuffix('/submit') + suffix)
            core.DOMContentLoaded += parsed
            core.NavigationCompleted += loaded
            def registered(task):
                try:
                    task.Result
                    self._ui(lambda: core.Navigate(session['url']))
                except Exception:
                    self._message(identity, {'value': {'sessionId': identity, 'status': 'error', 'attempted': False, 'message': '原站回执监听初始化失败。'}})
            core.AddScriptToExecuteOnDocumentCreatedAsync(bootstrap(dict(session))).ContinueWith(Action[Task[String]](registered))
        view.CoreWebView2InitializationCompleted += initialized
        view.EnsureCoreWebView2Async(form.browser.webview.CoreWebView2.Environment)

    def stop(self):
        self.stopping.set()
