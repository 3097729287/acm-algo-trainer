"""Verify an installed, reviewed input route and its durable offline cache.

The origin remains restricted by the production client. This command cannot
register URLs, upload files, alter a catalogue or declare a retired task ready.
Only binary blocks and small verification receipts cross process boundaries.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from required_downloads import RequiredDownloads


def verify(cache_root,*,origin=None,sha256=None,manifest_path=None):
    manager=RequiredDownloads(cache_root=cache_root,origin=origin,manifest_path=manifest_path)
    selected=[manager.descriptor(sha256)]if sha256 else list(manager.items.values())
    if not selected:raise ValueError('No reviewed required input archives are registered')
    started=time.monotonic();results=[]
    for item in selected:
        sha=item['sha256'];h=hashlib.sha256();count=0
        before=manager.status(sha)
        if before['cached']or before['verifiedBytes']==item['bytes']:
            raise ValueError('Choose a new/incomplete cache so this check must contact the distribution origin')
        for block in manager.blocks(sha):h.update(block);count+=len(block)
        if count!=item['bytes']or h.hexdigest()!=sha:raise ValueError('Required input response checksum mismatch')
        after=manager.status(sha)
        if not after['cached']or after['verifiedBytes']!=count:raise ValueError('Required input cache was not durably completed')
        offline=hashlib.sha256();offline_count=0;previous=os.environ.get('TB_OFFLINE')
        try:
            os.environ['TB_OFFLINE']='1'
            for block in manager.blocks(sha):offline.update(block);offline_count+=len(block)
        finally:
            if previous is None:os.environ.pop('TB_OFFLINE',None)
            else:os.environ['TB_OFFLINE']=previous
        if offline_count!=count or offline.hexdigest()!=sha:raise ValueError('Required input offline cache verification failed')
        results.append({'problemId':item['problemId'],'sha256':sha,'bytes':count,
            'route':manager.origin+'/updates/required-downloads/'+sha+'.zip',
            'cacheWasAlreadyComplete':before['cached'],'verifiedPrefixBeforeBytes':before['verifiedBytes'],
            'completeResponseAndDurableCacheVerified':True,'networkDisabledOfflineReplayVerified':True})
    return {'schema':1,'checkedAtUtc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        'origin':manager.origin,'seconds':round(time.monotonic()-started,3),'archives':results,
        'catalogueRetirementChanged':False,'ordinary32MiBLimitUnchanged':True,'privateAccountStateReadOrWritten':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin',help='Production trusted origin; loopback HTTP is accepted for isolated fixtures only')
    parser.add_argument('--cache-root',type=Path,required=True,help='Explicit isolated/durable cache directory')
    parser.add_argument('--sha256',help='One existing reviewed manifest SHA; never an arbitrary URL')
    parser.add_argument('--output',type=Path,required=True,help='New small JSON receipt, never archive data')
    args=parser.parse_args()
    if args.output.exists():parser.error('Choose a new receipt path')
    result=verify(args.cache_root,origin=args.origin,sha256=args.sha256)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf8',newline='\n')as out:out.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'archives':len(result['archives']),'bytes':sum(item['bytes']for item in result['archives']),
        'offlineCacheVerified':True,'catalogueRetirementChanged':False}))
