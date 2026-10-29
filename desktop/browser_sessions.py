"""User-authorized OJ login sync. Explicit site scopes, encrypted by Windows DPAPI."""
import json
import math
import secrets
import threading
import time
from pathlib import Path
from urllib.parse import urlsplit

from training import ServiceError
from translation_config import _crypt

DOMAINS = {'Codeforces': ('codeforces.com',), 'AtCoder': ('atcoder.jp',),
           '牛客': ('nowcoder.com',), '洛谷': ('luogu.com.cn',), 'QOJ': ('qoj.ac',)}
LOGIN_STATES = {'logged_in', 'logged_out', 'unknown'}


def live_cookies(snapshot):
    return [cookie for cookie in (snapshot or {}).get('cookies', [])
            if cookie.get('value') and cookie.get('expirationDate', float('inf')) > time.time()]


def first_party_partition(platform, partition):
    if partition is None:
        return True
    if (not isinstance(partition, dict) or not isinstance(partition.get('topLevelSite'), str)
            or partition.get('hasCrossSiteAncestor') not in (None, False)):
        return False
    try:
        site = urlsplit(partition.get('topLevelSite', ''))
        return (site.scheme == 'https' and not site.username and not site.password and site.port in (None, 443)
                and any(site.hostname == root or (site.hostname or '').endswith('.' + root) for root in DOMAINS[platform]))
    except (ValueError, TypeError):
        return False


class BrowserSessions:
    def __init__(self, path, crypt=_crypt):
        self.path, self.crypt = Path(path), crypt
        self.lock = threading.RLock()
        self.pending, self.snapshots = {}, {}
        try:
            self.snapshots = json.loads(crypt(self.path.read_bytes(), decrypt=True))
        except (OSError, ValueError, ServiceError):
            pass

    def request(self, platform):
        with self.lock:
            current = self.pending.get(platform)
            if not current or current['event'].is_set() or time.monotonic() - current['at'] >= 30:
                self.pending[platform] = {'nonce': secrets.token_urlsafe(24), 'event': threading.Event(), 'at': time.monotonic()}
            return self.pending[platform]['event']

    def requests(self):
        with self.lock:
            return [{'platform': p, 'nonce': v['nonce'], 'domains': list(DOMAINS[p])}
                    for p, v in self.pending.items() if not v['event'].is_set() and time.monotonic() - v['at'] < 30]

    def accept(self, body):
        platform, nonce = body.get('platform'), body.get('nonce')
        with self.lock:
            request = self.pending.get(platform)
            if not request or not isinstance(nonce, str) or not secrets.compare_digest(request['nonce'], nonce):
                raise ServiceError(403, '登录同步请求已失效')
            if request['event'].is_set():
                return {'ok': True}
            raw = body.get('cookies')
            if not isinstance(raw, list) or len(raw) > 300:
                raise ServiceError(400, '登录同步数据无效')
            cookies = []
            for cookie in raw:
                if not isinstance(cookie, dict):
                    raise ServiceError(400, '登录同步数据无效')
                domain = str(cookie.get('domain', '')).lstrip('.').lower()
                if not any(domain == root or domain.endswith('.' + root) for root in DOMAINS[platform]):
                    raise ServiceError(400, '拒绝同步其它网站的登录数据')
                if not first_party_partition(platform, cookie.get('partitionKey')):
                    continue
                item = {k: cookie[k] for k in ('name', 'value', 'domain', 'path', 'secure', 'httpOnly', 'sameSite', 'expirationDate') if k in cookie}
                if any(not isinstance(item.get(k), str) or len(item[k]) > 8192 for k in ('name', 'value', 'domain', 'path')):
                    raise ServiceError(400, '登录同步数据无效')
                if not item['path'].startswith('/') or any(c in item['name'] + item['domain'] for c in '\r\n\0'):
                    raise ServiceError(400, '登录同步数据无效')
                expires = item.get('expirationDate')
                if expires is not None and (not isinstance(expires, (int, float)) or not math.isfinite(expires)):
                    raise ServiceError(400, '登录同步数据无效')
                if expires is None or expires > time.time():
                    cookies.append(item)
            agent = body.get('userAgent', '')
            if not isinstance(agent, str) or len(agent) > 512 or any(c in agent for c in '\r\n\0'):
                raise ServiceError(400, '浏览器版本信息无效')
            state = body.get('loginState', 'unknown')
            if not isinstance(state, str) or state not in LOGIN_STATES:
                raise ServiceError(400, '浏览器登录状态无效')
            snapshot = {'cookies': cookies, 'userAgent': agent, 'at': time.time(),
                        'loginState': state, 'clientId': body.get('clientId', '')}
            updated = {**self.snapshots, platform: snapshot}
            self._save(updated)
            request['event'].set()
            return {'ok': True}

    def _save(self, updated):
        encrypted = self.crypt(json.dumps(updated, ensure_ascii=True).encode())
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix('.tmp')
        temporary.write_bytes(encrypted)
        temporary.replace(self.path)
        self.snapshots = updated

    def update_login_states(self, client, states):
        # Persist only metadata from the profile that supplied this exact
        # snapshot. Restarting TB must not discard a previously confirmed login.
        with self.lock:
            updated = dict(self.snapshots)
            for platform, state in states.items():
                current = updated.get(platform)
                if (current and current.get('clientId') == client and state in LOGIN_STATES
                        and state != current.get('loginState')):
                    updated[platform] = {**current, 'loginState': state}
            if updated != self.snapshots:
                self._save(updated)

    def snapshot(self, platform):
        with self.lock:
            value = self.snapshots.get(platform)
            if not isinstance(value, dict) or time.time() - value.get('at', 0) > 7 * 86400:
                return None
            return json.loads(json.dumps(value))

    def finish(self, platform):
        with self.lock:
            self.pending.pop(platform, None)
