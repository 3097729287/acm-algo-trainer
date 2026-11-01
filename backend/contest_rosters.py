"""Reviewed first-party roster evidence for existing cached public contest rows."""
import json
import re
from functools import lru_cache
from paths import resource

@lru_cache(maxsize=1)
def _load(stamp):
    try:return json.loads(resource('reviewed-contest-rosters.json').read_text('utf8')).get('contests',{})
    except (OSError,ValueError):return {}

def annotate(row):
    match=re.fullmatch(r'https://(?:www\.)?codeforces.com/contest/(\d+)/problem/([A-Za-z0-9]+)',row.get('url') or '')
    if not match:return row
    path=resource('reviewed-contest-rosters.json')
    try:stamp=(path.stat().st_size,path.stat().st_mtime_ns)
    except OSError:return row
    evidence=_load(stamp).get(match[1])
    if evidence and match[2] in {str(item.get('index')) for item in evidence['problems']}:
        return {**row,'contestRoster':True,'contestProblemCount':len(evidence['problems']),'contestRosterSource':evidence['source']}
    return row
