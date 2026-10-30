import os
import json,sqlite3
from pathlib import Path
ROOT=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve()
REPO=Path(__file__).resolve().parents[2];rows=[]
db=sqlite3.connect(REPO/'data/library.sqlite3')
for identity,content in db.execute('select problem_id,content from statements'):
    s=json.loads(content);t=s.get('translation') or {}
    if (s.get('integrity') or {}).get('status')!='complete' or not t.get('markdown'):continue
    rows.append({'id':identity,'title':s.get('title',''),'markdown':t['markdown']+'\n\n'+s.get('statementSupplement',''),
                 'samples':s['samples'],'nativePdf':False})
(ROOT/'render-chinese.json').write_text(json.dumps(rows,ensure_ascii=False),'utf8');print(len(rows))
