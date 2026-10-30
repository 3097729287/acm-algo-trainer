"""Small isolated journals and the actual asynchronous template-judge boundary."""
import copy
import json
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import test_training as fixtures
from account_sync import merge_states, baselines, AccountStateSync
from experience_challenge import KEY, PROBLEMS, read, merge, preserve_rows, update
from preferences import save_preferences
from training import ServiceError


class ChallengeTests(unittest.TestCase):
    accept = fixtures.ServiceTests.accept
    completed = fixtures.ServiceTests.completed

    def setUp(self):
        fixtures.ServiceTests.setUp(self)
        self.library.rows.extend(dict(id=p, contest='模板练习', problem='1', title=p,
                                      difficulty=1000, platform='ToBe', templatePractice=True,
                                      tags=['二分']) for p in PROBLEMS)
        original = self.assets.problem
        self.assets.problem = lambda identity: dict(original(identity), **({'judge': {'scope': 'template', 'cases': 24}, 'templatePractice': True} if identity in PROBLEMS else {}))
        self.judge.execute = self.judge_drill

    def tearDown(self):
        fixtures.ServiceTests.tearDown(self)

    @staticmethod
    def judge_drill(identity, code, mode='submit', **kwargs):
        verdict = 'WA' if code == 'wrong' else 'AC'
        count = 23 if code == 'partial' else 24
        cases = [{'verdict': 'SAMPLE_PASS', 'name': str(i)} for i in range(1 if code == 'missing-proof' else count)]
        return dict(verdict=verdict, scope='template', passed=count if verdict == 'AC' else 0,
                    total=24, caseResults=cases)

    def choose(self):
        with patch('experience_challenge.secrets.choice', return_value=PROBLEMS[0]):
            return update(self.service, {'action': 'choose', 'choice': 'experienced'})

    def pass_challenge(self):
        self.choose()
        self.completed(PROBLEMS[0], code='correct')
        return self.service.insights()['growth']

    def test_legacy_low_level_offer_is_owner_scoped_and_acknowledged_once(self):
        initial = self.service.insights()['growth']
        self.assertEqual(initial['level'], 1)
        self.assertTrue(initial['experienceChallenge']['promptRequired'])
        answer = update(self.service, {'action': 'seen'})
        self.assertFalse(answer['challenge']['promptRequired'])
        self.assertEqual(answer['challenge']['owner'], initial['authority']['owner'])
        update(self.service, {'action': 'choose', 'choice': 'beginner'})
        retry = update(self.service, {'action': 'choose', 'choice': 'experienced'})
        self.assertEqual(retry['challenge']['choice'], 'beginner')
        self.assertEqual(retry['growth']['totalXp'], initial['totalXp'])
        self.assertFalse(retry['challenge']['allNavigationUnlocked'])

    def test_assignment_is_durable_and_repeated_choice_does_not_change_it(self):
        self.choose()
        initial = read(self.service)
        self.service.close()
        self.service = type(self.service)(self.library, self.db, self.assets, self.judge, self.clock, self.root / 'backups')
        with patch('experience_challenge.secrets.choice', side_effect=AssertionError('reassigned')):
            self.choose()
        self.assertEqual(read(self.service), initial)
        with self.assertRaises(ServiceError):
            update(self.service, {'action': 'choose', 'choice': 'experienced', 'level': 5})
        with self.assertRaises(ServiceError):
            save_preferences(self.service, {'preferences': {'experienceChallenge': {'passed': True}}})

    def test_only_full_bound_submission_grants_once_and_normal_xp_still_accumulates(self):
        before = self.service.insights()['growth']
        granted = self.pass_challenge()
        self.assertEqual(granted['level'], 5)
        self.assertEqual(granted['totalXp'], 500)
        self.assertEqual(granted['challengeXp'], 500 - before['totalXp'])
        self.assertTrue(granted['experienceChallenge']['allNavigationUnlocked'])
        self.assertGreater(granted['authority']['revision'], before['authority']['revision'])
        self.assertEqual(granted['authority']['owner'], before['authority']['owner'])
        self.assertEqual(self.service.connection.execute('SELECT COUNT(*) FROM official_first_xp_awards').fetchone()[0], 0)
        self.completed(PROBLEMS[0], code='correct')
        self.assertEqual(self.service.insights()['growth']['totalXp'], 500)
        self.accept()
        later = self.service.insights()['growth']
        self.assertGreater(later['totalXp'], 500)
        self.assertEqual(later['challengeXp'], granted['challengeXp'])
        self.assertTrue(later['experienceChallenge']['allNavigationUnlocked'])

    def test_real_python_binary_search_full_judge_grants_from_all_24_cases(self):
        self.native_challenge(PROBLEMS[0], '''import bisect,sys
v=list(map(int,sys.stdin.buffer.read().split()));n,q=v[:2];a=v[2:2+n]
print(*(bisect.bisect_left(a,x) for x in v[2+n:]))
''')

    def test_real_python_prefix_sum_full_judge_grants_from_all_24_cases(self):
        self.native_challenge(PROBLEMS[1], '''import sys
v=list(map(int,sys.stdin.buffer.read().split()));n,q=v[:2];p=[0]
for x in v[2:2+n]:p.append(p[-1]+x)
print(*(p[v[i+1]]-p[v[i]] for i in range(2+n,len(v),2)))
''')

    def native_challenge(self, problem, code):
        from judge import Judge
        from template_drills import bundle
        self.assets.bundle = bundle
        self.service.judge = Judge(self.assets, self.root / 'native-judge')
        with patch('experience_challenge.secrets.choice', return_value=problem):
            update(self.service, {'action': 'choose', 'choice': 'experienced'})
        answer = self.service.submit(problem, code, language='python3')
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            result = self.service.submission(answer['submission']['id'])['submission']
            if result['finishedAt']:
                break
            time.sleep(.01)
        else:
            self.fail('The actual isolated Python template judge did not finish')
        self.assertEqual((result['verdict'], result['passed'], result['total']), ('AC', 24, 24), result)
        self.assertEqual(len(result['caseResults']), 24)
        growth = self.service.insights()['growth']
        self.assertEqual((growth['level'], growth['totalXp']), (5, 500))
        self.assertTrue(growth['experienceChallenge']['allNavigationUnlocked'])

    def test_samples_wrong_partial_and_missing_full_case_proof_never_grant(self):
        self.completed(PROBLEMS[0], code='correct')  # Before assignment.
        self.choose()
        for code, mode in [('correct', 'run'), ('wrong', 'submit'), ('partial', 'submit'), ('missing-proof', 'submit')]:
            self.completed(PROBLEMS[0], code=code, mode=mode)
            growth = self.service.insights()['growth']
            self.assertFalse(growth['experienceChallenge']['allNavigationUnlocked'], (code, mode))
            self.assertEqual(growth['challengeXp'], 0)
        self.completed(PROBLEMS[1], code='correct')  # Full pass on unassigned ID.
        self.assertFalse(read(self.service)['passedAt'])

    def test_a_foreign_journal_fact_cannot_grant_this_owner(self):
        self.pass_challenge()
        state = read(self.service)
        state['owner'] = '00000000-0000-4000-8000-000000000099'
        with self.service._write() as db:
            db.execute('UPDATE account_preferences SET value=? WHERE key=?', (json.dumps(state), KEY))
        growth = self.service.insights()['growth']
        self.assertFalse(growth['experienceChallenge']['allNavigationUnlocked'])
        self.assertEqual(growth['challengeXp'], 0)

    def test_incomplete_or_inconsistent_reserved_facts_are_not_accepted(self):
        self.pass_challenge()
        valid = read(self.service)
        for field in valid:
            malformed = copy.deepcopy(valid)
            malformed.pop(field)
            with self.service._write() as db:
                db.execute('UPDATE account_preferences SET value=? WHERE key=?', (json.dumps(malformed), KEY))
            growth = self.service.insights()['growth']
            self.assertEqual((growth['level'], growth['challengeXp']), (1, 0), field)
            self.assertTrue(growth['experienceChallenge']['promptRequired'])
        malformed = copy.deepcopy(valid)
        malformed['choice'] = 'beginner'
        with self.service._write() as db:
            db.execute('UPDATE account_preferences SET value=? WHERE key=?', (json.dumps(malformed), KEY))
        self.assertFalse(self.service.insights()['growth']['experienceChallenge']['allNavigationUnlocked'])

    def test_two_devices_and_old_state_merge_neither_double_award_nor_revoke(self):
        self.choose()
        old = read(self.service)
        self.completed(PROBLEMS[0], code='correct')
        self.service.insights()
        passed = read(self.service)
        other = copy.deepcopy(passed)
        other['awardedXp'] = max(0, passed['awardedXp'] - 100)
        for a, b in [(old, passed), (passed, old), (other, passed), (passed, other)]:
            joined = merge(a, b)
            self.assertTrue(joined['passedAt'])
            self.assertEqual(joined['seenVersion'], 1)
            self.assertEqual(joined['awardedXp'], passed['awardedXp'])
        def state(value):
            return {'format': 'tb-account-state-v1', 'tables': {'account_preferences': [{'key': KEY, 'value': json.dumps(value), 'updated_at': '2026-10-31'}]}, 'publicAccounts': {}}
        remote = state(passed)
        local = copy.deepcopy(remote)
        local['tables']['account_preferences'] = []
        merged = merge_states(remote, local, baselines(remote))
        self.assertEqual(len(merged['tables']['account_preferences']), 1)
        rows, retained = preserve_rows(self.service, [])
        self.assertTrue(retained)
        self.assertEqual(json.loads(rows[0]['value'])['awardedXp'], passed['awardedXp'])

    def test_applying_an_older_snapshot_keeps_earned_grant_and_requeues_journal(self):
        self.pass_challenge()
        sync = AccountStateSync.__new__(AccountStateSync)
        sync.service = self.service
        sync._check_stopping = lambda: None
        sync._apply_profiles = lambda state: None
        sync.chunks = SimpleNamespace(apply_code=lambda row, previous: row)
        with patch('account_sync.TABLES', {'account_preferences': ('key',), 'submissions': ('id',)}):
            changes = sync._apply({'tables': {'account_preferences': [], 'submissions': []}, 'publicAccounts': {}})
        self.assertLess(changes, self.service.connection.total_changes)
        self.assertTrue(read(self.service)['passedAt'])
        self.assertEqual(self.service.insights()['growth']['level'], 5)

    def test_nonzero_earned_xp_survives_old_snapshot_and_new_earnings_are_not_swallowed(self):
        from account_sync import TABLES
        self.service.connection.execute('CREATE TABLE IF NOT EXISTS account_sync_conflicts(id TEXT PRIMARY KEY,data TEXT NOT NULL)')
        original = {'tables': {name: [dict(row) for row in self.service.connection.execute(f'SELECT * FROM "{name}"')] for name in TABLES}, 'publicAccounts': {}}
        self.accept()
        self.assertEqual(self.service.insights()['growth']['totalXp'], 125)
        only_a = {'tables': {name: [dict(row) for row in self.service.connection.execute(f'SELECT * FROM "{name}"')] for name in TABLES}, 'publicAccounts': {}}
        granted = self.pass_challenge()
        self.assertEqual((granted['totalXp'], granted['challengeXp']), (500, 375))
        sync = AccountStateSync.__new__(AccountStateSync)
        sync.service = self.service
        sync._check_stopping = lambda: None
        sync._apply_profiles = lambda state: None
        sync.chunks = SimpleNamespace(apply_code=lambda row, previous: row)
        sync._apply(original)
        restored = self.service.insights()['growth']
        self.assertEqual((restored['level'], restored['totalXp'], restored['challengeXp']), (5, 500, 375))
        self.accept('fixture::B')
        self.assertEqual(self.service.insights()['growth']['totalXp'], 600)
        for late in [original, only_a, only_a]:
            sync._apply(late)
            self.assertEqual(self.service.insights()['growth']['totalXp'], 600)


if __name__ == '__main__':
    unittest.main()
