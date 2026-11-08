"""Apply exact-identity topic reviews without inventing official tags or results."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from knowledge import canonical_tag,enrich_row
from statement_seed import checksum

def read(path):return json.loads(path.read_text(encoding='utf-8'))
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def key(url):
    parts=urlsplit(url)
    assert parts.scheme=='https' and not parts.username and not parts.password and not parts.query and not parts.fragment
    return (parts.hostname or '').removeprefix('www.').lower()+parts.path.rstrip('/')

def main(folder=None):
    folder=folder or ROOT/'content-updates/20261108-knowledge-followup'
    assert folder.resolve().is_relative_to((ROOT/'content-updates').resolve())
    plan=read(folder/'review.json');source=ROOT/'data/library/problems.json'
    resource=ROOT/'backend/resources/knowledge_topic_review.json'
    rows=read(source);by_id={row['id']:row for row in rows};curation=read(resource)
    if plan['revision'] in curation.get('appliedPackets',[]):
        for item in plan['items']:
            row=by_id[item['id']]
            assert row['encoded'].get('knowledgeReview',{}).get('revision')==plan['revision']
            assert set(item['tags'])<=set(row['encoded']['tags'])
        print(json.dumps({'newReviews':0,'verifiedReviews':len(plan['items'])}));return
    before_resource=resource.read_bytes()
    assert hashlib.sha256(before_resource).hexdigest()==plan['resourceBeforeSha256'],'Topic curation changed; review the new base first'
    assets={entry['sha256'] for entry in read(ROOT/'data/library/statement_assets.json')}
    for item in plan['items']:
        assert checksum(by_id[item['id']])==item['beforeProblemSha256'],'Problem metadata changed: '+item['id']
        assert item['tags'] and all(canonical_tag(tag)==tag for tag in item['tags'])
        for evidence in item['sources']:
            reference=evidence['reference']
            if reference.startswith('https://'):
                assert evidence['sha256'] in assets
            else:
                path=(ROOT/reference).resolve(strict=True)
                assert path.is_relative_to(ROOT/'data/core7-completion') and path.suffix=='.md'
                assert hashlib.sha256(path.read_bytes()).hexdigest()==evidence['sha256']
        for url in item['urls']:
            name=key(url)
            previous=curation['problems'].get(name,{})
            entry=copy.deepcopy(previous)
            entry.update(problemIds=list(dict.fromkeys([*previous.get('problemIds',[]),item['id']])),url=url,
                tags=list(dict.fromkeys([*previous.get('tags',[]),*item['tags']])),
                removeTags=previous.get('removeTags',[]),
                sources=[*previous.get('sources',[]),*item['sources']],
                reviewMethod='source-reviewed-classification',official=False)
            curation['problems'][name]=entry
    curation['reviewedProblems']=len(curation['problems'])
    curation.setdefault('appliedPackets',[]).append(plan['revision'])
    dump(resource,curation)
    results=[]
    try:
        for item in plan['items']:
            row=by_id[item['id']];previous=copy.deepcopy(row['encoded'])
            encoded=enrich_row(previous)
            assert encoded['knowledgeAnalysis']['status']=='classified'
            assert set(item['tags'])<=set(encoded['tags'])
            encoded['knowledgeReviewRequired']=False
            encoded['knowledgeReview']={**previous.get('knowledgeReview',{}),'revision':plan['revision'],
                'official':False,'tags':item['tags'],'sources':item['sources']}
            row['encoded']=encoded
            row['raw']['知识点']=encoded['knowledge']
            assert (encoded.get('id'),encoded.get('url'),encoded.get('status'),encoded.get('date'))==(previous.get('id'),previous.get('url'),previous.get('status'),previous.get('date'))
            results.append({'id':item['id'],'tags':encoded['tags'],'status':encoded['knowledgeAnalysis']['status'],
                            'source':encoded['knowledgeAnalysis']['source'],'official':False})
        dump(source,rows)
    except BaseException:
        resource.write_bytes(before_resource)
        raise
    dump(folder/'applied.json',{'revision':plan['revision'],'problems':results,'privateStateReadOrWritten':False})
    print(json.dumps({'newReviews':len(results),'reviewedUrlEntries':curation['reviewedProblems'],'privateStateReadOrWritten':False}))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review',type=Path)
    args=parser.parse_args()
    main(args.review)
