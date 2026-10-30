import os
import concurrent.futures,hashlib,json,re,sys,threading
from pathlib import Path
ROOT=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve()
REPO=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).resolve().parent))
from fetch_all import Client,LOCAL,PARSED,RESULTS,write
from collections import defaultdict
from urllib.parse import urlsplit
import public_platforms
groups=defaultdict(list)
for row in json.loads((ROOT/'evidence/inventory.json').read_text('utf8')):
    m=re.fullmatch(r'https://codeforces.com/(contest|gym)/(\d+)/problem/([A-Z]\d?)',row['url'] or '')
    if m:groups[(m[1],m[2])].append((m[3],row))
def collect_group(item):
    (kind,cid),rows=item;LOCAL.sources=[];client=Client();source=f'https://codeforces.com/{kind}/{cid}/problems?locale=en'
    try:page=client.text(source)
    except Exception:return 0
    sources=list(LOCAL.sources)
    holders=list(re.finditer(r'<div\b[^>]*class="problemindexholder"[^>]*problemindex="([A-Z]\d?)"[^>]*>',page))
    sections={m[1]:page[m.start():holders[i+1].start() if i+1<len(holders) else page.find('<div class="footer',m.start()) if page.find('<div class="footer',m.start())>=0 else len(page)] for i,m in enumerate(holders)}
    count=0
    for letter,row in rows:
        target=PARSED/(hashlib.sha256(row['id'].encode()).hexdigest()+'.json')
        if target.exists() or letter not in sections:continue
        class Single:
            def text(self,url,headers=None):return sections[letter]
        try:
            value=public_platforms.statement(Single(),row['id'],row['title'],row['url'])
            packet={'statement':value,'sources':sources,'binding':{'sourceUrl':source,'contestId':cid,'problemIndex':letter}}
            temporary=target.with_suffix('.group.tmp');temporary.write_text(json.dumps(packet,ensure_ascii=False),'utf8');temporary.replace(target)
            write(RESULTS,{'id':row['id'],'url':row['url'],'result':'parsed-group','sourceUrl':source,'samples':len(value['samples'])});count+=1
        except Exception as e:write(RESULTS,{'id':row['id'],'url':row['url'],'result':'group-parse-failed','error':type(e).__name__,'message':str(e)[:180]})
    return count
count=0
with concurrent.futures.ThreadPoolExecutor(4) as pool:
    for i,n in enumerate(pool.map(collect_group,groups.items()),1):
        count+=n
        if i%10==0:print({'groups':i,'total':len(groups),'added':count},flush=True)
