"""Account-owned learning facts, proposals, accepted weekly plans and articles.

The ability model remains authoritative. A reading mark is exposure; explicit
adoption controls direction, while new receipts only update facts. Everything
uses the existing private SQLite journal and account snapshot protocol.
"""
from copy import deepcopy
from functools import lru_cache
import datetime as dt
import hashlib
import json
import math
import uuid

from paths import resource
from progression import SHANGHAI, parse_time
from training import ServiceError, iso
from insights import canonical_url

KEY = 'learning-summary-v1'
HISTORY = 'learning-summary-history:'
STAGES = ['基础编码', '常用算法与实现', '专题应用', '混合限时运用', '区域赛模拟与查缺']
LEVELS = ['尚未验证', '接触过', '理解原理', '能跟着实现', '能独立实现', '能独立用来解题', '隔一段时间仍能完成']
REASONS = {'meaning': '题意没理解', 'idea': '没有思路', 'implementation': '知道方法但写不出',
           'bug': '代码出错', 'forgot': '旧知识忘了', 'schedule': '任务安排不合适',
           'easy': '任务太简单', 'hard': '任务太难', 'verify': '不知道怎样检验', 'transfer': '学习后仍不会做题'}


@lru_cache(maxsize=1)
def curriculum():
    return json.loads(resource('learning-curriculum.json').read_text('utf8'))


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def read(training, key=KEY, default=None):
    row = training.connection.execute('SELECT value FROM account_preferences WHERE key=?', (key,)).fetchone()
    return json.loads(row[0]) if row else deepcopy(default)


def write(training, key, value):
    with training._write() as db:
        db.execute('INSERT INTO account_preferences VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at',
                   (key, json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False), iso(training._now())))


def empty():
    return {'version': 1, 'revision': '', 'config': {'goal': {'kind': 'xcpc', 'title': '区域赛铜牌', 'deadline': ''},
            'weekdayMinutes': None, 'weekendMinutes': None, 'restDays': [], 'team': False, 'role': ''},
            'plan': None, 'proposal': None, 'article': [], 'topics': [], 'seen': {}, 'view': {}, 'checks': {}, 'diagnoses': []}


def week(now):
    day = now.astimezone(SHANGHAI).date()
    return day - dt.timedelta(days=day.weekday())


def task_identity(kind, identity):
    return kind + ':' + str(identity)


class LearningSummary:
    def __init__(self, training):
        self.t = training

    def snapshot(self):
        with self.t.lock:
            state = read(self.t, default=empty())
            state['history'] = [value for row in self.t.connection.execute('SELECT value FROM account_preferences WHERE key LIKE ? ORDER BY updated_at DESC', (HISTORY + '%',))
                                if not (value := json.loads(row[0])).get('deleted')]
            state['history'] = [{'id': item['id'], 'at': item['at'], 'reason': item['reason'], 'week': item.get('plan', {}).get('week')} for item in state['history']]
            state['availableTopics'] = [{k: v for k, v in topic.items() if k in ('id', 'title', 'level', 'prerequisites', 'tags', 'course', 'template', 'lectures')} for topic in curriculum()['topics']]
            state['now'] = iso(self.t._now())
            state['activeContest'] = self.t.active_contest()
            return state

    def history(self, identity):
        with self.t.lock:
            value = read(self.t, HISTORY + str(identity))
            if not value or value.get('deleted'): raise ServiceError(404, '这份历史已删除或不存在')
            return value

    def _archive(self, state, reason):
        if not state.get('article'): return
        identity = uuid.uuid4().hex
        write(self.t, HISTORY + identity, {'id': identity, 'at': iso(self.t._now()), 'reason': reason,
              'article': state['article'], 'topics': state.get('topics', []), 'plan': state.get('plan') or {}})

    def _save(self, state):
        state['revision'] = uuid.uuid4().hex
        write(self.t, KEY, state)

    def _facts(self, state):
        from ability_assessment import from_records, assess
        from submission_evidence import annotate_sources
        t = self.t
        rows = t._library()
        records = annotate_sources([dict(r) for r in t.connection.execute("SELECT * FROM submissions WHERE mode='submit' ORDER BY submitted_at,rowid")], t.connection)
        now = t._now()
        events = from_records(rows, records, now)
        by_id = {r['id']: r for r in rows}
        alias = t._identity_map(rows)
        # Match exact reviewed originals or concrete knowledge tags. No title inference.
        def matches(row, topic):
            return (canonical_url(row.get('url')) in topic.get('practiceOriginals', [])
                    or not row.get('knowledgeReviewRequired') and bool(set(topic['tags']) & set(row.get('tags', []))))
        ui = read(t, 'ui', {})
        learned = set(ui.get('learnedLectures', []))
        topics = []
        from code_templates import builtins
        templates = {item['id']: item for item in builtins()}
        for topic in curriculum()['topics']:
            guided_keys = {canonical_url(p.get('url')) for p in curriculum()['courses'].get(topic.get('course'), {}).get('problems', [])}
            solved = [e for e in events if e['solved'] and e['id'] not in guided_keys and matches(by_id.get(e['problemId'], {}), topic)]
            public = [r for r in records if r.get('scope') == 'official' and r.get('verdict') == 'AC' and r.get('finished_at') and matches(by_id.get(alias.get(r['problem_id'], r['problem_id']), {}), topic)]
            delayed = []
            for event in solved:
                for r in public:
                    source = by_id.get(alias.get(r['problem_id'], r['problem_id']), {})
                    if canonical_url(source.get('url')) != event['id'] or r.get('solution_seen') != 0: continue
                    stamp = parse_time(r.get('submitted_at'))
                    if stamp and 86400 <= (stamp - parse_time(event['date'])).total_seconds() and stamp <= now:
                        from submission_evidence import source_present
                        if source_present(r) or r.get('timedReceipt'): delayed.append(event['problemId'])
            drills = templates.get(topic.get('template'), {}).get('practiceIds', [])
            practice = [r for r in records if r['problem_id'] in drills and r.get('scope') == 'template' and r.get('verdict') == 'AC' and r.get('finished_at')]
            checked = state.get('checks', {}).get(topic['id'], {})
            guided_passed = any(canonical_url(by_id.get(alias.get(r['problem_id'], r['problem_id']), {}).get('url')) in guided_keys for r in public)
            level = 6 if delayed else 5 if solved else 4 if any(r.get('solution_seen') == 0 for r in practice) else 3 if practice or guided_passed else 2 if checked.get('concept') else 1 if public or learned.intersection(topic['lectures']) or checked.get('read') else 0
            topics.append({'id': topic['id'], 'title': topic['title'], 'level': level, 'label': LEVELS[level],
                           'independent': len(solved), 'publicAccepted': len({canonical_url(by_id.get(alias.get(r['problem_id'], r['problem_id']), {}).get('url')) or r['problem_id'] for r in public}),
                           'retained': len(set(delayed)), 'evidence': [{k: e[k] for k in ('problemId', 'date', 'failures', 'firstPass')} for e in solved[-12:]],
                           'mixed': False, 'lastAt': max((e['date'] for e in solved), default=None)})
        completed_checks = []
        for task in (state.get('plan') or {}).get('tasks', []):
            if task['kind'] == 'mixed' and task.get('contestId'): completed_checks.append(task)
        for history in t.connection.execute('SELECT value FROM account_preferences WHERE key LIKE ?', (HISTORY + '%',)):
            value = json.loads(history[0])
            if not value.get('deleted'):
                completed_checks.extend(task for task in value.get('plan', {}).get('tasks', []) if task['kind'] == 'mixed' and task.get('contestId'))
        for task in completed_checks:
            contest = t.connection.execute('SELECT status FROM contests WHERE id=?', (task['contestId'],)).fetchone()
            if not contest or contest[0] != 'finished': continue
            for topic in topics:
                definition = next(item for item in curriculum()['topics'] if item['id'] == topic['id'])
                topic['mixed'] = topic['mixed'] or any(e['solved'] and e.get('timed') and self._matches(by_id.get(e['problemId'], {}), definition)
                    and any(r.get('contest_id') == task['contestId'] and r['problem_id'] in t._equivalent_ids(e['problemId']) and r.get('verdict') == 'AC' and r.get('solution_seen') == 0 for r in records) for e in events)
        return rows, records, events, topics, assess(events, now)

    def _config(self, value, previous):
        if not isinstance(value, dict) or set(value) - {'goal', 'weekdayMinutes', 'weekendMinutes', 'restDays', 'team', 'role'}:
            raise ServiceError(400, '时间或目标设置无效')
        result = {**previous, **value}
        for field in ('weekdayMinutes', 'weekendMinutes'):
            if type(result.get(field)) is not int or not 0 <= result[field] <= 720:
                raise ServiceError(422, '请填写工作日和周末可用分钟数（0–720）')
        rests = result.get('restDays', [])
        if not isinstance(rests, list) or len(rests) > 7 or any(type(d) is not int or not 0 <= d <= 6 for d in rests):
            raise ServiceError(400, '休息日设置无效')
        if type(result.get('team')) is not bool or not isinstance(result.get('role'), str) or len(result['role']) > 80:
            raise ServiceError(400, '队伍设置无效')
        goal = result.get('goal')
        if not isinstance(goal, dict) or set(goal) - {'kind', 'title', 'deadline'} or goal.get('kind') not in ('xcpc', 'cf', 'lanqiao', 'topic') or not isinstance(goal.get('title'), str) or not 1 <= len(goal['title'].strip()) <= 160:
            raise ServiceError(400, '请填写一个具体总目标')
        if goal.get('deadline'):
            try: deadline = dt.date.fromisoformat(goal['deadline'])
            except (TypeError, ValueError): raise ServiceError(400, '截止日期无效')
            if deadline < self.t._now().astimezone(SHANGHAI).date(): raise ServiceError(422, '截止日期已过，请调整目标日期')
        return result

    def _default_tracks(self, topics):
        supported = {item['id'] for item in topics if item['level'] >= 5}
        if not supported:
            old = max(topics, key=lambda item: item['publicAccepted'], default=None)
            if old and old['publicAccepted']:
                return [old['id']]
        # Retain learned facts from the whole history, independent of the rating window.
        for topic in curriculum()['topics']:
            if topic['id'] not in supported and set(topic['prerequisites']) <= supported:
                return [topic['id']]
        return [min(topics, key=lambda item: (item['level'], item['id']))['id']]

    def _complete(self, task, records, state):
        if task.get('status') == 'done': return True
        kind = task['kind']
        if kind in ('lecture', 'quiz', 'reflection'):
            return bool(state.get('completed', {}).get(task['key']))
        if kind == 'mixed':
            contest = self.t.connection.execute('SELECT status FROM contests WHERE id=?', (task.get('contestId'),)).fetchone()
            return bool(contest and contest[0] == 'finished' and state.get('completed', {}).get(task['key'] + ':reflection'))
        threshold = parse_time(task.get('createdAt'))
        if kind == 'course':
            originals = {canonical_url(p.get('url')) for p in curriculum()['courses'].get(task['id'], {}).get('problems', [])}
            rows = {r['id']: r for r in self.t._library()}
            return any(r.get('scope') == 'official' and r.get('verdict') == 'AC' and r.get('finished_at') and parse_time(r['submitted_at']) >= threshold and canonical_url(rows.get(r['problem_id'], {}).get('url')) in originals for r in records)
        for r in records:
            if r['problem_id'] not in self.t._equivalent_ids(task['id']) or r.get('verdict') != 'AC' or not r.get('finished_at'): continue
            stamp = parse_time(r['submitted_at'])
            if threshold and stamp < threshold: continue
            if task.get('minimumAt') and stamp < parse_time(task['minimumAt']): continue
            if task.get('notBefore') and stamp.astimezone(SHANGHAI).date().isoformat() < task['notBefore']: continue
            if kind in ('problem', 'review') and r.get('scope') != 'official': continue
            if kind == 'template-problem' and r.get('scope') != 'template': continue
            if kind == 'review' and r.get('solution_seen') != 0: continue
            return True
        return False

    def _plan(self, state, tracks, rows, records, events, topics, previous=None):
        now = self.t._now()
        monday = week(now)
        today = now.astimezone(SHANGHAI).date()
        config = state['config']
        topic_by_id = {topic['id']: topic for topic in curriculum()['topics']}
        proof = {topic['id']: topic for topic in topics}
        budgets = [{'date': (monday + dt.timedelta(days=d)).isoformat(), 'minutes': 0 if d in config['restDays'] else config['weekdayMinutes' if d < 5 else 'weekendMinutes'], 'used': 0} for d in range(7)]
        remaining = [day for day in budgets if day['date'] >= today.isoformat()]
        tasks, waiting, gaps = [], [], []
        used = set()
        if previous and previous.get('week') == monday.isoformat():
            for done in previous.get('tasks', []):
                if done.get('status') != 'done': continue
                tasks.append(deepcopy(done)); used.add(done['key'])
                day = next((d for d in budgets if d['date'] == done['date']), None)
                if day: day['used'] += done['minutes']
        def add(task):
            key = task['key']
            original = task.get('original')
            existing = next((t for t in tasks if original and t.get('original') == original), None)
            if existing:
                existing['purposes'] = sorted(set(existing.get('purposes', [existing.get('topicId')])) | {task.get('topicId')}, key=lambda x: str(x))
                return
            if key in used: return
            used.add(key)
            task = {**task, 'status': 'pending', 'createdAt': task.get('createdAt') or iso(now)}
            size = task['minutes']
            day = next((d for d in remaining if d['minutes'] - d['used'] >= size and d['date'] >= task.get('notBefore', today.isoformat())), None)
            if day:
                day['used'] += size
                tasks.append({**task, 'date': day['date'], 'order': len(tasks) + 1})
            else: waiting.append(task)
        def task(kind, identity, title, minutes, topic=None, condition='', **extra):
            return {'key': task_identity(kind, identity), 'kind': kind, 'id': identity, 'title': title,
                    'minutes': minutes, 'topicId': topic, 'condition': condition, **extra}
        # Existing commitments keep their identities and order; new work fits the remainder.
        prior = [t for t in (previous or {}).get('tasks', []) + (previous or {}).get('waiting', []) if t.get('status') != 'done' and (t.get('topicId') in tracks or t['kind'] == 'review') and t['kind'] != 'mixed']
        review = self.t.review_plan()
        for item in review.get('tasks', []):
            identity = item['problemId']
            row = next((r for r in rows if r['id'] == identity), None)
            if row: add(task('review', identity, row['title'], min(25, max(5, item.get('minutes', 20))), condition='本轮空白重写后原站独立 AC', reviewId=item['id'], original=canonical_url(row.get('url')) or identity))
        for item in prior: add(item)
        if config.get('team'):
            add(task('reflection', 'team-' + monday.isoformat(), '按本人职责整理团队备赛复盘', 15, condition='记录本人职责内的训练结果与下一次队内配合安排'))
        aliases = self.t._identity_map(rows)
        by_id = {r['id']: r for r in rows}
        solved = {e['id'] for e in events if e['solved']}
        solved.update(canonical_url(by_id.get(aliases.get(r['problem_id'], r['problem_id']), {}).get('url')) for r in records if r.get('scope') == 'official' and r.get('verdict') == 'AC')
        # Reserve a real, unlabelled mixed check and its review before filling new learning.
        mix_minutes = min(45, max((d['minutes'] - d['used'] for d in remaining), default=0))
        mix_minutes = max(5, mix_minutes - 10) if mix_minutes >= 10 else mix_minutes
        pool = []
        for row in rows:
            key = canonical_url(row.get('url')) or row['id']
            if key in solved or row.get('catalogHidden') or row.get('locked') or not row.get('catalogStatementReady') or not row.get('url'): continue
            if any(self._matches(row, topic_by_id[tid]) for tid in tracks): pool.append(row)
        goal_kind = config['goal']['kind']
        def goal_rank(row):
            name = ' '.join(str(row.get(k) or '') for k in ('contest', 'contestFullName', 'source'))
            return 0 if goal_kind == 'cf' and row.get('platform') == 'Codeforces' or goal_kind == 'lanqiao' and ('蓝桥' in name or 'lanqiao' in name) or goal_kind == 'xcpc' and ('ICPC' in name or 'CCPC' in name) else 1
        pool.sort(key=lambda r: (goal_rank(r), r.get('difficulty') if type(r.get('difficulty')) in (int, float) else 10000, r['id']))
        from rating_evidence import evidence as rating_evidence
        mixed_pool = [r for r in pool if rating_evidence(r)['known']]
        if mixed_pool and mix_minutes:
            chosen = []
            seen_originals = set()
            for tid in tracks:
                row = next((r for r in mixed_pool if self._matches(r, topic_by_id[tid]) and canonical_url(r.get('url')) not in seen_originals), None)
                if row:
                    seen_originals.add(canonical_url(row.get('url'))); chosen.append(row['id'])
            for row in mixed_pool:
                if len(chosen) >= max(len(tracks), min(3, max(1, mix_minutes // 15))): break
                key = canonical_url(row.get('url')) or row['id']
                if key in seen_originals: continue
                seen_originals.add(key); chosen.append(row['id'])
                if len(chosen) >= max(len(tracks), min(3, max(1, mix_minutes // 15))): break
            mixed = task('mixed', monday.isoformat(), '本周无算法提示综合检验与复盘', mix_minutes, condition='独立计时交卷，并完成复盘；样例通过不等于正式 AC', ids=chosen, reflectionMinutes=min(10, mix_minutes // 3))
            # Prefer the final available study day, including a late-week first visit.
            for day in reversed(remaining):
                if day['minutes'] - day['used'] >= mixed['minutes']:
                    mixed['notBefore'] = day['date']; break
            add(mixed)
        elif mix_minutes: gaps.append('综合检验题面正在准备；已有课程与复习仍可继续')
        from code_templates import builtins
        templates = {item['id']: item for item in builtins()}
        for tid in tracks:
            topic, evidence = topic_by_id[tid], proof[tid]
            if evidence['level'] < 2:
                for identity in ([] if state.get('checks', {}).get(tid, {}).get('read') else topic['lectures'][:1]):
                    add(task('lecture', identity, '阅读：' + topic['title'], 15, tid, '阅读正文并确认已读；理解另行检验'))
                if tid in QUIZZES: add(task('quiz', tid, '原理检查：' + topic['title'], 5, tid, '回答适用条件或边界问题'))
            template = templates.get(topic.get('template'), {})
            if evidence['level'] < 5:
                if topic.get('course'): add(task('course', topic['course'], '实验与跟做：' + topic['title'], 20, tid, '在课程内完成对应操作，再用脱离示例的实现验证'))
                for identity in template.get('practiceIds', [])[:1]: add(task('template-problem', identity, '实现检查：' + topic['title'], 25, tid, '本操作练习全部案例通过'))
            candidates = [r for r in pool if self._matches(r, topic) and (canonical_url(r.get('url')) or r['id']) not in {canonical_url(next((x for x in rows if x['id'] == pid), {}).get('url')) for t in tasks if t['kind'] == 'mixed' for pid in t.get('ids', [])}]
            for row in candidates[:2]:
                add(task('problem', row['id'], row['title'], 30, tid, '原站正式 AC；本轮使用提示时另记辅助完成', original=canonical_url(row.get('url')) or row['id']))
            if not candidates: gaps.append(topic['title'] + '：需要补充完整、未做过的原题')
            if evidence['level'] >= 5 and evidence['level'] < 6 and evidence['evidence']:
                item = evidence['evidence'][-1]
                row = next((r for r in rows if r['id'] == item['problemId']), None)
                if row:
                    after = (parse_time(item['date']).astimezone(SHANGHAI) + dt.timedelta(days=1)).date().isoformat()
                    add(task('review', row['id'], '隔日重写：' + row['title'], 25, tid, '间隔至少 24 小时，脱离旧代码后原站独立 AC', notBefore=after, minimumAt=iso(parse_time(item['date']) + dt.timedelta(days=1)), original=canonical_url(row.get('url')) or row['id']))
        tasks.sort(key=lambda item: (item['date'], item['order']))
        for index, item in enumerate(tasks): item['order'] = index + 1
        allocations = [{'id': tid, 'title': topic_by_id[tid]['title'], 'minutes': sum(t['minutes'] for t in tasks if t.get('topicId') == tid)} for tid in tracks]
        return {'id': uuid.uuid4().hex, 'week': monday.isoformat(), 'stage': (previous or {}).get('stage', self._stage(topics)),
                'tracks': tracks, 'tasks': tasks, 'waiting': waiting, 'days': budgets, 'allocations': allocations,
                'gaps': gaps, 'createdAt': iso(now), 'configHash': digest(config)}

    @staticmethod
    def _matches(row, topic):
        return canonical_url(row.get('url')) in topic.get('practiceOriginals', []) or not row.get('knowledgeReviewRequired') and bool(set(topic['tags']) & set(row.get('tags', [])))

    @staticmethod
    def _stage(topics):
        basic = topics[:7]
        if sum(topic['level'] >= 5 for topic in basic) < 3: return 0
        if sum(topic['level'] >= 5 for topic in topics[7:]) < 3: return 1
        if sum(topic['level'] >= 6 for topic in topics[7:]) < 3: return 2
        return 3

    def _article(self, state, records, events, assessment):
        topics = state['topics']; plan = state.get('plan'); config = state['config']; now = self.t._now()
        stage = (plan or {}).get('stage', self._stage(topics))
        active = {t['id']: t for t in topics if t['id'] in (plan or {}).get('tracks', [])}
        goal = config['goal']
        week_start = week(now)
        recent = [e for e in events if e['solved'] and parse_time(e['date']).astimezone(SHANGHAI).date() >= week_start]
        changes = '；'.join(t['title'] + '已' + t['label'] for t in active.values()) or '尚未选择执行主线'
        paragraph = [
            {'id': 'stage', 'title': '当前阶段', 'text': f'你的总目标是{goal["title"]}，目前按{STAGES[stage]}阶段接续。{changes}。已学历史继续保留，缺少近期检验的部分会单列待验证。'},
            {'id': 'progress', 'title': '最近进步', 'text': f'本周有{len(recent)}道不同原题留下新的独立通过证据。' + ('当前的具体依据可在下方专题记录中打开；一次通过与修改后通过沿用现有稳定性判断。' if recent else '这不表示此前没有学过；公开 AC、已读和跟做分别记录，暂不足以确认的能力继续等待检验。')},
            {'id': 'gaps', 'title': '主要缺口', 'text': '；'.join(t['title'] + '：' + ('隔日保持已有证据，未提示算法的综合迁移仍需检验' if t['level'] >= 6 else '下一步核实' + LEVELS[min(6, t['level'] + 1)]) for t in active.values()) or '先确定时间预算，再从已有记录支持的位置做少量验证，不以等级、阅读时长或翻页代替掌握。'}]
        if plan:
            total = sum(d['minutes'] for d in plan['days'])
            allocation = '、'.join(a['title'] + str(a['minutes']) + '分钟' for a in plan['allocations'])
            paragraph.append({'id': 'week', 'title': '本周安排', 'text': f'本周总预算{total}分钟，{allocation}，其余用于到期复习、无算法提示综合检验与复盘。按日期和顺序执行，下表列出真实入口与各自完成条件。未完成内容在后续预算内顺延，新内容相应后移。'})
            pending = [t for t in plan['tasks'] if t['status'] != 'done']
            next_task = pending[0] if pending else None
            next_text = '本周已安排任务已完成，可以复习或自行选题；下一阶段方案需采纳后启动。'
            if next_task:
                next_text = ('先完成“' + next_task['title'] + '”，' + next_task['condition'] + '。') if next_task['date'] <= now.astimezone(SHANGHAI).date().isoformat() else '下一项安排在' + next_task['date'] + '：“' + next_task['title'] + '”。今天可以休息或自行选择额外学习。'
            paragraph.append({'id': 'next', 'title': '现在最该做的一件事', 'text': next_text})
        else:
            paragraph.extend([{'id': 'week', 'title': '本周安排', 'text': '请先填写工作日、周末可用时间和休息日。系统不会猜测你的日程；计划方案确认后，整周任务统一进入“我的训练”。'},
                              {'id': 'next', 'title': '现在最该做的一件事', 'text': '填写可用时间，查看系统建议的起点并采纳；你也可以选择专题或提出已经掌握的内容，先做短验证。'}])
        goal_detail = '截止日期为' + goal['deadline'] + '，日程会按剩余时间调整；' if goal.get('deadline') else '目标无截止日期，按可用时间持续推进；'
        paragraph.append({'id': 'route', 'title': '下一阶段与检验', 'text': goal_detail + '当前阶段之后按“' + STAGES[min(stage + 1, len(STAGES) - 1)] + '”接续。先用复习保留旧知识，再补当前主线缺口，依次核对独立实现、未做过的原题、隔日保持和无算法提示综合任务。通过当前技能阶段不等于完成最终目标，区域赛奖牌以真实比赛结果确认。' + ('你选择了团队备赛，训练安排结合“' + (config['role'] or '职责待填写') + '”职责；这里仅记录你本人的表现。' if config.get('team') else '')})
        pending_minutes = sum(t['minutes'] for t in (plan or {}).get('tasks', []) if t['status'] != 'done')
        estimate = (f'按任务预算，本轮已安排的剩余内容约{pending_minutes / 60:.1f}–{pending_minutes * 1.5 / 60:.1f}小时，包含复习、综合检验与复盘；这是排程估计，会结合实际投入与完成情况修正。' if pending_minutes else '本周各项用时是可调整的训练估计。')
        paragraph.append({'id': 'estimate', 'title': '预计时间', 'text': estimate + '阶段周期还需实际检验结果；证据不足时先诊断，不把题量、能力分换算成获奖日期。'})
        today = now.astimezone(SHANGHAI).date().isoformat()
        today_records = [r for r in records if r.get('finished_at') and parse_time(r['submitted_at']).astimezone(SHANGHAI).date().isoformat() == today]
        aliases = self.t._identity_map()
        accepted = {aliases.get(r['problem_id'], r['problem_id']) for r in today_records if r.get('scope') == 'official' and r.get('verdict') == 'AC'}
        assisted = {aliases.get(r['problem_id'], r['problem_id']) for r in today_records if r.get('scope') == 'official' and r.get('verdict') == 'AC' and r.get('solution_seen')}
        from submission_evidence import source_present
        independent = {aliases.get(r['problem_id'], r['problem_id']) for r in today_records if r.get('scope') == 'official' and r.get('verdict') == 'AC' and r.get('solution_seen') == 0 and (source_present(r) or r.get('timedReceipt'))} - assisted
        unknown = accepted - assisted - independent
        reviews = sum(t['kind'] == 'review' and str(t.get('completedAt', '')).startswith(today) for t in (plan or {}).get('tasks', []))
        paragraph.append({'id': 'daily', 'title': '今日反馈', 'text': f'今天正式通过{len(accepted)}道不同原题：独立证据{len(independent)}道，辅助完成{len(assisted)}道，独立性尚未确认{len(unknown)}道；完成计划复习{reviews}项。尚未确认的原站回执不计完成。进步和主要问题见上文，下次打开继续同一份已采纳计划。'})
        if state.get('diagnoses'):
            d = state['diagnoses'][-1]
            paragraph.append({'id': 'diagnosis', 'title': '遇到困难', 'text': '你反馈“' + REASONS[d['reason']] + '”。' + d['advice'] + '涉及方向或任务替换的方案只在采纳后应用。'})
        return [{**p, 'hash': digest(p)} for p in paragraph]

    def refresh(self):
        with self.t.lock, self.t._library_view():
            state = read(self.t, default=empty())
            previous_state = digest(state)
            if self.t.active_contest(): return self.snapshot()
            rows, records, events, topics, assessment = self._facts(state)
            state['topics'] = topics
            plan = state.get('plan')
            if plan:
                before = deepcopy(plan)
                for task in plan['tasks'] + plan.get('waiting', []):
                    if task['status'] != 'done' and self._complete(task, records, state):
                        task['status'] = 'done'; task['completedAt'] = iso(self.t._now())
                if plan['week'] != week(self.t._now()).isoformat():
                    self._archive({**state, 'plan': before}, '周结束')
                    state['plan'] = plan = self._plan(state, plan['tracks'], rows, records, events, topics, plan)
                    self._prepare_reviews(plan)
                # Attainment creates a proposal, never silently changes direction.
                if all(next(t for t in topics if t['id'] == tid)['level'] >= 6 and next(t for t in topics if t['id'] == tid)['mixed'] for tid in plan['tracks']) and not state.get('proposal'):
                    if state.get('attainedPlanId') != plan['id']:
                        self._archive(state, '当前阶段检验完成')
                        state['attainedPlanId'] = plan['id']
                    following = self._default_tracks(topics)
                    if following != plan['tracks'] or plan['stage'] < len(STAGES) - 1:
                        state['proposal'] = self._plan(state, following, rows, records, events, topics)
                        state['proposal']['stage'] = min(len(STAGES) - 1, plan['stage'] + 1)
                        state['proposal']['reason'] = '当前主线已有独立应用与延迟检验证据，建议查看下一阶段方案'
                if not state.get('proposal') and len(plan['tracks']) == 1 and state.get('offeredParallelPlanId') != plan['id'] and sum(d['minutes'] for d in plan['days']) >= 240:
                    current_topic = next(t for t in topics if t['id'] == plan['tracks'][0])
                    following = self._default_tracks(topics)
                    if current_topic['level'] >= 5 and following[0] not in plan['tracks']:
                        state['proposal'] = self._plan(state, plan['tracks'] + following, rows, records, events, topics, plan)
                        state['proposal']['reason'] = '当前主线进入隔日保持检验，可在间隔期间并行学习另一项；采纳前请核对时间重新分配'
                        state['offeredParallelPlanId'] = plan['id']
            initial_article = not state.get('article')
            state['article'] = self._article(state, records, events, assessment)
            if initial_article: state['seen'] = {p['id']: p['hash'] for p in state['article']}
            state['effectiveSeconds'] = effective_seconds(self.t)
            facts_at = [parse_time(t['lastAt']) for t in topics if t.get('lastAt')]
            began = parse_time((plan or {}).get('acceptedAt') or (plan or {}).get('createdAt'))
            latest = max([d for d in facts_at + [began] if d], default=self.t._now())
            state['stalled'] = bool(plan and any(t['status'] != 'done' for t in plan['tasks']) and (self.t._now() - latest).total_seconds() >= 3 * 86400)
            if digest(state) != previous_state:
                state['updatedAt'] = iso(self.t._now())
                self._save(state)
            return self.snapshot()

    def update(self, body):
        if not isinstance(body, dict): raise ServiceError(400, '操作格式无效')
        action = body.get('action')
        with self.t.lock, self.t._library_view():
            state = read(self.t, default=empty())
            if body.get('revision') != state['revision']: raise ServiceError(409, '规划已更新，请读取后重试')
            if self.t.active_contest() and action not in ('seen', 'view', 'delete-history'):
                raise ServiceError(409, '请先完成当前限时训练，交卷后再调整规划')
            if action == 'configure':
                state['config'] = self._config(body.get('config'), state['config'])
                rows, records, events, topics, _ = self._facts(state)
                state['topics'] = topics
                tracks = body.get('tracks') or (state.get('plan') or {}).get('tracks') or self._default_tracks(topics)
                self._validate_tracks(tracks)
                if state.get('plan') and tracks == state['plan']['tracks']:
                    self._archive(state, '调整时间安排')
                    state['plan'] = self._plan(state, tracks, rows, records, events, topics, state['plan'])
                    self._prepare_reviews(state['plan'])
                else:
                    state['proposal'] = self._plan(state, tracks, rows, records, events, topics)
                    state['proposal']['reason'] = '按照目标、学习证据与共享时间预算制定；采纳后执行'
            elif action == 'propose':
                tracks = body.get('tracks'); self._validate_tracks(tracks)
                if state['config']['weekdayMinutes'] is None: raise ServiceError(422, '请先填写可用时间')
                rows, records, events, topics, _ = self._facts(state)
                state['proposal'] = self._plan(state, tracks, rows, records, events, topics, state.get('plan'))
                state['proposal']['reason'] = body.get('reason') or '调整学习主线；请核对时间重新分配与各主线节奏'
            elif action == 'accept':
                proposal = state.get('proposal')
                if not proposal or body.get('proposalId') != proposal['id']: raise ServiceError(409, '方案已变化，请重新查看')
                self._archive(state, '采纳重新规划')
                state['plan'] = proposal; state['proposal'] = None
                state['plan']['acceptedAt'] = iso(self.t._now())
                self._prepare_reviews(state['plan'])
            elif action == 'dismiss': state['proposal'] = None
            elif action == 'seen':
                if not isinstance(body.get('paragraphs'), dict) or len(body['paragraphs']) > 32: raise ServiceError(400, '段落阅读记录无效')
                for identity, value in body.get('paragraphs', {}).items():
                    if any(p['id'] == identity and p['hash'] == value for p in state['article']): state['seen'][identity] = value
            elif action == 'view':
                view = body.get('view')
                if not isinstance(view, dict) or len(json.dumps(view)) > 8192: raise ServiceError(400, '阅读状态无效')
                if set(view) - {'mode', 'pinned', 'collapsed', 'detailed', 'tone', 'follow', 'x', 'y', 'width', 'height', 'scrollTop'}: raise ServiceError(400, '阅读状态无效')
                if any(key in view and type(view[key]) is not bool for key in ('pinned', 'collapsed', 'detailed', 'follow')): raise ServiceError(400, '阅读状态无效')
                if 'mode' in view and view['mode'] not in ('full', 'float') or 'tone' in view and view['tone'] not in ('平实', '鼓励', '直接'): raise ServiceError(400, '阅读方式无效')
                if any(key in view and (type(view[key]) not in (int, float) or not math.isfinite(view[key]) or not 0 <= view[key] <= 10000000) for key in ('x', 'y', 'width', 'height', 'scrollTop')): raise ServiceError(400, '阅读位置无效')
                state['view'] = view
            elif action == 'difficulty':
                reason = body.get('reason')
                if reason not in REASONS: raise ServiceError(400, '请选择遇到的困难')
                advice = {'meaning': '先重述输入、输出与一个样例，再核对题面条件。', 'idea': '先判断是缺少适用条件还是识别方法，可用短原理检查定位。',
                          'implementation': '先做脱离示例的模板操作，核对不变量与边界。', 'bug': '先核对反例、边界与实际判定，结果本身不能说明具体错因。',
                          'forgot': '先做少量重写检查；再次确认困难后，再采纳补充方案。', 'schedule': '可以调整可用时间、日期与休息日，重排受影响任务。',
                          'easy': '可以直接用未做过的原题验证，独立通过后再调整起点。', 'hard': '先确认困难位置，再选择补先修或减少任务量。',
                          'verify': '短原理检查、模板操作和独立原题各验证不同能力。', 'transfer': '先用不提示算法的限时任务检验识别，交卷后再查看方法。'}[reason]
                state['diagnoses'] = (state['diagnoses'] + [{'reason': reason, 'at': iso(self.t._now()), 'advice': advice}])[-32:]
            elif action == 'reflect':
                task = self._task(state, body.get('key'))
                contest = self.t.connection.execute('SELECT status FROM contests WHERE id=?', (task.get('contestId'),)).fetchone()
                if task['kind'] != 'mixed' or not contest or contest[0] != 'finished': raise ServiceError(422, '先完成限时检验，再确认复盘')
                note = body.get('note', '')
                if not isinstance(note, str) or not 5 <= len(note.strip()) <= 2000: raise ServiceError(422, '请记录至少五个字的复盘，说明问题或下次改进')
                state.setdefault('completed', {})[task['key'] + ':reflection'] = {'at': iso(self.t._now()), 'note': note}
            elif action == 'assist':
                identity = body.get('problemId')
                task = self._task(state, body.get('key'))
                row = self.t._row(identity)
                topic = next((t for t in curriculum()['topics'] if t['id'] == task.get('topicId')), None)
                if task['kind'] in ('lecture', 'course', 'template') and topic and self._matches(row, topic): self.t.mark_solution_seen(identity)
            elif action == 'complete':
                task = self._task(state, body.get('key'))
                if task['kind'] not in ('lecture', 'reflection'): raise ServiceError(422, '本任务须通过实际作答或原理检查完成')
                state.setdefault('completed', {})[task['key']] = iso(self.t._now())
                task['status'] = 'done'
                if task.get('topicId'):
                    state['checks'].setdefault(task['topicId'], {})['read'] = iso(self.t._now())
            elif action == 'quiz':
                tid = body.get('topicId'); quiz = QUIZZES.get(tid)
                if not quiz or type(body.get('answer')) is not int: raise ServiceError(400, '检查题目无效')
                if body['answer'] != quiz[2]: raise ServiceError(422, '尚未通过，请重新核对适用条件与边界')
                state['checks'].setdefault(tid, {})['concept'] = iso(self.t._now())
                state.setdefault('completed', {})[task_identity('quiz', tid)] = iso(self.t._now())
            elif action == 'replace':
                task = self._task(state, body.get('key'))
                if task['kind'] != 'problem' or task.get('status') == 'done': raise ServiceError(422, '只更换尚未完成的独立原题；复习可推迟')
                topic = next(t for t in curriculum()['topics'] if t['id'] == task['topicId'])
                rows, records, events, topics, _ = self._facts(state)
                scheduled = {t.get('original') for t in state['plan']['tasks'] + state['plan'].get('waiting', [])}
                seen_ids = {r['problem_id'] for r in records}
                choices = [r for r in rows if r.get('catalogStatementReady') and not r.get('catalogHidden') and r.get('url') and r['id'] not in seen_ids and canonical_url(r['url']) not in scheduled and self._matches(r, topic)]
                choices.sort(key=lambda r: (r.get('difficulty') if type(r.get('difficulty')) in (int, float) else 10000, r['id']))
                if not choices: raise ServiceError(422, '同类可执行原题正在补充，可以先保留此题或推迟')
                row = choices[0]
                task.update(id=row['id'], key=task_identity('problem', row['id']), title=row['title'], original=canonical_url(row['url']), createdAt=iso(self.t._now()))
            elif action == 'postpone':
                task = self._task(state, body.get('key'))
                try: day = dt.date.fromisoformat(body.get('date', ''))
                except (TypeError, ValueError): raise ServiceError(400, '计划日期无效')
                if day < self.t._now().astimezone(SHANGHAI).date(): raise ServiceError(422, '请选择今天或之后的日期')
                task['notBefore'] = day.isoformat()
                rows, records, events, topics, _ = self._facts(state)
                state['plan'] = self._plan(state, state['plan']['tracks'], rows, records, events, topics, state['plan'])
            elif action == 'delete-history':
                identity = body.get('id')
                self.history(identity)
                write(self.t, HISTORY + identity, {'id': identity, 'deleted': True, 'at': iso(self.t._now())})
            else: raise ServiceError(400, '不支持这个规划操作')
            self._save(state)
        return self.snapshot() if action in ('seen', 'view', 'delete-history') else self.refresh()

    @staticmethod
    def _validate_tracks(tracks):
        valid = {t['id'] for t in curriculum()['topics']}
        if not isinstance(tracks, list) or not 1 <= len(tracks) <= 5 or any(not isinstance(t, str) or t not in valid for t in tracks) or len(set(tracks)) != len(tracks):
            raise ServiceError(400, '请选择 1–5 条不同主线，共用每周总时间')

    def start(self, body):
        with self.t.lock, self.t._library_view():
            state = read(self.t, default=empty())
            if body.get('planId') != (state.get('plan') or {}).get('id'): raise ServiceError(409, '执行计划已更新，请重新读取')
            task = self._task(state, body.get('key'))
            if task['kind'] != 'mixed': raise ServiceError(422, '请选择综合检验任务')
            if task.get('contestId'):
                return {'contest': self.t.contest(task['contestId'])}
            t = self.t
            options = t._contest_options({'strategy': 'comprehensive'})
            candidates = {r['id']: r for r in t._contest_candidates([t._row(i) for i in task['ids']])}
            if any(i not in candidates or not t._eligible_contest_row(candidates[i], options, 0, 10000, set()) for i in task['ids']):
                raise ServiceError(422, '检验题面尚待补齐，先继续已有学习内容，稍后重试')
            slots = [{'letter': chr(65 + n), 'id': i, 'title': candidates[i]['title'], 'difficulty': candidates[i]['difficulty'], 'tags': candidates[i].get('tags', []), 'judgeScope': candidates[i].get('judgeScope', 'samples')} for n, i in enumerate(task['ids'])]
            duration = max(1, task['minutes'] - task.get('reflectionMinutes', 0))
            plan = {'previewId': uuid.uuid4().hex, 'name': '本周综合检验', 'slots': slots, 'duration': duration, 'min': 0, 'max': 10000, 'strategy': 'comprehensive', 'constraints': options}
            t.previews[tuple(task['ids'])] = {'plan': plan, 'slots': slots, 'at': t._now()}
            result = t.start_contest({'ids': task['ids'], 'duration': duration, 'previewId': plan['previewId']})
            task['contestId'] = result['contest']['id']
            self._save(state)
            return result

    def _prepare_reviews(self, plan):
        for task in plan['tasks']:
            if task['kind'] != 'review' or task.get('reviewId'): continue
            identity = digest([plan['id'], task['key']])[:32]
            task['reviewId'] = identity
            write(self.t, 'review-task:' + identity, {'id': identity, 'problemId': task['id'], 'problemKey': task.get('original') or task['id'],
                'due': task['date'], 'minimumAt': task.get('minimumAt'), 'openedAt': None, 'completedAt': None,
                'failures': [], 'processed': [], 'summaryReview': True})

    @staticmethod
    def _task(state, key):
        task = next((t for t in (state.get('plan') or {}).get('tasks', []) if t['key'] == key), None)
        if task is None: raise ServiceError(404, '任务已变化，请重新读取')
        return task


# Small questions verify an explicit condition; no client-authored completion flag.
QUIZZES = {
    'io-basics': ('读取两个整数 a、b 并输出它们的和，需要输出什么？', ['a+b 的值', '字符 a+b', '两个变量的地址'], 0),
    'basic-control': ('循环中 continue 的作用是什么？', ['结束整个程序', '跳过本轮余下部分，继续判断下一轮', '退出所有循环'], 1),
    'arrays': ('长度为 n 的 vector，合法的下标范围是什么？', ['0 到 n', '1 到 n', '0 到 n−1'], 2),
    'functions': ('普通按值传入一个 int，在函数内修改形参会怎样？', ['自动修改调用方变量', '只修改本次调用的副本', '修改所有同名变量'], 1),
    'strings': ('空 string s 可以直接访问 s[0] 并当作第一个字符吗？', ['可以，总有第一个字符', '不能，先确认非空', '只有中文不能'], 1),
    'sorting-basics': ('std::sort 的比较器必须满足什么？', ['严格弱序；相等元素互比均为 false', 'a≤b 时返回 true', '随机返回 true 或 false'], 0),
    'enumeration': ('枚举所有长度 n 的二进制串有多少种？', ['n²', '2n', '2ⁿ'], 2),
    'prefix-difference': ('零起点前缀和 S[0]=0，区间 [l,r) 的和是什么？', ['S[r]−S[l]', 'S[r]−S[l−1]', 'S[r]+S[l]'], 0),
    'binary-search': ('用二分查找第一个满足条件的位置，谓词需要什么性质？', ['在搜索区间形成单一真假分界', '答案必须在正中间', '数组长度必须是二的幂'], 0),
    'two-pointers': ('一般含负数的数组，能直接用“和超标就缩左端”的窗口找固定和吗？', ['总能', '不能，和随端点变化未必单调', '只看数组长度'], 1),
    'recursion': ('递归除了终止条件，还应确认什么？', ['每次调用都严格接近终止状态', '函数名字越短越好', '永远不返回'], 0),
    'bfs': ('普通 BFS 首次到达即得到最短路，需要什么条件？', ['边权可以任意为负', '所有边代价相同', '图必须是一棵树'], 1),
    'dfs': ('含环图做 DFS，为什么通常要记录访问状态？', ['保证所有路径同长', '防止沿环反复递归', '把边权变成正数'], 1),
    'dsu': ('普通并查集能否直接删除任意边并拆分集合？', ['可以，修改一个 parent 即可', '不能，需要其他结构或离线方法', '只要路径压缩就可以'], 1),
    'knapsack': ('一维 0/1 背包按物品更新容量，通常为何倒序？', ['避免同一物品在本轮重复使用', '让每件物品无限使用', '仅为了排序'], 0),
    'fenwick': ('树状数组求 [l,r] 区间和通常如何计算？', ['prefix(r)−prefix(l−1)', 'prefix(r)+prefix(l)', '只读 tree[r]'], 0),
    'segment-tree': ('懒标记下放给子结点后，父结点的该标记应怎样处理？', ['保留并重复下放', '按组合规则更新子标记后清除父标记', '删除整棵树'], 1),
    'dijkstra': ('标准 Dijkstra 为什么不能直接用于一般负权图？', ['负权可能破坏已确定最短距离的性质', '不能使用堆', '不能读取负数'], 0),
    'trie': ('Trie 的一条从根出发的字符路径表示什么？', ['所有字符串长度', '一个字符串前缀', '字符出现的全局次数'], 1),
    'binary-lifting': ('倍增表 up[v][k] 通常表示什么？', ['第 k 个结点', 'v 的第 2ᵏ 个祖先', 'v 的度数'], 1),
    'dinic': ('残量网络中的反向边允许什么？', ['撤回此前送出的部分流量', '任意凭空增加容量', '忽略容量限制'], 0),
    'li-chao': ('标准 Li Chao 树用于维护哪类查询？', ['一组直线在指定 x 处的最小值或最大值', '任意函数无条件排序', '动态图连通性'], 0),
}


def public_quiz(identity):
    quiz = QUIZZES.get(identity)
    if not quiz: raise ServiceError(404, '没有这项原理检查')
    return {'topicId': identity, 'question': quiz[0], 'options': quiz[1]}


def effective_seconds(training):
    from usage import _merge
    total = 0
    for row in training.connection.execute("SELECT value FROM account_preferences WHERE key LIKE 'effective-learning-day:%'"):
        value = json.loads(row[0])
        total += sum(b - a for a, b in _merge(value.get('intervals', [])))
    return round(total)


def record_effective(training, body):
    """Only spans bracketed by real interactions less than five minutes apart.

    No provisional idle tail is committed, so the whole inactive interval is
    excluded. Absolute intervals are unioned across tabs, retries and devices.
    """
    spans = body.get('intervals')
    now = training._now().timestamp()
    if set(body) != {'intervals'} or not isinstance(spans, list) or len(spans) > 128:
        raise ServiceError(400, '有效学习时段无效')
    days = {}
    for span in spans:
        if not isinstance(span, list) or len(span) != 2 or any(type(v) not in (int, float) or not math.isfinite(v) for v in span): raise ServiceError(400, '有效学习时段无效')
        a, b = span
        if not 0 < b - a < 300 or a < now - 7 * 86400 or b > now + 5: raise ServiceError(400, '有效学习时段超出范围')
        cursor = dt.datetime.fromtimestamp(a, SHANGHAI)
        end = dt.datetime.fromtimestamp(b, SHANGHAI)
        while cursor < end:
            stop = min(end, dt.datetime.combine(cursor.date() + dt.timedelta(days=1), dt.time(), SHANGHAI))
            days.setdefault(cursor.date().isoformat(), []).append([cursor.timestamp(), stop.timestamp()]); cursor = stop
    from usage import _merge
    with training.lock:
        for day, intervals in days.items():
            key = 'effective-learning-day:' + day
            previous = read(training, key, {'intervals': []})
            write(training, key, {'intervals': _merge(previous['intervals'] + intervals)})
        return {'saved': True, 'totalSeconds': effective_seconds(training)}
