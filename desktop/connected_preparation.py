"""Reuse the user's registered browser and wake it silently on submit intent."""
import os
from pathlib import Path
import re
import sys
import threading
import time

from platform_login import SITES
from official_bridge import submission_target
from training import ServiceError


def connector_bundle_path(app_dir,state,port):
    if not getattr(sys,'frozen',False):
        from browser_extension_bundle import build
        return build(Path(state).parent/'cache'/'tb-connected-extension','http://127.0.0.1:'+str(port))
    # Assemble already generated official.js/identity.js. A frozen program
    # uses these exact shipped bytes and never needs raw underscore sources.
    # Missing optional connection assets do not prevent ordinary offline work.
    # The connection entry reports the missing directory on explicit use.
    return Path(app_dir)/'browser-extension'


class ConnectedPreparation:
    def __init__(self,bridge,extension_path,opener=None,*,waker=None,clock=None,profiles=None):
        self.bridge,self.path=bridge,Path(extension_path)
        self.opener=opener or os.startfile
        self.waker=waker or self._wake_registered
        self.clock=clock or time.monotonic
        self.profiles=profiles or self._registered_profiles
        self.wake_lock=threading.Lock()
        self.wake_at=float('-inf')
        self.wake_started=False
        self.profile_cache=[]
        self.profile_at=float('-inf')

    @staticmethod
    def _registered_profiles():
        if os.environ.get('TB_OFFLINE')=='1':return []
        from silent_browser import registered_browsers
        return list(registered_browsers())

    @staticmethod
    def _wake_registered():
        from silent_browser import wake_browser
        return wake_browser(unique=True)

    def snapshot(self):
        bridge=self.bridge
        with self.wake_lock:
            if self.clock()-self.profile_at>=30:
                try:self.profile_cache=list(self.profiles())
                except (OSError,ValueError):self.profile_cache=[]
                self.profile_at=self.clock()
            registered=list(self.profile_cache)
        expected_owners={platform:bridge.expected_owner(platform) if bridge.expected_owner else None for platform in SITES}
        with bridge.lock:
            clients=[key for key in bridge.clients if bridge.client_protocols.get(key)==4 and bridge._can_run(key)
                     and bridge.clock()-bridge.client_seen.get(key,-100)<=6]
            versions=sorted({bridge.client_versions.get(key,'') for key in clients})
            brands=sorted({bridge.brands.get(key,'chrome') for key in clients})
            platforms=[]
            for platform,(_,_,url) in SITES.items():
                expected=expected_owners[platform]
                client=bridge._client(platform,expected)
                platforms.append({'platform':platform,'state':bridge.client_login_states.get(client,{}).get(platform,'unknown'),'loginUrl':url})
        installed=bool(clients or registered)
        return {'available':True,'mode':'tabs','ready':bool(clients) or len(registered)==1,'extensionPath':str(self.path),
            'extension':{'installed':installed,'connected':bool(clients),'versions':versions},
            'preferredBrowser':brands[0] if len(brands)==1 else '',
            'browsers':[{'id':brand,'available':True} for brand in brands],
            'platforms':platforms,'manualLoadRequired':not installed,'automaticStartup':True}

    def check_submission(self,url):
        target=submission_target(url)
        expected=self.bridge.expected_owner(target['platform']) if self.bridge.expected_owner else None
        with self.bridge.lock:
            if self.bridge._client(target['platform'],expected):return
        # Do not wait for the extension while the HTTP account barrier is held:
        # its authenticated queue needs that same barrier to finish connecting.
        # One explicit submit starts one bounded wake attempt; idle refreshes
        # never launch a browser, create a login or touch another profile.
        with self.wake_lock:
            if self.clock()-self.wake_at>=10:
                self.wake_at=self.clock()
                try:self.wake_started=bool(self.waker())
                except OSError:self.wake_started=False
            if not self.wake_started:
                raise ServiceError(412,'尚未找到可自动连接的常用浏览器。首次在账号设置启用浏览器连接后，提交会自动静默启动，无需预先打开浏览器。')
        self.bridge.note_automatic_start()

    def action(self,body):
        action=body.get('action')
        if action in ('refresh','startup-logins') and set(body)=={'action'}:
            # Startup reads connection metadata only. No login preheat or tabs.
            return self.snapshot()
        if action=='open-folder' and set(body)=={'action'}:
            if not (self.path/'manifest.json').is_file():raise ServiceError(503,'浏览器连接目录缺失，请重新完整安装 ToBe')
            self.opener(str(self.path));return {'opened':True}
        if action=='open-extensions' and set(body)<= {'action','browser'}:
            brand=body.get('browser','chrome')
            if brand not in ('edge','chrome'):raise ServiceError(400,'请选择 Chrome 或 Edge')
            return {'opened':False,'url':brand+'://extensions','extensionPath':str(self.path)}
        if action=='open-login' and set(body)<= {'action','browser','platform'}:
            platform=body.get('platform')
            if platform not in SITES:raise ServiceError(400,'请选择支持的平台')
            owner=self.bridge.current_owner() if self.bridge.current_owner else None
            page=self.bridge.page(SITES[platform][2],owner,platform,manual=True)
            with self.bridge.lock:
                session=self.bridge.sessions[page.identity]
                session['command']=1;session['controlRequest']={'kind':'identity'}
            return {'opened':True}
        if action=='open-contest' and set(body)=={'action','url'}:
            url=body.get('url')
            if not isinstance(url,str) or not re.fullmatch(r'https://ac\.nowcoder\.com/acm/contest/[1-9]\d*',url):raise ServiceError(400,'牛客比赛原站地址无效')
            owner=self.bridge.current_owner() if self.bridge.current_owner else None
            page=self.bridge.page(url,owner,'牛客',manual=True)
            with self.bridge.lock:
                session=self.bridge.sessions[page.identity]
                session['command']=1;session['controlRequest']={'kind':'identity'}
            return {'opened':True}
        raise ServiceError(400,'浏览器连接操作无效')
