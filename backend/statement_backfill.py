"""Resumable public statement supplementation; never touches training records."""
import json
import logging
import os
import threading
import time
from urllib.parse import urlsplit

from contest_policy import content_ready
from integrations import PublicClient
from persistence import load_document, save_document
import public_platforms

LOG = logging.getLogger('tb.statements')


class StatementBackfill:
    def __init__(self, store, state_dir, client=None, clock=time.time):
        self.store = store
        self.path = state_dir / 'statement-backfill.json'
        self.stop = threading.Event()
        self.lock = threading.RLock()
        self.client = client or PublicClient(state_dir / 'statement-backfill', self.stop, spacing=2)
        self.clock = clock
        self.thread = None
        self.failures = load_document(self.path, {}).get('failures', {})
        self.host_retry = {}
        self._pending = None
        self.status = {'running': False, 'added': 0, 'remaining': None, 'message': '等待检查公开题面'}

    def pending(self):
        with self.store.library.connection() as db:
            # Existing valid statements/translations are never replaced.
            from library import _CONTENT_READY_SQL
            rows = db.execute('SELECT p.id,p.url,p.encoded FROM problems p WHERE NOT (' + _CONTENT_READY_SQL + ')').fetchall()
        return [(row['id'], row['url'], json.loads(row['encoded']).get('title') or row['id'])
                for row in rows if row['url'] and urlsplit(row['url']).hostname in
                {'codeforces.com', 'atcoder.jp', 'www.luogu.com.cn', 'luogu.com.cn', 'ac.nowcoder.com'}]

    def once(self):
        if self._pending is None:
            self._pending = self.pending()
        pending = self._pending
        with self.lock:
            self.status['remaining'] = len(pending)
        for identity, url, title in pending:
            if self.stop.is_set():
                return False
            now, host = self.clock(), urlsplit(url).hostname
            if self.failures.get(identity, 0) > now or self.host_retry.get(host, 0) > now:
                continue
            try:
                value = self.store.library.statement(identity)
                if not content_ready(value):
                    value = public_platforms.statement(self.client, identity, title, url)
                if not content_ready(value):
                    raise ValueError('原站尚未返回完整题面与样例')
                if self.stop.is_set():
                    return False
                self.store.library.save_statement(identity, value)
                self._pending.remove((identity, url, title))
                self.failures.pop(identity, None)
                with self.lock:
                    self.status['added'] += 1
                    self.status['remaining'] -= 1
                    self.status['message'] = '正在补全公开题面，关闭后下次继续'
            except Exception as issue:
                self.failures[identity] = now + 86400
                # Avoid repeated requests to a rejecting/unavailable site.
                if not isinstance(issue, ValueError):
                    self.host_retry[host] = now + 1800
                with self.lock:
                    self.status['message'] = '部分原站暂不可读取，已有题面可正常使用'
                LOG.debug('Statement backfill %s: %s', identity, type(issue).__name__)
            try:
                save_document(self.path, {'failures': self.failures})
            except (OSError, RuntimeError, ValueError):
                LOG.debug('Could not persist statement retry cursor')
            return True
        with self.lock:
            self.status['message'] = '公开题面已补齐' if not pending else '其余题面等待原站开放，稍后自动重试'
        self._pending = None
        return False

    def _loop(self):
        while not self.stop.is_set():
            try:
                active = self.once()
            except Exception:
                LOG.exception('Statement supplementation interrupted')
                active = False
            if self.stop.wait(3 if active else 300):
                break
        with self.lock:
            self.status['running'] = False

    def start(self):
        if os.environ.get('TB_OFFLINE') == '1' or self.thread:
            return
        self.status['running'] = True
        self.thread = threading.Thread(target=self._loop, name='TB-statement-backfill', daemon=True)
        self.thread.start()

    def snapshot(self):
        with self.lock:
            return dict(self.status)

    def close(self):
        self.stop.set()
