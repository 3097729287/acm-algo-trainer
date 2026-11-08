import assert from 'node:assert/strict';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {buildLearningIndex,learningSearch} from '../src/lib/learningBrowser.js';
import {workspaceSearchIndex,searchWorkspace} from '../src/lib/workspaceSearch.js';
import {normalizeProblemCode} from '../src/lib/problemSearchCodes.js';

const fixtures={rows:[
 {id:'opaque-id',problem:'P1886',title:'单调队列 / 滑动窗口',platform:'洛谷',tags:['单调队列']},
 {id:'legacy-code',code:'CF1237D',title:'Balanced Playlist'},
 {id:'legacy:P1440',title:'区间最小值'},
 {id:'namespaced-cf',problem:'E',title:'Shortest Path',url:'https://codeforces.com/contest/59/problem/E'},
 {id:'namespaced-at',problem:'G',title:'Cascading Grid',url:'https://atcoder.jp/contests/abc472/tasks/abc472_g'},
 {id:'nearby',problem:'P18860',title:'P1886 扩展练习'},
 {id:'bad-url',problem:'P3379',title:'LCA',url:'invalid://bad%escape'},
],lectures:[{id:'number-title',title:'P1886',concept:'P1886'}]};
const index=workspaceSearchIndex(fixtures);
for(const query of ['P1886','p1886',' Ｐ１８８６ ','P 1886','P-1886'])assert.equal(searchWorkspace(index,query)[0].id,'opaque-id',query);
for(const [query,id] of [['CF1237D','legacy-code'],['P1440','legacy:P1440'],['CF59E','namespaced-cf'],['59E','namespaced-cf'],['ABC472G','namespaced-at'],['abc472_g','namespaced-at'],['ABC 472 G','namespaced-at'],['P3379','bad-url']])assert.equal(searchWorkspace(index,query)[0].id,id,query);
assert.equal(searchWorkspace(index,'P18860')[0].id,'nearby');
assert.equal(searchWorkspace(index,'洛谷 P1886')[0].id,'opaque-id');
assert(!searchWorkspace(index,'P1886 动态规划').some(row=>row.id==='opaque-id'),'Additional query words still constrain the result');
assert.deepEqual(searchWorkspace(index,'P999999999'),[]);
assert(learningSearch(buildLearningIndex(fixtures),'P1886').some(row=>row.id==='opaque-id'),'Learning-content search uses the same recorded numbers');
const rows=JSON.parse(await readFile('../data/library/problems.json','utf8')).map(row=>row.encoded),real=workspaceSearchIndex({rows});
const cases=[['P1886','luogu-training-P1886'],['P1440','luogu-training-P1440'],['P1714','luogu-training-P1714'],['P5788','luogu-training-P5788'],['P3531','luogu-training-P3531'],['P2564','luogu-training-P2564'],['CF1237D','luogu-training-CF1237D'],['P7167','luogu-training-P7167'],['P1196','luogu-training-P1196'],['P2294','luogu-training-P2294'],['P3379','luogu-training-P3379'],['UVA11367','luogu-training-UVA11367'],['CF59E','lab:codeforces:59E'],['142559/D','remote:nowcoder:142559::D'],['ABC472E','ABC 472::E'],['ARC231A','ARC 231::A']];
for(const [query,id] of cases){const found=searchWorkspace(real,query);assert(found.some(row=>row.id===id),query);assert(found[0].normalizedCodes.includes(normalizeProblemCode(query)),'An exact problem number precedes title mentions');}
const report={ok:true,realLibraryRows:rows.length,realNumberCases:cases.length,recordedProblemField:true,legacyCodeAndId:true,officialUrlIdentifiers:true,caseAndWidthInsensitive:true,exactCodeFirst:true,additionalWordsPreserved:true,learningSearch:true};
await mkdir('../.backups/problem-number-search-20261108',{recursive:true});await writeFile('../.backups/problem-number-search-20261108/model.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));
