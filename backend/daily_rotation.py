"""Stable daily variety derived from first ACs and actual account actions."""
import datetime as dt
import hashlib
import json
from progression import SHANGHAI,TASKS,local_date

def _task(identity,title,description,kind,target=1,xp=30,**extra):
    return dict(id=identity,title=title,description=description,kind=kind,target=target,minDifficulty=0,xp=xp,scope='official',version=2,newOnly=True,**extra)

CHALLENGES=[
    *[dict(task,newOnly=True,description=task['description'].replace('一道','一道此前未 AC 的新')) for task in TASKS[3:]],
    _task('new-2','探索新题','首次 AC 两道不同的新题','solve',2,70),
    _task('new-independent','独立启航','独立首次 AC 一道新题','independent',xp=45),
    _task('new-platforms','跨站游学','在两个平台各首次 AC 一道新题','platforms',2,80),
    _task('new-topics','一题多获','首次 AC 的新题涉及至少两个不同知识点','topics',2,55),
    _task('new-morning','晨间热身','北京时间 6–11 点首次 AC 一道新题','morning',xp=40),
    _task('new-evening','晚间一题','北京时间 18–22 点首次 AC 一道新题','evening',xp=40),
    _task('new-topic-pair','连点成线','首次 AC 两道具有同一知识点的新题','topic-pair',2,70),
]
EXPLORATIONS=[
    _task('practice-new-one','基础巩固','首次 AC 一道新题','solve',xp=30),
    _task('practice-independent','独立巩固','独立首次 AC 一道新题','independent',xp=40),
]

def adapt_challenge(task, ability):
    """Difficulty tasks follow confirmed practice ability, never XP or rank art."""
    result=dict(task)
    if not result.get('minDifficulty'):return result
    score=ability if type(ability) in (int,float) and 0<ability<=4000 else None
    base=int(score//100)*100 if score is not None else 800
    offset=100 if result['id']=='hard-1500' else 200
    target=min(4000,base+offset)
    result.update(minDifficulty=target,abilityReference=score,difficultyEvidenceRequired=True,
                  xp=min(result.get('xp',100),80 if offset==100 else 100),
                  description=f'首次 AC 一道难度至少 {target} 的新题',
                  challengeBasis='近期独立作答能力' if score is not None else '入门训练起点，能力证据不足')
    return result

def tasks_for(day,owner):
    # Fixed within the Beijing date and independent of UI opening order.
    rank=lambda item:hashlib.sha256((str(owner)+'\0'+day+'\0'+item['id']).encode()).digest()
    challenge=sorted(CHALLENGES,key=rank)[:2]
    exploration=sorted(EXPLORATIONS,key=rank)[:1]
    return [dict(task) for task in [*TASKS[:3],*challenge,*exploration]]

def record_action(connection,kind,stamp,key):
    date=local_date(stamp)
    if date is None:return
    name='activity-actions:'+date.isoformat()
    row=connection.execute('SELECT value FROM account_preferences WHERE key=?',(name,)).fetchone()
    try:events=json.loads(row[0]) if row else {}
    except (ValueError,TypeError):events={}
    identity=hashlib.sha256((kind+'\0'+str(key)).encode()).hexdigest()
    if identity in events or len(events)>=512:return
    events[identity]={'kind':kind,'key':str(key),'at':stamp}
    connection.execute('INSERT INTO account_preferences VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at',(name,json.dumps(events,ensure_ascii=False,sort_keys=True),stamp))

def actions(training,day):
    row=training.connection.execute('SELECT value FROM account_preferences WHERE key=?',('activity-actions:'+day,)).fetchone()
    if not row:return []
    try:values=json.loads(row[0])
    except (ValueError,TypeError):return []
    return [{'_activityEvent':True,'kind':value['kind'],'day':day,'eventKey':key,'acceptedAt':value['at']} for key,value in values.items()]

def annotate(training,day,evidence):
    from custom_training_lists import read_lists
    listed={item['problemId'] for entry in read_lists(training) for item in entry['problems']}
    result=[]
    for item in evidence:
        value=dict(item)
        value.setdefault('newProblem',False)
        value['personalList']=item.get('problemId') in listed
        result.append(value)
    return result+actions(training,day)

def action_achievements(training,evidence):
    from preferences import read_preferences
    from custom_training_lists import read_lists
    prefs=read_preferences(training)['preferences'] or {}
    favorites=len(set(prefs.get('favorites',[])))
    learned=len(set(prefs.get('learnedLectures',[])))
    lists=read_lists(training)
    journals=[]
    for row in training.connection.execute("SELECT value FROM account_preferences WHERE key LIKE 'activity-actions:%'"):
        try:journals.extend(json.loads(row[0]).values())
        except (ValueError,TypeError):pass
    themes=[event['at'] for event in journals if event['kind']=='appearance']
    topics={tag for item in evidence for tag in item.get('tags',[])}
    platforms={item['platform'] for item in evidence if item.get('platform')}
    rows=[]
    def add(identity,title,description,amount,target,at=None):rows.append(dict(id=identity,name=title,description=description,progress=min(target,amount),target=target,unlocked=amount>=target,unlockedAt=at,rewardXp=0))
    add('collection-10','题海拾贝','收藏十道不同题目',favorites,10)
    add('curation-1','自成体系','创建第一份自己的题单',len(lists),1)
    add('curation-5','条理分明','创建五份自己的题单',len(lists),5)
    add('appearance-1','焕然一新','为工作台选择一次新的外观',len(themes),1,min(themes,default=None))
    add('lessons-1','点亮知识','标记一个已学会的从零讲知识点',learned,1)
    add('lessons-10','知识拼图','标记十个已学会的从零讲知识点',learned,10)
    add('topics-5','触类旁通','首次 AC 的题目覆盖五个不同知识点',len(topics),5)
    add('platforms-3','四海求索','在三个平台留下首次 AC',len(platforms),3)
    from training import parse_time
    clean={item['problemId']:parse_time(item.get('acceptedAt')) for item in evidence if item.get('independent')}
    failed=set()
    for row in training.connection.execute("SELECT problem_id,finished_at FROM submissions WHERE mode='submit' AND scope='official' AND verdict IN ('WA','TLE','RE','MLE') AND finished_at IS NOT NULL"):
        accepted=clean.get(row[0]);failure=parse_time(row[1])
        if accepted and failure and failure<accepted:failed.add(row[0])
    add('recovery-3','百折不挠','三个曾提交失败的题目最终独立首次 AC',len(failed),3)
    totals={}
    for item in evidence:
        if item.get('day'):totals[item['day']]=totals.get(item['day'],0)+1
    add('new-ten-day','十题探索','同一天首次 AC 十道不同新题',max(totals.values(),default=0),10)
    # Only actual service-returned awards prove a historical daily first place.
    wins=[]
    for row in training.connection.execute('SELECT awards FROM ranking_reward_totals'):
        try:awards=json.loads(row[0])
        except (ValueError,TypeError):continue
        wins.extend(item for item in awards if item.get('rank')==1 and item.get('period') in {'day','daily'})
    add('daily-leader-1','今日领跑','获得共享排行榜的每日第一名奖励',len(wins),1)
    return rows
