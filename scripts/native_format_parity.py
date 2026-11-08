"""Compare real pinned formatters through Rust IPC and the current Python service.

All personal journals are disposable. Only the explicit public source and pinned
tool directories are read; code is formatted, never compiled or executed.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/common'), str(ROOT / 'scripts')]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--tools-root', type=Path, required=True)
    args = parser.parse_args()
    source = args.source_root.resolve()
    os.environ['TB_OFFLINE'] = '1'
    os.environ['TB_FORMATTERS_ROOT'] = str(args.tools_root.resolve())
    from build_native_catalog import public_store
    from code_format import format_code
    from training import TrainingService, ServiceError

    work = Path(tempfile.mkdtemp(prefix='native-format-', dir=ROOT / '.backups'))
    now = dt.datetime(2026, 11, 8, tzinfo=dt.timezone.utc)
    env = {**os.environ, 'TB_NATIVE_TEST_NOW': now.isoformat()}
    process = subprocess.Popen(
        [str(ROOT / 'target/debug/tobe-core.exe'), 'sandbox', str(source), str(work / 'native')],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding='utf8', env=env,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    counter = 0
    token = None
    checks = []

    def rpc(path, body=None, query=None, override=None):
        nonlocal counter
        counter += 1
        request = {'version': 1, 'id': str(counter), 'method': 'GET' if body is None else 'POST',
                   'path': path, 'query': query or {}}
        if body is not None:
            request.update(body=body, token=token)
        request.update(override or {})
        process.stdin.write(json.dumps(request, ensure_ascii=False) + '\n')
        process.stdin.flush()
        line = process.stdout.readline()
        if not line:
            raise RuntimeError(process.stderr.read())
        return json.loads(line)

    def fingerprint(path):
        with sqlite3.connect(path) as db:
            return hashlib.sha256('\n'.join(db.iterdump()).encode()).hexdigest()

    legacy_db = sqlite3.connect(work / 'legacy.sqlite3', isolation_level=None)
    legacy_db.row_factory = sqlite3.Row
    legacy_db.executescript((ROOT / 'backend-rust/schema/personal.sql').read_text('utf8'))
    store = public_store(source / 'data/library.sqlite3')
    legacy = TrainingService.__new__(TrainingService)
    legacy.connection = legacy_db
    legacy.lock = threading.RLock()
    legacy.store = store
    legacy.db_path = work / 'legacy.sqlite3'
    legacy.clock = lambda: now
    legacy.closed = False
    legacy.admin_mode = False
    legacy._insights_signature = lambda _: None
    try:
        account = rpc('account')
        assert account['ok'] and account['data']['sandbox']
        token = account['data']['token']
        native_path = work / 'native/personal.sqlite3'
        identity = 'ABC 469::A'
        problem = rpc('problem', query={'id': [identity]})
        assert problem['ok'] and problem['data']['formattingAvailable'], problem
        before = [fingerprint(p) for p in (work / 'legacy.sqlite3', native_path)]

        def compare(name, body):
            actual = rpc('code/format', body)
            try:
                expected = format_code(legacy, body)
            except ServiceError as error:
                assert not actual['ok'] and actual['error']['status'] == error.status, (name, actual, str(error))
            else:
                if not actual['ok'] or actual['data'] != expected:
                    (work / (name + '.json')).write_text(json.dumps(
                        {'expected': expected, 'actual': actual}, ensure_ascii=False, indent=2), 'utf8')
                    raise AssertionError(f'{name}: output differs, see {work}')
                original = body['code'].encode('utf-16-le')
                for edit in reversed(actual['data']['changes']):
                    original = original[:edit['from'] * 2] + edit['insert'].encode('utf-16-le') + original[edit['to'] * 2:]
                assert original.decode('utf-16-le') == expected['code'], name
            checks.append(name)
            print('PASS', name, flush=True)

        snippets = [
            ('cpp-unicode', 'cpp17', '// 中文🦆\n#include <iostream>\nint main(){for(int i=0;i<3;i++){std::cout<<i;}}'),
            ('cpp-crlf', 'cpp17', '#include <vector>\r\nint f(int a,int b){return a+b;}\r\n'),
            ('cpp-comments', 'cpp17', '// preserve ++i in source\nint main(){int i=0; ++i;return i;}'),
            ('python-unicode', 'python3', '# 中文🦆\ns="一个字符串"\nfor i in range(3):\n print(i,s)\n'),
            ('python-crlf', 'python3', 'def f(a,b):\r\n return {"a":a,"b":b}\r\n'),
            ('python-invalid', 'python3', 'def (: \n'),
            ('cpp-blank', 'cpp17', '\t \n'),
            ('python-empty', 'python3', ''),
            ('code-size-limit', 'cpp17', 'x' * 65537),
            ('multibyte-size-limit', 'python3', '中' * 22000),
            ('invalid-language', 'rust', 'fn main(){}'),
            ('null-language', None, 'int x;'),
            ('numeric-language', 17, 'int x;'),
        ]
        for name, language, code in snippets:
            compare(name, {'id': identity, 'code': code, 'language': language})
        compare('explicit-contest', {'id': identity, 'code': 'int x;', 'contestId': 'timed'})
        compare('unknown-problem', {'id': 'missing-format-test', 'code': 'int x;'})
        assert not rpc('code/format', {'id': identity, 'code': 'int x;'}, override={'token': 'wrong'})['ok']
        checks.append('session-token-required')
        assert not rpc('code/format', {'id': identity, 'code': 'int x;'}, override={'owner': 'wrong'})['ok']
        checks.append('owner-isolation')
        after = [fingerprint(p) for p in (work / 'legacy.sqlite3', native_path)]
        assert before == after, 'Formatting changed a private journal'
        checks.append('formatting-preserves-private-journals')
        slots = json.dumps([{'letter': 'A', 'id': identity, 'title': 'format fixture', 'statementAvailable': True}])
        sql = 'INSERT INTO contests(id,name,status,started_at,deadline,duration,slots) VALUES (?,?,?,?,?,?,?)'
        values = ('format-test', 'isolated running fixture', 'running', now.isoformat(),
                  (now + dt.timedelta(hours=5)).isoformat(), 300, slots)
        legacy_db.execute(sql, values)
        with sqlite3.connect(native_path) as db:
            db.execute(sql, values)
        actual = rpc('code/format', {'id': identity, 'code': 'int x;'})
        assert not actual['ok'] and actual['error']['status'] == 409, actual
        try:
            format_code(legacy, {'id': identity, 'code': 'int x;'})
        except ServiceError as error:
            assert error.status == 409
        else:
            raise AssertionError('Running contest did not lock Python formatter')
        checks.append('running-contest-locked')
        result = {'checks': checks, 'passed': len(checks), 'realPinnedTools': True,
                  'isolatedPersonalState': True, 'officialSubmissions': 0, 'sourceRoot': str(source)}
        (work / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), 'utf8')
        print(json.dumps({'passed': len(checks), 'result': str(work / 'result.json')}, ensure_ascii=False))
    finally:
        process.stdin.close()
        process.wait(timeout=10)
        legacy_db.close()


if __name__ == '__main__':
    main()
