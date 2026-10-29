"""Read only problem/list navigation fields, never progress, drafts or accounts."""
from contextlib import closing
import json
import sqlite3
from core7_authoring import ROOT,OUT

installation=ROOT.parents[1]/'版本/最新版/程序'
path=installation/'state/tb-library.sqlite3'
fields=['id','url','title','difficulty','knowledge','tags','aliasIds','nativeDifficulty','difficultyHidden']
projection=','.join("json_extract(encoded,'$."+k+"') AS "+k for k in fields)
with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
    db.row_factory=sqlite3.Row
    rows=[]
    for item in db.execute('SELECT '+projection+' FROM problems'):
        row=dict(item)
        for key in ['tags','aliasIds']:
            row[key]=json.loads(row[key]) if row[key] else []
        rows.append(row)
    lists=[]
    for item in db.execute("SELECT content FROM training_lists WHERE COALESCE(json_extract(content,'$.custom'),0)=0"):
        value=json.loads(item['content'])
        allowed=['id','title','displayTitle','originalTitle','topicPath','sourceLabel','available','aggregateChildren','children','categories','problems','url']
        lists.append({key:value[key] for key in allowed if key in value})
(OUT/'live-navigation-fields.json').write_text(json.dumps({'rows':rows,'lists':lists},ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'navigationProblemRows':len(rows),'publicLists':len(lists),'openedReadonly':True,'progressFieldsRead':False}))
