"""Add only Gym 728862 content, preserving all existing library records."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from library import LibraryDatabase
from store import Store

CONTENT=ROOT/'data/school-training/728862'
PREFIX='remote:codeforces:728862::'

def load(path):return json.loads(path.read_text(encoding='utf8'))
def snapshot(source,target):
    source=Path(source).resolve();target=Path(target).resolve();target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():raise FileExistsError(target)
    with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as a,sqlite3.connect(target) as b:
        a.backup(b)
        assert b.execute('pragma quick_check').fetchone()[0]=='ok'

def additions():
    result={name:load(CONTENT/(name+'.json')) for name in ['problems','statements','solution_methods','links']}
    for table,folder in [('solutions','default'),('detailed_solutions','detailed')]:
        result[table]=[]
        for p in result['problems']:
            identity=p['id'];letter=p['encoded']['problem'];markdown=(CONTENT/folder/(letter+'.md')).read_text(encoding='utf8')
            images={path:'data:image/svg+xml;base64,'+base64.b64encode((CONTENT/path).read_bytes()).decode('ascii') for path in re.findall(r'!\[[^\]]*\]\((assets/[^)]+)\)',markdown)}
            result[table].append({'problem_id':identity,'markdown':markdown,'source_path':f'school-training/728862/{folder}/{letter}.md','images':images})
    return result

def insert(database,packet):
    """Additive transaction: no existing educational content is replaced."""
    library=LibraryDatabase(database)
    with library.connection() as db:
        tables={r[0] for r in db.execute("select name from sqlite_master where type='table'")}
        assert not tables.intersection({'submissions','drafts','training','documents'}),'Expected the public seed, not a personal database'
        db.execute('BEGIN IMMEDIATE')
        count=0
        for p in packet['problems']:
            assert p['id'].startswith(PREFIX)
            values=(p['id'],p['url'],json.dumps(p['raw'],ensure_ascii=False),json.dumps(p['encoded'],ensure_ascii=False))
            saved=db.execute('select id,url,raw,encoded from problems where id=?',(p['id'],)).fetchone()
            if saved:
                assert tuple(saved)==values,'Existing target problem differs; keep it for explicit reconciliation'
                continue
            db.execute('insert into problems values(?,?,?,?)',values);count+=1
        for table in ['solutions','detailed_solutions']:
            for s in packet[table]:
                values=(s['problem_id'],s['markdown'],s['source_path'],json.dumps(s['images'],ensure_ascii=False),hashlib.sha256(s['markdown'].encode()).hexdigest())
                saved=db.execute('select * from '+table+' where problem_id=?',(s['problem_id'],)).fetchone()
                if saved:assert tuple(saved)==values
                else:db.execute('insert into '+table+' values(?,?,?,?,?)',values)
        for table in ['statements','solution_methods']:
            for s in packet[table]:
                values=(s['problem_id'],json.dumps(s['content'],ensure_ascii=False))
                saved=db.execute('select * from '+table+' where problem_id=?',(s['problem_id'],)).fetchone()
                if saved:assert tuple(saved)==values
                else:db.execute('insert into '+table+' values(?,?)',values)
        for s in packet['links']:
            assert db.execute('select 1 from lectures where id=?',(s['lecture_id'],)).fetchone(),s
            values=(s['problem_id'],s['lecture_id'],s['kind'],s['position'])
            saved=db.execute('select * from problem_lectures where problem_id=? and lecture_id=?',values[:2]).fetchone()
            if saved:assert tuple(saved)==values
            else:db.execute('insert into problem_lectures values(?,?,?,?)',values)
        if count:
            LibraryDatabase._rebuild_urls(db)
            db.execute("insert into library_meta values('schoolTraining728862','2026-11-01') on conflict(key) do update set value=excluded.value")
            db.execute("update library_meta set value=cast(value as integer)+1 where key='revision'")
        assert not db.execute('pragma foreign_key_check').fetchall()
    return library

def text_source(packet):
    before=ROOT/'.backups/school728862/source-before';before.mkdir(parents=True,exist_ok=True)
    for table in ['problems','solutions','detailed_solutions','statements','solution_methods','links']:
        path=ROOT/'data/library'/(table+'.json')
        copy=before/path.name
        if not copy.exists():copy.write_bytes(path.read_bytes())
        old=load(copy)
        if table=='links':key=lambda v:(v['problem_id'],v['lecture_id'])
        else:key=lambda v:v['id'] if table=='problems' else v['problem_id']
        mapping={key(v):v for v in old}
        for item in packet[table]:
            identity=key(item)
            if identity in mapping:assert mapping[identity]==item
            else:old.append(item);mapping[identity]=item
        # Preserve the previous list order: the review should contain only the
        # twelve additions and their links, not a whole-corpus reorder.
        path.write_text(json.dumps(old,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8',newline='\n')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--seed',type=Path,required=True)
    ap.add_argument('--update-text-source',action='store_true');args=ap.parse_args()
    output=ROOT/'.backups/school728862';output.mkdir(parents=True,exist_ok=True)
    baseline=output/'baseline.sqlite3';candidate=ROOT/'data/library.sqlite3'
    if not baseline.exists():snapshot(args.seed,baseline)
    if not candidate.exists():snapshot(baseline,candidate)
    packet=additions();library=insert(candidate,packet)
    expected={p['id'] for p in packet['problems']}
    store=Store(data_file=output/'absent.md',library_file=candidate,history_file=output/'fixture/history.jsonl')
    rows=[row for row in store.data()['rows'] if row['id'] in expected]
    assert {r['id'] for r in rows}==expected
    assert all(r['schoolTraining'] and not r.get('catalogHidden') for r in rows)
    for identity in expected:
        value=store.solution(identity)
        assert value['methods'][0]['markdown']==value['markdown']
        assert value['methods'][0]['detailedSolution']==value['detailedSolution']
        assert value['markdown']!=value['detailedSolution']['markdown']
        assert library.statement(identity)['integrity']['status']=='complete'
    if args.update_text_source:text_source(packet)
    report={'count':len(rows),'articles':2*len(rows),'references':len(packet['links']),'counts':library.check(),
      'seed':str(args.seed),'candidate':str(candidate),'personalDatabasesModified':False,'textSourceUpdated':args.update_text_source}
    (output/'stage-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
