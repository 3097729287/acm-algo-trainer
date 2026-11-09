"""Loopback-only native service for review editor regression; no real OJ/login."""
import datetime as dt
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
import threading
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from test_training import Assets, Clock, Judge, Library
from training import ServiceError, TrainingService, UTC, iso

assert os.environ.get('TB_OFFLINE') == '1', 'Offline fixture only'
state = Path(os.environ['TB_REVIEW_TEST_STATE']).resolve()
assert state.is_relative_to((ROOT / '.backups/review-latest-ac-20261109').resolve())
state.mkdir(parents=True, exist_ok=True)
marker = state / 'fixture-marker.txt'
if marker.exists():
    assert marker.read_text() == 'review-editor-isolated-native-v1'
else:
    assert not list(state.iterdir()), 'A fixture may not adopt existing personal state'
    marker.write_text('review-editor-isolated-native-v1')


class ReviewAssets(Assets):
    def problem(self, identity):
        return {**super().problem(identity), 'title': '隔离复习源码回归',
                'url': 'https://codeforces.com/contest/123/problem/A',
                'translationAvailable': False, 'judge': {'scope': 'samples'}}


library = Library()
library.rows[0].update(platform='Codeforces', url='https://codeforces.com/contest/123/problem/A')
clock = Clock()
clock_file = state / 'clock.txt'
clock.value = dt.datetime.fromisoformat(clock_file.read_text()) if clock_file.exists() else dt.datetime.now(UTC) - dt.timedelta(days=1)
judge = Judge()
assets = ReviewAssets(library)
service = TrainingService(library, state / 'personal.sqlite3', assets, judge, clock, state / 'backups')
lock = threading.RLock()
sessions = {}
fail_drafts = False


def official(body):
    # This is the explicit local native-provider boundary. These receipts are
    # synthetic and cannot be sent to any public service or original site.
    clock.advance(seconds=1)
    number = 93000 + service.connection.execute("SELECT COUNT(*) FROM submissions WHERE scope='official'").fetchone()[0]
    remote = str(body.get('remote') or number)
    session = {'id': 'fixture::A', 'url': assets.problem('fixture::A')['url'],
               'code': body['code'], 'language': body.get('language', 'cpp17'),
               'reviewId': body.get('reviewId')}
    result = service.record_official(session, {'status': 'finished',
        'verdict': body.get('verdict', 'AC'), 'submissionId': remote,
        'acceptedAt': body.get('submittedAt') or iso(clock())})
    clock_file.write_text(clock().isoformat())
    return result, remote


if not (state / 'seeded.txt').exists():
    service.save_draft('fixture::A', 'int main() {} // previous ordinary template')
    official({'code': 'old wrong code', 'verdict': 'WA'})
    official({'code': 'old accepted code'})
    (state / 'seeded.txt').write_text('fixture seeds only')


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def do_GET(self):
        self.handle_request()

    def do_POST(self):
        self.handle_request()

    def handle_request(self):
        global fail_drafts
        parsed = urlsplit(self.path)
        query = {key: value[0] for key, value in parse_qs(parsed.query).items()}
        body = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))) or b'{}') if self.command == 'POST' else None
        try:
            with lock:
                if parsed.path == '/problem':
                    value = service.problem(query['id'], review_id=query.get('reviewId'))
                elif parsed.path == '/initial-code':
                    from initial_code import catalog
                    value = catalog(service)
                elif parsed.path == '/submission':
                    value = service.submission(query['id'])
                elif parsed.path == '/draft':
                    if fail_drafts:
                        raise ServiceError(503, 'Isolated draft-save failure')
                    value = service.save_draft(body['id'], body['code'], language=body.get('language', 'cpp17'), review_id=body.get('reviewId'))
                elif parsed.path == '/workspace':
                    value = service.workspace()
                elif parsed.path in ('/official/submit', '/official/open'):
                    result, remote = official(body)
                    identity = 'fixture-native-' + remote
                    value = {'sessionId': identity, 'status': 'finished', 'platform': 'Codeforces',
                             'verdict': 'AC', 'submissionId': remote, 'submission': result,
                             'message': 'Offline native receipt fixture; no OJ was contacted'}
                    sessions[identity] = value
                elif parsed.path == '/official/status':
                    value = sessions[query['sessionId']]
                elif parsed.path in ('/official/ack', '/official/close'):
                    value = {'closed': True}
                elif parsed.path == '/fixture/next-review':
                    clock.advance(days=10)
                    value = next(item for item in service.review_plan()['tasks'] if item['problemId'] == 'fixture::A')
                    service.problem('fixture::A', review_id=value['id'])
                    clock_file.write_text(clock().isoformat())
                elif parsed.path == '/fixture/late':
                    value, _remote = official(body)
                elif parsed.path == '/fixture/fail-drafts':
                    fail_drafts = body['enabled'] is True
                    value = {'enabled': fail_drafts}
                elif parsed.path == '/fixture/state':
                    value = {'drafts': [dict(r) for r in service.connection.execute('SELECT * FROM drafts')],
                             'submissions': [service._submission(r) for r in service.connection.execute('SELECT * FROM submissions ORDER BY submitted_at')],
                             'clock': iso(clock())}
                else:
                    raise ServiceError(404, 'Unknown isolated fixture route')
            self.reply(200, value)
        except ServiceError as error:
            self.reply(error.status, {'error': str(error)})
        except Exception as error:
            self.reply(500, {'error': type(error).__name__})

    def reply(self, status, value):
        raw = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
print(json.dumps({'endpoint': f'http://127.0.0.1:{server.server_port}', 'isolatedState': str(state)}), flush=True)
try:
    for line in sys.stdin:
        if line.strip() == 'stop':
            break
finally:
    server.shutdown()
    server.server_close()
    judge.release.set()
    service.close()
