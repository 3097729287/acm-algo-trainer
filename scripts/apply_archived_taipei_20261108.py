"""Import exact Gym identities from a verified archived original PDF.

Authoring only: requires complete native-render and page-reviewed sample records.
The default packet is the thirteen-problem Taipei booklet. A separately reviewed
packet may restore a smaller missing set. No private account data is accessed.
"""
import argparse
import copy
import datetime
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from codeforces_pdf import normalized
from statement_asset_store import dehydrate
from statement_integrity import annotate_type,content_complete
from statement_seed import checksum,load_statements


def read(path):return json.loads(path.read_text('utf8'))
def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')


def main(stage,review_path=None):
    source=ROOT/'data/library';author=review_path.parent if review_path else ROOT/'content-updates/20261108-taipei'
    review=read(review_path or author/'review.json')
    packet_name=review.get('packetName','zzzzzzzzzzzz-20261108-taipei-originals.json')
    assert re.fullmatch(r'z+-[A-Za-z0-9-]+\.json',packet_name)
    target=source/'statement-patches'/packet_name
    statements={r['problem_id']:r['content'] for r in load_statements(source)}
    if target.exists():
        for patch in read(target)['statements']:assert statements[patch['problem_id']]==patch['content']
        print('Existing archived-originals packet verified; no files changed.')
        return
    booklet_sha=review.get('bookletSha256',review.get('sourcePdfSha256'))
    assert booklet_sha==hashlib.sha256((stage/'original.pdf').read_bytes()).hexdigest()
    rendered=read(stage/'native-render-result.json');assert rendered['externalRequests']==0
    actual={r['id']:r for r in rendered['verified']}
    problems=read(source/'problems.json');by_id={r['id']:r for r in problems}
    assets={r['sha256']:r for r in read(source/'statement_assets.json')}
    parts=read(source/'statement_asset_parts.json');new_assets={};patches=[];proofs=[]
    def save(sha,mime,data):
        assert hashlib.sha256(data).hexdigest()==sha
        if sha in assets:assert assets[sha]['bytes']==len(data)
        elif sha in new_assets:assert new_assets[sha]==(mime,data)
        else:new_assets[sha]=(mime,data)
    for item in review['problems']:
        identity=item['id'];letter=identity.rsplit('::',1)[1];record=by_id[identity]
        value=read(stage/(letter+'.json'));before=statements.get(identity)
        value['statementSource']=review.get('statementSource',value.get('statementSource'))
        pdf=value['statementPdf'];observed=actual[identity]
        assert value['id']==identity and value['url']==record['url']
        assert normalized(value['title'])==normalized(record['encoded']['title'])
        assert pdf['sha256']==item['pdfSha256']==observed['sha256']
        assert pdf['pageCount']==observed['pages']==len(item['sourcePages'])
        assert item['samplesSha256']==checksum(value['samples'])
        assert all(page in item['samplePagesReviewed'] for page in item['samplePages'])
        assert item['numberedSamples']==len(value['samples'])
        # Reconcile the complete, reviewed samples instead of accepting the
        # automatic partial code/table extraction as the entire inventory.
        sample_record=read(author/(letter+'.samples.json'))
        assert sample_record['samples']==value['samples']
        assert sample_record['sourcePdfSha256']==pdf['sha256']
        value['sampleExtraction']=sample_record
        value['localJudgeSupported']=True
        assert (value.get('integrity') or {}).get('sourceVerified') is True,'Finalize and verify all original resources before applying the packet'
        value['integrity'].update(sampleCount=len(value['samples']),corpusAuditVerifiedSha256=hashlib.sha256(value['markdown'].encode()).hexdigest())
        value['sourcePdfSha256']=booklet_sha
        value['translationAvailable']=False
        value['translationUnavailableReason']='等待逐页核对原始 PDF 的文字与公式；完整英文 PDF 可正常阅读'
        if before:value.setdefault('previousStatementSnapshots',[]).append({'sha256':checksum(before),'content':copy.deepcopy(before)})
        value=annotate_type(value);assert content_complete(value)
        proof={'id':identity,'nativeRosterUrl':review['nativeRosterUrl'],'sourceArchiveUrl':review['sourceArchiveUrl'],
            'sourcePdfSha256':booklet_sha,'pdfSha256':pdf['sha256'],'sourcePages':item['sourcePages'],
            'completeRosterTitlesVerified':13,'samplePairs':len(value['samples']),'samplesSha256':item['samplesSha256'],
            'samplePagesReviewed':item['samplePagesReviewed'],'allPagesRendered':True}
        value['nativeSourceReview']=proof;proofs.append(proof)
        encoded=record['encoded']
        assert encoded.get('statementRetirementPolicy')=='public-statement-audit-v1',identity
        previous=encoded.get('statementPriorVisibility') or {}
        for key in ('catalogHidden','catalogNotice','catalogVisibilityPolicy'):
            if key in previous:encoded[key]=previous[key]
            else:encoded.pop(key,None)
        for key in ('statementRetired','statementRetirementPolicy','statementRetirementReason','statementPriorVisibility'):encoded.pop(key,None)
        encoded.update(problemType=value['problemType'],catalogStatementReady=True,catalogReplayReady=True)
        reviewed_tags=item.get('reviewedTags',[])
        if reviewed_tags:
            assert all(isinstance(tag,str) and 0<len(tag)<=40 for tag in reviewed_tags)
            encoded['tags']=list(dict.fromkeys([*(encoded.get('tags') or []),*reviewed_tags]))
            encoded['knowledgeReview']={'method':'reviewed-statement-structure','official':False,
                'sourceUrl':review['sourceArchiveUrl'],'sourcePdfSha256':pdf['sha256'],
                'reason':item['knowledgeReason'],'reviewedTags':reviewed_tags}
        patches.append({'problem_id':identity,'beforeSha256':checksum(before),'content':dehydrate(value,save)})
    assert len(patches)==review.get('expectedRestoredProblems',13)
    number=max(int(re.search(r'part-(\d+)',p['file'])[1]) for p in parts)+1
    name=f'statement-assets/part-{number:04d}.bin';destination=source/name
    assert not destination.exists();blob=bytearray()
    for sha,(mime,data) in sorted(new_assets.items()):
        assets[sha]={'sha256':sha,'mime':mime,'bytes':len(data),'file':name,'offset':len(blob)};blob.extend(data)
    assert len(blob)<24*1024*1024
    destination.write_bytes(blob);parts.append({'file':name,'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()})
    dump(source/'statement_assets.json',list(assets.values()));dump(source/'statement_asset_parts.json',parts)
    dump(source/'problems.json',problems);dump(target,{'schema':1,'statements':patches})
    result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'restoredOriginals':len(patches),'newIdentities':0,
        'nativePdfPagesRendered':sum(v['pages'] for v in actual.values()),'newResources':len(new_assets),'newResourceBytes':len(blob),
        'privateDatabasesRead':False,'installed':False,'productionDeployed':False,'translationComplete':False,'problems':proofs}
    verification_name=review.get('verificationName','taipei-originals-20261108.json')
    assert re.fullmatch(r'[A-Za-z0-9-]+\.json',verification_name)
    dump(ROOT/'docs/verification'/verification_name,result)
    print(json.dumps({k:v for k,v in result.items() if k!='problems'},ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--stage',type=Path,required=True)
    parser.add_argument('--review',type=Path,help='A separately reviewed archived-originals packet; the Taipei packet remains the default.')
    args=parser.parse_args();main(args.stage.resolve(strict=True),args.review.resolve(strict=True) if args.review else None)
