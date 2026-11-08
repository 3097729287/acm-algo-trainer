"""Normalize explicitly reviewed algorithm names; never infer from titles."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from knowledge import enrich_row,normalize_tags
from nowcoder_content import TOPIC_ALIASES,TOPICS


def main():
    source=ROOT/'data/library/problems.json';rows=json.loads(source.read_text('utf8'))
    ledger=json.loads((ROOT/'data/nowcoder-editorials/reviewed.json').read_text('utf8'))
    assert not normalize_tags([tag for tags in TOPIC_ALIASES.values() for tag in tags])['unknown']
    changed=[]
    for row in rows:
        identity=row['id'];before=row['encoded']
        if identity not in ledger or before.get('tags') or before.get('knowledgeCategories'):continue
        proof=ledger[identity]
        assert before.get('editorialTopics')==proof['knowledge']
        tags=list(dict.fromkeys(tag for x in proof['knowledge'] if x.strip()
                               for tag in TOPIC_ALIASES.get(x,[TOPICS.get(x,x)])))
        normalized=normalize_tags(tags)
        if not normalized['tags'] and not normalized['categories']:continue
        path=(ROOT/proof['articles']['default']).resolve(strict=True)
        assert path.is_relative_to((ROOT/'data/nowcoder-editorials').resolve())
        value=enrich_row(before,algorithm_evidence={'source':proof['articles']['default'],'tags':tags,'verified':True})
        assert value['tags'] or value['knowledgeCategories']
        value['knowledgeReviewRequired']=False
        value['knowledgeEditorialSha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        assert all(value.get(k)==before.get(k) for k in ('difficulty','difficultySource','difficultyEstimated','difficultyEvidence','url','editorialTopics'))
        row['encoded']=value;row['raw']['知识点']=value['knowledge']
        assert row['raw']['状态']=='未做' and row['raw']['日期']==''
        changed.append({'id':identity,'originalReviewedTopics':proof['knowledge'],'tags':value['tags'],
                        'source':proof['articles']['default'],'sourceSha256':value['knowledgeEditorialSha256']})
    if changed:source.write_text(json.dumps(rows,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print(json.dumps({'normalizedReviewedAlgorithms':len(changed),'usesTitleGuessing':False,'changes':changed},ensure_ascii=False))


if __name__=='__main__':main()
