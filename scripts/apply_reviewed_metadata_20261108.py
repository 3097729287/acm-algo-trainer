"""Apply three frozen, explicitly unofficial AtCoder model observations."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/common')]
from cf_eq import cf_eq_atcoder


def apply():
    review = json.loads((ROOT / 'content-updates/20261108-metadata/atcoder-models.json').read_text('utf8'))
    public_path = ROOT / 'backend/resources/public-problem-metadata.json'
    problems_path = ROOT / 'data/library/problems.json'
    public = json.loads(public_path.read_text('utf8'))
    problems = json.loads(problems_path.read_text('utf8'))
    updated = []
    for task in ('abc396_e', 'abc292_h', 'arc100_c'):
        native = review['selected'][task]
        assert native['is_experimental'] is False
        assert isinstance(native['difficulty'], int) and not isinstance(native['difficulty'], bool)
        url = f'https://atcoder.jp/contests/{task.split("_")[0]}/tasks/{task}'
        evaluation = cf_eq_atcoder(native['difficulty'])
        patch = {'difficulty': evaluation['cf_eq_rating'], 'difficultySource': 'CF-EQ · AtCoder Problems 模型估算',
                 'difficultyEstimated': True, 'difficultyConfidence': 'MEDIUM',
                 'difficultyBand': evaluation['cf_eq_band'], 'nativeDifficulty': native['difficulty'],
                 'difficultyCheckedAt': review['retrievedAt'], 'metadataVersion': '1.6.6',
                 'difficultyEvidence': [review['source'], review['documentation'], url,
                     'AtCoder Problems 非官方统计模型；不是 AtCoder 官方评级。',
                     '原始数据 SHA-256: ' + review['sha256'], *evaluation['difficulty_evidence']]}
        matches = [p for p in problems if p['url'] == url]
        assert len(matches) == 1, (task, len(matches))
        encoded = matches[0]['encoded']
        assert encoded.get('difficulty') is None or all(encoded.get(k) == v for k, v in patch.items()), task
        assert url not in public or all(public[url].get(k) == v for k, v in patch.items()), task
        public.setdefault(url, {}).update(patch)
        encoded.update(patch)
        updated.append({'id': matches[0]['id'], 'url': url, **patch})
    for path, data in ((public_path, public), (problems_path, problems)):
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    return updated


if __name__ == '__main__':
    print(json.dumps({'updated': apply()}, ensure_ascii=False))
