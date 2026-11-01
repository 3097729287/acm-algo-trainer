"""Small fixed milestones from confirmed submissions and private action facts."""
import datetime as dt
import json
from collections import defaultdict

from progression import SHANGHAI,parse_time


def fun_achievements(training,records):
    result=[]
    def add(identity,name,description,amount,target,at=None):
        result.append(dict(id=identity,name=name,description=description,progress=min(target,amount),target=target,
                           unlocked=amount>=target,unlockedAt=at if amount>=target else None,rewardXp=0))
    # Local runs and samples do not prove a submission to an official judge.
    official=sorted((record for record in records if record.get('scope')=='official' and record.get('mode')=='submit'
                     and record.get('finished_at') and parse_time(record.get('submitted_at'))),key=lambda record:record['submitted_at'])
    dated=[(record,parse_time(record['submitted_at']).astimezone(SHANGHAI)) for record in official]
    for identity,name,description,predicate in (
        ('morning-submit','晨光代码','北京时间 6–9 点完成一次正式提交',lambda stamp:6<=stamp.hour<9),
        ('evening-submit','星光代码','北京时间 20–次日 2 点完成一次正式提交',lambda stamp:stamp.hour>=20 or stamp.hour<2),
        ('weekend-submit','周末开卷','周末完成一次正式提交',lambda stamp:stamp.weekday()>=5),
    ):
        matching=[record['submitted_at'] for record,stamp in dated if predicate(stamp)]
        add(identity,name,description,len(matching),1,matching[0] if matching else None)
    by_day=defaultdict(list)
    for record,stamp in dated:by_day[stamp.date()].append(record)
    for prefix,name,targets,verdict in (
        ('day-submissions','键盘接力',(10,30,60),None),
        ('day-ac','绿灯连线',(5,10,20),'AC'),('day-wa','调试进行曲',(3,10,20),'WA'),
    ):
        for target in targets:
            batches=[[record for record in batch if verdict is None or record.get('verdict')==verdict] for _,batch in sorted(by_day.items())]
            at=next((batch[target-1]['submitted_at'] for batch in batches if len(batch)>=target),None)
            label=f'正式 {verdict}' if verdict else '正式提交'
            add(f'{prefix}-{target}',f'{name} {target}',f'同一天{label} {target} 次',max(map(len,batches),default=0),target,at)
    reviews=defaultdict(list)
    for row in training.connection.execute("SELECT value FROM account_preferences WHERE key LIKE 'review-task:%'"):
        try:task=json.loads(row[0])
        except (ValueError,TypeError):continue
        completed=parse_time(task.get('completedAt'));opened=parse_time(task.get('openedAt'))
        if completed and opened and completed>=opened and task.get('failures') and task.get('independent'):
            reviews[task.get('problemKey') or task.get('problemId')].append((completed,task['completedAt']))
    chains=[]
    for attempts in reviews.values():
        distinct=[]
        for stamp,raw in sorted(attempts):
            if not distinct or stamp-distinct[-1][0]>=dt.timedelta(days=1):distinct.append((stamp,raw))
        chains.append(distinct)
    for target in (2,3,5):
        completed=sorted(chain[target-1][1] for chain in chains if len(chain)>=target)
        add(f'review-rebound-{target}',f'再战老朋友 {target}',f'同一道题在相隔至少一天的 {target} 次间隔复习中，都先错误提交再独立 AC',max(map(len,chains),default=0),target,completed[0] if completed else None)
    actions=[]
    for row in training.connection.execute("SELECT value FROM account_preferences WHERE key LIKE 'activity-actions:%'"):
        try:value=json.loads(row[0])
        except (ValueError,TypeError):continue
        if isinstance(value,dict):actions.extend(event for event in value.values() if isinstance(event,dict))
    hearts={event.get('problemId') or event.get('target') or event.get('key'):event.get('at') for event in actions if event.get('kind')=='heart-given'}
    hearts.pop(None,None)
    for target in (3,10,25):
        times=sorted(stamp for stamp in hearts.values() if stamp)
        add(f'hearts-given-{target}',f'爱心传递 {target}',f'给 {target} 位不同的训练者点爱心',len(hearts),target,times[target-1] if len(times)>=target else None)
    teases=[event.get('at') for event in actions if event.get('kind')=='leader-tease' and event.get('at')]
    add('leader-tease','榜首切磋','给今日排行榜第一名留言“就这?”',len(teases),1,min(teases,default=None))
    # First-place achievements only use settlement receipts from the service.
    days={}
    for row in training.connection.execute('SELECT awards FROM ranking_reward_totals'):
        try:awards=json.loads(row[0])
        except (ValueError,TypeError):continue
        for award in awards if isinstance(awards,list) else ():
            if award.get('rank')!=1 or award.get('period') not in {'daily','day'}:continue
            key=award.get('startDate') or award.get('start') or award.get('key') or award.get('periodKey') or award.get('date')
            stamp=award.get('settledAt') or award.get('awardedAt') or award.get('createdAt') or award.get('at')
            if key:days[str(key)]=stamp
    for target in (3,7,30):
        times=sorted(stamp for stamp in days.values() if stamp)
        add(f'daily-leader-{target}',f'霸榜今日第一 {target} 天',f'累计获得 {target} 天今日排行榜第一名',len(days),target,times[target-1] if len(times)>=target else None)
    return result
