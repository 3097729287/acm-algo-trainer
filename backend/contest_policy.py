"""Public catalogue scope; retained personal evidence is never removed."""
from functools import lru_cache
import json
import re

MIN_XCPC_YEAR = 2017


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


def apply_visibility(row):
    if retired(row):
        return {**row, 'catalogHidden': True, 'catalogNotice': '已退出自动收录范围；个人训练与历史记录保留'}
    return row
