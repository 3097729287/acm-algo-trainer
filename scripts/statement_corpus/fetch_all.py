import os
"""Isolated anonymous GET collection. No account cookies, logins or submissions."""
import concurrent.futures,datetime,hashlib,json,sqlite3,sys,threading,time,urllib.request,urllib.error,re
from pathlib import Path
from urllib.parse import urlsplit,quote
ROOT=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve()
REPO=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(REPO/'backend'),str(REPO/'backend/common')]
import public_platforms
LOCK=threading.RLock();HOSTS={};LIMITS={};LOCAL=threading.local()
ANONYMOUS={}
RAW=ROOT/'raw';PARSED=ROOT/'parsed';RAW.mkdir(exist_ok=True);PARSED.mkdir(exist_ok=True)
IMMUTABLE=RAW/'by-sha';IMMUTABLE.mkdir(exist_ok=True)
LOG=ROOT/'evidence/attempts.jsonl';RESULTS=ROOT/'evidence/fetch-results.jsonl'
def write(path,data):
    with LOCK,path.open('a',encoding='utf8') as f:f.write(json.dumps(data,ensure_ascii=False)+'\n')
def raw_name(data):
    sha=hashlib.sha256(data).hexdigest();target=IMMUTABLE/(sha+'.bin')
    if not target.exists():target.write_bytes(data)
    return 'by-sha/'+target.name
class Client:
    def __init__(self):self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def bytes(self,url,headers=None):
        key=hashlib.sha256((url+json.dumps(headers or {},sort_keys=True)).encode()).hexdigest();path=RAW/(key+'.bin')
        if path.exists():
            cached=path.read_bytes()
            if b'C3VK=' not in cached[:1024]:
                LOCAL.sources.append({'url':url,'sha256':hashlib.sha256(cached).hexdigest(),'file':raw_name(cached),'cached':True})
                return cached
            path=RAW/(key+'.retry.bin')
            if path.exists():
                cached=path.read_bytes()
                if b'C3VK=' not in cached[:1024]:
                    LOCAL.sources.append({'url':url,'sha256':hashlib.sha256(cached).hexdigest(),'file':raw_name(cached),'cached':True})
                    return cached
        host=urlsplit(url).hostname
        with LOCK:
            semaphore=LIMITS.setdefault(host,threading.Semaphore(4));hostlock=HOSTS.setdefault(host,[threading.Lock(),0])
        with semaphore:
            with hostlock[0]:
                wait=hostlock[1]+.22-time.monotonic()
                if wait>0:time.sleep(wait)
                hostlock[1]=time.monotonic()
            attempt={'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'url':url,'route':'anonymous-direct','method':'GET'}
            try:
                request=urllib.request.Request(quote(url,safe=":/?#[]@!$&'()*+,;=%"),headers={'User-Agent':'TB/1.4.31 public-statement-archive (+read-only)','Accept':'text/html,application/json,application/pdf;q=.9',**(headers or {}),**({'Cookie':ANONYMOUS[host]} if host in ANONYMOUS else {})})
                with self.opener.open(request,timeout=18) as response:
                    data=response.read(32*1024*1024+1);attempt.update(status=response.status,finalUrl=response.url,mime=response.headers.get_content_type())
                # Only the literal anonymous first-party re-open cookie supplied
                # by this response; no scripts, login sessions or CAPTCHA logic.
                cookie=re.search(br'cookie="(C3VK=[a-zA-Z0-9]+); path=/; max-age=300;',data) if host=='www.luogu.com.cn' else None
                if cookie:
                    write(LOG,dict(attempt,result='anonymous_cookie_reopen'))
                    ANONYMOUS[host]=cookie[1].decode('ascii')
                    request.add_header('Cookie',ANONYMOUS[host])
                    with self.opener.open(request,timeout=18) as response:
                        data=response.read(32*1024*1024+1);attempt.update(status=response.status,finalUrl=response.url,mime=response.headers.get_content_type())
                if len(data)>32*1024*1024:raise ValueError('response_too_large')
                attempt.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),file=raw_name(data))
                path.write_bytes(data);LOCAL.sources.append(dict(attempt));return data
            except urllib.error.HTTPError as e:
                attempt.update(status=e.code,result='http_error');raise
            except Exception as e:
                attempt.update(status=None,result=type(e).__name__);raise
            finally:write(LOG,attempt)
    def text(self,url,headers=None):return self.bytes(url,headers).decode('utf8','replace')
    def json(self,url,headers=None):return json.loads(self.text(url,headers))
def collect(row):
    LOCAL.sources=[];key=hashlib.sha256(row['id'].encode()).hexdigest();target=PARSED/(key+'.json')
    if target.exists():return 'cached'
    result={'id':row['id'],'url':row['url'],'time':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        value=public_platforms.statement(Client(),row['id'],row['title'],row['url'])
        target.write_text(json.dumps({'statement':value,'sources':LOCAL.sources},ensure_ascii=False),'utf8');result.update(result='parsed',chars=len(value.get('markdown') or ''),samples=len(value.get('samples') or []))
    except Exception as e:result.update(result='failed',error=type(e).__name__,message=str(e)[:200])
    write(RESULTS,result);return result['result']
def main():
    rows=json.loads((ROOT/'evidence/inventory.json').read_text('utf8'))
    rows=[r for r in rows if r['url']]
    rows.sort(key=lambda r:('missing' not in r['issues'] and 'unreadable' not in r['issues'],r['id']))
    counts={}
    with concurrent.futures.ThreadPoolExecutor(16) as pool:
        for i,result in enumerate(pool.map(collect,rows),1):
            counts[result]=counts.get(result,0)+1
            if i%50==0:print(json.dumps({'done':i,'total':len(rows),'counts':counts}),flush=True)
    print(counts,flush=True)
if __name__=='__main__':main()
