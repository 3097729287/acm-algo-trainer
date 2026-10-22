"""First-party future schedules, failures, time zones and nonblocking cache."""
import datetime as dt
import html
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import contest_calendar as C


class Client:
    def __init__(self, payload):
        self.payload = payload

    def json(self, *args, **kwargs):
        return self.payload

    def text(self, *args, **kwargs):
        return self.payload


class CalendarTests(unittest.TestCase):
    def test_cf_only_announced_basic_rounds_including_educational_and_combined(self):
        names = ['Codeforces Round 1128 (Div. 2)', 'Codeforces Round 1129 (Div. 3)', 'Codeforces Round 1130 (Div. 4)',
                 'Educational Codeforces Round 200 (Rated for Div. 2)', 'Codeforces Round 1131 (Div. 1 + Div. 2)',
                 'Codeforces Round 1131 (Div. 1)', 'IOI Challenge', 'Codeforces Global Round 30']
        rows = [dict(id=index+1, name=name, phase='BEFORE', startTimeSeconds=1800000000, durationSeconds=7200) for index, name in enumerate(names)]
        rows.append({**rows[0], 'id': 20, 'phase': 'FINISHED'})
        events = C.codeforces(Client({'status': 'OK', 'result': rows}))
        self.assertEqual(len(events), 5)
        self.assertTrue(all(event['startAt'].endswith('+00:00') for event in events))
        self.assertEqual(events[0]['endAt'], C.utc(1800007200))

    def test_atcoder_scopes_upcoming_and_converts_japan_time(self):
        def row(cid):
            return f'<tr><td><time>2026-10-24 21:00:00+0900</time></td><td><a href="/contests/{cid}">Contest</a></td><td>01:40</td></tr>'
        page = '<div id="contest-table-upcoming"><tbody>' + ''.join(row(cid) for cid in ('abc481', 'arc233', 'agc100', 'ahc099')) + '</tbody></div>' + row('abc480')
        events = C.atcoder(Client(page))
        self.assertEqual([event['title'] for event in events], ['ABC 481', 'ARC 233'])
        self.assertEqual(events[0]['startAt'], '2026-10-24T12:00:00+00:00')
        self.assertEqual(events[0]['endAt'], '2026-10-24T13:40:00+00:00')

    def test_nowcoder_uses_contest_time_instead_of_registration_time(self):
        def block(identity, name):
            metadata = html.escape(json.dumps({'contestStartTime': 1800000000000, 'contestEndTime': 1800007200000}), quote=True)
            return f'<div data-id="{identity}" data-json="{metadata}"><h4><a>{name}</a></h4><div>报名时间 2000-01-01</div></div>'
        page = ''.join(block(index, name) for index, name in enumerate(('牛客周赛 Round 167', '牛客小白月赛139', '牛客练习赛159', '牛客挑战赛93', '娱乐赛99')))
        events = C.nowcoder(Client(page))
        self.assertEqual(len(events), 4)
        self.assertEqual(events[0]['startAt'], C.utc(1800000000))

    def test_luogu_excludes_unofficial_and_advanced_rounds(self):
        rows = [{'id': index + 1, 'name': name, 'host': {'id': host}, 'startTime': 1800000000, 'endTime': 1800007200}
                for index, (name, host) in enumerate([('洛谷月赛 LGR-311 Div.2', 1000), ('洛谷入门赛 53 Div.4', 1000), ('洛谷基础赛 41 Div.3', 1000), ('洛谷月赛 LGR-311 Div.1', 1000), ('洛谷入门赛 54', 123), ('ICPC 2019 南昌区域赛重现赛', 1000)])]
        events = C.luogu(Client({'status': 200, 'data': {'contests': {'result': rows}}}))
        self.assertEqual(len(events), 3)

    def test_cached_future_events_return_before_network_and_survive_failed_refresh(self):
        with tempfile.TemporaryDirectory(prefix='tb-calendar-') as directory:
            now = 1792800000
            calendar = C.ContestCalendar(directory, client=Client(None), clock=lambda: now, offline=False)
            old = C.event('codeforces', 1, 'Div.2 1128', now+3600, now+7200, 'https://codeforces.com/contest/1')
            past = C.event('codeforces', 2, 'Div.2 1127', now-3600, now, 'https://codeforces.com/contest/2')
            calendar.providers['codeforces'] = {'contests': [old, past], 'checkedAt': now-1000}
            entered = threading.Event()
            release = threading.Event()
            def failing(client):
                entered.set()
                release.wait(2)
                raise ValueError('Provider unavailable')
            adapters = {key: failing for key in C.PLATFORMS}
            with patch.dict(C.ADAPTERS, adapters):
                began = time.monotonic()
                snapshot = calendar.snapshot()
                self.assertLess(time.monotonic()-began, .3)
                self.assertEqual(snapshot['contests'], [old])
                self.assertTrue(snapshot['refreshing'])
                self.assertTrue(entered.wait(1))
                release.set()
                deadline = time.monotonic()+3
                while calendar.snapshot()['refreshing'] and time.monotonic() < deadline:
                    time.sleep(.01)
                snapshot = calendar.snapshot()
                self.assertFalse(snapshot['refreshing'])
                self.assertEqual(snapshot['contests'], [old])
                self.assertTrue(all(provider['status'] == 'error' for provider in snapshot['providers']))
            calendar.close()
            reopened = C.ContestCalendar(directory, client=Client(None), clock=lambda: now, offline=True)
            self.assertEqual(reopened.snapshot()['contests'], [old])
            self.assertFalse(reopened.running)
            reopened.close()


if __name__ == '__main__':
    unittest.main()
