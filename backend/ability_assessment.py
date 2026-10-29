"""Conservative, auditable practice ability; no XP or account writes.

Rasch likelihood and prior are shared with knowledge mastery. Practice is
self-selected, so the displayed lower estimate is bounded by a repeatedly
demonstrated difficulty; it is not an official contest rating.
"""
from collections import defaultdict
import datetime as dt
import math
from mastery_scale import ability_posterior
from progression import parse_time
from submission_evidence import source_present

FAILURES={'WA','TLE','MLE','RE','OLE'}
MODEL={'version':2,'method':'rasch-practice-evidence-v2','window':60,
       'bandWidth':100,'bandWeightCap':8,'minimumSuccesses':5,
       'supportCount':5,'scoreQuantile':.1,'calibrated':False}

def _number(value):
    return type(value) in (int,float) and 0<value<=4000 and math.isfinite(value)

def _weight(value):
    return max(0,min(1,value)) if type(value) in (int,float) and math.isfinite(value) else 0

def _iso(value):
    return value.astimezone(dt.timezone.utc).isoformat(timespec='microseconds').replace('+00:00','Z')

def from_records(rows, records, now):
    """One first-learning episode per exact original, never one per retry."""
    from insights import canonical_url
    from rating_evidence import evidence as rating_evidence
    metadata={};aliases={}
    for row in rows:
        key=canonical_url(row.get('url')) or row['id']
        if key not in metadata or metadata[key].get('source')=='remote':metadata[key]=row
        for identity in [row['id'],*row.get('aliasIds',[])]:aliases[identity]=key
    grouped=defaultdict(list)
    for record in records:
        stamp=parse_time(record.get('submitted_at'));finished=parse_time(record.get('finished_at'))
        if (record.get('mode')!='submit' or record.get('scope')!='official'
            or record.get('verdict') not in FAILURES|{'AC'} or not stamp or not finished
            or not stamp<=finished<=now):continue
        key=aliases.get(record.get('problem_id'))
        if key:grouped[key].append(record)
    result=[]
    for key,receipts in grouped.items():
        independent=lambda r:('solution_seen' in r and r['solution_seen'] is not None
                              and not r['solution_seen'] and source_present(r))
        # Compare instants, not ISO text (offsets can spell the same instant
        # differently). Uncertain or assisted facts win an exact AC tie.
        receipts.sort(key=lambda r:(parse_time(r['submitted_at']),independent(r),r.get('id','')))
        first_ac=next((r for r in receipts if r['verdict']=='AC'),None)
        before=[r for r in receipts if first_ac is None or parse_time(r['submitted_at'])<=parse_time(first_ac['submitted_at'])]
        failures=[r for r in before if r['verdict'] in FAILURES and independent(r)]
        solved=bool(first_ac and independent(first_ac))
        if not solved and not failures:continue
        row=metadata[key];rating=rating_evidence(row)
        # A failed independent attempt followed by an assisted AC is still an
        # uncompleted independent attempt, not a credential for the solution.
        stamp=first_ac['submitted_at'] if solved else failures[-1]['submitted_at']
        result.append({'id':key,'solved':solved,'rated':rating['known'],
            'difficulty':rating['lower'] if solved else rating['upper'],
            'weight':rating['weight']/(math.sqrt(1+min(8,len(failures))) if solved else 1),
            'date':_iso(parse_time(stamp)),'failures':len(failures),'firstPass':solved and not failures,
            'kind':rating['kind'],'topics':sorted({path.split(' / ')[0] for path in row.get('knowledgeCategories',[]) if path}),
            'problemId':row['id'],'tags':row.get('tags',[]),'independentKnown':True,
            'timed':bool((first_ac if solved else failures[-1]).get('contest_id'))})
    return result

def from_successes(evidence, now):
    """Compatibility for normalized official facts; unknown remains unknown."""
    from insights import canonical_url
    first={};facts=[]
    for item in evidence:
        stamp=parse_time(item.get('acceptedAt'));key=item.get('key') or item.get('problemKey') or item.get('problemId')
        if not stamp or stamp>now or not isinstance(key,str) or not key.strip() or item.get('scope')!='official' or item.get('verdict','AC')!='AC':continue
        key=canonical_url(key) or key
        d=item.get('abilityDifficulty',item.get('difficulty'))
        qualified=item.get('independent') is True and item.get('independentKnown') is True and _number(d)
        facts.append((stamp,key,qualified,item))
    for stamp,key,qualified,item in sorted(facts,key=lambda x:x[:3]):
        if key in first:continue
        first[key]=None
        d=item.get('abilityDifficulty',item.get('difficulty'))
        if not qualified:continue
        kind=item.get('difficultyKind','official-cf')
        first[key]={'id':key,'difficulty':d,'rated':True,'solved':True,'date':_iso(stamp),
            'weight':1 if kind=='official-cf' else .25,'kind':kind,'failures':0,'firstPass':True,'topics':[]}
    return [item for item in first.values() if item]

def assess(evidence, now):
    # Window advances with actual new problems, not with idle calendar days.
    # Repeating a solved task cannot push old failures out of this window.
    valid=[]
    for item in evidence:
        stamp=parse_time(item.get('date'))
        if stamp and stamp<=now:valid.append((stamp,{**item,'date':_iso(stamp)}))
    unique={}
    for stamp,item in sorted(valid,key=lambda pair:(pair[0],pair[1]['id'],bool(pair[1].get('solved')),bool(pair[1].get('rated')))):
        unique.setdefault(item['id'],item)
    all_items=sorted(unique.values(),key=lambda x:(parse_time(x['date']),x['id']))
    rated_items=[item for item in all_items if item.get('rated') and _number(item.get('difficulty')) and _weight(item.get('weight',0))>0]
    # An unrated QOJ task cannot erase previous rating evidence simply by
    # consuming a window slot. Keep its real participation count separately.
    items=rated_items[-MODEL['window']:]
    known=items
    successes=[item for item in known if item.get('solved')]
    bands=defaultdict(float)
    for item in known:bands[int(item['difficulty']//MODEL['bandWidth'])]+=_weight(item.get('weight',0))
    for item in known:
        weight=_weight(item.get('weight',0))
        item['weight']=weight*min(1,MODEL['bandWeightCap']/bands[int(item['difficulty']//MODEL['bandWidth'])]) if weight else 0
    posterior=ability_posterior(known)
    qualified=len(successes)>=MODEL['minimumSuccesses']
    support=sorted((item['difficulty'] for item in successes),reverse=True)
    ceiling=support[MODEL['supportCount']-1] if qualified else None
    score=int(math.floor(min(posterior['lower'],ceiling)/10)*10) if qualified else None
    recent=[item for item in all_items if (now-parse_time(item['date'])).total_seconds()<=90*86400]
    topics=defaultdict(lambda:{'attempted':0,'independentSolved':0,'rated':0})
    for item in items:
        for name in item.get('topics',[]):
            topics[name]['attempted']+=1;topics[name]['independentSolved']+=int(bool(item.get('solved')));topics[name]['rated']+=int(bool(item.get('rated')))
    age=(now-parse_time(items[-1]['date'])).days if items else None
    interval=posterior['interval'] if posterior else None
    reference=[min(score,interval[0]),interval[1]] if qualified else interval
    effective=sum(item['weight'] for item in known)
    confidence='none' if not qualified else 'low' if effective<10 or interval[1]-interval[0]>600 or age>90 else 'medium' if effective<25 or interval[1]-interval[0]>350 else 'high'
    return {'abilityScore':score,'qualified':qualified,'abilityInterval':reference,'posteriorInterval':interval,
        'posteriorMedian':posterior['median'] if posterior else None,'supportCeiling':ceiling,
        'evidenceCount':len(successes),'attemptedCount':len(items),'lifetimeAttemptedCount':len(all_items),
        'unratedAttemptedCount':len(all_items)-len(rated_items),
        'ratedEvidenceCount':len(known),'effectiveEvidence':round(effective,3),'confidence':confidence,
        'topDifficulties':support[:5],'minimumEvidence':MODEL['minimumSuccesses'],
        'model':dict(MODEL),'topicEvidence':dict(topics),'lastEvidenceAt':items[-1]['date'] if items else None,
        'recentPerformance':{'days':90,'attempted':len(recent),'independentSolved':sum(bool(x.get('solved')) for x in recent),
           'firstPass':sum(bool(x.get('firstPass')) for x in recent),'lastEvidenceAgeDays':age,
           'timedAttempted':sum(bool(x.get('timed')) for x in recent),
           'timedSolved':sum(bool(x.get('timed')) and bool(x.get('solved')) for x in recent)},
        'evidence':[{'id':item['id'],'problemId':item.get('problemId'),'difficulty':item['difficulty'],
           'solved':item['solved'],'weight':round(item['weight'],6),'date':item['date'],
           'difficultyKind':item.get('kind'),'failures':item.get('failures',0)} for item in known],
        'estimated':True,'intervalKind':'supported-reference',
        'rules':'5 级解锁段位。能力分和知识点掌握度共用 Rasch 作答模型：同一原题只计一份首次学习证据，采用最近 60 道难度已知且权重有效的不同原题的独立正式作答；未知难度另计参与数，不挤掉有效证据。未独立完成的有效失败参与估计，重试成功降低权重，样例、编译错误、辅助 AC 不充当独立成功。CF 官方题权重为 1，跨平台估计采用保守区间和较低权重；同一整百难度层最多 8 份有效证据。显示后验 10% 分位数，且不超过至少 5 道独立成功支持的难度；同时给出 95% 模型区间、90 天全部不同原题的实际结果和专题证据。模型参数是公开工程约定，尚未经共同人群标定，不是 CF 官方 rating。经验和奖励不参与能力计算；不因缺勤直接扣能力分。'}
