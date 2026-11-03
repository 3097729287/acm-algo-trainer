"""Collect the three requested public Nowcoder lists into the public text seed.

Anonymous GET only; resumable private HTTP cache. Collection and --apply are
separate, and neither writes a personal or bundled SQLite database.
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
import sys
import threading
import time
from urllib.parse import urljoin, urlsplit, parse_qs
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/common')]
from statement_format import Tree, plain
from statement_integrity import content_complete
from statement_seed import checksum, load_statements
from public_platforms import statement

BASE = 'https://ac.nowcoder.com'
SOURCE_IDS = ['817596', '828697', '926597']
TITLES = ['语法入门＋算法入门题单', '算法进阶题单', '算法基础精选题单']
# NC53264 links the original JOI task booklet and this illustration host.
# These are source assets, never alternative problem identities.
ASSET_HOSTS = {'www.ioi-jp.org', 'www2.ioi-jp.org', 'ioi-jp.org', 'z4a.net', 'www.z4a.net'}


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


class Client:
    def __init__(self, directory, delay=.2):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.delay, self.lock, self.next_at = delay, threading.Lock(), 0

    def bytes(self, url):
        parsed = urlsplit(url)
        host = parsed.hostname or ''
        if parsed.scheme not in ('http', 'https') or parsed.username or parsed.password or not (host == 'nowcoder.com' or host.endswith('.nowcoder.com') or host in ASSET_HOSTS):
            raise ValueError('Only public Nowcoder sources and reviewed original assets are allowed')
        key = hashlib.sha256(url.encode()).hexdigest()
        path = self.directory / (key + '.bin')
        if path.exists():
            value = path.read_bytes()
            receipt = json.loads(path.with_suffix('.json').read_text('utf-8'))
            if receipt['url'] != url or receipt['sha256'] != hashlib.sha256(value).hexdigest():
                raise ValueError('Public cache integrity mismatch')
            return value
        with self.lock:
            pause = max(0, self.next_at - time.monotonic())
            if pause:
                time.sleep(pause)
            self.next_at = time.monotonic() + self.delay
        transport = url.replace('http://z4a.net/', 'https://z4a.net/', 1)
        request = Request(transport, headers={'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'})
        with urlopen(request, timeout=20) as response:
            destination = urlsplit(response.url)
            if not ((destination.hostname or '') == 'nowcoder.com' or (destination.hostname or '').endswith('.nowcoder.com') or destination.hostname in ASSET_HOSTS):
                raise ValueError('Unexpected source redirect')
            value = response.read(12_000_001)
            if response.status != 200 or len(value) > 12_000_000:
                raise ValueError('Public response is unsuccessful or too large')
        path.write_bytes(value)
        dump(path.with_suffix('.json'), {'url': url, 'sha256': hashlib.sha256(value).hexdigest(), 'bytes': len(value)})
        return value

    def text(self, url):
        return self.bytes(url).decode('utf-8')

    def json(self, url):
        return json.loads(self.text(url))


def page_title(page, fallback):
    match = re.search(r'<title[^>]*>(.*?)</title>', page, re.S | re.I)
    title = html.unescape(re.sub('<[^>]*>', '', match[1])).strip() if match else ''
    return title or fallback


def key(url):
    if not isinstance(url, str) or not url:
        return ''
    parsed = urlsplit(url)
    return (parsed.hostname or '').removeprefix('www.') + parsed.path.rstrip('/')


def problem_item(pid, sections, source_url, title=''):
    return {'pid': 'NC' + str(pid), 'url': BASE + '/acm/problem/' + str(pid),
            'sections': sections, 'membershipSource': source_url, **({'sourceTitle': title} if title else {})}


def contest_list(client, url):
    cid = urlsplit(url).path.rsplit('/', 1)[1]
    endpoint = BASE + '/acm/contest/problem-list?token=&id=' + cid
    payload = client.json(endpoint)
    if payload.get('code') != 0:
        raise ValueError('Practice roster unavailable')
    data = payload.get('data') or {}
    rows, info = data.get('data'), data.get('basicInfo') or {}
    if not isinstance(rows, list) or not rows or not isinstance(info.get('problemCount'), int):
        raise ValueError('Practice roster is incomplete')
    rows = list(rows)
    page_count, page_size = info.get('pageCount', 1), info.get('pageSize', 50)
    if not isinstance(page_count, int) or not 1 <= page_count <= 50 or not isinstance(page_size, int) or page_size <= 0 or (info['problemCount'] + page_size - 1) // page_size != page_count:
        raise ValueError('Unexpected practice pagination')
    for page_number in range(2, page_count + 1):
        later = client.json(endpoint + '&page=' + str(page_number))
        data_page = later.get('data') or {}
        page_info = data_page.get('basicInfo') or {}
        if later.get('code') != 0 or page_info.get('problemCount') != info['problemCount'] or page_info.get('pageCurrent') != page_number or page_info.get('pageCount') != page_count or not isinstance(data_page.get('data'), list):
            raise ValueError('Practice pagination changed or is incomplete')
        rows.extend(data_page['data'])
    if info['problemCount'] != len(rows):
        raise ValueError('Practice roster count mismatch')
    if len({p.get('index') for p in rows}) != len(rows):
        raise ValueError('Duplicate practice letters')
    items = []
    for row in rows:
        pid, index = row.get('problemId'), row.get('index')
        if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0 or not re.fullmatch('[A-Za-z0-9]{1,12}', str(index)) or not row.get('title'):
            raise ValueError('Invalid public original problem binding')
        item = problem_item(pid, [], endpoint, row['title'])
        item.update(contestUrl=url + '/' + index, contestIndex=index)
        items.append(item)
    return {'id': 'nowcoder-contest-' + cid, 'url': url,
            'title': page_title(client.text(url), '牛客练习 ' + cid), 'problems': items,
            'officialProblemCount': info['problemCount'], 'children': [], 'categories': [], 'aggregateChildren': False, 'available': True}


def collection_list(client, url):
    pid = urlsplit(url).path.rsplit('/', 1)[1]
    pending, visited, ordered, expected, first = [url], set(), {}, None, ''
    while pending:
        current = pending.pop(0)
        if current in visited:
            continue
        if len(visited) >= 50:
            raise ValueError('Collection pagination exceeds review bound')
        visited.add(current)
        page = client.text(current)
        first = first or page
        match = re.search(r'pageInfo\s*:\s*(\{[^{}]*\})', page)
        info = json.loads(match[1]) if match else None
        if not info or not isinstance(info.get('totalCount'), int) or info['totalCount'] <= 0:
            raise ValueError('Collection total count missing')
        if expected is not None and expected != info['totalCount']:
            raise ValueError('Collection changed during collection')
        expected = info['totalCount']
        root = Tree(page).root
        for node in root.find(lambda n: n.tag == 'a' and bool(n.attrs.get('href'))):
            target = urljoin(current, node.attrs['href'])
            parsed = urlsplit(target)
            original = re.fullmatch(r'/acm/problem/(\d+)', parsed.path)
            if parsed.hostname == 'ac.nowcoder.com' and original:
                item = problem_item(original[1], [], current, plain(node).strip())
                if item['url'] not in ordered or 'title' in (node.attrs.get('class') or '').split():
                    ordered[item['url']] = item
            if parsed.hostname == 'ac.nowcoder.com' and parsed.path == urlsplit(url).path and parsed.query:
                query = parse_qs(parsed.query)
                if set(query) <= {'page'} and query.get('page', [''])[0].isdigit() and target not in visited and target not in pending:
                    pending.append(target)
    if len(ordered) != expected:
        raise ValueError(f'Collection incomplete: {len(ordered)} of {expected}')
    return {'id': 'nowcoder-collection-' + pid, 'url': url, 'title': page_title(first, '牛客题单 ' + pid),
            'problems': list(ordered.values()), 'officialProblemCount': expected, 'children': [],
            'categories': [], 'aggregateChildren': False, 'available': True}


def original_samples(page):
    root = Tree(page).root
    inputs, outputs = [], []
    for node in root.find(lambda n: n.tag == 'textarea'):
        name = node.attrs.get('data-clipboard-text-id') or ''
        if re.fullmatch(r'input\d*', name):
            inputs.append((name[5:], plain(node).strip('\r\n')))
        elif re.fullmatch(r'output\d*', name):
            outputs.append((name[6:], plain(node).strip('\r\n')))
    if [item[0] for item in inputs] != [item[0] for item in outputs] or len({item[0] for item in inputs}) != len(inputs):
        raise ValueError('Incomplete original sample pairs')
    return [{'name': '样例 ' + str(i + 1), 'input': a[1], 'output': b[1]} for i, (a, b) in enumerate(zip(inputs, outputs))]


def fetch_problem(client, url, fallback):
    page = client.text(url)
    title = page_title(page, fallback)
    if title in ('登录', '牛客网'):
        raise ValueError('Original problem requires login')
    pid = url.rsplit('/', 1)[1]
    value = statement(client, 'nowcoder-global::' + pid, title, url)
    samples = original_samples(page)
    for sample, previous in zip(samples, value['samples']):
        if previous.get('explanation'):
            sample['explanation'] = previous['explanation']
    value['samples'] = samples
    # Keep the stated C++ limit, not the adapter's historical fallback values.
    labels = html.unescape(re.sub('<[^>]*>', ' ', page))
    tl = re.search(r'时间限制[：:]\s*(?:C/C\+\+/Rust/Pascal\s*)?(\d+(?:\.\d+)?)\s*秒', labels)
    ml = re.search(r'(?:空间|内存)限制[：:]\s*(?:C/C\+\+/Rust/Pascal\s*)?(\d+(?:\.\d+)?)\s*M', labels)
    value['limits'] = {'timeMs': round(float(tl[1]) * 1000) if tl else None,
                       'memoryMb': round(float(ml[1])) if ml else None}
    value['integrity']['sampleCount'] = len(samples)
    value['sourceHtmlSha256'] = hashlib.sha256(page.encode()).hexdigest()
    if not content_complete(value):
        raise ValueError('Original statement or its resources remain incomplete')
    return {'id': value['id'], 'title': title, 'url': url, 'statement': value}


def collect(client, inventory, output):
    roots, linked, problems, errors = [], {}, {}, []
    for position, source in enumerate(inventory['sources']):
        source_id = source['discussionUrl'].rsplit('/', 1)[1]
        if source_id != SOURCE_IDS[position]:
            raise ValueError('Unexpected requested source')
        items, children = [], []
        for link in source['links']:
            if link['kind'] == 'problem':
                item = problem_item(link['url'].rsplit('/', 1)[1], link['sourceHeadings'], source['discussionUrl'], link['sourceLabel'])
                items.append(item)
            else:
                child = 'nowcoder-' + link['kind'] + '-' + link['url'].rsplit('/', 1)[1]
                if child not in children:
                    children.append(child)
                linked[child] = link
        roots.append({'id': 'nowcoder-' + source_id, 'title': TITLES[position], 'url': source['discussionUrl'],
                      'problems': items, 'children': children, 'aggregateChildren': True, 'available': True,
                      'categories': [{'id': 'nowcoder-public-foundations', 'name': '牛客公开题单', 'order': 0, 'position': position}]})

    def expand(pair):
        identity, link = pair
        try:
            value = (contest_list if link['kind'] == 'contest' else collection_list)(client, link['url'])
            if link.get('exerciseTitle'):
                value['title'] = link['exerciseTitle']
            return value, None
        except Exception as error:
            return {'id': identity, 'url': link['url'], 'title': link['sourceLabel'], 'problems': [], 'children': [], 'categories': [], 'available': False}, {'kind': 'roster', 'url': link['url'], 'error': str(error)}

    with ThreadPoolExecutor(max_workers=3) as pool:
        expanded = []
        for value, error in pool.map(expand, linked.items()):
            expanded.append(value)
            if error:
                errors.append(error)
    lists = roots + expanded
    references = {}
    for training in lists:
        for item in training['problems']:
            references.setdefault(item['url'], item.get('sourceTitle') or item['pid'])
    problem_cache = output.parent / 'problems'
    problem_cache.mkdir(parents=True, exist_ok=True)

    def original(pair):
        url, title = pair
        path = problem_cache / (url.rsplit('/', 1)[1] + '.json')
        try:
            value = json.loads(path.read_text('utf-8')) if path.exists() else fetch_problem(client, url, title)
            if value['url'] != url or not content_complete(value['statement']):
                raise ValueError('Cached original problem is incomplete')
            if not path.exists():
                dump(path, value)
            return url, value, None
        except Exception as error:
            return url, {'url': url, 'title': title}, {'kind': 'statement', 'url': url, 'error': str(error)}

    with ThreadPoolExecutor(max_workers=3) as pool:
        for url, value, error in pool.map(original, references.items()):
            problems[url] = value
            if error:
                errors.append(error)
            if len(problems) % 50 == 0:
                print('Original statements', len(problems), '/', len(references), flush=True)
    result = {'schema': 1, 'collectedAt': dt.datetime.now(dt.timezone.utc).isoformat(), 'lists': lists, 'problems': problems, 'errors': errors}
    dump(output, result)
    print(json.dumps({'lists': len(lists), 'problems': len(problems), 'statements': sum('statement' in p for p in problems.values()), 'rosterErrors': sum(e['kind'] == 'roster' for e in errors), 'statementErrors': sum(e['kind'] == 'statement' for e in errors)}), flush=True)
    return result


def source_roots(lists):
    by_id, result = {item['id']: item for item in lists}, {}
    for source_id in SOURCE_IDS:
        root = by_id.get('nowcoder-' + source_id)
        if not root:
            continue
        pending, visited = [root['id']], set()
        while pending:
            identity = pending.pop()
            if identity in visited or identity not in by_id:
                continue
            visited.add(identity)
            value = by_id[identity]
            for item in value['problems']:
                sources = result.setdefault(item['url'], [])
                if root['url'] not in sources:
                    sources.append(root['url'])
            pending.extend(value.get('children', []))
    return result


def apply(collection, source, backup):
    source, backup = Path(source), Path(backup)
    if source.suffix or source.is_symlink():
        raise ValueError('Only a public text seed directory is accepted')
    if any(error.get('kind') == 'roster' for error in collection['errors']) or any(not item.get('available') for item in collection['lists']):
        raise ValueError('Incomplete rosters cannot replace the public catalogue; collect and verify a new snapshot')
    listed = {item['id'] for item in collection['lists']}
    if any(child not in listed for item in collection['lists'] for child in item.get('children', [])):
        raise ValueError('A linked practice roster is missing')
    if any(problem['url'] not in collection['problems'] for item in collection['lists'] for problem in item['problems']):
        raise ValueError('An original problem identity is missing')
    originals = {name: (source / name).read_bytes() for name in ('problems.json', 'training_lists.json')}
    rows = json.loads(originals['problems.json'])
    lists = json.loads(originals['training_lists.json'])
    by_url = {key(row['url']): row for row in rows if key(row.get('url'))}
    statements = {s['problem_id']: s['content'] for s in load_statements(source)}
    roots_by_problem = source_roots(collection['lists'])
    added, reused, patches = [], [], []
    for url, value in collection['problems'].items():
        pid = url.rsplit('/', 1)[1]
        if not re.fullmatch(r'https://ac\.nowcoder\.com/acm/problem/[1-9]\d*', url):
            raise ValueError('Non-canonical original URL')
        old = by_url.get(key(url))
        if old:
            identity = old['id']
            reused.append(identity)
        else:
            identity = 'nowcoder-global::' + pid
            encoded = {'id': identity, 'url': url, 'title': value['title'], 'problem': 'NC' + pid,
                       'platform': '牛客', 'contest': '牛客题库', 'contestFamily': '牛客题库', 'contestRoster': False,
                       'series': '牛客题库', 'source': 'nowcoder-global', 'globalProblemId': int(pid),
                       'difficulty': None, 'difficultyEstimated': False, 'difficultySource': '牛客公开原题页未提供可核验评级',
                       'difficultyConfidence': 'UNKNOWN', 'tags': [], 'knowledge': '', 'knowledgeCategories': [],
                       'knowledgeReviewRequired': True, 'status': '未做', 'date': '', 'solutionAvailable': False,
                       'statementAvailable': bool(value.get('statement')), 'collectionSource': roots_by_problem.get(url, [url])[0],
                       'collectionSources': roots_by_problem.get(url, [url])}
            raw = {'_id': identity, '_url': url, '_platform': '牛客', '_series': '牛客题库', '场次': '牛客题库',
                   '题号': 'NC' + pid, '题名': value['title'], '知识点': '', '难度': '—', '状态': '未做', '日期': ''}
            row = {'id': identity, 'url': url, 'raw': raw, 'encoded': encoded}
            rows.append(row)
            by_url[key(url)] = row
            added.append(identity)
        incoming = value.get('statement')
        if incoming and identity not in statements:
            incoming = dict(incoming, id=identity)
            patches.append({'problem_id': identity, 'beforeSha256': checksum(None), 'content': incoming})
        for training in collection['lists']:
            for item in training['problems']:
                if item['url'] == url:
                    item['problemId'] = identity
    by_list = {training['id']: i for i, training in enumerate(lists)}
    for training in collection['lists']:
        incoming = dict(training, collectedAt=collection['collectedAt'], problemCount=len({p['url'] for p in training['problems']}))
        if incoming['id'] in by_list:
            lists[by_list[incoming['id']]] = incoming
        else:
            lists.append(incoming)
    backup.mkdir(parents=True, exist_ok=True)
    for name, raw in originals.items():
        if (backup / name).exists():
            raise ValueError('Use a new import backup directory')
        (backup / name).write_bytes(raw)
        if (source / name).read_bytes() != raw:
            raise ValueError('Public source changed during import')
    patch_path = source / 'statement-patches/nowcoder-next-local.json'
    # All changes are additive; preserve earlier import patches on a resumed run.
    previous = json.loads(patch_path.read_text('utf-8'))['statements'] if patch_path.exists() else []
    if patch_path.exists():
        shutil.copy2(patch_path, backup / patch_path.name)
    dump(patch_path, {'schema': 1, 'statements': previous + patches})
    dump(source / 'problems.json', rows)
    dump(source / 'training_lists.json', lists)
    report = {'schema': 1, 'collectedAt': collection['collectedAt'], 'rootLists': [BASE + '/discuss/' + n for n in SOURCE_IDS],
              'addedProblems': len(added), 'reusedProblems': len(reused), 'newStatements': len(patches),
              'uniqueProblems': len(collection['problems']), 'totalProblems': len(rows), 'listsFromThisImport': len(collection['lists']),
              'errors': collection['errors'], 'personalDatabasesModified': False, 'currentProgramsModified': False}
    dump(backup / 'report.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory', type=Path, default=ROOT / 'data/next-local/nowcoder-source-inventory.json')
    parser.add_argument('--cache', type=Path, default=ROOT / '.backups/next-local-dev-20261104/nowcoder/http')
    parser.add_argument('--collection', type=Path, default=ROOT / '.backups/next-local-dev-20261104/nowcoder/collection-current.json')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--source', type=Path, default=ROOT / 'data/library')
    parser.add_argument('--backup', type=Path, default=ROOT / '.backups/next-local-dev-20261104/nowcoder/before-import')
    args = parser.parse_args()
    collection = json.loads(args.collection.read_text('utf-8')) if args.collection.exists() else collect(Client(args.cache), json.loads(args.inventory.read_text('utf-8')), args.collection)
    if args.apply:
        print(json.dumps(apply(collection, args.source, args.backup), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
