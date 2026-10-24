"""Public catalogue scope; retained personal evidence is never removed."""
from functools import lru_cache
import json
import re
from urllib.parse import urlsplit

MIN_XCPC_YEAR = 2017
AUTHORIZED_SERIES = {'codeforces': ('Div.2', 'Div.3', 'Div.4'),
                     'atcoder': ('ABC', 'ARC'),
                     'nowcoder': ('周赛', '小白月赛', '练习赛', '挑战赛'),
                     'luogu': ('入门赛', '基础赛', '月赛')}
AUTO_SOURCES = ('remote', 'contest-completion')


@lru_cache(maxsize=1)
def policy():
    from paths import resource
    path = resource('contest-policy.json')
    return json.loads(path.read_text('utf8')) if path.exists() else {'curatedCodeforcesContests': [], 'knownGymContests': []}


def event_year(row):
    for key in ('xcpcYear', 'examYear', 'eventYear'):
        value = row.get(key)
        if type(value) is int and 1970 <= value <= 2100:
            return value
    match = re.search(r'(?:19|20)\d{2}', row.get('contestFullName') or row.get('name') or row.get('contest') or '')
    return int(match[0]) if match else None


def retired(row):
    if row.get('catalogRetired'):
        return True
    if row.get('source') != 'xcpc-codeforces':
        return False
    year = event_year(row)
    return year is None or year < MIN_XCPC_YEAR or str(row.get('contestId')) in policy().get('excludedGymContests', [])


def preserved_collection(row):
    """Historical XCPC and Lanqiao collections keep their existing scope."""
    source = row.get('source', '')
    name = ' '.join(str(row.get(key) or '') for key in ('contest', 'contestFullName', 'series'))
    return source.startswith(('xcpc-', 'lanqiao-')) or bool(re.search(r'ICPC|CCPC|XCPC|蓝桥杯', name, re.I))


def authorized(row, platform=None):
    if preserved_collection(row):
        return True
    from contest_names import regular_contest
    parsed = regular_contest(row.get('contestFullName')) or regular_contest(row.get('contest'))
    if not parsed:
        return False
    host = urlsplit(row.get('url') or '').hostname
    platform = platform or {'codeforces.com': 'codeforces', 'atcoder.jp': 'atcoder',
                            'ac.nowcoder.com': 'nowcoder', 'www.luogu.com.cn': 'luogu'}.get(host)
    if platform not in AUTHORIZED_SERIES:
        return False
    allowed = policy().get('authorizedSeries', AUTHORIZED_SERIES).get(platform, ())
    if parsed[0] not in allowed:
        return False
    # Only the Div.2 part of Luogu monthly contests was requested.
    if platform == 'luogu' and parsed[0] == '月赛':
        name = row.get('contestFullName') or row.get('contest') or ''
        division = re.search(r'Div\.\s*([1-4])', name, re.I)
        if division and division[1] != '2':
            return False
    return True


def content_ready(statement):
    if not isinstance(statement, dict) or not str(statement.get('markdown') or '').strip():
        return False
    samples = statement.get('samples')
    return bool(isinstance(samples, list) and samples and all(isinstance(sample, dict)
        and isinstance(sample.get('input'), str) and isinstance(sample.get('output'), str)
        for sample in samples))


def apply_visibility(row):
    if row.get('trainingListMember'):
        # Explicitly collected training lists extend catalogue scope. Stored
        # contest identities/content and all personal progress stay untouched.
        return {key: value for key, value in row.items() if key not in ('catalogHidden', 'catalogNotice', 'catalogVisibilityPolicy')}
    if retired(row):
        return {**row, 'catalogHidden': True, 'catalogNotice': '已退出自动收录范围；个人训练与历史记录保留'}
    if row.get('source') in AUTO_SOURCES and not preserved_collection(row):
        reason = None
        if not authorized(row):
            reason = '不在已指定的比赛系列内；个人训练与历史记录保留'
        elif not row.get('catalogContentReady') and not row.get('solutionAvailable'):
            reason = '公开题面与样例尚未就绪，暂不加入题库；个人训练与历史记录保留'
        if reason:
            return {**row, 'catalogHidden': True, 'catalogNotice': reason, 'catalogVisibilityPolicy': 'authorized-content-v2'}
        if row.get('catalogVisibilityPolicy') == 'authorized-content-v2':
            row = {key: value for key, value in row.items() if key not in ('catalogHidden', 'catalogNotice', 'catalogVisibilityPolicy')}
    return row
