"""Read authenticated identities in TB's browser and request missing logins in order.

Inspection never fills forms, exports cookies, or submits code. The browser's
existing encrypted login memory remains responsible for session persistence.
"""
import json
import re
import threading
import time
import weakref
from urllib.parse import urlsplit

from official_bridge import LOGIN_HOSTS

SITES = {
    'Codeforces': ('codeforces', 'https://codeforces.com/', 'https://codeforces.com/enter'),
    'AtCoder': ('atcoder', 'https://atcoder.jp/', 'https://atcoder.jp/login'),
    '牛客': ('nowcoder', 'https://ac.nowcoder.com/', 'https://ac.nowcoder.com/login'),
    '洛谷': ('luogu', 'https://www.luogu.com.cn/', 'https://www.luogu.com.cn/auth/login'),
}

LOGIN_SCRIPT = r"""(()=>{
if(window!==window.top||location.protocol!=='https:')return null;
const site={'codeforces.com':'Codeforces','www.codeforces.com':'Codeforces','atcoder.jp':'AtCoder','ac.nowcoder.com':'牛客','www.nowcoder.com':'牛客','nowcoder.com':'牛客','www.luogu.com.cn':'洛谷','luogu.com.cn':'洛谷','login.luogu.com.cn':'洛谷'}[location.hostname];
if(!site)return null;
const result={platform:site,url:location.href,state:'unknown',owner:''};
if(/just a moment|checking your browser|安全验证|人机验证/i.test(document.title))return result;
const links=selector=>[...document.querySelectorAll(selector)].map(a=>{try{const u=new URL(a.getAttribute('href'),location.href);return u.origin===location.origin?u.pathname:'';}catch{return '';}});
let owner='';
if(site==='Codeforces'){
 const paths=links('#header a[href],header a[href],.lang-chooser a[href]');
 // Blog authors and a viewed profile are never an authenticated identity.
 if(paths.some(path=>/^\/logout(?:\/|$)/.test(path)))owner=paths.map(path=>path.match(/^\/profile\/([A-Za-z0-9_.-]{1,64})\/?$/)?.[1]).find(Boolean)||'';
 if(!owner&&paths.some(path=>/^\/(?:enter|login)\/?$/.test(path)))result.state='logged_out';
}else if(site==='AtCoder'){
 const paths=links('.navbar a[href],#navbar-collapse a[href],header a[href]');
 const signed=paths.some(path=>/^\/(?:logout|signout)\/?$/.test(path))||!!document.querySelector('form[action="/logout"]');
 if(signed)owner=paths.map(path=>path.match(/^\/users\/([A-Za-z0-9_]{1,64})\/?$/)?.[1]).find(Boolean)||'';
 if(!owner&&paths.some(path=>/^\/login\/?$/.test(path)))result.state='logged_out';
}else if(site==='牛客'){
 const value=window.globalInfo?.ownerId;
 if(value!==undefined&&value!==null){if(/^[1-9]\d{0,19}$/.test(String(value)))owner=String(value);else if(Number(value)===0)result.state='logged_out';}
}else{
 let context=null;try{context=JSON.parse(document.querySelector('#lentille-context')?.textContent||'null');}catch{}
 const known=context&&Object.prototype.hasOwnProperty.call(context,'user');
 const legacy=window._feInjection;
 const user=known?context.user:legacy?.currentUser;
 if(/^[1-9]\d{0,19}$/.test(String(user?.uid||'')))owner=String(user.uid);
 else if(known&&context.user===null||legacy&&Object.prototype.hasOwnProperty.call(legacy,'currentUser')&&!legacy.currentUser)result.state='logged_out';
}
if(owner){result.owner=owner;result.state='logged_in';}
else if([...document.querySelectorAll('input[type="password"]')].some(node=>node.getClientRects().length))result.state='logged_out';
return result;
})()"""


def valid_identity(value, platform):
    if not isinstance(value, dict) or value.get('platform') != platform or platform not in SITES:
        return None
    try:
        page = urlsplit(value.get('url', ''))
        if (page.scheme != 'https' or page.hostname not in LOGIN_HOSTS[platform]
                or page.username or page.password or page.port not in (None, 443)):
            return None
    except (ValueError, TypeError):
        return None
    owner = value.get('owner')
    pattern = r'[1-9]\d{0,19}' if platform in ('牛客', '洛谷') else r'[A-Za-z0-9_.-]{1,64}'
    return owner if value.get('state') == 'logged_in' and isinstance(owner, str) and re.fullmatch(pattern, owner) else None


class PlatformLogins:
    def __init__(self, bridge, context, bind):
        self.bridge, self.context, self.bind = bridge, context, bind
        self.lock = threading.RLock()
        self.worker = None
        self.owner = None
        self.states = {platform: {'state': 'unknown', 'owner': ''} for platform in SITES}
        self.observed = {}
        self.started = weakref.WeakSet()
        self.busy = False

    def snapshot(self):
        with self.lock:
            return {'busy': self.busy, 'platforms': {key: dict(value) for key, value in self.states.items()}}

    def _current(self, owner):
        if self.bridge.stopping.is_set():
            return False
        try:
            return self.owner is owner and self.context() is owner
        except Exception:
            return False

    def start(self):
        owner = self.context()
        if owner is None:
            return {'started': False}
        with self.lock:
            if owner in self.started or self.worker and self.worker.is_alive() and self.owner is owner:
                return {'started': False}
            self.owner = owner
            self.started.add(owner)
            self.observed = {}
            self.busy = True
            self.worker = threading.Thread(target=self._run, args=(owner,), name='tb-platform-logins', daemon=True)
            self.worker.start()
        return {'started': True}

    def _accept(self, owner, platform, value):
        handle = valid_identity(value, platform)
        if not handle or not self._current(owner):
            return False
        if self.observed.get(platform) != handle:
            if not self.bind(owner, platform, handle):
                with self.lock:
                    self.states[platform] = {'state': 'mismatch', 'owner': ''}
                return False
            self.observed[platform] = handle
        with self.lock:
            self.states[platform] = {'state': 'logged_in', 'owner': handle}
        return True

    def _inspect(self, target, platform):
        from external_browser import DevToolsPage
        try:
            url = urlsplit(target.get('url', ''))
            if url.scheme != 'https' or url.hostname not in LOGIN_HOSTS[platform]:
                return None
            page = DevToolsPage(target['webSocketDebuggerUrl'], lambda *_: None)
            try:
                return page.evaluate(LOGIN_SCRIPT)
            finally:
                page.close()
        except Exception:
            return None

    def _probe(self, owner, platform):
        """Read existing tabs first, then one disposable, minimized home page."""
        from external_browser import DevToolsPage
        browser = self.bridge.browser
        for target in browser.request('/json/list'):
            value = self._inspect(target, platform)
            if self._accept(owner, platform, value):
                return True
        target = browser.new_submission_page()
        page = DevToolsPage(target['webSocketDebuggerUrl'], lambda *_: None)
        try:
            try:
                window = page.call('Browser.getWindowForTarget', {'targetId': target['id']})
                page.call('Browser.setWindowBounds', {'windowId': window['windowId'], 'bounds': {'windowState': 'minimized'}})
            except Exception:
                pass
            page.call('Page.navigate', {'url': SITES[platform][1]})
            deadline = time.monotonic() + 18
            while self._current(owner) and time.monotonic() < deadline:
                value = page.evaluate(LOGIN_SCRIPT)
                if self._accept(owner, platform, value):
                    return True
                if isinstance(value, dict) and value.get('state') == 'logged_out':
                    return False
                if self.bridge.stopping.wait(.6):
                    break
            return False
        finally:
            page.close()
            try:
                browser.close_page(target['id'])
            except Exception:
                pass

    def _wait_login(self, owner, platform, target):
        deadline = time.monotonic() + 600
        while self._current(owner) and time.monotonic() < deadline:
            current = next((item for item in self.bridge.browser.request('/json/list') if item.get('id') == target['id']), None)
            if current is None:
                return False  # Closing this login cancels the remaining popups.
            if self._accept(owner, platform, self._inspect(current, platform)):
                return True
            if self.bridge.stopping.wait(.8):
                break
        return False

    def _prepare(self, owner):
        self.bridge.browser.ensure(background=True)
        for platform in SITES:
            if not self._current(owner):
                return
            with self.lock:
                self.states[platform] = {'state': 'checking', 'owner': ''}
            if self._probe(owner, platform):
                continue
            if not self._current(owner):
                return
            # Never open the next site's login until this one succeeds.
            with self.lock:
                self.states[platform] = {'state': 'needs_login', 'owner': ''}
            target = self.bridge.browser.new_page(SITES[platform][2])
            if not self._wait_login(owner, platform, target):
                return

    def _run(self, owner):
        try:
            self._prepare(owner)
        except Exception:
            pass  # Explicit logins remain observable even after setup failed.
        finally:
            with self.lock:
                if self.owner is owner:
                    self.busy = False
        # Passive identity observation keeps manual official-site logins bound.
        while self._current(owner):
            try:
                for target in self.bridge.browser.request('/json/list')[:24]:
                    for platform in SITES:
                        value = self._inspect(target, platform)
                        if value is not None:
                            self._accept(owner, platform, value)
                            break
            except Exception:
                pass
            if self.bridge.stopping.wait(3):
                return
