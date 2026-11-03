"""Bind an original-site VP receipt to one validated local replay preview."""
import datetime as dt
import re
from urllib.parse import urlsplit

def virtual_spec(rows, duration):
    """Infer only from a common exact original contest, never display names."""
    candidates=[]
    for row in rows:
        url=row.get('url') or ''
        p=urlsplit(url)
        match=re.fullmatch(r'/(contest|gym)/(\d+)/problem/[A-Za-z]\d?',p.path)
        if p.scheme=='https' and p.hostname in ('codeforces.com','www.codeforces.com') and match:
            candidates.append(('Codeforces',match[1],match[2]))
            continue
        match=re.fullmatch(r'/problem/(\d+)',p.path)
        if p.scheme=='https' and p.hostname=='qoj.ac' and match and str(row.get('contestId','')).isdigit():
            candidates.append(('QOJ','contest',str(row['contestId'])))
            continue
        match=re.fullmatch(r'/acm/contest/(\d+)/[A-Za-z]\d?',p.path)
        if p.scheme=='https' and p.hostname=='ac.nowcoder.com' and match:
            candidates.append(('牛客','contest',match[1]))
            continue
        return None
    if not candidates or len(set(candidates))!=1:return None
    platform,kind,identity=candidates[0]
    if platform=='Codeforces':
        url=f'https://codeforces.com/{kind}/{identity}'
        registration=f'https://codeforces.com/contestRegistration/{identity}/virtual/true'
    elif platform=='QOJ':url=registration=f'https://qoj.ac/contest/{identity}'
    else:url=registration=f'https://ac.nowcoder.com/acm/contest/{identity}'
    return {'platform':platform,'contestId':identity,'url':url,'registrationUrl':registration,
            'duration':duration,'required':platform=='Codeforces'}

def confirmed_receipt(spec, receipt, now):
    from training import ServiceError,parse_time
    if not isinstance(receipt,dict) or receipt.get('confirmed') is not True:
        raise ServiceError(409,'原站 VP 尚未确认，本地比赛尚未开始')
    if any(receipt.get(key)!=spec[key] for key in ('platform','contestId','url')):
        raise ServiceError(409,'原站 VP 与当前比赛不一致')
    try:began=parse_time(receipt['startedAt']);ended=parse_time(receipt['deadline'])
    except (KeyError,ValueError,TypeError):raise ServiceError(409,'原站 VP 计时未确认')
    if not began or not ended or ended<=now or began>now+dt.timedelta(minutes=3) or abs((ended-began).total_seconds()-spec['duration']*60)>2:
        raise ServiceError(409,'原站 VP 计时与当前比赛不一致')
    return {key:receipt[key] for key in ('platform','contestId','url','startedAt','deadline','confirmed')}

def start_replay(server, training, body):
    from training import ServiceError
    # Serialize original-site intent with local starts, without holding SQLite's
    # lock across browser navigation. The account request barrier stays active.
    with server.work_start_lock:
        prepared=training.start_contest(body,prepare_only=True)
        spec=prepared.get('originalVirtual')
        receipt=None
        if spec:
            starter=getattr(server,'original_virtual_starter',None)
            if not callable(starter):
                if spec['required']:raise ServiceError(503,'请使用支持原站 VP 的最新版桌面程序')
            else:
                answer=starter(spec,training)
                if not isinstance(answer,dict):raise ServiceError(503,'原站 VP 尚未确认，本地比赛尚未开始')
                if answer.get('supported') is False:
                    if spec['required']:raise ServiceError(409,'原站 VP 暂不可用，本地比赛尚未开始')
                else:receipt=confirmed_receipt(spec,answer,training._now())
        return training.start_contest(body,original_virtual=receipt)
