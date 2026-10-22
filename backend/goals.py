"""Deadline plans with explicit workload assumptions and real acceptance evidence."""
import datetime as dt
import hashlib
import json
import math
import re
import uuid
from training import ServiceError, iso
from progression import SHANGHAI, parse_time
from insights import canonical_url

DISCLAIMER='题量是训练安排，不保证评级或奖项；每周还需比赛、复盘与专项学习。区域赛另需队伍配合。'


def shared_contest_plan(goals, rows=(), accepted_keys=()):
    """A contest appears once, with the strongest active requirement per field."""
    merged = {}
    for goal in goals:
        if goal.get('workloadCompleted'):
            continue
        for item in goal.get('contestPlan', []):
            if item['target'] <= 0:
                continue
            name = item['contest']
            saved = merged.setdefault(name, {**item, 'goalIds': [], 'referenceRating': 0})
            saved['target'] = max(saved['target'], item['target'])
            rating = goal.get('currentRating', 0)
            if rating >= saved['referenceRating']:
                saved['problems'] = item['problems']
                saved['referenceRating'] = rating
            saved['goalIds'].append(goal['id'])
    contests = list(merged.values())
    chosen=set(accepted_keys)
    patterns={'Codeforces Div.3':r'Div\.\s*3|第\s*3\s*组',
              'AtCoder ABC':r'ABC|AtCoder Beginner|AtCoder 初学者',
              '牛客周赛':r'周赛', '洛谷基础赛 / 月赛':r'入门赛|基础赛|月赛'}
    for item in contests:
        lower,upper=('C','F') if item['problems']=='C–F' else ('A','D')
        candidates=[]
        for row in rows:
            identity=canonical_url(row.get('url')) or row['id']
            if identity in chosen or row.get('catalogHidden'):continue
            platform={'Codeforces Div.3':'Codeforces','AtCoder ABC':'AtCoder','牛客周赛':'牛客','洛谷基础赛 / 月赛':'洛谷'}[item['contest']]
            if row.get('platform')!=platform:continue
            name=(row.get('contestFullName') or '')+' '+row.get('contest','')
            if not re.search(patterns[item['contest']],name,re.I):continue
            letter=str(row.get('problem',''))
            if len(letter)==1 and not lower<=letter<=upper:continue
            candidates.append(row)
        candidates.sort(key=lambda row:row['id'])
        candidates.sort(key=lambda row:str(row.get('contestDate') or row.get('startedAt') or ''),reverse=True)
        questions=[]
        for row in candidates:
            identity=canonical_url(row.get('url')) or row['id']
            if identity in chosen:continue
            chosen.add(identity)
            questions.append({field:row.get(field) for field in ('id','title','contest','problem','difficulty','difficultyEstimated')})
            if len(questions)>=item['target']:break
        item['questions']=questions
    return {'contests': contests, 'total': sum(item['target'] for item in contests),
            'goalCount': sum(not goal.get('workloadCompleted') for goal in goals)}


class Goals:
    def __init__(self,training):self.training=training

    def _activate_recommendation(self, db, identity, stamp):
        ids = self.training._equivalent_ids(identity)
        placeholders = ','.join('?' for _ in ids)
        today = self.training._now().astimezone(SHANGHAI).date()
        removed = db.execute(f'SELECT removed_at FROM training WHERE id IN ({placeholders}) AND active=0 AND removed_at IS NOT NULL', ids).fetchall()
        if any(parse_time(r['removed_at']).astimezone(SHANGHAI).date() >= today for r in removed):
            return
        self.training._activate(db, identity, stamp)

    def save(self,body):
        if not isinstance(body,dict):raise ServiceError(422,'目标参数无效')
        title=body.get('title','').strip() if isinstance(body.get('title',''),str) else ''
        if not title or len(title)>160:raise ServiceError(422,'请填写 1–160 字的具体目标')
        kind=body.get('kind','custom')
        match=re.search(r'(?i)\bcf\s*(\d{3,4})\b',title)
        if match and kind=='custom':kind='cf';body={**body,'targetRating':int(match[1])}
        if kind not in ('cf','xcpc','lanqiao','custom'):raise ServiceError(422,'目标类型无效')
        today=self.training._now().astimezone(SHANGHAI).date()
        try:
            deadline=dt.date.fromisoformat(body['deadline'])
            baseline=int(body.get('currentRating',1000))
            minutes=int(body.get('dailyMinutes',90))
            target=int(body.get('targetRating',2200 if kind=='cf' else 2000 if kind=='xcpc' else 1800))
            total=int(body.get('totalProblems',100)) if kind=='custom' else max(30,math.ceil(max(0,target-baseline)/100)*30)
        except (ValueError,TypeError,KeyError,OverflowError):raise ServiceError(422,'请填写具体截止日期、起点和每日可用分钟数')
        if not today<=deadline<=today+dt.timedelta(days=1826):raise ServiceError(422,'截止日期须在今天至五年内；过期目标请调整日期')
        if not 0<=baseline<=4000 or not 200<=target<=4000 or not 15<=minutes<=720 or not 1<=total<=10000:
            raise ServiceError(422,'起点须为 0–4000，目标参考值为 200–4000，每日 15–720 分钟，自定义题量 1–10000')
        t=self.training
        with t.lock:
            identity=body.get('id') or 'goal-'+uuid.uuid4().hex
            previous=t.connection.execute('SELECT * FROM goals WHERE id=?',(identity,)).fetchone()
            if body.get('id') and not previous:raise ServiceError(404,'目标不存在')
            if not previous and t.connection.execute("SELECT COUNT(*) FROM goals WHERE archived=0").fetchone()[0]>=10:raise ServiceError(422,'最多同时规划 10 个目标，请先归档已结束目标')
            start=previous['created_at'] if previous else iso(t._now())
            config={'title':title,'kind':kind,'deadline':deadline.isoformat(),'currentRating':baseline,'targetRating':target,
                    'dailyMinutes':minutes,'totalProblems':total,'minutesPerProblem':60 if kind in ('cf','xcpc') else 45,
                    'assumption':'参考值每提高 100，安排 30 道新题；最低 30 题。' if kind!='custom' else '按你填写的题量安排。',
                    'disclaimer':DISCLAIMER}
            with t._write() as db:
                db.execute('INSERT INTO goals(id,created_at,config,archived) VALUES(?,?,?,0) ON CONFLICT(id) DO UPDATE SET config=excluded.config',
                           (identity,start,json.dumps(config,ensure_ascii=False)))
            return self.list(assign=True)

    def archive(self,identity):
        t=self.training
        with t.lock:
            if not t.connection.execute('SELECT 1 FROM goals WHERE id=?',(identity,)).fetchone():raise ServiceError(404,'目标不存在')
            with t._write() as db:db.execute('UPDATE goals SET archived=1 WHERE id=?',(identity,))
        return self.list()

    def list(self, assign=False):
        t=self.training
        with t.lock:
            now=t._now();today=now.astimezone(SHANGHAI).date()
            if not t.connection.execute('SELECT 1 FROM goals WHERE archived=0 LIMIT 1').fetchone():return {'goals':[],'date':today.isoformat(),'contestPlan':shared_contest_plan([]),'goalTasks':[]}
            # Activating several recommendations recomputes aliases for each
            # task. Reuse a single fresh catalogue for this allocation only.
            with t._library_view():
                return self._list(assign)

    def _list(self, assign=False):
        t=self.training
        with t.lock:
            now=t._now();today=now.astimezone(SHANGHAI).date()
            review_plan = t.review_plan()
            rows=t._library();metadata={row['id']:row for row in rows}
            # A bundled roster can replace the visible remote row for the same
            # URL. Keep persisted selections and receipts attached to that task.
            for identity, preferred in t._identity_map(rows).items():
                if identity not in metadata and preferred in metadata:
                    metadata[identity]={**metadata[preferred],'id':identity}
            accepted={}
            for record in t.connection.execute("SELECT * FROM submissions WHERE mode='submit' AND verdict='AC' AND scope='official' AND finished_at IS NOT NULL ORDER BY submitted_at,rowid"):
                row=metadata.get(record['problem_id'],{})
                key=canonical_url(row.get('url')) or record['problem_id']
                accepted.setdefault(key,{'id':record['problem_id'],'at':parse_time(record['submitted_at'])})
            extension=getattr(t.store,'extensions',None)
            if extension:
                for account in extension.snapshot().get('accounts',[]):
                    for item in account.get('solved',[]):
                        stamp=parse_time(item.get('acceptedAt'));key=canonical_url(item.get('url'))
                        if key and stamp and (key not in accepted or stamp<accepted[key]['at']):accepted[key]={'id':None,'at':stamp}
            locked=set(t._locked_ids(t.connection.execute("SELECT * FROM contests WHERE status='running'").fetchone())) if t.active_contest() else set()
            records=t.connection.execute('SELECT * FROM goals WHERE archived=0 ORDER BY created_at,id').fetchall()
            assignments={row['goal_id']:row for row in t.connection.execute('SELECT * FROM goal_daily_assignments WHERE day=?',(today.isoformat(),))}
            problem_key=lambda row:canonical_url(row.get('url')) or row['id']
            # Reserve all existing selections before allocating any new goal.
            # Older releases could assign the same canonical problem twice.
            owners={}
            for record in records:
                saved=assignments.get(record['id'])
                for identity in json.loads(saved['ids']) if saved else []:
                    if identity in metadata:owners.setdefault(problem_key(metadata[identity]),record['id'])
            result=[];daily_selections={}
            for record in records:
                goal=json.loads(record['config']);start=parse_time(record['created_at']);first=start.astimezone(SHANGHAI).date();end=dt.date.fromisoformat(goal['deadline'])
                days=max(1,(end-first).days+1);total=goal['totalProblems']
                evidence=[item for item in accepted.values() if start<item['at']<=now and item['at'].astimezone(SHANGHAI).date()<=end]
                done=len(evidence);elapsed=max(0,min(days,(today-first).days));expected=math.ceil(total*elapsed/days)
                due=math.ceil(total*min(days,elapsed+1)/days);daily=max(0,due-expected)
                all_today_done=sum(item['at'].astimezone(SHANGHAI).date()==today for item in evidence)
                left=max(0,(end-today).days+1);remaining=max(0,total-done);weekly=math.ceil(remaining*min(7,left)/max(1,left))
                # Reserve 30% of study time for reviewing and contest participation.
                capacity=math.floor(left*goal['dailyMinutes']*.7/goal['minutesPerProblem']);warnings=[]
                if today>end and remaining:warnings.append('截止日期已过，训练题量尚未完成。请复盘并调整目标。')
                if remaining>capacity:warnings.append(f'时间压力：剩余 {remaining} 题超出预计容量 {capacity} 题，建议延后截止日期或调整目标。')
                if done<expected:warnings.append(f'进度落后 {expected-done} 题；本周需安排约 {weekly} 题。')
                if left<=14 and goal['kind']!='custom' and goal['targetRating']-goal['currentRating']>=300:warnings.append('期限明显偏紧，短期题量不能替代持续参赛与能力积累。')
                if goal['kind']=='cf' and goal['targetRating']<=goal['currentRating']:warnings.append('填写的起点已达到目标参考值，可改为巩固目标；评级结果需原站核验。')
                def score(row):
                    preferred=(goal['kind']=='lanqiao' and '蓝桥' in row['contest']) or (goal['kind']=='cf' and row.get('platform')=='Codeforces') or (goal['kind']=='xcpc' and re.search(r'(?i)(ICPC|CCPC)',row['contest']))
                    difficulty=row.get('difficulty');fit=abs(difficulty-goal['currentRating']-150) if isinstance(difficulty,(int,float)) else 500
                    return (not preferred,fit,row['id'])
                candidates=[row for row in rows if not row.get('catalogHidden') and row['id'] not in locked and (canonical_url(row.get('url')) or row['id']) not in accepted]
                candidates.sort(key=score)
                families=[('Codeforces Div.3',4),('AtCoder ABC',3),('牛客周赛',2),('洛谷基础赛 / 月赛',1)]
                if goal['kind']=='xcpc':families=[('Codeforces Div.3',2),('AtCoder ABC',2),('牛客周赛',4),('洛谷基础赛 / 月赛',2)]
                amounts=[1 if weekly>=4 else 0 for _ in families]
                for _ in range(max(0,weekly-sum(amounts))):
                    index=max(range(4),key=lambda i:families[i][1]/(amounts[i]+1))
                    amounts[index]+=1
                ranges=('A–D','A–D','A–D','基础题') if goal['currentRating']<1400 else ('C–F','C–F','C–F','提高题')
                contest_plan=[{'contest':name,'target':amount,'problems':ranges[i]} for i,((name,_),amount) in enumerate(zip(families,amounts))]
                before_today=max(0,total-done+all_today_done)
                task_target=min(8,before_today,max(daily,math.ceil(before_today/max(1,left)))) if left else 0
                if review_plan['minutes']:
                    task_target = min(task_target, review_plan['newMinutes'] // goal['minutesPerProblem'])
                # One persisted selection per goal/day: refreshes and restarts cannot
                # change the assignments or undo a user's removal on the same day.
                saved=assignments.get(record['id'])
                original_ids=json.loads(saved['ids']) if saved else []
                seen=set();selected=[]
                for identity in original_ids:
                    row=metadata.get(identity)
                    if not row:continue
                    key=problem_key(row)
                    if key in seen or owners.get(key)!=record['id']:continue
                    seen.add(key);selected.append(row)
                if saved and saved['target'] is not None:task_target=saved['target']
                if review_plan['reviewOnly']:
                    task_target = 0
                    selected = []
                elif review_plan['minutes']:
                    task_target = min(task_target, review_plan['newMinutes'] // goal['minutesPerProblem'])
                    selected = selected[:task_target]
                repairing=not saved or saved['target'] is None or len(selected)!=len(original_ids)
                if repairing and not review_plan['reviewOnly']:
                    for row in candidates:
                        if len(selected)>=task_target:break
                        key=problem_key(row)
                        if key in seen or key in owners:continue
                        owners[key]=record['id']
                        seen.add(key);selected.append(row)
                    if assign and not (saved and review_plan['minutes']):
                        with t._write() as db:
                            db.execute('INSERT INTO goal_daily_assignments(goal_id,day,ids,target) VALUES(?,?,?,?) ON CONFLICT(goal_id,day) DO UPDATE SET ids=excluded.ids,target=excluded.target',
                                       (record['id'],today.isoformat(),json.dumps([row['id'] for row in selected],ensure_ascii=False),task_target))
                            for row in selected:
                                if row['id'] not in original_ids:self._activate_recommendation(db,row['id'],iso(now))
                today_done=sum(1 for row in selected if (item:=accepted.get(problem_key(row)))
                               and start<item['at']<=now and item['at'].astimezone(SHANGHAI).date()==today)
                daily_selections[record['id']]=selected
                result.append({**goal,'id':record['id'],'createdAt':record['created_at'],'progress':done,'remaining':remaining,
                    'remainingDays':left,'weeklyTarget':weekly,'weeklyPlan':[],'contestPlan':contest_plan,'capacity':capacity,'warnings':warnings,'workloadCompleted':done>=total,
                    'dailyTask':{'date':today.isoformat(),'target':task_target,'progress':today_done,'completed':today_done>=task_target,
                                 'problems':[{key:row.get(key) for key in ('id','title','contest','difficulty')} for row in selected if (canonical_url(row.get('url')) or row['id']) not in accepted]}})
            tasks=self._tasks(result,rows,metadata,accepted,daily_selections,assign,locked)
            return {'goals':result,'date':today.isoformat(),'notice':DISCLAIMER,'contestPlan':shared_contest_plan(result,rows,accepted),'goalTasks':tasks}

    def _tasks(self,goals,rows,metadata,accepted,daily_selections,assign,locked):
        """Daily selections and new-contest practice groups share the existing journal.

        Generated groups are ordinary synchronized practice_sets, with a reserved
        ID prefix. No new snapshot protocol or second completion ledger is needed.
        A persisted selection never reactivates a task the user removed.
        """
        t=self.training;now=t._now();recent=now-dt.timedelta(days=7)
        review_plan = t.review_plan()
        if review_plan['reviewOnly'] or (review_plan['minutes'] and review_plan['newMinutes'] < min((g.get('minutesPerProblem',45) for g in goals), default=45)):
            return []
        key=lambda row:canonical_url(row.get('url')) or row['id']
        plans={goal['id']:goal for goal in goals if not goal['workloadCompleted']}
        tasks={}
        maximum = review_plan['newMinutes'] // min((g.get('minutesPerProblem',45) for g in goals), default=45) if review_plan['minutes'] else None
        def include(row,goal,source):
            if row['id'] in locked:return
            identity=key(row)
            if maximum is not None and identity not in tasks and len(tasks) >= maximum:return
            task=tasks.setdefault(identity,{**{field:row.get(field) for field in ('id','title','contest','problem','platform','difficulty','difficultyEstimated')},
                'accepted':identity in accepted,'goalTitles':[],'sources':[]})
            if goal['title'] not in task['goalTitles']:task['goalTitles'].append(goal['title'])
            if source not in task['sources']:task['sources'].append(source)
        def date(value):
            try:return parse_time(value) if value else None
            except (TypeError,ValueError,AttributeError):return None
        families={'Codeforces Div.3':('Codeforces',r'Div\.\s*3|第\s*3\s*组'),
                  'AtCoder ABC':('AtCoder',r'\bABC\b|AtCoder Beginner|AtCoder 初学者'),
                  '牛客周赛':('牛客',r'周赛'), '洛谷基础赛 / 月赛':('洛谷',r'入门赛|基础赛|月赛')}
        events={}
        for row in rows:
            if row.get('catalogHidden'):continue
            event_key=(canonical_url(row.get('url')) or '').rsplit('/',1)[0]
            if row.get('platform')=='洛谷':event_key='luogu/'+str(row.get('contestId') or row.get('contest',''))
            if not event_key:continue
            events.setdefault((row.get('platform'),event_key),[]).append(row)
        persisted={record['id']:dict(record) for record in t.connection.execute("SELECT * FROM practice_sets WHERE id LIKE 'goal-contest:%'")}
        for goal in plans.values():
            for row in daily_selections.get(goal['id'],[]):include(row,goal,'每日目标')
            prefix='goal-contest:'+goal['id']+':'
            for record in persisted.values():
                if not record['id'].startswith(prefix):continue
                for identity in json.loads(record['ids']):
                    if identity in metadata:include(metadata[identity],goal,'比赛目标')
            for requirement in goal.get('contestPlan',[]):
                if review_plan['minutes']:continue
                if requirement['target']<=0:continue
                platform,pattern=families[requirement['contest']]
                matches=[]
                for (site,event_key),roster in events.items():
                    if site!=platform or not re.search(pattern,(roster[0].get('contestFullName') or '')+' '+roster[0].get('contest',''),re.I):continue
                    end=max((stamp for row in roster if (stamp:=date(row.get('endedAt') or row.get('contestDate') or row.get('startedAt')))),default=None)
                    added=max((stamp for row in roster if (stamp:=date(row.get('addedAt')))),default=end)
                    if end and end>now:continue
                    if not added or added<max(recent,date(goal['createdAt'])) or added>now:continue
                    matches.append((added,event_key,roster))
                for _,event_key,roster in sorted(matches,key=lambda item:item[0],reverse=True)[:4]:
                    lower,upper=('C','F') if requirement['problems']=='C–F' else ('A','D')
                    seen=set();eligible=[]
                    for row in sorted(roster,key=lambda row:(str(row.get('problem','')),row['id'])):
                        letter=str(row.get('problem','')).upper()
                        identity=key(row)
                        if len(letter)==1 and not lower<=letter<=upper:continue
                        if identity in seen or row['id'] in locked:continue
                        seen.add(identity);eligible.append(row)
                    selected=eligible[:min(8,requirement['target'])]
                    if not selected:continue
                    group_id=prefix+hashlib.sha256(event_key.encode()).hexdigest()[:20]
                    saved=persisted.get(group_id)
                    # Frozen groups may expand with a larger requirement or a
                    # late public task. Existing rows retain their ownership.
                    old_ids=json.loads(saved['ids']) if saved else []
                    ids=list(dict.fromkeys(old_ids+[row['id'] for row in selected]))
                    if assign and ids!=old_ids:
                        name=f"目标题目 · {goal['title']} · {selected[0]['contest']} · {group_id[-8:]}"
                        with t._write() as db:
                            db.execute('INSERT INTO practice_sets(id,name,ids,created_at) VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET ids=excluded.ids',
                                (group_id,name,json.dumps(ids,ensure_ascii=False),iso(now)))
                            for row in selected:
                                if row['id'] not in old_ids:self._activate_recommendation(db,row['id'],iso(now))
                    for row in selected:include(row,goal,'比赛目标')
        return sorted(tasks.values(),key=lambda task:(task['accepted'],task['contest'] or '',str(task['problem'] or '')))
