import os
import collections,concurrent.futures,hashlib,json,sys,threading
from pathlib import Path
ROOT=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve()
REPO=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).resolve().parent))
from fetch_all import Client,LOCAL,PARSED,write,RESULTS,raw_name
from reparse_evidence import RES
import public_platforms
rows=json.loads((ROOT/'evidence/inventory.json').read_text('utf8'));targets=[]
for row in rows:
    if not row['url'] or 'luogu.com.cn' not in row['url'] or '/AT_' not in row['url']:continue
    path=PARSED/(hashlib.sha256(row['id'].encode()).hexdigest()+'.json')
    if not path.exists():continue
    packet=json.loads(path.read_text('utf8'))
    for source in packet.get('sources',[]):
        if source['url']!=row['url']:continue
        try:p=json.loads((ROOT/'raw'/source['file']).read_text('utf8'))['data']['problem']
        except Exception:continue
        link=(p.get('vjudge') or {}).get('link')
        if link and link.startswith('https://atcoder.jp/contests/'):targets.append((row,p,packet,link))
        break
class CachedClient(Client):
    def bytes(self,url,headers=None):
        if url in RES:
            x=RES[url];data=(ROOT/'resources'/x['file']).read_bytes()
            assert hashlib.sha256(data).hexdigest()==x['sha256']
            LOCAL.sources.append({'url':url,'sha256':x['sha256'],'file':raw_name(data),'time':x.get('time')});return data
        return super().bytes(url,headers)
def collect(item):
    row,p,packet,url=item;LOCAL.sources=[]
    try:
        value=public_platforms.statement(CachedClient(),row['id'],row['title'],url)
        def pairs(samples):return [(x[0].replace('\r\n','\n').rstrip('\n'),x[1].replace('\r\n','\n').rstrip('\n')) for x in samples]
        mirror=pairs(p.get('samples') or []);original=pairs([(s['input'],s['output']) for s in value['samples']])
        if mirror and not all(pair in original for pair in mirror):raise ValueError('Native/mirror sample mismatch; requires review')
        value.update(url=row['url'],originalSource=url,sourceStatementUrl=url)
        result={'statement':value,'sources':packet['sources']+LOCAL.sources,
            'binding':{'sourceUrl':url,'mirrorUrl':row['url'],'mirrorPid':p['pid'],'method':'publisher-vjudge-link-and-every-mirror-sample','mirrorSamples':len(mirror),'nativeSamples':len(original)}}
        path=PARSED/(hashlib.sha256(row['id'].encode()).hexdigest()+'.json');tmp=path.with_suffix('.native-at.tmp');tmp.write_text(json.dumps(result,ensure_ascii=False),'utf8');tmp.replace(path)
        write(RESULTS,{'id':row['id'],'url':url,'result':'native-at-verified'});return 'verified'
    except Exception as e:
        write(ROOT/'evidence/alternative-attempts.jsonl',{'id':row['id'],'url':url,'result':'native-at-failed','message':str(e)[:180]});return 'failed'
stats=collections.Counter()
with concurrent.futures.ThreadPoolExecutor(4) as pool:
    for i,result in enumerate(pool.map(collect,targets),1):
        stats[result]+=1
        if i%20==0:print({'done':i,'total':len(targets),'counts':dict(stats)},flush=True)
print(dict(stats),flush=True)
