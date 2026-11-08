"""Compare actual legacy/Rust goal business on generated independent journals.

Only random creation IDs are aligned. Allocation, outputs, receipts, drafts and
persisted records are compared without rewriting either implementation's logic.
"""
import argparse
from contextlib import contextmanager
import datetime as dt
import difflib
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import uuid
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/common'), str(ROOT / 'scripts')]
os.environ['TB_OFFLINE'] = '1'


def run(binary, output):
    from build_native_catalog import public_store, signature
    from catalog_payload import project_row
    from training import TrainingService, ServiceError
    from goals import Goals
    from assets import AssetLibrary
    work = Path(tempfile.mkdtemp(prefix='native-goals-', dir=ROOT / '.backups'))
    state = work / 'native'
    state.mkdir()
    binary = binary.resolve(strict=True)
    now = [dt.datetime(2026, 11, 6, 4, tzinfo=dt.timezone.utc)]
    process = None
    token = None
    counter = 0
    checks = []
    guards = []

    def rpc(path, body=None, query=None, fail=False):
        nonlocal counter
        counter += 1
        request = {'version': 1, 'id': str(counter), 'method': 'GET' if body is None else 'POST',
                   'path': path, 'query': {k: [str(v)] for k, v in (query or {}).items()}}
        if body is not None:
            request.update(body=body, token=token)
        process.stdin.write(json.dumps(request, ensure_ascii=False) + '\n')
        process.stdin.flush()
        line = process.stdout.readline()
        if not line:
            raise RuntimeError(process.stderr.read())
        response = json.loads(line)
        if not response['ok']:
            if fail:
                return response['error']
            raise AssertionError((path, response['error']))
        if fail:
            raise AssertionError('Expected a rejected request')
        return response['data']

    def launch():
        nonlocal process, token
        process = subprocess.Popen([str(binary), 'sandbox', str(ROOT), str(state)],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, encoding='utf8', env={**os.environ, 'TB_NATIVE_TEST_NOW': now[0].isoformat()},
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        token = rpc('account')['token']

    def stop():
        if process and process.poll() is None:
            process.stdin.close()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                raise
            assert process.returncode == 0

    def advance(**delta):
        stop()
        now[0] += dt.timedelta(**delta)
        launch()

    launch()
    native = sqlite3.connect(state / 'personal.sqlite3', isolation_level=None)
    legacy = sqlite3.connect(work / 'legacy.sqlite3', isolation_level=None)
    legacy.row_factory = sqlite3.Row
    legacy.executescript((ROOT / 'backend-rust/schema/personal.sql').read_text('utf8'))
    store = public_store(ROOT / 'data/library.sqlite3')
    rows = store._catalog_rows()
    store.training_data = lambda: {'rows': [project_row(row) for row in rows]}
    store.data = lambda: {'rows': rows}
    store.token = token
    old = TrainingService.__new__(TrainingService)
    old.connection = legacy
    old.lock = threading.RLock()
    old.store = store
    old.db_path = work / 'legacy.sqlite3'
    old.clock = lambda: now[0]
    old.closed = False
    old.admin_mode = False
    old._insights_signature = lambda _: None

    @contextmanager
    def write():
        legacy.execute('BEGIN IMMEDIATE')
        try:
            yield legacy
            legacy.execute('COMMIT')
        except BaseException:
            legacy.execute('ROLLBACK')
            raise

    old._write = write
    assets = AssetLibrary(store, cache_dir=work / 'assets', portable=old.portable_problem)
    original_problem = assets.problem
    assets.problem = lambda identity: original_problem(identity, fetch=False)
    old.assets = assets
    goals = Goals(old)

    def compare(name, actual, expected):
        if actual != expected:
            a = json.dumps(expected, ensure_ascii=False, sort_keys=True, indent=2)
            b = json.dumps(actual, ensure_ascii=False, sort_keys=True, indent=2)
            (work / (name + '-legacy.json')).write_text(a, 'utf8')
            (work / (name + '-rust.json')).write_text(b, 'utf8')
            print('\n'.join(list(difflib.unified_diff(a.splitlines(), b.splitlines(), fromfile='legacy', tofile='rust'))[:150]), flush=True)
            raise AssertionError(f'{name} differs; {work}')
        checks.append(name)
        print('PASS', name, flush=True)
        return actual

    def seed(sql, params=()):
        legacy.execute(sql, params)
        native.execute(sql, params)

    def snapshot(db):
        result = {}
        for table in ['goals', 'goal_daily_assignments', 'practice_sets', 'training', 'drafts', 'submissions']:
            values = []
            for row in db.execute(f'SELECT * FROM {table}'):
                value = list(row)
                names = [v[0] for v in db.execute(f'SELECT * FROM {table} LIMIT 0').description]
                for i, name in enumerate(names):
                    if name in ['config', 'ids', 'slots'] and isinstance(value[i], str):
                        value[i] = json.loads(value[i])
                values.append(value)
            result[table] = sorted(values, key=lambda row: json.dumps(row, ensure_ascii=False, sort_keys=True))
        result['reviews'] = [(r[0], json.loads(r[1]), r[2]) for r in db.execute("SELECT key,value,updated_at FROM account_preferences WHERE key LIKE 'review-%' ORDER BY key")]
        return result

    def persisted(name):
        compare(name, snapshot(native), snapshot(legacy))

    def read(name):
        return compare(name, rpc('goals'), goals.list())

    def workspace(name):
        return compare(name, rpc('workspace'), old.workspace())

    def save(name, body):
        actual = rpc('goals/save', body)
        if not body.get('id'):
            before = {r[0] for r in legacy.execute('SELECT id FROM goals')}
            created = [r[0] for r in native.execute('SELECT id FROM goals') if r[0] not in before]
            assert len(created) == 1
            with patch('goals.uuid.uuid4', return_value=uuid.UUID(hex=created[0].removeprefix('goal-'))):
                expected = goals.save(body)
        else:
            expected = goals.save(body)
        return compare(name, actual, expected)

    def reject(name, body, status=422):
        before = snapshot(native)
        assert rpc('goals/save', body, fail=True)['status'] == status
        try:
            goals.save(body)
        except ServiceError as error:
            assert error.status == status
        else:
            raise AssertionError('Legacy unexpectedly accepted ' + name)
        assert snapshot(native) == before
        guards.append(name)
        print('PASS', name, flush=True)

    def receipt(sid, pid, verdict, at, scope='official', mode='submit'):
        seed('INSERT INTO submissions(id,problem_id,mode,scope,verdict,code,submitted_at,finished_at) VALUES(?,?,?,?,?,?,?,?)',
             (sid, pid, mode, scope, verdict, 'generated test receipt', at, at))

    try:
        read('empty-goals-is-an-actual-empty-list')
        base = {'title': '独立目标甲', 'kind': 'custom', 'deadline': '2026-11-07', 'totalProblems': 4, 'dailyMinutes': 90}
        first = save('custom-goal-allocates-real-tasks', base)
        aid = first['goals'][0]['id']
        second = save('second-goal-reserves-distinct-canonical-tasks', {**base, 'title': '独立目标乙'})
        bid = next(r[0] for r in native.execute('SELECT id FROM goals') if r[0] != aid)
        persisted('creation-allocation-and-training-identical')
        workspace('workspace-marks-real-goal-rows-today')
        read('poll-keeps-the-same-selections')
        assignments = {r[0]: json.loads(r[1]) for r in native.execute('SELECT goal_id,ids FROM goal_daily_assignments')}
        assert len(assignments[aid]) == len(assignments[bid]) == 2
        assert set(assignments[aid]).isdisjoint(assignments[bid])
        apid, bpid = assignments[aid][0], assignments[bid][0]
        compare('ordinary-goal-draft-is-real-code', rpc('draft', {'id': apid, 'code': 'goal draft 😀', 'language': 'python3'}),
                old.save_draft(apid, 'goal draft 😀', language='python3'))
        compare('manual-removal-of-frozen-task', rpc('training/remove', {'id': apid}), old.remove_training(apid))
        seed('UPDATE goal_daily_assignments SET target=NULL')
        workspace('null-legacy-target-repair-preserves-manual-removal')
        persisted('null-target-repair-identical')
        assert native.execute('SELECT active FROM training WHERE id=?', (apid,)).fetchone()[0] == 0
        save('goal-edit-keeps-todays-frozen-target', {**base, 'id': aid, 'title': '改名后的独立目标', 'totalProblems': 8})
        persisted('goal-edit-keeps-both-allocations')
        receipt('local-is-not-a-pass', apid, 'AC', '2026-11-06T04:01:00.000000Z', scope='local')
        receipt('own-official-first-pass', bpid, 'AC', '2026-11-06T04:02:00.000000Z')
        advance(minutes=5)
        accepted = read('only-actual-official-evidence-completes-owned-daily-tasks')
        assert next(g for g in accepted['goals'] if g['id'] == aid)['dailyTask']['progress'] == 0
        assert next(g for g in accepted['goals'] if g['id'] == bid)['dailyTask']['progress'] == 1
        receipt('official-repeat-is-not-new-work', bpid, 'AC', '2026-11-06T04:03:00.000000Z')
        read('duplicate-receipt-cannot-multiply-progress')
        workspace('official-goal-progress-and-ordinary-draft-survive-restart')
        persisted('restart-and-receipt-journals-identical')
        advance(days=1)
        workspace('next-beijing-day-allocates-new-unaccepted-canonical-tasks')
        persisted('next-day-selection-and-training-identical')
        read('next-day-poll-remains-frozen')
        compare('archive-keeps-original-journal-and-draft', rpc('goals/archive', {'id': aid}), goals.archive(aid))
        compare('archive-is-idempotent', rpc('goals/archive', {'id': aid}), goals.archive(aid))
        save('archived-goal-edit-keeps-archived-identity-and-cf-title-inference',
             {**base, 'id': aid, 'title': 'CF 1600 巩固', 'deadline': '2027-05-01', 'currentRating': '1_000', 'targetRating': 999})
        assert native.execute('SELECT archived FROM goals WHERE id=?', (aid,)).fetchone()[0] == 1
        cf_config = json.loads(native.execute('SELECT config FROM goals WHERE id=?', (aid,)).fetchone()[0])
        assert cf_config['kind'] == 'cf' and cf_config['targetRating'] == 1600 and cf_config['totalProblems'] == 180
        persisted('archived-edit-preserves-journals')
        for name, value in [('empty-title', {**base, 'title': ''}), ('invalid-kind', {**base, 'kind': 'bogus'}),
                            ('past-deadline', {**base, 'deadline': '2026-01-01'}),
                            ('malformed-minutes', {**base, 'dailyMinutes': '9__0'}),
                            ('huge-rating', {**base, 'currentRating': 10**100}),
                            ('zero-workload', {**base, 'totalProblems': 0})]:
            reject(name, value)
        reject('unknown-goal-cannot-overwrite-another', {**base, 'id': 'unknown-goal'}, 404)
        compare('archive-last-goal-keeps-daily-history', rpc('goals/archive', {'id': bid}), goals.archive(bid))
        read('no-active-goals-keeps-all-archived-history')
        persisted('archiving-does-not-delete-code-or-history')
        for index in range(10):
            save('active-limit-real-goal-' + str(index + 1), {**base, 'title': '数量上限 ' + str(index), 'totalProblems': 1})
        reject('eleventh-active-goal-does-not-partially-write', {**base, 'title': '不应保存'})
        persisted('ten-goal-independent-allocations-identical')
        # Retained goals predate recently indexed public events. Verify that
        # generated contest groups are genuine legacy practice_sets, not merely
        # a projection that changes with each refresh.
        seed('UPDATE goals SET archived=1')
        recent = save('cf-goal-retains-real-contest-workload',
                      {'title': '区域训练准备', 'kind': 'cf', 'deadline': '2026-11-21',
                       'currentRating': 1200, 'targetRating': 1600, 'dailyMinutes': 240})
        cid = recent['goals'][0]['id']
        seed('UPDATE goals SET created_at=? WHERE id=?', ('2026-11-01T00:00:00.000000Z', cid))
        grouped = workspace('recent-public-contests-create-stable-owned-practice-groups')
        group_count = native.execute("SELECT COUNT(*) FROM practice_sets WHERE id LIKE 'goal-contest:%'").fetchone()[0]
        assert group_count > 0, 'The fixture must include actual eligible recent public events'
        persisted('recent-contest-group-identities-and-created-times-identical')
        ids = [row['id'] for row in grouped['training']]
        compare('clear-goal-and-contest-tasks-through-existing-training-action', rpc('training/clear', {'ids': ids}), old.clear_training(ids))
        workspace('refresh-cannot-reactivate-cleared-contest-groups')
        persisted('cleared-contest-group-journal-remains-identical')
        # A real prior-day official WA creates a nonzero review workload. That
        # single remaining-minute budget must be shared across all goals.
        candidates = [r for r in rows if r.get('platform') == 'Codeforces' and r.get('difficulty')
                      and not r.get('difficultyEstimated') and r.get('catalogContentReady')
                      and not r.get('catalogHidden') and r.get('problemType', 'standard') == 'standard'][:14]
        assert len(candidates) == 14
        for index, row in enumerate(candidates):
            receipt('budget-wa-' + str(index), row['id'], 'WA', '2026-11-07T00:00:00.000000Z')
            seed('INSERT INTO training(id,active_at,active) VALUES(?,?,1) ON CONFLICT(id) DO UPDATE SET active=1,removed_at=NULL',
                 (row['id'], '2026-11-07T00:00:00.000000Z'))
        advance(days=1)
        budget = workspace('real-review-backlog-shares-goal-workload-budget')
        assert budget['reviews']['minutes'] > 0
        save('second-cf-goal-cannot-multiply-remaining-review-budget',
             {'title': '另一份目标', 'kind': 'cf', 'deadline': '2026-11-21',
              'currentRating': 1400, 'targetRating': 1800, 'dailyMinutes': 240})
        budget = workspace('two-active-goals-share-one-real-remaining-minute-budget')
        assert sum(g['dailyTask']['target'] * g['minutesPerProblem'] for g in budget['goals']['goals']) <= budget['reviews']['newMinutes']
        persisted('review-state-goals-and-training-remain-identical')
        daily_before = native.execute('SELECT COUNT(*) FROM goal_daily_assignments').fetchone()[0]
        advance(days=1)
        mainline = {'kind': 'topic', 'title': '当前已采纳主线'}
        seed('INSERT INTO account_preferences(key,value,updated_at) VALUES(?,?,?)',
             ('learning-summary-v1', json.dumps({'config': {'goal': mainline}, 'plan': {'id': 'generated-adopted-plan'}}, ensure_ascii=False), now[0].isoformat()))
        adopted = workspace('adopted-mainline-suppresses-old-goal-rows-without-new-daily-assignment')
        assert adopted['goalTasks'] == [] and adopted['goals']['summaryGoal'] == mainline
        assert native.execute('SELECT COUNT(*) FROM goal_daily_assignments').fetchone()[0] == daily_before
        persisted('adopted-mainline-preserves-existing-goal-journal')
        original = snapshot(native)
        seed('INSERT INTO account_problem_facts VALUES(?,?,?)', ('unported-private-fact', '{}', now[0].isoformat()))
        assert rpc('goals', fail=True)['code'] == 'MIGRATION_PENDING'
        assert rpc('goals/save', {**base, 'id': bid, 'deadline': '2026-11-21'}, fail=True)['code'] == 'MIGRATION_PENDING'
        native.execute("DELETE FROM account_problem_facts WHERE problem_id='unported-private-fact'")
        legacy.execute("DELETE FROM account_problem_facts WHERE problem_id='unported-private-fact'")
        assert snapshot(native) == original
        guards.append('unported-account-facts-do-not-disappear-or-write-a-goal')
        with (ROOT / 'data/library.sqlite3').open('rb') as stream:
            seed_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
        result = {'passed': len(checks), 'checks': checks, 'exactLegacyComparisons': len(checks),
                  'guardsPassed': len(guards), 'guards': guards, 'work': str(work),
                  'nativeSha256': hashlib.sha256(binary.read_bytes()).hexdigest(), 'nativeBinary': str(binary),
                  'privateLiveStateOpened': False, 'officialSubmissionsSent': 0, 'pythonRuntimeFallback': False,
                  'randomIdentityAlignmentOnly': True,
                  'publicSeed': signature(ROOT / 'data/library.sqlite3'),
                  'publicSeedSha256': seed_hash,
                  'publicSeedScope': 'The exact current read-only public seed above; no personal catalogue or live account input.'}
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', 'utf8')
        print(json.dumps(result, ensure_ascii=False), flush=True)
    finally:
        assets.close()
        legacy.close()
        native.close()
        stop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    run(args.native, args.output)
