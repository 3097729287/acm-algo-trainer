"""Bounded anonymous discovery of newly published, post-2016 XCPC Gyms."""
import datetime as dt
from html.parser import HTMLParser
import re


class Roster(HTMLParser):
    def __init__(self, identity):
        super().__init__()
        self.identity=str(identity);self.current=None;self.content=[];self.tasks={}

    def handle_starttag(self,tag,attrs):
        if tag!='a':return
        href=dict(attrs).get('href','')
        match=re.fullmatch(r'/gym/'+re.escape(self.identity)+r'/problem/([A-Z]\d?)',href)
        if match:self.current=match[1];self.content=[]

    def handle_data(self,text):
        if self.current:self.content.append(text)

    def handle_endtag(self,tag):
        if tag!='a' or self.current is None:return
        title=' '.join(''.join(self.content).split())
        if title and title!=self.current:self.tasks[self.current]=title
        self.current=None


def historical(contest,now):
    name=contest.get('name','')
    year=re.search(r'20\d{2}',name)
    if not year or not 2017<=int(year[0])<=now.year or contest.get('phase')!='FINISHED':return False
    if not re.search(r'ICPC|CCPC',name,re.I):return False
    if re.search(r'ICPC[- ]style|ICPC format|Team (?:Selection|Formation)|Selection Contest|Internal Round|Mock Contest|ICPC.?de.?Tryst|Columbia University Local|\+ Some Problems|\+ GCJ',name,re.I):return False
    start=contest.get('startTimeSeconds');duration=contest.get('durationSeconds')
    return not (type(start) is int and type(duration) is int and start+duration>now.timestamp())


def discover_gyms(client,now,policy,limit=8):
    import public_platforms as P
    contests=P.cf_result(client,'contest.list?gym=true')
    known={str(value) for value in policy.get('knownGymContests',[])}|set(policy.get('excludedGymContests',[]))
    candidates=sorted((c for c in contests if str(c['id']) not in known and historical(c,now)),key=lambda c:c['id'],reverse=True)[:limit]
    rows=[];pending=[]
    for contest in candidates:
        cid=contest['id']
        try:
            parser=Roster(cid);parser.feed(client.text(f'https://codeforces.com/gym/{cid}'))
            if not parser.tasks:raise ValueError('公开题单暂不可读取')
            year=int(re.search(r'20\d{2}',contest['name'])[0])
            for index,title in parser.tasks.items():
                value=P.row('codeforces',{'id':cid,'name':contest['name'],'series':'XCPC'},index,title,f'https://codeforces.com/gym/{cid}/problem/{index}',None,'Gym 无官方单题 rating')
                value.update(source='xcpc-codeforces',contestFullName=contest['name'],contestPhase='FINISHED',
                             contestRoster=True,contestProblemCount=len(parser.tasks),xcpcYear=year,examYear=year,eventYear=year,
                             contestDifficulty=contest.get('difficulty'),contestDifficultySource='Codeforces Gym 公开整场难度（1–5 级），不是单题 rating',
                             collectionSource=f'https://codeforces.com/gym/{cid}',mirrorStartedAt=P.utc(contest.get('startTimeSeconds')),
                             metadataVersion='1.0.18',contestDatePrecision='year',contestDateSource='赛事原名年份；具体日期待核实')
                rows.append(value)
        except (OSError,ValueError,RuntimeError) as error:
            pending.append({'contestId':str(cid),'reason':str(error)[:150]})
    return rows,pending
