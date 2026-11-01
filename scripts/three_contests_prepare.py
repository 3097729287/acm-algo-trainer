"""Convert retained first-party pages into portable, validated library inputs."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.request
from urllib.parse import urlsplit
from three_contests_programs import ROOT, CONTENT, ARCHIVE, ROUNDS
from three_contests_articles import META

sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from public_platforms import statement
from difficulty import normalize_practice_difficulty

WHITE={
 'B':('奶龙的奇妙公式','结论与计数',900,['integer']),
 'C':('小芳的比赛','贪心[主] + 堆',1600,['heap','integer']),
 'D':('小苯的纸牌屋','枚举[主] + 前缀和',1400,['prefix','integer']),
 'E':('小芳的睡眠排序','结论与计数',1700,['integer','vector']),
 'F':('小芳的最小生成树','构造[主] + 生成树',2200,['vector','iterators']),
}
REASONS={
 ('week168','B'):'扫描网格并取四条边的并集，需正确处理单行单列与重复角，O(nm)。',
 ('week168','C'):'前后缀均包含当前位置，使用差的整除判定处理负数同余，O(n)。',
 ('week168','D'):'环上按原格数走步，再用后继并查集跳过占用位置，路径压缩及哨兵环绕。',
 ('week168','E'):'两前缀及最后来源堆的可达性 DP，O(nm)，价值由前缀和固定。',
 ('week168','F'):'嵌套安全集合的部分匹配计数 DP，再以三个计数消去零、一位喝奶者，O(n²)。',
 ('week168','G'):'证明前缀内部强制切段的两个计数条件充分必要，线性枚举前缀分配。',
 ('white139','B'):'逐对表达式恒等于右项，按右端点计数并注意六十四位整数。',
 ('white139','C'):'前缀比分约束转成最少改判次数，最小堆贪心及最终胜负约束，O(n log n)。',
 ('white139','D'):'从题目结构得到可选长度，再用前缀和枚举合法区间，O(n log n)。',
 ('white139','E'):'分段统计贡献并证明重排计数，需区分相同值和相同位置。',
 ('white139','F'):'利用相邻边替代约束构造生成树，处理等权、规范化点对、去重与补边。',
}

def dump(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf8')

class RetainedPage:
    def __init__(self,page,url):self.page=page;self.url=url
    def text(self,url,**kwargs):
        assert url.split('?')[0]==self.url
        return self.page
    def bytes(self,url,**kwargs):
        parsed=urlsplit(url)
        if parsed.scheme!='https' or parsed.hostname not in {'uploadfiles.nowcoder.com','atcoder.jp','img.atcoder.jp'}:
            raise ValueError('Unexpected statement resource host: '+url)
        with urllib.request.urlopen(url,timeout=35) as reply:return reply.read(32*1024*1024+1)

def main():
    model_path=CONTENT/'atcoder-model-evidence.json'
    if model_path.exists():models=json.loads(model_path.read_text('utf8'))['models']
    else:
        url='https://kenkoooo.com/atcoder/resources/problem-models.json'
        with urllib.request.urlopen(url,timeout=40) as reply:data=json.load(reply)
        models={k:v for k,v in data.items() if k.startswith('abc482_')}
        dump(model_path,{'url':url,'retrievedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'models':models,'kind':'third-party statistical estimate, not AtCoder official difficulty'})
    all_problems=[];statements=[];methods=[];links=[]
    for key,(platform,series,number,contest_url,letters) in ROUNDS.items():
        archive=ARCHIVE/platform/series/number
        for letter in letters:
            title,knowledge,rating,lessons=(WHITE[letter] if key=='white139' else META[key,letter])
            site='atcoder' if key=='abc482' else 'nowcoder'
            cid='abc482' if site=='atcoder' else contest_url.rsplit('/',1)[-1]
            identity=f'remote:{site}:{cid}::{letter}'
            url=contest_url+('/tasks/abc482_'+letter.lower() if site=='atcoder' else '/'+letter)
            page=(archive/'_work/raw'/(letter+'.html')).read_text('utf8')
            original=statement(RetainedPage(page,url),identity,title,url)
            if site=='nowcoder':
                match=re.search(r'时间限制：C/C\+\+/Rust/Pascal\s*([0-9.]+)秒',page)
                memory=re.search(r'空间限制：C/C\+\+/Rust/Pascal\s*(\d+)\s*M',page)
                if match:original['limits']['timeMs']=int(float(match[1])*1000)
                if memory:original['limits']['memoryMb']=int(memory[1])
            assert original['integrity']['status']=='complete',(identity,original.get('resourceIssues'))
            assert original['samples'],identity
            original['sourceSnapshotSha256']=hashlib.sha256(page.encode()).hexdigest()
            dump(CONTENT/key/'statements'/(letter+'.json'),original)
            statements.append({'problem_id':identity,'content':original})
            encoded={'id':identity,'contest':series+' '+number,'contestId':cid,'problem':letter,'title':title,
                'originalTitle':title,'url':url,'platform':platform,'series':series,'contestFamily':series,
                'difficulty':rating,'difficultyEstimated':True,'difficultyConfidence':'MEDIUM',
                'difficultySource':'ToBe 题面与算法复核估算','difficultyBand':[max(800,rating-200),rating+200],
                'difficultyEvidence':[url,REASONS.get((key,letter),''),'训练参考估计，非原站官方 rating。'],
                'knowledge':knowledge,'tags':[t.strip() for t in knowledge.replace('[主]','').split('+')],
                'status':'未做','date':'','source':'bundled','solutionAvailable':True,'detailedSolutionAvailable':True,
                'solutionState':'available','statementAvailable':True,'contestProblemCount':7 if key!='white139' else 6,
                'collectionSource':contest_url,'contestRoster':True,'metadataVersion':'2026-11-02-three-contests'}
            if site=='atcoder':
                raw=models['abc482_'+letter.lower()]['difficulty']
                converted=max(800,int((.67*raw+650)/100+.5)*100)
                assert converted==rating,(letter,raw,converted,rating)
                encoded.update(difficultySource='CF-EQ v1.0 / AtCoder Problems 第三方模型',
                    nativeDifficulty=raw,difficultyConfidence='MEDIUM',difficultyBand=[max(800,rating-100),rating+100],
                    difficultyEvidence=[url,'https://kenkoooo.com/atcoder/resources/problem-models.json',
                        f'原模型 {raw}；max(800, round100(0.67 × 模型 + 650)) = {rating}；非官方评分。'])
            date_evidence=CONTENT/'contest-date-evidence.json'
            if date_evidence.exists():
                encoded.update(json.loads(date_evidence.read_text('utf8'))['records'].get(identity,{}))
            encoded=normalize_practice_difficulty(encoded)
            raw={'_id':identity,'场次':series+' '+number,'题号':letter,'题名':title,'知识点':knowledge,'难度':str(rating),'状态':'未做','日期':''}
            all_problems.append({'id':identity,'url':url,'raw':raw,'encoded':encoded})
            methods.append({'problem_id':identity,'content':{'primaryMethod':'main','methods':[{'id':'main','title':'主解法',
                'legacy':True,'tags':encoded['tags'],'lectureIds':['lecture:foundation-'+x for x in lessons],
                'validation':{'officialSubmissionsSent':0,'source':'programs/'+letter+'/'+letter.lower()+'.cpp',
                    'programSha256':hashlib.sha256((CONTENT/key/'programs'/letter/(letter.lower()+'.cpp')).read_bytes()).hexdigest()}}]}})
            for index,name in enumerate(lessons):links.append({'problem_id':identity,'lecture_id':'lecture:foundation-'+name,'kind':'own','position':index})
    for name,rows in [('problems',all_problems),('statements',statements),('solution_methods',methods),('links',links)]:dump(CONTENT/(name+'.json'),rows)
    dump(CONTENT/'scope.json',{'contests':3,'problems':16,'articles':32,'scope':'B–G / B–F / B–F',
      'excluded':[{'contest':'周赛 168','letter':'A','reason':'签到题'}, {'contest':'ABC 482','letter':'A','reason':'签到题'},
        {'contest':'小白月赛 139','letter':'A','reason':'签到题'}, {'contest':'ABC 482','letter':'G','reason':'CF-EQ 2500，高于 ≤2300 补写上限','nativeModel':models['abc482_g']['difficulty']}],
      'white139':'Reused the authored manuscripts, programs and figures; no replacement algorithm.',
      'officialSubmissionsSent':0,'publicDeployment':False})
    print('Prepared 16 complete first-party statements and evidence-labelled problem records.')

if __name__=='__main__':main()
