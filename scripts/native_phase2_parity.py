"""Real Python/Rust domain comparisons on two independent disposable journals."""
from pathlib import Path
from contextlib import contextmanager
import datetime as dt
import difflib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import zlib
import argparse
import hashlib

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common'),str(ROOT/'scripts')]
os.environ['TB_OFFLINE']='1'
NOW=dt.datetime(2026,11,5,4,0,tzinfo=dt.timezone.utc)


def run(binary=None,report=None):
    from build_native_catalog import public_store
    from training import TrainingService
    from assets import AssetLibrary
    from learning_summary import LearningSummary,record_effective,public_quiz
    from lecture_library import LectureLibrary
    import usage,preferences
    from catalog_payload import project_row
    work=Path(tempfile.mkdtemp(prefix='native-phase2-',dir=ROOT/'.backups'))
    native_dir=work/'native';native_dir.mkdir()
    binary=(binary or ROOT/'target/debug/tobe-core.exe').resolve(strict=True)
    process=subprocess.Popen([str(binary),'sandbox',str(ROOT),str(native_dir)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf8',env={**os.environ,'TB_NATIVE_TEST_NOW':NOW.isoformat()},creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    counter=0
    def rpc(path,body=None,query=None,fail=False):
        nonlocal counter
        counter+=1
        value={'version':1,'id':str(counter),'method':'GET' if body is None else 'POST','path':path,'query':query or {}}
        if body is not None:value.update(body=body,token=token)
        process.stdin.write(json.dumps(value,ensure_ascii=False)+'\n');process.stdin.flush()
        line=process.stdout.readline()
        if not line:raise RuntimeError(process.stderr.read())
        value=json.loads(line)
        if not value['ok']:
            if fail:return value['error']
            raise AssertionError(f'{path}: {value["error"]}')
        if fail:raise AssertionError('Expected a rejected request')
        return value['data']
    token=rpc('account')['token']
    schema=(ROOT/'backend-rust/schema/personal.sql').read_text('utf8')
    legacy_db=sqlite3.connect(work/'legacy.sqlite3',isolation_level=None);legacy_db.row_factory=sqlite3.Row;legacy_db.executescript(schema)
    native_db=sqlite3.connect(native_dir/'personal.sqlite3',isolation_level=None)
    store=public_store(ROOT/'data/library.sqlite3');rows=store._catalog_rows();compact=[project_row(row) for row in rows]
    store.training_data=lambda:{'rows':compact};store.data=lambda:{'rows':rows};store.token=token
    legacy=TrainingService.__new__(TrainingService)
    legacy.connection=legacy_db;legacy.lock=threading.RLock();legacy.store=store;legacy.db_path=work/'legacy.sqlite3';legacy.clock=lambda:NOW;legacy.closed=False;legacy.admin_mode=False
    legacy._insights_signature=lambda _:None
    @contextmanager
    def write():
        legacy_db.execute('BEGIN IMMEDIATE')
        try:yield legacy_db;legacy_db.execute('COMMIT')
        except:legacy_db.execute('ROLLBACK');raise
    legacy._write=write
    assets=AssetLibrary(store,cache_dir=work/'assets');original_problem=assets.problem;assets.problem=lambda identity:original_problem(identity,fetch=False);legacy.assets=assets
    lectures=LectureLibrary(store)
    checks=[]
    def compare(name,native,old,strip_revision=False):
        expected=old();actual=native()
        if strip_revision:
            expected={k:v for k,v in expected.items() if k!='revision'};actual={k:v for k,v in actual.items() if k!='revision'}
        if expected!=actual:
            a=json.dumps(expected,ensure_ascii=False,indent=2,sort_keys=True).splitlines();b=json.dumps(actual,ensure_ascii=False,indent=2,sort_keys=True).splitlines()
            (work/(name+'-legacy.json')).write_text('\n'.join(a),'utf8');(work/(name+'-rust.json')).write_text('\n'.join(b),'utf8')
            print('\n'.join(list(difflib.unified_diff(a,b,fromfile='legacy',tofile='rust'))[:150]))
            raise AssertionError(f'{name} differs; preserved at {work}')
        checks.append(name);print('PASS',name)
    def seed(sql,params=()):
        legacy_db.execute(sql,params);native_db.execute(sql,params)
    try:
        import hashlib,status_report
        revision=hashlib.sha256(json.dumps(rows,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        compare('catalogue-compact',lambda:rpc('data',query={'compact':['1']}),lambda:{'rows':compact,'statuses':list(status_report.STATES),'categories':store.categories(),'revision':revision,'token':token,'today':dt.date.today().isoformat()})
        compare('catalogue-full',lambda:rpc('data'),lambda:{'rows':rows,'statuses':list(status_report.STATES),'categories':store.categories(),'revision':revision,'token':token,'today':dt.date.today().isoformat()})
        compare('workspace-empty',lambda:rpc('workspace'),legacy.workspace)
        compare('learning-empty',lambda:rpc('learning-summary'),lambda:LearningSummary(legacy).snapshot())
        compare('lectures-empty-queue',lambda:rpc('lectures'),lambda:__import__('lecture_queue').project(legacy,lectures.snapshot(),lectures))
        compare('public-training-lists',lambda:rpc('training-lists'),lambda:{'lists':store.public_training_lists()})
        compare('custom-training-lists-empty',lambda:rpc('training-lists',query={'custom':['1']}),lambda:{'lists':[]})
        with sqlite3.connect((ROOT/'data/native-catalog.sqlite3').resolve().as_uri()+'?mode=ro',uri=True) as compiled:
            hashes={row[0] for row in compiled.execute('SELECT sha256 FROM derived_assets')}
            sampled=0
            for pid,packed in compiled.execute('SELECT id,patch FROM problem_projections WHERE error IS NULL ORDER BY id'):
                patch=zlib.decompress(packed).decode()
                if not any(sha in patch for sha in hashes):continue
                compare('problem-public-inline-assets-'+str(sampled),lambda pid=pid:rpc('problem',query={'id':[pid]}),lambda pid=pid:legacy.problem(pid))
                sampled+=1
                if sampled==3:break
            assert sampled==3,'Public inline-resource cases must be exercised'
        identity=rows[0]['id']
        compare('training-start',lambda:rpc('training/start',{'id':identity}),lambda:legacy.start_training(identity))
        compare('training-deferred',lambda:rpc('training/start',{'id':identity,'deferWorkspace':True,'deferActivation':True}),lambda:legacy.start_training(identity,defer_workspace=True,activate=False))
        compare('draft-python',lambda:rpc('draft',{'id':identity,'code':'print("中文")','language':'python3'}),lambda:legacy.save_draft(identity,'print("中文")',language='python3'))
        compare('workspace-with-draft',lambda:rpc('workspace'),legacy.workspace)
        compare('problem-with-draft',lambda:rpc('problem',query={'id':[identity]}),lambda:legacy.problem(identity))
        compare('lectures-encountered',lambda:rpc('lectures'),lambda:__import__('lecture_queue').project(legacy,lectures.snapshot(),lectures))
        prefs={'theme':'light','fontSize':18,'onboardingGuideVersion':2,'seenAchievements':['first-ac'],'learningPaths':{'sectionWorkspaces':{'training':{'version':1,'groups':[]}}}}
        compare('preferences-save',lambda:rpc('preferences',{'preferences':prefs}),lambda:preferences.save_preferences(legacy,{'preferences':prefs}))
        compare('preferences-merge',lambda:rpc('preferences',{'preferences':{'theme':'dark','seenAchievements':['second-ac'],'onboardingGuideVersion':1}}),lambda:preferences.save_preferences(legacy,{'preferences':{'theme':'dark','seenAchievements':['second-ac'],'onboardingGuideVersion':1}}))
        compare('usage-empty',lambda:rpc('usage'),lambda:usage.snapshot(legacy))
        for sequence in [1,1,2]:
            body={'sessionId':'12345678-1234-1234-1234-123456789abc','sequence':sequence,'seconds':15,'learning':True}
            compare(f'usage-write-{len(checks)}',lambda body=body:rpc('usage',body),lambda body=body:usage.record(legacy,body))
        compare('usage-union',lambda:rpc('usage'),lambda:usage.snapshot(legacy))
        spans={'intervals':[[NOW.timestamp()-60,NOW.timestamp()-30],[NOW.timestamp()-45,NOW.timestamp()-15]]}
        compare('effective-learning-union',lambda:rpc('learning-summary/time',spans),lambda:record_effective(legacy,spans))
        compare('effective-learning-repeat',lambda:rpc('learning-summary/time',spans),lambda:record_effective(legacy,spans))
        empty_history={'id':'empty','at':NOW.isoformat(),'reason':'首次规划'}
        seed('INSERT INTO account_preferences VALUES(?,?,?)',('learning-summary-history:empty',json.dumps(empty_history),NOW.isoformat()))
        compare('learning-empty-history',lambda:rpc('learning-summary/history',query={'id':['empty']}),lambda:LearningSummary(legacy).history('empty'))
        compare('learning-with-history',lambda:rpc('learning-summary'),lambda:LearningSummary(legacy).snapshot())
        for topic in ['io-basics','binary-search','dinic']:compare('quiz-'+topic,lambda topic=topic:rpc('learning-summary/quiz',query={'id':[topic]}),lambda topic=topic:public_quiz(topic))
        current=rpc('learning-summary');body={'action':'view','revision':current['revision'],'view':{'mode':'float','pinned':True,'x':100,'y':200}}
        compare('learning-view-update',lambda:rpc('learning-summary/update',body),lambda:LearningSummary(legacy).update(body),True)
        # Generated revisions differ by design; align the CAS token in the two
        # disposable journals before the next real mutation comparison.
        native_state=json.loads(native_db.execute("SELECT value FROM account_preferences WHERE key='learning-summary-v1'").fetchone()[0]);old_state=json.loads(legacy_db.execute("SELECT value FROM account_preferences WHERE key='learning-summary-v1'").fetchone()[0]);old_state['revision']=native_state['revision'];legacy_db.execute("UPDATE account_preferences SET value=? WHERE key='learning-summary-v1'",(json.dumps(old_state),))
        body={'action':'delete-history','revision':native_state['revision'],'id':'empty'}
        compare('learning-history-tombstone',lambda:rpc('learning-summary/update',body),lambda:LearningSummary(legacy).update(body),True)
        compare('training-remove-keeps-draft',lambda:rpc('training/remove',{'id':identity}),lambda:legacy.remove_training(identity))
        compare('training-restart',lambda:rpc('training/start',{'id':identity}),lambda:legacy.start_training(identity))
        compare('training-clear',lambda:rpc('training/clear',{'ids':[identity]}),lambda:legacy.clear_training([identity]))
        # Scope guards must reject incomplete projections before any write.
        guards=[]
        native_db.execute("INSERT INTO contests(id,name,status,started_at,deadline,duration,slots,config) VALUES('archived-replay','Historic','finished',?,?,60,'[]',?)",(NOW.isoformat(),NOW.isoformat(),json.dumps({'strategy':'replay','contest':'ABC 469'})))
        assert rpc('workspace',fail=True)['code']=='MIGRATION_PENDING';guards.append('finished-replay-history-not-hidden')
        previous=native_db.execute('SELECT * FROM training ORDER BY id').fetchall()
        assert rpc('training/start',{'id':identity,'deferWorkspace':True,'deferActivation':True},fail=True)['code']=='MIGRATION_PENDING'
        assert native_db.execute('SELECT * FROM training ORDER BY id').fetchall()==previous;guards.append('unsupported-start-does-not-mutate-training')
        native_db.execute("DELETE FROM contests WHERE id='archived-replay'")
        native_db.execute('INSERT INTO account_problem_facts VALUES(?,?,?)',('private-only',json.dumps({'statement':{'accountReading':True}}),NOW.isoformat()))
        assert rpc('data',fail=True)['code']=='MIGRATION_PENDING';guards.append('private-catalogue-overlay-not-hidden')
        native_db.execute("DELETE FROM account_problem_facts WHERE problem_id='private-only'")
        alias=rows[0].get('aliasIds',[identity])[-1]
        records=[('one',identity,'run','local','RUN_OK','print(1)','2026-11-04T10:00:00Z'),
                 ('two',alias,'submit','official','WA','int main(){return 1;}','2026-11-04T11:00:00Z'),
                 ('three',identity,'submit','official','AC','int main(){return 0;}','2026-11-04T12:00:00Z'),
                 ('four',rows[1]['id'],'submit','local','SAMPLE_PASS','sample-only','2026-11-04T12:00:00Z')]
        for sid,pid,mode,scope,verdict,code,at in records:
            seed('INSERT INTO submissions(id,problem_id,mode,scope,verdict,code,submitted_at,finished_at) VALUES(?,?,?,?,?,?,?,?)',(sid,pid,mode,scope,verdict,code,at,at))
        for index,query in enumerate([{}, {'compact':['1']},{'id':[identity]},{'id':[alias],'compact':['1']},{'resultsOnly':['1']},{'verdict':['WA']},{'platform':['AtCoder']},{'platform':['CF']},{'q':['Train']},{'q':['wa']},{'q':["x') OR 1=1 --"]},{'offset':['1'],'limit':['2'],'order':['asc']} ]):
            kwargs={k:v[0] for k,v in query.items()}
            mapping={'id':'identity','resultsOnly':'results_only','q':'query'}
            kwargs={mapping.get(k,k):v for k,v in kwargs.items()}
            for flag in ['compact','results_only']:
                if flag in kwargs:kwargs[flag]=kwargs[flag]=='1'
            compare('submission-list-'+str(index),lambda query=query:rpc('submissions',query=query),lambda kwargs=kwargs:legacy.submissions(**kwargs))
        for sid,_,_,_,_,_,_ in records:
            compare('history-code-'+sid,lambda sid=sid:rpc('submission',query={'id':[sid]})['submission'],lambda sid=sid:legacy._submission(legacy_db.execute('SELECT * FROM submissions WHERE id=?',(sid,)).fetchone()))
        compare('official-history-and-real-review-view',lambda:rpc('workspace'),legacy.workspace)
        result={'passed':len(checks),'checks':checks,'guardsPassed':len(guards),'guards':guards,'work':str(work),'personalDataUsed':False,'fixedClock':NOW.isoformat(),'catalogueRows':len(rows)}
        result['nativeSha256']=hashlib.sha256(binary.read_bytes()).hexdigest()
        (report or ROOT/'.backups/native-phase2-parity.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
        print(json.dumps(result,ensure_ascii=False))
    finally:
        assets.close();legacy_db.close();native_db.close();process.stdin.close()
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:process.kill();process.wait()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--native',type=Path);parser.add_argument('--output',type=Path)
    args=parser.parse_args();run(args.native,args.output)
