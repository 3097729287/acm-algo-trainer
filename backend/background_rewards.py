"""New replays earn one background from durable official-AC evidence.

The desktop attests evidence, as it already does for task rewards. The shared
service owns the random draw and owner/original-contest deduplication.
"""
import hashlib
import json
import statistics
import uuid

def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()

def freeze(rows, info, duration, owner, *, lab=False):
    if lab or info.get('complete') is False or len(rows)<2 or duration!=info['duration']:
        return None
    keys=sorted({str(row.get('url') or row['id']).rstrip('/') for row in rows})
    if len(keys)!=len(rows):return None
    ratings=[float(row['difficulty']) for row in rows if isinstance(row.get('difficulty'),(int,float)) and not isinstance(row.get('difficulty'),bool) and 0<=row['difficulty']<=10000]
    return {'version':1,'owner':owner,'contestKey':'replay:'+digest('\n'.join(keys)),
            'originalDuration':info['duration'],'difficulty':statistics.median(ratings) if ratings else 0,
            'problems':{row['id']:'p:'+digest(str(row.get('url') or row['id']).rstrip('/')) for row in rows}}

def record_eligible(training, connection, record):
    from training import iso,parse_time
    policy=json.loads(record['config'] or '{}').get('backgroundReward')
    if not isinstance(policy,dict) or policy.get('version')!=1 or record['status']!='finished' or record['duration']!=policy['originalDuration']:
        return None
    owner=training._ranking_profile()['user_id']
    if policy.get('owner')!=owner:return None
    key='background-eligible:'+record['id']
    saved=connection.execute('SELECT value FROM account_preferences WHERE key=?',(key,)).fetchone()
    if saved:
        envelope=json.loads(saved[0])
        return envelope.get('evidence') if envelope.get('owner')==owner else None
    began,ended=parse_time(record['started_at']),parse_time(record['finished_at'])
    if not began or not ended or (ended-began).total_seconds()<record['duration']*30 or ended>parse_time(record['deadline']):return None
    aliases=training._identity_map()
    known={aliases.get(identity,identity):problem for identity,problem in policy['problems'].items()}
    accepted={}
    for row in connection.execute("SELECT id,problem_id,submitted_at FROM submissions WHERE contest_id=? AND mode='submit' AND scope='official' AND verdict='AC' AND finished_at IS NOT NULL ORDER BY submitted_at,id",(record['id'],)):
        identity=aliases.get(row['problem_id'],row['problem_id'])
        when=parse_time(row['submitted_at'])
        if identity not in known or not when or not began<=when<=ended:continue
        accepted.setdefault(known[identity],{'problemKey':known[identity],'submissionId':row['id'],'submittedAt':int(when.timestamp()*1000),'scope':'official','verdict':'AC'})
    if len(accepted)<2:return None
    value={'version':1,'contestKey':policy['contestKey'],'replayId':record['id'],
           'duration':record['duration'],'originalDuration':policy['originalDuration'],
           'startedAt':int(began.timestamp()*1000),'finishedAt':int(ended.timestamp()*1000),
           'difficulty':policy['difficulty'],'total':len(known),'accepted':list(accepted.values())}
    connection.execute('INSERT INTO account_preferences VALUES(?,?,?) ON CONFLICT(key) DO NOTHING',(key,json.dumps({'owner':owner,'evidence':value},ensure_ascii=False),iso(training._now())))
    return value

def deliver_completed(training, identity=None):
    from training import iso,ServiceError
    from gameplay import _request
    owner=training._ranking_profile()['user_id']
    with training.lock,training._write() as connection:
        clauses="status='finished' AND config LIKE '%\"backgroundReward\"%'"
        records=connection.execute('SELECT * FROM contests WHERE '+clauses+(' AND id=?' if identity else ''),(identity,) if identity else ()).fetchall()
        for record in records:record_eligible(training,connection,record)
        rows=[dict(row) for row in connection.execute("SELECT key,value FROM account_preferences p WHERE key LIKE 'background-eligible:%' AND NOT EXISTS(SELECT 1 FROM account_preferences done WHERE done.key='background-granted:'||substr(p.key,21))"+(' AND key=?' if identity else '')+' ORDER BY key LIMIT 100',('background-eligible:'+identity,) if identity else ())]
    result=None
    for row in rows:
        suffix=row['key'][len('background-eligible:'):]
        marker='background-granted:'+suffix
        envelope=json.loads(row['value'])
        if envelope.get('owner')!=owner:continue
        evidence=envelope['evidence']
        request_id=str(uuid.UUID(digest(owner+'\0'+marker)[:32],version=4))
        receipt=_request(training,'POST','/v1/stickers/replay-background',{'requestId':request_id,'evidence':evidence},expected_owner=owner)
        with training.lock,training._write() as connection:
            if training._ranking_profile()['user_id']!=owner:raise ServiceError(409,'账号已切换')
            connection.execute('INSERT INTO account_preferences VALUES(?,?,?) ON CONFLICT(key) DO NOTHING',(marker,json.dumps(receipt.get('backgroundReward')),iso(training._now())))
        result=receipt
    return result
