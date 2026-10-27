"""Adaptive, account-owned review plans. No code or acceptance is ever erased.

The decay and interval parameters are scheduling heuristics inspired by spaced
retrieval, not measured probabilities of remembering an algorithm. All durable
state uses the existing synchronized preference journal and draft contexts.
"""
import datetime as dt
import hashlib
import json
import math

from insights import canonical_url
from progression import SHANGHAI, parse_time


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), sort_keys=True)


def task_context(identity):
    return 'review:' + identity


def interval_after_pass(stability, difficulty, ability, failures=0, assisted=False):
    if assisted:
        return 1.0, 1
    relative = difficulty - ability if difficulty is not None and ability is not None else 0
    factor = max(1.5, min(3.2, 2.6 - relative / 650))
    factor *= .78 ** min(3, failures)
    stability = min(75., max(1.1, stability * max(1.2, factor)))
    return round(stability, 3), max(1, min(90, round(stability * 1.2)))


class ReviewScheduler:
    def __init__(self, training):
        self.t = training

    def read(self, key, fallback=None):
        row = self.t.connection.execute('SELECT value FROM account_preferences WHERE key=?', (key,)).fetchone()
        try:
            return json.loads(row['value']) if row else fallback
        except (TypeError, ValueError):
            return fallback

    def save(self, db, key, value):
        from training import iso
        payload = encoded(value)
        old = db.execute('SELECT value FROM account_preferences WHERE key=?', (key,)).fetchone()
        if not old or old['value'] != payload:
            db.execute('INSERT INTO account_preferences VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at',
                       (key, payload, iso(self.t._now())))

    def task(self, identity, review_id, contest_id=None, open_task=False):
        from training import ServiceError, iso
        if not review_id:
            return None
        if contest_id or not isinstance(review_id, str) or len(review_id) != 32:
            raise ServiceError(400, '复习上下文无效')
        item = self.read('review-task:' + review_id)
        if not isinstance(item, dict) or item.get('problemId') not in self.t._equivalent_ids(identity):
            raise ServiceError(404, '没有找到这次复习')
        if not item.get('openedAt') and open_task:
            if item['due'] > self.t._now().astimezone(SHANGHAI).date().isoformat():
                raise ServiceError(409, '这道题还未到复习时间')
            item['openedAt'] = iso(self.t._now())
            with self.t._write() as db:
                self.save(db, 'review-task:' + review_id, item)
        return item

    def bind(self, db, submission_id, review_id):
        if review_id:
            self.save(db, 'review-receipt:' + submission_id, review_id)

    def session(self, db, session_id, review_id):
        if review_id:
            self.save(db, 'review-session:' + session_id, review_id)

    def assisted(self, identity, task, submitted_at):
        if not task or not task.get('openedAt'):
            return False
        ids = self.t._equivalent_ids(identity)
        placeholders = ','.join('?' for _ in ids)
        seen = self.t.connection.execute(f'SELECT MAX(solution_seen_at) FROM training WHERE id IN ({placeholders})', ids).fetchone()[0]
        return bool(seen and task['openedAt'] <= seen <= submitted_at)

    def plan(self):
        t = self.t
        with t.lock, t._library_view():
            return self._plan()

    def _plan(self):
        from training import iso
        from tb_rank import _skill_evidence, MIN_RANK_EVIDENCE
        t = self.t
        now = t._now()
        today = now.astimezone(SHANGHAI).date()
        day = today.isoformat()
        library = t._library()
        # Include content changes, cloud merges and the Beijing date. Saving a
        # draft invalidates cheaply; unchanged UI polling does not replay history.
        signature = (t.connection.total_changes, t.connection.execute('PRAGMA data_version').fetchone()[0],
                     day, tuple((r['id'], r.get('difficulty')) for r in library))
        cached = getattr(t, '_review_plan_cache', None)
        if cached and cached[0] == signature:
            return cached[1]
        metadata = {r['id']: r for r in library}
        aliases = t._identity_map(library)
        active = {aliases.get(r['id'], r['id']) for r in t.connection.execute('SELECT id FROM training WHERE active=1')}
        locked = {aliases.get(s['id'], s['id']) for r in t.connection.execute("SELECT slots FROM contests WHERE status='running'") for s in json.loads(r['slots'])}
        facts = {}
        evidence = []
        for record in t.connection.execute("SELECT * FROM submissions WHERE mode='submit' AND scope='official' AND finished_at IS NOT NULL ORDER BY submitted_at,rowid"):
            if parse_time(record['submitted_at']) > now:
                continue
            identity = aliases.get(record['problem_id'], record['problem_id'])
            facts.setdefault(identity, []).append(dict(record))
            row = metadata.get(identity, {})
            evidence.append({'key': canonical_url(row.get('url')) or identity, 'acceptedAt': record['submitted_at'],
                             'scope': 'official', 'verdict': record['verdict'], 'difficulty': row.get('difficulty'),
                             'independent': not bool(record['solution_seen']), 'independentKnown': True})
        skills = _skill_evidence(evidence, now)
        ability = skills[MIN_RANK_EVIDENCE // 2] if len(skills) >= MIN_RANK_EVIDENCE else None
        preferences = {}
        for r in t.connection.execute("SELECT key,value FROM account_preferences WHERE key LIKE 'review-%'"):
            try:
                preferences[r['key']] = json.loads(r['value'])
            except (ValueError, TypeError):
                continue
        updates = {}

        def create_task(state, anchor, due, identity):
            task_id = hashlib.sha256((state['key'] + '\0' + anchor).encode()).hexdigest()[:32]
            state.update(taskId=task_id, due=due, anchor=anchor)
            key = 'review-task:' + task_id
            if key not in preferences:
                preferences[key] = {'id': task_id, 'problemId': identity, 'problemKey': state['key'],
                                    'due': due, 'openedAt': None, 'completedAt': None, 'failures': [], 'processed': []}
                updates[key] = preferences[key]

        candidates = []
        for identity, receipts in facts.items():
            if identity not in active:
                continue
            accepted = [r for r in receipts if r['verdict'] == 'AC']
            if not accepted:
                continue
            row = metadata.get(identity)
            if not row:
                try:
                    row = t._row(identity)
                except Exception as issue:
                    if getattr(issue, 'status', None) != 404:
                        raise
                    continue
            # Preserve all receipts, draft contexts and prior review tasks. Pure
            # I/O/elementary language exercises simply leave the automatic queue.
            # Scheduling receives compact catalog rows, which intentionally
            # omit the display-only normalization flag. Re-evaluate the stable
            # original URL here so elementary tasks leave the real queue too.
            from difficulty import normalize_practice_difficulty
            if normalize_practice_difficulty(row).get('reviewTrivial'):
                continue
            difficulty = row.get('difficulty')
            if type(difficulty) not in (int, float) or not math.isfinite(difficulty) or difficulty <= 0:
                difficulty = None
            problem_key = canonical_url(row.get('url')) or identity
            state_key = 'review-state:' + hashlib.sha256(problem_key.encode()).hexdigest()
            state = preferences.get(state_key)
            before = encoded(state)
            if not isinstance(state, dict) or state.get('version') != 1:
                # Existing official redos are respected during migration. This
                # introduces overdue history gradually through the daily budget.
                seed = accepted[-1]
                due = (parse_time(seed['submitted_at']).astimezone(SHANGHAI).date() + dt.timedelta(days=1)).isoformat()
                state = {'version': 1, 'key': problem_key, 'stability': 1., 'successes': 0,
                         'lapses': 0, 'lastAt': seed['submitted_at'], 'parked': False}
                create_task(state, seed['id'], due, identity)
            task = preferences.get('review-task:' + state.get('taskId', ''))
            if not isinstance(task, dict):
                create_task(state, state.get('anchor', accepted[-1]['id']), state.get('due') or day, identity)
                task = preferences['review-task:' + state['taskId']]
            task_before = encoded(task)
            if task.get('openedAt') and not task.get('completedAt'):
                processed = set(task.get('processed', []))
                for receipt in receipts:
                    if receipt['id'] in processed or preferences.get('review-receipt:' + receipt['id']) != task['id']:
                        continue
                    # A late result for code accepted before this review opened
                    # cannot complete today's fresh rewrite.
                    if receipt['submitted_at'] < task['openedAt']:
                        continue
                    task['processed'].append(receipt['id'])
                    if receipt['verdict'] in {'WA', 'TLE', 'MLE', 'RE', 'OLE'}:
                        task['failures'].append(receipt['id'])
                        state['lapses'] += 1
                    if receipt['verdict'] == 'AC':
                        assisted = bool(receipt['solution_seen'])
                        failures = len(task['failures'])
                        state['stability'], interval = interval_after_pass(state['stability'], difficulty, ability, failures, assisted)
                        state['successes'] = 0 if assisted else state['successes'] + 1
                        state['lastAt'] = receipt['submitted_at']
                        task.update(completedAt=receipt['finished_at'], independent=not assisted)
                        easy = difficulty is not None and ability is not None and difficulty <= ability - 200
                        state['parked'] = bool(easy and not assisted and not failures)
                        state['due'] = None if state['parked'] else (parse_time(receipt['submitted_at']).astimezone(SHANGHAI).date() + dt.timedelta(days=interval)).isoformat()
                        if state['due']:
                            create_task(state, receipt['id'], state['due'], identity)
                        break
            if encoded(task) != task_before:
                updates['review-task:' + task['id']] = task
            if state.get('parked'):
                failure = next((r for r in reversed(receipts) if r['submitted_at'] > state['lastAt'] and r['verdict'] in {'WA','TLE','MLE','RE','OLE'}), None)
                if failure:
                    state['parked'] = False
                    state['stability'] = 1.
                    create_task(state, failure['id'], (parse_time(failure['submitted_at']).astimezone(SHANGHAI).date() + dt.timedelta(days=1)).isoformat(), identity)
            if encoded(state) != before:
                updates[state_key] = state
            current = preferences.get('review-task:' + state['taskId'])
            if identity not in locked and state.get('due') and state['due'] <= day and current and not current.get('completedAt'):
                elapsed = max(0, (now - parse_time(state['lastAt'])).total_seconds() / 86400)
                retention = .9 ** min(100, elapsed / max(.4, state['stability']))
                relative = difficulty - ability if difficulty is not None and ability is not None else 0
                minutes = max(5, min(40, round(15 + relative / 40)))
                priority = (bool(current.get('openedAt')), -retention, min(3, state['lapses']), relative, problem_key)
                candidates.append({'id': current['id'], 'problemId': identity, 'due': state['due'],
                                   'openedAt': current.get('openedAt'), 'stage': state['successes'],
                                   'minutes': minutes, 'priority': priority})
        # Reuse the time the user already supplied, without adding another
        # setting or assuming that parallel goals multiply their available day.
        minutes = 90
        budgets = []
        for record in t.connection.execute('SELECT config FROM goals WHERE archived=0'):
            try:
                budgets.append(max(15, min(720, int(json.loads(record['config']).get('dailyMinutes', 90)))))
            except (TypeError, ValueError):
                pass
        if budgets:
            minutes = max(budgets)
        candidates.sort(key=lambda item: item['priority'], reverse=True)
        allocation_key = 'review-day:' + day
        allocation = preferences.get(allocation_key, {'ids': []})
        saved_ids = set(allocation.get('ids', []))
        selected = [r for r in candidates if r['id'] in saved_ids or r['openedAt']]
        # A day's budget includes completed reviews. Completing one does not
        # refill an unbounded queue on the next automatic refresh.
        spent = sum(r['minutes'] for r in candidates if r['id'] in saved_ids)
        for task_id in saved_ids:
            old = preferences.get('review-task:' + task_id, {})
            if old.get('completedAt'):
                spent += int(allocation.get('minutes', {}).get(task_id, 15))
        for candidate in candidates:
            if candidate in selected:
                continue
            allowance = minutes if len(candidates) >= 4 else max(15, round(minutes * .6))
            if len(selected) >= 8 or (spent + candidate['minutes'] > allowance and selected):
                continue
            if spent >= allowance:
                break
            selected.append(candidate)
            spent += candidate['minutes']
        planned_ids = list(dict.fromkeys(allocation.get('ids', []) + [r['id'] for r in selected]))
        costs = {**allocation.get('minutes', {}), **{r['id']: r['minutes'] for r in selected}}
        if planned_ids != allocation.get('ids', []):
            updates[allocation_key] = {'ids': planned_ids, 'minutes': costs}
        # Preserve already-started work, but defer new recommendations whenever
        # retrieval fills the day or a due backlog would otherwise keep growing.
        pause = bool((candidates and len(candidates) > len(selected)) or spent >= minutes * .65)
        result = {'date': day, 'tasks': [{k:v for k,v in r.items() if k != 'priority'} for r in selected],
                  'dueCount': len(candidates), 'deferredCount': len(candidates) - len(selected),
                  'minutes': spent, 'dailyMinutes': minutes, 'newMinutes': max(0, minutes - spent),
                  'reviewOnly': pause, 'abilityScore': ability, 'policyVersion': 1}
        if updates:
            with t._write() as db:
                for key, value in updates.items():
                    self.save(db, key, value)
        signature = (t.connection.total_changes, t.connection.execute('PRAGMA data_version').fetchone()[0], day, signature[3])
        t._review_plan_cache = (signature, result)
        return result
