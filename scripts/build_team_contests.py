"""Compile public contest identities for server-owned team training selection.

The service accepts a catalogue key, never client-provided questions or scores.
Unavailable originals remain disabled slots in otherwise playable contests.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/common')]
from contest_scope import excluded
from insights import canonical_url
from statement_integrity import content_complete, native_submission_supported, statement_type
from statement_seed import load_statements


def identity(row):
    url = urlsplit(row.get('url') or '')
    if url.scheme != 'https' or url.username or url.password or url.query or url.fragment:
        return None
    if url.hostname == 'codeforces.com':
        match = re.fullmatch(r'/(contest|gym)/(\d+)/problem/([A-Z][0-9]?)', url.path)
        if match:
            return 'codeforces:' + match[1] + ':' + match[2], match[3], 'Codeforces'
    elif url.hostname == 'atcoder.jp':
        match = re.fullmatch(r'/contests/([a-z0-9_-]+)/tasks/([a-z0-9_-]+)', url.path)
        if match:
            return 'atcoder:' + match[1], row['problem'], 'AtCoder'
    elif url.hostname == 'ac.nowcoder.com':
        match = re.fullmatch(r'/acm/contest/(\d+)/([A-Z][0-9]?)', url.path)
        if match:
            return 'nowcoder:' + match[1], match[2], '牛客'
    return None


def build(source):
    statements = {r['problem_id']: r['content'] for r in load_statements(source)}
    groups = collections.defaultdict(dict)
    names = {}
    for record in json.loads((source / 'problems.json').read_text('utf8')):
        row = record['encoded']
        if excluded(row) or row.get('catalogHidden') and not row.get('statementRetired'):
            continue
        bound = identity(row)
        canonical = canonical_url(row.get('url'))
        if not bound or not canonical:
            continue
        contest, letter, platform = bound
        statement = statements.get(row['id']) or {}
        kind = statement_type(statement)
        problem_key = hashlib.sha256(canonical.encode()).hexdigest()
        value = {'id': row['id'], 'letter': letter, 'title': row['title'], 'url': row['url'],
                 'problemKey': problem_key, 'problemType': kind,
                 'available': content_complete(statement) and native_submission_supported(row['url'])
                 and not row.get('statementRetired') and kind not in {'communication', 'output-only', 'attachment'}}
        names.setdefault(contest, (row['contest'], platform))
        previous = groups[contest].get(problem_key)
        if previous is None or not previous['available'] and value['available']:
            groups[contest][problem_key] = value
    contests = []
    for key, tasks in sorted(groups.items()):
        if not 2 <= len(tasks) <= 26 or not any(t['available'] for t in tasks.values()):
            continue
        problems = sorted(tasks.values(), key=lambda value: [int(p) if p.isdigit() else p
                          for p in re.split(r'(\d+)', str(value['letter']))])
        assert len({p['letter'] for p in problems}) == len(problems), 'Ambiguous native task letters: ' + key
        title, platform = names[key]
        contests.append({'id': key, 'title': title, 'platform': platform, 'problems': problems,
                         'availableProblems': sum(p['available'] for p in problems),
                         'missingProblems': sum(not p['available'] for p in problems)})
    payload = json.dumps(contests, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    return {'schema': 1, 'revision': hashlib.sha256(payload).hexdigest(), 'contests': contests}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'data/library')
    parser.add_argument('--output', type=Path, default=ROOT / 'server/leaderboard/src/team-contests.json')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = build(args.source)
    if args.check:
        assert json.loads(args.output.read_text('utf8')) == result, 'Team catalogue is stale'
    else:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', 'utf8', newline='\n')
    print(json.dumps({'contests': len(result['contests']), 'problems': sum(len(r['problems']) for r in result['contests']),
                      'partialContests': sum(bool(r['missingProblems']) for r in result['contests']),
                      'revision': result['revision']}, ensure_ascii=False))
