"""Reviewed, mandatory output-only inputs; separate from ordinary inline assets.

Only a bundled, manually reviewed manifest can authorize a download. User URLs
and private account state never participate. Every cached/network block is
verified before use; the final response block waits for the complete checksum.
"""
import copy
from functools import lru_cache
import hashlib
from http.client import IncompleteRead
import json
import os
from pathlib import Path
import re
import shutil
import threading
from urllib.error import HTTPError,URLError
from urllib.parse import urlsplit
from urllib.request import Request

CHUNK_BYTES=65536
MAX_DOWNLOAD=128*1024*1024
_locks=[threading.RLock()for _ in range(32)]
_default=None
_default_lock=threading.Lock()


def validate_manifest(value):
    if not isinstance(value,dict)or value.get('schema')!=1 or not isinstance(value.get('downloads'),list)or len(value['downloads'])>32:
        raise ValueError('Invalid required-download manifest')
    result={}
    hex64=lambda s:isinstance(s,str)and bool(re.fullmatch('[a-f0-9]{64}',s))
    for item in value['downloads']:
        if not isinstance(item,dict):raise ValueError('Invalid reviewed download')
        sha=item.get('sha256');size=item.get('bytes');chunks=item.get('chunkSha256');bindings=item.get('statementSha256')
        if (not hex64(sha)or sha in result or type(size)is not int or not 0<size<=MAX_DOWNLOAD
            or item.get('mime')!='application/zip'or item.get('problemType')!='output-only'
            or item.get('role')!='required-output-only-inputs'or item.get('manuallyReviewed')is not True
            or item.get('requiredForStatement')is not True or item.get('optional')is not False
            or not hex64(item.get('reviewSha256'))or item.get('chunkBytes')!=CHUNK_BYTES
            or not isinstance(chunks,list)or len(chunks)!=(size+CHUNK_BYTES-1)//CHUNK_BYTES or not all(map(hex64,chunks))
            or not isinstance(bindings,list)or not 1<=len(bindings)<=8 or not all(map(hex64,bindings))
            or not isinstance(item.get('problemId'),str)or not 1<=len(item['problemId'])<=512
            or not isinstance(item.get('fileName'),str)or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}\.zip',item['fileName'])):
            raise ValueError('Invalid reviewed required-download metadata')
        for key in ('sourceUrl','originalDownloadUrl'):
            p=urlsplit(item.get(key)or'')
            if p.scheme!='https'or not p.hostname or p.username or p.password or p.fragment:
                raise ValueError('Invalid required-download provenance')
        members=item.get('members')
        if not isinstance(members,list)or not 1<=len(members)<=1000:raise ValueError('Missing required input inventory')
        names=set()
        for member in members:
            name=member.get('name')if isinstance(member,dict)else None
            if (not isinstance(name,str)or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}',name)
                or name in names or not hex64(member.get('sha256'))or type(member.get('bytes'))is not int or member['bytes']<1):
                raise ValueError('Invalid required input inventory')
            names.add(name)
        result[sha]=copy.deepcopy(item)
    return result


def load_manifest(path=None):
    from paths import resource
    path=Path(path or resource('reviewed-required-downloads.json'))
    if path.stat().st_size>2*1024*1024:raise ValueError('Required-download manifest too large')
    return validate_manifest(json.loads(path.read_text('utf8')))


@lru_cache(maxsize=1)
def bundled_manifest():
    # Reading source metadata does not construct a network/cache client or
    # depend on the personal account's service configuration.
    return load_manifest()


def trusted_origin(origin):
    from leaderboard import bundled_endpoint
    p=urlsplit(origin);expected=urlsplit(bundled_endpoint())
    loopback=p.hostname in {'127.0.0.1','localhost','::1'}
    if (p.username or p.password or p.query or p.fragment or p.path not in ('','/')
        or not(loopback and p.scheme=='http'or p.scheme=='https'and p.hostname==expected.hostname and p.port in (None,443))):
        raise ValueError('Untrusted required-download origin')
    return origin.rstrip('/')


def default_manager():
    global _default
    with _default_lock:
        if _default is None:_default=RequiredDownloads()
        return _default


def attach_statement(value,identity=None,manager=None):
    """Resolve an exact reviewed source to a small, same-origin download link.

    This does not alter completeness, retirement, source text, samples or IDs.
    The remote source remains an original link in the stored statement.
    """
    if not isinstance(value,dict):return value
    identity=identity or value.get('id')
    if value.get('id')!=identity:return value
    items=manager.items if manager is not None else bundled_manifest()
    selected=[item for item in items.values()if item['problemId']==identity]
    if not selected:return value
    digest=hashlib.sha256((value.get('markdown')or'').encode()).hexdigest()
    result=copy.deepcopy(value)
    for item in selected:
        if value.get('url')!=item['sourceUrl']or digest not in item['statementSha256']:continue
        url=item['originalDownloadUrl']
        if url not in (value.get('markdown')or''):continue
        result.setdefault('attachments',{})[url]={
            'sourceUrl':url,'fileName':item['fileName'],'mime':item['mime'],
            'bytes':item['bytes'],'sha256':item['sha256'],'requiredForStatement':True,
            'kind':'reviewed-required-download','reviewSha256':item['reviewSha256'],
            'data':'/api/required-downloads/'+item['sha256'],
        }
    return result


def byte_range(value,size):
    if value is None:return 0,size-1,False
    match=re.fullmatch(r'bytes=(\d+)-(\d*)',value)
    if not match:raise ValueError('Invalid download range')
    start=int(match[1]);end=min(int(match[2])if match[2]else size-1,size-1)
    if start>end or start>=size:raise ValueError('Invalid download range')
    return start,end,True


class RequiredDownloads:
    def __init__(self,*,manifest_path=None,cache_root=None,origin=None,opener_factory=None,retries=2):
        from paths import STATE
        from leaderboard import bundled_endpoint,service_opener
        self.items=load_manifest(manifest_path)
        self.cache_root=Path(cache_root or STATE.parent/'cache'/'required-downloads').resolve()
        self.origin=trusted_origin(origin or bundled_endpoint())
        self.opener_factory=opener_factory or service_opener
        if type(retries)is not int or not 0<=retries<=3:raise ValueError('Invalid required-download retry limit')
        self.retries=retries;self.progress={};self.progress_lock=threading.Lock()

    def descriptor(self,sha):
        if not isinstance(sha,str)or not re.fullmatch('[a-f0-9]{64}',sha)or sha not in self.items:
            raise FileNotFoundError('Unknown reviewed required download')
        return self.items[sha]

    def _paths(self,item):
        self.cache_root.mkdir(parents=True,exist_ok=True)
        complete=self.cache_root/(item['sha256']+'.zip');partial=self.cache_root/(item['sha256']+'.part')
        for path in (complete,partial):
            if path.is_symlink()or path.exists()and not path.is_file():raise ValueError('Invalid required-download cache path')
            if path.resolve().parent!=self.cache_root:raise ValueError('Invalid required-download cache location')
        return complete,partial

    @staticmethod
    def _scan(path,item):
        """Return only the durable, verified contiguous prefix and its hasher."""
        h=hashlib.sha256();valid=0
        if not path.exists():return valid,h,False
        with path.open('rb')as f:
            for index,expected in enumerate(item['chunkSha256']):
                count=min(CHUNK_BYTES,item['bytes']-valid);block=f.read(count)
                if len(block)!=count or hashlib.sha256(block).hexdigest()!=expected:return valid,h,False
                if index==0 and not block.startswith((b'PK\x03\x04',b'PK\x05\x06')):return valid,h,False
                h.update(block);valid+=len(block)
            extra=f.read(1)
        if h.hexdigest()!=item['sha256']:raise ValueError('Required-download manifest checksum mismatch')
        return valid,h,not extra

    def _state(self,item,**updates):
        with self.progress_lock:
            value=self.progress.setdefault(item['sha256'],{'verifiedBytes':0,'cached':False,'downloading':False,'error':''})
            value.update(updates)

    def status(self,sha):
        item=self.descriptor(sha)
        with self.progress_lock:value=dict(self.progress.get(sha,{}))
        if not value.get('downloading'):
            complete,partial=self._paths(item)
            try:
                count,_,cached=self._scan(complete,item)
                if not cached:count,_,_=self._scan(partial,item)
                value.update(verifiedBytes=count,cached=cached,downloading=False)
            except (OSError,ValueError):value.update(verifiedBytes=0,cached=False,error='缓存尚未通过校验')
        return {'sha256':sha,'fileName':item['fileName'],'bytes':item['bytes'],
                'verifiedBytes':value.get('verifiedBytes',0),'cached':bool(value.get('cached')),
                'downloading':bool(value.get('downloading')),'error':value.get('error','')}

    def _open(self,item,start,end):
        if os.environ.get('TB_OFFLINE')=='1':raise OSError('Required inputs have not been cached for offline use')
        url=self.origin+'/updates/required-downloads/'+item['sha256']+'.zip'
        request=Request(url,headers={'Accept':'application/zip','Accept-Encoding':'identity',
            'Range':f'bytes={start}-{end}','If-Range':'"sha256:'+item['sha256']+'"',
            'User-Agent':'ToBe-required-inputs/1'})
        response=self.opener_factory(url).open(request,timeout=20)
        try:
            status=getattr(response,'status',None);headers=response.headers
            final=getattr(response,'url',url)
            if final!=url:raise ValueError('Required input download redirected')
            if headers.get('Content-Encoding','identity').lower()!='identity':raise ValueError('Unexpected required input encoding')
            full=status==200 and start==0 and end==item['bytes']-1
            if not full and(status!=206 or headers.get('Content-Range')!=f'bytes {start}-{end}/{item["bytes"]}'):
                raise ValueError('Required input range mismatch')
            if int(headers.get('Content-Length','-1'))!=end-start+1:raise ValueError('Required input length mismatch')
            return response
        except BaseException:response.close();raise

    def blocks(self,sha,start=0,end=None):
        """Yield verified bytes with bounded memory and a resumable file cache."""
        item=self.descriptor(sha);end=item['bytes']-1 if end is None else end
        if type(start)is not int or type(end)is not int or not 0<=start<=end<item['bytes']:
            raise ValueError('Invalid required-download range')
        lock=_locks[int(sha[:2],16)%len(_locks)]
        with lock:
            complete,partial=self._paths(item)
            valid,hasher,cached=self._scan(complete,item)
            if complete.exists()and not cached:
                os.replace(complete,partial)
            if not cached:
                valid,hasher,_=self._scan(partial,item)
                if valid==item['bytes']:
                    # A crash may occur after the durable last block but before
                    # the atomic promotion. Recheck and finish that promotion.
                    with partial.open('r+b')as f:f.truncate(valid);f.flush();os.fsync(f.fileno())
                    os.replace(partial,complete);cached=True
            self._state(item,verifiedBytes=valid,cached=cached,downloading=True,error='')
            target=complete if cached else partial
            remote=None;working=None;pending=None
            try:
                if not cached:
                    if shutil.disk_usage(self.cache_root).free<item['bytes']-valid+128*1024*1024:
                        raise OSError('Insufficient required-download cache space')
                    working=target.open('r+b'if target.exists()else'w+b');working.truncate(valid)
                else:working=target.open('rb')
                last=end//CHUNK_BYTES;remote_end=min((last+1)*CHUNK_BYTES,item['bytes'])-1
                for index in range(last+1):
                    offset=index*CHUNK_BYTES;length=min(CHUNK_BYTES,item['bytes']-offset)
                    if offset<valid:
                        working.seek(offset);block=working.read(length)
                    else:
                        for attempt in range(self.retries+1):
                            try:
                                if remote is None:remote=self._open(item,offset,remote_end)
                                block=remote.read(length)
                                if len(block)!=length:raise IncompleteRead(block,length-len(block))
                                break
                            except (OSError,URLError,IncompleteRead)as issue:
                                if remote is not None:remote.close();remote=None
                                if isinstance(issue,HTTPError)and issue.code not in {408,429,500,502,503,504}:raise
                                if attempt==self.retries:raise
                        if hashlib.sha256(block).hexdigest()!=item['chunkSha256'][index]:
                            raise ValueError('Required input block checksum mismatch')
                        if index==0 and not block.startswith((b'PK\x03\x04',b'PK\x05\x06')):
                            raise ValueError('Required input archive is not a ZIP')
                        working.seek(offset);working.write(block);working.flush()
                        hasher.update(block);valid+=len(block)
                        self._state(item,verifiedBytes=valid)
                    # Recheck cached blocks too; another local process cannot
                    # substitute bytes after the prefix scan unnoticed.
                    if len(block)!=length or hashlib.sha256(block).hexdigest()!=item['chunkSha256'][index]:
                        raise ValueError('Cached required input block checksum mismatch')
                    if index==0 and not block.startswith((b'PK\x03\x04',b'PK\x05\x06')):
                        raise ValueError('Required input archive is not a ZIP')
                    if not cached and valid==item['bytes']:
                        if hasher.hexdigest()!=sha:raise ValueError('Required input whole checksum mismatch')
                        working.flush();os.fsync(working.fileno());working.close();working=None
                        os.replace(partial,complete);cached=True
                        self._state(item,cached=True)
                    left=max(start-offset,0);right=min(end-offset+1,len(block))
                    if left<right:
                        if pending is not None:yield pending
                        pending=block[left:right]
                if pending is not None:yield pending
            except GeneratorExit:
                raise
            except BaseException as issue:
                self._state(item,error='输入数据下载未完成，可重新点击继续'if isinstance(issue,(OSError,URLError,IncompleteRead))else'输入数据校验失败，已保留通过校验的部分')
                raise
            finally:
                if remote is not None:remote.close()
                if working is not None:working.close()
                self._state(item,downloading=False,cached=cached)


def serve(handler,sha,manager=None):
    """Send a native browser download; no archive ever enters an API JSON body."""
    manager=manager or default_manager();item=manager.descriptor(sha)
    try:start,end,partial=byte_range(handler.headers.get('Range'),item['bytes'])
    except ValueError:
        handler.send_response(416);handler.send_header('Content-Range',f'bytes */{item["bytes"]}')
        handler.send_header('Content-Length','0');handler.end_headers();return
    stream=None;first=None
    if handler.command!='HEAD':
        stream=manager.blocks(sha,start,end)
        try:first=next(stream)
        except BaseException:stream.close();raise
    handler.send_response(206 if partial else 200)
    for key,value in {'Content-Type':item['mime'],'Content-Length':str(end-start+1),
        'Content-Disposition':'attachment; filename="'+item['fileName']+'"',
        'Accept-Ranges':'bytes','ETag':'"sha256:'+sha+'"','X-Content-SHA256':sha,
        'Cache-Control':'private, max-age=31536000, immutable','X-Content-Type-Options':'nosniff',
        **({'Content-Range':f'bytes {start}-{end}/{item["bytes"]}'}if partial else{})}.items():handler.send_header(key,value)
    handler.end_headers()
    if stream is None:return
    try:
        handler.wfile.write(first)
        for block in stream:handler.wfile.write(block)
    except (OSError,ValueError,URLError,IncompleteRead):
        # Do not send JSON after download headers or complete a corrupt file.
        handler.close_connection=True
        try:handler.connection.shutdown(2)
        except OSError:pass
    finally:stream.close()
