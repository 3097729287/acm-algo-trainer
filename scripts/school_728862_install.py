"""Install the verified additive school-training content into local public seeds.

No executable or private database is replaced. Normal application startup
uses the existing three-way seed upgrade and preserves local imports/edits.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

from school_728862_stage import ROOT,PREFIX,additions,insert,snapshot

def hash_file(path):
    with Path(path).open('rb') as handle:return hashlib.file_digest(handle,'sha256').hexdigest()

def private_inventory(state):
    result={}
    for path in sorted(state.rglob('*.sqlite3')):
        relative=path.relative_to(state)
        if set(relative.parts).intersection({'backups','judge-work','http','tb-problem-assets'}):continue
        with sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True) as db:
            names={r[0] for r in db.execute("select name from sqlite_master where type='table'")}
            if 'problems' in names and 'solutions' in names:continue
            stable={}
            for table in sorted(names):
                if table.startswith('sqlite_'):continue
                cols=[r[1] for r in db.execute('pragma table_info("'+table.replace('"','""')+'")')]
                if table=='submissions' or table=='drafts' or table=='documents' or any('code' in column for column in cols):
                    rows=db.execute('select * from "'+table.replace('"','""')+'" order by rowid').fetchall()
                    stable[table]={'rows':len(rows),'sha256':hashlib.sha256(repr(rows).encode()).hexdigest()}
            result[str(relative)]={'path':str(path),'tables':stable}
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true');args=ap.parse_args()
    folder=ROOT/'.backups/school728862';packet=additions()
    assert json.loads((folder/'render/report.json').read_text())['passed']
    assert json.loads((folder/'upgrade-report.json').read_text())['passed']
    newest=ROOT.parents[1]/'版本'/'最新版'
    recovery=folder/('local-install-'+dt.datetime.now().strftime('%Y%m%d-%H%M%S'))
    recovery.mkdir(parents=True)
    baseline=folder/'baseline.sqlite3';baseline_hash=hash_file(baseline)
    result={'applied':args.apply,'recovery':str(recovery),'installations':[],'nativeFilesChanged':False,'cleanupPerformed':False}
    for name in ['程序','管理员程序']:
        installation=(newest/name).resolve();assert installation.is_relative_to(newest.resolve())
        seed=installation/'data/library.sqlite3'
        if not seed.exists():continue
        seed_hash=hash_file(seed)
        before=private_inventory(installation/'state')
        for i,item in enumerate(before.values()):
            snapshot(Path(item['path']),recovery/name/f'private-{i:02}.sqlite3')
        # Reuse the already validated online seed snapshot if bytes are equal;
        # otherwise snapshot the exact installed seed before any mutation.
        backup=baseline if seed_hash==baseline_hash else recovery/name/'public-seed-before.sqlite3'
        if backup!=baseline:snapshot(seed,backup)
        with sqlite3.connect(seed.as_uri()+'?mode=ro',uri=True) as db:
            counts_before={table:db.execute('select count(*) from '+table).fetchone()[0] for table in ['problems','solutions','detailed_solutions','statements']}
            existing=db.execute('select count(*) from problems where id like ?',(PREFIX+'%',)).fetchone()[0]
        assert existing in (0,12)
        if args.apply:
            lib=insert(seed,packet);counts_after=lib.check()
            assert all(counts_after[t]==counts_before[t]+(0 if existing else 12) for t in counts_before)
            assert private_inventory(installation/'state')==before,'Private data changed during public-seed installation'
        else:counts_after=counts_before
        item={'installation':str(installation),'version':(installation/'VERSION').read_text().strip(),
          'before':counts_before,'after':counts_after,'privateDatabasesBackedUp':len(before),'privateInventory':before,
          'publicSeedBackup':str(backup),'seedBeforeSha256':seed_hash,'seedAfterSha256':hash_file(seed)}
        result['installations'].append(item)
        if args.apply:
            note={'contest':'https://codeforces.com/gym/728862','problems':12,'articles':24,
              'appliedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'nativeVersion':item['version'],
              'kind':'local public educational content overlay','source':str(ROOT),'seedSha256':item['seedAfterSha256']}
            marker=installation/'data/Gym728862-CONTENT.json'
            if marker.exists():
                saved=recovery/name/'previous-content-marker.json';saved.parent.mkdir(parents=True,exist_ok=True);saved.write_bytes(marker.read_bytes())
            marker.write_text(json.dumps(note,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    (folder/'local-install.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    # Do not echo private inventory or machine/account identifiers to the log.
    print(json.dumps({'applied':args.apply,'installations':len(result['installations']),
       'backedUpPrivateDatabases':sum(i['privateDatabasesBackedUp'] for i in result['installations']),
       'tasksAddedPerSeed':12,'articlesAddedPerSeed':24,'personalDataUnchanged':True},ensure_ascii=False))

if __name__=='__main__':main()
