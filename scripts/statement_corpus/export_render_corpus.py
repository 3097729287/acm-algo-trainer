import os
import json,sqlite3
from pathlib import Path
ROOT=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve()
REPO=Path(__file__).resolve().parents[2]
db=sqlite3.connect(REPO/'data/library.sqlite3');rows=[]
for identity,encoded,content in db.execute('select p.id,p.encoded,s.content from problems p join statements s on s.problem_id=p.id'):
    meta=json.loads(encoded);s=json.loads(content)
    if (s.get('integrity') or {}).get('status')!='complete':continue
    rows.append({'id':identity,'title':s.get('title',meta['title']),'markdown':s.get('currentSourceMarkdown') or s.get('markdown',''),
        'samples':s.get('samples',[]),'nativePdf':bool(s.get('statementPdf'))})
(ROOT/'render-corpus.json').write_text(json.dumps(rows,ensure_ascii=False),'utf8')
print(len(rows))
