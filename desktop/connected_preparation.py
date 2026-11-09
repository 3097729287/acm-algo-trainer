"""A compact connection entry for the user's own browser; no browser launch."""
import os
from pathlib import Path
import re

from platform_login import SITES
from official_bridge import submission_target
from training import ServiceError


class ConnectedPreparation:
    def __init__(self,bridge,extension_path,opener=None):
        self.bridge,self.path=bridge,Path(extension_path)
        self.opener=opener or os.startfile

    def snapshot(self):
        bridge=self.bridge
        expected_owners={platform:bridge.expected_owner(platform) if bridge.expected_owner else None for platform in SITES}
        with bridge.lock:
            clients=[key for key in bridge.clients if bridge.client_protocols.get(key)==4 and bridge.client_windows.get(key)
                     and bridge.clock()-bridge.client_seen.get(key,-100)<=6]
            versions=sorted({bridge.client_versions.get(key,'') for key in clients})
            brands=sorted({bridge.brands.get(key,'chrome') for key in clients})
            platforms=[]
            for platform,(_,_,url) in SITES.items():
                expected=expected_owners[platform]
                client=bridge._client(platform,expected)
                platforms.append({'platform':platform,'state':bridge.client_login_states.get(client,{}).get(platform,'unknown'),'loginUrl':url})
        return {'available':True,'mode':'tabs','ready':bool(clients),'extensionPath':str(self.path),
            'extension':{'installed':bool(clients),'connected':bool(clients),'versions':versions},
            'preferredBrowser':brands[0] if len(brands)==1 else '',
            'browsers':[{'id':brand,'available':True} for brand in brands],
            'platforms':platforms,'manualLoadRequired':not clients}

    def check_submission(self,url):
        target=submission_target(url)
        expected=self.bridge.expected_owner(target['platform']) if self.bridge.expected_owner else None
        with self.bridge.lock:
            if not self.bridge._client(target['platform'],expected):
                raise ServiceError(412,'请在账号设置的“浏览器连接”加载扩展，再继续提交；不会另开独立登录')

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
