"""Read-only original statements and AST samples; explicit reviewed local profiles."""
import hashlib
import json
from functools import lru_cache
from pathlib import Path
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit
import reviewed_cases

class AssetLibrary:
    def __init__(self,store,cache_dir=None,portable=None):
        self.store=store
        self.lock=threading.RLock()
        self.cache_dir=Path(cache_dir) if cache_dir else __import__('paths').STATE/'tb-problem-assets'
        self._candidate_rows=None
        self._public_client=None
        self._fetch_stop=threading.Event()
        self._fetches={}
        self._fetch_errors={}
        self._fetch_executor=None
        self._closed=False
        self.portable=portable

    def _row(self,identity):
        row=(self._candidate_rows or {}).get(identity)
        if row is not None:return row
        try:return self.store.row(identity)
        except Exception as error:
            if getattr(error,'status',None)!=404:raise
            fact=self.portable(identity) if self.portable else None
            if fact and fact.get('raw'):return fact['raw']
            raise

    def _cache_path(self,identity):
        return self.cache_dir/(hashlib.sha256(identity.encode('utf-8')).hexdigest()+'.json')

    def _paths(self,identity):
        import toolutil
        row=self._row(identity)
        if row.get('_remote'):return row,None
        series,number=toolutil.parse_contest(row['场次'])
        directory,_=toolutil.contest_paths(self.store.data_root,series,number)
        return row,Path(directory) if directory else None

    @lru_cache(maxsize=256)
    def _cached(self,identity):
        value=self.store.library.statement(identity)
        if value:return value
        fact=self.portable(identity) if self.portable else None
        if fact and fact.get('statement'):return fact['statement']
        row=self._row(identity)
        found=self.store.library.find(identity,row.get('_url'))
        value=self.store.library.statement(found['id'] if found else identity)
        if value:return value
        if row.get('_remote'):return self.store.extensions.statement(identity,fetch=False)
        available,url=self.store._archive_info(row)
        return {'id':identity,'title':row['题名'],'markdown':None,'url':url,'samples':[],
                'limits':{'timeMs':2000,'memoryMb':256},'statementAvailable':False}

    def problem(self,identity,fetch=True):
        with self.lock:
            value=dict(self._cached(identity))
        if fetch and not value['statementAvailable'] and value['url']:
            fetched=self._fetch_statement(identity,value)
            with self.lock:
                value=dict(self._cached(identity))
                if fetched and fetched.get('statementError'):value['statementError']=fetched['statementError']
        bundle=self.bundle(identity)
        value.update(judge={'scope':bundle['scope'],'label':'本地审核测试' if bundle['scope']=='local' else '仅官方样例', 'cases':len(bundle['cases'])},locked=False,draft='',submissions=[])
        return value

    def _fetch_statement(self,identity,value):
        # Never hold the shared asset lock while waiting for the original site.
        # A blocked CF page must not block cached statements or other platforms.
        if identity.startswith('remote:') and not self.store.library.find(identity):
            fetched=self.store.extensions.statement(identity,fetch=True)
            with self.lock:
                self._cached.cache_clear();self.bundle.cache_clear()
            return fetched
        return self._fetch_missing(identity,value)

    def background_problem(self,identity,refresh=False):
        """Return cached content/draft immediately; bound slow public fetching."""
        value=self.problem(identity,fetch=False)
        if value['statementAvailable'] or not value.get('url'):
            return value
        with self.lock:
            if refresh:self._fetch_errors.pop(identity,None)
            failed=self._fetch_errors.get(identity)
            pending=self._fetches.get(identity)
            if pending is None and not self._closed and (not failed or time.monotonic()-failed[0]>=60):
                # Keep the queue bounded even when repeatedly opening missing
                # historical pages; public discovery owns its separate budget.
                if len(self._fetches)<4:
                    if self._fetch_executor is None:
                        self._fetch_executor=ThreadPoolExecutor(max_workers=2,thread_name_prefix='tb-statement')
                    pending=self._fetch_executor.submit(self._background_fetch,identity,dict(value))
                    self._fetches[identity]=pending
                    pending.add_done_callback(lambda future:self._finish_fetch(identity,future))
                else:
                    value['statementError']='正在读取其他题面，请稍后重试。'
            value['statementLoading']=pending is not None
            if failed and pending is None:value['statementError']=failed[1]
        return value

    def _background_fetch(self,identity,value):
        try:
            fetched=self._fetch_statement(identity,value)
            if fetched and fetched.get('statementError'):
                return fetched['statementError']
            with self.lock:
                if self._cached(identity).get('statementAvailable'):
                    return None
            return '原站暂未返回可用题面，请稍后重试。'
        except (OSError,ValueError,RuntimeError) as error:
            return str(error)[:250]

    def _finish_fetch(self,identity,future):
        try:error=future.result()
        except Exception:error='原站题面读取未完成，请稍后重试。'
        with self.lock:
            if self._fetches.get(identity) is future:self._fetches.pop(identity,None)
            if error:self._fetch_errors[identity]=(time.monotonic(),error)
            else:self._fetch_errors.pop(identity,None)
            # Negative results should stay small during long practice sessions.
            while len(self._fetch_errors)>128:self._fetch_errors.pop(next(iter(self._fetch_errors)))

    def close(self):
        with self.lock:
            self._closed=True
            executor=self._fetch_executor
            client=self._public_client
            self._fetch_stop.set()
        if client is not None:client.stop.set()
        if executor is not None:executor.shutdown(wait=True,cancel_futures=True)
        with self.lock:
            self._cached.cache_clear();self.bundle.cache_clear()
            self._fetches.clear();self._fetch_errors.clear();self._candidate_rows=None

    def _fetch_missing(self,identity,value):
        """Only an explicit single-problem opening fetches; preview never does network I/O."""
        parsed=urlsplit(value['url'])
        if parsed.hostname in ('codeforces.com','atcoder.jp','www.luogu.com.cn','ac.nowcoder.com'):
            try:
                from integrations import PublicClient
                from public_platforms import statement
                with self.lock:
                    if self._closed:return {'statementError':'题面服务已关闭'}
                    if self._public_client is None:self._public_client=PublicClient(self.cache_dir,stop=self._fetch_stop)
                    client=self._public_client
                saved=statement(client,identity,value['title'],value['url'])
                self.cache_dir.mkdir(parents=True,exist_ok=True)
                self.store.library.save_statement(identity,saved)
                # SQLite transaction above owns the fetched statement cache.
                with self.lock:
                    self._cached.cache_clear();self.bundle.cache_clear()
                return saved
            except (OSError,ValueError,RuntimeError) as error:return {'statementError':str(error)[:250]}
    def localized_statement(self,identity):
        """On demand, refresh old Luogu caches that predate site translations."""
        with self.lock:
            value=dict(self._cached(identity))
        if urlsplit(value.get('url') or '').hostname!='www.luogu.com.cn':return None
        if value.get('statementVersion',0)<2:
            if identity.startswith('remote:') and not self.store.library.find(identity):
                self.store.extensions.statement(identity,fetch=True,refresh=True)
                with self.lock:
                    self._cached.cache_clear();self.bundle.cache_clear()
            else:self._fetch_missing(identity,value)
            with self.lock:
                value=dict(self._cached(identity))
        return value.get('translation')

    @lru_cache(maxsize=32)
    def bundle(self,identity):
        base=self._cached(identity)
        cases=list(base['samples']);checker=None
        local=False
        # A profile alone is insufficient: original statement and samples must also exist.
        if identity in reviewed_cases.PROFILES and base['statementAvailable'] and cases:
            extra,checker=reviewed_cases.build(identity)
            if extra:cases+=extra;local=True
        return {'scope':'local' if local else 'samples','cases':cases,'limits':dict(base['limits']),
                'checker':checker,'nonunique':bool(re.search(r'(?:multiple (?:sequences|solutions)|output any|any (?:valid|solution)|Special Judge|absolute.{0,20}error|relative error|误差|输出任意|多种答案|任意.*(?:排列|方案|答案))',base['markdown'] or '',re.I)) or '构造' in self._row(identity)['知识点'],
                'caseInsensitive':bool(re.search(r'(?:any case|case.insensitive|任意大小写|不区分大小写)',base['markdown'] or '',re.I)),
                'coverage':reviewed_cases.PROFILES.get(identity) if local else '仅样例，不代表完整评测'}

    def candidates(self,rows):
        # One request-scoped snapshot avoids re-parsing the full table per problem.
        # It is discarded after scanning, so later requests still read current rows.
        with self.lock:
            result=[]
            if hasattr(self.store,'raw_rows'):
                self._candidate_rows={r['场次']+'::'+r['题号']:r for r in self.store.raw_rows()}
                extensions=getattr(self.store,'extensions',None)
                if extensions:
                    for row in rows:
                        if row['id'].startswith('remote:'):
                            remote=extensions.row(row['id'])
                            if remote:self._candidate_rows[row['id']]=remote
            try:
                for row in rows:
                    try:base=self._cached(row['id'])
                    except (OSError,ValueError,SyntaxError):continue
                    if base['statementAvailable'] and base['samples']:
                        result.append(dict(row,judgeScope='local' if row['id'] in reviewed_cases.PROFILES else 'samples'))
                return result
            finally:self._candidate_rows=None
