"""Collect the public Luogu training directory, then append missing library tasks.

Anonymous GET only. Cached collection is reviewable and resumable; --apply is
explicit and only edits the public text seed, never a personal database.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/common')]
from insights import canonical_url
import cf_eq
from difficulty import normalize_practice_difficulty

BASE = 'https://www.luogu.com.cn'
LINK = re.compile(r'(?<![\w/.:])(?P<url>(?:https?://(?:www\.)?luogu\.(?:com\.cn|org))?/(?P<kind>problem|training)/(?P<id>[A-Za-z0-9_]+))(?![A-Za-z0-9_])')


def dump(path, value, *, sort_keys=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=sort_keys), encoding='utf8', newline='\n')


class Client:
    def __init__(self, cache):
        self.cache = cache
        cache.mkdir(parents=True, exist_ok=True)

    def get(self, path):
        url = BASE + path
        cached = self.cache / (hashlib.sha256(url.encode()).hexdigest() + '.json')
        if cached.exists():
            return json.loads(cached.read_text('utf8'))
        for attempt in range(3):
            result = subprocess.run(['curl.exe' if sys.platform == 'win32' else 'curl',
                                     '-sS', '--fail', '--location', '--max-redirs', '5', '--max-time', '30',
                                     '-H', 'x-lentille-request: content-only', url], capture_output=True)
            try:
                if result.returncode:
                    raise ValueError('Public GET failed: ' + str(result.returncode))
                value = json.loads(result.stdout)
                if value.get('status', 200) != 200:
                    raise ValueError('Unexpected public response status')
                dump(cached, value)
                time.sleep(.15)
                return value
            except (ValueError, UnicodeError):
                if attempt == 2:
                    raise
                time.sleep(1 + attempt)


def clean_heading(text):
    text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)
    return html.unescape(re.sub(r'<[^>]*>|[*`#]', '', text)).strip()[:180]


def description_links(description, own_id):
    """Keep actual heading/link structure, without copying third-party prose."""
    headings = []
    problems, children = {}, []
    fenced = False
    for line in description.splitlines():
        if re.match(r'^\s*(```|~~~)', line):
            fenced = not fenced
        if fenced:
            continue
        heading = re.match(r'^\s*(#{1,6})\s+(.+)', line)
        if heading:
            depth, name = len(heading[1]), clean_heading(heading[2])
            headings = [(d, n) for d, n in headings if d < depth]
            if name:
                headings.append((depth, name))
        for match in LINK.finditer(line):
            identity = match['id']
            if match['kind'] == 'training' and identity.isdigit():
                child = 'luogu-' + identity
                if child != own_id and child not in children and not re.search(r'返回|回到|主题单|总题单|总目录|上级', line):
                    children.append(child)
            elif match['kind'] == 'problem' and re.fullmatch(r'(?:P|B|U|T|CF|SP|AT)[A-Za-z0-9_]+', identity):
                problems.setdefault(identity, [name for _, name in headings])
    return problems, children


def collect(client, output):
    index = client.get('/training/list')['data']
    categories = [{**c, 'order': i} for i, c in enumerate(index['categories'])]
    if not any(c['key'] == 'select' for c in categories):
        categories.append({'key': 'select', 'name': '精选用户分享', 'order': len(categories)})
    roots, indexed = {}, {}
    for category in categories:
        ids, page, expected = [], 1, None
        while expected is None or len(ids) < expected:
            listing = client.get('/training/list?type=' + quote(category['key']) + '&page=' + str(page))['data']['trainings']
            expected = listing['count']
            entries = listing['result']
            before = len(ids)
            for entry in entries:
                identity = 'luogu-' + str(entry['id'])
                indexed.setdefault(identity, entry)
                if identity not in ids:
                    ids.append(identity)
            if len(ids) == before and len(ids) < expected:
                raise ValueError('Incomplete directory pagination: ' + category['key'])
            page += 1
        if len(ids) != expected:
            raise ValueError('Directory changed during collection: ' + category['key'])
        roots[category['key']] = ids
        print(category['name'], len(ids), flush=True)

    lists, metadata, errors = {}, {}, []
    pending = list(indexed)
    attempted = set()

    def fetch(identity):
        try:
            training = client.get('/training/' + identity.removeprefix('luogu-'))['data']['training']
            refs, children = description_links(training.get('description', ''), identity)
            problems = training.get('problems', [])
            if len(problems) != training['problemCount']:
                raise ValueError('Training problem count mismatch')
            ordered = {p['pid']: refs.get(p['pid'], []) for p in problems}
            for pid, sections in refs.items():
                ordered.setdefault(pid, sections)
            return identity, {
                'id': identity, 'title': training['name'], 'url': BASE + '/training/' + str(training['id']),
                'officialProblemCount': training['problemCount'],
                'problems': [{'pid': pid, 'sections': sections} for pid, sections in ordered.items()],
                'children': children, 'categories': [], 'available': True,
            }, problems, None
        except Exception as error:
            entry = indexed.get(identity, {})
            return identity, {'id': identity, 'title': entry.get('name', '洛谷题单 ' + identity[6:]),
                              'url': BASE + '/training/' + identity[6:], 'officialProblemCount': entry.get('problemCount'),
                              'problems': [], 'children': [], 'categories': [], 'available': False}, [], str(error)

    with ThreadPoolExecutor(max_workers=3) as pool:
        while pending:
            if len(attempted) + len(pending) > 2500:
                raise ValueError('Linked training graph exceeds review bound')
            attempted.update(pending)
            next_ids = []
            for identity, value, problems, error in pool.map(fetch, pending):
                lists[identity] = value
                for p in problems:
                    metadata[p['pid']] = {k: p.get(k) for k in ('pid', 'name', 'difficulty', 'tags')}
                if error:
                    errors.append({'kind': 'training', 'id': identity, 'error': error})
                for child in value['children']:
                    if child not in attempted and child not in next_ids:
                        next_ids.append(child)
                if len(lists) % 30 == 0:
                    print('Collected trainings', len(lists), 'problems', len(metadata), flush=True)
            pending = next_ids
    for category in categories:
        for order, identity in enumerate(roots[category['key']]):
            lists[identity]['categories'].append({'id': category['key'], 'name': category['name'],
                                                'order': category['order'], 'position': order})
    unknown = list(dict.fromkeys(p['pid'] for t in lists.values() for p in t['problems'] if p['pid'] not in metadata))
    print('Embedded problem links needing metadata', len(unknown), flush=True)

    def problem(pid):
        try:
            value = client.get('/problem/' + pid)['data']['problem']
            return pid, {'pid': value.get('pid') or pid, 'name': value.get('title') or value.get('name'),
                         'difficulty': value.get('difficulty'), 'tags': value.get('tags', [])}, None
        except Exception as error:
            return pid, None, str(error)

    with ThreadPoolExecutor(max_workers=3) as pool:
        for i, (pid, value, error) in enumerate(pool.map(problem, unknown)):
            if error:
                errors.append({'kind': 'problem', 'id': pid, 'error': error})
            else:
                metadata[pid] = value
            if (i + 1) % 40 == 0:
                print('Resolved embedded problems', i + 1, '/', len(unknown), flush=True)
    tags = client.get('/_lfe/tags')['tags']
    result = {'source': BASE + '/training/list', 'collectedAt': dt.datetime.now(dt.timezone.utc).isoformat(),
              'categories': categories, 'lists': list(lists.values()), 'problems': metadata,
              'tags': {str(t['id']): t['name'] for t in tags if t.get('type') == 2}, 'errors': errors}
    dump(output, result)
    print(json.dumps({'lists': len(lists), 'problems': len(metadata), 'errors': errors}, ensure_ascii=False), flush=True)
    return result


def difficulty_metadata(level, url):
    value = cf_eq.cf_eq_luogu(level)
    known = value['cf_eq_rating'] is not None
    return normalize_practice_difficulty({'difficulty': value['cf_eq_rating'], 'difficultyEstimated': True,
            'difficultySource': 'CF-EQ / 洛谷官方难度档' if known else '洛谷暂无评定（未知难度）',
            'difficultyConfidence': 'LOW' if known else 'UNKNOWN', 'difficultyBand': value['cf_eq_band'],
            'difficultyEvidence': [url, *value['difficulty_evidence']]})


def apply(collection, source, backup):
    existing = json.loads((source / 'problems.json').read_text('utf8'))
    by_url = {canonical_url(p['url']): p for p in existing}
    added, unresolved = [], []
    referenced = list(dict.fromkeys(p['pid'] for t in collection['lists'] for p in t['problems']))
    identities = {}
    for pid in referenced:
        metadata = collection['problems'].get(pid)
        resolved_pid = metadata.get('pid', pid) if metadata else pid
        url = BASE + '/problem/' + resolved_pid
        key = canonical_url(url)
        candidates = [key, canonical_url(BASE + '/problem/' + pid)]
        cf = re.fullmatch(r'CF(\d+)([A-Za-z][0-9]?)', resolved_pid)
        at = re.fullmatch(r'AT_((?:abc|arc|agc)\d+)_([a-z0-9]+)', resolved_pid)
        if cf:
            candidates.append(canonical_url(f'https://codeforces.com/contest/{cf[1]}/problem/{cf[2]}'))
        if at:
            candidates.append(canonical_url(f'https://atcoder.jp/contests/{at[1]}/tasks/{at[1]}_{at[2]}'))
        previous = next((by_url[candidate] for candidate in candidates if candidate in by_url), None)
        if previous:
            identities[pid] = previous['id']
            continue
        if not metadata or not metadata.get('name'):
            unresolved.append(pid)
            continue
        identity = 'luogu-training-' + resolved_pid
        difficulty = difficulty_metadata(metadata.get('difficulty'), url)['difficulty']
        tags = [collection['tags'][str(t)] for t in metadata.get('tags') or [] if str(t) in collection['tags']]
        encoded = {'id': identity, 'url': url, 'title': metadata['name'], 'problem': resolved_pid,
                   'platform': '洛谷', 'contest': '洛谷专题练习', 'series': '洛谷题单',
                   'source': 'luogu-training', 'difficulty': difficulty,
                   **difficulty_metadata(metadata.get('difficulty'), url),
                   'tags': tags, 'knowledge': '、'.join(tags), 'status': '未做', 'date': '',
                   'knowledgeCategories': [], 'knowledgeReviewRequired': not bool(tags),
                   'solutionAvailable': False, 'statementAvailable': False,
                   'collectionSource': collection['source']}
        raw = {'场次': encoded['contest'], '题号': resolved_pid, '题名': encoded['title'], '知识点': encoded['knowledge'],
               '难度': str(difficulty) if difficulty is not None else '—', '状态': '未做', '日期': '',
               '_id': identity, '_url': url, '_platform': '洛谷', '_series': '洛谷题单'}
        row = {'id': identity, 'url': url, 'raw': raw, 'encoded': encoded}
        existing.append(row)
        by_url[key] = row
        identities[pid] = identity
        added.append(identity)
    for training in collection['lists']:
        training['collectedAt'] = collection['collectedAt']
        # A roster's links can recommend other unrelated lists. Directory-only
        # entries aggregate their linked chapters; actual rosters keep their scope.
        training['aggregateChildren'] = training.get('officialProblemCount') == 0
        for p in training['problems']:
            p['problemId'] = identities.get(p['pid'])
            p['url'] = BASE + '/problem/' + collection['problems'].get(p['pid'], {}).get('pid', p['pid'])
    backup.mkdir(parents=True, exist_ok=True)
    for name in ('problems.json', 'training_lists.json'):
        path = source / name
        if path.exists():
            target = backup / name
            if target.exists():
                raise ValueError('Use a new backup directory')
            shutil.copy2(path, target)
    dump(source / 'problems.json', existing, sort_keys=False)
    dump(source / 'training_lists.json', collection['lists'])
    report = {'source': collection['source'], 'collectedAt': collection['collectedAt'],
              'categories': len(collection['categories']), 'lists': len(collection['lists']),
              'indexedLists': sum(bool(t['categories']) for t in collection['lists']),
              'uniqueProblems': len(referenced), 'addedProblems': len(added),
              'reusedProblems': len(identities) - len(added), 'unresolvedProblems': unresolved,
              'errors': collection['errors'], 'totalLibraryProblems': len(existing)}
    dump(ROOT / 'data/luogu-training-coverage.json', report)
    print(json.dumps(report, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=ROOT / '.backups/luogu-training/http')
    parser.add_argument('--collection', type=Path, default=ROOT / '.backups/luogu-training/collection.json')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--source', type=Path, default=ROOT / 'data/library')
    parser.add_argument('--backup', type=Path, default=ROOT / '.backups/luogu-training/before-import')
    args = parser.parse_args()
    collection = json.loads(args.collection.read_text('utf8')) if args.collection.exists() else collect(Client(args.cache), args.collection)
    if args.apply:
        apply(collection, args.source, args.backup)


if __name__ == '__main__':
    main()
