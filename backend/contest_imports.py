"""Import an explicitly requested or started contest from its public source.

Schedules and rosters are public catalogue data, independent of account sessions.
No authentication, submission, editorial disclosure, or speculative task creation.
"""
import hashlib
import re

import public_platforms as P
from contest_policy import content_ready
from persistence import load_document, save_document


SCHOOL_CONTESTS = (
    {'id': 'codeforces:726517', 'platform': 'codeforces', 'title': '校队训练 · Gym 726517',
     'url': 'https://codeforces.com/gym/726517', 'schoolTraining': True},
    {'id': 'nowcoder:142622', 'platform': 'nowcoder', 'title': '1024数学专场考核',
     'url': 'https://ac.nowcoder.com/acm/contest/142622', 'schoolTraining': True},
)


def roster(client, event):
    """Validate the exact contest identity; points are never treated as rating."""
    platform = event['platform']
    cid = event['id'].split(':', 1)[1]
    contest = {'id': cid, 'name': event['title'], 'start': event.get('startAt'),
               'end': event.get('endAt'), 'series': P.LABELS[platform]}
    rows = []
    if platform == 'codeforces':
        result = P.cf_roster(client, cid)
        actual = result.get('contest') or {}
        if str(actual.get('id')) != cid:
            raise ValueError('原站比赛编号与请求不一致')
        contest['name'] = actual.get('name') or contest['name']
        contest['start'] = actual.get('startTimeSeconds') or contest['start']
        if actual.get('startTimeSeconds') and actual.get('durationSeconds'):
            contest['end'] = actual['startTimeSeconds'] + actual['durationSeconds']
        prefix = 'gym' if '/gym/' in event['url'] else 'contest'
        for task in result.get('problems') or []:
            index = str(task.get('index') or '')
            if not re.fullmatch(r'[A-Z][0-9]?', index):
                continue
            rows.append(P.row(platform, contest, index, task['name'],
                f'https://codeforces.com/{prefix}/{cid}/problem/{index}', P.integer(task.get('rating')),
                'Codeforces 官方 rating', [P.CF_TAGS[tag] for tag in task.get('tags', []) if tag in P.CF_TAGS]))
    elif platform == 'atcoder':
        if not re.fullmatch(r'[a-z0-9_-]+', cid):
            raise ValueError('AtCoder 比赛编号无效')
        page = client.text(f'https://atcoder.jp/contests/{cid}/tasks?lang=en')
        for block in re.findall(r'<tr\b[^>]*>.*?</tr>', page, re.S):
            links = re.findall(r'<a\b[^>]*href=["\']/contests/([^/"\']+)/tasks/([^"\']+)["\'][^>]*>(.*?)</a>', block, re.S)
            if len(links) < 2 or any(link[0] != cid for link in links):
                continue
            task, index, title = links[0][1], P.text(links[0][2]), P.text(links[1][2])
            if not re.fullmatch(r'[a-z0-9_]+', task):
                continue
            rows.append(P.row(platform, contest, index, title, f'https://atcoder.jp/contests/{cid}/tasks/{task}', None, '比赛尚无可靠难度评分'))
    elif platform == 'nowcoder':
        if not cid.isdigit():
            raise ValueError('牛客比赛编号无效')
        result = client.json('https://ac.nowcoder.com/acm/contest/problem-list?token=&id=' + cid)
        if result.get('code') != 0:
            raise ValueError('原站题单尚未公开或需要报名')
        for task in (result.get('data') or {}).get('data') or []:
            index = str(task.get('index') or '')
            if not re.fullmatch(r'[A-Z][0-9]?', index):
                continue
            rows.append(P.row(platform, contest, index, task['title'], f'https://ac.nowcoder.com/acm/contest/{cid}/{index}', None, '原站未提供可靠数值难度'))
    elif platform == 'luogu':
        if not cid.isdigit():
            raise ValueError('洛谷比赛编号无效')
        result = P.lg_data(client.json('https://www.luogu.com.cn/contest/' + cid, headers={'x-lentille-request': 'content-only'}))
        actual = result.get('contest') or {}
        if str(actual.get('id')) != cid:
            raise ValueError('原站比赛编号与请求不一致')
        contest.update(name=actual.get('name') or contest['name'], start=actual.get('startTime'), end=actual.get('endTime'))
        for position, entry in enumerate(result.get('contestProblems') or []):
            task = entry.get('problem') or {}
            pid = str(task.get('pid') or '')
            if not re.fullmatch(r'[A-Za-z0-9_]+', pid):
                continue
            value = P.row(platform, contest, str(entry.get('no') or chr(65 + position)), task.get('name') or pid,
                          'https://www.luogu.com.cn/problem/' + pid, None, '比赛尚无可靠 CF 难度评分')
            value['nativeDifficulty'] = task.get('difficulty')
            rows.append(value)
    else:
        raise ValueError('尚不支持这个比赛平台')
    if not rows or len(rows) > 100:
        raise ValueError('原站未返回可识别的完整题单；等待公开后重试')
    if len({row['id'] for row in rows}) != len(rows):
        raise ValueError('原站题单存在重复题号，暂缓导入')
    for row in rows:
        row.update(contestRoster=True, contestProblemCount=len(rows), calendarImport=True,
                   schoolTraining=bool(event.get('schoolTraining')))
    return rows


def import_contest(service, event):
    """Publish complete roster with truthful per-task availability, idempotently."""
    rows = roster(service.client, event)
    ready, errors = 0, []
    for row in rows:
        if service.stop.is_set():
            raise RuntimeError('应用正在关闭，稍后继续')
        path = service.state_dir / 'statements' / (hashlib.sha256(row['id'].encode()).hexdigest() + '.json')
        statement = load_document(path, {})
        if not content_ready(statement):
            try:
                statement = P.statement(service.client, row['id'], row['title'], row['url'])
                if not content_ready(statement):
                    raise ValueError('题面与样例尚未完整公开')
                save_document(path, statement)
            except (OSError, ValueError, RuntimeError, KeyError, TypeError) as error:
                errors.append(row['problem'] + '：' + str(error)[:100])
        row['catalogContentReady'] = content_ready(statement)
        if row['catalogContentReady']:
            ready += 1
        else:
            row['statementNotice'] = '原站题面尚未公开或需要在原站报名'
    with service.lock:
        if service.closed:
            raise RuntimeError('应用正在关闭，稍后继续')
        for row in rows:
            old = service.state['rows'].get(row['id'], {})
            # Do not discard later ratings, local supplementation, or first-added dates.
            merged = {**old, **row}
            if row.get('difficulty') is None:
                for key in ('difficulty', 'difficultySource', 'difficultyEvidence', 'difficultyEstimated'):
                    if key in old:
                        merged[key] = old[key]
            service.state['rows'][row['id']] = merged
        service._save()
    return {'status': 'ready' if ready == len(rows) else 'partial', 'total': len(rows),
            'ready': ready, 'title': rows[0]['contest'], 'error': '；'.join(errors)[:350]}
