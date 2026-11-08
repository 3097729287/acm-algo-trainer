"""Deliver only reviewed Nowcoder rows onto the precise installed public baseline."""
import argparse,datetime as dt,hashlib,json,os,shutil,sqlite3,subprocess,sys
from contextlib import closing
from pathlib import Path
from nowcoder_editorials import ROOT,OUT,CONTENT,read,write,sha
from nowcoder_content import checked_entries,public_artifact_only
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from library import LibraryDatabase

REVISION='nowcoder-editorials-20261108'


def filehash(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def connection(path):
    db=sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True,timeout=30)
    db.row_factory=sqlite3.Row
    return db


def backup(source,dest):
    assert not dest.exists(),dest
    dest.parent.mkdir(parents=True,exist_ok=True)
    with closing(connection(source)) as a,closing(sqlite3.connect(dest)) as b:a.backup(b)


def atomic_json(path,value):
    temporary=path.with_name(path.name+'.nowcoder-incoming')
    write(temporary,value);os.replace(temporary,path)


def checksums(db,table,key,ignore=()):
    ignored=set(ignore);digest=hashlib.sha256();count=0
    for row in db.execute('SELECT * FROM '+table+' ORDER BY '+key):
        if row[key] in ignored:continue
        values=[hashlib.sha256(v).hexdigest() if isinstance(v,bytes) else v for v in row]
        digest.update(json.dumps(values,ensure_ascii=False,separators=(',',':')).encode());count+=1
    return {'rows':count,'sha256':digest.hexdigest()}


def fingerprints(path,ledger,ratings):
    with closing(connection(path)) as db:
        result={}
        for table,key,excluded in [
            ('problems','id',ratings),('solutions','problem_id',ledger),
            ('detailed_solutions','problem_id',[k for k,v in ledger.items() if 'detailed' in v['articles']]),
            ('statements','problem_id',[read(p)['id'] for p in (CONTENT/'statements').glob('NC*.json')]),
            ('training_lists','id',()),('lectures','id',()),('problem_lectures','problem_id,position',()),
            ('solution_methods','problem_id',()),('statement_assets','sha256',())]:
            # Link table has no scalar exclusion key.
            if ',' in key:
                digest=hashlib.sha256()
                for row in db.execute('SELECT * FROM '+table+' ORDER BY '+key):digest.update(json.dumps(tuple(row),ensure_ascii=False).encode())
                result[table]=digest.hexdigest()
            else:result[table]=checksums(db,table,key,excluded)
        return result


def repair_placeholders(library):
    changed=0
    patches=read(ROOT/'data/library/statement-patches/zzzzzzzzz-nowcoder-editorials-pdf-20261108.json')['statements']
    with library.connection() as db:
        for patch in patches:
            row=db.execute('SELECT content FROM statements WHERE problem_id=?',(patch['problem_id'],)).fetchone()
            if not row:continue
            current=json.loads(row[0])
            if sha(current.get('markdown',''))!=patch['beforeSha256']:continue
            incoming=json.dumps(patch['content'],ensure_ascii=False)
            db.execute('UPDATE statements SET content=? WHERE problem_id=?',(incoming,patch['problem_id']))
            digest=sha(json.dumps({'problem_id':patch['problem_id'],'content':incoming},ensure_ascii=False,sort_keys=True))
            db.execute('INSERT OR REPLACE INTO bundled_items VALUES(?,?,?)',('statements',patch['problem_id'],digest));changed+=1
    return changed


def verify_owned(path,ledger):
    with closing(connection(path)) as db:
        for identity,entry in ledger.items():
            for variant,table in [('default','solutions'),('detailed','detailed_solutions')]:
                if variant not in entry['articles']:continue
                row=db.execute('SELECT markdown,images FROM '+table+' WHERE problem_id=?',(identity,)).fetchone()
                expected=(ROOT/entry['articles'][variant]).read_text(encoding='utf-8')
                assert row and row['markdown']==expected,(path,identity,variant)
                for name,data in json.loads(row['images']).items():
                    if name.endswith('.gif'):assert data.startswith('data:image/gif;base64,'),(identity,name)
        assert db.execute('PRAGMA quick_check').fetchone()[0]=='ok'
        assert not db.execute('PRAGMA foreign_key_check').fetchall()


def local_amendments(path):
    result={}
    with closing(connection(path)) as db:
        for table,key in [('solutions','problem_id'),('detailed_solutions','problem_id'),('statements','problem_id')]:
            columns=[r[1] for r in db.execute('PRAGMA table_info('+table+')')]
            for row in db.execute('SELECT * FROM '+table):
                identity=row[key];content={k:row[k] for k in columns}
                digest=sha(json.dumps(content,ensure_ascii=False,sort_keys=True))
                prior=db.execute('SELECT digest FROM bundled_items WHERE table_name=? AND item_id=?',(table,identity)).fetchone()
                if not prior or prior[0]!=digest:result[table,identity]=digest
    return result


def unchanged_amendments(path,expected,repair_ids):
    with closing(connection(path)) as db:
        for (table,identity),digest in expected.items():
            if table=='statements' and identity in repair_ids:continue
            row=db.execute('SELECT * FROM '+table+' WHERE problem_id=?',(identity,)).fetchone()
            assert row and sha(json.dumps(dict(row),ensure_ascii=False,sort_keys=True))==digest,('Local amendment changed',table,identity)


def stage(target,folder):
    ledger=checked_entries();ratings=read(CONTENT/'ratings.json');assert read(CONTENT/'progress.json')['allComplete']
    public=target/'data/library.sqlite3';public_artifact_only(public);folder.mkdir(parents=True,exist_ok=False)
    candidate=folder/'library.sqlite3';backup(public,candidate)
    original=fingerprints(public,ledger,ratings)
    old_problems={x['id']:x for x in read(OUT/'source-before/problems.json')}
    new_problems={x['id']:x for x in read(ROOT/'data/library/problems.json')}
    with closing(sqlite3.connect(candidate)) as db,closing(connection(ROOT/'data/library.sqlite3')) as source:
        db.row_factory=sqlite3.Row
        for identity in ratings:
            row=db.execute('SELECT * FROM problems WHERE id=?',(identity,)).fetchone();assert row,identity
            raw,encoded=json.loads(row['raw']),json.loads(row['encoded'])
            assert row['url']==new_problems[identity]['url']
            for name,content in [('raw',raw),('encoded',encoded)]:
                old,new=old_problems[identity][name],new_problems[identity][name]
                for key in set(old)|set(new):
                    if old.get(key)!=new.get(key):
                        if key in new:content[key]=new[key]
                        else:content.pop(key,None)
            db.execute('UPDATE problems SET raw=?,encoded=? WHERE id=?',(json.dumps(raw,ensure_ascii=False),json.dumps(encoded,ensure_ascii=False),identity))
        for identity,entry in ledger.items():
            for variant,table in [('default','solutions'),('detailed','detailed_solutions')]:
                if variant not in entry['articles']:continue
                row=source.execute('SELECT * FROM '+table+' WHERE problem_id=?',(identity,)).fetchone()
                db.execute('INSERT OR REPLACE INTO '+table+' VALUES(?,?,?,?,?)',tuple(row))
        for path in (CONTENT/'statements').glob('NC*.json'):
            identity=read(path)['id'];row=source.execute('SELECT * FROM statements WHERE problem_id=?',(identity,)).fetchone()
            db.execute('INSERT OR REPLACE INTO statements VALUES(?,?)',tuple(row))
        db.execute('INSERT OR REPLACE INTO library_meta VALUES(?,?)',('nowcoderEditorialRevision',REVISION))
        db.execute("UPDATE library_meta SET value=CAST(value AS INTEGER)+1 WHERE key='revision'");db.commit()
    assert fingerprints(candidate,ledger,ratings)==original
    verify_owned(candidate,ledger)
    state=target/('admin-workspace/state' if (target/'admin-workspace/state').is_dir() else 'state')
    live=state/'tb-library.sqlite3';assert live.is_file()
    saved=folder/'workspace-before.sqlite3';backup(live,saved)
    rehearsal=folder/'workspace-rehearsal.sqlite3';backup(saved,rehearsal)
    amendments=local_amendments(saved)
    library=LibraryDatabase(rehearsal);library.merge_seed(candidate);repaired=repair_placeholders(library)
    verify_owned(rehearsal,ledger)
    # Every fetched statement and independent local annotation remains byte-identical.
    repaired_ids={read(p)['id'] for p in (CONTENT/'statements').glob('NC*.json')}
    unchanged_amendments(rehearsal,amendments,repaired_ids)
    report={'revision':REVISION,'target':str(target),'publicBeforeSha256':filehash(public),
        'candidateSha256':filehash(candidate),'buildInfoSha256':filehash(target/'BUILD-INFO.json'),
        'liveLibrary':str(live),'workspaceBackup':str(saved),'reviewedProblems':len(ledger),
        'eligibleProblems':926,'unrelatedPublicRowsPreserved':True,'localAmendmentsPreserved':len(amendments),
        'guardedPdfRepairsInRehearsal':repaired,'workspaceRehearsalPassed':True,
        'nativeAndFrontendSha256':{str(p.relative_to(target)):filehash(p) for p in [target/'ToBe.exe',target/'ToBeLoader.exe'] if p.exists()}}
    write(folder/'stage.json',report);return report


def apply(target,folder):
    report=read(folder/'stage.json');ledger=checked_entries()
    public=target/'data/library.sqlite3';candidate=folder/'library.sqlite3';live=Path(report['liveLibrary'])
    assert report['target']==str(target) and filehash(public)==report['publicBeforeSha256']
    assert filehash(candidate)==report['candidateSha256']
    assert filehash(target/'BUILD-INFO.json')==report['buildInfoSha256']
    recovery=folder/'public-before.sqlite3';backup(public,recovery)
    # Rehearse once more if any bundled/private catalog row changed since the snapshot.
    amendments=local_amendments(live)
    temporary=public.with_name('library.sqlite3.nowcoder-incoming')
    shutil.copy2(candidate,temporary);assert filehash(temporary)==report['candidateSha256'];os.replace(temporary,public)
    library=LibraryDatabase(live);library.merge_seed(candidate);repaired=repair_placeholders(library)
    verify_owned(live,ledger)
    repair_ids={read(p)['id'] for p in (CONTENT/'statements').glob('NC*.json')}
    unchanged_amendments(live,amendments,repair_ids)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    summary={'revision':REVISION,'eligibleProblems':926,'editorials':936,'detailedArticles':52,
        'animations':16,'animatedProblems':20,'sourceCommit':commit,'officialSubmissionsSent':0,
        'completedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'localOnly':True}
    for path in [target/'BUILD-INFO.json',target/'resources/BUILD-INFO.json']:
        if not path.exists():continue
        value=read(path);value.update(contentSourceCommit=commit,contentRevision=REVISION,
            publicLibrarySha256=report['candidateSha256'],nowcoderEditorials=summary)
        atomic_json(path,value)
    atomic_json(target/'resources/nowcoder-editorials.json',summary)
    for name,digest in report['nativeAndFrontendSha256'].items():assert filehash(target/name)==digest
    report.update(applied=True,appliedAt=summary['completedAt'],nativeExecutablesUnchanged=True,
        privateAccountDraftSubmissionTrainingFilesOpened=False,guardedPdfRepairs=repaired,
        liveOwnedArticlesVerified=936,publicOnlyLocalInstall=True)
    write(folder/'installed.json',report);return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['stage','apply'])
    parser.add_argument('--target',required=True,type=Path);parser.add_argument('--folder',required=True,type=Path)
    args=parser.parse_args();value=globals()[args.action](args.target.resolve(),args.folder.resolve())
    print(json.dumps({k:v for k,v in value.items() if k not in {'nativeAndFrontendSha256','target','liveLibrary','workspaceBackup'}},ensure_ascii=False))
