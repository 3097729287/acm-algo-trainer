"""Loopback-only adapter fixture. The test browser intercepts every site request."""
import json
import os
from pathlib import Path
import sys
import queue
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[2]
for folder in ('backend', 'backend/common', 'desktop'):
    sys.path.insert(0, str(ROOT / folder))
from external_browser import BrowserProcess, ExternalBrowserBridge

saved = []
prepared = queue.Queue()


class FixtureBrowser(BrowserProcess):
    def __init__(self, profile):
        super().__init__(profile)
        self.profile = self.root  # The intercepted Playwright browser owns this explicit fixture profile.

    def new_page(self, *args, **kwargs):
        # Playwright creates and fully guards the blank tab first. Only then
        # may the real Python CDP transport navigate it to a fixture hostname.
        identity = prepared.get(timeout=10)
        self.ensure()
        return next(item for item in self.request('/json/list') if item['id'] == identity)


FixtureBrowser.new_submission_page = FixtureBrowser.new_page

bridge = ExternalBrowserBridge(Path(os.environ['TB_EXTERNAL_FIXTURE_PROFILE']),
    browser_process=FixtureBrowser(Path(os.environ['TB_EXTERNAL_FIXTURE_PROFILE'])),
    on_receipt=lambda sid, value: saved.append({key:value.get(key) for key in ('sessionId','platform','verdict','submissionId')}) or True)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        target = urlsplit(self.path)
        if target.path == '/prepare':
            identity = parse_qs(target.query)['id'][0]
            prepared.put(identity)
            value = {'attached': True}
        elif target.path == '/create':
            query = parse_qs(target.query)
            value = bridge.submit(query['url'][0], 'int main(){}', 'isolated fixture')
        elif target.path == '/ack':
            value=bridge.acknowledge(parse_qs(target.query)['id'][0])
        elif target.path == '/saved':
            value = saved
        elif target.path == '/status':
            value = [bridge.status(identity) for identity in bridge.sessions]
        else:
            self.send_error(404)
            return
        data = json.dumps(value).encode()
        self.send_response(200)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(('127.0.0.1',0), Handler)
print(json.dumps({'port':server.server_port}),flush=True)
server.serve_forever()
