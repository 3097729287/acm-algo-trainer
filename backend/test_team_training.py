import io
import json
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from team_training import relay, TeamServiceError


class TeamTransportTests(unittest.TestCase):
    def setUp(self):
        self.profile = {'user_id': 'isolated-owner', 'endpoint': 'https://example.invalid', 'auth_token': 'fixture-token'}
        self.training = SimpleNamespace(admin_mode=False, _ranking_profile=Mock(return_value=self.profile),
                                        lock=threading.RLock(), active_contest=Mock(return_value=None))

    def test_shared_code_uses_bound_credentials_and_cannot_inject_scores_or_paths(self):
        value = {'requestId': 'fixture-request', 'roomId': 'fixture-room', 'problemId': 'task',
                 'revision': 1, 'code': '// 中文🦆', 'language': 'cpp17', 'leaseToken': 'lease'}
        opener = Mock();opener.open.return_value = io.BytesIO(b'{"owner":"isolated-owner","team":null}')
        with patch('team_training.service_opener', return_value=opener):
            self.assertIsNone(relay(self.training, 'draft', value)['team'])
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, 'https://example.invalid/v1/team-training/draft')
        self.assertEqual(request.get_header('Authorization'), 'Bearer fixture-token')
        self.assertEqual(json.loads(request.data), value)
        for path, body in [('draft', {**value, 'totalScore': 999}), ('../accounts', None), ('create', {'owner': 'someone-else'})]:
            with patch('team_training.service_opener') as network, self.assertRaises(TeamServiceError):
                relay(self.training, path, body)
            network.assert_not_called()
        with patch('team_training.service_opener') as network,self.assertRaises(TeamServiceError):
            relay(self.training,'native-receipt',{'requestId':'fake','intentId':'fake','submissionId':'999','handle':'someone'})
        network.assert_not_called()

    def test_owner_token_or_endpoint_change_discards_a_late_response(self):
        for changed in ({**self.profile, 'user_id': 'other-owner'}, {**self.profile, 'auth_token': 'renewed'},
                        {**self.profile, 'endpoint': 'https://other.invalid'}):
            self.training._ranking_profile.side_effect = [self.profile, changed]
            opener = Mock();opener.open.return_value = io.BytesIO(b'{"owner":"isolated-owner","team":null}')
            with patch('team_training.service_opener', return_value=opener), self.assertRaises(TeamServiceError) as issue:
                relay(self.training)
            self.assertEqual(issue.exception.code, 'TEAM_OWNER_CHANGED')

    def test_old_service_remote_conflict_query_limits_and_local_contest_guard(self):
        opener = Mock();opener.open.side_effect = HTTPError('https://example.invalid', 404, 'missing', {}, io.BytesIO())
        with patch('team_training.service_opener', return_value=opener):
            self.assertFalse(relay(self.training)['enabled'])
        opener.open.side_effect = HTTPError('https://example.invalid', 409, 'conflict', {},
                                           io.BytesIO(b'{"code":"TEAM_REVISION_CONFLICT","error":"conflict"}'))
        with patch('team_training.service_opener', return_value=opener), self.assertRaises(TeamServiceError) as issue:
            relay(self.training, 'draft', {'code': ''})
        self.assertEqual(issue.exception.code, 'TEAM_REVISION_CONFLICT')
        for query in ({'id': ['one', 'two']}, {'id': ['../accounts']}, {'endpoint': ['https://other.invalid']}):
            with self.assertRaises(TeamServiceError):relay(self.training, 'catalogue', query=query)
        self.training.active_contest.return_value = {'id': 'normal-contest'}
        with patch('team_training.service_opener') as network, self.assertRaises(TeamServiceError) as issue:
            relay(self.training, 'ready', {'ready': True})
        self.assertEqual(issue.exception.code, 'TEAM_CONTEST_ACTIVE');network.assert_not_called()
        self.training.admin_mode = True
        with patch('team_training.service_opener') as network, self.assertRaises(TeamServiceError):relay(self.training)
        network.assert_not_called()


if __name__ == '__main__':
    unittest.main()
