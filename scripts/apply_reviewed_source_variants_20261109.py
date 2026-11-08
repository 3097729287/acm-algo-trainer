"""Apply the four individually reviewed source variants; catalogue stays owned
by the integration worktree. Automatic parser title/size rules stay unchanged.
"""
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from statement_asset_store import references
from statement_integrity import content_complete,statement_type
from statement_seed import load_statements,checksum
from translation import bundled_translation
from verify_reviewed_optional_resources_20261109 import validate

REVIEW=ROOT/'content-updates/20261109-reviewed-source-variants'
PATCH=ROOT/'data/library/statement-patches'/('z'*31+'-20261109-reviewed-source-variants.json')
GOOGLE={'luogu-training-P13110','luogu-training-P13143'}
EXPECTED=GOOGLE|{'luogu-training-P7562','remote:codeforces:105977::J'}

def main():
    records=json.loads((REVIEW/'records.json').read_text('utf8'))
    proofs={r['id']:r for r in json.loads((REVIEW/'review.json').read_text('utf8'))['problems']}
    assert {r['problem_id']for r in records}==set(proofs)==EXPECTED
    current={r['problem_id']:r['content']for r in load_statements(ROOT/'data/library')}
    assets=json.loads((ROOT/'data/library/statement_assets.json').read_text('utf8'))
    assets+=json.loads((REVIEW/'assets.json').read_text('utf8'))
    known={r['sha256']for r in assets}
    for entry in json.loads((REVIEW/'assets.json').read_text('utf8')):
        p=(ROOT/'data/library'/entry['file']).resolve(strict=True)
        assert p.is_relative_to((ROOT/'data/library/statement-assets').resolve())and not p.is_symlink()
        raw=p.read_bytes();assert len(raw)==entry['bytes']and hashlib.sha256(raw).hexdigest()==entry['sha256']
    if PATCH.exists():
        for r in records:
            value=current[r['problem_id']]
            assert value['integrity']['reviewedRecoveryRecordSha256']==checksum(r['content'])
            validate(value,r['problem_id'])
        print(json.dumps({'alreadyApplied':len(records)}));return
    result=[]
    for r in records:
        pid=r['problem_id'];value=copy.deepcopy(r['content']);proof=proofs[pid];old=current.get(pid)
        assert value['id']==pid and value['url']==proof['url']
        assert value['integrity']['markdownSha256']==proof['markdownSha256']==hashlib.sha256(value['markdown'].encode()).hexdigest()
        assert proof['originalDescriptionReviewed']and content_complete(value)
        assert references(value)<=known
        validate(value,pid)
        pairs=lambda v:Counter((s['input'],s['output'])for s in (v or{}).get('samples',[]))
        missing=pairs(old)-pairs(value)
        if missing:
            assert pid in GOOGLE and set(missing)=={('','')},'A real previous sample may not disappear'
            assert statement_type(value)=='interactive'and not value['samples']
            assert value['sampleInventory']['fullInteractionIncluded']is True
            assert any(h['kind']=='native-empty-interactive-placeholder'and h['samples']==old['samples']for h in value['sampleExtractionHistory'])
        if pid in GOOGLE:assert bundled_translation(value)
        if pid=='remote:codeforces:105977::J':
            alias=value['manualSourceAliasReview'];assert alias==proof['binding']
            assert alias['contestId']==105977 and alias['letter']=='J'and alias['originalId']==pid
            assert alias['officialStatement']['pages']==[18,19]and alias['officialTutorial']['pages']==[12]
            assert alias['automaticTitleMatchingChanged']is False
            assert value['statementPdf']['sourceSha256']==alias['officialStatement']['sha256']
            assert value['samples'][0]['input']==alias['sampleBinding']['input']and value['samples'][0]['output']==alias['sampleBinding']['output']
        value['integrity']['reviewedRecoveryRecordSha256']=checksum(r['content'])
        if old:value['previousSourceStatement']=copy.deepcopy(old)
        result.append({'problem_id':pid,'beforeSha256':checksum(old),'content':value})
    PATCH.write_text(json.dumps({'schema':1,'statements':result},ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'restoredOriginals':len(result),'chineseTranslations':2,'reviewedOptionalLinks':3,'globalParserRulesChanged':False,'catalogueAndGlobalAssetRegistrationPending':True}))

if __name__=='__main__':main()
