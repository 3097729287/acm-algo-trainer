"""Install only the validated public educational overlay, after normal app exit."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
from three_contests_stage import ROOT,CONTENT,OUT,additions,insert,load,dump,snapshot

NEWEST=Path('D:/项目/TB/版本/最新版').resolve()

def file_hash(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def assert_closed():
    command="$OutputEncoding=[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new(); Get-CimInstance Win32_Process -Filter \"Name='ToBe.exe'\" | Select-Object ExecutablePath,ProcessId | ConvertTo-Json -Compress"
    run=subprocess.run(['powershell.exe','-NoProfile','-Command',command],capture_output=True,encoding='utf8',timeout=30,check=True)
    rows=json.loads(run.stdout) if run.stdout.strip() else []
    if isinstance(rows,dict):rows=[rows]
    running=[r['ProcessId'] for r in rows if r.get('ExecutablePath') and Path(r['ExecutablePath']).resolve().is_relative_to(NEWEST)]
    assert not running,'Save and close the normal ToBe windows first; do not force terminate them.'

def personal_paths(installation):
    result=[]
    for state in [installation/'state',installation/'admin-workspace/state']:
        if not state.exists():continue
        for path in sorted(state.rglob('*.sqlite3')):
            if set(path.relative_to(state).parts).intersection({'backups','judge-work','http','tb-problem-assets'}):continue
            result.append(path)
    return result

def stable_inventory(paths):
    result={}
    for path in paths:
        tables={}
        with sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True) as db:
            for (name,) in db.execute("select name from sqlite_master where type='table' order by name"):
                if name.startswith('sqlite_'):continue
                columns=[r[1] for r in db.execute('pragma table_info("'+name.replace('"','""')+'")')]
                if name not in {'submissions','drafts','documents'} and not any('code' in c for c in columns):continue
                h=hashlib.sha256();count=0
                for row in db.execute('select * from "'+name.replace('"','""')+'" order by rowid'):
                    h.update(repr(tuple(row)).encode());h.update(b'\n');count+=1
                tables[name]={'rows':count,'sha256':h.hexdigest()}
        result[str(path)]={'tables':tables}
    return result

def public_digest(path,identities):
    result={};params=tuple(sorted(identities));marks=','.join('?' for _ in params)
    spec={'problems':'id','problem_urls':'problem_id','solutions':'problem_id','detailed_solutions':'problem_id',
          'statements':'problem_id','solution_methods':'problem_id','problem_lectures':'problem_id','lectures':None,'training_lists':None,'statement_assets':None}
    with sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True) as db:
        for table,key in spec.items():
            h=hashlib.sha256();count=0
            query='select * from '+table+((' where '+key+' not in ('+marks+')') if key else '')+' order by 1,2'
            for row in db.execute(query,params if key else ()):
                h.update(repr(tuple(row)).encode());h.update(b'\n');count+=1
            result[table]={'rows':count,'sha256':h.hexdigest()}
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');args=ap.parse_args()
    assert load(OUT/'render/report.json')['passed']
    assert load(OUT/'upgrade-report.json')['passed']
    assert load(CONTENT/'validation.json')['passed']
    assert all(v['passed'] for v in load(OUT/'format-report.json'))
    assert all(v['passed'] for v in load(OUT/'mdfull-report.json'))
    assert_closed();packet=additions();identities={r['id'] for r in packet['problems']}
    recovery=OUT/('local-install-'+dt.datetime.now().strftime('%Y%m%d-%H%M%S'));recovery.mkdir(parents=True)
    baseline=OUT/'baseline.sqlite3';known_backups={file_hash(baseline):baseline} if baseline.exists() else {}
    source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    report={'applied':args.apply,'sourceCommit':source_commit,'recovery':str(recovery),'installations':[],
      'publicProblems':16,'articles':32,'personalDatabaseReplacement':False,'publicDeployment':False,'cleanupPerformed':False}
    for name in ['程序','管理员程序']:
        installation=(NEWEST/name).resolve();assert installation.is_relative_to(NEWEST)
        seed=installation/'data/library.sqlite3';assert seed.is_file()
        native={f:file_hash(installation/f) for f in ['VERSION','BUILD-INFO.json','ToBe.exe','ToBeLoader.exe'] if (installation/f).exists()}
        before_hash=file_hash(seed);backup=known_backups.get(before_hash)
        if backup is None:
            backup=recovery/name/'public-seed-before.sqlite3';snapshot(seed,backup);known_backups[before_hash]=backup
        paths=personal_paths(installation);before_private=stable_inventory(paths)
        for index,path in enumerate(paths):snapshot(path,recovery/name/f'personal-{index:02}.sqlite3')
        before_public=public_digest(seed,identities)
        with sqlite3.connect(seed.as_uri()+'?mode=ro',uri=True) as db:
            previous={table:db.execute('select count(*) from '+table).fetchone()[0] for table in ['problems','solutions','detailed_solutions','statements']}
            present=db.execute('select count(*) from problems where id in ('+','.join('?' for _ in identities)+')',tuple(identities)).fetchone()[0]
        assert present in (0,16)
        if args.apply:
            lib=insert(seed,packet);after=lib.check()
            assert all(after[t]==previous[t]+(16 if present==0 else 0) for t in previous)
            assert public_digest(seed,identities)==before_public,'An unrelated public row changed'
            assert stable_inventory(paths)==before_private,'Personal data changed during the public overlay'
            assert {f:file_hash(installation/f) for f in native}==native
            marker=installation/'data/THREE-CONTESTS-20261102.json'
            if marker.exists():
                saved=recovery/name/'previous-marker.json';saved.parent.mkdir(parents=True,exist_ok=True);saved.write_bytes(marker.read_bytes())
            dump(marker,{'kind':'local public educational content overlay','sourceCommit':source_commit,'sourceBranch':'content/three-contests-20261102',
                'contests':['周赛 168','ABC 482','小白月赛 139'],'problems':16,'articles':32,'nativeVersion':(installation/'VERSION').read_text().strip(),
                'seedSha256':file_hash(seed),'installedAt':dt.datetime.now(dt.timezone.utc).isoformat()})
        else:after=previous
        report['installations'].append({'installation':str(installation),'version':(installation/'VERSION').read_text().strip(),
            'before':previous,'after':after,'personalDatabasesBackedUp':len(paths),'privateInventory':before_private,
            'publicSeedBackup':str(backup),'seedBeforeSha256':before_hash,'seedAfterSha256':file_hash(seed),
            'unrelatedPublicRowsUnchanged':True,'nativeHashesUnchanged':True})
    dump(OUT/'local-install.json',report)
    print(json.dumps({'applied':args.apply,'installations':len(report['installations']),
      'backedUpPersonalDatabases':sum(i['personalDatabasesBackedUp'] for i in report['installations']),
      'newProblemsPerInstallation':16,'newArticlesPerInstallation':32,'personalDataUnchanged':True},ensure_ascii=False))

if __name__=='__main__':main()
