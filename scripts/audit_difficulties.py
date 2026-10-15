"""Recheck every bundled task against public difficulty evidence.

Read-only HTTP requests, resumable public cache, no personal state. Output is
reviewable JSON; --apply updates text seed and the public metadata overlay.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/common')]
import cf_eq
from difficulty import nowcoder, unknown, VERSION


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    checked = dt.datetime.now(dt.timezone.utc).isoformat()
    problems_path = ROOT / 'data/library/problems.json'
    problems = json.loads(problems_path.read_text('utf8'))
    metadata_path = ROOT / 'backend/resources/public-problem-metadata.json'
    metadata = json.loads(metadata_path.read_text('utf8'))

    def get(url, headers=None):
        path = args.cache / (hashlib.sha256(url.encode()).hexdigest() + '.json')
        if path.exists():
            return json.loads(path.read_text('utf8'))
        for attempt in range(2):
            try:
                request = Request(url, headers={'User-Agent': 'Mozilla/5.0 TB public difficulty audit', **(headers or {})})
                with urlopen(request, timeout=18) as response:
                    data = json.load(response)
                path.write_text(json.dumps(data, ensure_ascii=False), 'utf8')
                time.sleep(.3)
                return data
            except Exception:
                if attempt:
                    raise
                time.sleep(1)

    sources = {}
    failures = []
    urls = set()
    for problem in problems:
        url = problem['encoded'].get('url', '')
        if 'luogu.com.cn/problem/' in url:
            urls.add(url)
        elif 'ac.nowcoder.com/acm/contest/' in url:
            urls.add('https://ac.nowcoder.com/acm/contest/problem-list?token=&id=' + url.split('/')[-2])
    urls.update(('https://codeforces.com/api/problemset.problems', 'https://kenkoooo.com/atcoder/resources/problem-models.json'))

    def fetch(url):
        headers = {'x-lentille-request': 'content-only'} if 'luogu.com.cn' in url else None
        return url, get(url, headers)

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(fetch, url): url for url in sorted(urls)}
        for i, future in enumerate(as_completed(futures), 1):
            try:
                url, data = future.result()
                sources[url] = data
            except Exception as error:
                failures.append({'url': futures[future], 'error': type(error).__name__})
            if i % 50 == 0 or i == len(futures):
                print('public sources', i, '/', len(futures), 'unavailable', len(failures), flush=True)

    cf = sources.get('https://codeforces.com/api/problemset.problems', {})
    cf = {f"{p['contestId']}/{p['index']}": p for p in (cf.get('result') or {}).get('problems', [])}
    at = sources.get('https://kenkoooo.com/atcoder/resources/problem-models.json', {})
    audit = []
    for problem in problems:
        row = problem['encoded']
        url = row.get('url', '')
        previous = row.get('difficulty')
        result = None
        if row.get('platform') == 'Codeforces':
            match = re.search(r'/(?:contest|gym)/(\d+)/problem/([^/]+)', url)
            entry = cf.get('/'.join(match.groups())) if match else None
            if entry is not None:
                rating = entry.get('rating')
                result = {'difficulty': rating, 'nativeDifficulty': rating,
                          'difficultySource': 'Codeforces 官方 rating' if rating is not None else 'Codeforces 官方尚未评级',
                          'difficultyEstimated': False, 'difficultyConfidence': 'HIGH' if rating is not None else 'UNKNOWN',
                          'difficultyBand': [rating, rating] if rating is not None else None,
                          'difficultyEvidence': ['https://codeforces.com/api/problemset.problems', url]}
            elif cf:
                result = unknown('Codeforces 未提供官方 rating', [url])
        elif row.get('platform') == 'AtCoder':
            model = at.get(url.rsplit('/', 1)[-1])
            if model and model.get('difficulty') is not None:
                native = model['difficulty']
                converted = cf_eq.cf_eq_atcoder(native)
                result = {'difficulty': converted['cf_eq_rating'], 'nativeDifficulty': native,
                          'difficultySource': 'CF-EQ · AtCoder Problems 最新模型估算',
                          'difficultyEstimated': True, 'difficultyConfidence': 'MEDIUM',
                          'difficultyBand': converted['cf_eq_band'], 'difficultyEvidence': converted['difficulty_evidence']}
            elif at:
                result = unknown('AtCoder Problems 尚无模型难度', [url])
        elif row.get('platform') == '洛谷':
            data = sources.get(url, {})
            entry = (data.get('data') or {}).get('problem') or {}
            if entry.get('pid') == url.rsplit('/', 1)[-1]:
                native = entry.get('difficulty')
                converted = cf_eq.cf_eq_luogu(native)
                result = {'difficulty': converted['cf_eq_rating'], 'nativeDifficulty': native,
                          'difficultySource': f'CF-EQ · 洛谷官方难度档 {native}（区间换算）',
                          'difficultyEstimated': True, 'difficultyConfidence': 'LOW' if converted['cf_eq_rating'] is not None else 'UNKNOWN',
                          'difficultyBand': converted['cf_eq_band'], 'difficultyEvidence': converted['difficulty_evidence']}
        elif row.get('platform') == '牛客':
            source = 'https://ac.nowcoder.com/acm/contest/problem-list?token=&id=' + url.split('/')[-2]
            entries = (sources.get(source, {}).get('data') or {}).get('data') or []
            entry = next((p for p in entries if str(p.get('index')) == row['problem']), None)
            max_accepted = max((p.get('acceptedCount', 0) for p in entries), default=0)
            result = nowcoder(row, entry, max_accepted)
        if result is None:
            # A failed request does not validate a previous heuristic.
            result = unknown('难度待复核 · 本次公开来源不可用', [url])
        result.update(metadataVersion=VERSION, difficultyCheckedAt=checked)
        row.update(result)
        problem['raw']['难度'] = str(result['difficulty']) if result['difficulty'] is not None else '—'
        metadata[url] = {**metadata.get(url, {}), **result}
        audit.append({'id': row['id'], 'url': url, 'before': previous, **result})
    report = {'version': VERSION, 'checkedAt': checked, 'problems': len(audit),
              'changed': sum(p['before'] != p['difficulty'] for p in audit),
              'rated': sum(p['difficulty'] is not None for p in audit),
              'unknown': sum(p['difficulty'] is None for p in audit),
              'failedSources': failures, 'audit': audit}
    (args.cache / 'audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf8')
    if args.apply:
        problems_path.write_text(json.dumps(problems, ensure_ascii=False, indent=2) + '\n', 'utf8')
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', 'utf8')
        public = {key: value for key, value in report.items() if key != 'audit'}
        (ROOT / 'backend/resources/difficulty-audit.json').write_text(json.dumps(public, ensure_ascii=False, indent=2) + '\n', 'utf8')
    print(json.dumps({key: value for key, value in report.items() if key not in ('audit', 'failedSources')}), flush=True)


if __name__ == '__main__':
    main()
