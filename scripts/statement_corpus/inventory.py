import os
import base64,collections,hashlib,json,re,sqlite3,sys
from pathlib import Path
from urllib.parse import urlsplit
from PIL import Image
import io
root=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve()
REPO=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(REPO/'backend'),str(REPO/'backend/common')]
from statement_quality import has_body
from statement_cleanup import clean_statement
from contest_scope import excluded
db=sqlite3.connect(root/'baseline.sqlite3');db.row_factory=sqlite3.Row
rows=[];stats=collections.Counter();hosts=collections.Counter();assets={}
for row in db.execute('select p.*,s.content from problems p left join statements s on p.id=s.problem_id order by p.id'):
    p=json.loads(row['encoded']);s=json.loads(row['content']) if row['content'] else {};text=s.get('markdown') or '';clean=clean_statement(s) if s else {}
    issues=[];host=urlsplit(row['url'] or '').hostname or 'none';hosts[host]+=1
    if not s:issues.append('missing')
    elif not clean.get('statementAvailable'):issues.append('unreadable')
    if s and not s.get('samples'):issues.append('no_samples_requires_type_review')
    if s and len(re.sub(r'\W','',text))<120:issues.append('short_requires_source_review')
    if re.search(r'(?i)this is an interactive problem|this problem is interactive|交互题|交互式题|communication task|output.only|提交答案|答案提交',text):issues.append('special_type_requires_review')
    refs=re.findall(r'!\[[^\]]*\]\(([^\s)]+)',text)
    links=re.findall(r'(?<!!)\[[^\]]*\]\(([^\s)]+)',text)
    imgs=s.get('images') or {}
    for ref in dict.fromkeys(refs):
        value=imgs.get(ref,ref)
        if value.startswith(('https://','http://')):issues.append('external_image');assets.setdefault(value,set()).add(row['id'])
        elif value.startswith('data:image/'):
            try:
                data=base64.b64decode(value.split(',',1)[1],validate=True)
                if value.startswith('data:image/svg'):assert b'<svg' in data
                else:
                    with Image.open(io.BytesIO(data)) as im:im.verify()
            except Exception:issues.append('invalid_embedded_image')
        else:issues.append('unresolved_image')
    attachments=[x for x in links if re.search(r'\.(?:pdf|zip|gif|png|jpg|jpeg|txt|in|out|cpp|h|py|tgz|gz|7z)(?:[?#]|$)|download|attachment',x,re.I)]
    if attachments:issues.append('attachment_requires_offline_review')
    record={'id':row['id'],'url':row['url'],'title':p.get('title'),'platform':p.get('platform'),'source':p.get('source'),'contest':p.get('contest'),'catalogHidden':bool(p.get('catalogHidden')),'chars':len(text),'samples':len(s.get('samples') or []),'statementVersion':s.get('statementVersion'),'markdownSha256':hashlib.sha256(text.encode()).hexdigest(),'issues':sorted(set(issues)),'images':refs,'attachments':attachments}
    rows.append(record);stats.update(set(issues));stats['total']+=1
    if s:stats['stored']+=1
    if clean.get('statementAvailable'):stats['readable_by_old_gate']+=1
for name,value in [('inventory',rows),('asset-urls',{k:sorted(v) for k,v in assets.items()}),('inventory-summary',{'counts':stats,'hosts':hosts})]:
    (root/'evidence'/f'{name}.json').write_text(json.dumps(value,ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'counts':stats,'hosts':hosts},ensure_ascii=False,indent=2))
print('statement keys',collections.Counter(k for x, in db.execute('select content from statements') for k in json.loads(x)))
for h in hosts:
    print(h,collections.Counter(z for x in rows if urlsplit(x['url'] or '').hostname==h for z in x['issues']))
print('missing first',json.dumps([x for x in rows if 'missing' in x['issues']][:5],ensure_ascii=False))
