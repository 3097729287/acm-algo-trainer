"""Real HTTP checks for shared-service routing and single-send account writes."""
import json
import os
import socket
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from urllib.error import URLError
from urllib.request import Request

from accounts import Accounts
from leaderboard import LeaderboardClient, service_opener
from training import ServiceError


class SharedTransportTests(unittest.TestCase):
    def setUp(self):
        self.requests = []
        self.drop_response = False
        self.delay = 0
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                self.do_POST()

            def do_POST(self):
                body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
                owner.requests.append((self.path, self.headers.get('Authorization'), body))
                if owner.delay:
                    time.sleep(owner.delay)
                if owner.drop_response:
                    self.connection.shutdown(socket.SHUT_RDWR)
                    self.connection.close()
                    return
                if self.path == '/redirect':
                    self.send_response(307)
                    self.send_header('Location', 'http://redirect.fixture.test/receive')
                    self.end_headers()
                    return
                raw = json.dumps({'ok': True}).encode()
                self.send_response(200)
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.endpoint = f'http://accounts.fixture.test:{self.server.server_port}'
        getaddrinfo = socket.getaddrinfo

        def resolve(host, *args, **kwargs):
            return getaddrinfo('127.0.0.1' if host == 'accounts.fixture.test' else host, *args, **kwargs)

        self.dns = patch('socket.getaddrinfo', side_effect=resolve)
        self.dns.start()
        self.bundled = patch('leaderboard.bundled_endpoint', return_value=self.endpoint)
        self.bundled.start()

    def tearDown(self):
        self.bundled.stop()
        self.dns.stop()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(3)

    def proxy(self, address):
        return patch.dict(os.environ, {'http_proxy': address, 'https_proxy': address,
                                      'HTTP_PROXY': address, 'HTTPS_PROXY': address,
                                      'no_proxy': '', 'NO_PROXY': ''})

    def test_bundled_public_host_sends_once_despite_unreachable_proxy(self):
        with self.proxy('http://127.0.0.1:9'):
            request = Request(self.endpoint + '/register', data=b'{"nickname":"fixture"}',
                              headers={'Authorization': 'Bearer fixture-only'})
            with service_opener(self.endpoint).open(request, timeout=2) as response:
                self.assertTrue(json.load(response)['ok'])
        self.assertEqual(self.requests, [('/register', 'Bearer fixture-only', b'{"nickname":"fixture"}')])

    def test_custom_service_keeps_system_proxy(self):
        proxy = f'http://127.0.0.1:{self.server.server_port}'
        with self.proxy(proxy):
            with service_opener('http://custom.fixture.test').open('http://custom.fixture.test/profile', timeout=2) as response:
                self.assertTrue(json.load(response)['ok'])
        self.assertEqual(self.requests[0][0], 'http://custom.fixture.test/profile')

    def test_redirect_does_not_forward_credentials_or_replay_post(self):
        with self.proxy('http://127.0.0.1:9'):
            request = Request(self.endpoint + '/redirect', data=b'fixture-body',
                              headers={'Authorization': 'Bearer fixture-only'})
            with self.assertRaises(URLError):
                service_opener(self.endpoint).open(request, timeout=2)
        self.assertEqual(self.requests, [('/redirect', 'Bearer fixture-only', b'fixture-body')])

    def test_dropped_account_response_never_replays_registration(self):
        self.drop_response = True
        account = Accounts.__new__(Accounts)
        account.closed, account.endpoint, account.session = False, self.endpoint, None
        account.opener = service_opener(self.endpoint)
        with self.assertLogs('tb.accounts', level='WARNING') as log:
            with self.assertRaises(ServiceError) as caught:
                account._remote('POST', '/register', {'password': 'private-fixture-only'})
        self.assertEqual(caught.exception.status, 503)
        self.assertEqual(len(self.requests), 1)
        self.assertNotIn('private-fixture-only', '\n'.join(log.output))

    def test_ranking_accepts_a_response_slower_than_the_old_five_second_limit(self):
        self.delay = 5.2
        client = LeaderboardClient(None)
        self.addCleanup(client.close)
        profile = {'endpoint': self.endpoint, 'user_id': 'fixture', 'auth_token': 'fixture-only'}
        started = time.monotonic()
        self.assertTrue(client._request(profile, 'GET', '/slow-ranking')['ok'])
        self.assertGreater(time.monotonic() - started, 5)
        self.assertEqual(len(self.requests), 1)


if __name__ == '__main__':
    unittest.main()
