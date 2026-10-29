"""Merge only authored, verified route entries into the public seed.

Both variants of each method are required. Existing reference programs and
figures are preserved, and every unrelated public row is compared verbatim.
Personal databases and the live installation are never opened here.
"""
from collections import defaultdict
from copy import deepcopy
import datetime as dt
import json
from pathlib import Path
import re
import shutil
import sys

from core7_authoring import ROOT, OUT, CONTENT, source_hash, load_all, lesson_data


def read(path):return json.loads(path.read_text('utf-8'))
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def programs(text):return re.findall(r'^```cpp\s*\n(.*?)^```',text,re.S|re.M)


def prepare():
    source=ROOT/'data/library'
    names=['solutions','detailed_solutions','solution_methods','lectures','links','statements','meta']
    before={name:read(source/(name+'.json')) for name in names}
    result=deepcopy(before)
    index={name:{r['problem_id']:r for r in result[name]} for name in ['solutions','detailed_solutions','solution_methods','statements']}
    verification={(r['pid'],r['method']):r for r in read(OUT/'verification.json')}
    correction_path=CONTENT/'corrections.json'
    corrections={r['problemId']:r for r in read(correction_path)} if correction_path.exists() else {}
    authored=read(OUT/'authored.json')
    grouped=defaultdict(list)
    for entry in authored:
        key=(entry['pid'],entry['method']);evidence=verification[key]
        assert evidence['passed'] and evidence['programSha256']==entry['programSha256'],key
        assert set(entry['variants'])=={'default','detailed'},key
        first,second=entry['variants']['default'],entry['variants']['detailed']
        assert first['markdown']!=second['markdown'],key
        assert programs(first['markdown'])==programs(second['markdown']) and len(programs(first['markdown']))==1,key
        assert source_hash(programs(first['markdown'])[0])==entry['programSha256'],key
        grouped[entry['problemId']].append(entry)
    for identity,methods in grouped.items():
        primary=methods[0]
        for table,variant in [('solutions','default'),('detailed_solutions','detailed')]:
            article=deepcopy(primary['variants'][variant])
            if identity in index[table]:
                previous=index[table][identity]
                if programs(previous['markdown'])!=programs(article['markdown']):
                    old=programs(previous['markdown']);fix=corrections.get(identity)
                    assert fix and len(old)==1 and source_hash(old[0])==fix['previousProgramSha256'],identity
                    assert fix['reproductions'] and all(r['observed']!=r['expected'] for r in fix['reproductions']),identity
                for key,value in previous['images'].items():assert article['images'].get(key)==value,(identity,key)
                previous.update(article)
            else:
                row={'problem_id':identity,**article,'source_path':f'core7-editorials/{primary["pid"]}/{primary["method"]}/{variant}.md'}
                result[table].append(row);index[table][identity]=row
        catalog=[]
        for method in methods:
            catalog.append({'id':method['method'],'title':method['title'],'tags':method['tags'],
                'lectureIds':['lecture:foundation-'+name for name in method['lessons']],
                **method['variants']['default'],'detailedSolution':method['variants']['detailed'],
                'validation':{'programSha256':method['programSha256'],'officialSubmissionsSent':0}})
        if identity in index['solution_methods']:
            old=index['solution_methods'][identity]['content']
            by_id={m['id']:m for m in catalog}
            for method in old.get('methods',[]):
                if method['id'] not in by_id:catalog.append(method)
        content={'primaryMethod':primary['method'],'methods':catalog}
        row={'problem_id':identity,'content':content}
        if identity in index['solution_methods']:index['solution_methods'][identity].update(row)
        else:result['solution_methods'].append(row)
        if identity not in index['statements']:
            statement=read(OUT/'statements'/('luogu-training-'+primary['pid']+'.json'))
            result['statements'].append({'problem_id':identity,'content':statement})

    sources,inline=lesson_data()
    needed=defaultdict(set)
    for method in authored:
        for name in method['lessons']:needed[name].add(method['problemId'])
    existing_lectures={r['id']:r for r in result['lectures']}
    linked={(r['problem_id'],r['lecture_id']) for r in result['links']}
    for name,identities in needed.items():
        key='lecture:foundation-'+name;lesson=sources[name]
        if key in existing_lectures:
            content=existing_lectures[key]['content']
            content['sourceProblemIds']=sorted(set(content.get('sourceProblemIds',[]))|identities)
            if content.get('editorialVersion')=='2026-10-30-core7':
                body=lesson['body'];digest=source_hash(body)
                content.update(markdown=body,images=lesson['images'],sourceMarkdown='# '+lesson['title']+'\n\n'+body,
                               sourceHash=digest,originalSourceHash=digest)
        else:
            title=lesson['title'];body=lesson['body'];digest=source_hash(body)
            content={'id':key,'available':True,'conceptSource':'independent-foundation','curationVersion':'lectures-v1.1',
                'title':'从零讲：'+title,'displayTitle':title,'concept':title,'topic':title,'knowledgeName':title.split('：')[0],
                'markdown':body,'images':lesson['images'],'sourceMarkdown':'# '+title+'\n\n'+body,
                'sourcePath':'docs/foundations/'+name+'.md','sourceTitle':'独立基础课','sourceProblemIds':sorted(identities),
                'sourceHash':digest,'originalSourceHash':digest,'originalTitle':title,'originalConcept':title,
                'category':'语言基础','categories':['语言基础'],'catalogTags':[],'tags':[],'sourceTags':[],
                'editorialVersion':'2026-10-30-core7','excerpt':re.sub(r'[`$]','',body.split('\n\n')[0]),
                'quality':{'normalized':True,'supplemented':True,'sourceAlgorithmReverified':False}}
            result['lectures'].append({'id':key,'content':content})
        for identity in sorted(identities):
            if (identity,key) in linked:continue
            result['links'].append({'problem_id':identity,'lecture_id':key,'kind':'own','position':sum(p==identity for p,l in linked)})
            linked.add((identity,key))
    result['meta']['revision']=str(int(result['meta'].get('revision','0'))+1)
    result['meta']['core7EditorialRevision']='2026-10-30-method-variants-v1'
    if isinstance(result['meta'].get('lectureAudit'),dict):
        result['meta']['lectureAudit']['count']=len(result['lectures'])
    touched=set(grouped)
    for table in ['solutions','detailed_solutions','solution_methods','statements']:
        after={r['problem_id']:r for r in result[table]}
        for row in before[table]:
            if row['problem_id'] not in touched:assert after[row['problem_id']]==row,(table,row['problem_id'])
    report={'problems':len(grouped),'methods':len(authored),'articles':len(authored)*2,
            'before':{n:len(before[n]) for n in names if n!='meta'},'after':{n:len(result[n]) for n in names if n!='meta'},
            'unrelatedArticlesPreserved':True,'verifiedBaselineProgramsPreserved':True,
            'documentedBoundaryCorrections':sorted(corrections),'officialSubmissionsSent':0,
            'personalDatabasesOpened':False,'remainingRouteProblems':len(read(OUT/'scope.json'))-len(grouped)}
    return before,result,report


def main():
    apply='--apply' in sys.argv
    before,result,report=prepare()
    if apply:
        folder=OUT/'before/data-library';folder.mkdir(parents=True,exist_ok=True)
        for name,value in result.items():
            target=ROOT/'data/library'/(name+'.json')
            assert read(target)==before[name],'Concurrent source edit: '+name
            if not(folder/target.name).exists():shutil.copy2(target,folder/target.name)
            dump(target,value)
    report['applied']=apply
    dump(OUT/'import-report.json',report)
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
