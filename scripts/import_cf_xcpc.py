"""Import finished ICPC/CCPC Gyms from public Codeforces metadata and dashboards.

The cache is resumable. API calls are spaced by at least 2.1 seconds. A failed
roster is reported, never replaced by guessed letters, titles or difficulties.
Statements can be fetched separately by TB when a task is opened.
"""
import argparse
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
from library import LibraryDatabase
from public_platforms import CF_TAGS, row


def historical_contest(contest):
    name = contest.get('name', '')
    if contest.get('phase') != 'FINISHED' or not re.search(r'ICPC|CCPC', name, re.I):
        return False
    year = re.search(r'(?:19|20)\d{2}', name)
    if not year or int(year[0]) < 2017:
        return False
    # Using ACM/ICPC rules does not make a school test an ICPC event.
    return not re.search(r'ICPC[- ]style|ICPC format|ICPC правила|правила.*ICPC|'
                         r'Team Formation|Team Selection|Selection Contest|Internal Round|'
                         r'Mock (?:Contest|Competition)|Practice Session|Summer School|'
                         r'\bCT S\d+E\d+|\+ Some Problems|\+ GCJ|\+.*Google Code Jam', name, re.I)


def normalize_gym_names(database):
    from collections import defaultdict
    from contest_names import normalize_row
    entries = [entry for entry in database.catalog() if entry['encoded'].get('source') == 'xcpc-codeforces']
    groups = defaultdict(set)
    for entry in entries:
        value = entry['encoded']
        value.pop('contestVariant', None)
        value['contest'] = value.get('contestFullName', value['contest'])
        value = normalize_row(value)
        entry['encoded'] = value
        groups[value['contest']].add(value['contestId'])
    with database.connection() as connection:
        for entry in entries:
            value = entry['encoded']
            if len(groups[value['contest']]) > 1:
                value['contestVariant'] = 'Gym ' + value['contestId']
                value = normalize_row(value)
            entry['raw']['场次'] = value['contest']
            connection.execute('UPDATE problems SET raw=?,encoded=? WHERE id=?',
                               (json.dumps(entry['raw'], ensure_ascii=False), json.dumps(value, ensure_ascii=False), entry['id']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', required=True, type=Path)
    parser.add_argument('--database', required=True, type=Path)
    parser.add_argument('--list-file', type=Path)
    parser.add_argument('--roster-file', type=Path, required=True, help='Verified public dashboard rosters, keyed by Gym ID')
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    last_request = 0

    def get(path):
        nonlocal last_request
        cached = args.cache / (hashlib.sha256(path.encode()).hexdigest() + '.json')
        if cached.exists():
            return json.loads(cached.read_text('utf8'))
        for attempt in range(3):
            time.sleep(max(0, 2.1 - (time.monotonic() - last_request)))
            last_request = time.monotonic()
            try:
                request = Request('https://codeforces.com/api/' + path,
                                  headers={'User-Agent': 'TB public XCPC archive'})
                with urlopen(request, timeout=22) as response:
                    value = json.load(response)
                if value.get('status') != 'OK':
                    raise ValueError(str(value.get('comment', 'API failure')))
                cached.write_text(json.dumps(value, ensure_ascii=False), 'utf8')
                return value
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2 * (attempt + 1))

    listing = json.loads(args.list_file.read_text('utf8')) if args.list_file else get('contest.list?gym=true')
    if listing.get('status') != 'OK':
        raise ValueError('No verified public Gym list')
    named = [c for c in listing['result'] if c.get('phase') == 'FINISHED' and re.search(r'ICPC|CCPC', c.get('name', ''), re.I)]
    contests = [c for c in named if historical_contest(c)]
    database = LibraryDatabase(args.database)
    public_rosters = json.loads(args.roster_file.read_text('utf8'))
    existing = {p.get('url') for p in database.rows()}
    report = {'source': 'https://codeforces.com/api/contest.list?gym=true',
              'checkedAt': dt.datetime.now(dt.timezone.utc).isoformat(),
              'nameMatches': len(named), 'discovered': len(contests),
              'excludedTraining': [{'id': c['id'], 'name': c['name']} for c in named if not historical_contest(c)],
              'coverage': [], 'missing': [], 'added': 0,
              'notice': '公开且已结束的 ICPC/CCPC Gym；题单按公开比赛页面核对。无官方 rating 的题目保持未定级，题面打开时读取原站。'}
    for index, contest in enumerate(contests, 1):
        cid = contest['id']
        try:
            # Gym standings API requires API authentication. Public dashboard
            # task tables are sufficient for anonymous roster collection.
            if str(cid) not in public_rosters:
                raise ValueError('公开题单本次无法读取')
            data = {'contest': {'id': cid}, 'problems': public_rosters[str(cid)]}
            tasks = data.get('problems') or []
            if not tasks or data.get('contest', {}).get('id') != cid:
                raise ValueError('Empty or mismatched roster')
            records = []
            year = re.search(r'(?:19|20)\d{2}', contest['name'])
            for task in tasks:
                letter = task['index']
                url = f'https://codeforces.com/gym/{cid}/problem/{letter}'
                if url in existing:
                    continue
                value = row('codeforces', {'id': cid, 'name': contest['name'], 'series': 'XCPC'},
                            letter, task['name'], url, task.get('rating'),
                            'Codeforces 官方 rating' if task.get('rating') is not None else 'Codeforces Gym 未提供官方 rating',
                            [CF_TAGS[t] for t in task.get('tags', []) if t in CF_TAGS])
                # Gym startTimeSeconds is often the mirror upload or replay date,
                # not the original event date. Do not invent contest chronology.
                value.update(source='xcpc-codeforces', contestFullName=contest['name'],
                             contestFamily='XCPC', xcpcYear=int(year[0]) if year else None,
                             examYear=int(year[0]) if year else None,
                             xcpcKind='邀请赛' if re.search('Invitational|邀请', contest['name'], re.I)
                             else '网络赛' if re.search('Online|网络', contest['name'], re.I)
                             else '省赛' if re.search('Provincial|省', contest['name'], re.I) else '区域赛',
                             contestProblemCount=len(tasks), contestRoster=True,
                             collectionSource=f'https://codeforces.com/gym/{cid}',
                             collectionNotice='按 Codeforces Gym 公开题单核对；题面打开时联网读取，原站不可用时可稍后重试或打开原题。',
                             difficultyEstimated=task.get('rating') is None,
                             difficultyConfidence='HIGH' if task.get('rating') is not None else 'UNKNOWN',
                             metadataVersion='1.0.18')
                raw = {'场次': value['contest'], '题号': letter, '题名': value['title'],
                       '知识点': value['knowledge'], '难度': str(value['difficulty']) if value['difficulty'] is not None else '—',
                       '状态': '未做', '日期': '', '_id': value['id'], '_url': url,
                       '_platform': 'Codeforces', '_series': 'XCPC'}
                records.append((raw, value, None, None))
                existing.add(url)
            database.import_records(records, {}, {})
            report['added'] += len(records)
            report['coverage'].append({'id': cid, 'name': contest['name'], 'url': f'https://codeforces.com/gym/{cid}',
                                       'problems': [p['index'] for p in tasks], 'count': len(tasks)})
        except Exception as error:
            report['missing'].append({'id': cid, 'name': contest['name'], 'error': str(error)[:160]})
        (args.cache / 'coverage.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf8')
        if index % 10 == 0 or index == len(contests):
            print(f"rosters {index}/{len(contests)} added {report['added']} unavailable {len(report['missing'])}", flush=True)
    normalize_gym_names(database)
    (ROOT / 'backend/resources/cf-xcpc-coverage.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf8')


if __name__ == '__main__':
    main()
