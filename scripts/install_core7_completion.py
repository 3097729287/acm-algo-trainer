"""Append verified public editorials; never replace a personal SQLite database."""
import argparse,hashlib,json,re,shutil,sqlite3,sys
from contextlib import closing
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.backups/core7-complete-20261108'
PREFIX='data/core7-completion/'
REVISION='2026-11-08-live619-complete-v1'

def digest(value):return hashlib.sha256(value.encode('utf8')).hexdigest()
def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')
def read(path):return json.loads(path.read_text('utf8'))
def checksum(row):return digest(json.dumps(dict(row),ensure_ascii=False,sort_keys=True))

def prepare():
    source=ROOT/'data/library';roster=read(ROOT/'data/core7-completion/requested-roster.json');records=[]
    for path in sorted((ROOT/'data/core7-completion').glob('*/entry.json')):
        entry=read(path);pid=path.parent.name;code=(path.parent/'main.cpp').read_text('utf8');proof=entry['validation']
        assert proof['passed'] and not proof['failures'] and digest(code)==proof['programSha256'],pid
        assert proof['samples']+proof['independentCases']+len(proof.get('protocolCases',[]))>0,pid
        for edition,markdown in entry['variants'].items():
            blocks=re.findall(r'^```cpp\n(.*?)^```',markdown,re.M|re.S);assert blocks==[code],pid
            (path.parent/(edition+'.md')).write_text(markdown,encoding='utf8')
            records.append({'table':'solutions' if edition=='default' else 'detailed_solutions','problem_id':entry['problemId'],'markdown':markdown,'images':entry['images'],'source_path':PREFIX+pid+'/'+edition+'.md'})
    assert len(records)==632
    stats={};backup=WORK/'source-before-import';backup.mkdir(exist_ok=True)
    for table in ['solutions','detailed_solutions']:
        path=source/(table+'.json');oldBytes=path.read_bytes();rows=json.loads(oldBytes.decode('utf8'));by_id={r['problem_id']:r for r in rows};added=updated=0
        for incoming in (r for r in records if r['table']==table):
            row={k:v for k,v in incoming.items() if k!='table'};previous=by_id.get(row['problem_id'])
            if previous is None:rows.append(row);by_id[row['problem_id']]=row;added+=1
            elif previous!=row:
                assert previous.get('source_path','').startswith(PREFIX),'Concurrent or existing editorial: '+row['problem_id']
                previous.clear();previous.update(row);updated+=1
        assert path.read_bytes()==oldBytes,'Concurrent source mutation'
        if not (backup/path.name).exists():shutil.copy2(path,backup/path.name)
        dump(path,rows)
        original={r['problem_id']:r for r in read(backup/path.name)}
        stats[table]={'added':sum(r['problem_id'] not in original for r in rows),
                      'updatedExisting':sum(r['problem_id'] in original and r!=original[r['problem_id']] for r in rows),
                      'total':len(rows)}
    path=source/'solution_methods.json';raw=path.read_bytes();methods=json.loads(raw.decode('utf8'));known={r['problem_id']:r for r in methods};links=read(source/'links.json')
    for entryPath in sorted((ROOT/'data/core7-completion').glob('*/entry.json')):
        entry=read(entryPath);identity=entry['problemId'];proof=entry['validation']
        descriptor={'id':'core7-complete-20261108','legacy':True,'title':entry['method'],'lectureIds':list(dict.fromkeys(r['lecture_id'] for r in links if r['problem_id']==identity)),'validation':{'programSha256':proof['programSha256'],'officialSubmissionsSent':0,'sampleCases':proof['samples'],'independentInputGroups':proof['independentCases'],'protocolCases':len(proof.get('protocolCases',[]))}}
        if proof.get('semanticLimitation'):descriptor['validation']['semanticLimitation']=proof['semanticLimitation']
        row={'problem_id':identity,'content':{'primaryMethod':descriptor['id'],'methods':[descriptor]}}
        if identity not in known:methods.append(row);known[identity]=row
        elif known[identity]['content'].get('primaryMethod')==descriptor['id']:known[identity].update(row)
        # Existing alternate methods keep their identity and metadata intact.
    assert path.read_bytes()==raw,'Concurrent method mutation'
    if not (backup/path.name).exists():shutil.copy2(path,backup/path.name)
    dump(path,methods)
    defaults={r['problem_id'] for r in read(source/'solutions.json')};details={r['problem_id'] for r in read(source/'detailed_solutions.json')}
    missing=[p['pid'] for p in roster if p['id'] not in defaults or p['id'] not in details];assert not missing,missing
    validations=[read(p)['validation'] for p in (ROOT/'data/core7-completion').glob('*/entry.json')]
    audit={'revision':REVISION,'requestedProblems':len(roster),'stages':{s:sum(p['stage']==s for p in roster) for s in sorted({p['stage'] for p in roster})},'defaultAndDetailedAvailable':len(roster),'newProblems':len(validations),'newRequestedProblems':sum(any(p['id']==v['id'] for p in roster) for v in validations),'sampleCases':sum(v['samples'] for v in validations),'independentInputGroups':sum(v['independentCases'] for v in validations),'protocolCases':sum(len(v.get('protocolCases',[])) for v in validations),'semanticLimitations':{v['pid']:v['semanticLimitation'] for v in validations if v.get('semanticLimitation')},'originalJudgeSubmissions':0,'sourceChanges':stats}
    metaPath=source/'meta.json';meta=read(metaPath)
    if not (backup/metaPath.name).exists():shutil.copy2(metaPath,backup/metaPath.name)
    meta['core7CompletionRevision']=REVISION;meta['core7CompletionAudit']=json.dumps(audit,ensure_ascii=False,sort_keys=True);dump(metaPath,meta)
    problemIds={r['problem_id'] for r in records};plan={'revision':REVISION,'rows':records,'methods':[r for r in methods if r['problem_id'] in problemIds],'problems':[r for r in read(source/'problems.json') if r['id'] in problemIds],'audit':audit}
    dump(WORK/'install-plan.json',plan);dump(ROOT/'data/core7-completion/coverage.json',audit);print(json.dumps(audit,ensure_ascii=False))

def apply_database(path,backup):
    path=Path(path).resolve();backup=Path(backup).resolve();plan=read(WORK/'install-plan.json');assert not backup.exists()
    sys.path.insert(0,str(ROOT/'scripts'));from standardize_editorial_code import public_database
    backup.parent.mkdir(parents=True,exist_ok=True)
    with closing(sqlite3.connect(path,timeout=60)) as db:
        db.row_factory=sqlite3.Row;public_database(db)
        with closing(sqlite3.connect(backup)) as saved:db.backup(saved);assert saved.execute('PRAGMA quick_check').fetchone()[0]=='ok'
        changed={};preserved=[]
        with db:
            db.execute('BEGIN IMMEDIATE')
            for p in plan['problems']:
                if not db.execute('SELECT 1 FROM problems WHERE id=?',(p['id'],)).fetchone():
                    db.execute('INSERT INTO problems(id,url,raw,encoded) VALUES(?,?,?,?)',(p['id'],p['url'],json.dumps(p['raw'],ensure_ascii=False),json.dumps(p['encoded'],ensure_ascii=False)))
            for row in plan['rows']:
                table=row['table'];identity=row['problem_id'];assert table in ['solutions','detailed_solutions']
                current=db.execute('SELECT * FROM '+table+' WHERE problem_id=?',(identity,)).fetchone()
                if current and not current['source_path'].startswith(PREFIX):preserved.append({'table':table,'id':identity});continue
                new={'problem_id':identity,'markdown':row['markdown'],'source_path':row['source_path'],'images':json.dumps(row['images'],ensure_ascii=False),'digest':digest(row['markdown'])}
                if current and dict(current)==new:continue
                db.execute('INSERT INTO '+table+'(problem_id,markdown,source_path,images,digest) VALUES(?,?,?,?,?) ON CONFLICT(problem_id) DO UPDATE SET markdown=excluded.markdown,source_path=excluded.source_path,images=excluded.images,digest=excluded.digest',tuple(new.values()))
                db.execute('INSERT INTO bundled_items(table_name,item_id,digest) VALUES(?,?,?) ON CONFLICT(table_name,item_id) DO UPDATE SET digest=excluded.digest',(table,identity,checksum(new)))
                changed[table]=changed.get(table,0)+1
            for row in plan['methods']:
                current=db.execute('SELECT content FROM solution_methods WHERE problem_id=?',(row['problem_id'],)).fetchone()
                if current and json.loads(current[0]).get('primaryMethod')!='core7-complete-20261108':continue
                new={'problem_id':row['problem_id'],'content':json.dumps(row['content'],ensure_ascii=False)}
                db.execute('INSERT INTO solution_methods(problem_id,content) VALUES(?,?) ON CONFLICT(problem_id) DO UPDATE SET content=excluded.content',tuple(new.values()))
                db.execute('INSERT INTO bundled_items(table_name,item_id,digest) VALUES(?,?,?) ON CONFLICT(table_name,item_id) DO UPDATE SET digest=excluded.digest',('solution_methods',row['problem_id'],checksum(new)))
            for key,value in [('core7CompletionRevision',REVISION),('core7CompletionAudit',json.dumps(plan['audit'],ensure_ascii=False,sort_keys=True))]:
                db.execute('INSERT INTO library_meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(key,value))
            db.execute("UPDATE library_meta SET value=CAST(value AS INTEGER)+1 WHERE key='revision'")
            assert not db.execute('PRAGMA foreign_key_check').fetchall()
        assert db.execute('PRAGMA quick_check').fetchone()[0]=='ok'
    return {'database':str(path),'backup':str(backup),'changed':changed,'existingEditorialsPreserved':preserved,'integrity':True}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['prepare','apply']);parser.add_argument('--database',type=Path);parser.add_argument('--backup',type=Path);args=parser.parse_args()
    if args.action=='prepare':prepare()
    else:
        assert args.database and args.backup;result=apply_database(args.database,args.backup);print(json.dumps(result,ensure_ascii=False))
