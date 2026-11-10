"""In-memory ConnectedBrowserBridge fixture; no account DB/profile discovery."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import threading
from http.server import ThreadingHTTPServer
from types import SimpleNamespace
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / name) for name in ('desktop', 'backend', 'backend/common')]
from backend import Handler
from connected_browser import ConnectedBrowserBridge

owner = object()
observed = {'register': [], 'queueWithoutWindow': 0, 'savedReceipts': 0, 'pendingReceipts': 0}
identity = None
URL = 'https://ac.nowcoder.com/acm/problem/21992'
CODE = 'int main(){}'
parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=0)
parser.add_argument('--handshake-only', action='store_true')
options = parser.parse_args()
if not 0 <= options.port <= 65535:
    parser.error('port out of range')


class Bridge(ConnectedBrowserBridge):
    def register_browser(self, body):
        observed['register'].append({'protocol': body.get('protocol'), 'backgroundWindows': body.get('backgroundWindows') is True})
        return super().register_browser(body)

    def browser_queue(self, body, capability):
        if body.get('hasWindow') is False:
            observed['queueWithoutWindow'] += 1
        return super().browser_queue(body, capability)


def save(sid, session):
    observed['savedReceipts'] += 1
    return {'id': 'official-' + hashlib.sha256(('ac.nowcoder.com/' + session['submissionId']).encode()).hexdigest(), 'problemId': 'fixture::21992',
            'mode': 'submit', 'scope': 'official', 'code': session['code'], 'language': 'cpp17',
            'verdict': session['verdict'], 'finishedAt': '2026-11-10T00:00:00+00:00',
            'message': '原站确认提交 #' + session['submissionId']}


def pending(_sid, _session):
    observed['pendingReceipts'] += 1
    return True


class Fixture(Handler):
    def do_GET(self):
        global identity
        path = urlsplit(self.path).path
        bridge = self.server.browser_bridge
        if options.handshake_only and path in ('/fixture/create', '/fixture/ack', '/fixture/status'):
            self.send_json(403, {'error': 'HANDSHAKE_ONLY_NO_JOB'})
            return
        if path == '/fixture/create':
            value = bridge.submit(URL, CODE, 'isolated zero-window fixture')
            identity = value['sessionId']
            self.send_json(200, {'sessionId': identity, 'status': value['status']})
        elif path == '/fixture/status':
            value = bridge.status(identity) if identity else {}
            self.send_json(200, {key: value.get(key) for key in ('sessionId', 'status', 'submissionId', 'verdict', 'receiptSaved', 'windowClosed')})
        elif path == '/fixture/ack':
            self.send_json(200, bridge.acknowledge(identity))
        elif path == '/fixture/proof':
            self.send_json(200, {**observed, 'inMemoryOnly': True, 'personalDatabaseOpened': False,
                                'registeredProfilesRead': False, 'realSiteRequests': 0})
        else:
            super().do_GET()


server = ThreadingHTTPServer(('127.0.0.1', options.port), Fixture)
server.daemon_threads = True
server.frontend_origins = set()
server.dist_dir = None
server.store = SimpleNamespace(token='isolated-fixture-only')
server.browser_bridge = Bridge('http://127.0.0.1:' + str(server.server_port), current_owner=lambda: owner,
                               expected_owner=lambda _: '12345', on_identity=lambda *_: True,
                               on_receipt=save, on_pending=pending)


def stop():
    sys.stdin.readline()
    server.shutdown()


threading.Thread(target=stop, daemon=True).start()
print(json.dumps({'port': server.server_port}), flush=True)
try:
    server.serve_forever()
finally:
    server.server_close()
