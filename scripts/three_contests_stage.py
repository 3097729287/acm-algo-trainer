"""Add the three requested contests without replacing any existing content."""
import argparse
import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import sys
from three_contests_programs import ROOT, CONTENT, ROUNDS

sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from library import LibraryDatabase
from store import Store

OUT=ROOT/'.backups/three-contests'
TABLES=['problems','solutions','detailed_solutions','statements','solution_methods','links']

def load(path):return json.loads(Path(path).read_text('utf8'))
def dump(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf8',newline='\n')

def snapshot(source,target):
    source=Path(source).resolve();target=Path(target).resolve();target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():raise FileExistsError(target)
    with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as a,sqlite3.connect(target) as b:
        a.backup(b)
        assert b.execute('pragma quick_check').fetchone()[0]=='ok'

def additions():
    result={name:load(CONTENT/(name+'.json')) for name in ['problems','statements','solution_methods','links']}
    for table,variant in [('solutions','default'),('detailed_solutions','detailed')]:
        result[table]=[]
        for p in result['problems']:
            row=p['encoded'];key=next(key for key,s in ROUNDS.items() if row['contest']==s[1]+' '+s[2])
            letter=row['problem'];folder=CONTENT/key
            markdown=(folder/variant/(letter+'.md')).read_text('utf8')
            images={rel:'data:image/svg+xml;base64,'+base64.b64encode((folder/rel).read_bytes()).decode('ascii')
                    for rel in re.findall(r'!\[[^\]]*\]\((assets/[^)]+)\)',markdown)}
            code=re.findall(r'(?ms)^```cpp\s*\n(.*?)^```',markdown)
            expected=(folder/'programs'/letter/(letter.lower()+'.cpp')).read_text('utf8')
            assert len(code)==1 and code[0].strip()==expected.strip(),p['id']
            result[table].append({'problem_id':p['id'],'markdown':markdown,'images':images,
                'source_path':f'contest-editorials/20261102/{key}/{variant}/{letter}.md'})
    assert len(result['problems'])==16
    return result

def insert(database,packet):
    lib=LibraryDatabase(database)
    with lib.connection() as db:
        names={r[0] for r in db.execute("select name from sqlite_master where type='table'")}
        assert not names.intersection({'submissions','drafts','training','documents'}),'Use a public seed, never a personal database'
        db.execute('BEGIN IMMEDIATE')
        changed=0
        for p in packet['problems']:
            values=(p['id'],p['url'],json.dumps(p['raw'],ensure_ascii=False),json.dumps(p['encoded'],ensure_ascii=False))
            saved=db.execute('select id,url,raw,encoded from problems where id=?',(p['id'],)).fetchone()
            if saved:assert tuple(saved)==values,('Existing target differs',p['id'])
            else:db.execute('insert into problems values(?,?,?,?)',values);changed+=1
        for table in ['solutions','detailed_solutions']:
            for row in packet[table]:
                values=(row['problem_id'],row['markdown'],row['source_path'],json.dumps(row['images'],ensure_ascii=False),hashlib.sha256(row['markdown'].encode()).hexdigest())
                saved=db.execute('select * from '+table+' where problem_id=?',(row['problem_id'],)).fetchone()
                if saved:assert tuple(saved)==values,('Existing article differs',row['problem_id'])
                else:db.execute('insert into '+table+' values(?,?,?,?,?)',values)
        for table in ['statements','solution_methods']:
            for row in packet[table]:
                values=(row['problem_id'],json.dumps(row['content'],ensure_ascii=False))
                saved=db.execute('select * from '+table+' where problem_id=?',(row['problem_id'],)).fetchone()
                if saved:assert tuple(saved)==values,('Existing content differs',row['problem_id'])
                else:db.execute('insert into '+table+' values(?,?)',values)
        for row in packet['links']:
            assert db.execute('select 1 from lectures where id=?',(row['lecture_id'],)).fetchone(),row
            values=(row['problem_id'],row['lecture_id'],row['kind'],row['position'])
            saved=db.execute('select * from problem_lectures where problem_id=? and lecture_id=?',values[:2]).fetchone()
            if saved:assert tuple(saved)==values
            else:db.execute('insert into problem_lectures values(?,?,?,?)',values)
        if changed:
            LibraryDatabase._rebuild_urls(db)
            db.execute("insert into library_meta values('threeContests20261102','16-problems-32-articles') on conflict(key) do update set value=excluded.value")
            db.execute("update library_meta set value=cast(value as integer)+1 where key='revision'")
        assert not db.execute('pragma foreign_key_check').fetchall()
    return lib

def text_source(packet):
    for table in TABLES:
        path=ROOT/'data/library'/(table+'.json');saved=OUT/'source-before'/path.name
        saved.parent.mkdir(parents=True,exist_ok=True)
        if not saved.exists():shutil.copy2(path,saved)
        old=load(saved);result=deepcopy(old)
        key=(lambda x:(x['problem_id'],x['lecture_id'])) if table=='links' else (lambda x:x['id'] if table=='problems' else x['problem_id'])
        by_id={key(row):row for row in result}
        for row in packet[table]:
            identity=key(row)
            if identity in by_id:assert by_id[identity]==row,identity
            else:result.append(row);by_id[identity]=row
        assert result[:len(old)]==old
        dump(path,result)

def portable_seed(packet):
    path=OUT/'packet.sqlite3'
    if path.exists():return LibraryDatabase(path)
    lib=LibraryDatabase(path)
    wanted={row['lecture_id'] for row in packet['links']}
    with lib.connection() as db:
        for row in load(ROOT/'data/library/lectures.json'):
            if row['id'] not in wanted:continue
            content=json.dumps(row['content'],ensure_ascii=False)
            db.execute('insert into lectures values(?,?,?)',(row['id'],content,hashlib.sha256(content.encode()).hexdigest()))
    return insert(path,packet)

def upgrade_check(packet,seed):
    path=OUT/'upgrade-fixture.sqlite3';lib=LibraryDatabase(path)
    identity=packet['problems'][0]['id'];local='Local editorial amendment must survive public content installation.'
    with lib.connection() as db:
        p=packet['problems'][0]
        db.execute('insert or ignore into problems values(?,?,?,?)',(identity,p['url'],json.dumps(p['raw']),json.dumps(p['encoded'])))
        db.execute('insert or replace into solutions values(?,?,?,?,?)',(identity,local,'local-edit', '{}',hashlib.sha256(local.encode()).hexdigest()))
        own='local:private-import'
        db.execute('insert or ignore into problems values(?,?,?,?)',(own,'https://example.invalid/local',json.dumps({'_id':own,'场次':'个人导入','题号':'X','题名':'Keep local','知识点':'','难度':'','状态':'未做','日期':''}),json.dumps({'id':own,'title':'Keep local','source':'local'})))
    lib.merge_seed(seed.path)
    assert lib.solution(identity)['markdown']==local
    assert lib.find(own)
    for p in packet['problems']:
        assert lib.solution(p['id'],'detailed')
    dump(OUT/'upgrade-report.json',{'passed':True,'localEditorialPreserved':True,'localImportPreserved':True,'detailedArticles':16})

def export_readers(lib,packet):
    store=Store(data_file=OUT/'absent.md',library_file=lib.path,history_file=OUT/'fixture/history.jsonl')
    rows=[]
    for p in packet['problems']:
        value=store.solution(p['id'])
        assert value['markdown']!=value['detailedSolution']['markdown']
        assert value['methods'][0]['markdown']==value['markdown']
        assert value['methods'][0]['detailedSolution']==value['detailedSolution']
        assert lib.statement(p['id'])['integrity']['status']=='complete'
        rows.append(value)
    dump(OUT/'readers.json',{'readers':rows,'lectures':lib.lecture_index() if hasattr(lib,'lecture_index') else [],'statements':[row['content'] for row in packet['statements']]})

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--update-text-source',action='store_true');ap.add_argument('--seed',type=Path);args=ap.parse_args()
    OUT.mkdir(parents=True,exist_ok=True);packet=additions()
    seed=portable_seed(packet);counts=seed.check()
    assert counts['problems']==counts['solutions']==counts['detailed_solutions']==16
    upgrade_check(packet,seed)
    export_readers(seed,packet)
    if args.update_text_source:text_source(packet)
    if args.seed:
        baseline=OUT/'baseline.sqlite3';candidate=OUT/'candidate.sqlite3'
        if not baseline.exists():snapshot(args.seed,baseline)
        if not candidate.exists():snapshot(baseline,candidate)
        candidate_lib=insert(candidate,packet)
        assert candidate_lib.check()['solutions']>=counts['solutions']
    dump(OUT/'stage-report.json',{'passed':True,'problems':16,'articles':32,'lectureLinks':len(packet['links']),
      'counts':counts,'textSourceUpdated':args.update_text_source,'personalDatabasesModified':False})
    print('Staged 16 problems, 32 articles,',len(packet['links']),'lecture links; isolated upgrade preserved local edits/imports.')

if __name__=='__main__':main()
