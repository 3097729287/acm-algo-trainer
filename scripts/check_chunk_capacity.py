"""Simulate two years of chunk packing without using any private account data.

This measures bytes/objects and incremental write amplification. It is not a
50-user HTTP load test or a prediction of every user's future code size.
"""
import argparse
import base64
import datetime as dt
import hashlib
import json
from pathlib import Path
import random
import sqlite3
import sys
import threading
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from account_chunks import ChunkTransport,code_reference,encode
from account_sync import TABLES

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--days',type=int,default=730)
    parser.add_argument('--per-day',type=int,default=10)
    parser.add_argument('--attempts',type=int,default=3)
    parser.add_argument('--growth-days',type=int,default=30)
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    if not (1<=args.days<=1000 and 1<=args.per_day<=30 and 1<=args.attempts<=5 and 0<=args.growth_days<=60):parser.error('Simulation bounds exceeded')
    db=sqlite3.connect(':memory:',isolation_level=None);db.row_factory=sqlite3.Row
    now=dt.datetime(2026,10,28,tzinfo=dt.timezone.utc)
    service=SimpleNamespace(connection=db,lock=threading.RLock(),_now=lambda:now)
    sync=SimpleNamespace(service=service,owner='10000000-0000-4000-8000-000000000001',meta={},stop=threading.Event())
    transport=ChunkTransport(sync);transport.enabled=True
    state={'format':'tb-account-state-v1','tables':{t:[] for t in TABLES},'publicAccounts':{}}
    rng=random.Random(20261028)
    templates=json.loads((ROOT/'backend/resources/code-templates.json').read_text(encoding='utf8'))['templates']
    # Portable facts have 4 KiB of deterministic, incompressible synthetic
    # text (about 3 KiB after gzip), matching the measured order of magnitude.
    def task(day,index):
        identity=f'simulated-task-{day:04d}-{index:02d}'
        noise=base64.b64encode(rng.randbytes(3072)).decode('ascii')
        stamp=(now-dt.timedelta(days=args.days-day)).isoformat()
        state['tables']['account_problem_facts'].append({'problem_id':identity,'value':json.dumps({'row':{'id':identity,'title':'Synthetic fixture'},'statement':{'markdown':noise}}),'updated_at':stamp})
        for attempt in range(args.attempts):
            code=templates[(day+index)%len(templates)]['contestCode']+'\n// fixture '+base64.b64encode(rng.randbytes(192)).decode('ascii')+'\n'
            state['tables']['submissions'].append({'id':identity+'-'+str(attempt),'problem_id':identity,'code':code,'submitted_at':stamp,'finished_at':stamp,'scope':'local','mode':'run','verdict':'SAMPLE_PASS'})
    for day in range(args.days):
        for index in range(args.per_day):task(day,index)
    def objects():return {p['hash']:len(p['payload']) for p in db.execute('SELECT hash,payload FROM account_sync_objects')}
    value=transport.canonicalize(state);root=transport.pack(value);initial=objects();archives={code_reference(p['code'])['root'] for p in value['tables']['submissions'] if code_reference(p['code'])}
    # Check the exact root structure and a sample of historical code offsets.
    manifest=json.loads(transport.read_blob(root));assert manifest['format']=='tb-private-chunk-state-v2'
    for row in value['tables']['submissions'][::max(1,len(value['tables']['submissions'])//100)]:
        ref=code_reference(row['code'])
        if not ref:continue
        raw=transport.read_blob(ref['root'],262144)[ref.get('offset',0):ref.get('offset',0)+ref['bytes']]
        assert hashlib.sha256(raw).hexdigest()==ref['sha256']
    days=[]
    for extra in range(args.growth_days):
        for index in range(args.per_day):task(args.days+extra,index)
        prior=objects();value=transport.canonicalize(state);transport.pack(value);current=objects()
        added={h:n for h,n in current.items() if h not in prior}
        days.append({'newObjects':len(added),'compressedBytes':sum(added.values())})
    final=objects()
    report={'simulation':True,'newProblems':args.days*args.per_day,'submissions':args.days*args.per_day*args.attempts,
        'attemptsPerProblem':args.attempts,'syntheticFactRawBytes':4096,
        'initialObjects':len(initial),'initialCompressedBytes':sum(initial.values()),'coldArchives':len(archives),
        'additionalDays':args.growth_days,'dailyChanges':days,'maximumDailyCompressedBytes':max((x['compressedBytes'] for x in days),default=0),
        'allCachedObjectBytesAfterGrowth':sum(final.values()),'largestCompressedObject':max(final.values()),
        'fiftyAccountsCompressedObjectsWithoutSqlOverhead':50*sum(final.values()),
        'limits':'Compression/object accounting only; SQL indexes, binary logs, OS, backups, network contention and larger future code are additional.'}
    assert report['largestCompressedObject']<=66*1024
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='dailyChanges'},indent=2))
    db.close()

if __name__=='__main__':main()
