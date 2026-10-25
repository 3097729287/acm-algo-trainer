import datetime as dt
import unittest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
from library import LibraryDatabase
from assets import AssetLibrary
from insights import build_insights


class ActivityCountsTests(unittest.TestCase):
    def test_bundled_remote_id_fetches_and_caches_statement_without_remote_state(self):
        with tempfile.TemporaryDirectory() as root:
            library = LibraryDatabase(Path(root) / 'library.sqlite3')
            identity = 'remote:codeforces:123456::A'
            url = 'https://codeforces.com/gym/123456/problem/A'
            raw = {'场次': 'ICPC fixture', '题号': 'A', '题名': 'Task', '知识点': '',
                   '难度': '—', '状态': '未做', '日期': '', '_id': identity, '_url': url}
            library.import_records([(raw, {'id': identity, 'url': url}, None, None)], {}, {})
            store = Mock(library=library)
            store.row.return_value = raw
            store._archive_info.return_value = (False, url)
            assets = AssetLibrary(store, Path(root) / 'cache')
            statement = {'id': identity, 'title': 'Task', 'url': url, 'markdown': 'Public task',
                         'samples': [], 'limits': {'timeMs': 1000, 'memoryMb': 256}, 'statementAvailable': True}
            with patch('public_platforms.statement', return_value=statement) as fetch:
                value = assets.problem(identity)
                self.assertTrue(value['statementAvailable'])
                self.assertTrue(assets.problem(identity)['statementAvailable'])
                fetch.assert_called_once()
                store.extensions.statement.assert_not_called()

    def test_daily_first_passes_exclude_repeated_days_and_samples(self):
        rows = [{'id': 'p', 'url': 'https://codeforces.com/gym/123456/problem/A',
                 'tags': [], 'difficulty': 1200}]
        def record(time, scope='official', verdict='AC', identity='p'):
            return {'problem_id': identity, 'mode': 'submit', 'finished_at': time,
                    'submitted_at': time, 'scope': scope, 'verdict': verdict, 'code': 'x'}
        records = [record('2026-10-13T12:00:00Z'), record('2026-10-14T12:00:00Z'),
                   record('2026-10-14T13:00:00Z'), record('2026-10-14T14:00:00Z', 'local'),
                   record('2026-10-15T01:00:00Z', verdict='WA'),
                   record('2026-10-15T02:00:00Z', verdict='SAMPLE_PASS')]
        hub = {'accounts': [{'solved': [
            {'url': rows[0]['url'], 'acceptedAt': '2026-10-13T12:00:00Z'},
            {'url': 'https://codeforces.com/contest/999/problem/B', 'acceptedAt': '2026-10-14T13:00:00Z'},
        ]}]}
        value = build_insights(rows, records, [], {'training': [], 'contests': []}, hub,
                               dt.datetime(2026, 10, 15, 12, tzinfo=dt.timezone.utc))
        days = {entry['date']: entry for entry in value['activity']}
        self.assertEqual(days['2026-10-13']['officialAccepted'], 1)
        self.assertEqual(days['2026-10-14']['officialAccepted'], 1)
        self.assertEqual(days['2026-10-15']['officialAccepted'], 0)
        self.assertEqual(value['summary']['totalSolved'], 2)


class FirstAcRegressionTests(unittest.TestCase):
    def test_unsorted_receipts_aliases_public_evidence_and_beijing_midnight(self):
        rows=[{'id': 'p', 'url': 'https://codeforces.com/contest/9/problem/A', 'tags': [], 'difficulty': 1200},
              {'id': 'alias', 'url': 'https://codeforces.com/problemset/problem/9/A', 'tags': [], 'difficulty': 1200}]
        def record(pid, time):
            return dict(problem_id=pid,mode='submit',scope='official',verdict='AC',code='x',submitted_at=time,finished_at=time)
        records=[record('p','2026-10-26T01:00:00Z'),record('alias','2026-10-25T15:59:00Z'),record('p','2026-10-25T16:00:00Z')]
        hub={'accounts':[{'solved':[{'url':rows[0]['url'],'acceptedAt':'2026-01-01T10:00:00Z'},
                                    {'url':'https://atcoder.jp/contests/abc481/tasks/abc481_b','acceptedAt':'2026-10-25T16:00:00Z'}]},
                         {'solved':[{'url':rows[1]['url'],'acceptedAt':'2026-10-26T02:00:00Z'}]}]}
        result=build_insights(rows,records,[],{},hub,dt.datetime(2026,10,26,12,tzinfo=dt.timezone.utc))
        days={row['date']:row for row in result['activity']}
        self.assertEqual(days['2026-01-01']['officialAccepted'],1)
        self.assertEqual(days['2026-10-25']['officialAccepted'],0)
        self.assertEqual(days['2026-10-26']['officialAccepted'],1)
        self.assertEqual(days['2026-10-26']['submissions'],2)
        self.assertEqual((result['summary']['beforeTodaySolved'],result['summary']['todaySolved'],result['summary']['totalSolved']),(1,1,2))

    def test_first_ac_outside_calendar_window_never_moves_to_repeat_date(self):
        row={'id':'p','url':'https://atcoder.jp/contests/abc100/tasks/abc100_a','tags':[],'difficulty':800}
        records=[dict(problem_id='p',mode='submit',scope='official',verdict='AC',code='x',submitted_at=date,finished_at=date)
                 for date in ['2020-01-01T00:00:00Z','2026-10-26T00:00:00Z']]
        result=build_insights([row],records,[],{}, {},dt.datetime(2026,10,26,12,tzinfo=dt.timezone.utc))
        days={day['date']:day for day in result['activity']}
        self.assertEqual(days['2020-01-01']['officialAccepted'],1)
        self.assertEqual(days['2026-10-26']['officialAccepted'],0)
        self.assertEqual(result['summary']['todaySolved'],0)
        self.assertEqual(result['summary']['totalSolved'],1)


if __name__ == '__main__':
    unittest.main()
