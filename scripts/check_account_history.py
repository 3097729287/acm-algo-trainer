"""Restore a large synthetic journal through real HTTP on two disposable clients.

Uses the production HTTP handler and chunk client with an isolated SQLite
service fixture. No real account, personal installation or official submission
is accessed. MySQL behavior is checked by the separate shared-service suite.
"""
import argparse
import base64
import copy
import datetime as dt
import hashlib
import http.client
import json
import os
from pathlib import Path
import random
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
os.environ['TB_OFFLINE']='1'
from test_account_sync import CloudStateTests
from account_chunks import code_reference

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--problems',type=int,default=7300)
    parser.add_argument('--attempts',type=int,default=3)
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    if not 1<=args.problems<=10000 or not 1<=args.attempts<=5:parser.error('Fixture bounds exceeded')
    fixture=CloudStateTests();fixture.setUp();started=time.monotonic()
    try:
        fixture.signup();status,result=fixture.login();assert status==200,result
        sync=fixture.server.accounts.state_sync;sync.close();sync.stop.clear()
        service=fixture.server.training
        # A finished WA fixture supplies every current submission column without
        # inventing an official success or triggering any real platform request.
        result=service.record_official({'id':'fixture::A','url':'https://codeforces.com/contest/1/problem/A','code':'// prototype'},
            {'status':'finished','submissionId':'100000000','verdict':'WA'})
        state,_=sync._capture()
        proto=state['tables']['submissions'][0]
        fact=json.loads(state['tables']['account_problem_facts'][0]['value'])
        state['tables']['submissions']=[];state['tables']['account_problem_facts']=[]
        state['tables']['training']=[];state['tables']['drafts']=[]
        rng=random.Random(20261028);original={};now=service._now()
        templates=json.loads((ROOT/'backend/resources/code-templates.json').read_text(encoding='utf8'))['templates']
        for i in range(args.problems):
            pid=f'history-fixture::{i:05d}';value=copy.deepcopy(fact)
            value['row'].update(id=pid,title=f'Synthetic history {i}',problem=str(i),url=f'https://example.test/task/{i}')
            value['statement'].update(id=pid,title=f'Synthetic history {i}',markdown='# Fixture\n\n'+base64.b64encode(rng.randbytes(3072)).decode('ascii'))
            state['tables']['account_problem_facts'].append({'problem_id':pid,'value':json.dumps(value,ensure_ascii=False),'updated_at':now.isoformat()})
            stamp=(now-dt.timedelta(days=i//10+1)).isoformat()
            for attempt in range(args.attempts):
                identity=pid+':'+str(attempt)
                code=templates[i%len(templates)]['contestCode']+'\n// fixture '+base64.b64encode(rng.randbytes(192)).decode('ascii')+'\n'
                row={**proto,'id':identity,'problem_id':pid,'code':code,'scope':'samples','mode':'run','verdict':'SAMPLE_PASS','submitted_at':stamp,'finished_at':stamp}
                state['tables']['submissions'].append(row);original[identity]=code
        state=sync.chunks.canonicalize(state);calls=[];request=sync.chunks.request
        def record(method,path,body=None,**kwargs):
            calls.append((method,path,len(json.dumps(body).encode()) if body else 0))
            return request(method,path,body,**kwargs)
        uploaded_at=time.monotonic()
        with __import__('unittest.mock',fromlist=['patch']).patch.object(sync.chunks,'request',side_effect=record):
            saved=sync._call('PUT','/v1/accounts/state',{'revision':sync.revision,'state':state})
        upload_seconds=time.monotonic()-uploaded_at
        other=fixture.other_computer(missing_library=True);restore_at=time.monotonic()
        connection=http.client.HTTPConnection('127.0.0.1',other.server_port,timeout=300)
        body=json.dumps({'loginId':'account_a','password':'fixture-password'}).encode()
        connection.request('POST','/api/account/login',body,{'Content-Type':'application/json','X-TB-Token':other.store.token})
        response=connection.getresponse();answer=json.loads(response.read());connection.close()
        assert response.status==200 and answer['authenticated'],answer
        restore_seconds=time.monotonic()-restore_at
        other_sync=other.accounts.state_sync;other_sync.close();other_sync.stop.clear()
        with other.training.lock:
            rows=[dict(p) for p in other.training.connection.execute('SELECT id,code FROM submissions')]
            assert len(rows)==len(original),(len(rows),len(original))
            assert other.training.connection.execute('SELECT COUNT(*) FROM account_problem_facts').fetchone()[0]==args.problems
        deferred=sum(not p['code'] for p in rows)
        expected_deferred=sum(code_reference(p['code']) is not None for p in state['tables']['submissions'])
        assert deferred==expected_deferred,(deferred,expected_deferred)
        for row in rows[::max(1,len(rows)//50)]:
            code=other.training.submission(row['id'])['submission']['code']
            assert code==original[row['id']],row['id']
        largest=max(n for _,_,n in calls)
        assert largest<=128*1024
        report={'synthetic':True,'storage':'isolated SQLite HTTP service; production chunk protocol and two real backend clients',
            'problems':args.problems,'submissions':len(rows),'codeDeferredOnRestore':deferred,
            'uploadRequests':len(calls),'batchUploads':sum(path=='/v2/accounts/state/objects' for _,path,_ in calls),
            'largestRequestBodyBytes':largest,'uploadSeconds':round(upload_seconds,3),'restoreSeconds':round(restore_seconds,3),
            'exactCodeSamplesChecked':len(rows[::max(1,len(rows)//50)]),'revision':saved['revision'],'totalSeconds':round(time.monotonic()-started,3)}
        if args.report:
            args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
        print(json.dumps(report,indent=2))
    finally:fixture.tearDown()

if __name__=='__main__':main()
