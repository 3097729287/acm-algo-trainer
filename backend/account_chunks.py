"""Private, content-addressed incremental sync with bounded transfer objects.

The local SQLite journal remains authoritative for pending edits. Only an atomic
root CAS makes a new cloud version visible. Code older than 30 days is a separate
object: metadata restores immediately; opening that submission fetches its code.
An existing machine keeps every local copy. Nothing is pruned from personal data.
"""
from __future__ import annotations
import base64
import datetime as dt
import gzip
import hashlib
import io
import json
import re
import time

from training import ServiceError

CHUNK=64*1024
RAW_LIMIT=128*1024*1024
CODE_PREFIX='\x00TB-CODE-V2:'
HASH=re.compile(r'^[a-f0-9]{64}$')

def encode(value):
    return json.dumps(value,ensure_ascii=False,separators=(',',':'),sort_keys=True).encode('utf8')

def object_hash(kind,payload,children):
    return hashlib.sha256((kind+'\n'+''.join(children)+'\n').encode('ascii')+payload).hexdigest()

def code_reference(value):
    if not isinstance(value,str) or not value.startswith(CODE_PREFIX):return None
    try:
        ref=json.loads(value[len(CODE_PREFIX):])
        if (set(ref) not in ({'root','sha256','bytes'},{'root','sha256','bytes','offset'}) or not HASH.fullmatch(ref['root']) or
            not HASH.fullmatch(ref['sha256']) or type(ref['bytes']) is not int or not 0<=ref['bytes']<=262144 or
            type(ref.get('offset',0)) is not int or not 0<=ref.get('offset',0)<=262144-ref['bytes']):raise ValueError()
        return ref
    except (TypeError,ValueError,KeyError):
        raise ServiceError(503,'历史代码引用校验失败，本机数据已保留') from None

class ChunkTransport:
    def __init__(self,sync):
        self.sync=sync;self.enabled=False;self.answer=None;self.migrate=False
        with sync.service.lock:
            sync.service.connection.executescript('''
              CREATE TABLE IF NOT EXISTS account_sync_objects(
                hash TEXT PRIMARY KEY,kind TEXT NOT NULL,payload BLOB NOT NULL,
                children TEXT NOT NULL,uploaded_at REAL NOT NULL DEFAULT 0);
              CREATE TABLE IF NOT EXISTS account_sync_code_refs(
                submission_id TEXT PRIMARY KEY,reference TEXT NOT NULL);
            ''')
        sync.service.history_code_loader=self.submission_code

    def request(self,method,path,body=None,cached_revision=None,retry=True):
        attempts=40
        for attempt in range(attempts):
            if self.sync.stop.is_set():raise ServiceError(503,'账号同步正在停止，本机数据已保留')
            session=self.sync.session
            try:
                value=self.sync.accounts._remote(method,path,body,session,invalidate=False,maximum=128*1024,timeout=40,
                    **({'state_revision':cached_revision} if cached_revision is not None else {}))
                self.sync._check_stopping()
                return value
            except ServiceError as issue:
                if issue.status==401 and session['token']!=self.sync.session['token']:continue
                if (getattr(issue, 'connection_unavailable', False)
                    and self.sync.accounts.restore_time_remaining() is not None):
                    raise  # A verified local lease must not wait through retry backoff.
                if (issue.status not in (429,502,503,504) or attempt==attempts-1 or
                    (issue.status!=429 and (attempt>=8 or not retry))):raise
                # Stable owner-based jitter spreads devices without a global lock.
                delay=min(2,.2*2**attempt)+(int(self.sync.owner.replace('-','')[:4],16)%251)/1000
                if self.sync.stop.wait(delay):raise ServiceError(503,'账号同步正在停止，本机数据已保留') from None

    def negotiate(self):
        cached=self.sync.meta.get('revision') if self.sync.meta.get('transport')==2 else None
        try:self.answer=self.request('GET','/v2/accounts/state',cached_revision=cached,retry=False)
        except ServiceError as issue:
            if issue.status not in (404,405) or self.sync.meta.get('transport')==2:raise
            return
        if self.answer.get('protocol')!=2:raise ServiceError(503,'分块同步协议校验失败，本机数据已保留')
        if self.sync.meta.get('transport')==2 and self.answer.get('legacy'):
            raise ServiceError(503,'云端分块版本暂不可用，本机数据已保留，请联系维护者恢复云端记录')
        self.enabled=True;self.migrate=bool(self.answer.get('legacy'))

    def _cached(self,identity):
        with self.sync.service.lock:
            row=self.sync.service.connection.execute('SELECT kind,payload,children,uploaded_at FROM account_sync_objects WHERE hash=?',(identity,)).fetchone()
            return dict(row) if row else None

    def _store(self,identity,kind,payload,children,uploaded=0):
        with self.sync.service.lock:
            db=self.sync.service.connection
            db.execute('INSERT OR IGNORE INTO account_sync_objects VALUES(?,?,?,?,?)',(identity,kind,payload,json.dumps(children),uploaded))
            if uploaded:db.execute('UPDATE account_sync_objects SET uploaded_at=? WHERE hash=?',(uploaded,identity))

    def _node(self,kind,raw,children=()):
        if len(raw)>CHUNK:raise ServiceError(413,'单个同步分块过大，本机数据已保留')
        children=sorted(set(children))
        if len(children)>256:raise ServiceError(413,'同步分块依赖过多，本机数据已保留')
        payload=gzip.compress(raw,compresslevel=6,mtime=0)
        identity=object_hash(kind,payload,children)
        self._store(identity,kind,payload,children)
        return identity

    def _links(self,identities):
        identities=list(dict.fromkeys(identities))
        if not identities:return []
        while len(identities)>128:
            identities=[self._node('concat',encode({'parts':[]}),identities[i:i+128]) for i in range(0,len(identities),128)]
        return identities

    def write_blob(self,raw,links=()):
        if len(raw)>RAW_LIMIT:raise ServiceError(413,'单项账号数据超过分块容量，本机数据已保留')
        parts=[self._node('data',raw[i:i+CHUNK]) for i in range(0,len(raw),CHUNK)] or [self._node('data',b'')]
        while len(parts)>128:
            parts=[self._node('concat',encode({'parts':parts[i:i+128]}),parts[i:i+128]) for i in range(0,len(parts),128)]
        return self._node('concat',encode({'parts':parts}),[*parts,*self._links(links)])

    def _load(self,identity):
        if not isinstance(identity,str) or not HASH.fullmatch(identity):raise ValueError('Invalid chunk ID')
        item=self._cached(identity)
        if item:return item
        value=self.request('GET','/v2/accounts/state/objects/'+identity)
        if set(value)!={'kind','data','children'} or value['kind'] not in ('data','concat'):raise ValueError('Invalid chunk schema')
        children=value['children']
        if (not isinstance(children,list) or len(children)>256 or children!=sorted(set(children)) or
            any(not isinstance(h,str) or not HASH.fullmatch(h) for h in children)):raise ValueError('Invalid chunk links')
        payload=base64.b64decode(value['data'],validate=True)
        if len(payload)>66*1024 or object_hash(value['kind'],payload,children)!=identity:raise ValueError('Invalid chunk checksum')
        self._store(identity,value['kind'],payload,children,time.time())
        return {'kind':value['kind'],'payload':payload,'children':json.dumps(children),'uploaded_at':time.time()}

    def read_blob(self,identity,maximum=RAW_LIMIT):
        output=io.BytesIO();ancestors=set()
        def visit(key,depth):
            if depth>24 or key in ancestors:raise ValueError('Invalid chunk graph')
            ancestors.add(key)
            try:
                item=self._load(key)
                if object_hash(item['kind'],item['payload'],json.loads(item['children']))!=key:raise ValueError('Invalid cached chunk checksum')
                with gzip.GzipFile(fileobj=io.BytesIO(item['payload'])) as stream:raw=stream.read(CHUNK+1)
                if len(raw)>CHUNK:raise ValueError('Expanded chunk too large')
                if item['kind']=='data':
                    if output.tell()+len(raw)>maximum:raise ValueError('Expanded object too large')
                    output.write(raw)
                else:
                    index=json.loads(raw)
                    if (set(index)!={'parts'} or not isinstance(index['parts'],list) or len(index['parts'])>128 or
                        any(h not in json.loads(item['children']) for h in index['parts'])):raise ValueError('Invalid index')
                    for part in index['parts']:visit(part,depth+1)
            finally:ancestors.remove(key)
        visit(identity,0)
        return output.getvalue()

    def canonicalize(self,state):
        """Represent cold code identically whether a machine has fetched it or not."""
        if not self.enabled:return state
        cutoff=self.sync.service._now()-dt.timedelta(days=30)
        with self.sync.service.lock:
            refs=dict(self.sync.service.connection.execute('SELECT submission_id,reference FROM account_sync_code_refs'))
        rows=[];pending={}
        for row in state['tables'].get('submissions',[]):
            row=dict(row);code=row.get('code','')
            ref=code_reference(code)
            if ref:
                rows.append(row);continue
            raw=code.encode('utf8')
            # Reuse immutable archives once created. A new machine need not
            # fetch unrelated historical code to produce the same state.
            old=code_reference(refs[row['id']]) if row['id'] in refs else None
            if old and code and hashlib.sha256(raw).hexdigest()==old['sha256']:
                row['code']=refs[row['id']];rows.append(row);continue
            if not code and row['id'] in refs:
                row['code']=refs[row['id']];rows.append(row);continue
            try:
                when=dt.datetime.fromisoformat(str(row.get('finished_at') or '').replace('Z','+00:00'))
                if when.tzinfo is None:when=when.replace(tzinfo=dt.timezone.utc)
                cold=when<cutoff
            except (ValueError,TypeError):cold=False
            if cold and code:
                bucket=str(row.get('submitted_at') or '')[:7]+':'+hashlib.sha256(row['id'].encode('utf8')).hexdigest()[0]
                pending.setdefault(bucket,[]).append((row,raw))
            rows.append(row)
        # A month/bucket archive packs many small source files into at most
        # 64 KiB. Opening one record reads that bounded archive, then slices and
        # verifies exactly that code. Large individual files remain standalone.
        saved=[]
        def archive(items):
            if not items:return
            raw=b''.join(code for _,code in items);root=self.write_blob(raw);offset=0
            for row,code in items:
                row['code']=CODE_PREFIX+encode({'root':root,'sha256':hashlib.sha256(code).hexdigest(),
                    'bytes':len(code),'offset':offset}).decode('utf8')
                saved.append((row['id'],row['code']));offset+=len(code)
        for bucket,items in sorted(pending.items()):
            group=[];size=0
            for item in sorted(items,key=lambda p:p[0]['id']):
                if group and size+len(item[1])>CHUNK:archive(group);group=[];size=0
                group.append(item);size+=len(item[1])
            archive(group)
        if saved:
            with self.sync.service.lock:
                self.sync.service.connection.executemany('''INSERT INTO account_sync_code_refs VALUES(?,?)
                    ON CONFLICT(submission_id) DO UPDATE SET reference=excluded.reference
                    WHERE reference<>excluded.reference''',saved)
        return {**state,'tables':{**state['tables'],'submissions':rows}}

    def pack(self,state):
        from account_sync import TABLES
        manifest={'format':'tb-private-chunk-state-v2','tables':{},'publicAccounts':None};roots=[]
        for table,keys in TABLES.items():
            buckets={}
            for row in state['tables'].get(table,[]):
                width=2 if table in ('account_problem_facts','account_sync_conflicts') else 1
                key=hashlib.sha256(encode([row.get(k) for k in keys])).hexdigest()[:width]
                if table=='submissions':key=str(row.get('submitted_at') or '')[:7]+':'+key
                buckets.setdefault(key,[]).append(row)
            entries=[]
            for bucket,rows in sorted(buckets.items()):
                links=[]
                for row in rows:
                    source=row if table=='submissions' else None
                    if table=='account_sync_conflicts':
                        try:
                            conflict=json.loads(row.get('data',''))
                            if conflict.get('table')=='submissions' and isinstance(conflict.get('row'),dict):source=conflict['row']
                        except (ValueError,TypeError,AttributeError):pass
                    if source is not None and (ref:=code_reference(source.get('code'))):links.append(ref['root'])
                root=self.write_blob(encode(rows),links);roots.append(root);entries.append({'bucket':bucket,'root':root})
            manifest['tables'][table]=entries
        profile=self.write_blob(encode(state['publicAccounts']));manifest['publicAccounts']=profile;roots.append(profile)
        return self.write_blob(encode(manifest),roots)

    def upload(self,root):
        order=[];known=set();now=time.time()
        def visit(key):
            if key in known:return
            known.add(key);item=self._cached(key)
            if item is None:
                # A cold code object may belong to the authenticated current
                # cloud graph without ever having been downloaded here.
                answer=self.request('POST','/v2/accounts/state/missing',{'hashes':[key]})
                if answer.get('missing')==[]:return
                raise ServiceError(503,'待同步分块缺失，本机数据已保留')
            if item['uploaded_at']>now-7*86400:return
            for child in json.loads(item['children']):visit(child)
            order.append((key,item))
        visit(root)
        missing=set()
        for i in range(0,len(order),128):
            ids=[key for key,_ in order[i:i+128]]
            answer=self.request('POST','/v2/accounts/state/missing',{'hashes':ids})
            if not isinstance(answer.get('missing'),list) or set(answer['missing'])-set(ids):raise ServiceError(503,'同步缺失清单校验失败')
            missing.update(answer['missing'])
        pending=[]
        def save_batch():
            if not pending:return
            keys=[item['hash'] for item in pending]
            answer=self.request('POST','/v2/accounts/state/objects',{'objects':pending})
            if answer.get('uploaded')!=keys:raise ServiceError(503,'同步分块确认不一致，本机数据已保留')
            with self.sync.service.lock:self.sync.service.connection.executemany('UPDATE account_sync_objects SET uploaded_at=? WHERE hash=?',[(now,key) for key in keys])
            pending.clear()
        for key,item in order:
            if key in missing:
                value={'hash':key,'kind':item['kind'],'data':base64.b64encode(item['payload']).decode('ascii'),'children':json.loads(item['children'])}
                if pending and (len(pending)>=64 or len(encode({'objects':[*pending,value]}))>120*1024):save_batch()
                pending.append(value)
            else:
                with self.sync.service.lock:self.sync.service.connection.execute('UPDATE account_sync_objects SET uploaded_at=? WHERE hash=?',(now,key))
        save_batch()

    def get(self,cached_revision=None):
        answer=self.answer;self.answer=None
        if answer is None:answer=self.request('GET','/v2/accounts/state',cached_revision=cached_revision)
        if answer.get('unchanged'):return answer
        if answer.get('legacy'):
            value=self.sync._legacy_call('GET','/v1/accounts/state')
            if value.get('state') is not None:value['state']=self.canonicalize(value['state'])
            return value
        try:
            manifest=json.loads(self.read_blob(answer['root'],4*1024*1024))
            from account_sync import TABLES
            if manifest.get('format')!='tb-private-chunk-state-v2' or set(manifest['tables'])!=set(TABLES):raise ValueError('Invalid manifest')
            state={'format':'tb-account-state-v1','tables':{},'publicAccounts':json.loads(self.read_blob(manifest['publicAccounts']))}
            total=0
            for table,entries in manifest['tables'].items():
                if not isinstance(entries,list) or len(entries)>4096:raise ValueError('Invalid table chunks')
                rows=[];keys=set()
                for entry in entries:
                    value=self.read_blob(entry['root']);total+=len(value)
                    if total>512*1024*1024:raise ValueError('Account expanded data limit')
                    group=json.loads(value)
                    if not isinstance(group,list):raise ValueError('Invalid table rows')
                    for row in group:
                        if not isinstance(row,dict):raise ValueError('Invalid row')
                        key=tuple(row.get(k) for k in TABLES[table])
                        if key in keys:raise ValueError('Duplicate row')
                        keys.add(key);rows.append(row)
                rows.sort(key=lambda row:tuple(str(row.get(k) or '') for k in TABLES[table]));state['tables'][table]=rows
            answer['state']=self.canonicalize(state)
            return answer
        except (ValueError,OSError,EOFError,KeyError,TypeError):
            raise ServiceError(503,'云端分块数据校验失败，本机记录已保留，请稍后重试') from None

    def put(self,body):
        root=self.pack(body['state']);self.upload(root)
        result=self.request('PUT','/v2/accounts/state',{'revision':body['revision'],'root':root})
        if result.get('revision')!=body['revision']+1 or result.get('root')!=root:
            raise ServiceError(503,'云端同步确认不一致，本机数据已保留')
        self.migrate=False
        return result

    def apply_code(self,row,previous):
        ref=code_reference(row.get('code'))
        db=self.sync.service.connection
        if ref:
            db.execute('INSERT INTO account_sync_code_refs VALUES(?,?) ON CONFLICT(submission_id) DO UPDATE SET reference=excluded.reference',(row['id'],row['code']))
            old=previous.get(row['id'],'')
            return {**row,'code':old if hashlib.sha256(old.encode('utf8')).hexdigest()==ref['sha256'] else ''}
        db.execute('DELETE FROM account_sync_code_refs WHERE submission_id=?',(row['id'],))
        return row

    def submission_code(self,identity):
        with self.sync.service.lock:
            row=self.sync.service.connection.execute('SELECT code FROM submissions WHERE id=?',(identity,)).fetchone()
            reference=self.sync.service.connection.execute('SELECT reference FROM account_sync_code_refs WHERE submission_id=?',(identity,)).fetchone()
            if not row or row['code'] or not reference:return row['code'] if row else ''
            ref=code_reference(reference[0])
        try:
            archive=self.read_blob(ref['root'],262144)
            offset=ref.get('offset',0);raw=archive[offset:offset+ref['bytes']]
            if len(raw)!=ref['bytes'] or hashlib.sha256(raw).hexdigest()!=ref['sha256']:raise ValueError('Invalid code digest')
            code=raw.decode('utf8')
        except (ValueError,OSError,EOFError,KeyError,TypeError):raise ServiceError(503,'历史代码读取校验失败，请重试；云端记录仍保留') from None
        # Network work is complete before taking the SQLite write lock. Avoid
        # replacing a late-arriving official receipt's newer nonempty code.
        with self.sync.service.lock:
            self.sync.service.connection.execute("UPDATE submissions SET code=? WHERE id=? AND code=''",(code,identity))
        return code
