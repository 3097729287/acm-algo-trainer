"""Local persistence plus optional real public rendering; no logins or chats."""
import argparse
import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import uuid

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--include-real-public-page', action='store_true')
parser.add_argument('--only-real', action='store_true')
args = parser.parse_args()
case = ROOT / '.backups' / ('deepseek-native-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8])
case.mkdir(parents=True, exist_ok=False)


class OwnSite(BaseHTTPRequestHandler):
    def do_GET(self):
        seed = self.path == '/seed'
        body = ('<!doctype html><h1>Owned persistence verification</h1><script>' +
                ('document.cookie="tb_deepseek_probe=kept; Max-Age=86400; Path=/; SameSite=Lax";localStorage.setItem("tb-deepseek-probe","kept");' if seed else '') +
                '</script>').encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *_):
        pass


server = ThreadingHTTPServer(('127.0.0.1', 0), OwnSite)
threading.Thread(target=server.serve_forever, daemon=True).start()
origin = 'http://127.0.0.1:' + str(server.server_port)
results = []
try:
    phases = ('real',) if args.only_real else ('seed', 'verify', *(('real',) if args.include_real_public_page else ()))
    for phase in phases:
        command = [sys.executable, '-B', str(ROOT / 'desktop/tests/deepseek_native_probe.py'), '--case', str(case), '--phase', phase]
        if phase != 'real':
            command += ['--origin', origin]
        process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
        print(json.dumps({'nativeProbePid': process.pid, 'phase': phase, 'case': str(case)}), flush=True)
        try:
            stdout, stderr = process.communicate(timeout=65)
        except subprocess.TimeoutExpired:
            # Only this exact child PID belongs to this harness.
            process.kill()
            stdout, stderr = process.communicate()
        (case / ('stdout-' + phase + '.log')).write_bytes(stdout)
        (case / ('stderr-' + phase + '.log')).write_bytes(stderr)
        result_path = case / ('result-' + phase + '.json')
        result = json.loads(result_path.read_text('utf8')) if result_path.exists() else {'ok': False, 'errorClass': 'NoChildReceipt'}
        results.append({'phase': phase, 'exit': process.returncode, 'ok': result['ok'], 'pid': process.pid})
        print(json.dumps(results[-1]), flush=True)
        if process.returncode or not result['ok']:
            break
finally:
    server.shutdown()
    server.server_close()
report = {'ok': all(r['ok'] and r['exit'] == 0 for r in results) and len(results) == len(phases),
          'testedPhases': list(phases),
          'sequentialNativeWindowsOnly': True, 'case': str(case), 'results': results,
          'defaultBrowserCookiesReadOrCopied': False, 'ordinaryProgramControlled': False, 'realDeepseekLoginOrChatAttempted': False}
(case / 'result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(json.dumps(report), flush=True)
raise SystemExit(0 if report['ok'] else 1)
