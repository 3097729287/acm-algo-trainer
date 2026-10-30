import os
import concurrent.futures,hashlib,json,sys
from pathlib import Path
ROOT=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve()
REPO=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).resolve().parent))
from fetch_all import Client,LOCAL,PARSED,RESULTS,write,collect
import public_platforms
rows=json.loads((ROOT/'evidence/inventory.json').read_text('utf8'))
rows=[r for r in rows if ('missing' in r['issues'] or 'unreadable' in r['issues']) and not (PARSED/(hashlib.sha256(r['id'].encode()).hexdigest()+'.json')).exists()]
def retry(row):
    result=collect(row)
    if result!='failed' or 'codeforces.com' not in (row['url'] or ''):return result
    LOCAL.sources=[]
    class LocaleClient(Client):
        def text(self,url,headers=None):
            if '/problem/' in url and '?' not in url:url+='?locale=en'
            return super().text(url,headers)
    try:
        value=public_platforms.statement(LocaleClient(),row['id'],row['title'],row['url'])
        target=PARSED/(hashlib.sha256(row['id'].encode()).hexdigest()+'.json')
        target.write_text(json.dumps({'statement':value,'sources':LOCAL.sources},ensure_ascii=False),'utf8')
        write(RESULTS,{'id':row['id'],'url':row['url'],'result':'parsed-locale-retry'});return 'parsed-locale-retry'
    except Exception as e:
        write(RESULTS,{'id':row['id'],'url':row['url'],'result':'retry-failed','message':str(e)[:200]});return 'failed'
with concurrent.futures.ThreadPoolExecutor(4) as pool:
    for i,result in enumerate(pool.map(retry,rows),1):
        print({'done':i,'total':len(rows),'last':result},flush=True)
