"""Normalize display ratings and make unresolved knowledge explicit, retaining evidence."""
from pathlib import Path
import copy
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/common')]
from difficulty import round_difficulty


def main():
    path = ROOT / 'data/library/problems.json'
    rows = json.loads(path.read_text('utf8'))
    before = copy.deepcopy(rows)
    ledger=json.loads((ROOT/'data/nowcoder-editorials/reviewed.json').read_text('utf8'))
    rounded = []
    pending = []
    editions=[]
    for row in rows:
        original = row['encoded']
        value = round_difficulty(original)
        if value.get('difficulty') != original.get('difficulty'):
            assert value['difficultyBeforeRounding'] == original['difficulty']
            assert all(value.get(k) == original.get(k) for k in (
                'difficultySource', 'difficultyEstimated', 'difficultyEvidence', 'nativeDifficulty', 'difficultyBand'))
            row['raw']['难度'] = str(value['difficulty'])
            rounded.append(row['id'])
        if not value.get('tags') and not value.get('knowledgeCategories') and not value.get('knowledgeReviewRequired'):
            value['knowledgeReviewRequired'] = True
            pending.append(row['id'])
        if row['id'] in ledger:
            variants=list(ledger[row['id']]['articles'])
            assert 'default' in variants and set(variants)<={'default','detailed'}
            assert value['solutionAvailable'] and value['detailedSolutionAvailable']==('detailed' in variants)
            if value.get('editorialVariants')!=variants:
                value['editorialVariants']=variants;editions.append(row['id'])
        row['encoded'] = value
    assert [row['id'] for row in before] == [row['id'] for row in rows]
    for old, new in zip(before, rows):
        assert all(old.get(k) == new.get(k) for k in ('id', 'url'))
        assert old['raw']['状态'] == new['raw']['状态'] == '未做'
        assert old['raw']['日期'] == new['raw']['日期'] == ''
        assert old['encoded'].get('knowledgeAnalysis') == new['encoded'].get('knowledgeAnalysis')
    if rows != before:
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf8')
    print(json.dumps({'problems': len(rows), 'normalizedDisplayRatings': len(rounded),
                      'pendingKnowledgeFlagsCorrected': len(pending), 'originalEvidenceRetained': True,
                      'editorialEditionsDeclared':len(editions),
                      'afterSha256': hashlib.sha256(path.read_bytes()).hexdigest()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
