"""Upcoming basic contests from anonymous, first-party public GET requests.

Nothing starts during application startup. Opening the calendar returns the
previous snapshot immediately and refreshes each provider in its own worker.
"""
import copy
import datetime as dt
import html
import os
import re
import threading
import time

from contest_names import contest_name
from persistence import load_document, save_document
from public_platforms import cf_result, integer, lg_data, text, utc

PLATFORMS = {'codeforces': 'Codeforces', 'atcoder': 'AtCoder', 'nowcoder': '牛客', 'luogu': '洛谷'}


def event(platform, identity, title, start, end, url):
    start, end = utc(start), utc(end)
    if not start or not end or end <= start:
        return None
    return {'id': platform + ':' + str(identity), 'platform': platform,
            'title': title, 'startAt': start, 'endAt': end, 'url': url}


def codeforces(client):
    rows = cf_result(client, 'contest.list?gym=false')
    if not isinstance(rows, list):
        raise ValueError('无法识别 Codeforces 赛程')
    result = []
    for row in rows:
        name = row.get('name', '')
        # Educational and combined Div.1+Div.2 are basic-series rounds too.
        basic = bool(re.search(r'Div\.\s*[234]\b|Div\.\s*1\s*\+\s*(?:Div\.\s*)?2\b|Educational Codeforces', name, re.I))
        start, duration, identity = row.get('startTimeSeconds'), row.get('durationSeconds'), row.get('id')
        if not basic or row.get('phase') != 'BEFORE' or any(integer(value) is None for value in (start, duration, identity)):
            continue
        result.append(event('codeforces', identity, contest_name(name), start, start + duration, f'https://codeforces.com/contest/{identity}'))
    return [row for row in result if row]


def atcoder(client):
    page = client.text('https://atcoder.jp/contests/?lang=en')
    upcoming = re.search(r'id=["\']contest-table-upcoming["\']', page)
    if not upcoming:
        raise ValueError('无法识别 AtCoder 即将开始的比赛')
    table = page[upcoming.end():].split('</tbody>', 1)[0]
    result = []
    for block in re.findall(r'<tr\b[^>]*>.*?</tr>', table, re.S):
        identity = re.search(r'href=["\']/contests/((?:abc|arc)\d+)["\']', block)
        start = re.search(r'<time\b[^>]*>([^<]+)</time>', block)
        duration = re.search(r'<td\b[^>]*>\s*(\d+):(\d\d)\s*</td>', block)
        if not identity or not start or not duration:
            continue
        try:
            began = dt.datetime.strptime(start[1].strip(), '%Y-%m-%d %H:%M:%S%z')
        except ValueError:
            continue
        cid = identity[1]
        title = re.sub(r'^(abc|arc)(\d+)$', lambda match: match[1].upper() + ' ' + str(int(match[2])), cid)
        end = began + dt.timedelta(hours=int(duration[1]), minutes=int(duration[2]))
        result.append(event('atcoder', cid, title, began.isoformat(), end.isoformat(), 'https://atcoder.jp/contests/' + cid))
    return [row for row in result if row]


def nowcoder(client):
    import json
    page = client.text('https://ac.nowcoder.com/acm/contest/vip-index')
    blocks = re.findall(r'<div\b[^>]*data-id="(\d+)"[^>]*data-json="([^"]+)"[^>]*>(.*?)(?=<div\b[^>]*data-id=|$)', page, re.S)
    if not blocks:
        raise ValueError('无法识别牛客赛程')
    result = []
    for identity, encoded, body in blocks:
        try:
            metadata = json.loads(html.unescape(html.unescape(encoded)))
        except ValueError:
            continue
        heading = re.search(r'<h4\b[^>]*>.*?<a\b[^>]*>(.*?)</a>', body, re.S)
        name = text(heading[1]) if heading else ''
        if not re.search(r'(?:小白月赛|练习赛|挑战赛|周赛)\s*(?:Round\s*)?\d+', name):
            continue
        result.append(event('nowcoder', identity, contest_name(name), metadata.get('contestStartTime'), metadata.get('contestEndTime'), 'https://ac.nowcoder.com/acm/contest/' + identity))
    return [row for row in result if row]


def luogu(client):
    from contest_policy import authorized
    from contest_names import regular_contest
    data = lg_data(client.json('https://www.luogu.com.cn/contest/list', headers={'x-lentille-request': 'content-only'}))
    rows = (data.get('contests') or {}).get('result')
    if not isinstance(rows, list):
        raise ValueError('无法识别洛谷赛程')
    result = []
    for row in rows:
        name = row.get('name', '')
        identity = row.get('id')
        series = regular_contest(name)
        if not series or series[0] not in ('月赛', '基础赛', '入门赛') or (row.get('host') or {}).get('id') != 1000 or not authorized({'contest': name}, 'luogu') or integer(identity) is None:
            continue
        result.append(event('luogu', identity, contest_name(name), row.get('startTime'), row.get('endTime'), 'https://www.luogu.com.cn/contest/' + str(identity)))
    return [row for row in result if row]


ADAPTERS = {'codeforces': codeforces, 'atcoder': atcoder, 'nowcoder': nowcoder, 'luogu': luogu}


class ContestCalendar:
    def __init__(self, state_dir, *, client=None, clock=None, offline=None):
        from pathlib import Path
        self.path = Path(state_dir) / 'contest-calendar.json'
        self.stop = threading.Event()
        self.lock = threading.RLock()
        self.clock = clock or time.time
        self.offline = os.environ.get('TB_OFFLINE') == '1' if offline is None else offline
        if client is None:
            from integrations import PublicClient
            client = PublicClient(Path(state_dir) / 'contest-calendar', stop=self.stop)
        self.client = client
        saved = load_document(self.path, {})
        self.providers = {key: saved.get(key, {}) for key in PLATFORMS}
        self.running = set()
        self.attempted = {}

    def snapshot(self, refresh=False):
        now = self.clock()
        with self.lock:
            for key in PLATFORMS:
                cached = self.providers[key]
                stale = now - cached.get('checkedAt', 0) >= 900
                retry = now - self.attempted.get(key, 0) >= 60
                if not self.offline and not self.stop.is_set() and key not in self.running and (refresh or stale and retry):
                    self.running.add(key)
                    self.attempted[key] = now
                    threading.Thread(target=self._refresh, args=(key,), name='TB-calendar-' + key, daemon=True).start()
            timestamp = dt.datetime.fromtimestamp(now, dt.timezone.utc).isoformat()
            contests = {}
            statuses = []
            for key, label in PLATFORMS.items():
                cached = self.providers[key]
                for row in cached.get('contests', []):
                    if row['startAt'] > timestamp:
                        contests[row['id']] = row
                statuses.append({'platform': key, 'label': label, 'status': 'refreshing' if key in self.running else 'offline' if self.offline else cached.get('status', 'pending'),
                                 'checkedAt': cached.get('checkedAt'), 'error': cached.get('error', '')})
            return copy.deepcopy({'contests': sorted(contests.values(), key=lambda row: (row['startAt'], row['id'])), 'providers': statuses,
                                  'refreshing': bool(self.running), 'offline': self.offline})

    def _refresh(self, key):
        try:
            contests = ADAPTERS[key](self.client)
            update = {'contests': contests, 'checkedAt': self.clock(), 'status': 'ready', 'error': ''}
        except (OSError, RuntimeError, ValueError, KeyError, TypeError) as issue:
            update = {'status': 'error', 'error': str(issue)[:180]}
        with self.lock:
            if not self.stop.is_set():
                self.providers[key] = {**self.providers[key], **update}
                try:
                    save_document(self.path, self.providers)
                except (OSError, RuntimeError, ValueError):
                    # A visible result is still useful if the cache cannot be saved.
                    pass
            self.running.discard(key)

    def close(self):
        self.stop.set()
