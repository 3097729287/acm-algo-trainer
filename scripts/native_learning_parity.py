"""Exercise the real legacy planner and Rust against independent test journals."""
from contextlib import contextmanager
from pathlib import Path
import datetime as dt
import difflib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import argparse
import hashlib

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common'),str(ROOT/'scripts')]
os.environ['TB_OFFLINE']='1'

def run(binary=None,report=None):
    from build_native_catalog import public_store
    from catalog_payload import project_row
    from training import TrainingService,ServiceError
    from learning_summary import LearningSummary,KEY
    work=Path(tempfile.mkdtemp(prefix='native-learning-',dir=ROOT/'.backups'))
    now=[dt.datetime(2026,11,5,4,tzinfo=dt.timezone.utc)]
    binary=(binary or ROOT/'target/debug/tobe-core.exe').resolve(strict=True)
    native_dir=work/'native';native_dir.mkdir()
    process=None;token=None;counter=0;checks=[];guards=[]
    def launch():
        nonlocal process,token
        process=subprocess.Popen([str(binary),'sandbox',str(ROOT),str(native_dir)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf8',env={**os.environ,'TB_NATIVE_TEST_NOW':now[0].isoformat()},creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        token=rpc('account')['token']
    def stop():
        if process:
            process.stdin.close()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait()
    def rpc(path,body=None,query=None,fail=False):
        nonlocal counter
        counter+=1
        envelope={'version':1,'id':str(counter),'method':'GET' if body is None else 'POST','path':path,'query':{k:[v] for k,v in (query or {}).items()}}
        if body is not None:envelope.update(body=body,token=token)
        process.stdin.write(json.dumps(envelope,ensure_ascii=False)+'\n');process.stdin.flush()
        line=process.stdout.readline()
        if not line:raise RuntimeError(process.stderr.read())
        result=json.loads(line)
        if not result['ok']:
            if fail:return result['error']
            raise AssertionError(result['error'])
        if fail:raise AssertionError('Expected a rejected mutation')
        return result['data']
    launch()
    native=sqlite3.connect(native_dir/'personal.sqlite3',isolation_level=None)
    legacy=sqlite3.connect(work/'legacy.sqlite3',isolation_level=None);legacy.row_factory=sqlite3.Row
    legacy.executescript((ROOT/'backend-rust/schema/personal.sql').read_text('utf8'))
    store=public_store(ROOT/'data/library.sqlite3');rows=store._catalog_rows()
    store.training_data=lambda:{'rows':[project_row(row) for row in rows]};store.data=lambda:{'rows':rows};store.token=token
    old=TrainingService.__new__(TrainingService);old.connection=legacy;old.lock=threading.RLock();old.store=store;old.db_path=work/'legacy.sqlite3';old.clock=lambda:now[0];old.closed=False;old.admin_mode=False;old._insights_signature=lambda _:None
    @contextmanager
    def write():
        legacy.execute('BEGIN IMMEDIATE')
        try:yield legacy;legacy.execute('COMMIT')
        except:legacy.execute('ROLLBACK');raise
    old._write=write
    summary=LearningSummary(old)
    def normal(v):
        if isinstance(v,list):return [normal(x) for x in v]
        if not isinstance(v,dict):return v
        result={k:normal(value) for k,value in v.items() if k!='revision'}
        if 'id' in result and ('week' in result and 'tasks' in result and 'tracks' in result or 'reason' in result and 'at' in result):result['id']='<generated-id>'
        return result
    def compare(name,actual,expected):
        a,b=normal(expected),normal(actual)
        if a!=b:
            expected=json.dumps(a,ensure_ascii=False,sort_keys=True,indent=2);actual=json.dumps(b,ensure_ascii=False,sort_keys=True,indent=2)
            (work/(name+'-legacy.json')).write_text(expected,'utf8');(work/(name+'-rust.json')).write_text(actual,'utf8')
            print('\n'.join(list(difflib.unified_diff(expected.splitlines(),actual.splitlines()))[:100]))
            raise AssertionError(f'{name} differs; preserved at {work}')
        checks.append(name);print('PASS',name,flush=True)
        return rpc('learning-summary')
    def refresh(name):return compare(name,rpc('learning-summary/refresh',{}),summary.refresh())
    def update(name,action,**fields):
        n=rpc('learning-summary');p=summary.snapshot()
        return compare(name,rpc('learning-summary/update',{'action':action,'revision':n['revision'],**fields}),summary.update({'action':action,'revision':p['revision'],**fields}))
    def accept(name):
        n=rpc('learning-summary');p=summary.snapshot()
        return compare(name,rpc('learning-summary/update',{'action':'accept','revision':n['revision'],'proposalId':n['proposal']['id']}),summary.update({'action':'accept','revision':p['revision'],'proposalId':p['proposal']['id']}))
    def snapshot_db(db):return [tuple(row) for row in db.execute('SELECT key,value,updated_at FROM account_preferences ORDER BY key')]
    def rejected(name,action,status,**fields):
        n=rpc('learning-summary');p=summary.snapshot();saved=snapshot_db(native);saved_old=snapshot_db(legacy)
        error=rpc('learning-summary/update',{'action':action,'revision':n['revision'],**fields},fail=True)
        assert error['status']==status,(name,error)
        try:summary.update({'action':action,'revision':p['revision'],**fields})
        except ServiceError as e:assert e.status==status,(name,e.status)
        else:raise AssertionError('Legacy request should fail')
        assert snapshot_db(native)==saved and snapshot_db(legacy)==saved_old
        checks.append(name);print('PASS',name,flush=True)
    try:
        refresh('first-refresh-no-guessed-time')
        prior=rpc('learning-summary')['revision'];refresh('idempotent-refresh');assert prior==rpc('learning-summary')['revision']
        rejected('configure-invalid-minutes','configure',422,config={'weekdayMinutes':True,'weekendMinutes':120})
        rejected('configure-invalid-rest-days','configure',400,config={'weekdayMinutes':60,'weekendMinutes':120,'restDays':[True]})
        rejected('configure-invalid-tracks','configure',400,config={'weekdayMinutes':60,'weekendMinutes':120},tracks=['io-basics','io-basics'])
        value=update('configure-shared-budget','configure',config={'weekdayMinutes':60,'weekendMinutes':120,'restDays':[5]},tracks=['io-basics','basic-control'])
        assert value['plan'] is None and all(d['used']<=d['minutes'] for d in value['proposal']['days'])
        rejected('wrong-proposal-id','accept',409,proposalId='stale')
        value=accept('explicit-adoption');assert len(value['history'])==1
        lecture=next(t for t in value['plan']['tasks'] if t['kind']=='lecture')
        assisted=next(t for t in value['plan']['tasks'] if t['kind']=='problem' and t['topicId']==lecture['topicId'])
        value=update('assisted-study-keeps-source-context','assist',key=lecture['key'],problemId=assisted['id'])
        assert [tuple(r) for r in native.execute('SELECT * FROM training ORDER BY id')]==[tuple(r) for r in legacy.execute('SELECT * FROM training ORDER BY id')]
        value=update('reading-is-not-independent-evidence','complete',key=lecture['key'])
        topic=next(t for t in value['topics'] if t['id']==lecture['topicId']);assert topic['level']==1 and topic['independent']==0
        rejected('quiz-wrong-answer','quiz',422,topicId='io-basics',answer=1)
        rejected('quiz-rejects-bool','quiz',400,topicId='io-basics',answer=True)
        value=update('quiz-only-proves-concept','quiz',topicId='io-basics',answer=0);assert value['topics'][0]['level']==2 and value['topics'][0]['independent']==0
        task=next(t for t in value['plan']['tasks'] if t['kind']=='problem')
        rejected('cannot-check-off-a-problem','complete',422,key=task['key'])
        value=update('replace-with-unscheduled-original','replace',key=task['key'])
        value=update('postpone-reallocates-shared-budget','postpone',key=next(t['key'] for t in value['plan']['tasks'] if t['kind']=='problem'),date='2026-11-07')
        value=update('time-adjustment-keeps-completed-and-history','configure',config={'weekdayMinutes':90,'weekendMinutes':120})
        assert any(t['key']==lecture['key'] and t['status']=='done' for t in value['plan']['tasks'])
        from learning_summary import curriculum
        topic_ids=[t['id'] for t in curriculum()['topics']]
        for index in range(0,len(topic_ids),5):
            update('all-topics-shared-plan-'+str(index//5),'propose',tracks=topic_ids[index:index+5])
            update('all-topics-dismiss-'+str(index//5),'dismiss')
        update('switch-proposal-does-not-replace-plan','propose',tracks=['binary-search'])
        value=accept('switch-mainline-preserves-old-history')
        for index,reason in enumerate(['meaning','idea','implementation','bug','schedule','verify','transfer']):value=update('difficulty-advice-'+reason,'difficulty',reason=reason)
        for reason in ['hard','easy','forgot']:
            value=update('pace-proposal-'+reason,'difficulty',reason=reason)
            value=update('dismiss-proposal-'+reason,'dismiss')
        for goal,title in [('cf','练习 CF 原题'),('lanqiao','蓝桥基础'),('topic','二分边界')]:
            value=update('goal-priority-'+goal,'configure',config={'goal':{'kind':goal,'title':title,'deadline':''}})
        value=update('all-rest-days-preserve-waiting-tasks','configure',config={'restDays':list(range(7))})
        assert all(t['status']=='done' for t in value['plan']['tasks']) and value['plan']['waiting']
        value=update('restore-study-days','configure',config={'restDays':[]})
        from code_templates import builtins
        from learning_summary import curriculum
        templates={t['id']:t for t in builtins()}
        definition=next(t for t in curriculum()['topics'] if templates.get(t.get('template'),{}).get('practiceIds'))
        pid=templates[definition['template']]['practiceIds'][0]
        for db in [native,legacy]:db.execute("INSERT INTO submissions(id,problem_id,mode,code,scope,submitted_at,finished_at,verdict,solution_seen) VALUES('template-fact',?,'submit','implementation','template',?,?,'AC',1)",(pid,now[0].isoformat(),now[0].isoformat()))
        value=refresh('guided-template-is-not-independent-implementation');assert next(t for t in value['topics'] if t['id']==definition['id'])['level']==3
        for db in [native,legacy]:db.execute("UPDATE submissions SET solution_seen=0 WHERE id='template-fact'")
        value=refresh('template-evidence-preserves-implementation-stage');assert next(t for t in value['topics'] if t['id']==definition['id'])['level']==4
        value=update('team-role-budget','configure',config={'team':True,'role':'实现与核对边界'})
        reflection=next(t for t in value['plan']['tasks'] if t['kind']=='reflection')
        value=update('team-reflection-does-not-prove-independent-solve','complete',key=reflection['key'])
        # A failed final save rolls back earlier history and training writes.
        native.execute("CREATE TRIGGER reject_summary_write BEFORE INSERT ON account_preferences WHEN NEW.key='learning-summary-v1' BEGIN SELECT RAISE(ABORT,'injected failure'); END")
        saved=snapshot_db(native);n=rpc('learning-summary')
        rpc('learning-summary/update',{'action':'configure','revision':n['revision'],'config':{'weekdayMinutes':120}},fail=True)
        assert snapshot_db(native)==saved;guards.append('save-failure-rolls-back-archive-and-plan')
        n=rpc('learning-summary');lecture=next(t for t in n['plan']['tasks'] if t['kind']=='lecture');problem=next(t for t in n['plan']['tasks'] if t['kind']=='problem')
        saved_training=native.execute('SELECT * FROM training ORDER BY id').fetchall()
        rpc('learning-summary/update',{'action':'assist','revision':n['revision'],'key':lecture['key'],'problemId':problem['id']},fail=True)
        assert snapshot_db(native)==saved and native.execute('SELECT * FROM training ORDER BY id').fetchall()==saved_training;guards.append('save-failure-rolls-back-assisted-training-context')
        native.execute('DROP TRIGGER reject_summary_write')
        stop();now[0]+=dt.timedelta(days=7);launch();refresh('week-roll-preserves-old-snapshot')
        # Existing official and review facts await their own migration and must
        # never be projected as an empty ability/review history.
        native.execute("INSERT INTO submissions(id,problem_id,mode,code,scope,submitted_at,finished_at,verdict) VALUES('official-fact',?,'submit','saved source','official',?,?,'AC')",(rows[0]['id'],now[0].isoformat(),now[0].isoformat()))
        saved=snapshot_db(native);assert rpc('learning-summary/refresh',{},fail=True)['code']=='MIGRATION_PENDING';assert snapshot_db(native)==saved;guards.append('official-evidence-is-not-guessed-or-erased')
        result={'passed':len(checks),'checks':checks,'guardsPassed':len(guards),'guards':guards,'work':str(work),'personalDataUsed':False,'scope':'Local planning without unported official/review/contest facts; formal architecture remains React + Python'}
        result['nativeSha256']=hashlib.sha256(binary.read_bytes()).hexdigest()
        (report or ROOT/'.backups/native-learning-parity.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
        print(json.dumps(result,ensure_ascii=False))
    finally:stop();legacy.close();native.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--native',type=Path);parser.add_argument('--output',type=Path)
    args=parser.parse_args();run(args.native,args.output)
