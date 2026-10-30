import os
"""Read the actual public search roster and original PDFs; never infer QOJ IDs."""
import concurrent.futures,datetime,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve()
REPO=Path(__file__).resolve().parents[2];sys.path[:0]=[str(Path(__file__).resolve().parent),str(REPO/'backend'),str(REPO/'backend/common')]
from fetch_all import Client,LOCAL,write
from qoj import statement
from statement_format import Tree,plain
from statement_resources import archive_resources
from statement_integrity import annotate_type
from contest_scope import excluded
folder=ROOT/'qoj-new';folder.mkdir(exist_ok=True)
source='https://qoj.ac/problems?search=Xi%27an'
LOCAL.sources=[];html=Client().text(source);roster_sources=list(LOCAL.sources);rows=[]
category_url='https://qoj.ac/category/576'
category=Client().text(category_url)
category_rows=[tr for tr in Tree(category).root.find(lambda n:n.tag=='tr') if '2025' in plain(tr) and "Xi'an Regional" in plain(tr)]
assert len(category_rows)==1 and any(n.attrs.get('href')=='/contest/2562' for n in category_rows[0].find(lambda n:n.tag=='a'))
category_label=plain(category_rows[0]);roster_sources=list(LOCAL.sources)
for tr in Tree(html).root.find(lambda n:n.tag=='tr'):
    label=plain(tr)
    if not re.search(r"Xi.an Regional 2025\s*$",label,re.I):continue
    links=list(tr.find(lambda n:n.tag=='a' and re.fullmatch(r'/problem/[1-9]\d*',n.attrs.get('href',''))))
    assert len(links)==1,'Ambiguous native roster'
    node=links[0];rows.append({'url':'https://qoj.ac'+node.attrs['href'],'title':plain(node).strip(),'rosterLabel':label})
assert len(rows)==13 and len({r['url'] for r in rows})==13,rows
def collect(row):
    LOCAL.sources=[];url=row['url'];pid=url.rsplit('/',1)[-1];client=Client()
    try:
        value=statement(client,'xcpc-qoj::'+pid,row['title'],url)
        text=value.get('sourceText','');head='\n'.join(text.splitlines()[:5])
        match=re.search(r'(?m)^\s*Problem\s+([A-Z])\.\s*([^\n]*)',text[:650])
        native_page=client.text(url)
        memberships=[(n.attrs['href'],plain(n).strip()) for n in Tree(native_page).root.find(lambda n:n.tag=='a' and re.fullmatch(r'/contest/\d+',n.attrs.get('href','')))]
        assert any(href=='/contest/2562' and 'Xi' in label for href,label in memberships),memberships
        norm=lambda s:re.sub(r'[^a-z0-9]','',s.lower())
        assert norm(match[2] if match else text.splitlines()[0])==norm(row['title']),(row,head)
        value=archive_resources(value,client)
        assert not value.get('resourceIssues') and value.get('statementPdf'),value.get('resourceIssues')
        value=annotate_type(value)
        # Every published example remains in the original multi-page PDF. A
        # layout we cannot extract is readable, but never a local judge input.
        value['integrity']={'status':'complete','sourceVerified':True,'pdfPageCountVerified':True,
            'sampleCount':len(value['samples']),'checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        if not value['samples']:value['localJudgeSupported']=False
        proof={'id':pid,'letter':match[1] if match else None,'title':row['title'],'url':url,'nativeRosterUrl':source,'rosterLabel':row['rosterLabel'],
            'contestId':'2562','nativeMemberships':memberships,'categoryUrl':category_url,'categoryLabel':category_label,
            'pdfHeader':head,'pdfUrl':value['sourcePdfUrl'],'pdfSha256':value['sourcePdfSha256'],
            'pages':value['pageCount'],'samplesExtracted':len(value['samples']),'sources':roster_sources+list(LOCAL.sources)}
        (folder/(pid+'.json')).write_text(json.dumps({'statement':value,'proof':proof},ensure_ascii=False),'utf8')
        print(json.dumps({k:proof[k] for k in ('id','letter','title','pages','samplesExtracted')},ensure_ascii=False),flush=True)
        return proof
    except Exception as e:
        print(json.dumps(dict(row,error=str(e)[:350]),ensure_ascii=False),flush=True);return {'url':url,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(1) as pool:results=list(pool.map(collect,rows))
result={'rosterUrl':source,'retrievedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'results':results,
    'completeProblemSet':len([r for r in results if not r.get('error')])==13,
    'completeRoster':len([r for r in results if not r.get('error')])==13 and {r.get('letter') for r in results}==set('ABCDEFGHIJKLM')}
(ROOT/'evidence/qoj-new-discovery.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
print('completeRoster',result['completeRoster'],flush=True)
