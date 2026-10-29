"""Stage/apply a content-only local upgrade on top of the installed public seed.

The executable, frontend and personal databases are never replaced. Public
statements, original identities and unrelated editorials come from the installed
seed, so a concurrent language/content patch cannot be rolled back. Staging is
read-only for the installation; --apply requires a matching staged fingerprint.
All recovery data and validation reports remain under the ignored task folder.
"""
import argparse
from contextlib import closing
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime,timezone

from core7_authoring import ROOT,OUT,source_hash
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from library import LibraryDatabase

PRIVATE={'accounts','submissions','drafts','training','documents','account_preferences'}

def read(path):return json.loads(path.read_text('utf-8-sig'))
def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def atomic_bytes(path,value):
    temporary=path.with_name(path.name+'.core7-staged')
    with temporary.open('wb') as stream:
        stream.write(value);stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,path)
def filehash(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def quote(name):return '"'+name.replace('"','""')+'"'
def jsonrow(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,default=lambda x:{'bytes':x.hex()},separators=(',',':'))
def tables(db):return {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'") if not r[0].startswith('sqlite_')}

def fingerprints(path,selected=None):
    with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
        result={}
        for table in sorted(tables(db)):
            if selected is not None and table not in selected:continue
            count=len(db.execute('PRAGMA table_info('+quote(table)+')').fetchall())
            digest=hashlib.sha256();rows=0
            for row in db.execute('SELECT * FROM '+quote(table)+' ORDER BY '+','.join(str(i+1) for i in range(count))):
                digest.update(jsonrow(row).encode());digest.update(b'\n');rows+=1
            result[table]={'rows':rows,'sha256':digest.hexdigest()}
        return result

def backup(source,destination):
    destination.parent.mkdir(parents=True,exist_ok=True)
    assert not destination.exists(),destination
    with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as src,closing(sqlite3.connect(destination)) as dest:
        src.backup(dest)
        assert dest.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    return destination

def authored():
    entries=read(OUT/'authored.json');proof={(r['pid'],r['method']):r for r in read(OUT/'verification.json')}
    for entry in entries:
        check=proof[entry['pid'],entry['method']]
        assert check['passed'] and check['programSha256']==entry['programSha256']
    return entries

def stage(target):
    target=target.resolve();public=target/'data/library.sqlite3';assert public.is_file()
    build=target/'BUILD-INFO.json';assert build.is_file()
    folder=OUT/'delivery'/target.name;folder.mkdir(parents=True,exist_ok=True)
    staged=folder/'library.sqlite3'
    if staged.exists():
        # Staging output is disposable, never a personal database.
        assert staged.resolve().is_relative_to((OUT/'delivery').resolve())
        staged.unlink()
    backup(public,staged)
    entries=authored();identities={x['problemId'] for x in entries}
    needed={'lecture:foundation-'+name for x in entries for name in x['lessons']}
    source=ROOT/'data/library'
    original=fingerprints(public,{'problems','problem_urls','statements','training_lists'})
    before=LibraryDatabase(public,readonly=True).check()
    with closing(sqlite3.connect(staged)) as db:
        assert not tables(db)&PRIVATE,'Personal table in bundled content'
        assert 'solution_methods' in tables(db),'Installed reader does not support methods'
        db.execute('PRAGMA foreign_keys=ON')
        for table in ['solutions','detailed_solutions']:
            for row in read(source/(table+'.json')):
                if row['problem_id'] not in identities:continue
                previous=db.execute('SELECT images FROM '+table+' WHERE problem_id=?',(row['problem_id'],)).fetchone()
                if previous:
                    for key,value in json.loads(previous[0]).items():assert row['images'].get(key)==value
                db.execute('INSERT INTO '+table+' VALUES (?,?,?,?,?) ON CONFLICT(problem_id) DO UPDATE SET markdown=excluded.markdown,source_path=excluded.source_path,images=excluded.images,digest=excluded.digest',
                    (row['problem_id'],row['markdown'],row['source_path'],json.dumps(row['images'],ensure_ascii=False),source_hash(row['markdown'])))
        for row in read(source/'solution_methods.json'):
            if row['problem_id'] not in identities:continue
            previous=db.execute('SELECT content FROM solution_methods WHERE problem_id=?',(row['problem_id'],)).fetchone()
            content=deepcopy(row['content'])
            if previous:
                old=json.loads(previous[0]);keys={m['id'] for m in content['methods']}
                content['methods'] += [m for m in old.get('methods',[]) if m['id'] not in keys]
            db.execute('INSERT INTO solution_methods VALUES (?,?) ON CONFLICT(problem_id) DO UPDATE SET content=excluded.content',
                (row['problem_id'],json.dumps(content,ensure_ascii=False)))
        for row in read(source/'lectures.json'):
            if row['id'] not in needed:continue
            previous=db.execute('SELECT content FROM lectures WHERE id=?',(row['id'],)).fetchone();content=deepcopy(row['content'])
            if previous:
                saved=json.loads(previous[0]);saved['sourceProblemIds']=sorted(set(saved.get('sourceProblemIds',[]))|set(content.get('sourceProblemIds',[])))
                if saved.get('editorialVersion')!='2026-10-30-core7':content=saved
            db.execute('INSERT INTO lectures VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET content=excluded.content,digest=excluded.digest',
                (row['id'],json.dumps(content,ensure_ascii=False),source_hash(content['markdown'])))
        for row in read(source/'links.json'):
            if row['problem_id'] not in identities or row['lecture_id'] not in needed:continue
            present=db.execute('SELECT 1 FROM problem_lectures WHERE problem_id=? AND lecture_id=?',(row['problem_id'],row['lecture_id'])).fetchone()
            if not present:
                position=db.execute('SELECT COALESCE(MAX(position),-1)+1 FROM problem_lectures WHERE problem_id=?',(row['problem_id'],)).fetchone()[0]
                db.execute('INSERT INTO problem_lectures VALUES (?,?,?,?)',(row['problem_id'],row['lecture_id'],row['kind'],position))
        revision=db.execute("SELECT value FROM library_meta WHERE key='revision'").fetchone()
        db.execute("UPDATE library_meta SET value=? WHERE key='revision'",(str(int(revision[0])+1),))
        db.execute("INSERT OR REPLACE INTO library_meta VALUES ('core7EditorialRevision','2026-10-30-method-variants-v1')")
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
        db.commit()
    assert fingerprints(staged,set(original))==original,'Identity, statement or list regression'
    counts=LibraryDatabase(staged,readonly=True).check()
    # Exact preservation of every non-target editorial, including old images.
    with closing(sqlite3.connect(public.as_uri()+'?mode=ro',uri=True)) as old,closing(sqlite3.connect(staged.as_uri()+'?mode=ro',uri=True)) as new:
        for table in ['solutions','detailed_solutions','solution_methods']:
            for row in old.execute('SELECT * FROM '+table):
                if row[0] not in identities:assert new.execute('SELECT * FROM '+table+' WHERE problem_id=?',(row[0],)).fetchone()==row
    fresh=folder/'fresh-install.sqlite3'
    if fresh.exists():fresh.unlink()
    LibraryDatabase(fresh).merge_seed(staged)
    assert LibraryDatabase(fresh,readonly=True).check()==counts
    # Upgrade from the precise installed public baseline with an independent
    # local amendment/import. Actual personal state is tested separately below.
    upgrade=folder/'upgrade-fixture.sqlite3'
    if upgrade.exists():upgrade.unlink()
    check=LibraryDatabase(upgrade);check.merge_seed(public)
    with check.connection() as db:
        db.execute("UPDATE solutions SET markdown='local amendment',digest=? WHERE problem_id='luogu-training-P5707'",(source_hash('local amendment'),))
        db.execute('CREATE TABLE local_code_fixture(id TEXT PRIMARY KEY,code TEXT)')
        db.execute('INSERT INTO local_code_fixture VALUES (?,?)',('private-import','int main(){return 7;}'))
    check.merge_seed(staged)
    assert check.solution('luogu-training-P5707')['markdown']=='local amendment'
    with check.connection() as db:assert db.execute('SELECT code FROM local_code_fixture').fetchone()[0]=='int main(){return 7;}'
    progress=read(ROOT/'data/core7-editorials/progress.json')
    report={'target':str(target),'publicSeedBeforeSha256':filehash(public),'buildInfoBeforeSha256':filehash(build),
        'stagedSha256':filehash(staged),'countsBefore':before,'countsAfter':counts,'problems':len(identities),'methods':len(entries),
        'articles':2*len(entries),'scopeTotal':progress['totalProblems'],'complete':progress['complete'],
        'missingDualEditorials':progress['missingVariants'],'pendingStandardReview':progress['pendingStandardReview'],
        'unrelatedContentPreserved':True,'statementAndIdentityPreserved':True,'freshInstallPassed':True,'upgradeFixturePassed':True}
    dump(folder/'stage-report.json',report)
    return report

def apply(target):
    target=target.resolve();folder=OUT/'delivery'/target.name;report=read(folder/'stage-report.json')
    public=target/'data/library.sqlite3';build=target/'BUILD-INFO.json';staged=folder/'library.sqlite3'
    assert str(target)==report['target']
    assert filehash(public)==report['publicSeedBeforeSha256'],'Installed seed changed: restage'
    assert filehash(build)==report['buildInfoBeforeSha256'],'Installed patch changed: restage'
    assert filehash(staged)==report['stagedSha256']
    rendered=read(OUT/'render/report.json')
    assert not rendered['errors']
    for entry in authored():
        for variant,value in entry['variants'].items():
            digest=source_hash(value['markdown'])
            frames=[f for f in rendered['frames'] if f['pid']==entry['pid'] and f['method']==entry['method'] and f['variant']==variant and f['markdownSha256']==digest and f.get('imagesSha256')]
            assert {f['width'] for f in frames}=={390,1050,1440},(entry['pid'],entry['method'],variant)
    assert all(not r['failed'] for r in read(OUT/'format-all.json'))
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT).strip(),'Commit the source before delivery'
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    source_branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
    recovery=folder/'recovery';recovery.mkdir(exist_ok=False)
    backup(public,recovery/'public-library.sqlite3')
    private=[]
    for state in [target/'state',target/'admin-workspace/state']:
        if not state.exists():continue
        for path in sorted(state.rglob('*.sqlite3')):
            if 'backups' in path.relative_to(state).parts:continue
            assert path.resolve().is_relative_to(state.resolve())
            saved=backup(path,recovery/'personal'/path.relative_to(target))
            summary=fingerprints(saved)
            assert summary==fingerprints(path),'State changed during backup; close the app first'
            private.append({'path':path,'backup':saved,'fingerprints':summary})
            if path.name=='tb-library.sqlite3':
                rehearsal=folder/('upgrade-'+str(len(private))+'.sqlite3');backup(saved,rehearsal)
                with closing(sqlite3.connect(rehearsal)) as copydb:before_ids={r[0] for r in copydb.execute('SELECT id FROM problems')}
                LibraryDatabase(rehearsal).merge_seed(staged)
                with closing(sqlite3.connect(rehearsal)) as copydb:after_ids={r[0] for r in copydb.execute('SELECT id FROM problems')}
                assert before_ids<=after_ids,'Local imports lost'
    names=['BUILD-INFO.json','SOURCE-MANIFEST.json']
    for prefix in [Path(),Path('resources')]:
        for name in names:
            p=target/prefix/name
            if p.exists():
                dest=recovery/prefix/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    info=read(build)
    source_manifest={}
    paths=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode('utf-8').split('\0')
    for name in paths:
        if name and (ROOT/name).is_file():source_manifest[name]=filehash(ROOT/name)
    manifest_bytes=(json.dumps(source_manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
    info.update(localRevision='english-first-core7-20261030',commit=commit,sourceCommit=commit,sourceBranch=source_branch,
        contentSourceCommit=commit,sourcePushed=False,workingTreeDirty=False,sourceTag=None,
        status='local content-only editorial update; English-first frontend retained; unpublished',
        sourceManifestSha256=hashlib.sha256(manifest_bytes).hexdigest(),core7Editorials={k:report[k] for k in ['problems','methods','articles','scopeTotal','complete','missingDualEditorials','pendingStandardReview']})
    info['publicLibrary'].update(report['countsAfter'])
    # Preserve the exact EXE and frontend provenance of the preceding patch.
    assert info.get('buildSourceCommit') and info.get('frontendSourceCommit')
    payloads={}
    info_bytes=(json.dumps(info,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
    for prefix in [Path(),Path('resources')]:
        payloads[target/prefix/'SOURCE-MANIFEST.json']=manifest_bytes
        payloads[target/prefix/'BUILD-INFO.json']=info_bytes
    payloads[target/'resources/core7-editorials.json']=(json.dumps({'revision':'2026-10-30-method-variants-v1','sourceCommit':commit,**info['core7Editorials']},ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
    old_metadata={p:p.read_bytes() if p.exists() else None for p in payloads}
    try:
        temporary=public.with_name(public.name+'.core7-staged');shutil.copy2(staged,temporary)
        os.replace(temporary,public)
        for path,value in payloads.items():atomic_bytes(path,value)
    except Exception:
        temporary=public.with_name(public.name+'.core7-rollback');shutil.copy2(recovery/'public-library.sqlite3',temporary);os.replace(temporary,public)
        for path,value in old_metadata.items():
            if value is None:path.unlink(missing_ok=True)
            else:atomic_bytes(path,value)
        raise
    assert filehash(public)==report['stagedSha256']
    for item in private:assert fingerprints(item['path'])==item['fingerprints'],'Unexpected personal change during content-only install'
    report.update(applied=True,sourceCommit=commit,localOnly=True,exeAndFrontendUnchanged=True,
        onlinePersonalBackups=len(private),personalTablesPreserved=True,appliedAt=datetime.now(timezone.utc).isoformat())
    dump(folder/'install-report.json',report)
    # Do not distribute paths or private hashes in BUILD-INFO/resources.
    return {k:v for k,v in report.items() if k!='target'}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--target',type=Path,required=True);parser.add_argument('--apply',action='store_true')
    args=parser.parse_args();print(json.dumps(apply(args.target) if args.apply else stage(args.target),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
