import os
import collections,hashlib,json,sqlite3,sys,datetime,re,unicodedata
from pathlib import Path
ROOT=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve()
REPO=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).resolve().parent))
from prepare_corpus import canonical_prose
from fetch_all import write
rows=json.loads((ROOT/'evidence/inventory.json').read_text('utf8'));index=collections.defaultdict(list)
def title_key(text):return re.sub(r'\W+','',unicodedata.normalize('NFKC',text or '')).casefold()
def pairs(value):
    return [(s['input'].replace('\r\n','\n').rstrip('\n'),s['output'].replace('\r\n','\n').rstrip('\n')) for s in value.get('samples') or []]
for row in rows:
    path=ROOT/'parsed'/(hashlib.sha256(row['id'].encode()).hexdigest()+'.json')
    if not path.exists():continue
    index[title_key(row['title'])].append((row['id'],row['url'],path))
db=sqlite3.connect(ROOT/'baseline.sqlite3');old={p:json.loads(s) for p,s in db.execute('select problem_id,content from statements')}
count=0;unmatched=[]
for row in rows:
    path=ROOT/'parsed'/(hashlib.sha256(row['id'].encode()).hexdigest()+'.json')
    if path.exists() or row['id'] not in old:continue
    value=old[row['id']];key=canonical_prose(value.get('markdown'))
    matches=index.get(title_key(row['title']),[]) if len(key)>150 else []
    selected=None
    for identity,url,candidate in matches:
        if url==row['url']:continue
        packet=json.loads(candidate.read_text('utf8'))
        body=packet['statement'].get('markdown') or ''
        if len(body)>100000:continue
        if canonical_prose(body)==key and pairs(value)==pairs(packet['statement']):selected=(identity,url,packet);break
    if selected:
        identity,url,packet=selected;statement=dict(packet['statement'],id=row['id'],url=row['url'],title=row['title'],limits=value.get('limits') or packet['statement']['limits'])
        result={'statement':statement,'sources':packet['sources'],
            'binding':{'method':'all-body-prose-math-io-constraints-and-every-sample','originalUrl':row['url'],'mirrorUrl':url,'mirrorId':identity,
                'originalArchiveBodySha256':hashlib.sha256((value.get('markdown') or '').encode()).hexdigest(),
                'mirrorBodySha256':hashlib.sha256((packet['statement'].get('markdown') or '').encode()).hexdigest()}}
        path.write_text(json.dumps(result,ensure_ascii=False),'utf8');count+=1
        write(ROOT/'evidence/alternative-attempts.jsonl',{'id':row['id'],'url':url,'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':200,'result':'verified-existing-public-capture','binding':result['binding']})
    else:unmatched.append(row)
(ROOT/'evidence/remaining-source-gaps.json').write_text(json.dumps(unmatched,ensure_ascii=False,indent=2),'utf8')
print({'recovered':count,'remainingExistingArchives':len(unmatched)},flush=True)
