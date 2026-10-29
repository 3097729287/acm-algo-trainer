"""List projection preserves real frontend filtering, labels and chronology."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from catalog_payload import catalogue_payload

ROOT=Path(__file__).resolve().parent.parent


def fixture():
    return {'rows':[
        {'id':'Div.2 1127::C','title':'Lavencia Oranges','contest':'Div.2 1127','problem':'C',
         'platform':'Codeforces','series':'Div.2','url':'https://codeforces.com/contest/2274/problem/C',
         'source':'archive','status':'未做','date':'','queue':None,'tags':['二分答案','构造'],
         'knowledge':'二分答案 + 构造','knowledgeCategories':['思维与策略'],'knowledgeReviewRequired':True,'difficulty':None,
         'difficultySource':'Codeforces 官方尚未评级','difficultyEstimated':False,'difficultyConfidence':'UNKNOWN',
         'difficultyEvidence':['https://codeforces.com/api/problemset.problems'], 'difficultyBand':None,
         'solutionAvailable':True,'solutionState':'available','contestDate':'2026-10-11T18:35:00Z',
         'startedAt':'2026-10-11T18:35:00Z','endedAt':'2026-10-11T20:35:00Z',
         'contestDateSource':'原站公开比赛时间','contestDatePrecision':'datetime',
         'contestFullName':'Codeforces Round 1127 (Div. 2)','contestProblemCount':6,
         'knowledgeAnalysis':{'evidence':[{'reason':'long reviewed derivation'}]},
         'sourceTags':['binary search'],'originalTitle':'Lavencia Oranges','metadataVersion':'1.0.20'},
        {'id':'gym::A','title':'XCPC fixture','contest':'ICPC 2026 南京区域赛','problem':'A','platform':'Codeforces',
         'series':'XCPC','source':'xcpc-codeforces','url':'https://codeforces.com/gym/100000/problem/A',
         'status':'未做','date':'','tags':[],'knowledge':'','knowledgeCategories':['图论'],'knowledgeReviewRequired':False,'difficulty':1800,
         'difficultyEstimated':True,'difficultyBand':[1600,2100],'difficultyConfidence':'LOW',
         'difficultySource':'训练参考估算','difficultyEvidence':['published public evidence'],
         'xcpcYear':2026,'eventYear':2026,'xcpcKind':'区域赛','xcpcPlace':'南京','contestVariant':'Gym 100000',
         'contestDifficulty':3,'contestDifficultySource':'CF Gym 公开整场难度','collectionNotice':'原赛公开题单',
         'contestDate':None,'contestDatePrecision':'year','contestProblemCount':12,
         'knowledgeAnalysis':{'evidence':['full evidence remains available from problem detail']}},
        {'id':'lanqiao::A','title':'B group fixture','contest':'蓝桥杯 2026 初赛','problem':'A','platform':'蓝桥杯',
         'series':'蓝桥杯 C/C++大学B','source':'lanqiao-history','status':'未做','date':'','tags':['模拟'],
         'knowledge':'模拟','knowledgeCategories':['基础技巧'],'difficulty':1000,'examYear':2026,'examStage':'初赛','examGroup':'C/C++大学B'},
        {'id':'hidden::A','title':'Retained history','contest':'教育赛 195','problem':'A','platform':'Codeforces',
         'series':'教育赛','source':'remote','status':'未做','date':'','tags':[],'knowledge':'','difficulty':None,
         'catalogHidden':True,'catalogNotice':'不在指定系列','catalogVisibilityPolicy':'authorized-content-v2'}],
        'revision':'catalog-revision','categories':[{'name':'构造','tags':['构造']}],
        'token':'fixture-token','today':'2026-10-15','statuses':['未做','独立AC']}


class CataloguePayloadTests(unittest.TestCase):
    def test_all_identities_order_visibility_and_display_evidence_are_preserved(self):
        original=fixture();before=copy.deepcopy(original);compact=catalogue_payload(original)
        self.assertEqual(original,before)
        self.assertEqual([row['id'] for row in compact['rows']],[row['id'] for row in original['rows']])
        for old,new in zip(original['rows'],compact['rows']):
            for key in ('id','title','url','contest','problem','tags','knowledge','knowledgeCategories','knowledgeReviewRequired','difficulty',
                        'difficultySource','difficultyBand','difficultyConfidence','difficultyEvidence','difficultyEstimated',
                        'catalogHidden','catalogNotice','contestDate','startedAt','endedAt','contestDatePrecision',
                        'eventYear','xcpcYear','xcpcKind','examYear','examStage','contestVariant','contestProblemCount',
                        'contestDifficulty','contestDifficultySource','solutionAvailable','collectionNotice'):
                if key in old:self.assertEqual(new[key],old[key],key)
            self.assertNotIn('knowledgeAnalysis',new)
            self.assertNotIn('sourceTags',new)
        for key in ('revision','categories','token','today','statuses'):self.assertEqual(compact[key],original[key])

    @unittest.skipUnless(shutil.which('node'),'Node is needed to execute the actual frontend models')
    def test_actual_frontend_filters_shelves_labels_and_date_order_are_equivalent(self):
        original=fixture();compact=catalogue_payload(original)
        with tempfile.TemporaryDirectory(prefix='tb-compact-catalogue-') as directory:
            root=Path(directory);data=root/'views.json'
            data.write_text(json.dumps({'original':original,'compact':compact},ensure_ascii=False),'utf8')
            script=root/'check.mjs'
            script.write_text('''
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { pathToFileURL } from 'node:url';
const base=process.argv[2], data=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
const load=path=>import(pathToFileURL(`${base}/frontend/src/${path}`));
const {filteredRows}=await load('models/model.js');
const {difficultyLabel,difficultyDescription,compareContestNewest}=await load('lib/practiceMetadata.js');
const {matchesShelf}=await load('lib/contestShelves.js');
const {knowledgeLabels}=await load('lib/knowledgeLabels.js');
const ids=rows=>rows.map(row=>row.id);
for (const options of [{query:'构造'},{query:'1127 C'},{platform:'Codeforces',min:1200,sort:'difficulty'},
                       {tags:['模拟']},{query:'未做'},{sort:'title',desc:true}]) {
  assert.deepEqual(ids(filteredRows(data.original.rows,options)),ids(filteredRows(data.compact.rows,options)));
}
for (let i=0;i<data.original.rows.length;i++) {
  const full=data.original.rows[i], compact=data.compact.rows[i];
  assert.equal(difficultyLabel(full),difficultyLabel(compact));
  assert.equal(difficultyDescription(full),difficultyDescription(compact));
  assert.deepEqual(knowledgeLabels(full),knowledgeLabels(compact));
  for (const shelf of ['all','xcpc','lanqiao','Codeforces','AtCoder','牛客']) assert.equal(matchesShelf(full,shelf),matchesShelf(compact,shelf));
}
assert.deepEqual(ids([...data.original.rows].sort(compareContestNewest)),ids([...data.compact.rows].sort(compareContestNewest)));
''','utf8')
            result=subprocess.run([shutil.which('node'),str(script),str(ROOT),str(data)],stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT,text=True,encoding='utf8',creationflags=0x08000000,timeout=20)
            self.assertEqual(result.returncode,0,result.stdout)


if __name__=='__main__':unittest.main()
