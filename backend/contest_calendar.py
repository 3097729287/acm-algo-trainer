"""Upcoming basic contests from anonymous, first-party public GET requests.

Cached schedules return immediately. A bounded background worker imports
announced tasks when the contest starts; unavailable sources retry later.
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
        if not basic or row.get('phase') not in ('BEFORE', 'CODING') or any(integer(value) is None for value in (start, duration, identity)):
            continue
        result.append(event('codeforces', identity, contest_name(name), start, start + duration, f'https://codeforces.com/contest/{identity}'))
    return [row for row in result if row]


def atcoder(client):
    page = client.text('https://atcoder.jp/contests/?lang=en')
    upcoming = re.search(r'id=["\']contest-table-(?:upcoming|active)["\']', page)
    if not upcoming:
        raise ValueError('无法识别 AtCoder 即将开始的比赛')
    table = '\n'.join(page[match.end():].split('</tbody>', 1)[0] for match in re.finditer(r'id=["\']contest-table-(?:upcoming|active)["\']', page))
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
    def __init__(self, state_dir, *, client=None, clock=None, offline=None, importer=None):
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
        self.importer = importer
        self.import_path = Path(state_dir) / 'contest-imports.json'
        self.imports = load_document(self.import_path, {})
        self.import_running = set()
        self.manual_import_attempted = {}
        self.scheduler = None

    def start(self):
        if self.offline or self.scheduler is not None:
            return
        self.scheduler = threading.Thread(target=self._schedule, name='TB-contest-start', daemon=True)
        self.scheduler.start()

    def _schedule(self):
        while not self.stop.is_set():
            self.snapshot()
            with self.lock:
                future=[dt.datetime.fromisoformat(row['startAt']).timestamp()-self.clock()
                        for provider in self.providers.values() for row in provider.get('contests',[])
                        if dt.datetime.fromisoformat(row['startAt']).timestamp()>self.clock()]
            self.stop.wait(max(.05,min([15,*future])))

    def ongoing(self, identity):
        """Resolve a cached first-party event; callers cannot supply a deadline."""
        from training import ServiceError
        with self.lock:
            row=next((row for provider in self.providers.values() for row in provider.get('contests',[])
                      if row['id']==identity),None)
            if row is None:raise ServiceError(404,'没有找到这场公开比赛，请刷新赛程')
            now=self.clock()
            if not dt.datetime.fromisoformat(row['startAt']).timestamp()<=now<dt.datetime.fromisoformat(row['endAt']).timestamp():
                raise ServiceError(409,'这场比赛尚未开始或已经结束')
            imported=self.imports.get(identity,{})
            if imported.get('status')!='ready':raise ServiceError(409,'完整题面尚未就绪，请稍后重试')
            return {**copy.deepcopy(row),'contest':imported.get('title') or row['title']}

    def import_due(self, refresh=False):
        if self.offline or self.stop.is_set() or self.importer is None:
            return
        from contest_imports import SCHOOL_CONTESTS
        now = self.clock()
        with self.lock:
            events = {row['id']: row for provider in self.providers.values() for row in provider.get('contests', [])}
            events.update({row['id']: dict(row) for row in SCHOOL_CONTESTS})
            def priority(item):
                identity, row = item
                started = row.get('startAt') and dt.datetime.fromisoformat(row['startAt']).timestamp() <= now
                ongoing = started and row.get('endAt') and now < dt.datetime.fromisoformat(row['endAt']).timestamp()
                return (0 if ongoing else 1, self.imports.get(identity, {}).get('checkedAt', 0), identity)
            for identity, row in sorted(events.items(), key=priority):
                if row.get('startAt') and dt.datetime.fromisoformat(row['startAt']).timestamp() > now:
                    continue
                # Stale schedules are not a request to crawl the entire archive.
                if row.get('endAt') and dt.datetime.fromisoformat(row['endAt']).timestamp() + 86400 < now:
                    continue
                old = self.imports.get(identity, {})
                ongoing = row.get('endAt') and now < dt.datetime.fromisoformat(row['endAt']).timestamp()
                manual = refresh and ongoing and now - self.manual_import_attempted.get(identity, float('-inf')) >= 15
                moved = old.get('scheduledStartAt') is not None and old.get('scheduledStartAt') != row.get('startAt')
                if old.get('status') == 'ready' or identity in self.import_running or not (manual or moved) and now < old.get('retryAt', 0):
                    continue
                # One source operation at a time; rate limiting is also shared with sync.
                if self.import_running:
                    break
                if manual:
                    self.manual_import_attempted[identity] = now
                self.import_running.add(identity)
                threading.Thread(target=self._import, args=(copy.deepcopy(row),), name='TB-contest-import', daemon=True).start()

    def _import(self, event):
        identity = event['id']
        try:
            result = self.importer(event)
            if not isinstance(result, dict):
                raise ValueError('原站导入结果无效，请稍后重试')
        except (OSError, ValueError, RuntimeError, KeyError, TypeError, AttributeError) as issue:
            result = {'status': 'error', 'error': str(issue)[:350]}
        with self.lock:
            old = self.imports.get(identity, {})
            attempts = (old.get('attempts', 0) if old.get('scheduledStartAt', event.get('startAt')) == event.get('startAt') else 0) + 1
            now = self.clock()
            ongoing = event.get('endAt') and now < dt.datetime.fromisoformat(event['endAt']).timestamp()
            # Live contests last only a few hours. Do not spend that window
            # waiting 2/4/8/16 minutes after a pre-publication response.
            opening_window = event.get('startAt') and now - dt.datetime.fromisoformat(event['startAt']).timestamp() < 600
            if ongoing and opening_window and attempts <= 8:
                delay = min(60, 15 * 2 ** min(attempts - 1, 2))
            elif ongoing:
                delay = 300
            else:
                delay = min(3600, 60 * 2 ** min(attempts, 6))
            result.update(id=identity, url=event['url'], title=result.get('title') or event['title'],
                          checkedAt=now, retryAt=now + delay, attempts=attempts,
                          scheduledStartAt=event.get('startAt'))
            try:
                if not self.stop.is_set():
                    self.imports[identity] = result
                    save_document(self.import_path, self.imports)
            except (OSError, RuntimeError, ValueError):
                result['error'] = '导入结果暂时无法保存，重启后将重新核验'
            finally:
                self.import_running.discard(identity)

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
            # Opening/refreshing the calendar at the start boundary can launch
            # one bounded import immediately; it never waits for network I/O.
            self.import_due(refresh=refresh)
            contests = {}
            statuses = []
            for key, label in PLATFORMS.items():
                cached = self.providers[key]
                for row in cached.get('contests', []):
                    if row['endAt'] > timestamp:
                        contests[row['id']] = dict(row)
                        if row['id'] in self.imports:
                            contests[row['id']]['import'] = self.imports[row['id']]
                statuses.append({'platform': key, 'label': label, 'status': 'refreshing' if key in self.running else 'offline' if self.offline else cached.get('status', 'pending'),
                                 'checkedAt': cached.get('checkedAt'), 'error': cached.get('error', '')})
            return copy.deepcopy({'contests': sorted(contests.values(), key=lambda row: (row['startAt'], row['id'])), 'providers': statuses,
                                  'imports': list(self.imports.values()), 'importing': bool(self.import_running),
                                  'refreshing': bool(self.running), 'offline': self.offline})

    def _refresh(self, key):
        try:
            contests = ADAPTERS[key](self.client)
            with self.lock:
                retained = {row['id']: row for row in self.providers[key].get('contests', []) if dt.datetime.fromisoformat(row['endAt']).timestamp() + 86400 > self.clock()}
            retained.update({row['id']: row for row in contests})
            update = {'contests': list(retained.values()), 'checkedAt': self.clock(), 'status': 'ready', 'error': ''}
        except (OSError, RuntimeError, ValueError, KeyError, TypeError, AttributeError) as issue:
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
