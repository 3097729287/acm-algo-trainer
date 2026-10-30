"""Account-owned entry assessment, bound to the real full template judge.

The private journal key is deliberately outside editable UI preferences. Cloud
merges keep acknowledgements and the single policy grant monotonic.
"""
import copy
import json
import re
import secrets
import uuid

KEY = 'experience-challenge-v1'
POLICY = 1
PROBLEMS = ('template-drill:binary-search:1', 'template-drill:prefix-difference:1')
_SUBMISSION = re.compile(r'^submission-[a-f0-9]{32}$')


def _owner(training):
    return training._ranking_profile()['user_id']


def _empty(owner):
    return dict(policyVersion=POLICY, owner=owner, seenVersion=0, choice=None,
                problemId=None, challengeId=None, startedAt=None, attempts=[],
                passedAt=None, submissionId=None, awardedXp=None)


def validate(value, owner=None):
    if not isinstance(value, dict) or value.get('policyVersion') != POLICY:
        return None
    if not isinstance(value.get('owner'), str) or owner is not None and value['owner'] != owner:
        return None
    if set(value) != set(_empty(value['owner'])):
        return None
    if type(value.get('seenVersion')) is not int or value['seenVersion'] not in (0, POLICY):
        return None
    if value.get('choice') not in (None, 'beginner', 'experienced'):
        return None
    attempts = value.get('attempts', [])
    if not isinstance(attempts, list) or len(attempts) > 128 or any(not isinstance(v, str) or not _SUBMISSION.fullmatch(v) for v in attempts):
        return None
    if value.get('choice') == 'experienced':
        if value.get('problemId') not in PROBLEMS or not isinstance(value.get('startedAt'), str):
            return None
        try:
            uuid.UUID(value['challengeId'])
        except (ValueError, TypeError, KeyError, AttributeError):
            return None
    elif attempts or any(value.get(field) is not None for field in ('problemId', 'challengeId', 'startedAt', 'passedAt', 'submissionId', 'awardedXp')):
        return None
    if value.get('passedAt'):
        if value.get('choice') != 'experienced' or not isinstance(value['passedAt'], str) or value.get('submissionId') not in attempts:
            return None
    amount = value.get('awardedXp')
    if amount is not None and (not value.get('passedAt') or type(amount) is not int or not 0 <= amount <= 500):
        return None
    return copy.deepcopy(value)


def merge(left, right):
    """Never add two device grants or let an older acknowledgement revoke one."""
    a, b = validate(left), validate(right)
    if not a or not b:
        return a or b
    if a['owner'] != b['owner']:
        return None
    score = lambda v: (bool(v.get('passedAt')), v.get('choice') == 'experienced', v.get('startedAt') or '', v.get('challengeId') or '')
    result = copy.deepcopy(max((a, b), key=score))
    result['seenVersion'] = max(a['seenVersion'], b['seenVersion'])
    # Bound proofs from a different device assignment must not qualify a local
    # answer to another question. Passed grants remain independently durable.
    same = [v for v in (a, b) if v.get('challengeId') == result.get('challengeId')]
    result['attempts'] = sorted(set(x for v in same for x in v.get('attempts', [])))[-128:]
    if result.get('passedAt'):
        result['attempts'] = list(dict.fromkeys([*result['attempts'], result['submissionId']]))[-128:]
        rewards = [v['awardedXp'] for v in (a, b) if v.get('passedAt') and v.get('awardedXp') is not None]
        result['awardedXp'] = max(rewards) if rewards else None
    return result


def read(training):
    row = training.connection.execute('SELECT value FROM account_preferences WHERE key=?', (KEY,)).fetchone()
    try:
        value = validate(json.loads(row[0]), _owner(training)) if row else None
    except (ValueError, TypeError):
        value = None
    return value or _empty(_owner(training))


def preserve_rows(training, rows):
    """An older restored snapshot cannot delete a same-owner earned grant."""
    rows = copy.deepcopy(rows)
    current = training.connection.execute('SELECT * FROM account_preferences WHERE key=?', (KEY,)).fetchone()
    incoming = next((row for row in rows if row.get('key') == KEY), None)
    def parsed(row):
        try:
            return validate(json.loads(row['value']), _owner(training)) if row else None
        except (ValueError, TypeError):
            return None
    local, remote = parsed(current), parsed(incoming)
    joined = merge(local, remote)
    if joined is None:
        return rows, False
    encoded = json.dumps(joined, ensure_ascii=False, sort_keys=True)
    if incoming and validate(remote) == joined:
        return rows, False
    record = dict(current or incoming)
    record['value'] = encoded
    return [row for row in rows if row.get('key') != KEY] + [record], True


def preserve_earned_rows(training, table, rows):
    """Keep the actual immutable XP evidence, not an artificial XP floor.

    A previous same-owner snapshot may predate the assessment. Preserving its
    original ACs/claims means a late copy of those facts deduplicates normally,
    while genuinely new earnings still count in full after restoration.
    """
    keys = {'submissions': ('id',), 'official_first_xp_awards': ('problem_key',),
            'official_xp_state': ('id',), 'achievement_xp_claims': ('achievement_id',),
            'daily_missions': ('day', 'id'), 'ranking_reward_totals': ('endpoint', 'user_id'),
            'account_preferences': ('key',)}.get(table)
    if not keys:
        return rows, False
    def earned(row):
        if table == 'submissions':
            return row.get('mode') == 'submit' and row.get('scope') == 'official' and row.get('verdict') == 'AC' and bool(row.get('finished_at'))
        if table == 'daily_missions':
            try:
                return bool(row.get('claimed_at')) and json.loads(row.get('definition') or '{}').get('version') in (2, 3)
            except (ValueError, TypeError, AttributeError):
                return False
        if table == 'account_preferences':
            return str(row.get('key', '')).startswith('review-reward:')
        if table == 'ranking_reward_totals':
            return row.get('user_id') == _owner(training)
        return True
    result = {tuple(row.get(k) for k in keys): copy.deepcopy(row) for row in rows}
    retained = False
    for local in training.connection.execute(f'SELECT * FROM "{table}"'):
        local = dict(local)
        if not earned(local):
            continue
        key = tuple(local[k] for k in keys)
        remote = result.get(key)
        winner = copy.deepcopy(local if remote is None or not earned(remote) else remote)
        for field in ('awarded_xp', 'total_xp'):
            if field in local:
                winner[field] = max(local[field], winner.get(field, 0))
        for field in ('accepted_at', 'unlocked_at', 'claimed_at', 'migrated_at'):
            stamps = [value for value in (local.get(field), winner.get(field)) if value]
            if field in local and stamps:
                winner[field] = min(stamps)
        if winner != remote:
            result[key] = winner
            retained = True
    return list(result.values()), retained


def _save(training, connection, value):
    from training import iso
    assert validate(value, _owner(training)) is not None
    connection.execute('INSERT INTO account_preferences VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at',
                       (KEY, json.dumps(value, ensure_ascii=False, sort_keys=True), iso(training._now())))


def reward(training, base_xp):
    """A fixed, once-only top-up preserves later normal XP accumulation."""
    from tb_rank import RANK_UNLOCK_XP
    state = read(training)
    if not state.get('passedAt'):
        return 0
    if state.get('awardedXp') is None:
        state['awardedXp'] = max(0, RANK_UNLOCK_XP - max(0, int(base_xp)))
        with training._write() as connection:
            _save(training, connection, state)
    return state['awardedXp']


def snapshot(training, level):
    state = read(training)
    passed = bool(state.get('passedAt'))
    eligible = not training.admin_mode and level < 5 and not passed
    pending = False
    if state['attempts']:
        pending = any(training.connection.execute('SELECT 1 FROM submissions WHERE id=? AND finished_at IS NULL', (identity,)).fetchone() for identity in state['attempts'])
    status = 'passed' if passed else 'judging' if pending else 'active' if state['choice'] == 'experienced' else 'beginner' if state['choice'] == 'beginner' else 'offered'
    return dict(owner=state['owner'], policyVersion=POLICY, eligible=eligible,
                promptRequired=eligible and state['seenVersion'] < POLICY,
                seenVersion=state['seenVersion'], choice=state['choice'], status=status,
                problemId=state['problemId'], allNavigationUnlocked=passed,
                awardedXp=state.get('awardedXp') or 0)


def update(training, body):
    from training import ServiceError, iso
    if not isinstance(body, dict) or body.get('action') not in ('seen', 'choose'):
        raise ServiceError(400, '挑战操作无效')
    allowed = {'action', 'choice'} if body['action'] == 'choose' else {'action'}
    if set(body) != allowed or body['action'] == 'choose' and body.get('choice') not in ('beginner', 'experienced'):
        raise ServiceError(400, '请选择新手或老手')
    initial = training.insights()['growth']
    with training.lock:
        if training.workspace().get('activeContest'):
            raise ServiceError(409, '请先结束正在进行的模拟赛')
        state = read(training)
        if not initial['experienceChallenge']['eligible'] and not state.get('passedAt'):
            raise ServiceError(409, '当前等级已经解锁全部功能')
        state['seenVersion'] = POLICY
        if body['action'] == 'choose' and not state['choice'] and not state.get('passedAt'):
            state['choice'] = body['choice']
            if state['choice'] == 'experienced':
                state.update(problemId=secrets.choice(PROBLEMS), challengeId=str(uuid.uuid4()), startedAt=iso(training._now()))
        with training._write() as connection:
            _save(training, connection, state)
            if state['choice'] == 'experienced' and not state.get('passedAt'):
                training._activate(connection, state['problemId'], state['startedAt'])
    value = training.insights()['growth']
    return {'challenge': value['experienceChallenge'], 'growth': value}


def bind_submission(training, connection, identity, problem_id, mode, scope):
    state = read(training)
    if state.get('passedAt') or state['choice'] != 'experienced' or state['problemId'] != problem_id or mode != 'submit' or scope != 'template':
        return
    state['attempts'] = list(dict.fromkeys([*state['attempts'], identity]))[-128:]
    _save(training, connection, state)


def finish_submission(training, connection, identity):
    from template_drills import bundle
    state = read(training)
    if state.get('passedAt') or identity not in state['attempts']:
        return
    row = connection.execute('SELECT * FROM submissions WHERE id=?', (identity,)).fetchone()
    if not row or row['problem_id'] != state['problemId'] or row['contest_id'] or row['mode'] != 'submit' or row['scope'] != 'template' or row['verdict'] != 'AC' or not row['finished_at'] or row['submitted_at'] < state['startedAt']:
        return
    count = len(bundle(row['problem_id'])['cases'])
    try:
        cases = json.loads(row['case_results'])
    except (ValueError, TypeError):
        return
    if row['passed'] != count or row['total'] != count or not isinstance(cases, list) or len(cases) != count or any(not isinstance(case, dict) or case.get('verdict') != 'SAMPLE_PASS' for case in cases):
        return
    state.update(passedAt=row['finished_at'], submissionId=identity)
    _save(training, connection, state)
