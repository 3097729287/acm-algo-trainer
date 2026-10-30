"""Verified public educational patches, applied online without touching accounts."""
from contextlib import closing
import gzip
import hashlib
import io
import logging
import json
import os
from pathlib import Path
import re
import sqlite3
import threading
import zlib
from urllib.parse import urlsplit
from urllib.request import Request,build_opener,ProxyHandler,HTTPRedirectHandler

from software_updates import DOMESTIC_ROOT,REPOSITORY,version_tuple
from version import VERSION

ROOT=DOMESTIC_ROOT+'/content'
GITHUB='https://raw.githubusercontent.com/'+REPOSITORY+'/main/content-updates'
MAX_PACKED=64*1024*1024
MAX_UNPACKED=256*1024*1024
LOG=logging.getLogger(__name__)
TABLES={'problems':('id',('id','url','raw','encoded')),
        'solutions':('problem_id',('problem_id','markdown','source_path','images','digest')),
        'detailed_solutions':('problem_id',('problem_id','markdown','source_path','images','digest')),
        'statements':('problem_id',('problem_id','content')),
        'solution_methods':('problem_id',('problem_id','content')),
        'training_lists':('id',('id','content'))}

def trusted(url):
    try:parts=urlsplit(url);port=parts.port
    except (ValueError,TypeError):return False
    if parts.scheme!='https' or parts.username or parts.password or parts.query or parts.fragment or port not in (None,443):return False
    return any(url==root+'/manifest-v1.json' or re.fullmatch(re.escape(root)+r'/[a-f0-9]{64}\.json\.gz',url) for root in (ROOT,GITHUB))

class Redirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if not trusted(newurl) or urlsplit(newurl).hostname!=urlsplit(req.full_url).hostname:
            raise ValueError('公共内容下载来源无效')
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

def validate(payload,current):
    if not isinstance(payload,dict) or set(payload)-{'schema','revision','minClientVersion','tables'} or payload.get('schema')!=1:
        raise ValueError('公共内容包格式无效')
    if type(payload.get('revision')) is not int or not 0<payload['revision']<2**63:raise ValueError('公共内容版本无效')
    if version_tuple(payload.get('minClientVersion'))>version_tuple(current):raise ValueError('公共内容需要更新的客户端')
    tables=payload.get('tables')
    if not isinstance(tables,dict) or set(tables)-TABLES.keys():raise ValueError('公共内容表无效')
    for table,rows in tables.items():
        key,columns=TABLES[table]
        if not isinstance(rows,list) or len(rows)>100000:raise ValueError('公共内容条目无效')
        seen=set()
        for row in rows:
            if not isinstance(row,dict) or set(row)!=set(columns):raise ValueError('公共内容字段无效')
            identity=row[key]
            if not isinstance(identity,str) or not 0<len(identity)<=512 or identity in seen:raise ValueError('公共内容编号无效')
            seen.add(identity)
            if any(not isinstance(row[column],str) for column in columns if column!='url'):raise ValueError('公共内容文本无效')
            if table=='problems':
                encoded,raw=json.loads(row['encoded']),json.loads(row['raw'])
                if encoded.get('id')!=identity or raw.get('_id',identity)!=identity or encoded.get('url')!=row['url']:
                    raise ValueError('公共内容原题身份不一致')
                if encoded.get('date') or encoded.get('queue') or encoded.get('accepted') or raw.get('日期'):
                    raise ValueError('公共内容含个人进度')
            elif 'content' in row:
                value=json.loads(row['content'])
                if not isinstance(value,dict) or table=='training_lists' and value.get('custom'):raise ValueError('公共内容不可包含私有题单')
                if table=='statements':
                    from statement_asset_store import references
                    if references(value):raise ValueError('Schema-1 content patches cannot transport SQLite statement assets; use a program update')
    return payload

def apply(store,payload,current=VERSION):
    """Three-way merge against bundled digests; online backup includes the WAL."""
    validate(payload,current)
    library=store.library
    with store.lock:
        if int(library.metadata().get('content_update_revision','0'))>=payload['revision']:return False
        library.backup('before-content-update')
        metadata={}
        with library.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            saved_metadata=db.execute("SELECT value FROM library_meta WHERE key='content_update_metadata'").fetchone()
            metadata=json.loads(saved_metadata[0]) if saved_metadata else {}
            for table,rows in payload['tables'].items():
                key,columns=TABLES[table]
                for row in rows:
                    identity=row[key];checksum=digest(row)
                    saved=db.execute('SELECT '+','.join(columns)+' FROM '+table+' WHERE '+key+'=?',(identity,)).fetchone()
                    old=db.execute('SELECT digest FROM bundled_items WHERE table_name=? AND item_id=?',(table,identity)).fetchone()
                    previous=dict(saved) if saved else None
                    if previous is not None and digest(previous)!=checksum and (not old or digest(previous)!=old[0]):
                        # Local imports/edits win; nothing private is overwritten.
                        continue
                    values=tuple(row[column] for column in columns)
                    changes=','.join(column+'=excluded.'+column for column in columns if column!=key)
                    db.execute('INSERT INTO '+table+' ('+','.join(columns)+') VALUES ('+','.join('?' for _ in columns)+') ON CONFLICT('+key+') DO UPDATE SET '+changes,values)
                    db.execute('INSERT INTO bundled_items VALUES (?,?,?) ON CONFLICT(table_name,item_id) DO UPDATE SET digest=excluded.digest',(table,identity,checksum))
                    if table=='problems':
                        encoded=json.loads(row['encoded'])
                        if encoded.get('url'):metadata[encoded['url']]={k:v for k,v in encoded.items() if k.startswith('difficulty') or k in ('nativeDifficulty','metadataVersion','officialTags','officialSourceTags','officialTagsCheckedAt')}
            if 'problems' in payload['tables']:library._rebuild_urls(db)
            if db.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('公共内容引用不完整')
            db.execute("INSERT INTO library_meta VALUES ('content_update_revision',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(str(payload['revision']),))
            db.execute("INSERT INTO library_meta VALUES ('content_update_metadata',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(json.dumps(metadata,ensure_ascii=False),))
            db.execute("UPDATE library_meta SET value=CAST(value AS INTEGER)+1 WHERE key='revision'")
        refresh=getattr(store,'_refresh_training_membership',None)
        if callable(refresh):refresh()
        integration=getattr(store,'extensions',None)
        if integration:
            with integration.lock:
                for url,patch in metadata.items():
                    old=integration.state['difficultyMetadata'].get(url,{})
                    if old.get('difficultyCheckedAt','')>patch.get('difficultyCheckedAt',''):continue
                    if patch:integration.state['difficultyMetadata'][url]={**old,**patch}
                try:integration._save()
                except (OSError,RuntimeError):LOG.exception('Public metadata is durable in library_meta; side cache save will retry')
    return True

class ContentUpdates:
    def __init__(self,store,*,current=VERSION,opener=None,offline=None,on_applied=None):
        self.store,self.current,self.on_applied=store,current,on_applied
        self.offline=os.environ.get('TB_OFFLINE')=='1' if offline is None else offline
        self.opener=opener
        self.stop=threading.Event();self.worker=None;self.lock=threading.RLock()
        self.status='idle';self.error=''
        with store.library.connection() as db:
            saved_row=db.execute("SELECT value FROM library_meta WHERE key='content_update_metadata'").fetchone()
            saved=saved_row[0] if saved_row else None
        integration=getattr(store,'extensions',None)
        if saved and integration:
            with integration.lock:
                for url,patch in json.loads(saved).items():
                    old=integration.state['difficultyMetadata'].get(url,{})
                    if old.get('difficultyCheckedAt','')<=patch.get('difficultyCheckedAt',''):integration.state['difficultyMetadata'][url]={**old,**patch}

    def read(self,url,limit):
        if not trusted(url):raise ValueError('公共内容下载来源无效')
        opener=self.opener or build_opener(*([ProxyHandler({})] if url.startswith(ROOT+'/') else []),Redirect())
        with opener.open(Request(url,headers={'User-Agent':'ToBe/'+self.current,'Cache-Control':'no-cache'}),timeout=25) as response:
            value=response.read(limit+1)
        if len(value)>limit:raise ValueError('公共内容超过大小限制')
        return value

    def check(self):
        if self.offline or self.stop.is_set():return False
        with self.lock:self.status='checking';self.error=''
        failures=[]
        for root in (ROOT,GITHUB):
            try:
                manifest=json.loads(self.read(root+'/manifest-v1.json',1024*1024))
                if not isinstance(manifest,dict) or manifest.get('schema')!=1:raise ValueError('公共内容清单格式无效')
                revision=manifest.get('revision')
                if type(revision) is not int or revision<=0:raise ValueError('公共内容版本无效')
                if revision<=int(self.store.library.metadata().get('content_update_revision','0')):
                    with self.lock:self.status='current'
                    return False
                sha,size=manifest.get('sha256'),manifest.get('size')
                if not isinstance(sha,str) or not re.fullmatch('[a-f0-9]{64}',sha) or type(size) is not int or not 0<size<=MAX_PACKED:
                    raise ValueError('公共内容摘要或大小无效')
                if version_tuple(manifest.get('minClientVersion'))>version_tuple(self.current):
                    with self.lock:self.status='client-required'
                    return False
                packed=self.read(root+'/'+sha+'.json.gz',size)
                if len(packed)!=size or hashlib.sha256(packed).hexdigest()!=sha:raise ValueError('公共内容校验失败')
                with gzip.GzipFile(fileobj=io.BytesIO(packed)) as stream:raw=stream.read(MAX_UNPACKED+1)
                if len(raw)>MAX_UNPACKED:raise ValueError('公共内容展开后超过大小限制')
                payload=json.loads(raw)
                if payload.get('revision')!=revision or payload.get('minClientVersion')!=manifest.get('minClientVersion'):raise ValueError('公共内容版本不一致')
                if self.stop.is_set():return False
                changed=apply(self.store,payload,self.current)
                if changed and self.on_applied:self.on_applied()
                with self.lock:self.status='current';self.error=''
                return changed
            except (OSError,ValueError,RuntimeError,KeyError,TypeError,EOFError,sqlite3.Error,zlib.error) as error:failures.append(str(error)[:180])
        with self.lock:self.status='error';self.error='；'.join(failures)
        return False

    def snapshot(self):
        with self.lock:return {'revision':int(self.store.library.metadata().get('content_update_revision','0')),'status':self.status,'error':self.error}

    def start(self):
        if self.offline or self.worker is not None:return
        def run():
            while not self.stop.is_set():
                self.check()
                self.stop.wait(300)
        self.worker=threading.Thread(target=run,name='ToBe-public-content',daemon=True);self.worker.start()

    def close(self):self.stop.set()
