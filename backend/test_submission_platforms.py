"""Real SQL platform filtering over temporary histories, aliases and retired facts."""
import json
import unittest
from urllib.parse import urlencode
from unittest.mock import patch

import test_training as F
from training import ServiceError, iso


class SubmissionPlatformTests(unittest.TestCase):
    tearDown = F.ServiceTests.tearDown

    def setUp(self):
        F.ServiceTests.setUp(self)
        platforms = ['QOJ', 'Codeforces', 'AtCoder', '牛客', '洛谷', 'FutureJudge', 'unknown', '']
        urls = ['https://qoj.ac/problem/15032', 'https://codeforces.com/contest/777/problem/A',
                'https://atcoder.jp/contests/abc777/tasks/abc777_a', 'https://ac.nowcoder.com/acm/contest/777/A',
                'https://www.luogu.com.cn/problem/P777', 'https://future.example/problem/A', '', '']
        for row, platform, url in zip(self.library.rows, platforms, urls):
            row.update(platform=platform, url=url, source='archive')
        self.library.rows[0]['aliasIds'] = ['old-qoj']
        # Canonical original identity wins over a differently labelled mirror.
        self.library.rows.append(dict(self.library.rows[0], id='mirror-qoj', platform='洛谷', source='remote', aliasIds=[]))
        timestamp = iso(self.clock())
        self.service.connection.execute('INSERT INTO account_problem_facts VALUES(?,?,?)',
            ('retired-qoj', json.dumps({'row': {'id': 'retired-qoj', 'platform': 'QOJ', 'url': 'https://qoj.ac/problem/99999', 'title': 'Retired task'}}), timestamp))
        for index, pid in enumerate([*[r['id'] for r in self.library.rows[:8]], 'old-qoj', 'mirror-qoj',
                                     'remote:codeforces:777::A', 'retired-qoj', 'unresolved-orphan']):
            self.service.connection.execute('INSERT INTO submissions(id,problem_id,mode,code,submitted_at,finished_at,verdict,scope,output,stderr) VALUES(?,?,?,?,?,?,?,?,?,?)',
                (f's{index:02}', pid, 'submit', 'PRIVATE exact source\n' * 3000, timestamp, timestamp,
                 'WA' if pid == 'old-qoj' else 'AC', 'official', 'PRIVATE output', 'PRIVATE stderr'))

    def test_each_real_platform_is_filtered_before_count_and_paging(self):
        expected = {'QOJ': {'fixture::A', 'old-qoj', 'mirror-qoj', 'retired-qoj'},
                    'Codeforces': {'fixture::B', 'remote:codeforces:777::A'},
                    'AtCoder': {'fixture::C'}, '牛客': {'fixture::D'}, '洛谷': {'fixture::E'},
                    'FutureJudge': {'fixture::F'}, 'unknown': {'fixture::G'}}
        for platform, identities in expected.items():
            with self.subTest(platform=platform):
                pages = [self.service.submissions(platform=platform, compact=True, limit=1, offset=i, order='asc') for i in range(len(identities) + 1)]
                self.assertEqual({p['total'] for p in pages}, {len(identities)})
                self.assertEqual({s['problemId'] for p in pages for s in p['submissions']}, identities)
                self.assertEqual([p['hasMore'] for p in pages], [i + 1 < len(identities) for i in range(len(identities) + 1)])
                self.assertTrue(all(s['platform'] == platform for p in pages for s in p['submissions']))
                self.assertEqual(pages[-1]['submissions'], [])

    def test_aliases_return_canonical_public_metadata_without_private_blobs(self):
        queries = []
        self.service.connection.set_trace_callback(queries.append)
        try:
            result = self.service.submissions(platform=' qOj ', compact=True, limit=100)
        finally:
            self.service.connection.set_trace_callback(None)
        self.assertEqual(result['total'], 4)
        for row in result['submissions']:
            self.assertTrue(row['codePending'])
            self.assertTrue(row['url'].startswith('https://qoj.ac/problem/'))
            self.assertFalse({'code', 'output', 'stderr', 'message', 'caseResults'} & row.keys())
            if row['problemId'] != 'retired-qoj':
                self.assertEqual(row['canonicalProblemId'], 'fixture::A')
        selects = [query.lower() for query in queries if query.lower().startswith('select') and 'from submissions' in query.lower()]
        self.assertTrue(any('count(*)' in query and 'json_each' in query for query in selects))
        self.assertTrue(any('limit 100 offset 0' in query and 'json_each' in query for query in selects))
        self.assertTrue(all('select *' not in query and not any(blob in query.split('from submissions')[0] for blob in ('code', 'output', 'stderr')) for query in selects))
        self.assertEqual(self.service.connection.execute('SELECT code FROM submissions WHERE id=?', ('s00',)).fetchone()[0], 'PRIVATE exact source\n' * 3000)

    def test_platform_combines_with_verdict_identity_and_ascending_results(self):
        result = self.service.submissions(platform='QOJ', verdict='WA', results_only=True, compact=True)
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['submissions'][0]['problemId'], 'old-qoj')
        result = self.service.submissions(identity='fixture::A', platform='QOJ', compact=True)
        self.assertEqual(result['total'], 3)
        self.assertEqual(self.service.submissions(identity='fixture::A', platform='洛谷')['total'], 0)
        # Familiar spellings are canonicalized; unrelated future names stay exact.
        for label, count in [('cf', 2), ('AtCoDeR', 1), ('nowcoder', 1), ('luogu', 1), ('futurejudge', 0)]:
            self.assertEqual(self.service.submissions(platform=label)['total'], count)

    def test_unknown_or_hostile_strings_never_disable_the_filter(self):
        for value in ["QOJ' OR 1=1 --", 'QOJ%_', 'QOJ\x00', 'not-a-platform']:
            with self.subTest(value=value):
                self.assertEqual(self.service.submissions(platform=value, compact=True)['total'], 0)
        for value in [None, 1, False, [], 'x' * 81]:
            with self.subTest(value=value), self.assertRaises(ServiceError) as error:
                self.service.submissions(platform=value)
            self.assertEqual(error.exception.status, 400)
        self.assertEqual(self.service.submissions(platform='', compact=True)['total'], 13)
        self.assertEqual(self.service.submissions(platform='QOJ', limit=1, offset=1000000)['total'], 4)
        with self.assertRaises(ServiceError):
            self.service.submissions(platform='QOJ', limit=101)


class SubmissionPlatformHTTPTests(unittest.TestCase):
    setUp = F.HTTPTests.setUp
    tearDown = F.HTTPTests.tearDown
    request = F.HTTPTests.request

    def test_get_passes_platform_to_real_filtered_count_and_compact_metadata(self):
        timestamp = iso(self.clock())
        self.server.training.connection.execute('INSERT INTO submissions(id,problem_id,mode,code,submitted_at,finished_at,verdict,scope) VALUES(?,?,?,?,?,?,?,?)',
            ('http-platform', 'http-qoj', 'submit', 'PRIVATE', timestamp, timestamp, 'AC', 'official'))
        rows = [{'id': 'http-qoj', 'platform': 'QOJ', 'title': 'HTTP task', 'url': 'https://qoj.ac/problem/15032'}]
        with patch.object(self.server.training, '_library', return_value=rows):
            for platform, expected in [('QOJ', 1), ('Codeforces', 0), ("QOJ' OR 1=1 --", 0)]:
                status, value = self.request('GET', '/api/submissions?' + urlencode({'platform': platform, 'compact': 1, 'limit': 1}))
                self.assertEqual(status, 200)
                self.assertEqual(value['total'], expected)
                if expected:
                    self.assertEqual(value['submissions'][0]['platform'], 'QOJ')
                    self.assertNotIn('code', value['submissions'][0])


if __name__ == '__main__':
    unittest.main()
