import datetime as dt
from types import SimpleNamespace
import unittest

from official_sync import OfficialSync, cf_receipts
import test_training as fixtures
from training import ServiceError
from contest_names import contest_name


class ReceiptSyncTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    tearDown = fixtures.ServiceTests.tearDown
    completed = fixtures.ServiceTests.completed
    contest = fixtures.ServiceTests.contest

    def sync(self):
        self.library.rows[0]['url'] = 'https://codeforces.com/contest/123/problem/A'
        self.library.extensions = SimpleNamespace(rows=lambda: [], snapshot=lambda: {'settings':{'accounts':{'codeforces':'owner','atcoder':'owner'}}})
        server = SimpleNamespace(store=self.library, training=self.service, accounts=None)
        payload = {'status':'OK','result':[{'id':1234,'problem':{'contestId':123,'index':'A'},'author':{'members':[{'handle':'owner'}]},'verdict':'OK','creationTimeSeconds':int(self.clock.value.timestamp())}]}
        return OfficialSync(server, fetch=lambda _:payload), payload

    def test_official_ac_without_job_backfills_and_deduplicates_with_correct_day(self):
        sync, payload = self.sync()
        sync.once(); sync.once()
        self.assertEqual(self.service.submissions()['total'], 1)
        record = self.service.submissions()['submissions'][0]
        self.assertEqual((record['verdict'], record['scope'], record['code']), ('AC','official',''))
        summary = self.service.workspace()['summary']
        self.assertEqual((summary['todayAccepted'], summary['historicalAccepted']), (1,1))
        self.clock.advance(days=1)
        sync.once()
        self.assertEqual(self.service.workspace()['summary']['todayAccepted'], 0)
        payload['result'][0]['id'] = 1235
        payload['result'][0]['creationTimeSeconds'] = int(self.clock.value.timestamp())
        sync.once()
        summary = self.service.workspace()['summary']
        self.assertEqual((summary['todayAccepted'],summary['historicalAccepted']), (1,1))

    def test_other_owner_and_judging_are_not_final_receipts(self):
        sync, payload = self.sync()
        payload['result'][0]['author']['members'][0]['handle'] = 'someone-else'
        self.assertEqual(cf_receipts(payload,'owner'), [])
        payload['result'][0]['author']['members'][0]['handle'] = 'owner'
        payload['result'][0]['verdict'] = 'TESTING'
        sync.once()
        self.assertEqual(self.service.submissions()['total'], 0)

    def test_pending_fetch_cannot_cross_personal_workspace(self):
        sync, payload = self.sync()
        def changed_owner(_):
            self.library.extensions.snapshot = lambda: {'settings':{'accounts':{'codeforces':'different'}}}
            return payload
        sync.fetch = changed_owner
        sync.once()
        self.assertEqual(self.service.submissions()['total'], 0)

    def test_delete_finished_contest_preserves_code_and_running_contest(self):
        old = self.contest()
        problem = old['slots'][0]['id']
        self.service.save_draft(problem, 'saved contest code', old['id'])
        self.service.finish_contest(old['id'])
        running = self.contest()
        with self.assertRaises(ServiceError): self.service.delete_contests(running['id'])
        result = self.service.delete_contests(all_records=True)
        self.assertEqual(result['deleted'], 1)
        self.assertEqual([c['id'] for c in result['workspace']['contests']], [running['id']])
        self.assertEqual(self.service.connection.execute('SELECT code FROM drafts WHERE context=?',(old['id'],)).fetchone()[0], 'saved contest code')

    def test_results_pagination_excludes_local_runs_and_samples(self):
        self.completed(mode='run',code='AC')
        self.completed(code='AC')
        sync, _ = self.sync(); sync.once()
        result = self.service.submissions(results_only=True, limit=1)
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['submissions'][0]['scope'], 'official')
        self.assertFalse(result['hasMore'])
        self.assertEqual(self.service.submissions()['total'], 3)

    def test_names_preserve_divisions_and_educational_series(self):
        self.assertEqual(contest_name('Codeforces Round 1124 (Div. 1)'), 'Div.1 1124')
        self.assertEqual(contest_name('Educational Codeforces Round 194 (Rated for Div. 2)'), '教育赛 194')
        self.assertEqual(contest_name('[ICPC2019 Yinchuan R] ICPC 2019 区域赛银川站重现赛'), 'ICPC 2019 银川区域赛')
        self.assertEqual(contest_name('Codeforces Round 1000 (Div. 1 + Div. 2)'), 'Div.1+Div.2 1000')

    def test_passive_browser_receipts_require_matching_platform_owner_and_url(self):
        sync, _ = self.sync()
        record={'submissionId':'56789','url':'https://codeforces.com/contest/123/problem/A','verdict':'AC','acceptedAt':self.clock.value.isoformat()}
        self.assertEqual(sync.from_browser({'platform':'Codeforces','owner':'owner','records':[record]})['imported'],1)
        self.assertEqual(sync.from_browser({'platform':'Codeforces','owner':'owner','records':[record]})['imported'],0)
        with self.assertRaises(ServiceError):
            sync.from_browser({'platform':'Codeforces','owner':'someone-else','records':[record]})
        self.assertEqual(sync.from_browser({'platform':'AtCoder','owner':'owner','records':[record]})['imported'],0)

    def test_total_solved_includes_external_known_ac_but_not_sample_runs(self):
        sync, _ = self.sync();sync.once()
        self.completed(mode='run',code='AC')
        result=self.service.insights({'accounts':[{'solved':[{'url':'https://codeforces.com/contest/123/problem/A'}, {'url':'https://codeforces.com/contest/999/problem/Z'}]}]})
        self.assertEqual(result['summary']['totalSolved'],2)
        self.assertEqual(result['summary']['officialSolved'],1)

    def test_contest_roster_is_not_trimmed_by_training_difficulty(self):
        from integrations import IntegrationService
        settings={'minDifficulty':800,'maxDifficulty':1999}
        for rating in (None,3500):
            self.assertTrue(IntegrationService._collectable({'difficulty':rating,'contestProblemCount':7},settings))
        self.assertFalse(IntegrationService._collectable({'difficulty':3500},settings))
