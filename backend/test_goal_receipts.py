"""Discovered contests and owner receipts use disposable account state only."""
import copy
import datetime as dt
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

from goals import Goals
from integrations import PublicClient
from official_sync import OfficialSync
from persistence import load_document
from site_receipts import PublicReceiptSource, atcoder_receipts, luogu_receipts, nowcoder_receipts
from training import TrainingService
import test_training as fixtures


def nc_payload():
    stamp = int(dt.datetime(2026, 10, 18, 13, 30, tzinfo=dt.timezone.utc).timestamp() * 1000)
    return {'code': 0, 'data': {'problemData': [{'problemId': i, 'index': c} for i, c in enumerate('ABCD', 1)],
        'submitDataList': [{'basicInfo': {'contestId': 166}, 'signUpUsers': [{'uid': 42}],
            'submissions': [{'uid': 42, 'problemId': i, 'submissionId': 10000 + i,
                             'status': 5, 'rightCaseRate': 1, 'submitTime': stamp + i * 1000} for i in (1, 2, 3)]}]}}


class GoalReceiptTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    tearDown = fixtures.ServiceTests.tearDown

    def prepare(self):
        self.clock.value = dt.datetime(2026, 10, 10, 4, tzinfo=dt.timezone.utc)
        Goals(self.service).save({'title': '区域赛银牌', 'kind': 'xcpc', 'deadline': '2026-10-30', 'currentRating': 800, 'targetRating': 2000})
        self.clock.value = dt.datetime(2026, 10, 19, 4, tzinfo=dt.timezone.utc)
        for i, row in enumerate(self.library.rows[:4]):
            row.update(platform='牛客', contest='周赛 166', problem='ABCD'[i],
                url=f'https://ac.nowcoder.com/acm/contest/166/{"ABCD"[i]}',
                endedAt='2026-10-18T14:00:00+00:00', addedAt=self.clock.value.isoformat())
        bindings = {'codeforces': '', 'nowcoder': '42', 'atcoder': '', 'luogu': ''}
        self.library.extensions = SimpleNamespace(rows=lambda: [], snapshot=lambda: {'settings': {'accounts': bindings}})
        server = SimpleNamespace(store=self.library, training=self.service, accounts=None)
        sync = OfficialSync(server, fetch=lambda _: self.fail('No CF handle was configured'),
                            site_fetch=lambda site, owner, rows: nowcoder_receipts(nc_payload(), owner, '166'))
        return sync, bindings

    def test_sunday_ac_discovered_on_monday_keeps_original_day_and_ids(self):
        sync, _ = self.prepare()
        self.assertEqual(sync.once()['imported'], 3)
        self.assertEqual(sync.once()['imported'], 0)
        workspace = self.service.workspace()
        self.assertEqual((workspace['summary']['historicalAccepted'], workspace['summary']['todayAccepted']), (3, 0))
        task = {r['problem']: r for r in workspace['training'] if r['contest'] == '周赛 166' and r.get('reviewTask')}
        self.assertEqual({k: v['accepted'] for k, v in task.items()}, {'A': True, 'B': True, 'C': True})
        self.assertEqual(workspace['goalTasks'], [], 'due reviews take priority over new automatic recommendations')
        self.assertEqual(self.service.submissions()['total'], 3)
        self.assertTrue(all(r['submittedAt'].startswith('2026-10-18') for r in self.service.submissions()['submissions']))
        self.assertEqual(workspace['goals']['goals'][0]['progress'], 3)
        self.assertTrue(all(row['today'] for row in workspace['training'] if row['id'] in {t['id'] for t in task.values()}))
        self.assertFalse(any(s['id'].startswith('goal-contest:') for s in workspace['sets']))

    def test_frozen_contest_tasks_survive_restart_and_manual_clear(self):
        sync, _ = self.prepare()
        self.service.workspace() # freeze the new contest before its ACs arrive
        frozen = [tuple(r) for r in self.service.connection.execute('SELECT * FROM practice_sets ORDER BY id')]
        sync.once()
        self.service.clear_training()
        self.assertEqual(self.service.workspace()['training'], [])
        self.service.close()
        self.service = TrainingService(self.library, self.db, self.assets, self.judge, self.clock, self.root / 'backups')
        self.assertEqual([tuple(r) for r in self.service.connection.execute('SELECT * FROM practice_sets ORDER BY id')], frozen)
        self.assertEqual(self.service.workspace()['training'], [])

    def test_matching_all_four_families_ignores_unrelated_old_and_future_events(self):
        self.prepare()
        samples = [('Codeforces', 'Div.3 1000', 'https://codeforces.com/contest/1000/problem/A'),
                   ('AtCoder', 'ABC 500', 'https://atcoder.jp/contests/abc500/tasks/abc500_a'),
                   ('洛谷', '基础赛 40', 'https://www.luogu.com.cn/problem/P20000')]
        for i, (platform, contest, url) in enumerate(samples, 4):
            self.library.rows[i].update(platform=platform, contest=contest, url=url, problem='A',
                endedAt='2026-10-18T14:00:00+00:00', addedAt=self.clock.value.isoformat())
        tasks = self.service.workspace()['goalTasks']
        self.assertEqual({row['platform'] for row in tasks if '比赛目标' in row['sources']}, {'Codeforces', 'AtCoder', '牛客', '洛谷'})
        # New unrelated/future events must not be introduced as contest tasks.
        other = self.library.rows[7]
        other.update(platform='牛客', contest='练习赛 123', url='https://ac.nowcoder.com/acm/contest/123/A', problem='A', addedAt=self.clock.value.isoformat())
        self.assertNotIn(other['id'], {r['id'] for r in self.service.workspace()['goalTasks'] if '比赛目标' in r['sources']})
        other.update(contest='周赛 999', endedAt='2026-10-20T14:00:00+00:00')
        self.assertNotIn(other['id'], {r['id'] for r in self.service.workspace()['goalTasks'] if '比赛目标' in r['sources']})

    def test_unknown_task_receipts_are_retained_until_catalogue_arrives(self):
        sync, _ = self.prepare()
        old_url = self.library.rows[0].pop('url')
        self.assertEqual(sync.once()['imported'], 2)
        self.library.rows[0]['url'] = old_url
        sync.site_fetch = lambda *_: (_ for _ in ()).throw(OSError('unavailable'))
        status = sync.once()
        self.assertEqual(status['imported'], 1)
        self.assertEqual(self.service.workspace()['summary']['historicalAccepted'], 3)
        self.assertEqual(status['platforms'][0]['status'], 'error')

    def test_inflight_fetch_cannot_change_owner_or_workspace(self):
        sync, bindings = self.prepare()
        def changed(*_):
            bindings['nowcoder'] = '999'
            return nowcoder_receipts(nc_payload(), '42', '166')
        sync.site_fetch = changed; sync.once()
        self.assertEqual(self.service.submissions()['total'], 0)


class PublicReceiptTests(unittest.TestCase):
    def test_nowcoder_rejects_other_owner_contest_partial_pending_and_team(self):
        value = nc_payload()
        group = value['data']['submitDataList'][0]
        original = copy.deepcopy(group['submissions'][0])
        for patch in ({'uid': 99}, {'rightCaseRate': .5}, {'status': 1}, {'submissionId': 'made-up'}, {'submitTime': 9999999999999}):
            group['submissions'].append({**original, **patch})
        value['data']['submitDataList'].append({**copy.deepcopy(group), 'basicInfo': {'contestId': 167}})
        self.assertEqual(len(nowcoder_receipts(value, '42', '166')), 3)
        group['signUpUsers'][0]['team'] = True
        self.assertEqual(nowcoder_receipts(value, '42', '166'), [])

    def test_atcoder_and_luogu_require_real_owner_and_terminal_record(self):
        stamp = 1792320000
        at = [{'id': 123, 'user_id': 'owner', 'contest_id': 'abc500', 'problem_id': 'abc500_a', 'result': 'AC', 'epoch_second': stamp},
              {'id': 124, 'user_id': 'other', 'contest_id': 'abc500', 'problem_id': 'abc500_b', 'result': 'AC', 'epoch_second': stamp}]
        self.assertEqual([r['submissionId'] for r in atcoder_receipts(at, 'OWNER')], ['123'])
        lg = {'status': 200, 'data': {'records': {'result': [
            {'id': 123, 'user': {'uid': 42}, 'problem': {'pid': 'P1000'}, 'status': 12, 'submitTime': stamp},
            {'id': 124, 'user': {'uid': 42}, 'problem': {'pid': 'P1001'}, 'status': 0, 'submitTime': stamp},
            {'id': 125, 'user': {'uid': 43}, 'problem': {'pid': 'P1002'}, 'status': 12, 'submitTime': stamp}]}}}
        self.assertEqual([r['submissionId'] for r in luogu_receipts(lg, '42')], ['123'])

    def test_public_cache_retains_only_requested_owner(self):
        value = nc_payload()
        value['data']['submitDataList'][0]['submissions'].append({**value['data']['submitDataList'][0]['submissions'][0], 'uid': 99, 'submissionId': 99999})
        url = 'https://ac.nowcoder.com/acm/contest/rank/submit-list?currentContestId=166'
        with tempfile.TemporaryDirectory() as root:
            calls = []
            client = PublicClient(root, spacing=0, transport=lambda *_: (calls.append(1) or json.dumps(value).encode(), None))
            def read(owner): return client.owner_json(url, owner, lambda payload: nowcoder_receipts(payload, owner, '166'))
            self.assertEqual(len(read('42')), 3); read('42')
            self.assertEqual(len(calls), 1)
            self.assertEqual(len(read('99')), 1)
            for owner in ('42', '99'):
                cache = client.directory / (hashlib.sha256((url + '\0owner-receipts-v1:' + owner).encode()).hexdigest() + '.json')
                saved = load_document(cache, {})
                self.assertEqual({r['owner'] for r in json.loads(saved['text'])}, {owner})
                self.assertNotIn('submitDataList', saved['text'])

    def test_atcoder_recent_window_does_not_stop_at_first_lifetime_submissions(self):
        calls = []
        client = SimpleNamespace(json=lambda url: calls.append(url) or [])
        PublicReceiptSource(client).fetch('atcoder', 'owner', [])
        self.assertGreater(int(parse_qs(urlsplit(calls[0]).query)['from_second'][0]), 0)


if __name__ == '__main__':
    unittest.main()
