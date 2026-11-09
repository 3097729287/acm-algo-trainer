"""Test-only old Python policy oracle; all owners/receipts are synthetic."""
from pathlib import Path
import copy
import hashlib
import json
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'backend'))
import experience_challenge as exp
import starter_pacing as starter

OWNER = 'synthetic-owner-a'
SID = 'submission-' + 'a'*32


def fixtures():
    empty = exp._empty(OWNER)
    seen = dict(empty, seenVersion=1)
    beginner = dict(seen, choice='beginner')
    assignment = dict(seen, choice='experienced',problemId=exp.PROBLEMS[0],
        challengeId='00000000-0000-4000-8000-000000000001',
        startedAt='2026-11-09T00:00:00Z',attempts=[SID])
    passed = dict(assignment,passedAt='2026-11-09T00:01:00Z',submissionId=SID,awardedXp=350)
    other = dict(assignment,challengeId='00000000-0000-4000-8000-000000000002',
        startedAt='2026-11-10T00:00:00Z',attempts=['submission-'+'b'*32])
    other_passed = dict(other,passedAt='2026-11-10T00:01:00Z',submissionId=other['attempts'][0],awardedXp=100)
    values = [None, {}, empty,seen,beginner,assignment,passed,other,other_passed,
        dict(passed,awardedXp=0),dict(passed,awardedXp=None),dict(passed,owner='synthetic-owner-b'),dict(empty,owner='')]
    for key in empty:
        v=copy.deepcopy(passed);v.pop(key);values.append(v)
    for key, items in {
        'policyVersion':[True,False,1.0,2,None,'1'],
        'seenVersion':[True,False,1.0,2,None,'1'],
        'choice':['forged',True,{},None,'beginner'],
        'problemId':[exp.PROBLEMS[1],'unreviewed',None],
        'challengeId':['invalid',None,'00000000000040008000000000000001','{00000000-0000-4000-8000-000000000001}','urn:uuid:00000000-0000-4000-8000-000000000001'],
        'attempts':[[SID]*128,[SID]*129,[],[1],['submission-'+'A'*32]],
        'passedAt':['',None,False,0,[],{},'not-checked-as-a-time'],
        'submissionId':['submission-'+'f'*32,None],
        'awardedXp':[-1,501,True,1.0,'100'],
    }.items():
        for item in items:
            v=copy.deepcopy(passed);v[key]=item;values.append(v)
    # Falsy historical passedAt is readable but cannot grant XP.
    values.extend(dict(assignment,passedAt=v) for v in (False,0,[],{}))
    validations=[dict(value=v,owner=owner,expected=exp.validate(v,owner)) for v in values
        for owner in (None,OWNER,'synthetic-owner-b')]
    merges=[dict(left=a,right=b,expected=exp.merge(a,b)) for a in values[:13] for b in values[:13]]
    starts=[None,{}]
    for stamp in ['2026-11-09T00:00:00Z','2026-11-09T08:00:00+08:00',
        '2026-11-09T00:00:00','2026-11-09','20261109','2026-W46-1','2026-11-09T00:00',
        '2026-11-09X00:00:00','2026-11-09T23:59:60Z','0000-11-09T00:00:00Z','2026-11-09T00:00:00z','bad',None,0]:
        starts.append(dict(version=1,owner=OWNER,selectedAt=stamp))
    starts += [dict(version=True,owner=OWNER,selectedAt='2026-11-09'),
        dict(version=1.0,owner=OWNER,selectedAt='2026-11-09'),
        dict(version=1,owner='',selectedAt='2026-11-09'),
        dict(version=1,owner='synthetic-owner-b',selectedAt='2026-11-09'),
        dict(version=1,owner=OWNER,selectedAt='2026-11-09',extra=True)]
    starter_validations=[dict(value=v,owner=owner,expected=starter.validate(v,owner)) for v in starts for owner in (None,OWNER,'synthetic-owner-b')]
    starter_merges=[dict(left=a,right=b,expected=starter.merge(a,b)) for a in starts for b in starts]
    receipts=[]
    for version in [1,True,1.0,2]:
        for amount in [0,1500,1501,-1,True,1.0,'10']:
            v=dict(version=version,owner=OWNER,xp=amount,awardedAt='')
            receipts.append(v)
    receipts += [None,{},dict(version=1,owner='synthetic-owner-b',xp=10,awardedAt='2026-11-09'),
        dict(version=1,owner=OWNER,xp=10,awardedAt='2026-11-09',retained='metadata')]
    receipts += [json.dumps(v) for v in receipts.copy()]+['{bad']
    six=[dict(value=v,owner=OWNER,expected=exp.six_receipt(v,OWNER)) for v in receipts]
    return dict(experienceValidations=validations,experienceMerges=merges,
        starterValidations=starter_validations,starterMerges=starter_merges,sixReceipts=six,
        sources={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
            for name in ['backend/experience_challenge.py','backend/starter_pacing.py','backend/tb_rank.py']})


if __name__=='__main__':
    print(json.dumps(fixtures(),ensure_ascii=False,separators=(',',':')))
