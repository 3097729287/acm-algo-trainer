"""Three progressive daily lanes and three settled daily challenges."""
import datetime as dt
import hashlib
import json

from daily_rotation import CHALLENGES, EXPLORATIONS, tasks_for, adapt_challenge, task_condition
from progression import SHANGHAI, parse_time, task_progress
from training import ServiceError, iso
from usage import learning_seconds


def threshold(step):
    return (1, 2, 3, 5)[step % 4] * 10 ** (step // 4)


def time_threshold(step):
    return (5, 15, 30, 60, 90, 120)[step] if step < 6 else (step - 3) * 60


def _read(training, key, default=None):
    row = training.connection.execute('SELECT value FROM account_preferences WHERE key=?', (key,)).fetchone()
    try:
        return json.loads(row['value']) if row else default
    except (ValueError, TypeError):
        return default


def _advance_read_caches(training, day, before):
    """Task-only journal writes do not change already verified AC evidence."""
    cache = getattr(training, '_daily_evidence_cache', None)
    if cache and cache[1] == day and cache[2] is not None and cache[2][1][0] == before:
        signature = cache[2]
        signature = (signature[0], (training.connection.total_changes, *signature[1][1:]), *signature[2:])
        training._daily_evidence_cache = (cache[0], day, signature, cache[3])
    plan = getattr(training, '_review_plan_cache', None)
    if plan and plan[0][0] == before:
        training._review_plan_cache = ((training.connection.total_changes, *plan[0][1:]), plan[1])


def _completed_reviews(training, day):
    """Verify completion against the first bound official AC, never a UI flag."""
    keys = set()
    yesterday = (dt.date.fromisoformat(day) - dt.timedelta(days=1)).isoformat()
    for row in training.connection.execute("SELECT value FROM account_preferences WHERE key LIKE 'review-task:%' "
        "AND json_valid(value) AND substr(json_extract(value,'$.completedAt'),1,10) IN (?,?)", (day, yesterday)):
        try:
            task = json.loads(row['value'])
            finished = parse_time(task.get('completedAt'))
            if not finished or finished.astimezone(SHANGHAI).date().isoformat() != day or task.get('due', day) > day or not task.get('openedAt'):
                continue
        except (ValueError, TypeError, AttributeError):
            continue
        receipt = training.connection.execute("SELECT s.* FROM submissions s JOIN account_preferences p ON p.key='review-receipt:'||s.id "
            "WHERE p.value=? AND s.mode='submit' AND s.scope='official' AND s.verdict='AC' AND s.finished_at IS NOT NULL AND s.submitted_at>=? ORDER BY s.submitted_at,s.rowid LIMIT 1",
            (json.dumps(task['id']), task['openedAt'])).fetchone()
        if not receipt or parse_time(receipt['submitted_at']).astimezone(SHANGHAI).date().isoformat() != day:
            continue
        ids = training._equivalent_ids(receipt['problem_id'])
        marks = ','.join('?' for _ in ids)
        wrong = training.connection.execute(f"SELECT 1 FROM submissions WHERE problem_id IN ({marks}) AND mode='submit' AND scope='official' AND verdict='WA' AND finished_at IS NOT NULL AND submitted_at<? LIMIT 1", [*ids, task['openedAt']]).fetchone()
        if wrong:
            keys.add(task['problemKey'])
    return keys


def _review_limit(training, day, completed):
    plan = training.review_plan()
    keys = set(completed)
    for item in plan['tasks']:
        task = _read(training, 'review-task:' + item['id'], {})
        if task.get('problemKey'):
            keys.add(task['problemKey'])
    key = 'daily-review-limit:' + day
    previous = _read(training, key, [])
    excluded = set()
    if previous:
        aliases = training._identity_map()
        removed = {aliases.get(row['id'], row['id']) for row in training.connection.execute(
            'SELECT id,removed_at FROM training WHERE active=0 AND removed_at IS NOT NULL')
            if (stamp := parse_time(row['removed_at'])) and stamp.astimezone(SHANGHAI).date().isoformat() == day}
        for row in training.connection.execute("SELECT value FROM account_preferences WHERE key LIKE 'review-task:%' "
            "AND json_valid(value) AND json_extract(value,'$.completedAt') IS NULL "
            "AND json_extract(value,'$.due')<=? AND json_extract(value,'$.problemKey') IN (SELECT value FROM json_each(?)) "
            "AND (json_extract(value,'$.cancelledAt') IS NOT NULL OR json_extract(value,'$.problemId') IN (SELECT value FROM json_each(?)))",
            (day, json.dumps(previous), json.dumps(sorted(removed)))):
            task = json.loads(row['value'])
            if task.get('problemKey'):
                excluded.add(task['problemKey'])
    # Only an explicit cancellation/clear lowers the saved plan. Actual passes
    # and currently assigned work remain even if an older rewrite was cancelled.
    keys.update(set(previous) - excluded)
    if sorted(keys) != previous:
        with training._write() as db:
            db.execute('INSERT INTO account_preferences VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at',
                       (key, json.dumps(sorted(keys)), iso(training._now())))
    return len(keys)


def _definition(identity, lane, step, title, description, kind, target, xp, slot, **extra):
    return dict(id=identity, lane=lane, step=step, title=title, description=description,
                kind=kind, target=target, xp=xp, slot=slot, version=3, scope='official', minDifficulty=0, **extra)


def _next_step(records, lane):
    steps = [json.loads(row['definition']).get('step', -1) for row in records.values()
             if row['claimed_at'] and json.loads(row['definition']).get('lane') == lane]
    return max(steps, default=-1) + 1


def _evidence_key(item):
    return item.get('eventKey') if item.get('_activityEvent') else item.get('problemKey')


def progress(training, task, evidence, day, completed=None):
    if task['kind'] == 'learning':
        seconds = max(0, learning_seconds(training, day) - task.get('secondsBaseline', 0))
        amount = min(task['target'], int(seconds // 60))
        return amount, ['learning:' + day + ':' + str(int(seconds))]
    if task['kind'] == 'review':
        keys = _completed_reviews(training, day) if completed is None else completed
        return min(task['target'], len(keys)), sorted(keys)
    baseline = set(task.get('baseline', []))
    fresh = [item for item in evidence if _evidence_key(item) not in baseline]
    return task_progress(task, fresh, day)


def _random(training, day, owner, step, fixed, evidence, records, allowed=None):
    identity = 'review-random:' + str(step)
    conditions={task_condition(task) for task in fixed}
    if identity in records:
        saved=json.loads(records[identity]['definition'])
        if records[identity]['claimed_at'] or task_condition(saved) not in conditions:return saved
    excluded = {task['id'] for task in fixed}
    previous = records.get('review-random:' + str(step - 1))
    if previous:
        excluded.add(json.loads(previous['definition']).get('sourceId'))
    basis=_challenge_reference(training,day)
    pool = [task for task in [*CHALLENGES, *EXPLORATIONS]
            if task['id'] not in excluded and task['kind'] not in ('morning', 'evening')
            and (not allowed or allowed(adapt_challenge(task,basis)))
            and task_condition(adapt_challenge(task,basis)) not in conditions]
    # A short extra learning session remains possible after finite actions run
    # out. New rounds require new evidence instead of immediately reusing ACs.
    pool.append(dict(id='learning-extra', title='再学一会', description='继续学习 5 分钟', kind='learning', target=5, xp=10))
    rank = lambda item: hashlib.sha256((owner + '\0' + day + '\0review\0' + str(step) + '\0' + item['id']).encode()).digest()
    choice = adapt_challenge(min(pool, key=rank), _challenge_reference(training,day))
    task = {**choice, 'id': identity, 'sourceId': choice['id'], 'lane': 'review-random', 'step': step,
            'slot': 1, 'version': 3, 'baseline': sorted({_evidence_key(item) for item in evidence if _evidence_key(item)}),
            'secondsBaseline': learning_seconds(training, day), 'issuedAt': iso(training._now())}
    return task


def _sticker_task(task, slot, owner, day, ability=None):
    from gameplay import daily_pack_rarity
    if task.get('stickerPolicy')==3:return dict(task)
    value = task.get('stickerXp', task['xp'])
    rarity=daily_pack_rarity(owner,day,task['id'])
    base=int(ability//100)*100 if type(ability) in (int,float) and 0<ability<=4000 else 800
    count,offset={'common':(1,-100),'rare':(1,100),'epic':(2,200),'legendary':(3,300)}[rarity]
    difficulty=max(600,min(4000,base+offset))
    kind=task.get('kind','solve')
    if kind=='learning':
        count={'common':5,'rare':10,'epic':20,'legendary':40}[rarity]
        description=f'学习 {count} 分钟'
        difficulty=0
    else:
        if kind in {'topics','topic-pair','platforms'}:count=max(count,task.get('target',1))
        prefix='独立首次 AC' if kind=='independent' else '首次 AC'
        description=f'{prefix} {count} 道难度至少 {difficulty} 的新题'
        if kind=='platforms':description=f'在 {count} 个平台各首次 AC 一道难度至少 {difficulty} 的新题'
        elif kind=='topics':description=f'首次 AC 难度至少 {difficulty} 的新题，涉及至少 {count} 个不同知识点'
        elif kind=='topic-pair':description=f'首次 AC {count} 道具有同一知识点且难度至少 {difficulty} 的新题'
        elif kind in {'morning','evening'}:description=('北京时间 6–11 点' if kind=='morning' else '北京时间 18–22 点')+description
    return {**task, 'xp': 0, 'stickerXp': value, 'stickerSlot': slot, 'stickerPolicy': 3,
            'rewardSticker': {'rarity': rarity},'rewardPack':{'rarity':rarity,'quantity':{'common':3,'rare':4,'epic':5,'legendary':6}[rarity]},
            'kind':kind,'target':count,'minDifficulty':difficulty,'newOnly':True,
            'abilityReference':ability,'difficultyEvidenceRequired':kind!='learning',
            'description':description}


def _sticker_definitions(fixed, review, records, completed, owner, day, ability=None):
    saved = [json.loads(row['definition']) for row in records.values()]
    chosen = next((task['id'] for task in saved if task.get('stickerSlot') == 'fixed'), None)
    candidates = [task for task in fixed if not records.get(task['id']) or not records[task['id']]['claimed_at']]
    if chosen is None and candidates:
        chosen = min(candidates, key=lambda task: hashlib.sha256((owner+'\0'+day+'\0sticker\0'+task['id']).encode()).digest())['id']
    fixed = [_sticker_task(task, 'fixed', owner, day, ability) if task['id'] == chosen else task for task in fixed]
    if review.get('lane') == 'review-random' and completed:
        old = next((task for task in saved if task['id'] == review['id']), {})
        slots = {task.get('stickerSlot') for task in saved}
        slot = old.get('stickerSlot') or next((name for name in ('review-0', 'review-1') if name not in slots), None)
        if slot and not (records.get(review['id']) and records[review['id']]['claimed_at']):
            review = _sticker_task(review, slot, owner, day, ability)
    return fixed, review


def _challenge_reference(training, day):
    key='daily-challenge-reference:'+day
    saved=_read(training,key)
    if isinstance(saved,dict) and saved.get('version')==2:return saved.get('score')
    # Use the same failure-aware model as the displayed ability score. The
    # day's reference is frozen so a task cannot move while being attempted.
    from ability_assessment import assess, from_records
    from submission_evidence import annotate_sources
    records=[dict(row) for row in training.connection.execute("SELECT * FROM submissions WHERE mode='submit' AND finished_at IS NOT NULL")]
    model=assess(from_records(training._library(),annotate_sources(records,training.connection),training._now()),training._now())
    score=model['abilityScore'] if model['qualified'] else None
    value=json.dumps({'version':2,'score':score},ensure_ascii=False)
    with training._write() as db:
        db.execute('INSERT INTO account_preferences VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at',(key,value,iso(training._now())))
    return score


def snapshot(training, goal_tasks=None, evidence=None, *, completed=None):
    with training._library_view(), training.lock:
        day = training._now().astimezone(SHANGHAI).date().isoformat()
        owner = training._ranking_profile()['user_id']
        evidence = training._daily_evidence(day) if evidence is None else evidence
        before_changes = training.connection.total_changes
        records = {row['id']: row for row in training.connection.execute('SELECT * FROM daily_missions WHERE day=?', (day,))}
        completed = _completed_reviews(training, day) if completed is None else completed
        limit = _review_limit(training, day, completed)
        basis=_challenge_reference(training,day)
        from learning_access import challenge_filter
        allowed = challenge_filter(training)
        fixed = [{**adapt_challenge(task,basis), 'lane': 'fixed', 'slot': i + 3} for i, task in enumerate(tasks_for(day, owner, basis, allowed)[3:])]
        saved_fixed = [json.loads(row['definition']) for row in records.values() if json.loads(row['definition']).get('lane')=='fixed']
        if len(saved_fixed)==3 and all(task.get('accessPolicy')==1 for task in saved_fixed):
            fixed=sorted(saved_fixed,key=lambda task:task['slot'])
        else:
            fixed=[{**task,'accessPolicy':1} for task in fixed]
        ac_step = _next_step(records, 'ac')
        # A legacy already-claimed 1/3-AC tier is not paid a second time.
        legacy_target = max((target for key,target in [('solve-1',1),('solve-3',3)] if key in records and records[key]['claimed_at']), default=0)
        while threshold(ac_step) <= legacy_target:
            ac_step += 1
        ac_target = threshold(ac_step)
        ac = _definition('ac-chain:' + str(ac_step), 'ac', ac_step, 'AC', f'AC {ac_target} 道不同题目', 'solve', ac_target, min(200, 25 + 5 * ac_step), 0)
        study_step = _next_step(records, 'learning')
        study_target = time_threshold(study_step)
        study = _definition('learning-chain:' + str(study_step), 'learning', study_step, '使用时长', f'学习 {study_target} 分钟', 'learning', study_target, min(100, 10 * (study_step + 1)), 2, unit='分钟')
        review_step = _next_step(records, 'review')
        last_review = max((json.loads(row['definition'])['target'] for row in records.values()
                           if row['claimed_at'] and json.loads(row['definition']).get('lane') == 'review'), default=0)
        if limit > last_review:
            target = min(limit, threshold(review_step))
            # If late-arriving official history expands today's review plan,
            # skip thresholds already paid rather than regranting an old tier.
            while target <= last_review:
                review_step += 1
                target = min(limit, threshold(review_step))
            review = _definition('review-chain:' + str(review_step), 'review', review_step, '复习', f'复习 {target} 道题目', 'review', target, min(100, 10 + 5 * review_step), 1)
        else:
            review = _random(training, day, owner, _next_step(records, 'review-random'), fixed, evidence, records, allowed)
        fixed, review = _sticker_definitions(fixed, review, records, completed, owner, day, basis)
        definitions = [ac, review, study, *fixed]
        changes = [task for task in definitions if task['id'] not in records or not records[task['id']]['claimed_at']
                   and records[task['id']]['definition'] != json.dumps(task, ensure_ascii=False)]
        if changes:
            with training._write() as db:
                for task in changes:
                    db.execute('INSERT INTO daily_missions(day,id,definition) VALUES(?,?,?) ON CONFLICT(day,id) DO UPDATE SET definition=excluded.definition WHERE claimed_at IS NULL',
                               (day, task['id'], json.dumps(task, ensure_ascii=False)))
        current = {row['id']: row for row in training.connection.execute('SELECT * FROM daily_missions WHERE day=?', (day,))}
        tasks = []
        for definition in definitions:
            row = current[definition['id']]
            task = {**json.loads(row['definition']), 'lane': definition['lane'], 'slot': definition['slot']}
            amount, _ = progress(training, task, evidence, day, completed)
            task['stickerRarity']=task.get('rewardSticker',{}).get('rarity') or __import__('gameplay').rarity(task)
            task.update(progress=amount, completed=amount >= task['target'], claimed=bool(row['claimed_at']), claimedAt=row['claimed_at'])
            tasks.append(task)
        if goal_tasks is None:
            from goals import Goals
            goal_tasks = Goals(training).list(assign=True).get('goalTasks', [])
        else:
            _advance_read_caches(training, day, before_changes)
        claimed = [row for row in current.values() if row['claimed_at']]
        visible_completed=sum(json.loads(row['definition']).get('lane') in ('fixed','review-random') for row in claimed)
        visible_completed+=sum(task['lane'] in ('fixed','review-random') and task['completed'] and not task['claimed'] for task in tasks)
        # Count only issued challenges. The review lane does not add a random
        # challenge until its actual review requirements have been settled.
        random_ids = {row['id'] for row in claimed if json.loads(row['definition']).get('lane') == 'review-random'}
        random_ids.update(task['id'] for task in tasks if task['lane'] == 'review-random')
        visible_target = min(10, 3 + len(random_ids))
        return {'date': day, 'timezone': 'Asia/Shanghai', 'policyVersion': 3, 'tasks': tasks, 'goalTasks': goal_tasks,
                'goalPending': sum(not task['accepted'] for task in goal_tasks), 'claimable': sum(task['completed'] and not task['claimed'] for task in tasks),
                'completedCount': len(claimed), 'reviewLimit': limit, 'reviewCompleted': len(completed),
                'displayCompletedCount':visible_completed,'displayTarget':visible_target,
                'displayComplete':visible_completed>=10,
                'totalClaimedXp': sum(row['awarded_xp'] for row in claimed)}


def claim(training, identity, date=None):
    if not isinstance(identity, str) or not identity or len(identity) > 64:
        raise ServiceError(400, '每日任务编号无效')
    with training._library_view(), training.lock:
        day = training._now().astimezone(SHANGHAI).date().isoformat()
        if date is not None and date != day:
            raise ServiceError(409, '每日任务已刷新，请重新打开任务列表')
        evidence = training._daily_evidence(day)
        completed = _completed_reviews(training, day)
        current = snapshot(training, goal_tasks=[], evidence=evidence, completed=completed)
        row = training.connection.execute('SELECT * FROM daily_missions WHERE day=? AND id=?', (day, identity)).fetchone()
        if row is None or not row['claimed_at'] and identity not in {task['id'] for task in current['tasks']}:
            raise ServiceError(404, '没有找到这项每日任务')
        already = bool(row['claimed_at'])
        task = json.loads(row['definition'])
        if not already:
            amount, proof = progress(training, task, evidence, day, completed)
            if amount < task['target']:
                raise ServiceError(409, '这项任务尚未完成')
            before_changes = training.connection.total_changes
            with training._write() as db:
                db.execute('UPDATE daily_missions SET claimed_at=?,awarded_xp=?,evidence=? WHERE day=? AND id=? AND claimed_at IS NULL',
                           (iso(training._now()), task['xp'], json.dumps(proof), day, identity))
                if task.get('rewardSticker') and task.get('stickerSlot'):
                    db.execute('INSERT INTO account_preferences VALUES(?,?,?) ON CONFLICT(key) DO NOTHING',('sticker-eligible:'+day+':'+identity,json.dumps(task,ensure_ascii=False),iso(training._now())))
            _advance_read_caches(training, day, before_changes)
        # Compute the next tier only after the claim is durably committed.
        return {'dailyTasks': snapshot(training, goal_tasks=[], evidence=evidence, completed=completed),
                'awardedXp': 0 if already else task['xp'], 'alreadyClaimed': already,
                **({'rewardPack':task['rewardPack']} if task.get('rewardPack') else {})}
