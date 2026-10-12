"""Public preparation status and explicit user actions; never returns cookies."""
import os
from pathlib import Path
import subprocess
import threading
import time

from browser_sessions import DOMAINS
from silent_browser import registered_browsers, wake_browser
from training import ServiceError

LOGIN_URLS = {'Codeforces': 'https://codeforces.com/enter', 'AtCoder': 'https://atcoder.jp/login',
              '牛客': 'https://ac.nowcoder.com/login', '洛谷': 'https://www.luogu.com.cn/auth/login'}


class BrowserPreparation:
    def __init__(self, bridge, extension_path, profiles=registered_browsers, opener=None):
        self.bridge, self.path, self.profiles = bridge, Path(extension_path), profiles
        self.opener = opener or self._open
        self.lock = threading.RLock()
        self.profile_cache, self.profile_at = [], float('-inf')

    def _profiles(self, force=False):
        with self.lock:
            if force or time.monotonic() - self.profile_at > 5:
                self.profile_cache = list(self.profiles())
                self.profile_at = time.monotonic()
            return list(self.profile_cache)

    @staticmethod
    def _executables():
        return {'edge': Path(os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)')) / 'Microsoft/Edge/Application/msedge.exe',
                'chrome': Path(os.environ.get('PROGRAMFILES', 'C:/Program Files')) / 'Google/Chrome/Application/chrome.exe'}

    def snapshot(self):
        bridge = self.bridge
        profiles = self._profiles()
        with bridge.lock:
            connected = any(bridge.clock() - at <= 6 for at in bridge.client_seen.values())
            states = dict(bridge.client_login_states.get(bridge.sync_client, {}))
            versions = [bridge.client_versions.get(client, '') for client, at in bridge.client_seen.items()
                        if bridge.clock() - at <= 6]
        installed = bool(profiles) or connected
        platforms = []
        for platform in DOMAINS:
            cached = bridge.session_store.snapshot(platform) if bridge.session_store else None
            state = states.get(platform, 'unknown')
            if cached is None:
                state = 'not_synced'
            elif not any(cookie.get('value') and cookie.get('expirationDate', float('inf')) > time.time()
                         for cookie in cached.get('cookies', [])):
                state = 'logged_out'
            platforms.append({'platform': platform, 'state': state, 'loginUrl': LOGIN_URLS[platform]})
        return {'available': True, 'extensionPath': str(self.path),
                'extension': {'installed': installed, 'connected': connected, 'versions': versions},
                'browsers': [{'id': key, 'name': 'Microsoft Edge' if key == 'edge' else 'Google Chrome',
                              'available': path.is_file()} for key, path in self._executables().items()],
                'platforms': platforms, 'ready': installed and all(p['state'] == 'logged_in' for p in platforms)}

    def check_submission(self, url):
        from official_bridge import submission_target
        platform = submission_target(url)['platform']
        value = self.snapshot()
        state = next(p['state'] for p in value['platforms'] if p['platform'] == platform)
        if not value['extension']['installed']:
            raise ServiceError(412, '请先安装并启用 TB 浏览器连接扩展，按“浏览器提交准备”中的步骤操作')
        if state in ('not_synced', 'logged_out'):
            raise ServiceError(412, '请先在安装了 TB 扩展的浏览器登录 ' + platform + '，再回 TB 重新检测')

    def action(self, body):
        action = body.get('action')
        if set(body) - {'action', 'browser', 'platform'}:
            raise ServiceError(400, '浏览器准备请求无效')
        if action == 'refresh':
            self._profiles(force=True)
            if self.bridge.session_store:
                for platform in DOMAINS:
                    self.bridge.session_store.request(platform)
            threading.Thread(target=wake_browser, daemon=True).start()
            return {**self.snapshot(), 'checking': True}
        if action == 'open-folder':
            if not (self.path / 'manifest.json').is_file():
                raise ServiceError(503, '浏览器连接扩展文件缺失，请重新完整安装 TB')
            self.opener('folder', self.path, None)
        elif action in ('open-extensions', 'open-login'):
            browser = body.get('browser')
            if browser not in self._executables():
                raise ServiceError(400, '请选择 Edge 或 Chrome')
            if action == 'open-login':
                platform = body.get('platform')
                if platform not in LOGIN_URLS:
                    raise ServiceError(400, '请选择支持的竞赛平台')
                url = LOGIN_URLS[platform]
            else:
                url = 'edge://extensions' if browser == 'edge' else 'chrome://extensions'
            self.opener(browser, url, self._profiles())
        else:
            raise ServiceError(400, '浏览器准备操作无效')
        return {'opened': True}

    def _open(self, browser, target, profiles):
        if browser == 'folder':
            os.startfile(str(target))
            return
        executable = self._executables()[browser]
        if not executable.is_file():
            raise ServiceError(404, '没有找到所选浏览器，请在浏览器地址栏手动打开说明中的地址')
        profile = next((name for path, name in profiles if Path(path) == executable), None)
        args = [str(executable), *(['--profile-directory=' + profile] if profile else []), str(target)]
        subprocess.Popen(args, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
