"""Verify real native local runs against the current judge using public data only.

Python orchestrates the comparison. Rust never invokes the legacy backend.
The isolated journal, compiler files and source programs are disposable.
"""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import queue
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'backend'), str(ROOT / 'backend/common'), str(ROOT / 'scripts')]


class Native:
    def __init__(self, executable, state, cpp, python, *, test_clock=None):
        environment = dict(os.environ, TB_NATIVE_CPP17=str(cpp), TB_NATIVE_PYTHON3=str(python))
        environment.pop('TB_NATIVE_TEST_NOW', None)
        if test_clock is not None:
            environment['TB_NATIVE_TEST_NOW'] = test_clock
        self.process = subprocess.Popen([str(executable), 'sandbox', str(ROOT), str(state)],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        text=True, encoding='utf-8', env=environment)
        self.responses = queue.Queue()
        def read():
            for line in self.process.stdout:
                try:
                    self.responses.put(json.loads(line))
                except ValueError:
                    self.responses.put({'ok': False, 'error': {'code': 'INVALID_NATIVE_RESPONSE'}})
        threading.Thread(target=read, daemon=True).start()
        self.token = self.call('account')['token']
        self.owner = self.call('api/capabilities')['owner']

    def call(self, path, body=None, query=None, request_id=None):
        request = {'version': 1, 'id': request_id or uuid.uuid4().hex, 'method': 'POST' if body is not None else 'GET',
                   'path': path, 'query': {k: [v] for k, v in (query or {}).items()}}
        if body is not None:
            request.update(body=body, token=self.token, owner=self.owner)
        self.process.stdin.write(json.dumps(request, ensure_ascii=False) + '\n')
        self.process.stdin.flush()
        response = self.responses.get(timeout=15)
        assert response.get('ok'), response.get('error')
        return response['data']

    def finished(self, identity):
        deadline = time.monotonic() + 35
        while time.monotonic() < deadline:
            record = self.call('submission', query={'id': identity})['submission']
            if record.get('finishedAt'):
                return record
            time.sleep(.02)
        raise AssertionError('Native run did not finish')

    def close(self):
        self.process.stdin.close()
        try:
            self.process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)
            raise AssertionError('Native lifecycle did not terminate its owned jobs')
        assert self.process.returncode == 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--cpp', type=Path, required=True)
    parser.add_argument('--python', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    for path in [args.native, args.cpp, args.python]:
        assert path.is_absolute() and path.is_file()
    os.environ['TB_OFFLINE'] = '1'
    from build_native_catalog import public_store
    from assets import AssetLibrary
    from judge import Judge
    seed = ROOT / 'data/library.sqlite3'
    before = seed.stat().st_size, seed.stat().st_mtime_ns
    with closing(sqlite3.connect((ROOT / 'data/native-catalog.sqlite3').as_uri() + '?mode=ro', uri=True)) as catalog:
        identity = catalog.execute("SELECT id FROM catalogue WHERE json_extract(compact,'$.url') LIKE '%/problem/P1001' LIMIT 1").fetchone()[0]
    checked = []
    with tempfile.TemporaryDirectory(prefix='ToBe-native-run-parity-') as temporary:
        scratch = Path(temporary)
        reference = Judge(AssetLibrary(public_store(seed), cache_dir=scratch / 'public-cache'), scratch / 'reference-runs')
        reference.compiler = str(args.cpp)
        reference.python = str(args.python)
        native = Native(args.native, scratch / 'native-state', args.cpp, args.python)
        try:
            draft = 'int preservedDraft = 1; // 私人草稿 😀\n'
            native.call('draft', {'id': identity, 'code': draft, 'language': 'cpp17'})
            cases = [
                ('cpp17', '#include <iostream>\nint main(){long long a,b;std::cin>>a>>b;std::cout<<a+b<<"\\n";}\n', True, ''),
                ('python3', 'a,b=map(int,input().split()); print(a+b)\n# 中文 😀\n', False, '20 22\n'),
                ('python3', 'print(99999)\n', True, ''),
                ('cpp17', '#error EXPECTED_COMPILER_DIAGNOSTIC\n', True, ''),
            ]
            for language, code, samples, input_text in cases:
                body = {'id': identity, 'code': code, 'mode': 'run', 'language': language, 'sampleRun': samples, 'input': input_text}
                request_id = uuid.uuid4().hex
                started = time.monotonic()
                queued = native.call('submissions', body, request_id=request_id)['submission']
                queued_ms = (time.monotonic() - started) * 1000
                assert queued_ms < 1500
                result = native.finished(queued['id'])
                expected = reference.execute(identity, code, 'run', input_text, sample_run=samples, language=language)
                assert result['verdict'] == expected['verdict'], (language, result['verdict'], expected['verdict'])
                assert result['passed'] == expected['passed'] and result['total'] == expected['total']
                assert result['scope'] == 'samples' and result['code'] == code and result['language'] == language
                for actual, old in zip(result['caseResults'], expected['caseResults'], strict=True):
                    for field in ['input', 'expected', 'actual', 'verdict', 'exitCode']:
                        assert actual[field] == old[field], (language, field)
                repeated = native.call('submissions', body, request_id=request_id)['submission']
                assert repeated['id'] == queued['id']
                checked.append({'language': language, 'sampleRun': samples, 'verdict': result['verdict'],
                                'cases': len(result['caseResults']), 'queueMillis': round(queued_ms, 3),
                                'sourceSha256': hashlib.sha256(code.encode()).hexdigest(), 'idempotentRetry': True})
            # The slim public seed may reference an optional remote picture.
            # This offline runner comparison reads the saved draft directly;
            # statement/resource hydration has its own full service checks.
            exported = native.call('data/export')
            assert any(row['problem_id'] == identity and row['context'] == '' and row['code'] == draft
                       for row in exported['tables']['drafts'])
            with closing(sqlite3.connect(scratch / 'native-state/personal.sqlite3')) as db:
                assert db.execute('SELECT count(*) FROM submissions').fetchone()[0] == len(cases)
                assert db.execute("SELECT count(*) FROM submissions WHERE verdict='AC' OR scope='official'").fetchone()[0] == 0
                assert db.execute('SELECT count(*) FROM training WHERE accepted_at IS NOT NULL').fetchone()[0] == 0
                assert db.execute('SELECT count(*) FROM submissions WHERE finished_at IS NULL').fetchone()[0] == 0
        finally:
            native.close()
    assert before == (seed.stat().st_size, seed.stat().st_mtime_ns)
    with args.native.open('rb') as stream:
        binary_sha = hashlib.file_digest(stream, 'sha256').hexdigest()
    report = {'ok': True, 'at': datetime.now(timezone.utc).isoformat(), 'identity': identity, 'checked': checked,
              'actualCompilers': True, 'actualProblemSiteSubmissions': 0, 'nativeBinarySha256': binary_sha,
              'privateCodeDraftIdentityTrainingPreserved': True, 'publicSeedUnmodified': True,
              'legacyBackendFallback': False, 'officialAcClaims': 0}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
