"""Verify three individually reviewed optional source links; no parser exemptions.

This authoring check does not alter runtime discovery or the 32 MiB resource
limit. It rejects all missing necessary resources, including images and input
archives, and accepts only the exact reviewed role/ID/URL/source combinations.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from statement_integrity import statement_type
from statement_resources import resource_references

RUNNER='https://storage.googleapis.com/coding-competitions.appspot.com/interactive_runner.py'
TESTS='https://www.ioi-jp.org/camp/2021/2021-sp-tasks/day4/event2-data.zip'
REVIEWED={
    'luogu-training-P13110':(RUNNER,'optional-generic-process-launcher','interactive'),
    'luogu-training-P13143':(RUNNER,'optional-generic-process-launcher','interactive'),
    'luogu-training-P7562':(TESTS,'optional-complete-official-test-suite','standard'),
}

def validate(value,identity):
    assert value['id']==identity
    body=value.get('currentSourceMarkdown')or value['markdown']
    source_hash=hashlib.sha256(body.encode()).hexdigest()
    entries=value.get('optionalExternalResources')or[]
    snapshots={item['sha256']:item for item in value.get('sourceSnapshots',[])}
    for digest,item in snapshots.items():
        assert hashlib.sha256(item['markdown'].encode()).hexdigest()==digest
    by_url={item['url']:item for item in entries};assert len(by_url)==len(entries)
    missing=[]
    for ref in resource_references(value):
        payload=(value.get('images')or{}).get(ref['key'])if ref['kind']=='image'else(value.get('attachments')or{}).get(ref['key'],{}).get('data')
        if payload:
            assert ref['key']not in by_url,'Optional uncached entry must not claim fabricated cached bytes'
            continue
        assert ref['kind']=='attachment','A necessary image is never optional'
        assert identity in REVIEWED,'This problem has no reviewed optional exception'
        expected,role,kind=REVIEWED[identity]
        assert ref['key']==ref['url']==expected and expected in by_url,'Unknown missing resource'
        item=by_url[expected]
        assert item['role']==role and statement_type(value)==kind
        assert item['sourceHash']==source_hash and item['sourceSnapshotHash']in snapshots
        original=snapshots[item['sourceSnapshotHash']]['markdown']
        assert expected in original
        assert item['cached']is False and item['requiredForStatement']is False and item['individuallyReviewed']is True
        assert item['sourceEvidence']['quote']in original
        assert item['sourceEvidence']['nativeProblemId']==identity.removeprefix('luogu-training-')
        if role=='optional-generic-process-launcher':
            assert item['availability']['httpStatus']==403 and item['availability']['fileRecovered']is False
            assert value['sampleInventory']['kind']=='inline-interaction-without-standalone-sample-pairs'
            assert value['sampleInventory']['fullInteractionIncluded']is True and not value['samples']
            assert any('local_testing_tool.py'in url and entry.get('data')for url,entry in value['attachments'].items())
        else:
            assert item['availability']['httpStatus']==200
            assert item['availability']['contentLength']==99667903
            assert item['availability']['inlineResourceLimitBytes']==32*1024*1024
            assert item['availability']['contentLength']>item['availability']['inlineResourceLimitBytes']
            assert len(value['samples'])==4,'All native/official examples remain necessary'
            for suffix in ['event2.pdf','2021-sp-d4-notice.pdf']:
                assert any(url.endswith(suffix)and entry.get('data')for url,entry in value['attachments'].items())
        missing.append(expected)
    assert set(missing)==set(by_url),'Optional evidence must correspond to actual retained source links'
    return missing

if __name__=='__main__':
    records=json.loads(Path(sys.argv[1]).read_text('utf8'))
    reviewed=[{'id':r['problem_id'],'optionalExternalResources':validate(r['content'],r['problem_id'])}for r in records]
    print(json.dumps({'reviewed':reviewed,'necessaryResourcesExempted':0},ensure_ascii=False))
