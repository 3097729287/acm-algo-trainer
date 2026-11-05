"""Compare migrated APIs with the real legacy implementation on disposable state."""
from contextlib import contextmanager
from pathlib import Path
import argparse
import datetime as dt
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/common')]
os.environ['TB_OFFLINE'] = '1'


class LegacyState:
    def __init__(self, path):
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.lock = threading.RLock()

    def _now(self):
        return dt.datetime.now(dt.timezone.utc)

    @contextmanager
    def _write(self):
        with self.connection:
            yield self.connection


def run(binary, report):
    import initial_code
    import code_templates
    import wiki
    import training
    with tempfile.TemporaryDirectory(prefix='tobe-native-parity-', dir=ROOT / '.backups') as folder:
        sandbox = Path(folder)
        process = subprocess.Popen([str(binary), 'sandbox', str(ROOT), str(sandbox)], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8',
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        sequence = 0

        def rpc(path, body=None, query=None, token=None):
            nonlocal sequence
            sequence += 1
            message = {'version': 1, 'id': str(sequence), 'method': 'POST' if body is not None else 'GET', 'path': path, 'query': query or {}}
            if body is not None:
                message['body'] = body
                message['token'] = token
            process.stdin.write(json.dumps(message, ensure_ascii=False) + '\n')
            process.stdin.flush()
            line = process.stdout.readline()
            if not line:
                raise RuntimeError(process.stderr.read())
            result = json.loads(line)
            if not result['ok']:
                raise RuntimeError(result['error'])
            return result['data']

        checks = []
        timing = []
        state = None
        try:
            account = rpc('account')
            state = LegacyState(sandbox / 'personal.sqlite3')

            def compare(name, native, legacy):
                start = time.perf_counter_ns()
                expected = legacy()
                legacy_time = time.perf_counter_ns() - start
                start = time.perf_counter_ns()
                actual = native()
                native_time = time.perf_counter_ns() - start
                if expected != actual:
                    expected_file = sandbox / (name + '-legacy.json')
                    actual_file = sandbox / (name + '-rust.json')
                    expected_file.write_text(json.dumps(expected, ensure_ascii=False, indent=2), encoding='utf-8')
                    actual_file.write_text(json.dumps(actual, ensure_ascii=False, indent=2), encoding='utf-8')
                    raise AssertionError(f'{name}: native/legacy mismatch; {expected_file}, {actual_file}')
                checks.append(name)
                timing.append({'name': name, 'legacyDirectMicros': legacy_time // 1000,
                               'nativeCliRoundTripMicros': native_time // 1000})

            compare('initial-defaults', lambda: rpc('initial-code'), lambda: initial_code.catalog(state))
            compare('template-catalog', lambda: rpc('templates'), lambda: code_templates.catalog(state))
            for query in ['', '动态规划', 'dp', 'binary search']:
                compare('wiki-' + str(len(checks)), lambda q=query: rpc('wiki', query={'q': [q]}), lambda q=query: wiki.read(q))
            articles = rpc('wiki')['articles']
            for index in [0, len(articles) // 2, len(articles) - 1]:
                identity = articles[index]['id']
                compare('wiki-article-' + str(index), lambda identity=identity: rpc('wiki', query={'id': [identity]}),
                        lambda identity=identity: wiki.read(identity=identity))
            for language in ['cpp17', 'python3']:
                result = rpc('initial-code/save', {'title': '兼容性验证', 'language': language, 'code': 'int main() {}' if language == 'cpp17' else 'print("中文")'}, token=account['token'])
                compare('initial-saved-' + language, lambda: rpc('initial-code'), lambda: initial_code.catalog(state))
                identity = result['template']['id']
                revision = rpc('initial-code')['revisions'][language]
                rpc('initial-code/select', {'id': identity, 'language': language, 'revision': revision}, token=account['token'])
                compare('initial-selected-' + language, lambda: rpc('initial-code'), lambda: initial_code.catalog(state))
                rpc('initial-code/save', {'id': identity, 'revision': result['template']['revision'], 'delete': True}, token=account['token'])
                compare('initial-deleted-' + language, lambda: rpc('initial-code'), lambda: initial_code.catalog(state))
            custom = rpc('templates/save', {'title': '自定义模板', 'category': '', 'language': 'cpp17', 'code': 'int x;', 'notes': '原有注释'}, token=account['token'])
            compare('custom-template-saved', lambda: rpc('templates'), lambda: code_templates.catalog(state))
            rpc('templates/save', {'id': custom['template']['id'], 'revision': custom['template']['revision'], 'delete': True}, token=account['token'])
            compare('custom-template-deleted', lambda: rpc('templates'), lambda: code_templates.catalog(state))
            for identity, context in [('A', ''), ('题目::B', 'contest-123')]:
                expected_key = 'draft-language:' + __import__('hashlib').sha256((identity + '\0' + context).encode()).hexdigest()
                assert training.TrainingService._draft_language_key(identity, context) == expected_key
                checks.append('legacy-draft-language-key-' + identity)
            result = {'passed': len(checks), 'checks': checks, 'timing': timing,
                      'measurementScope': 'Same local read APIs, Python direct calls versus Rust CLI round trip; not full application performance',
                      'source': str(ROOT), 'binary': str(binary), 'personalDataUsed': False}
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            print(f'{len(checks)} real legacy/Rust compatibility checks passed: {report}')
        finally:
            if state:
                state.connection.close()
            process.stdin.close()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary', type=Path, default=ROOT / 'target/debug/tobe-core.exe')
    parser.add_argument('--report', type=Path, default=ROOT / '.backups/native-parity.json')
    args = parser.parse_args()
    run(args.binary.resolve(), args.report.resolve())
