import os
import concurrent.futures,datetime,difflib,hashlib,html,json,re,sqlite3,sys
from pathlib import Path
ROOT=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve()
REPO=Path(__file__).resolve().parents[2];sys.path[:0]=[str(Path(__file__).resolve().parent),str(REPO/'backend'),str(REPO/'backend/common')]
from fetch_all import Client,LOCAL,write
import public_platforms
issues=json.loads((ROOT/'evidence/corpus-render.json').read_text('utf8'))['issues']
db=sqlite3.connect(ROOT/'baseline.sqlite3');meta={i:json.loads(e) for i,e in db.execute('select id,encoded from problems')}
rows=[]
for issue in issues:
    row=meta.get(issue['id']) or {};match=re.fullmatch(r'https://www.luogu.com.cn/problem/CF(\d+)([A-Z]\d?)',row.get('url',''))
    if match:rows.append((issue['id'],row,match.groups()))
folder=ROOT/'render-recoveries';folder.mkdir(exist_ok=True)
def collect(args):
    identity,row,parts=args;LOCAL.sources=[];url='https://codeforces.com/problemset/problem/'+parts[0]+'/'+parts[1]
    result={'id':identity,'url':url,'time':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        old=json.loads((ROOT/'parsed'/(hashlib.sha256(identity.encode()).hexdigest()+'.json')).read_text('utf8'))['statement']
        value=public_platforms.statement(Client(),identity,row['title'],url)
        pairs=lambda samples:[(s['input'].replace('\r\n','\n').rstrip('\n'),s['output'].replace('\r\n','\n').rstrip('\n')) for s in samples]
        assert pairs(old['samples'])==pairs(value['samples']),'Original sample bytes differ'
        def words(s):return re.findall(r'[a-z]{2,}|\d+',html.unescape(re.sub(r'\\[A-Za-z]+','',s)).lower())
        similarity=difflib.SequenceMatcher(None,words(old['markdown']),words(value['markdown']),autojunk=False).ratio()
        assert similarity>=.8,('Full source alignment requires review',similarity)
        assert (value.get('integrity') or {}).get('status')=='complete',value.get('resourceIssues')
        proof={'method':'explicit-luogu-CF-source-identity-native-header-full-text-alignment-and-all-samples',
            'mirrorUrl':row['url'],'originalUrl':url,'sourceProblemId':'CF'+''.join(parts),'textAlignment':similarity,
            'mirrorMarkdownSha256':hashlib.sha256(old['markdown'].encode()).hexdigest(),'allSamplesEqual':True}
        packet={'statement':value,'sources':list(LOCAL.sources),'binding':proof}
        (folder/(hashlib.sha256(identity.encode()).hexdigest()+'.json')).write_text(json.dumps(packet,ensure_ascii=False),'utf8')
        result.update(result='verified-original-for-render-repair',binding=proof)
    except Exception as e:result.update(result='native-render-source-unverified',error=str(e)[:250])
    write(ROOT/'evidence/alternative-attempts.jsonl',result);return result
with concurrent.futures.ThreadPoolExecutor(8) as pool:results=list(pool.map(collect,rows))
(ROOT/'evidence/render-source-recoveries.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),'utf8')
print({'attempted':len(results),'verified':sum(r['result']=='verified-original-for-render-repair' for r in results)},flush=True)
