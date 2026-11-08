"""Restore reviewed first-party originals, preserving identities and old source."""
import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from statement_asset_store import references
from statement_integrity import content_complete,native_submission_supported,statement_type
from statement_quality import japanese_only
from statement_seed import checksum,load_statements

SOURCE=ROOT/'data/library'
REVIEW=ROOT/'content-updates/20261109-luogu-recovery'
PATCH=SOURCE/'statement-patches/zzzzzzzzzzzzzzzzzz-20261109-luogu-recovery.json'


def write(path,value,*,sort_keys=True):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=sort_keys)+'\n',encoding='utf8')


def revive(meta,incoming):
    if not meta.get('statementRetired'):
        assert meta.get('catalogStatementReady') is True
        return False
    assert meta.get('statementRetirementPolicy')=='public-statement-audit-v1'
    prior=meta.get('statementPriorVisibility') or {}
    for key in ('catalogHidden','catalogNotice','catalogVisibilityPolicy'):
        if key in prior:meta[key]=prior[key]
        else:meta.pop(key,None)
    for key in ('statementRetired','statementRetirementPolicy','statementRetirementReason','statementPriorVisibility'):meta.pop(key,None)
    kind=statement_type(incoming)
    meta.update(statementAvailable=True,problemType=kind,catalogStatementReady=True,
                catalogReplayReady=native_submission_supported(incoming['url']) and kind not in {'communication','output-only','attachment'})
    return True


def main(review=REVIEW,patch=PATCH,statements_only=False,register_existing=False):
    assert not (statements_only and register_existing)
    assert review.resolve().is_relative_to((ROOT/'content-updates').resolve())
    assert patch.parent.resolve()==(SOURCE/'statement-patches').resolve() and patch.suffix=='.json'
    records=json.loads((review/'records.json').read_text('utf8'))
    reviewed={r['id']:r for r in json.loads((review/'review.json').read_text('utf8'))['problems']}
    current={r['problem_id']:r['content'] for r in load_statements(SOURCE)}
    rows=json.loads((SOURCE/'problems.json').read_text('utf8'));by_id={r['id']:r for r in rows}
    assets=json.loads((SOURCE/'statement_assets.json').read_text('utf8'));known={a['sha256'] for a in assets}
    for entry in json.loads((review/'assets.json').read_text('utf8')):
        path=(SOURCE/entry['file']).resolve(strict=True)
        assert path.is_relative_to((SOURCE/'statement-assets').resolve()) and not path.is_symlink()
        data=path.read_bytes()
        assert len(data)==entry['bytes'] and hashlib.sha256(data).hexdigest()==entry['sha256']
        if entry['sha256'] not in known:assets.append(entry);known.add(entry['sha256'])
    if register_existing and not patch.exists():raise ValueError('Registration requires the already reviewed guarded statement packet')
    if patch.exists():
        packet=json.loads(patch.read_text('utf8'));assert {p['problem_id'] for p in packet['statements']}==set(reviewed)
        registered=0
        for record in records:
            saved=current[record['problem_id']]
            assert saved['integrity']['reviewedRecoveryRecordSha256']==checksum(record['content'])
            if register_existing:
                proof=reviewed[record['problem_id']]
                assert proof['originalDescriptionReviewed'] and content_complete(saved) and references(saved)<=known
                assert saved['url']==by_id[record['problem_id']]['url']==proof['url']
                registered+=revive(by_id[record['problem_id']]['encoded'],saved)
            if not statements_only:assert not by_id[record['problem_id']]['encoded'].get('statementRetired')
        if register_existing:
            write(SOURCE/'statement_assets.json',assets,sort_keys=False)
            write(SOURCE/'problems.json',rows,sort_keys=False)
            if registered or not (review/'catalog-registration.json').exists():
                write(review/'catalog-registration.json',{'registeredProblemIds':[r['problem_id'] for r in records],
                    'newlyRevived':registered,'offlineAssets':len(assets),'originalIdsPreserved':True,'privateRecordsReadOrWritten':False})
        print(json.dumps({'alreadyApplied':len(records),'originalIdsPreserved':True}));return
    patches=[]
    for record in records:
        identity=record['problem_id'];incoming=copy.deepcopy(record['content']);proof=reviewed[identity]
        assert incoming['id']==identity and incoming['url']==by_id[identity]['url']==proof['url']
        assert incoming['integrity']['markdownSha256']==proof['markdownSha256']==hashlib.sha256(incoming['markdown'].encode()).hexdigest()
        assert proof['originalDescriptionReviewed'] and content_complete(incoming) and not japanese_only(incoming['markdown'])
        assert references(incoming)<=known and len(incoming['samples'])==proof['samples']
        old=current.get(identity)
        pairs=lambda s:Counter((' '.join(x['input'].split()),' '.join(x['output'].split())) for x in (s or {}).get('samples',[]))
        assert not pairs(old)-pairs(incoming),identity+' would lose an existing sample'
        incoming['integrity']['reviewedRecoveryRecordSha256']=checksum(record['content'])
        if old:incoming['previousSourceStatement']=copy.deepcopy(old)
        patches.append({'problem_id':identity,'beforeSha256':checksum(old),'content':incoming})
        if statements_only:continue
        meta=by_id[identity]['encoded']
        revive(meta,incoming)
    assert set(reviewed)=={p['problem_id'] for p in patches}
    # Existing order keeps public SQLite page layout stable for small updates.
    if not statements_only:
        write(SOURCE/'statement_assets.json',assets,sort_keys=False)
        write(SOURCE/'problems.json',rows,sort_keys=False)
    write(patch,{'schema':1,'statements':patches})
    print(json.dumps({'restoredOriginals':len(patches),'offlineAssets':len(assets),'originalIdsPreserved':True,'personalStateRead':False,'catalogAndAssetRegistrationPending':statements_only}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review',type=Path,default=REVIEW)
    parser.add_argument('--patch-name',default=PATCH.name)
    parser.add_argument('--statements-only',action='store_true',help='Prepare guarded statements; leave catalogue and asset registration to the owning integration worktree')
    parser.add_argument('--register-existing',action='store_true',help='Verify an existing reviewed packet and register its retained IDs and canonical assets')
    args=parser.parse_args()
    main(args.review,SOURCE/'statement-patches'/args.patch_name,args.statements_only,args.register_existing)
