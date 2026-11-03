import io
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError
from thought_duel import relay, PkServiceError


class ThoughtRelayTests(unittest.TestCase):
    def setUp(self):
        self.profile = {'user_id': 'isolated-owner', 'endpoint': 'https://example.invalid', 'auth_token': 'fixture-token'}
        self.training = SimpleNamespace(admin_mode=False, _ranking_profile=Mock(return_value=self.profile))

    def test_relay_pins_identity_and_does_not_accept_model_or_winner(self):
        payload = {'matchId': 'fixture', 'text': '我的思路', 'revision': 2, 'requestId': 'fixture-request'}
        response = io.BytesIO(json.dumps({'owner': 'isolated-owner', 'status': 'active'}).encode())
        opener = Mock();opener.open.return_value = response
        with patch('thought_duel.service_opener', return_value=opener):
            self.assertEqual(relay(self.training, 'game/draft', payload)['status'], 'active')
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, 'https://example.invalid/api/pk/v1/game/draft')
        self.assertEqual(request.get_header('Authorization'), 'Bearer fixture-token')
        self.assertEqual(json.loads(request.data), payload)
        with self.assertRaises(PkServiceError) as rejected:
            relay(self.training, 'game/submit', {**payload, 'winner': 'A'})
        self.assertEqual(rejected.exception.code, 'PK_REQUEST_INVALID')

    def test_old_service_disables_new_mode_and_owner_switch_discards_response(self):
        opener = Mock();opener.open.side_effect = HTTPError('https://example.invalid', 404, 'missing', {}, io.BytesIO())
        with patch('thought_duel.service_opener', return_value=opener):
            self.assertFalse(relay(self.training)['enabled'])
        self.training._ranking_profile.side_effect = [self.profile, {**self.profile, 'user_id': 'other-owner'}]
        opener.open.side_effect = None;opener.open.return_value = io.BytesIO(b'{"owner":"isolated-owner","status":"idle"}')
        with patch('thought_duel.service_opener', return_value=opener), self.assertRaises(PkServiceError) as issue:
            relay(self.training)
        self.assertEqual(issue.exception.code, 'PK_OWNER_CHANGED')

    def test_remote_errors_keep_pk_code_and_admin_workspace_never_connects(self):
        opener = Mock();opener.open.side_effect = HTTPError('https://example.invalid', 409, 'locked', {}, io.BytesIO(b'{"code":"PK_ANSWER_LOCKED","error":"locked"}'))
        with patch('thought_duel.service_opener', return_value=opener), self.assertRaises(PkServiceError) as issue:
            relay(self.training, 'game/submit', {'text': ''})
        self.assertEqual(issue.exception.code, 'PK_ANSWER_LOCKED')
        self.training.admin_mode = True
        with patch('thought_duel.service_opener') as network, self.assertRaises(PkServiceError):
            relay(self.training)
        network.assert_not_called()


if __name__ == '__main__':
    unittest.main()
