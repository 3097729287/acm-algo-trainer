import os
import json,sqlite3,sys
from pathlib import Path
ROOT=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve()
REPO=Path(__file__).resolve().parents[2];sys.path.insert(0,str(REPO/'backend'))
from statement_asset_store import hydrate
db=sqlite3.connect(REPO/'data/library.sqlite3');db.row_factory=sqlite3.Row;rows=[]
for row in db.execute('select p.id,p.encoded,s.content from problems p join statements s on s.problem_id=p.id'):
    s=json.loads(row['content'])
    if (s.get('integrity') or {}).get('status')!='complete' or not s.get('statementPdf'):continue
    pdf=hydrate({'statementPdf':s['statementPdf']},db)['statementPdf']
    rows.append({'originalId':row['id'],'id':'pdf-fixture','title':s['title'],'url':s['url'],
        'markdown':s.get('currentSourceMarkdown') or s['markdown'],'statementAvailable':True,'statementPdf':pdf,
        'samples':s['samples'],'limits':s['limits'],'judge':{'scope':'unsupported','cases':0},'draft':'// preserved fixture draft','submissions':[]})
(ROOT/'native-render-corpus.json').write_text(json.dumps(rows,ensure_ascii=False),'utf8')
print(len(rows))
