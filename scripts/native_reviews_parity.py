"""Exercise legacy/Rust review scheduling and official history on generated journals.

The legacy implementation is an independent test oracle. Neither runtime opens
the normal installation or an existing personal journal, and Rust has no fallback.
"""
import argparse
from contextlib import contextmanager
import datetime as dt
import difflib
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common'),str(ROOT/'scripts')]
os.environ['TB_OFFLINE']='1'


def run(binary,output):
    from build_native_catalog import public_store, signature
    from training import TrainingService,ServiceError
    from assets import AssetLibrary
    from catalog_payload import project_row
    work=Path(tempfile.mkdtemp(prefix='native-reviews-',dir=ROOT/'.backups'))
    state=work/'native';state.mkdir()
    now=[dt.datetime(2026,11,6,4,tzinfo=dt.timezone.utc)]
    binary=binary.resolve(strict=True)
    process=None;counter=0;token=None
    checks=[];guards=[]
    def rpc(path,body=None,query=None,fail=False):
        nonlocal counter
        counter+=1
        request={'version':1,'id':str(counter),'method':'GET' if body is None else 'POST','path':path,'query':{k:[str(v)] for k,v in (query or {}).items()}}
        if body is not None:request.update(body=body,token=token)
        process.stdin.write(json.dumps(request,ensure_ascii=False)+'\n');process.stdin.flush()
        response=process.stdout.readline()
        if not response:raise RuntimeError(process.stderr.read())
        response=json.loads(response)
        if not response['ok']:
            if fail:return response['error']
            raise AssertionError((path,response['error']))
        if fail:raise AssertionError('Expected rejection')
        return response['data']
    def launch():
        nonlocal process,token
        process=subprocess.Popen([str(binary),'sandbox',str(ROOT),str(state)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf8',env={**os.environ,'TB_NATIVE_TEST_NOW':now[0].isoformat()},creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        token=rpc('account')['token']
    def stop():
        if process:
            process.stdin.close()
            try:process.wait(timeout=8)
            except subprocess.TimeoutExpired:process.kill();process.wait();raise
            assert process.returncode==0
    launch()
    native=sqlite3.connect(state/'personal.sqlite3',isolation_level=None)
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
    assets=AssetLibrary(store,cache_dir=work/'assets',portable=old.portable_problem)
    original_problem=assets.problem;assets.problem=lambda identity:original_problem(identity,fetch=False);old.assets=assets
    def compare(name,actual,expected):
        if actual!=expected:
            a=json.dumps(expected,ensure_ascii=False,sort_keys=True,indent=2);b=json.dumps(actual,ensure_ascii=False,sort_keys=True,indent=2)
            (work/(name+'-legacy.json')).write_text(a,'utf8');(work/(name+'-rust.json')).write_text(b,'utf8')
            print('\n'.join(list(difflib.unified_diff(a.splitlines(),b.splitlines(),fromfile='legacy',tofile='rust'))[:120]),flush=True)
            raise AssertionError(f'{name} differs; {work}')
        checks.append(name);print('PASS',name,flush=True)
        return actual
    def seed(sql,params=()):
        legacy.execute(sql,params);native.execute(sql,params)
    def receipt(sid,pid,verdict,at,code='int main(){}',seen=0,scope='official',mode='submit',message=''):
        seed('INSERT INTO submissions(id,problem_id,mode,scope,verdict,code,submitted_at,finished_at,solution_seen,message) VALUES(?,?,?,?,?,?,?,?,?,?)',(sid,pid,mode,scope,verdict,code,at,at,seen,message))
    def workspace(name):return compare(name,rpc('workspace'),old.workspace())
    def documents(name):
        snapshot=lambda db:[(row[0],json.loads(row[1]),row[2]) for row in db.execute("SELECT key,value,updated_at FROM account_preferences WHERE key LIKE 'review-%' ORDER BY key")]
        compare(name,snapshot(native),snapshot(legacy))
    def reject(name,path,body,old_action,status,query=None):
        before=native.execute('SELECT * FROM drafts ORDER BY problem_id,context').fetchall()
        assert rpc(path,body,query,True)['status']==status
        try:old_action()
        except ServiceError as error:assert error.status==status,(name,error.status)
        else:raise AssertionError(f'Legacy did not reject {name}')
        assert native.execute('SELECT * FROM drafts ORDER BY problem_id,context').fetchall()==before
        guards.append(name);print('PASS',name,flush=True)
    try:
        candidates=[row for row in rows if row.get('platform')=='Codeforces' and row.get('difficulty') and not row.get('difficultyEstimated') and row.get('catalogContentReady') and not row.get('catalogHidden') and row.get('problemType','standard')=='standard']
        selected=candidates[:16];assert len(selected)==16
        pid=selected[0]['id'];alias=next((v for v in selected[0].get('aliasIds',[]) if v!=pid),pid)
        workspace('empty-history')
        for index,row in enumerate(selected[:8]):
            stamp=f'2026-11-{index+1:02}T00:00:00.000000Z'
            if index>=5:stamp='2026-11-05T00:00:00.000000Z'
            receipt('ability-'+str(index),row['id'],'AC',stamp)
        workspace('qualified-independent-official-history')
        # Repeated passes do not create a new first-pass calendar day.
        receipt('repeat',selected[1]['id'],'AC','2026-11-06T00:00:00.000000Z')
        workspace('duplicate-ac-keeps-first-pass-streak')
        receipt('actual-wa',alias,'WA','2026-11-04T16:01:00.000000Z')
        compare('join-real-wa',rpc('training/start',{'id':pid}),old.start_training(pid))
        plan=workspace('beijing-next-day-rewrite')['reviews'];task=next(item for item in plan['tasks'] if item['problemId']==pid);review_id=task['id']
        documents('identical-rewrite-journal')
        compare('deferred-rewrite-entry',rpc('training/start',{'id':pid,'deferWorkspace':True}),old.start_training(pid,defer_workspace=True))
        compare('ordinary-draft',rpc('draft',{'id':pid,'code':'normal draft','language':'python3'}),old.save_draft(pid,'normal draft',language='python3'))
        compare('review-open-keeps-ordinary-draft',rpc('problem',query={'id':pid,'reviewId':review_id}),old.problem(pid,review_id=review_id))
        compare('review-draft-separated',rpc('draft',{'id':pid,'reviewId':review_id,'code':'fresh review 😀','language':'python3'}),old.save_draft(pid,'fresh review 😀',language='python3',review_id=review_id))
        compare('review-draft-read',rpc('problem',query={'id':pid,'reviewId':review_id}),old.problem(pid,review_id=review_id))
        if alias!=pid:
            # The immutable native URL index also carries retired remote IDs;
            # the offline oracle has no remote extension to open those rows.
            value=rpc('problem',query={'id':alias,'reviewId':review_id})
            assert value['reviewTask']['id']==review_id and value['draft']=='fresh review 😀' and value['draftLanguage']=='python3'
            checks.append('compiled-alias-preserves-canonical-review-and-draft')
        compare('ordinary-draft-still-present',rpc('problem',query={'id':pid}),old.problem(pid))
        reject('wrong-task-identity','problem',None,lambda:old.problem(selected[1]['id'],review_id=review_id),404,{'id':selected[1]['id'],'reviewId':review_id})
        compare('remove-cancels-review-keeps-code',rpc('training/remove',{'id':pid}),old.remove_training(pid))
        compare('restore-review',rpc('training/start',{'id':pid,'restoreReviewId':review_id,'deferWorkspace':True}),old.start_training(pid,restore_review_id=review_id,defer_workspace=True))
        documents('cancel-restore-identical-journal')
        receipt('fresh-verified-ac',pid,'AC','2026-11-06T04:00:00.000000Z',code='fresh rewritten source')
        # A real native receipt commit also activates the problem. The browser
        # adapter itself remains unported and is not impersonated by this test.
        seed("UPDATE training SET active=1,removed_at=NULL,active_at=MAX(active_at,?) WHERE id=?",('2026-11-06T04:00:00.000000Z',pid))
        workspace('actual-receipt-settles-rewrite')
        documents('actual-next-day-reward-once')
        for db in (native,legacy):assert sum(json.loads(row[0]).get('xp',0) for row in db.execute("SELECT value FROM account_preferences WHERE key LIKE 'review-reward:%'"))==20
        workspace('same-receipt-poll-does-not-duplicate-reward')
        compare('review-bound-history',rpc('submissions',query={'id':pid,'reviewId':review_id}),old.submissions(pid,review_id=review_id))
        compare('reward-attached-only-to-bound-receipt',rpc('submission',query={'id':'fresh-verified-ac'})['submission'],old._submission(legacy.execute("SELECT * FROM submissions WHERE id='fresh-verified-ac'").fetchone()))
        for index,row in enumerate(selected[8:]):
            sid='backlog-'+str(index);receipt(sid,row['id'],'WA','2026-11-05T00:00:00.000000Z')
            seed('INSERT INTO training(id,active_at) VALUES(?,?)',(row['id'],'2026-11-05T00:00:00.000000Z'))
        backlog=workspace('backlog-budget-and-paused-new-work')
        documents('backlog-allocation-persisted')
        compare('clear-today-postpones-real-reviews',rpc('training/clear',{'ids':[r['id'] for r in selected[8:]]}),old.clear_training([r['id'] for r in selected[8:]]))
        workspace('no-same-day-review-refill')
        stop();now[0]+=dt.timedelta(days=1);launch()
        workspace('restart-next-day-restores-spaced-queue')
        documents('restart-preserves-all-receipts')
        # Frozen history is a real workspace input, including tombstones,
        # absent statements and saved exam drafts. No contest is started here.
        def contest(cid,strategy='replay',*,slots=None,config=None,deleted=None,status='finished'):
            frozen=slots if slots is not None else [dict(letter=chr(65+i),id=row['id'],title=row['title'],difficulty=row['difficulty'],tags=row.get('tags',[]),judgeScope='official',statementAvailable=i==0) for i,row in enumerate(selected[:2])]
            cfg={'strategy':strategy,'contest':selected[0]['contest'],'wrongPenalty':20,'compilePenalty':False,**(config or {})}
            seed('INSERT INTO contests(id,name,status,started_at,deadline,finished_at,duration,slots,config,deleted_at) VALUES(?,?,?,?,?,?,?,?,?,?)',(cid,'重现赛 · '+selected[0]['contest'],status,'2026-11-03T00:00:00.000000Z','2026-11-03T01:00:00.000000Z','2026-11-03T01:00:00.000000Z',60,json.dumps(frozen,ensure_ascii=False),json.dumps(cfg,ensure_ascii=False),deleted))
        contest('finished-replay')
        compare('frozen-replay-read',rpc('contest',query={'id':'finished-replay'}),old.contest('finished-replay'))
        workspace('finished-replay-history-no-longer-blocks-workspace')
        for sid,verdict,scope,minute in [('exam-ce','CE','official',1),('exam-wa','WA','official',2),('exam-ac','AC','official',8)]:
            receipt(sid,pid,verdict,f'2026-11-03T00:{minute:02}:00.000000Z',scope=scope)
            seed('UPDATE submissions SET contest_id=? WHERE id=?',('finished-replay',sid))
        compare('replay-official-score-alias-and-penalty',rpc('contest',query={'id':'finished-replay'}),old.contest('finished-replay'))
        compare('finished-exam-draft-context',rpc('problem',query={'id':pid,'contestId':'finished-replay'}),old.problem(pid,contest_id='finished-replay'))
        reject('finished-exam-cannot-rewrite-draft','draft',{'id':pid,'contestId':'finished-replay','code':'must not be written'},lambda:old.save_draft(pid,'must not be written',contest_id='finished-replay'),409)
        contest('finished-team',strategy='team')
        receipt('peer-local-sample',pid,'SAMPLE_PASS','2026-11-03T00:10:00.000000Z',scope='local');seed('UPDATE submissions SET contest_id=? WHERE id=?',('finished-team','peer-local-sample'))
        value=compare('team-history-local-samples-are-not-official-score',rpc('contest',query={'id':'finished-team'}),old.contest('finished-team'));assert value['contest']['accepted']==0
        contest('finished-blind',strategy='comprehensive',config={'compilePenalty':True})
        for sid,verdict,minute in [('blind-ce','CE',1),('blind-sample','SAMPLE_PASS',5)]:
            receipt(sid,pid,verdict,f'2026-11-03T00:{minute:02}:00.000000Z',scope='local');seed('UPDATE submissions SET contest_id=? WHERE id=?',('finished-blind',sid))
        compare('reviewed-local-history-keeps-legacy-score',rpc('contest',query={'id':'finished-blind'}),old.contest('finished-blind'))
        contest('finished-calendar',config={'calendarEvent':{'id':'generated-calendar-event'}})
        compare('calendar-history-keeps-live-label-and-statement-readiness',rpc('contest',query={'id':'finished-calendar'}),old.contest('finished-calendar'))
        contest('deleted-replay',deleted='2026-11-06T00:00:00.000000Z')
        workspace('tombstoned-replay-still-keeps-reveal-evidence')
        compare('tombstoned-contest-stays-readable-by-id',rpc('contest',query={'id':'deleted-replay'}),old.contest('deleted-replay'))
        cancelled=selected[11]['id'];contest('cancelled-exam',status='cancelled',deleted='2026-11-06T00:00:00.000000Z',slots=[{'letter':'A','id':cancelled,'title':selected[11]['title']}])
        seed('INSERT INTO drafts VALUES(?,?,?,?)',(cancelled,'cancelled-exam','withdrawn exam draft 😀','2026-11-06T00:00:00.000000Z'))
        compare('cancelled-draft-recovered-without-overwriting-normal-context',rpc('problem',query={'id':cancelled}),old.problem(cancelled))
        extra=candidates[16:20];assert len(extra)==4
        frozen=[dict(letter=chr(65+i),id=row['id'],title=row['title'],difficulty=row['difficulty'],tags=row.get('tags',[]),judgeScope='official',trainingBefore=None,trainingAdded=i!=3) for i,row in enumerate(extra)]
        contest('legacy-auto-joins',slots=frozen)
        for row in extra:seed('INSERT INTO training(id,active_at) VALUES(?,?)',(row['id'],'2026-11-03T00:00:00.000000Z'))
        seed('INSERT INTO drafts VALUES(?,?,?,?)',(extra[1]['id'],'','','2026-11-03T00:00:00.000000Z'))
        receipt('protected-history',extra[2]['id'],'RUN_OK','2026-11-03T00:00:00.000000Z',scope='samples',mode='run')
        stop();launch();old._contest_entries_checked=False
        workspace('prune-only-proven-unedited-legacy-auto-joins')
        assert native.execute('SELECT active FROM training WHERE id=?',(extra[0]['id'],)).fetchone()[0]==0
        assert all(native.execute('SELECT active FROM training WHERE id=?',(row['id'],)).fetchone()[0]==1 for row in extra[1:])
        compare('legacy-prune-receipt',json.loads(native.execute("SELECT value FROM account_preferences WHERE key='contest-edited-training-v1'").fetchone()[0]),json.loads(legacy.execute("SELECT value FROM account_preferences WHERE key='contest-edited-training-v1'").fetchone()[0]))
        contest('unknown-retained-name',config={'contest':'Unknown private provenance fixture'})
        unchanged=native.execute('SELECT * FROM training ORDER BY id').fetchall()
        assert rpc('workspace',fail=True)['code']=='MIGRATION_PENDING';assert native.execute('SELECT * FROM training ORDER BY id').fetchall()==unchanged;guards.append('unported-event-name-does-not-drop-history-or-mutate-training')
        seed("DELETE FROM contests WHERE id='unknown-retained-name'")
        # Malformed retained goals and unported planner evidence are guarded.
        seed("INSERT INTO goals(id,created_at,config) VALUES('not-ported',?,'{}')",(now[0].isoformat(),))
        assert rpc('workspace',fail=True)['code']=='INVALID_STORED_DATA';guards.append('malformed-goal-is-not-hidden')
        native.execute("DELETE FROM goals WHERE id='not-ported'");legacy.execute("DELETE FROM goals WHERE id='not-ported'")
        previous=native.execute('SELECT * FROM training ORDER BY id').fetchall()
        assert rpc('learning-summary/refresh',{},fail=True)['code']=='MIGRATION_PENDING';guards.append('full-learning-evidence-not-projected-as-empty')
        assert native.execute('SELECT * FROM training ORDER BY id').fetchall()==previous
        with (ROOT/'data/library.sqlite3').open('rb') as stream:seed_hash=hashlib.file_digest(stream,'sha256').hexdigest()
        result={'passed':len(checks),'checks':checks,'exactLegacyComparisons':len(checks)-int(alias!=pid),'additionalConfirmedAliasCheck':alias!=pid,'guardsPassed':len(guards),'guards':guards,'work':str(work),'nativeSha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'nativeBinary':str(binary),'privateLiveStateOpened':False,'officialSubmissionsSent':0,'pythonRuntimeFallback':False,'publicSeed':signature(ROOT/'data/library.sqlite3'),'publicSeedSha256':seed_hash,'publicSeedScope':'The exact current read-only public seed above; no personal catalogue or live account input.'}
        output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(result,ensure_ascii=False),flush=True)
    finally:
        assets.close();legacy.close();native.close();stop()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--native',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();run(args.native,args.output)
