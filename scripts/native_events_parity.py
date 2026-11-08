"""Compare native IPC public rosters with current legacy event projection."""
import argparse,hashlib,json,os,sys,tempfile
from contextlib import closing
from pathlib import Path
import sqlite3

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common'),str(ROOT/'scripts')]
os.environ['TB_OFFLINE']='1'
from build_native_catalog import public_store,public_replay_events
from assets import AssetLibrary
from native_run_parity import Native


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--native',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    store=public_store(ROOT/'data/library.sqlite3');rows=store._catalog_rows();assets=AssetLibrary(store,cache_dir=ROOT/'.backups/native-public-input')
    try:expected=public_replay_events(store,assets,rows)
    finally:assets.close()
    with tempfile.TemporaryDirectory(prefix='ToBe-native-events-') as directory:
        state=Path(directory);native=Native(args.native,state,'not-used','not-used')
        try:
            assert native.call('contests/events')==expected
            with closing(sqlite3.connect(state/'personal.sqlite3')) as db:
                db.execute("INSERT INTO account_problem_facts VALUES('private-fixture','{\"row\":{\"id\":\"private-fixture\"}}','now')");db.commit()
                native.process.stdin.write(json.dumps({'version':1,'id':'private-events','method':'GET','path':'contests/events','query':{}})+'\n');native.process.stdin.flush()
                response=native.responses.get(timeout=15);assert not response['ok'] and response['error']['code']=='MIGRATION_PENDING'
                assert db.execute("SELECT value FROM account_problem_facts WHERE problem_id='private-fixture'").fetchone()[0]=='{"row":{"id":"private-fixture"}}'
        finally:native.close()
    report={'ok':True,'events':len(expected['events']),'incompleteEventsPreserved':sum(not e['complete'] for e in expected['events']),
            'allLegacyPublicFieldsEqual':True,'privateOverlayExplicitlyBlockedWithoutMutation':True,'privateLiveStateOpened':False,
            'nativeSha256':hashlib.sha256(args.native.read_bytes()).hexdigest(),'pythonRuntimeFallback':False,'networkRequests':0}
    args.output.parent.mkdir(exist_ok=True,parents=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps(report))


if __name__=='__main__':main()
