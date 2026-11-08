"""Reuse only hash-pinned public illustration fields; private SQLite is read-only."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
import gzip,hashlib,io,os,re,sqlite3
from pathlib import Path
from urllib.request import Request,build_opener,ProxyHandler,HTTPRedirectHandler
from binary_delta import file_delta

RESOURCE_ROOT='https://47.82.84.74/updates/library-assets/'
TABLES={'solutions','detailed_solutions'}

def digest(raw):return hashlib.sha256(raw).hexdigest()
def valid_sha(value):return isinstance(value,str) and re.fullmatch('[a-f0-9]{64}',value)

def validate(fields,target_bytes):
    if not isinstance(fields,list) or not fields or len(fields)>128:raise ValueError('公共插图清单无效')
    ranges=[];raw_bytes=0
    for item in fields:
        if not isinstance(item,dict) or not valid_sha(item.get('sha256')) or not valid_sha(item.get('compressedSha256')):raise ValueError('公共插图摘要无效')
        if type(item.get('bytes')) is not int or not 1<=item['bytes']<=16*1024**2 or type(item.get('compressedBytes')) is not int or not 1<=item['compressedBytes']<=16*1024**2:raise ValueError('公共插图大小无效')
        if item.get('url')!=RESOURCE_ROOT+item['compressedSha256']+'.bin':raise ValueError('公共插图地址无效')
        candidates=item.get('candidates')
        if not isinstance(candidates,list) or not 1<=len(candidates)<=16:raise ValueError('公共插图来源无效')
        for source in candidates:
            if not isinstance(source,dict) or set(source)!={'table','id'} or source['table'] not in TABLES or not isinstance(source['id'],str) or not 1<=len(source['id'])<=512:raise ValueError('只能复用指定的公共题解插图')
        spans=item.get('spans')
        if not isinstance(spans,list) or not spans:raise ValueError('公共插图位置无效')
        for span in spans:
            if not isinstance(span,list) or len(span)!=3 or any(type(v) is not int for v in span):raise ValueError('公共插图位置无效')
            at,offset,size=span
            if at<100 or offset<0 or size<=0 or at+size>target_bytes or offset+size>item['bytes']:raise ValueError('公共插图位置越界')
            ranges.append((at,at+size))
        raw_bytes+=item['bytes']
    if raw_bytes>32*1024**2 or len(ranges)>16384:raise ValueError('公共插图总量过大')
    previous=0
    for start,end in sorted(ranges):
        if start<previous:raise ValueError('公共插图位置重叠')
        previous=end

def ordinary(path):
    return path.is_file() and not path.is_symlink() and not getattr(path.lstat(),'st_file_attributes',0)&0x400

def local_value(app,item):
    path=Path(app)/'state/tb-library.sqlite3'
    try:
        if not ordinary(path) or any(p.is_symlink() or getattr(p.lstat(),'st_file_attributes',0)&0x400 for p in (path.parent,Path(app))):return None
        with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=2)) as db:
            for source in item['candidates']:
                # Identifier is a fixed two-item enum; the public problem ID
                # remains a SQL parameter. No credentials or private tables.
                row=db.execute('SELECT images FROM '+source['table']+' WHERE problem_id=?',(source['id'],)).fetchone()
                if row is None or not isinstance(row[0],str):continue
                raw=row[0].encode('utf8')
                if len(raw)==item['bytes'] and digest(raw)==item['sha256']:return raw
    except (OSError,sqlite3.Error,UnicodeError):pass
    return None

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise OSError('公共插图下载发生重定向')

def remote_value(item):
    opener=build_opener(ProxyHandler({}),NoRedirect())
    with opener.open(Request(item['url'],headers={'Accept-Encoding':'identity','User-Agent':'ToBe-Public-Update/1'}),timeout=30) as response:
        if response.status!=200:raise OSError('公共插图暂不可用')
        raw=response.read(item['compressedBytes']+1)
    if len(raw)!=item['compressedBytes'] or digest(raw)!=item['compressedSha256']:raise ValueError('公共插图下载校验失败')
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:decoded=stream.read(item['bytes']+1)
    if len(decoded)!=item['bytes'] or digest(decoded)!=item['sha256']:raise ValueError('公共插图内容校验失败')
    return decoded

def patch_file(source,patch,target,*,app,expected_target,template_sha,fields,target_bytes):
    if not valid_sha(expected_target) or not valid_sha(template_sha):raise ValueError('公共题库目标摘要无效')
    validate(fields,target_bytes)
    def resolve(item):
        raw=local_value(app,item)
        return (remote_value(item),False) if raw is None else (raw,True)
    # Resolve independently hash-pinned public fields concurrently, retaining
    # manifest order. No output is created until every value is verified.
    with ThreadPoolExecutor(max_workers=min(4,len(fields))) as workers:
        resolved=list(workers.map(resolve,fields))
    values=[raw for raw,_ in resolved];reused=sum(kept for _,kept in resolved)
    file_delta(source,patch,target,expected_target=template_sha)
    if Path(target).stat().st_size!=target_bytes:raise ValueError('公共题库模板大小无效')
    with Path(target).open('r+b') as output:
        for item,raw in zip(fields,values):
            for at,offset,size in item['spans']:
                output.seek(at)
                if output.read(size)!=bytes(size):raise ValueError('公共插图模板位置校验失败')
                output.seek(at);output.write(raw[offset:offset+size])
        output.flush();os.fsync(output.fileno())
        output.seek(0)
        if hashlib.file_digest(output,'sha256').hexdigest()!=expected_target:raise ValueError('公共题库重建校验失败')
    return {'bytes':target_bytes,'sha256':expected_target,'reusedPublicFields':reused,'downloadedPublicFields':len(fields)-reused,'privateStateWritten':False}
