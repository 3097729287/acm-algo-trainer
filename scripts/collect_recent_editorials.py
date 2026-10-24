"""Read public problem evidence for the four contests on 2026-10-24."""
import concurrent.futures
import json
from pathlib import Path
import re
import sqlite3
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.backups' / 'recent-20261024'
INSTALL = ROOT.parents[1] / '版本' / '最新版' / '程序'
CONTESTS = ['基础赛 41', '月赛 311', 'Div.2 1129', 'ABC 481']


def readonly(path):
    return sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)


def fetch(item):
    url, name = item
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(request, timeout=30) as response:
            content = response.read().decode('utf-8')
        (OUT / 'raw' / name).write_text(content, encoding='utf-8')
        return {'url': url, 'file': name, 'bytes': len(content)}
    except Exception as error:
        return {'url': url, 'error': str(error)}


def main():
    (OUT / 'raw').mkdir(parents=True, exist_ok=True)
    (OUT / 'statements').mkdir(exist_ok=True)
    with readonly(INSTALL / 'state' / 'tb-documents.sqlite3') as db:
        source = json.loads(db.execute("SELECT value FROM documents WHERE key='integrations.json'").fetchone()[0])
    rows = [dict(r) for r in source['rows'].values() if r.get('contest') in CONTESTS]
    for r in rows:
        r.pop('addedAt', None)
        r['date'] = ''
        r['status'] = '未做'
    ids = {r['id'] for r in rows}
    statements = {}
    with readonly(INSTALL / 'state' / 'statements' / 'tb-documents.sqlite3') as db:
        for key, value in db.execute('SELECT key,value FROM documents'):
            obj = json.loads(value)
            if isinstance(obj, dict) and obj.get('id') in ids:
                statements[obj['id']] = obj
    # Public HTML cache is retained only for the requested original-site URLs.
    with readonly(INSTALL / 'state' / 'http' / 'tb-documents.sqlite3') as db:
        for key, value in db.execute('SELECT key,value FROM documents'):
            obj = json.loads(value)
            if isinstance(obj, dict) and re.search(r'abc481|contest/2277|P1776[0-7]|contest/345405|contest/364653', obj.get('url', '')):
                (OUT / 'raw' / ('cached-' + key)).write_text(json.dumps(obj, ensure_ascii=False), encoding='utf-8')
    for r in rows:
        pid = r['id']
        slug = pid.replace(':', '_')
        if pid in statements:
            (OUT / 'statements' / (slug + '.json')).write_text(json.dumps(statements[pid], ensure_ascii=False, indent=2), encoding='utf-8')
            (OUT / 'statements' / (slug + '.md')).write_text(statements[pid]['markdown'], encoding='utf-8')
    (OUT / 'scope.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    requests = [(r['url'] + ('?lang=en' if r['platform'] == 'AtCoder' else ''), r['id'].replace(':', '_') + '.html') for r in rows]
    requests += [(f'https://codeforces.com/contest/2277/problem/{letter}', f'cf2277_{letter}.html') for letter in ['D1', 'D2']]
    requests += [('https://codeforces.com/api/contest.standings?contestId=2277&from=1&count=100', 'cf-standings.json'), ('https://atcoder.jp/contests/abc481/editorial', 'abc481-editorial.html')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(fetch, requests))
    (OUT / 'fetch-log.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'problems': len(rows), 'cachedStatements': len(statements), 'fetches': results}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
