"""Private foreground intervals; learning-page time is kept separately."""
import datetime as dt
import json
import math
import re
from training import ServiceError, iso
from progression import SHANGHAI

KEY='usage-v1'
LEARNING_KEY='learning-usage-v1'

def _state(training,key=KEY):
    row=training.connection.execute('SELECT value FROM account_preferences WHERE key=?',(key,)).fetchone()
    try:
        value=json.loads(row['value']) if row else {}
        if value.get('version')==1:return value
    except (ValueError,TypeError,AttributeError):pass
    return {'version':1,'days':{},'sessions':{}}

def _merge(intervals):
    result=[]
    for begin,end in sorted(intervals):
        if result and begin<=result[-1][1]:result[-1][1]=max(end,result[-1][1])
        else:result.append([begin,end])
    return result

def snapshot(training):
    with training.lock:
        state=_state(training)
    days=[{'date':day,'seconds':round(value['seconds'])} for day,value in sorted(state['days'].items())]
    best=max(days,key=lambda day:day['seconds'],default=None)
    return {'days':days,'totalSeconds':sum(day['seconds'] for day in days),'maxDailySeconds':best['seconds'] if best else None,
            'maxDailyDate':best['date'] if best else None,'startedAt':state.get('startedAt')}

def learning_seconds(training,day):
    with training.lock:
        return max(0,min(86400,float(_state(training,LEARNING_KEY)['days'].get(day,{}).get('seconds',0))))

def _append(value,now,seconds):
    start=now-dt.timedelta(seconds=seconds);cursor=start
    while cursor<now:
        boundary=dt.datetime.combine(cursor.date()+dt.timedelta(days=1),dt.time(),SHANGHAI)
        end=min(boundary,now);day=cursor.date().isoformat();entry=value['days'].setdefault(day,{'seconds':0,'intervals':[]})
        intervals=_merge(entry.get('intervals',[])+[[cursor.timestamp(),end.timestamp()]])
        entry.update(intervals=intervals,seconds=sum(stop-begin for begin,stop in intervals));cursor=end
    value.setdefault('startedAt',iso(start))
    for day,entry in value['days'].items():
        if day<start.date().isoformat():entry.pop('intervals',None)

def record(training,body):
    if (not isinstance(body,dict) or set(body)-{'sessionId','sequence','seconds','learning'} or not {'sessionId','sequence','seconds'}<=set(body)
        or not isinstance(body['sessionId'],str) or not re.fullmatch(r'[0-9a-f-]{36}',body['sessionId'])
        or type(body['sequence']) is not int or not 1<=body['sequence']<=2**31
        or type(body['seconds']) not in (int,float) or not math.isfinite(body['seconds']) or not 0<body['seconds']<=60
        or type(body.get('learning',False)) is not bool):
        raise ServiceError(400,'使用时长格式无效')
    now=training._now().astimezone(SHANGHAI)
    with training.lock:
        value=_state(training);sessions=value['sessions'];previous=sessions.get(body['sessionId'],{})
        if body['sequence']<=previous.get('sequence',0):return {'saved':True}
        _append(value,now,body['seconds'])
        sessions[body['sessionId']]={'sequence':body['sequence'],'lastAt':iso(now)}
        # Past intervals are finalized, and bounded session cursors only prevent retries.
        value['sessions']=dict(sorted(sessions.items(),key=lambda pair:pair[1]['lastAt'])[-64:])
        with training._write() as connection:
            connection.execute('INSERT INTO account_preferences VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at',
                               (KEY,json.dumps(value,ensure_ascii=False,separators=(',',':')),iso(now)))
            if body.get('learning'):
                study=_state(training,LEARNING_KEY)
                _append(study,now,body['seconds'])
                connection.execute('INSERT INTO account_preferences VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at',
                                   (LEARNING_KEY,json.dumps(study,ensure_ascii=False,separators=(',',':')),iso(now)))
    return {'saved':True}
