"""Install the reviewed educational overlay, preserving private SQLite state."""
import argparse
import datetime as dt
from pathlib import Path
import sqlite3
import subprocess
from cf2278_stage import ROOT, CONTENT, OUT, additions, shared
from three_contests_install import NEWEST, file_hash, assert_closed, personal_paths, stable_inventory, public_digest

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');args=ap.parse_args()
    assert shared.load(OUT/'render/report.json')['passed']
    assert shared.load(OUT/'upgrade-report.json')['passed']
    assert shared.load(CONTENT/'validation.json')['passed']
    assert all(x['passed'] for x in shared.load(OUT/'format-report.json'))
    assert all(x['passed'] for x in shared.load(OUT/'mdfull-report.json'))
    assert_closed();packet=additions();identities={p['id'] for p in packet['problems']}
    recovery=Path.home()/'.dsh/backups/div3-1131-20261102'/dt.datetime.now().strftime('%Y%m%d-%H%M%S')
    recovery.mkdir(parents=True)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    report={'applied':args.apply,'sourceCommit':commit,'recovery':str(recovery),'installations':[],
        'publicProblems':6,'articles':12,'personalDatabaseReplacement':False,'publicDeployment':False}
    known_backups={}
    for name in ['程序','管理员程序']:
        installation=(NEWEST/name).resolve();assert installation.is_relative_to(NEWEST)
        seed=installation/'data/library.sqlite3';assert seed.is_file()
        native={f:file_hash(installation/f) for f in ['VERSION','BUILD-INFO.json','ToBe.exe','ToBeLoader.exe'] if (installation/f).exists()}
        seed_hash=file_hash(seed);backup=known_backups.get(seed_hash)
        if backup is None:
            backup=recovery/name/'public-seed-before.sqlite3';shared.snapshot(seed,backup);known_backups[seed_hash]=backup
        paths=personal_paths(installation);private=stable_inventory(paths)
        snapshots=[]
        for index,path in enumerate(paths):
            saved=recovery/name/f'personal-{index:02}.sqlite3';shared.snapshot(path,saved)
            snapshots.append({'source':str(path),'backup':str(saved),'backupSha256':file_hash(saved)})
        unrelated=public_digest(seed,identities)
        with sqlite3.connect(seed.as_uri()+'?mode=ro',uri=True) as db:
            previous={t:db.execute('select count(*) from '+t).fetchone()[0] for t in ['problems','solutions','detailed_solutions','statements']}
            present=db.execute('select count(*) from problems where id in ('+','.join('?' for _ in identities)+')',tuple(identities)).fetchone()[0]
        assert present in (0,6)
        print('Verified recovery and public/private baseline:',name,flush=True)
        assert_closed()
        assert file_hash(seed)==seed_hash,'Another task changed this public seed during validation'
        if args.apply:
            lib=shared.insert(seed,packet,meta_key='cf2278Content');after=lib.check()
            assert all(after[t]==previous[t]+(6 if present==0 else 0) for t in previous)
            assert public_digest(seed,identities)==unrelated,'An unrelated public row changed'
            assert stable_inventory(paths)==private,'Private records changed during public installation'
            assert {f:file_hash(installation/f) for f in native}==native
            marker=installation/'data/CF2278-CONTENT.json'
            if marker.exists():
                saved=recovery/name/'previous-marker.json';saved.parent.mkdir(parents=True,exist_ok=True)
                saved.write_bytes(marker.read_bytes())
            shared.dump(marker,{'kind':'local public educational content overlay','sourceCommit':commit,
                'sourceBranch':'content/div3-1131-20261102','contest':'Div.3 1131','contestId':2278,
                'problems':6,'articles':12,'nativeVersion':(installation/'VERSION').read_text().strip(),
                'seedSha256':file_hash(seed),'installedAt':dt.datetime.now(dt.timezone.utc).isoformat()})
        else:after=previous
        report['installations'].append({'installation':str(installation),'version':(installation/'VERSION').read_text().strip(),
            'before':previous,'after':after,'personalDatabasesBackedUp':len(paths),'privateInventory':private,
            'snapshots':snapshots,'publicSeedBackup':str(backup),'seedBeforeSha256':seed_hash,
            'seedAfterSha256':file_hash(seed),'unrelatedPublicRowsUnchanged':True,'nativeHashesUnchanged':True})
        print('Public overlay installed and private inventory unchanged:',name,flush=True)
    shared.dump(OUT/'local-install.json',report)
    print({'applied':args.apply,'installations':len(report['installations']),
        'personalDatabaseBackups':sum(x['personalDatabasesBackedUp'] for x in report['installations'])})

if __name__=='__main__':main()
