"""Retry only explicit original IDs and previously reviewed mirror bindings."""
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys

ROOT=Path(os.environ['TB_STATEMENT_AUDIT_DIR']).resolve();REPO=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(REPO/'backend'),str(REPO/'backend/common')]
from fetch_all import Client,LOCAL,write
from reconcile_recovery import equivalents,samples
from statement_integrity import content_complete,native_submission_supported
import public_platforms

mapping=json.loads((REPO/'backend/resources/replay-mirrors.json').read_text('utf8'))
known={}
for first,second in mapping.items():known.setdefault(first,[]).append(second);known.setdefault(second,[]).append(first)
review=ROOT/'recovery-render-review.json'
render_bad={r['id'].split('\t',1)[0] for r in json.loads(review.read_text('utf8'))['issues']} if review.exists() else set()
with sqlite3.connect(ROOT/'baseline.sqlite3') as db:
    old={identity:json.loads(raw) for identity,raw in db.execute('SELECT problem_id,content FROM statements')}
    meta={identity:json.loads(raw) for identity,raw in db.execute('SELECT id,encoded FROM problems')}

def recover(row):
    identity=row['id'];target=ROOT/'parsed'/(hashlib.sha256(identity.encode()).hexdigest()+'.json')
    if identity not in render_bad and target.exists() and content_complete(json.loads(target.read_text('utf8'))['statement']):return 'already-complete'
    url=row['url'];urls=[*known.get(url,[]),*('https://'+key for key in equivalents(url))]
    match=re.fullmatch(r'https://codeforces.com/(?:contest/(\d+)/problem|problemset/problem/(\d+))/([A-Z]\d?)',url)
    if match:urls.append('https://www.luogu.com.cn/problem/CF'+(match[1] or match[2])+match[3])
    match=re.fullmatch(r'https://atcoder.jp/contests/[^/]+/tasks/([\w]+)',url)
    if match:urls.append('https://www.luogu.com.cn/problem/AT_'+match[1])
    for key in ('originalUrl','mirrorUrl','originalProblemUrl','sourceProblemUrl'):
        candidate=meta[identity].get(key)
        if isinstance(candidate,str) and native_submission_supported(candidate):urls.append(candidate)
    for candidate in dict.fromkeys(u for u in urls if u!=url):
        LOCAL.sources=[]
        attempt={'id':identity,'url':candidate,'originalUrl':url,'time':dt.datetime.now(dt.timezone.utc).isoformat(),'binding':'explicit-platform-id-or-reviewed-mirror'}
        try:
            value=public_platforms.statement(Client(),identity,row['title'],candidate)
            if not content_complete(value):raise ValueError('Original resources remain incomplete')
            if samples(old.get(identity) or {})-samples(value):raise ValueError('Existing source samples differ from this candidate')
            value.update(id=identity,url=url)
            packet={'statement':value,'sources':LOCAL.sources,'binding':{'method':'explicit-platform-id-or-reviewed-mirror-and-all-existing-samples','originalUrl':url,'mirrorUrl':candidate}}
            target.write_text(json.dumps(packet,ensure_ascii=False),'utf8');attempt.update(status=200,result='verified');write(ROOT/'evidence/identity-alternatives.jsonl',attempt);return 'recovered'
        except Exception as error:
            attempt.update(status=getattr(error,'code',None),result='unresolved',error=str(error)[:180]);write(ROOT/'evidence/identity-alternatives.jsonl',attempt)
    return 'unresolved'

rows=json.loads((ROOT/'initial-audit.json').read_text('utf8'))['missing']
counts={}
with concurrent.futures.ThreadPoolExecutor(4) as pool:
    for result in pool.map(recover,rows):counts[result]=counts.get(result,0)+1
print(json.dumps(counts),flush=True)
