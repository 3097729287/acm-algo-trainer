"""Compare the actual native export RPC with the legacy portable journal export."""
from contextlib import closing
from datetime import datetime,timezone
import argparse,hashlib,json,os,sqlite3,sys,tempfile,threading,tomllib
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common'),str(ROOT/'scripts')]
os.environ['TB_OFFLINE']='1'
from data_export import export_data
from account_sync import TABLES
from native_run_parity import Native

NOW=datetime(2026,11,9,9,tzinfo=timezone.utc)


def normalized(value):
    value=json.loads(json.dumps(value,ensure_ascii=False))
    for row in value['tables']['account_preferences']:
        if row['key'] in ('ui','receipt-bindings'):row['value']=json.loads(row['value'])
    value.pop('appVersion');value['exportedAt']=datetime.fromisoformat(value['exportedAt'].replace('Z','+00:00')).isoformat()
    return value


def fingerprint(db):
    digest=hashlib.sha256()
    for name,sql in db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"):
        digest.update(repr((name,sql)).encode('utf8'))
        for row in db.execute('SELECT * FROM "'+name.replace('"','""')+'" ORDER BY rowid'):
            digest.update(repr(tuple(row)).encode('utf8'))
    return digest.hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--native',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();checks=[]
    version=tomllib.loads((ROOT/'Cargo.toml').read_text('utf8'))['workspace']['package']['version']
    with tempfile.TemporaryDirectory(prefix='ToBe-native-export-') as temporary:
        state=Path(temporary);native=Native(args.native,state,'not-used','not-used',test_clock=NOW.isoformat())
        try:
            with closing(sqlite3.connect(state/'personal.sqlite3')) as db:
                db.row_factory=sqlite3.Row
                for pid,context,code in [('z','','中文\n\0'),('a','review:first','print(42)')]:db.execute('INSERT INTO drafts VALUES(?,?,?,?)',(pid,context,code,'2026-11-09T08:00:00Z'))
                db.execute("INSERT INTO training(id,active_at) VALUES('z','2026-11-09T08:00:00Z')")
                db.execute("INSERT INTO practice_sets VALUES('p','fixture list','[\"z\"]','now')")
                db.execute("INSERT INTO contests(id,name,status,started_at,deadline,duration,slots) VALUES('c','fixture contest','finished','now','now',30,'[]')")
                db.execute("INSERT INTO submissions(id,problem_id,mode,code,submitted_at,finished_at,verdict,scope) VALUES('s','z','run','print(42)','now','now','SAMPLE_PASS','samples')")
                db.execute("INSERT INTO tb_rank_profile VALUES(1,'now')")
                db.execute("INSERT INTO official_first_xp_awards VALUES('fixture-key','now',0)")
                db.execute("INSERT INTO official_xp_state VALUES(1,'now')")
                db.execute("INSERT INTO daily_missions(day,id,definition) VALUES('2026-11-09','m','{}')")
                db.execute("INSERT INTO goals VALUES('g','now','{}',0)")
                db.execute("INSERT INTO goal_daily_assignments VALUES('g','2026-11-09','[\"z\"]',1)")
                db.execute("INSERT INTO ranking_receipts VALUES('https://fixture.invalid','r','now')")
                db.execute("INSERT INTO ranking_reward_totals VALUES('https://fixture.invalid','fixture',0,'[]','now')")
                db.execute("INSERT INTO achievement_xp_claims VALUES('fixture','now',0,'now')")
                db.execute("INSERT INTO account_problem_facts VALUES('custom','{}','now')")
                db.execute("CREATE TABLE account_sync_conflicts(id TEXT PRIMARY KEY,data TEXT NOT NULL)")
                db.execute("INSERT INTO account_sync_conflicts VALUES('losing-draft','{\"code\":\"retained\"}')")
                db.execute("INSERT INTO ranking_profile(singleton,user_id,nickname,auth_token,created_at) VALUES(1,'fixture','测试昵称','PRIVATE-CREDENTIAL-MARKER','now')")
                db.execute("CREATE TABLE future_device_cache(secret TEXT)");db.execute("INSERT INTO future_device_cache VALUES('PRIVATE-DEVICE-MARKER')")
                prefs={'ui':json.dumps({'nested':{'apiKey':'PRIVATE-KEY-MARKER','path':'C:/Local/a','good':'保留'},'items':['\\\\server\\private','https://example.org/a'],'E:/private':'hidden'},ensure_ascii=False),
                       'receipt-bindings':json.dumps({'cookie':'PRIVATE-COOKIE-MARKER','binding':{'url':'https://example.org/task','token':'PRIVATE-TOKEN-MARKER'}}),
                       'draft-language:'+'a'*64:'python3','submission-language:abc-123':'cpp17','submission-language:bad_key':'cpp17','translation-settings':'PRIVATE-SETTINGS-MARKER'}
                db.executemany('INSERT INTO account_preferences VALUES(?,?,?)',[(key,value,'now') for key,value in prefs.items()]);db.commit()
                reference=SimpleNamespace(connection=db,lock=threading.RLock(),_now=lambda:NOW,store=SimpleNamespace(extensions=None))
                before=fingerprint(db);legacy=export_data(reference);actual=native.call('data/export')
                assert actual['appVersion']==version
                assert normalized(actual)==normalized(legacy)
                assert set(actual['tables'])==set(TABLES) and all(actual['tables'][table] for table in TABLES)
                assert 'PRIVATE-' not in json.dumps(actual,ensure_ascii=False)
                assert before==fingerprint(db)
                checks+=['all-17-current-table-contracts','compound-key-order','unicode-and-nul-code','nested-preference-portability','language-key-allowlist','credentials-and-device-state-excluded','read-only-entire-journal']
                def raw(owner=None):
                    request={'version':1,'id':'export-boundary','method':'GET','path':'data/export','query':{}}
                    if owner is not None:request['owner']=owner
                    native.process.stdin.write(json.dumps(request)+'\n');native.process.stdin.flush()
                    return native.responses.get(timeout=15)
                mismatch=raw('different-owner');assert not mismatch['ok'] and mismatch['error']['code']=='ACCOUNT_CHANGED'
                assert before==fingerprint(db);checks.append('owner-switch-refused-with-original-preserved')
                native.close();native=Native(args.native,state,'not-used','not-used',test_clock=NOW.isoformat())
                assert normalized(native.call('data/export'))==normalized(legacy);checks.append('restart-restores-identical-export')
                db.execute("UPDATE account_preferences SET value='{broken' WHERE key='ui'");db.commit();before=fingerprint(db)
                try:export_data(reference)
                except json.JSONDecodeError:pass
                else:raise AssertionError('Legacy accepted malformed stored JSON')
                failed=raw();assert not failed['ok'] and failed.get('data') is None
                assert before==fingerprint(db);checks.append('malformed-json-refused-with-original-preserved')
        finally:native.close()
    report={'ok':True,'checks':checks,'legacyTables':len(TABLES),'nativeSha256':hashlib.sha256(args.native.read_bytes()).hexdigest(),
            'nativeVersion':version,'publicAccountAdaptersMigrated':False,'usesIsolatedGeneratedJournal':True,'privateLiveStateOpened':False,'officialSubmissionsSent':0,'pythonRuntimeFallback':False}
    args.output.parent.mkdir(exist_ok=True,parents=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps(report))


if __name__=='__main__':main()
