"""Import owner-scoped official receipts independently of a TB submit attempt."""
import contextlib
import datetime as dt
import json
import logging
import os
import re
import threading
import urllib.request
from urllib.parse import quote

from insights import canonical_url
from training import ServiceError

LOG = logging.getLogger('tb.official-sync')
CF_VERDICTS = {'OK': 'AC', 'WRONG_ANSWER': 'WA', 'TIME_LIMIT_EXCEEDED': 'TLE',
               'MEMORY_LIMIT_EXCEEDED': 'MLE', 'RUNTIME_ERROR': 'RE',
               'COMPILATION_ERROR': 'CE', 'OUTPUT_LIMIT_EXCEEDED': 'OLE'}


def cf_receipts(payload, handle):
    if not isinstance(payload, dict) or payload.get('status') != 'OK' or not isinstance(payload.get('result'), list):
        raise ValueError('Codeforces 提交记录暂不可用')
    result = []
    for row in payload['result']:
        problem = row.get('problem') or {}
        identity, cid, index = row.get('id'), problem.get('contestId'), problem.get('index')
        verdict, created = CF_VERDICTS.get(row.get('verdict')), row.get('creationTimeSeconds')
        members = (row.get('author') or {}).get('members') or []
        if (type(identity) is not int or identity <= 0 or type(cid) is not int or cid <= 0
                or not re.fullmatch(r'[A-Za-z]\d?', str(index)) or not verdict
                or type(created) is not int or not 0 < created <= dt.datetime.now(dt.timezone.utc).timestamp() + 300
                or not any(str(m.get('handle', '')).casefold() == handle.casefold() for m in members)):
            continue
        result.append({'platform': 'Codeforces', 'owner': handle, 'submissionId': str(identity),
                       'url': f'https://codeforces.com/{"gym" if cid >= 100000 else "contest"}/{cid}/problem/{index.upper()}',
                       'verdict': verdict, 'status': 'finished',
                       'acceptedAt': dt.datetime.fromtimestamp(created, dt.timezone.utc).isoformat(),
                       'message': '官网提交同步；原站未提供源码'})
    return result


class OfficialSync:
    def __init__(self, server, fetch=None):
        self.server = server
        self.fetch = fetch or self._fetch
        self.stop = threading.Event()
        self.lock = threading.Lock()
        self.thread = None
        self.status = {'lastSuccessAt': None, 'imported': 0, 'message': '等待同步官网提交'}

    @staticmethod
    def _fetch(handle):
        url = 'https://codeforces.com/api/user.status?handle=' + quote(handle, safe='') + '&from=1&count=1000'
        request = urllib.request.Request(url, headers={'User-Agent': 'TB official receipt sync', 'Accept': 'application/json'})
        with urllib.request.urlopen(request, timeout=12) as response:
            return json.loads(response.read(8 * 1024 * 1024))

    def start(self):
        if os.environ.get('TB_OFFLINE') == '1' or self.thread:
            return
        self.thread = threading.Thread(target=self._loop, name='tb-official-sync', daemon=True)
        self.thread.start()

    def _context(self):
        accounts = getattr(self.server, 'accounts', None)
        return accounts.request_context() if accounts else contextlib.nullcontext()

    def _owner(self):
        accounts = getattr(self.server, 'accounts', None)
        if accounts:
            accounts.require()
        hub = self.server.store.extensions.snapshot()
        return hub.get('settings', {}).get('accounts', {}).get('codeforces', '').strip()

    def once(self):
        if not self.lock.acquire(blocking=False):
            return dict(self.status)
        try:
            with self._context():
                handle, training = self._owner(), self.server.training
            if not handle:
                return dict(self.status)
            receipts = cf_receipts(self.fetch(handle), handle)
            with self._context():
                # A logout/account switch while the GET was in flight must not
                # attach the old owner's submissions to the new workspace.
                if self.server.training is not training or self._owner() != handle:
                    return dict(self.status)
                imported = self.import_receipts(receipts)
            self.status.update(lastSuccessAt=dt.datetime.now(dt.timezone.utc).isoformat(),
                               imported=imported, message='官网提交已同步')
        except Exception as error:
            self.status['message'] = '官网提交同步暂不可用，稍后自动重试'
            LOG.debug('Official receipt sync: %s', type(error).__name__)
        finally:
            self.lock.release()
        return dict(self.status)

    def import_receipts(self, receipts):
        training = self.server.training
        with training.lock, training._library_view():
            rows = {}
            for row in training._library():
                key = canonical_url(row.get('url'))
                if key:
                    rows.setdefault(key, row)
            imported = 0
            for receipt in sorted(receipts, key=lambda r: r.get('acceptedAt', '')):
                row = rows.get(canonical_url(receipt.get('url')))
                if not row:
                    continue
                try:
                    before = training.connection.total_changes
                    training.record_official({'id': row['id'], 'url': row['url'], 'code': '', 'external': True}, receipt)
                    imported += int(training.connection.total_changes > before)
                except ServiceError as error:
                    if error.status not in (403, 404, 409):
                        raise
                    continue
                bridge = getattr(self.server, 'browser_bridge', None)
                if bridge and hasattr(bridge, 'observe_receipt'):
                    bridge.observe_receipt(receipt)
            return imported

    def from_browser(self, body):
        """Only the authenticated extension sends this; bind to configured owner."""
        platform, owner, records = body.get('platform'), body.get('owner'), body.get('records')
        sites = {
            'Codeforces': ('codeforces', r'https://(?:www\.)?codeforces.com/(?:contest|gym)/\d+/problem/[A-Za-z]\d?'),
            'AtCoder': ('atcoder', r'https://atcoder.jp/contests/[\w-]+/tasks/[\w-]+'),
            '牛客': ('nowcoder', r'https://ac.nowcoder.com/acm/contest/\d+/[A-Za-z]\d?'),
            '洛谷': ('luogu', r'https://(?:www\.)?luogu.com.cn/problem/[A-Za-z0-9_-]+'),
        }
        if platform not in sites or not isinstance(owner, str) or not isinstance(records, list) or len(records) > 100:
            raise ServiceError(400, '官网提交记录格式无效')
        account, pattern = sites[platform]
        expected = str(self.server.store.extensions.snapshot().get('settings', {}).get('accounts', {}).get(account, ''))
        if not expected or expected.casefold() != owner.casefold():
            raise ServiceError(403, '官网提交账号与当前配置不一致')
        accepted = []
        for row in records:
            if not isinstance(row, dict):
                continue
            url = str(row.get('url', '')).split('#')[0].split('?')[0]
            if (not re.fullmatch(pattern, url)
                    or not re.fullmatch(r'[1-9]\d{0,19}', str(row.get('submissionId', '')))
                    or row.get('verdict') not in set(CF_VERDICTS.values())):
                continue
            try:
                date = dt.datetime.fromisoformat(row['acceptedAt'])
                if date.tzinfo is None or date.timestamp() > dt.datetime.now(dt.timezone.utc).timestamp() + 300:
                    continue
            except (ValueError, TypeError, KeyError):
                continue
            accepted.append({**row, 'url':url, 'platform':platform, 'owner':owner, 'status':'finished'})
        return {'imported': self.import_receipts(accepted)}

    def _loop(self):
        while not self.stop.is_set():
            self.once()
            self.stop.wait(15)

    def close(self):
        self.stop.set()
