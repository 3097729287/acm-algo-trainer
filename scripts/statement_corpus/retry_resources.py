import os
import concurrent.futures,datetime,hashlib,json,sys,urllib.request,urllib.error,time
from pathlib import Path
from urllib.parse import quote,urlsplit,urlunsplit
ROOT=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve()
REPO=Path(__file__).resolve().parents[2];sys.path[:0]=[str(REPO/'backend'),str(ROOT)]
from statement_resources import inspect_resource
from fetch_all import write
latest={}
for line in (ROOT/'evidence/resource-results.jsonl').read_text('utf8').splitlines():
    x=json.loads(line);latest[x['url']]=x
existing=ROOT/'evidence/resource-alternatives.jsonl'
if existing.exists():
    for line in existing.read_text('utf8').splitlines():
        x=json.loads(line)
        if x['result']=='verified':latest[x['originalUrl']]=x
bad=[x for x in latest.values() if x['result']!='verified']
def collect(item):
    original=item['url'];urls=[original]
    p=urlsplit(original)
    if p.scheme=='http':urls.append(urlunsplit(('https',p.netloc,p.path,p.query,p.fragment)))
    if p.hostname=='cdn.luogu.com.cn':urls.append(original.replace('cdn.luogu.com.cn','cdn.luogu.org'))
    for url in dict.fromkeys(urls):
        record={'url':url,'originalUrl':original,'kind':item['kind'],'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'GET'}
        try:
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            headers={'User-Agent':'TB/1.4.31 public-statement-archive (+read-only)','Referer':'https://www.luogu.com.cn/','Accept':'image/gif,image/*,*/*;q=.8'}
            with opener.open(urllib.request.Request(quote(url,safe=":/?#[]@!$&'()*+,;=%"),headers=headers),timeout=15) as response:
                chunks=[];size=0;deadline=time.monotonic()+20
                while True:
                    if time.monotonic()>deadline:raise TimeoutError('Original resource total read budget exceeded')
                    chunk=response.read1(65536)
                    if not chunk:break
                    chunks.append(chunk);size+=len(chunk)
                    if size>32*1024*1024:raise ValueError('Original resource too large')
                data=b''.join(chunks);record.update(status=response.status,finalUrl=response.url)
            info=inspect_resource(data,url,item['kind']);file=info['sha256']+'.bin';(ROOT/'resources'/file).write_bytes(data)
            record.update(result='verified',**info,file=file)
            write(ROOT/'evidence/resource-alternatives.jsonl',record);write(ROOT/'evidence/alternative-attempts.jsonl',record);return 'verified'
        except urllib.error.HTTPError as e:record.update(status=e.code,result='http_error')
        except Exception as e:record.update(result='failed',message=str(e)[:180])
        write(ROOT/'evidence/resource-alternatives.jsonl',record);write(ROOT/'evidence/alternative-attempts.jsonl',record)
    return 'unresolved'
from collections import Counter
print('retry resources',len(bad),flush=True)
print(Counter(concurrent.futures.ThreadPoolExecutor(6).map(collect,bad)),flush=True)
