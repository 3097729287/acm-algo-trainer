"""Two disposable computers share a real local account HTTP service."""
import copy
import datetime as dt
import http.client
import json
from pathlib import Path
import threading
import time
import unittest
from unittest.mock import patch

import backend
import test_accounts as fixtures
from account_sync import baselines, merge_states
from goals import Goals
from public_platforms import profile
from training import ServiceError


class CloudStateTests(unittest.TestCase):
    setUp = fixtures.AccountTests.setUp
    start = fixtures.AccountTests.start
    stop = fixtures.AccountTests.stop
    call = fixtures.AccountTests.call
    signup = fixtures.AccountTests.signup
    login = fixtures.AccountTests.login

    def tearDown(self):
        for close in reversed(getattr(self, 'other_closers', [])):
            close()
        fixtures.AccountTests.tearDown(self)

    def other_computer(self, missing_library=False):
        folder = self.root / 'second-computer'
        folder.mkdir(exist_ok=True)
        library_file = self.library_file
        if missing_library:
            from library import LibraryDatabase
            library_file = folder / 'empty-library.sqlite3'
            LibraryDatabase(library_file)
        server = backend.create_server(training_file=folder / 'tb-personal.sqlite3', library_file=library_file,
            data_root=folder, data_file=folder / 'absent.md', integration_auto_start=False,
            assets=None if missing_library else fixtures.Assets(None), judge=self.judge, account_endpoint=self.endpoint, backup_dir=folder / 'backups')
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        def close():
            server.shutdown(); server.server_close(); thread.join(3)
        if not hasattr(self, 'other_closers'):
            self.other_closers = []
        self.other_closers.append(close)
        return server

    def call_other(self, server, path, body=None):
        connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=20)
        connection.request('GET' if body is None else 'POST', path,
                           body=None if body is None else json.dumps(body).encode(),
                           headers={'Content-Type': 'application/json', 'X-TB-Token': server.store.token})
        response = connection.getresponse()
        result = response.status, json.loads(response.read())
        connection.close()
        return result

    def test_two_computers_receive_all_learning_data_before_login_and_revoke_old_device(self):
        self.signup(); self.assertEqual(self.login()[0], 200)
        service = self.server.training
        service.start_training('fixture::A')
        service.save_draft('fixture::A', 'first computer draft')
        service.record_official({'id': 'fixture::A', 'url': 'https://codeforces.com/contest/1/problem/A', 'code': 'int main(){}'},
                                {'status': 'finished', 'submissionId': '123456', 'verdict': 'AC'})
        goal = Goals(service).save({'title': 'shared goal', 'kind': 'custom', 'deadline': '2026-12-31', 'totalProblems': 10})
        with self.server.store.extensions.lock:
            self.server.store.extensions.state['settings']['accounts']['codeforces'] = 'fixture_owner'
            value = profile('codeforces', 'fixture_owner')
            value.update(status='ready', rating=1800, maxRating=1900, updatedAt='2026-10-15T10:00:00Z',
                         solved=[{'url': 'https://codeforces.com/contest/1/problem/A', 'acceptedAt': '2026-10-15T10:00:00Z'}])
            self.server.store.extensions.state['accounts']['codeforces'] = value
        service.daily_tasks()
        with service.lock:
            service.connection.execute("UPDATE daily_missions SET claimed_at='2026-10-15T12:00:00Z',awarded_xp=20 WHERE id=(SELECT id FROM daily_missions LIMIT 1)")
            service.connection.execute("INSERT OR REPLACE INTO achievement_xp_claims VALUES('official-first','2026-10-15T12:00:00Z',30,'2026-10-15T12:00:00Z')")
            service.connection.execute("INSERT OR REPLACE INTO account_preferences VALUES('favorites','[\"fixture::A\"]','2026-10-15T12:00:00Z')")
        service.insights()  # Award new achievements exactly once before capture.
        before = service.insights()
        claim_count = service.connection.execute('SELECT COUNT(*) FROM achievement_xp_claims').fetchone()[0]
        self.server.accounts.sync_pending(wait=True)
        other = self.other_computer()
        status, login = self.call_other(other, '/api/account/login', {'loginId': 'account_a', 'password': 'fixture-password'})
        self.assertEqual(status, 200, login)
        self.assertTrue(login['authenticated'])
        self.assertFalse(login['sync']['pending'])
        self.assertEqual(other.training.problem('fixture::A')['draft'], 'first computer draft')
        records = other.training.submissions()['submissions']
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['scope'], 'official')
        self.assertEqual(records[0]['code'], 'int main(){}')
        self.assertEqual(Goals(other.training).list()['goals'][0]['title'], 'shared goal')
        self.assertEqual(other.store.extensions.snapshot()['settings']['accounts']['codeforces'], 'fixture_owner')
        restored_growth=other.training.insights()['growth']
        self.assertEqual(restored_growth['authority']['owner'],before['growth']['authority']['owner'])
        self.assertNotEqual(restored_growth['authority']['epoch'],before['growth']['authority']['epoch'])
        self.assertEqual({k:v for k,v in restored_growth.items() if k!='authority'},
                         {k:v for k,v in before['growth'].items() if k!='authority'})
        self.assertEqual(other.training.connection.execute('SELECT COUNT(*) FROM achievement_xp_claims').fetchone()[0], claim_count)
        self.assertEqual(json.loads(other.training.connection.execute("SELECT value FROM account_preferences WHERE key='favorites'").fetchone()[0]), ['fixture::A'])
        deadline = time.monotonic() + 6
        while self.server.accounts.session and time.monotonic() < deadline:
            time.sleep(.05)
        self.assertIsNone(self.server.accounts.session, 'The previous computer is invalidated by heartbeat')
        self.assertEqual(self.call('/api/workspace')[0], 401)
        other.training.save_draft('fixture::A', 'second computer draft')
        other.accounts.sync_pending(wait=True)
        self.assertEqual(self.call_other(other, '/api/account/logout', {})[0], 200)
        self.assertEqual(self.login()[0], 200)
        self.assertEqual(self.server.training.problem('fixture::A')['draft'], 'second computer draft')
        resumed_growth=self.server.training.insights()['growth']
        self.assertEqual(resumed_growth['authority']['owner'],before['growth']['authority']['owner'])
        self.assertEqual({k:v for k,v in resumed_growth.items() if k!='authority'},
                         {k:v for k,v in before['growth'].items() if k!='authority'})

    @patch('integrations.IntegrationService.sync', lambda service, body=None: service.snapshot())
    def test_receipt_owner_bindings_follow_account_across_computers_and_clear_on_switch(self):
        self.signup(); self.login()
        self.assertEqual(self.call('/api/hub/configure', {'accounts': {'nowcoder': '42', 'luogu': '66'}})[0], 200)
        self.server.accounts.sync_pending(wait=True)
        other = self.other_computer()
        status, result = self.call_other(other, '/api/account/login', {'loginId': 'account_a', 'password': 'fixture-password'})
        self.assertEqual(status, 200, result)
        def bindings():
            value = other.store.extensions.snapshot()['settings']['accounts']
            return {site: value[site] for site in ('nowcoder', 'luogu')}
        self.assertEqual(bindings(), {'nowcoder': '42', 'luogu': '66'})
        self.assertEqual(self.call_other(other, '/api/account/logout', {})[0], 200)
        self.assertEqual(self.call_other(other, '/api/account/register', {'loginId': 'account_b', 'nickname': '账号乙', 'password': 'fixture-password'})[0], 200)
        self.assertEqual(self.call_other(other, '/api/account/login', {'loginId': 'account_b', 'password': 'fixture-password'})[0], 200)
        self.assertEqual(bindings(), {'nowcoder': '', 'luogu': ''})
        self.assertEqual(self.call_other(other, '/api/account/logout', {})[0], 200)
        self.assertEqual(self.call_other(other, '/api/account/login', {'loginId': 'account_a', 'password': 'fixture-password'})[0], 200)
        self.assertEqual(bindings(), {'nowcoder': '42', 'luogu': '66'})
        self.assertEqual(self.call_other(other, '/api/hub/configure', {'accounts': {'nowcoder': '', 'luogu': ''}})[0], 200)
        other.accounts.sync_pending(wait=True)
        self.assertEqual(self.call_other(other, '/api/account/logout', {})[0], 200)
        # The first computer learns that another login revoked its session on
        # its heartbeat. Fast offline fixtures must not log in before that.
        deadline = time.monotonic() + 6
        while self.server.accounts.session and time.monotonic() < deadline:
            time.sleep(.05)
        self.assertIsNone(self.server.accounts.session)
        status, answer = self.login()
        self.assertEqual(status, 200, answer)
        value = self.server.store.extensions.snapshot()['settings']['accounts']
        self.assertEqual((value['nowcoder'], value['luogu']), ('', ''))

    def test_unsynchronized_legacy_draft_is_preserved_in_conflicts_when_remote_is_newer(self):
        self.signup(); self.login()
        service = self.server.training
        service.save_draft('fixture::A', 'remote latest draft')
        self.server.accounts.sync_pending(wait=True)
        other = self.other_computer()
        other.training.save_draft('fixture::A', 'old local unique draft')
        with other.training.lock:
            other.training.connection.execute("UPDATE drafts SET saved_at='2020-01-01T00:00:00Z'")
            other.training.connection.execute('UPDATE ranking_profile SET user_id=?', (self.server.accounts.session['userId'],))
        other.accounts.legacy_owner = self.server.accounts.session['userId']
        status, result = self.call_other(other, '/api/account/login', {'loginId': 'account_a', 'password': 'fixture-password'})
        self.assertEqual(status, 200, result)
        self.assertEqual(other.training.problem('fixture::A')['draft'], 'remote latest draft')
        conflicts = other.training.connection.execute('SELECT data FROM account_sync_conflicts').fetchall()
        self.assertTrue(any('old local unique draft' in row[0] for row in conflicts))
        self.assertTrue(list((self.root / 'second-computer/backups').glob('*.bak')))

    def test_slow_cloud_upload_does_not_hold_the_training_lock_and_later_write_is_flushed(self):
        self.signup(); self.login()
        service, sync = self.server.training, self.server.accounts.state_sync
        sync.close()  # Use an explicit flush for deterministic scheduling.
        sync.stop.clear()
        service.save_draft('fixture::A', 'before slow upload')
        original, entered, release = sync._call, threading.Event(), threading.Event()
        def slow(method, path, body=None):
            if method == 'PUT':
                entered.set(); release.wait(5)
            return original(method, path, body)
        with patch.object(sync, '_call', slow):
            worker = threading.Thread(target=sync.flush)
            worker.start()
            try:
                self.assertTrue(entered.wait(3))
                start = time.monotonic()
                service.save_draft('fixture::A', 'written during upload')
                self.assertLess(time.monotonic() - start, .5)
            finally:
                release.set(); worker.join(5)
        self.assertNotEqual(service.connection.total_changes, sync.last_changes)
        sync.flush()
        remote = original('GET', '/v1/accounts/state')['state']
        self.assertEqual(remote['tables']['drafts'][0]['code'], 'written during upload')

    def test_takeover_heartbeat_runs_while_an_upload_is_waiting(self):
        self.signup(); self.login()
        sync = self.server.accounts.state_sync
        original, entered, release = sync._call, threading.Event(), threading.Event()
        def delayed(method, path, body=None):
            if method == 'PUT':
                entered.set(); release.wait(8)
            return original(method, path, body)
        with patch.object(sync, '_call', delayed):
            self.server.training.save_draft('fixture::A', 'durable pending draft')
            self.server.accounts.sync_pending(wait=False)
            self.assertTrue(entered.wait(3))
            try:
                other = self.other_computer()
                status, login = self.call_other(other, '/api/account/login', {'loginId': 'account_a', 'password': 'fixture-password'})
                self.assertEqual(status, 200, login)
                deadline = time.monotonic() + 4
                while self.server.accounts.session and time.monotonic() < deadline:
                    time.sleep(.02)
                self.assertIsNone(self.server.accounts.session, 'A pending upload must not postpone forced logout')
                self.assertEqual(self.server.training.connection.execute('SELECT code FROM drafts').fetchone()[0], 'durable pending draft')
            finally:
                release.set()

    def test_failed_initial_sync_does_not_authenticate_or_replace_existing_drafts(self):
        self.server.training.save_draft('fixture::A', 'original local private draft')
        self.signup()
        original = self.server.accounts._remote
        def unavailable(method, path, *args, **kwargs):
            if path == '/v1/accounts/state':
                raise ServiceError(503, 'fixture offline')
            return original(method, path, *args, **kwargs)
        with patch.object(self.server.accounts, '_remote', unavailable):
            self.assertEqual(self.login()[0], 503)
        self.assertIsNone(self.server.accounts.session)
        self.assertEqual(self.server.training.problem('fixture::A')['draft'], 'original local private draft')
        self.assertEqual(self.call('/api/data')[0], 401)
        self.assertEqual(self.login()[0], 200)
        self.assertEqual(self.server.training.problem('fixture::A')['draft'], 'original local private draft')

    def test_switching_accounts_closes_unused_services_and_isolates_public_handles(self):
        self.signup(); self.login()
        previous = self.server.training
        extensions = self.server.store.extensions
        with extensions.lock:
            extensions.state['settings']['accounts']['codeforces'] = 'account_a_handle'
            extensions.state['accounts']['codeforces'] = profile('codeforces', 'account_a_handle')
        self.assertEqual(self.call('/api/account/logout', {})[0], 200)
        self.signup('account_b', '账号乙')
        self.assertEqual(self.login('account_b')[0], 200)
        deadline = time.monotonic() + 3
        while not previous.closed and time.monotonic() < deadline:
            time.sleep(.02)
        self.assertTrue(previous.closed)
        self.assertEqual(len(self.server.accounts.services), 1)
        self.assertEqual(extensions.snapshot()['settings']['accounts']['codeforces'], '')
        self.assertEqual(self.call('/api/account/logout', {})[0], 200)
        self.assertEqual(self.login()[0], 200)
        self.assertEqual(extensions.snapshot()['settings']['accounts']['codeforces'], 'account_a_handle')

    @patch('account_chunks.ChunkTransport.negotiate',lambda self:None)
    def test_large_source_history_is_compressed_and_recovered_without_server_inflation(self):
        self.signup(); self.login()
        service = self.server.training
        code = '// reusable source line\n' * 2600
        stamp = '2026-10-15T10:00:00Z'
        with service.lock:
            service.connection.executemany('''INSERT INTO submissions
                (id,problem_id,mode,code,submitted_at,finished_at,verdict,scope)
                VALUES(?,?,'run',?,?,?,'RUN_OK','local')''',
                [(f'large-source-{i}', 'fixture::A', code, stamp, stamp) for i in range(220)])
        self.server.accounts.sync_pending(wait=True)
        remote = self.server.accounts._remote('GET', '/v1/accounts/state', session=self.server.accounts.session, maximum=4 * 1024 * 1024)['state']
        self.assertEqual(remote['format'], 'tb-account-state-gzip-v1')
        self.assertGreater(remote['uncompressedBytes'], 12 * 1024 * 1024)
        self.assertLess(len(remote['payload']), 256 * 1024)
        other = self.other_computer()
        status, value = self.call_other(other, '/api/account/login', {'loginId': 'account_a', 'password': 'fixture-password'})
        self.assertEqual(status, 200, value)
        self.assertEqual(other.training.connection.execute('SELECT COUNT(*) FROM submissions').fetchone()[0], 220)
        self.assertEqual(other.training.connection.execute("SELECT code FROM submissions WHERE id='large-source-219'").fetchone()[0], code)

    def test_offline_public_handle_edit_survives_restart_and_is_uploaded_for_its_owner(self):
        self.signup(); self.login()
        extensions = self.server.store.extensions
        with extensions.lock:
            extensions.state['settings']['accounts']['codeforces'] = 'before_offline'
            extensions.state['accounts']['codeforces'] = profile('codeforces', 'before_offline')
            extensions._save()
        self.server.accounts.sync_pending(wait=True)
        self.server.accounts.state_sync.close()
        with extensions.lock:
            extensions.state['settings']['accounts']['codeforces'] = 'edited_offline'
            extensions.state['accounts']['codeforces'] = profile('codeforces', 'edited_offline')
            extensions._save()
        self.stop(); self.start()
        self.assertTrue(self.call('/api/account')[1]['authenticated'])
        self.assertEqual(self.server.store.extensions.snapshot()['settings']['accounts']['codeforces'], 'edited_offline')
        remote = self.server.accounts.state_sync._call('GET', '/v1/accounts/state')['state']
        self.assertEqual(remote['publicAccounts']['codeforces']['handle'], 'edited_offline')

    def test_private_problem_facts_include_only_owned_references_and_open_on_an_empty_computer(self):
        from test_library import record
        source = list(record())
        source[2] = {'markdown': 'Private imported explanation. ![](C:\\Private\\picture.svg)',
                     'path': 'C:\\Private\\solution.md',
                     'images': {'C:\\Private\\picture.svg': 'data:image/svg+xml;base64,PHN2Zy8+'}}
        source[3] = {'markdown': 'Portable statement', 'samples': [{'input': '2\n', 'output': '2\n'}],
                     'limits': {'timeMs': 1000, 'memoryMb': 256}, 'statementAvailable': True}
        self.server.store.library.import_records([tuple(source), record('other-owner::B', title='Other account private import')], {}, {})
        self.signup(); self.login()
        self.server.training.save_draft('fixture::A', 'private source for portable problem')
        self.server.accounts.sync_pending(wait=True)
        state = self.server.accounts.state_sync._call('GET', '/v1/accounts/state')['state']
        facts = state['tables']['account_problem_facts']
        self.assertEqual([row['problem_id'] for row in facts], ['fixture::A'])
        saved = json.loads(facts[0]['value'])
        self.assertEqual(saved['row']['title'], 'Fixture')
        self.assertEqual(saved['statement']['samples'][0]['input'], '2\n')
        self.assertNotIn('C:\\Private', json.dumps(saved))
        self.assertIn('portable/', saved['solution']['markdown'])
        other = self.other_computer(missing_library=True)
        status, login = self.call_other(other, '/api/account/login', {'loginId': 'account_a', 'password': 'fixture-password'})
        self.assertEqual(status, 200, login)
        self.assertEqual(other.training._row('fixture::A')['title'], 'Fixture')
        problem = other.training.problem('fixture::A')
        self.assertEqual(problem['draft'], 'private source for portable problem')
        self.assertEqual(problem['markdown'], 'Portable statement')
        status, solution = self.call_other(other, '/api/solution?id=fixture::A')
        self.assertEqual(status, 200, solution)
        self.assertIn('Private imported explanation', solution['markdown'])


class MergeTests(unittest.TestCase):
    def test_three_way_merge_preserves_unsent_goal_edits_and_respects_deletions(self):
        initial = {'format': 'tb-account-state-v1', 'tables': {'goals': [{'id': 'goal-one', 'created_at': '2026-10-15', 'config': 'old', 'archived': 0}]}, 'publicAccounts': {}}
        baseline = baselines(initial)
        local = copy.deepcopy(initial)
        local['tables']['goals'][0]['config'] = 'edited offline'
        self.assertEqual(merge_states(initial, local, baseline)['tables']['goals'][0]['config'], 'edited offline')
        removed = copy.deepcopy(initial)
        removed['tables']['goals'] = []
        self.assertEqual(merge_states(removed, initial, baseline)['tables']['goals'], [])
        self.assertEqual(merge_states(initial, removed, baseline)['tables']['goals'], [])

    def test_rewards_are_deduplicated_instead_of_summed_and_earliest_unlock_is_kept(self):
        def state(xp, unlock):
            return {'format': 'tb-account-state-v1', 'tables': {
                'achievement_xp_claims': [{'achievement_id': 'official-first', 'awarded_xp': xp, 'unlocked_at': unlock, 'claimed_at': unlock}],
                'official_first_xp_awards': [{'problem_key': 'one', 'awarded_xp': xp, 'accepted_at': unlock}],
                'tb_rank_profile': [{'id': 1, 'unlocked_at': unlock}],
            }, 'publicAccounts': {}}
        result = merge_states(state(20, '2026-10-15'), state(30, '2026-10-14'))
        self.assertEqual(result['tables']['achievement_xp_claims'][0]['awarded_xp'], 30)
        self.assertEqual(result['tables']['official_first_xp_awards'][0]['awarded_xp'], 30)
        self.assertEqual(result['tables']['tb_rank_profile'][0]['unlocked_at'], '2026-10-14')

    def test_achievement_without_official_timestamp_merges_without_inventing_unlock_time(self):
        def state(unlock):
            return {'format': 'tb-account-state-v1', 'tables': {'achievement_xp_claims': [
                {'achievement_id': 'official-count', 'unlocked_at': unlock, 'awarded_xp': 30, 'claimed_at': '2026-10-15'}]}, 'publicAccounts': {}}
        self.assertIsNone(merge_states(state(None), state(None))['tables']['achievement_xp_claims'][0]['unlocked_at'])
        self.assertEqual(merge_states(state(None), state('2026-10-14'))['tables']['achievement_xp_claims'][0]['unlocked_at'], '2026-10-14')


if __name__ == '__main__':
    unittest.main()
