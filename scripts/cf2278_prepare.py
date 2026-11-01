"""Retain first-party statements and separate official ratings from reviews."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import urllib.request
from urllib.parse import urlsplit
from cf2278_programs import ROOT,CONTENT,ARCHIVE,OUT,LETTERS,META

sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from public_platforms import statement
import fetch_problem as adapter

REASONS={
'B':'选择出现最多的类别并固定克制手势，按频数证明对所有排列不败，O(x+y+z)。',
'C':'区分内部质量守恒和端点流失，证明内部活跃传播与端点滚动的最优损失，O(n)。',
'D':'将锁定操作与整体平移联系到中位数距离和，再证明极差下界同时可达，O(n log n)。',
'E':'交错变号把操作转成相邻交换，按正负位置分配最大最小元素，O(n log n)。',
'F':'相邻余数和的额外损失至多一，分类化为到二的前缀，前缀和优化 DP，O(nm)。',
'G':'根路径的二进制加法、同深度全局位与分支进位、逐位最小性，迭代树遍历 O(n)。',
}

def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8',newline='\n')

class Retained:
    def __init__(self,page,url):self.page=page;self.url=url
    def text(self,url,**kwargs):
        assert url.split('?')[0]==self.url
        return self.page
    def bytes(self,url,**kwargs):
        host=urlsplit(url).hostname
        if host not in {'espresso.codeforces.com','codeforces.com'} or not url.startswith('https://'):raise ValueError('Unexpected original attachment source')
        cache=OUT/'resources'/(hashlib.sha256(url.encode()).hexdigest()+'.bin');cache.parent.mkdir(parents=True,exist_ok=True)
        if not cache.exists():
            result=subprocess.run([adapter.CURL,'-fsSL','-A',adapter.UA,url,'-o',str(cache)],capture_output=True,timeout=45)
            if result.returncode:raise ValueError('Original attachment download failed')
        data=cache.read_bytes()
        if len(data)>32*1024*1024:raise ValueError('Oversized original resource')
        return data

def main():
    official=json.loads((ARCHIVE/'_work/official-roster.json').read_text('utf8'))
    dump(CONTENT/'official-roster.json',official)
    ratings={p['index']:p.get('rating') for p in official['problems']}
    date=dt.datetime.fromtimestamp(official['contest']['startTimeSeconds'],dt.timezone.utc)
    end=date+dt.timedelta(seconds=official['contest']['durationSeconds'])
    problems=[];statements=[];methods=[];links=[]
    for letter in LETTERS:
        title,knowledge,estimate,lessons=META[letter];identity='remote:codeforces:2278::'+letter;url='https://codeforces.com/contest/2278/problem/'+letter
        page=(ARCHIVE/'_work/raw'/(letter+'.html')).read_text('utf8')
        value=statement(Retained(page,url),identity,title,url)
        assert value['integrity']['status']=='complete' and value['samples'],(letter,value.get('resourceIssues'))
        value['sourceSnapshotSha256']=hashlib.sha256(page.encode()).hexdigest()
        dump(CONTENT/'statements'/(letter+'.json'),value);statements.append({'problem_id':identity,'content':value})
        rating=ratings[letter]
        encoded={'id':identity,'contest':'Div.3 1131','contestId':'2278','contestFullName':official['contest']['name'],
          'platform':'Codeforces','series':'Div.3','contestFamily':'Div.3','problem':letter,'title':title,'originalTitle':title,'url':url,
          'knowledge':knowledge,'tags':[x.strip() for x in knowledge.replace('[主]','').split('+')],
          'difficulty':rating if rating is not None else estimate,'officialRating':rating,'difficultyEstimated':rating is None,
          'difficultySource':'Codeforces 官方 rating' if rating is not None else 'ToBe 题面与算法复核估算（官方未定级）',
          'difficultyConfidence':'HIGH' if rating is not None else 'MEDIUM',
          'difficultyBand':[rating,rating] if rating is not None else [max(800,estimate-200),estimate+200],
          'difficultyEvidence':[url,'https://codeforces.com/api/contest.standings?contestId=2278','https://codeforces.com/blog/entry/158300',REASONS[letter],
            '未公布的官方 rating 保留为空；人工复核估分独立标注，不冒充正式评分。'],
          'metadataVersion':'2026-11-02-div3-1131','source':'bundled','status':'未做','date':'','solutionAvailable':True,
          'detailedSolutionAvailable':True,'solutionState':'available','statementAvailable':True,'contestProblemCount':7,'contestRoster':True,
          'collectionSource':'https://codeforces.com/contest/2278','startedAt':date.isoformat(),'endedAt':end.isoformat(),
          'contestDate':date.isoformat(),'contestDateSource':'Codeforces 官方比赛时间','eventYear':date.year}
        assert encoded['difficulty']<=2300
        raw={'_id':identity,'场次':'Div.3 1131','题号':letter,'题名':title,'知识点':knowledge,'难度':str(encoded['difficulty']),'状态':'未做','日期':''}
        problems.append({'id':identity,'url':url,'raw':raw,'encoded':encoded})
        methods.append({'problem_id':identity,'content':{'primaryMethod':'main','methods':[{'id':'main','title':'主解法','legacy':True,
           'tags':encoded['tags'],'lectureIds':['lecture:foundation-'+s for s in lessons],
           'validation':{'programSha256':hashlib.sha256((CONTENT/'programs'/letter/(letter.lower()+'.cpp')).read_bytes()).hexdigest(),'officialSubmissionsSent':0}}]}})
        for index,name in enumerate(lessons):links.append({'problem_id':identity,'lecture_id':'lecture:foundation-'+name,'kind':'own','position':index})
    for name,rows in [('problems',problems),('statements',statements),('solution_methods',methods),('links',links)]:dump(CONTENT/(name+'.json'),rows)
    dump(CONTENT/'scope.json',{'contest':'Div.3 1131','contestId':2278,'letters':LETTERS,'problems':6,'articles':12,
      'officialRatingPublished':any(ratings[l] is not None for l in LETTERS),'excluded':[{'letter':'A','reason':'签到题'}],
      'statementSemanticNote':{'C':'原文终止句有歧义，参考程序与正文采用官方题解及样例的“只剩一颗即结束”口径。'},
      'verificationCorrections':[{'letter':'G','inputTarget':'00010','initialExpected':'2','correctedExpected':'-1',
          'reason':'独立逐脉冲模拟证明同层冲突；保留原输入，另加可达目标00110期望2，参考程序未改。'}]})
    print('Prepared six complete original statements, including the original G illustration.')

if __name__=='__main__':main()
