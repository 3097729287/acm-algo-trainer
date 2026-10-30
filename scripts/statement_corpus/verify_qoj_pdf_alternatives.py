import os
import collections,datetime,hashlib,json,re,sqlite3,sys
from pathlib import Path
ROOT=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve()
REPO=Path(__file__).resolve().parents[2];sys.path[:0]=[str(Path(__file__).resolve().parent),str(REPO/'backend')]
from fetch_all import Client,LOCAL,write
from qoj import pdf_statement
from codeforces_pdf import roster,normalized
from contest_translations import xcpc_name
from statement_format import Tree,plain
from reparse_evidence import Replay
db=sqlite3.connect(ROOT/'baseline.sqlite3');meta={i:json.loads(e) for i,e in db.execute('select id,encoded from problems')};old={i:json.loads(s) for i,s in db.execute('select problem_id,content from statements')}
stats=collections.Counter();rosters={}
for file in (ROOT/'qoj-alternatives').glob('*.json'):
    packet=json.loads(file.read_text('utf8'));identity=packet['originalId'];value=packet['statement'];target=ROOT/'parsed'/(hashlib.sha256(identity.encode()).hexdigest()+'.json')
    if target.exists() or not value.get('sourcePdfUrl'):continue
    row=meta[identity];match=re.fullmatch(r'https://codeforces.com/gym/(\d+)/problem/([A-Z]\d?)',row['url'] or '')
    if not match:continue
    cid,letter=match.groups();source=value['url'];expected=xcpc_name(row.get('contestFullName') or row.get('contest'))
    try:
        text=(value.get('sourceText') or '').replace('\r','');header='\n'.join(text.splitlines()[:4])
        label=re.search(r'(?m)^\s*Problem\s+([A-Z]\d?)(?:[.: \t]*\n|[.: \t]+)([^\n]*)',text[:600])
        if not label or label[1]!=letter:stats['letter-not-verified']+=1;continue
        if normalized(label[2])!=normalized(row['title']):stats['pdf-title-not-verified']+=1;continue
        observed=xcpc_name(header)
        client=Replay(packet,{'url':source});page=client.text(source);members=[]
        for node in Tree(page).root.find(lambda n:n.tag=='a' and re.match(r'/contest/\d+',n.attrs.get('href',''))):
            name=xcpc_name(plain(node).strip())
            if name:members.append(name)
        if not expected or observed!=expected and expected not in members:stats['event-not-verified']+=1;continue
        if cid not in rosters:
            LOCAL.sources=[];c=Client();roster_url='https://codeforces.com/gym/'+cid;raw=c.text(roster_url)
            rosters[cid]=(roster(raw,cid),list(LOCAL.sources),roster_url)
        tasks,roster_sources,roster_url=rosters[cid]
        if letter not in tasks or normalized(tasks[letter]['title'])!=normalized(row['title']):stats['native-roster-not-verified']+=1;continue
        data=client.bytes(value['sourcePdfUrl']);fresh=pdf_statement(data,source.rsplit('/',1)[-1],render_pages=False)
        def pairs(s):return [(' '.join(x['input'].split()),' '.join(x['output'].split())) for x in s or []]
        if old.get(identity,{}).get('samples') and pairs(old[identity]['samples'])!=pairs(fresh['samples']):stats['samples-not-verified']+=1;continue
        value.update(fresh,id=identity,url=row['url'],limits=tasks[letter]['limits'],originalSource=source,sourceStatementUrl=source,statementAvailable=True)
        # Keep the already verified original PDF and its native viewer payload.
        value['markdown']='# '+row['title']+'\n\n[PDF]('+value['sourcePdfUrl']+')'
        packet.update(statement=value,sources=packet['sources']+roster_sources,verifiedIdentity=True,
            binding={'method':'native-event-roster-explicit-pdf-letter-title-and-all-available-samples','originalUrl':row['url'],'mirrorUrl':source,
                'originalRosterUrl':roster_url,'letter':letter,'expectedEvent':expected,'pdfEvent':observed,'publishedMemberships':members,
                'pdfSha256':hashlib.sha256(data).hexdigest(),'pdfHeader':header})
        target.write_text(json.dumps(packet,ensure_ascii=False),'utf8');stats['verified']+=1
        write(ROOT/'evidence/alternative-attempts.jsonl',{'id':identity,'url':source,'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':200,'result':'verified-formal-pdf-mirror','binding':packet['binding']})
    except Exception as e:stats['failed']+=1;write(ROOT/'evidence/alternative-attempts.jsonl',{'id':identity,'url':source,'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'result':'pdf-identity-not-verified','message':str(e)[:180]})
print(dict(stats),flush=True)
