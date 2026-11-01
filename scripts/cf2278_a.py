"""Append A as a default-only warm-up while preserving the six existing tasks."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from cf2278_programs import ROOT, CONTENT, ARCHIVE, put
from cf2278_prepare import Retained, statement
from cf2278_translate import translate, bundled_translation, TRANSLATION_FORMAT
import cf2278_stage as stage

OUT=ROOT/'.backups/div3-1131-a/final'
IDENTITY='remote:codeforces:2278::A'

def dump(path,value):put(path,json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
def load(path):return json.loads(path.read_text('utf8'))

def prepare():
    rows=load(CONTENT/'problems.json')
    original=next((x for x in rows if x['id']==IDENTITY),None)
    if original is not None:return
    encoded=deepcopy(rows[0]['encoded'])
    url='https://codeforces.com/contest/2278/problem/A'
    roster=load(CONTENT/'official-roster.json')
    official=next(x for x in roster['problems'] if x['index']=='A').get('rating')
    encoded.update(id=IDENTITY,problem='A',title='Fraction and Six',originalTitle='Fraction and Six',url=url,
        knowledge='模拟',tags=['模拟'],difficulty=official if official is not None else 800,
        officialRating=official,difficultyEstimated=official is None,difficultyBand=[800,1000],
        detailedSolutionAvailable=False,editorialVariants=['default'],
        difficultyEvidence=[url,'https://codeforces.com/api/contest.standings?contestId=2278',
            '分子与分母的二十六类字符频数作差，匹配 six；线性扫描，无需处理顺序。',
            '官方未定级，800 为独立复核估分。'],metadataVersion='2026-11-02-div3-1131-a')
    raw={'_id':IDENTITY,'场次':'Div.3 1131','题号':'A','题名':'Fraction and Six','知识点':'模拟',
         '难度':str(encoded['difficulty']),'状态':'未做','日期':''}
    rows.append({'id':IDENTITY,'url':url,'raw':raw,'encoded':encoded});dump(CONTENT/'problems.json',rows)
    page=(ARCHIVE/'_work/raw/A.html').read_text('utf8')
    value=statement(Retained(page,url),IDENTITY,'Fraction and Six',url)
    assert value['integrity']['status']=='complete' and len(value['samples'])==1
    value['sourceSnapshotSha256']=hashlib.sha256(page.encode()).hexdigest()
    value['translation']={'kind':'bundled','provider':'ToBe 中文题面复核','format':TRANSLATION_FORMAT,
        'sourceHash':hashlib.sha256(value['markdown'].encode()).hexdigest(),'sourceLanguage':'en','targetLanguage':'zh-CN',
        'markdown':translate(value['markdown'],'A'),'notice':'中文译文；公式、数值、输入输出与样例保留原题。'}
    assert bundled_translation(value)
    dump(CONTENT/'statements/A.json',value)
    statements=load(CONTENT/'statements.json');statements.append({'problem_id':IDENTITY,'content':value});dump(CONTENT/'statements.json',statements)
    methods=load(CONTENT/'solution_methods.json')
    methods.append({'problem_id':IDENTITY,'content':{'primaryMethod':'main','methods':[{'id':'main','title':'主解法','legacy':True,
        'tags':['模拟'],'lectureIds':[],'validation':{'programSha256':hashlib.sha256((CONTENT/'programs/A/a.cpp').read_bytes()).hexdigest(),'officialSubmissionsSent':0}}]}})
    dump(CONTENT/'solution_methods.json',methods)
    scope=load(CONTENT/'scope.json');scope.update(letters='ABCDEFG',problems=7,articles=13,defaultArticles=7,detailedArticles=6,excluded=[],defaultOnly=['A'])
    scope['warmupPolicy']='签到题也收录，仅提供默认版；保留既有详细版。用户于 2026-11-02 明确修改。'
    dump(CONTENT/'scope.json',scope)

def main():
    OUT.mkdir(parents=True,exist_ok=True);prepare()
    stage.OUT=OUT;stage.shared.OUT=OUT
    packet=stage.additions();lib=stage.seed(packet)
    assert len(packet['problems'])==7 and len(packet['solutions'])==7 and len(packet['detailed_solutions'])==6
    stage.shared.upgrade_check(packet,lib);stage.shared.export_readers(lib,packet);stage.shared.text_source(packet,replace_ids={IDENTITY})
    assert lib.solution(IDENTITY,'detailed') is None
    dump(OUT/'stage-report.json',{'passed':True,'problems':7,'defaultArticles':7,'detailedArticles':6,
        'aDefaultOnly':True,'existingRowsPreserved':True,'personalDatabasesModified':False})
    print('A default-only article staged; all six existing task variants preserved.')

if __name__=='__main__':main()
