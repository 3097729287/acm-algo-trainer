import os
import collections,concurrent.futures,datetime,hashlib,json,re,sqlite3,sys,threading
from pathlib import Path
from urllib.parse import quote,urljoin
ROOT=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve()
REPO=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).resolve().parent))
from fetch_all import Client,LOCAL,write,raw_name
from reparse_evidence import RES
from prepare_corpus import canonical_prose
from statement_format import Tree,plain
import public_platforms
db=sqlite3.connect(ROOT/'baseline.sqlite3');old={p:json.loads(s) for p,s in db.execute('select problem_id,content from statements')}
rows=json.loads((ROOT/'evidence/inventory.json').read_text('utf8'))
rows=[r for r in rows if r['url'] and not (ROOT/'parsed'/(hashlib.sha256(r['id'].encode()).hexdigest()+'.json')).exists()]
CANDIDATES=ROOT/'qoj-alternatives';CANDIDATES.mkdir(exist_ok=True)
def key(text):return re.sub(r'\W+','',text or '').casefold()
def pairs(value):return [(' '.join(s['input'].split()),' '.join(s['output'].split())) for s in value.get('samples') or []]
class CachedClient(Client):
    def bytes(self,url,headers=None):
        if url in RES:
            x=RES[url];data=(ROOT/'resources'/x['file']).read_bytes();assert hashlib.sha256(data).hexdigest()==x['sha256']
            LOCAL.sources.append({'url':url,'sha256':x['sha256'],'file':raw_name(data),'time':x.get('time')});return data
        return super().bytes(url,headers)
def spec(text):
    text=re.split(r'(?im)^#{1,6}\s*(?:Examples?|Samples?|Sample Input|Note|Hints?|样例|示例|备注)',text or '',maxsplit=1)[0]
    return canonical_prose(text)
def search(row):
    LOCAL.sources=[];client=CachedClient();url='https://qoj.ac/problems?search='+quote(row['title'] or '')
    result={'id':row['id'],'url':url,'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'GET','candidateIds':[]}
    try:
        page=client.text(url);root=Tree(page).root;links={}
        for node in root.find(lambda n:n.tag=='a' and re.fullmatch(r'/problem/\d+',n.attrs.get('href',''))):
            if key(plain(node).strip())==key(row['title']):links[urljoin(url,node.attrs['href'])]=plain(node).strip()
        result.update(status=200,result='searched',candidateIds=[u.rsplit('/',1)[-1] for u in links])
        for source,title in links.items():
            before=len(LOCAL.sources)
            try:value=public_platforms.statement(client,row['id'],title,source)
            except Exception as e:
                write(ROOT/'evidence/alternative-attempts.jsonl',{'id':row['id'],'url':source,'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'result':'candidate-read-failed','message':str(e)[:180]});continue
            packet={'statement':value,'sources':list(LOCAL.sources),'originalId':row['id'],'originalUrl':row['url'],'verifiedIdentity':False}
            previous=old.get(row['id'])
            if previous and spec(previous.get('markdown'))==spec(value.get('markdown')) and len(spec(value.get('markdown')))>150 and pairs(previous)==pairs(value):
                packet['verifiedIdentity']=True;value.update(id=row['id'],url=row['url'],originalSource=source,sourceStatementUrl=source)
                packet['binding']={'method':'full-specification-io-constraints-and-all-samples','originalUrl':row['url'],'mirrorUrl':source}
                target=ROOT/'parsed'/(hashlib.sha256(row['id'].encode()).hexdigest()+'.json');target.write_text(json.dumps(packet,ensure_ascii=False),'utf8')
                result['result']='verified-mirror'
            (CANDIDATES/(hashlib.sha256((row['id']+source).encode()).hexdigest()+'.json')).write_text(json.dumps(packet,ensure_ascii=False),'utf8')
        return result
    except Exception as e:result.update(result='search-failed',message=str(e)[:180]);return result
    finally:write(ROOT/'evidence/alternative-attempts.jsonl',result)
stats=collections.Counter()
with concurrent.futures.ThreadPoolExecutor(4) as pool:
    for i,result in enumerate(pool.map(search,rows),1):
        stats[result['result']]+=1
        if i%20==0:print({'done':i,'total':len(rows),'counts':dict(stats)},flush=True)
print(dict(stats),flush=True)
