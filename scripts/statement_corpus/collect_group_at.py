import os
import concurrent.futures,hashlib,html,json,re,sys
from pathlib import Path
ROOT=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve()
REPO=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).resolve().parent))
from fetch_all import Client,LOCAL,PARSED,RESULTS,write
from collections import defaultdict
import public_platforms
from statement_format import Tree,plain
groups=defaultdict(list)
for row in json.loads((ROOT/'evidence/inventory.json').read_text('utf8')):
    m=re.fullmatch(r'https://atcoder.jp/contests/([^/]+)/tasks/([^/?]+)',row['url'] or '')
    if m:groups[m[1]].append(row)
def collect(item):
    cid,rows=item;LOCAL.sources=[];c=Client();source=f'https://atcoder.jp/contests/{cid}/tasks_print?lang=en';roster=f'https://atcoder.jp/contests/{cid}/tasks?lang=en'
    try:page=c.text(source);roster_page=c.text(roster)
    except Exception:return 0
    bindings={}
    for tr in Tree(roster_page).root.find(lambda n:n.tag=='tr'):
        links=list(tr.find(lambda n:n.tag=='a' and n.attrs.get('href','').startswith(f'/contests/{cid}/tasks/')))
        if len(links)>=2:bindings['https://atcoder.jp'+links[0].attrs['href']]=(plain(links[0]).strip(),plain(links[1]).strip())
    holders=list(re.finditer(r'<span class="h2">(.*?)</span>',page,re.S))
    sections={html.unescape(m[1]).strip():page[m.start():holders[i+1].start() if i+1<len(holders) else len(page)] for i,m in enumerate(holders)}
    count=0
    for row in rows:
        target=PARSED/(hashlib.sha256(row['id'].encode()).hexdigest()+'.json')
        if target.exists() or row['url'] not in bindings:continue
        letter,title=bindings[row['url']];heading=letter+' - '+title
        if heading not in sections:continue
        class Single:
            def text(self,url,headers=None):return sections[heading]
        try:
            value=public_platforms.statement(Single(),row['id'],row['title'],row['url'])
            packet={'statement':value,'sources':list(LOCAL.sources),'binding':{'sourceUrl':source,'sourceRosterUrl':roster,'taskId':row['url'].rsplit('/',1)[-1],'letter':letter}}
            tmp=target.with_suffix('.at-group.tmp');tmp.write_text(json.dumps(packet,ensure_ascii=False),'utf8');tmp.replace(target)
            write(RESULTS,{'id':row['id'],'url':row['url'],'result':'parsed-group','sourceUrl':source,'samples':len(value['samples'])});count+=1
        except Exception as e:write(RESULTS,{'id':row['id'],'url':row['url'],'result':'group-parse-failed','error':type(e).__name__,'message':str(e)[:180]})
    return count
count=0
with concurrent.futures.ThreadPoolExecutor(4) as pool:
    for i,n in enumerate(pool.map(collect,groups.items()),1):
        count+=n
        if i%10==0:print({'groups':i,'total':len(groups),'added':count},flush=True)
