import os
import concurrent.futures,datetime,hashlib,json,sys
from pathlib import Path
from urllib.parse import quote
ROOT=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve()
REPO=Path(__file__).resolve().parents[2];sys.path[:0]=[str(Path(__file__).resolve().parent),str(REPO/'backend')]
from fetch_all import Client,LOCAL,write
from statement_format import Tree,plain
ids=set()
for name in ('corpus-render-review.json','chinese-corpus-render.json'):
    ids.update(r['id'] for r in json.loads((ROOT/'evidence'/name).read_text('utf8'))['issues'])
problems={r['id']:r['encoded'] for r in json.loads((REPO/'data/library/problems.json').read_text('utf8'))}
def check(identity):
    LOCAL.sources=[];url='https://qoj.ac/problems?search='+quote(problems[identity]['title'],safe='')
    record={'id':identity,'url':url,'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'purpose':'formal-alternative-for-unrenderable-source-math'}
    try:
        text=Client().text(url);candidates=[{'url':'https://qoj.ac'+n.attrs['href'],'title':plain(n).strip()} for n in Tree(text).root.find(lambda n:n.tag=='a' and n.attrs.get('href','').startswith('/problem/'))]
        record.update(result='searched-no-verified-equivalent',candidates=candidates,sourceSha256=hashlib.sha256(text.encode()).hexdigest())
    except Exception as e:record.update(result='alternative-search-transient-or-unavailable',status=getattr(e,'code',None),error=str(e)[:180])
    write(ROOT/'evidence/alternative-attempts.jsonl',record);return record
with concurrent.futures.ThreadPoolExecutor(4) as pool:results=list(pool.map(check,sorted(ids)))
(ROOT/'evidence/render-alternative-search.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),'utf8')
print({'attempted':len(results),'verifiedAdditionalCompletions':0},flush=True)
