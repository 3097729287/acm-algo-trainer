"""Remember only the managed browser's OJ cookies, encrypted for this Windows user."""
import base64
import json
import math
import time
from pathlib import Path

from persistence import load_document, save_document
from translation_config import _crypt

ROOTS = ('codeforces.com', 'atcoder.jp', 'nowcoder.com', 'luogu.com.cn', 'qoj.ac')
FIELDS = ('name', 'value', 'domain', 'path', 'secure', 'httpOnly', 'sameSite', 'expires', 'partitionKey')


def site_cookie(cookie):
    if not isinstance(cookie, dict):
        return None
    domain = str(cookie.get('domain', '')).lstrip('.').lower()
    root = next((root for root in ROOTS if domain == root or domain.endswith('.' + root)), None)
    if root is None:
        return None
    if any(not isinstance(cookie.get(key), str) or len(cookie[key]) > 8192 for key in ('name', 'value', 'domain', 'path')):
        return None
    if not cookie['path'].startswith('/') or any(char in cookie['name'] + domain for char in '\r\n\0'):
        return None
    expiration = cookie.get('expires', -1)
    if type(expiration) not in (int, float) or not math.isfinite(expiration) or expiration > 0 and expiration <= time.time():
        return None
    partition = cookie.get('partitionKey')
    if partition is not None:
        from urllib.parse import urlsplit
        if not isinstance(partition, dict) or partition.get('hasCrossSiteAncestor') is not False:
            return None
        site = urlsplit(partition.get('topLevelSite', ''))
        if site.scheme != 'https' or not (site.hostname == root or (site.hostname or '').endswith('.' + root)):
            return None
    item = {key: cookie[key] for key in FIELDS if key in cookie}
    if expiration <= 0:
        item.pop('expires', None)  # Restore a session cookie as a session cookie.
    return item


class BrowserLoginMemory:
    def __init__(self, directory, browser='edge', crypt=_crypt):
        self.path = Path(directory) / ('managed-login-' + browser + '.json')
        self.crypt = crypt
        self.signature = None

    def restore(self, page):
        try:
            protected = load_document(self.path, None)
            if not isinstance(protected, str) or len(protected) > 3_000_000:
                return
            value = json.loads(self.crypt(base64.b64decode(protected, validate=True), decrypt=True))
            if not 0 <= time.time() - value['savedAt'] <= 30 * 86400:
                return
            current = page.call('Storage.getCookies').get('cookies', [])
            keys = {(item.get('name'), item.get('domain'), item.get('path')) for item in current}
            cookies = [valid for item in value['cookies'] if (valid := site_cookie(item)) and
                       (valid['name'], valid['domain'], valid['path']) not in keys]
            if cookies:
                page.call('Storage.setCookies', {'cookies': cookies})
        except Exception:
            # Expired or undecryptable sessions require normal site login.
            # Never fall back to plaintext or the user's daily browser profile.
            return

    def capture(self, page):
        raw = page.call('Storage.getCookies').get('cookies', [])
        cookies = [item for cookie in raw[:1200] if (item := site_cookie(cookie))]
        cookies.sort(key=lambda item: (item['domain'], item['path'], item['name']))
        signature = json.dumps(cookies, sort_keys=True, separators=(',', ':'))
        if signature == self.signature:
            return
        data = json.dumps({'savedAt': time.time(), 'cookies': cookies}, separators=(',', ':')).encode()
        protected = self.crypt(data)
        save_document(self.path, base64.b64encode(protected).decode('ascii'))
        self.signature = signature
