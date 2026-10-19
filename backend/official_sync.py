"""Import owner-scoped official receipts independently of a TB submit attempt."""
import contextlib
import datetime as dt
import hashlib
import json
import logging
import os
import re
import threading
import urllib.request
from urllib.parse import quote, urlsplit

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
    def __init__(self, server, fetch=None, site_fetch=None):
        self.server = server
        self.fetch = fetch or self._fetch
        self.site_fetch = site_fetch
        client=getattr(server.store.extensions,'client',None)
        if fetch is None and site_fetch is None and client is not None:
            from site_receipts import PublicReceiptSource
            self.site_fetch = PublicReceiptSource(client).fetch
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
                self._owner()  # Require the active TB session before any work.
                training = self.server.training
                bindings = dict(self.server.store.extensions.snapshot().get('settings',{}).get('accounts',{}))
                with training.lock,training._library_view():rows=training._library()
            imported=0;platforms=[]
            for platform,handle in bindings.items():
                if not handle or platform!='codeforces' and not self.site_fetch:continue
                try:
                    with self._context():
                        current=self.server.store.extensions.snapshot().get('settings',{}).get('accounts',{})
                        if self.server.training is not training or current.get(platform)!=handle:return dict(self.status)
                        imported+=self.import_receipts(self._remember(training,platform,handle,[]))
                    receipts=cf_receipts(self.fetch(handle),handle) if platform=='codeforces' else self.site_fetch(platform,handle,rows)
                    with self._context():
                        # Both the TB workspace and the platform binding must
                        # still belong to the request that began this fetch.
                        current=self.server.store.extensions.snapshot().get('settings',{}).get('accounts',{})
                        if self.server.training is not training or current.get(platform)!=handle:return dict(self.status)
                        receipts=self._remember(training,platform,handle,receipts)
                        imported+=self.import_receipts(receipts)
                    platforms.append({'platform':platform,'status':'ready'})
                except Exception as error:
                    platforms.append({'platform':platform,'status':'error','message':'原站记录暂不可用，保留已有结果'})
                    LOG.debug('Official %s sync: %s',platform,type(error).__name__)
            self.status.update(imported=imported,platforms=platforms,
                message='官网提交已同步' if not any(item['status']=='error' for item in platforms) else '部分原站记录暂不可用，稍后重试')
            if any(item['status']=='ready' for item in platforms):self.status['lastSuccessAt']=dt.datetime.now(dt.timezone.utc).isoformat()
        except Exception as error:
            self.status['message'] = '官网提交同步暂不可用，稍后自动重试'
            LOG.debug('Official receipt sync: %s', type(error).__name__)
        finally:
            self.lock.release()
        return dict(self.status)

    @staticmethod
    def _remember(training,platform,owner,receipts):
        from persistence import load_document,save_document
        path=training.db_path.parent/'official-receipt-cache.json'
        cache=load_document(path,{})
        previous=cache.get(platform,{})
        existing=previous.get('records',[]) if previous.get('owner')==owner else []
        merged={row['submissionId']:row for row in existing}
        merged.update({row['submissionId']:row for row in receipts})
        value={'owner':owner,'records':sorted(merged.values(),key=lambda row:row['acceptedAt'])[-5000:]}
        if value!=previous:
            cache[platform]=value;save_document(path,cache)
        return value['records']

    def import_receipts(self, receipts):
        if not receipts:return 0
        training = self.server.training
        with training.lock, training._library_view():
            recorded={row[0] for row in training.connection.execute("SELECT id FROM submissions WHERE id LIKE 'official-%'")}
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
                remote_id='official-'+hashlib.sha256((str(urlsplit(row['url']).hostname)+'/'+str(receipt.get('submissionId'))).encode()).hexdigest()
                if remote_id in recorded:continue
                try:
                    before = training.connection.total_changes
                    training.record_official({'id': row['id'], 'url': row['url'], 'code': '', 'external': True}, receipt)
                    recorded.add(remote_id)
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
