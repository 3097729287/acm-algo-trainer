"""Bounded, read-only imports of the configured owner's actual submissions."""
import datetime as dt
import re
from urllib.parse import quote, urlencode
from public_platforms import utc, lg_data

LABELS={'atcoder':'AtCoder','nowcoder':'牛客','luogu':'洛谷'}
LUOGU_VERDICTS={2:'CE',3:'OLE',4:'MLE',5:'TLE',6:'WA',7:'RE',12:'AC',14:'WA'}


def receipt(platform,owner,identity,url,verdict,created):
    if not re.fullmatch(r'[1-9]\d{0,19}',str(identity or '')) or verdict not in {'AC','WA','CE','RE','TLE','MLE','OLE'}:return None
    stamp=utc(created)
    if not stamp or dt.datetime.fromisoformat(stamp)>dt.datetime.now(dt.timezone.utc)+dt.timedelta(minutes=5):return None
    return {'platform':platform,'owner':str(owner),'submissionId':str(identity),'url':url,
            'verdict':verdict,'acceptedAt':stamp,'status':'finished','message':'原站提交记录同步；未取得源码'}


def nowcoder_receipts(payload,owner,contest):
    if not isinstance(payload,dict) or payload.get('code')!=0:raise ValueError('牛客提交记录暂不可用')
    data=payload.get('data') or {}
    if not isinstance(data,dict) or not isinstance(data.get('submitDataList'),list):raise ValueError('牛客提交记录格式变化')
    problems={str(row.get('problemId')):str(row.get('index','')).upper() for row in data.get('problemData',[]) if isinstance(row,dict)}
    result=[]
    for group in data['submitDataList']:
        if not isinstance(group,dict) or str((group.get('basicInfo') or {}).get('contestId'))!=str(contest):continue
        if any(str(row.get('uid'))==owner and row.get('team') for row in group.get('signUpUsers',[]) if isinstance(row,dict)):continue
        for row in group.get('submissions',[]):
            if not isinstance(row,dict) or str(row.get('uid'))!=owner:continue
            index=problems.get(str(row.get('problemId')))
            if not index or not re.fullmatch(r'[A-Z]\d?',index):continue
            verdict={3:'RE',4:'WA',5:'AC',6:'TLE',7:'MLE',10:'OLE',12:'CE',13:'WA',15:'RE',16:'RE',21:'RE'}.get(row.get('status'))
            if verdict=='AC' and isinstance(row.get('rightCaseRate'),(int,float)) and row['rightCaseRate']<1:continue
            value=receipt('牛客',owner,row.get('submissionId'),f'https://ac.nowcoder.com/acm/contest/{contest}/{index}',verdict,row.get('submitTime'))
            if value:result.append(value)
    return result


def atcoder_receipts(payload,owner):
    if not isinstance(payload,list):raise ValueError('AtCoder 提交记录暂不可用')
    result=[]
    for row in payload:
        if not isinstance(row,dict) or str(row.get('user_id','')).casefold()!=owner.casefold():continue
        contest,task=row.get('contest_id'),row.get('problem_id')
        if not re.fullmatch(r'[\w-]{1,100}',str(contest or '')) or not re.fullmatch(r'[\w-]{1,100}',str(task or '')):continue
        value=receipt('AtCoder',owner,row.get('id'),f'https://atcoder.jp/contests/{contest}/tasks/{task}',row.get('result'),row.get('epoch_second'))
        if value:result.append(value)
    return result


def luogu_receipts(payload,owner):
    data=lg_data(payload)
    records=data.get('records') or {}
    rows=records.get('result',[]) if isinstance(records,dict) else records
    if not isinstance(rows,list):raise ValueError('洛谷提交记录格式变化')
    result=[]
    for row in rows:
        if not isinstance(row,dict) or str((row.get('user') or {}).get('uid'))!=owner:continue
        pid=(row.get('problem') or {}).get('pid')
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,40}',str(pid or '')):continue
        value=receipt('洛谷',owner,row.get('id'),f'https://www.luogu.com.cn/problem/{pid}',LUOGU_VERDICTS.get(row.get('status')),row.get('submitTime'))
        if value:result.append(value)
    return result


class PublicReceiptSource:
    def __init__(self,client):self.client=client

    def _read(self,url,owner,parse,headers=None):
        # Production caches only normalized owner records, not other users on
        # the public standings board. Fixture clients can supply ordinary JSON.
        method=getattr(self.client,'owner_json',None)
        return method(url,owner,parse,headers=headers) if method else parse(self.client.json(url,headers=headers) if headers else self.client.json(url))

    def fetch(self,platform,owner,rows):
        if platform=='nowcoder':
            contests={}
            for row in rows:
                match=re.fullmatch(r'https://ac\.nowcoder\.com/acm/contest/(\d+)/[A-Za-z]\d?',str(row.get('url','')).split('?')[0])
                if match and not row.get('catalogHidden'):
                    contests[match[1]]=max(contests.get(match[1],''),str(row.get('endedAt') or row.get('contestDate') or row.get('addedAt') or ''))
            selected=sorted(contests,key=lambda cid:(contests[cid],int(cid)),reverse=True)[:8]
            result=[]
            for contest in selected:
                url='https://ac.nowcoder.com/acm/contest/rank/submit-list?'+urlencode({'currentContestId':contest,'contestList':contest,'rankScope':'ALL'})
                result.extend(self._read(url,owner,lambda value:nowcoder_receipts(value,owner,contest)))
            return result
        if platform=='atcoder':
            # Start with recent activity. Starting at epoch zero would keep
            # returning the first lifetime submissions of experienced users.
            cursor=int((dt.datetime.now(dt.timezone.utc)-dt.timedelta(days=30)).timestamp());result=[];seen=set()
            for _ in range(6):
                url='https://kenkoooo.com/atcoder/atcoder-api/v3/user/submissions?user='+quote(owner,safe='')+'&from_second='+str(cursor)
                payload=self.client.json(url)
                result.extend(row for row in atcoder_receipts(payload,owner) if row['submissionId'] not in seen)
                seen.update(row['submissionId'] for row in result)
                if len(payload)<500:break
                latest=max((row.get('epoch_second',0) for row in payload if isinstance(row,dict) and type(row.get('epoch_second')) is int),default=cursor)
                if latest<=cursor:break
                cursor=latest
            return result
        if platform=='luogu':
            result=[]
            for page in range(1,4):
                url='https://www.luogu.com.cn/record/list?'+urlencode({'user':owner,'page':page})
                values=self._read(url,owner,lambda value:luogu_receipts(value,owner),headers={'x-lentille-request':'content-only'})
                result.extend(values)
                if len(values)<20:break
            return result
        return []
