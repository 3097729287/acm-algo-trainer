"""Apply exact native tags and explicitly unofficial, source-reviewed estimates.

The input packet records original source hashes, tag IDs, editorial pages and
previous values. No statement, account, draft or submission is read or changed.
"""
import argparse
import copy
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from knowledge import enrich_row,normalize_tags,public_knowledge
from statement_seed import checksum
from apply_reviewed_knowledge_20261108 import main as apply_editorials

REVIEW=ROOT/'content-updates/20261109-reviewed-metadata-followup'

def read(path):return json.loads(path.read_text('utf8'))
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main(review=REVIEW):
    assert review.resolve().is_relative_to((ROOT/'content-updates').resolve())
    plan=read(review/'review.json');revision=plan['revision']
    source=ROOT/'data/library/problems.json';rows=read(source);before=copy.deepcopy(rows)
    byid={r['id']:r for r in rows};path=ROOT/'backend/resources/public-knowledge.json';public=read(path)
    known={a['sha256'] for a in read(ROOT/'data/library/statement_assets.json')}
    for item in plan['items']:
        assert all(s['sha256'] in known for s in item['sources'])
    native=[]
    for item in plan['luoguNativeReviews']:
        row=byid[item['id']];value=row['encoded']
        assert row['url']==item['url'] and item['nativeProblemId']==item['url'].rsplit('/',1)[-1]
        assert normalize_tags(item['nativeTags'],official=True)['tags']==item['normalizedTags']
        if value.get('knowledgeSourceReview',{}).get('revision')==revision:continue
        assert checksum(row)==item['beforeProblemSha256'] and not value.get('tags'),item['id']
        public.setdefault('problems',{})[row['url']]={
            'tags':item['nativeTags'],'source':row['url'],'sourceSha256':item['sourceSha256'],
            'nativeProblemId':item['nativeProblemId'],'nativeTagIds':item['nativeTagIds'],
            'tagDictionarySha256':item['tagDictionary']['sha256'],'checkedAt':plan['checkedAt'],
            'reason':'已核对原站题目ID及公开标签词典，按精确标签映射；只声明分类，不声明完整解法已验收或原站通过。'}
        native.append(item)
    if native:write(path,public);public_knowledge.cache_clear()
    for item in native:
        row=byid[item['id']];value=enrich_row(row['encoded'])
        assert set(item['normalizedTags'])<=set(value['tags'])
        value['knowledgeReviewRequired']=False
        value['knowledgeSourceReview']={'revision':revision,'source':item['url'],'sourceSha256':item['sourceSha256'],
            'nativeTagIds':item['nativeTagIds'],'tagDictionarySha256':item['tagDictionary']['sha256'],
            'method':'native-public-tags-exact-canonical-mapping','algorithmVerified':False}
        row['encoded']=value;row['raw']['知识点']=value['knowledge']
    if native:write(source,rows)
    apply_editorials(review)
    rows=read(source);byid={r['id']:r for r in rows};rated=[]
    public_path=ROOT/'backend/resources/public-problem-metadata.json';metadata=read(public_path)
    for item in plan['difficultyEstimates']:
        assert item['official'] is False and item['difficulty']%100==0
        assert len(item['difficultyBand'])==2 and item['difficultyBand'][0]<=item['difficulty']<=item['difficultyBand'][1]
        confidence=item.get('confidence','MEDIUM');assert confidence in {'LOW','MEDIUM'}
        topic=next(topic for topic in plan['items'] if topic['id']==item['id'])
        assert any(s['reference']==item['source'] and s['sha256']==item['sourceSha256'] for s in topic['sources'])
        row=byid[item['id']];value=row['encoded']
        if value.get('difficultyReviewRevision')==revision:
            assert value['difficulty']==item['difficulty'] and value['difficultyEstimated'] is True
            continue
        assert row['url']==item['url'] and value.get('difficulty') is None and item['official'] is False
        patch={'difficulty':item['difficulty'],'difficultyBand':item['difficultyBand'],
            'difficultySource':'ToBe 官方题解与算法复核估算（非官方评级）',
            'difficultyEstimated':True,'difficultyConfidence':confidence,'difficultyCheckedAt':plan['checkedAt'],
            'difficultyReviewRevision':revision,'difficultyEvidence':[item['source'],
                '原始题解资料 SHA-256: '+item['sourceSha256'],item['reason'],
                '按常规算法的推导与实现复杂度给出的训练参考区间；不是 Codeforces 官方 rating，也不按团队通过率换算。']}
        value.update(patch);row['raw']['难度']=str(item['difficulty']);metadata.setdefault(row['url'],{}).update(patch);rated.append(item['id'])
    if rated:write(source,rows);write(public_path,metadata)
    assert [r['id'] for r in rows]==[r['id'] for r in before]
    for a,b in zip(before,rows):
        assert a['url']==b['url']
        for key in ['状态','日期']:assert a['raw'].get(key)==b['raw'].get(key)
        for key in ['status','date','nativeDifficulty']:assert a['encoded'].get(key)==b['encoded'].get(key)
    result={'revision':revision,'nativeTagReviews':len(plan['luoguNativeReviews']),
        'editorialTopicReviews':len(plan['items']),'explicitUnofficialEstimates':len(plan['difficultyEstimates']),
        'newNativeTagsApplied':len(native),'newEstimatesApplied':len(rated),'privateRecordsReadOrWritten':False,
        'existingOfficialRatingsPreserved':True}
    if native or rated or not (review/'metadata-applied.json').exists():write(review/'metadata-applied.json',result)
    print(json.dumps(result))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review',type=Path,default=REVIEW)
    args=parser.parse_args()
    main(args.review)
