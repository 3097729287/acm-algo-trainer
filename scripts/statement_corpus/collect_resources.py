import os
import concurrent.futures,hashlib,json,sqlite3,sys,threading,urllib.request,urllib.error,datetime,time
from pathlib import Path
ROOT=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve()
REPO=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(REPO/'backend'),str(REPO/'backend/common')]
from statement_resources import resource_references,inspect_resource
from urllib.parse import urlsplit,quote
DIR=ROOT/'resources';DIR.mkdir(exist_ok=True);LOCK=threading.RLock();PACING={}
LOG=ROOT/'evidence/resource-attempts.jsonl';RESULT=ROOT/'evidence/resource-results.jsonl'
def log(path,row):
    with LOCK,path.open('a',encoding='utf8') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
def fetch(ref):
    url=ref['url'];kind=ref['kind'];record={'url':url,'kind':kind,'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'route':'anonymous-direct'}
    try:
        parsed=urlsplit(url)
        if parsed.scheme not in ('https','http') or not parsed.hostname or parsed.username or parsed.password:raise ValueError('Invalid public resource URL')
        with LOCK:
            scheduled=max(time.monotonic(),PACING.get(parsed.hostname,0)+.25);PACING[parsed.hostname]=scheduled
        if scheduled>time.monotonic():time.sleep(scheduled-time.monotonic())
        op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with op.open(urllib.request.Request(quote(url,safe=":/?#[]@!$&'()*+,;=%"),headers={'User-Agent':'TB/1.4.31 public-statement-archive (+read-only)'}),timeout=18) as response:
            data=response.read(32*1024*1024+1);record.update(status=response.status,finalUrl=response.url)
        info=inspect_resource(data,url,kind);file=info['sha256']+'.bin';(DIR/file).write_bytes(data)
        record.update(result='verified',**info,file=file)
    except urllib.error.HTTPError as e:record.update(status=e.code,result='http_error')
    except Exception as e:record.update(result='failed',error=type(e).__name__,message=str(e)[:180])
    log(LOG,record);log(RESULT,record);return record
def main():
    done=set()
    if RESULT.exists():done={json.loads(x)['url'] for x in RESULT.read_text('utf8').splitlines()}
    db=sqlite3.connect(ROOT/'baseline.sqlite3')
    initial=[json.loads(x[0]) for x in db.execute('select content from statements')]
    seenfiles=set();round=0
    while True:
        refs={}
        values=initial if round==0 else [];round+=1
        for path in (ROOT/'parsed').glob('*.json'):
            if path.name in seenfiles:continue
            try:values.append(json.loads(path.read_text('utf8'))['statement']);seenfiles.add(path.name)
            except Exception:pass
        for value in values:
            for ref in resource_references(value):
                if ref['url'] not in done and ref['key'] not in value.get('images',{}) and ref['url'].startswith(('https://','http://')):refs[ref['url']]=ref
        if refs:
            with concurrent.futures.ThreadPoolExecutor(12) as pool:
                for i,result in enumerate(pool.map(fetch,refs.values()),1):
                    done.add(result['url'])
                    if i%100==0:print({'round':round,'done':len(done),'batch':len(refs)},flush=True)
        if (ROOT/'collection-done').exists():break
        time.sleep(20)
if __name__=='__main__':main()
