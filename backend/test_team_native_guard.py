"""Real ExternalBrowserBridge guard with deferred workers; no browser/OJ/login."""
from pathlib import Path
import sys
import threading
from types import MethodType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import copy

import backend
import test_team_workbench as team_fixtures
import test_training as fixtures
from team_workbench import authorized, current_authorized_contest, write
from training import ServiceError, TrainingService

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'desktop'))
from external_browser import ExternalBrowserBridge


class TeamNativeGuardTests(unittest.TestCase):
    setUp = fixtures.ServiceTests.setUp
    tearDown = fixtures.ServiceTests.tearDown
    room = team_fixtures.TeamWorkbenchTests.room
    body = team_fixtures.TeamWorkbenchTests.body
    remote = team_fixtures.TeamWorkbenchTests.remote

    def bridge(self):
        server = SimpleNamespace(training=self.service, store=self.library, accounts=None,
            official_session_lock=threading.RLock(), official_sessions={},
            browser_preparation=None, register_official_session=Mock())
        server.validate_official_url = MethodType(backend.LocalServer.validate_official_url, server)
        browser = Mock()
        bridge = ExternalBrowserBridge(self.root / 'unused-profile',
            guard=server.validate_official_url, browser_process=browser)
        server.official_submitter = bridge.submit
        # Model the real worker's second, immediately pre-click guard only.
        # Thread.start is mocked, and this callback never launches a provider.
        bridge._run = Mock(side_effect=lambda _identity: server.validate_official_url(self.library.rows[0]['url']))
        return server, bridge, browser

    def assert_denied_without_browser(self, server, bridge, browser, url, context=None):
        with patch('external_browser.threading.Thread') as worker:
            if context is None:
                with self.assertRaises(ServiceError):
                    bridge.submit(url, 'int main(){}', 'isolated')
            else:
                owner, contest = context
                with authorized(owner, contest), self.assertRaises(ServiceError):
                    bridge.submit(url, 'int main(){}', 'isolated')
            worker.assert_not_called()
        self.assertEqual(bridge.sessions, {})
        self.assertEqual(browser.mock_calls, [])

    def test_real_team_write_and_external_guard_keep_only_the_roster_identity(self):
        contest = self.room()
        # Same canonical URL, another catalogue identity outside this roster.
        self.library.rows[3]['url'] = self.library.rows[0]['url']
        server, bridge, browser = self.bridge()
        with patch('team_workbench.relay', side_effect=self.remote), \
                patch('team_workbench._bound_handle', return_value='isolatedOwner'), \
                patch.object(self.service, 'assert_official_allowed', wraps=self.service.assert_official_allowed) as check, \
                patch('external_browser.threading.Thread') as worker:
            result = write(server, 'official-submit', self.body())
            self.assertIn(result['sessionId'], bridge.sessions)
            self.assertEqual(result['status'], 'loading')
            worker.return_value.start.assert_called_once()
            args = worker.call_args.kwargs
            self.assertEqual(browser.mock_calls, [])
            self.assertFalse(bridge.sessions[result['sessionId']]['attempted'])
            self.assertTrue(all(c.args == ('fixture::A', contest['id']) for c in check.call_args_list))
            self.assertIsNone(current_authorized_contest(self.service))
            # The surrounding team authorization is already reset. Execute
            # only the captured guard callback in its copied worker context.
            args['target'](*args['args'])
            bridge._run.assert_called_once_with(result['sessionId'])
            self.assertTrue(all(c.args == ('fixture::A', contest['id']) for c in check.call_args_list))
        self.assertIsNone(current_authorized_contest(self.service))
        self.assertEqual(browser.mock_calls, [])

    def test_no_context_cannot_use_an_active_team_contest(self):
        self.room()
        server, bridge, browser = self.bridge()
        self.assert_denied_without_browser(server, bridge, browser, self.library.rows[0]['url'])

    def test_wrong_training_context_fails_closed_instead_of_becoming_ordinary(self):
        contest = self.room()
        server, bridge, browser = self.bridge()
        self.assert_denied_without_browser(server, bridge, browser, self.library.rows[0]['url'],
                                           (object(), contest['id']))

    def test_wrong_url_or_known_problem_outside_roster_is_rejected(self):
        contest = self.room()
        for url in ['https://codeforces.com/contest/999/problem/Z', self.library.rows[3]['url']]:
            server, bridge, browser = self.bridge()
            self.assert_denied_without_browser(server, bridge, browser, url,
                                               (self.service, contest['id']))

    def test_missing_slot_statement_and_wrong_contest_are_rejected(self):
        contest = self.room()
        for url, contest_id in [(self.library.rows[1]['url'], contest['id']),
                                (self.library.rows[0]['url'], 'team-does-not-exist')]:
            server, bridge, browser = self.bridge()
            self.assert_denied_without_browser(server, bridge, browser, url,
                                               (self.service, contest_id))

    def test_copied_worker_rechecks_expiry_and_current_training_before_dispatch(self):
        contest = self.room()
        server, bridge, browser = self.bridge()
        with patch('external_browser.threading.Thread') as worker:
            with authorized(self.service, contest['id']):
                bridge.submit(self.library.rows[0]['url'], 'int main(){}', 'isolated')
            run = worker.call_args.kwargs
        other = TrainingService(self.library, self.root / 'other.sqlite3', self.assets,
                                 self.judge, self.clock, self.root / 'other-backups')
        try:
            server.training = other
            with self.assertRaises(ServiceError):
                run['target'](*run['args'])
            server.training = self.service
            self.clock.advance(minutes=6)
            with self.assertRaises(ServiceError):
                run['target'](*run['args'])
        finally:
            other.close()
        self.assertEqual(browser.mock_calls, [])
        self.assertTrue(all(not s['attempted'] for s in bridge.sessions.values()))

    def test_mutated_owner_or_non_team_contest_does_not_reuse_a_grant(self):
        contest = self.room()
        original = self.service.connection.execute('SELECT config FROM contests WHERE id=?', (contest['id'],)).fetchone()[0]
        import json
        for changes in [{'teamOwner': 'different-account'}, {'strategy': 'replay'}]:
            config = {**json.loads(original), **changes}
            with self.service._write() as db:
                db.execute('UPDATE contests SET config=? WHERE id=?', (json.dumps(config), contest['id']))
            server, bridge, browser = self.bridge()
            self.assert_denied_without_browser(server, bridge, browser, self.library.rows[0]['url'],
                                               (self.service, contest['id']))

    def test_ordinary_session_cannot_be_adopted_by_team_even_if_already_attempted(self):
        self.library.rows[0]['url'] = 'https://codeforces.com/contest/123/problem/A'
        server, bridge, browser = self.bridge()
        with patch('external_browser.threading.Thread') as worker:
            old = bridge.open(self.library.rows[0]['url'], 'same source', 'isolated')
            self.assertNotIn('_guardAuthorization', old)
            contest = self.room()
            for attempted in [False, True]:
                bridge.sessions[old['sessionId']]['attempted'] = attempted
                before = copy.deepcopy(bridge.sessions)
                worker.reset_mock()
                with authorized(self.service, contest['id']), self.assertRaises(ServiceError) as error:
                    bridge.submit(self.library.rows[0]['url'], 'same source', 'isolated')
                self.assertEqual(error.exception.status, 409)
                self.assertEqual(bridge.sessions, before)
                worker.assert_not_called()
        self.assertEqual(browser.mock_calls, [])

    def test_same_authorization_reuses_one_pending_session_without_second_dispatch(self):
        contest = self.room()
        _server, bridge, browser = self.bridge()
        with patch('external_browser.threading.Thread') as worker, authorized(self.service, contest['id']):
            one = bridge.submit(self.library.rows[0]['url'], 'same source', 'isolated')
            two = bridge.submit(self.library.rows[0]['url'], 'same source', 'isolated')
            self.assertEqual(one['sessionId'], two['sessionId'])
            self.assertEqual(worker.call_count, 1)
            live = bridge.sessions[one['sessionId']]
            live.update(attempted=True, intent=False, dispatched=True, status='judging')
            third = bridge.submit(self.library.rows[0]['url'], 'same source', 'isolated')
            self.assertEqual(third['sessionId'], one['sessionId'])
            self.assertFalse(live['intent'])
            self.assertTrue(live['dispatched'])
            self.assertEqual(worker.call_count, 1)
        self.assertEqual(browser.mock_calls, [])


if __name__ == '__main__':
    unittest.main()
