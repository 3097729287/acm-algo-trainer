"""Exercise all fixed full local suites through an explicit release Rust IPC process.

The old backend is a read-only comparison oracle for two audited profiles only.
No native runtime delegates grading, HTTP or account state to it.
"""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'backend'), str(ROOT / 'backend/common'), str(ROOT / 'scripts')]
from native_run_parity import Native


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--cpp', type=Path, required=True)
    parser.add_argument('--python', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    for path in (args.native, args.cpp, args.python):
        assert path.is_absolute() and path.is_file()
    os.environ['TB_OFFLINE'] = '1'
    from build_native_catalog import public_store
    from assets import AssetLibrary
    from judge import Judge
    manifest = json.loads((ROOT / 'backend-rust/resources/reviewed_cases/manifest.json').read_text('utf8'))
    identities = [item['profile_id'] for item in manifest['profiles']]
    archived = json.loads((ROOT / 'data/library/solutions.json').read_text('utf8'))
    cpp = {}
    for row in archived:
        if row['problem_id'] not in identities or row['problem_id'] in cpp:
            continue
        sources = re.findall(r'```(?:cpp|c\+\+)\s*\n(.*?)```', row['markdown'], re.S)
        cpp[row['problem_id']] = next(text for text in sources if re.search(r'\bmain\s*\(', text))
    assert set(cpp) == set(identities)
    programs = (ROOT / 'backend-rust/tests/reviewed_programs.py').read_text('utf8').split('\nif __name__')[0]
    seed = ROOT / 'data/library.sqlite3'
    before = seed.stat().st_size, seed.stat().st_mtime_ns
    checks = []
    with tempfile.TemporaryDirectory(prefix='ToBe-native-reviewed-submit-') as temporary:
        scratch = Path(temporary)
        reference = Judge(AssetLibrary(public_store(seed), cache_dir=scratch / 'public-cache'), scratch / 'reference-runs')
        reference.compiler, reference.python = str(args.cpp), str(args.python)
        native = Native(args.native, scratch / 'native-state', args.cpp, args.python)
        saved = {}
        try:
            sentinel = 'int unrelatedPrivateDraft = 7; // retained 😀\n'
            native.call('draft', {'id': 'luogu-training-P1001', 'code': sentinel, 'language': 'cpp17'})
            for identity in identities:
                started = time.monotonic()
                request_id = uuid.uuid4().hex
                body = {'id': identity, 'mode': 'submit', 'language': 'cpp17', 'code': cpp[identity]}
                queued = native.call('submissions', body, request_id=request_id)['submission']
                queue_ms = (time.monotonic() - started) * 1000
                receipt = native.finished(queued['id'])
                assert receipt['verdict'] == 'SAMPLE_PASS', (identity, receipt['verdict'], receipt['message'])
                assert receipt['scope'] == 'local' and receipt['mode'] == 'submit'
                extra = next(p['case_count'] for p in manifest['profiles'] if p['profile_id'] == identity)
                assert receipt['total'] > extra and receipt['passed'] == receipt['total']
                assert receipt['reviewRewardXp'] == 0
                assert all(c['input'] == '' and c['actual'] == '' and c['expected'] is None
                           for c in receipt['caseResults'])
                assert native.call('submissions', body, request_id=request_id)['submission']['id'] == receipt['id']
                old_checked = identity in ('入门赛 49::D', '周赛 164::C')
                if old_checked:
                    expected = reference.execute(identity, cpp[identity], 'submit', language='cpp17')
                    for key in ('verdict', 'scope', 'passed', 'total'):
                        assert receipt[key] == expected[key], (identity, key, receipt[key], expected[key])
                    for actual, old in zip(receipt['caseResults'], expected['caseResults'], strict=True):
                        for key in ('name', 'input', 'actual', 'expected', 'verdict', 'exitCode'):
                            assert actual[key] == old[key], (identity, key)
                saved[receipt['id']] = (identity, receipt['passed'])
                checks.append({'identity': identity, 'language': 'cpp17', 'verdict': receipt['verdict'],
                               'passed': receipt['passed'], 'originalSamples': receipt['total'] - extra,
                               'auditedExtraCases': extra, 'queueMillis': round(queue_ms, 3),
                               'oldJudgeCompared': old_checked, 'idempotent': True})
            for identity in ('入门赛 49::D', '周赛 164::C'):
                code = programs + f'\nprint(PROGRAMS[{identity!r}](sys.stdin.buffer.read()))\n'
                queued = native.call('submissions', {'id': identity, 'mode': 'submit', 'language': 'python3', 'code': code})['submission']
                receipt = native.finished(queued['id'])
                assert receipt['verdict'] == 'SAMPLE_PASS', (identity, receipt)
                assert receipt['scope'] == 'local' and receipt['passed'] == receipt['total']
                assert receipt['reviewRewardXp'] == 0
                saved[receipt['id']] = (identity, receipt['passed'])
                checks.append({'identity': identity, 'language': 'python3', 'verdict': receipt['verdict'], 'passed': receipt['passed']})
            exported = native.call('data/export')['tables']
            assert any(row['problem_id'] == 'luogu-training-P1001' and row['context'] == '' and row['code'] == sentinel
                       for row in exported['drafts'])
            with closing(sqlite3.connect(scratch / 'native-state/personal.sqlite3')) as db:
                assert db.execute('SELECT COUNT(*) FROM submissions').fetchone()[0] == len(saved)
                assert db.execute("SELECT COUNT(*) FROM submissions WHERE verdict='AC' OR scope='official' OR finished_at IS NULL").fetchone()[0] == 0
                assert db.execute('SELECT COUNT(*) FROM training WHERE accepted_at IS NOT NULL').fetchone()[0] == 0
                assert db.execute("SELECT COUNT(*) FROM account_preferences WHERE key LIKE 'review-reward:%'").fetchone()[0] == 0
        finally:
            native.close()
        reopened = Native(args.native, scratch / 'native-state', args.cpp, args.python)
        try:
            for sid, (identity, count) in saved.items():
                receipt = reopened.call('submission', query={'id': sid})['submission']
                assert receipt['id'] == sid and receipt['passed'] == count and receipt['verdict'] == 'SAMPLE_PASS'
            assert len(reopened.call('data/export')['tables']['submissions']) == len(saved)
        finally:
            reopened.close()
    assert before == (seed.stat().st_size, seed.stat().st_mtime_ns)
    report = {'ok': True, 'at': datetime.now(timezone.utc).isoformat(), 'checks': checks,
              'actualNativeServiceSubmissions': len(checks), 'fixedProfiles': len(identities),
              'totalPassedCases': sum(item['passed'] for item in checks),
              'oldJudgeProfilesCompared': 2, 'reopenDidNotReexecute': True,
              'nativeBinarySha256': hashlib.file_digest(args.native.open('rb'), 'sha256').hexdigest(),
              'publicSeedUnmodified': True, 'realPersonalDataReadOrWritten': False,
              'officialSiteSubmissions': 0, 'officialAcClaims': 0, 'reviewRewards': 0,
              'runtimePythonBackendFallback': False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({key: value for key, value in report.items() if key != 'checks'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
