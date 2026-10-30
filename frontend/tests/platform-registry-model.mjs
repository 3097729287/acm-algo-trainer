import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {PLATFORM_REGISTRY,platformInfo,platformNames,platformFromUrl,rowPlatform,normalizePlatform} from '../src/lib/platformRegistry.js';
import {catalogPaths,catalogPathMatches,catalogEntries,contestOptions} from '../src/lib/contestCatalog.js';
import {matchesShelf} from '../src/lib/contestShelves.js';
import {trainingListPlatform,platformTrainingLists} from '../src/lib/trainingListPlatforms.js';
import {submissionQuery} from '../src/lib/submissionPages.js';

const cases=[];
for(const {id}of PLATFORM_REGISTRY){
 const row={id:id+'::fixture',platform:id,title:'A',contest:'CCPC 2026 隔离省赛',series:'XCPC',eventYear:2026,url:id==='QOJ'?'https://qoj.ac/problem/18307':undefined};
 const original=JSON.stringify(row);
 assert(!matchesShelf(row,id));assert(matchesShelf(row,'xcpc'));
 assert(!catalogPathMatches(row,[id]));assert(catalogPathMatches(row,['XCPC','省赛']));
 assert.equal(catalogEntries([row],[id]).length,0);
 assert.equal(catalogPaths(row).length,1);
 assert.equal(rowPlatform(row),id);assert.equal(JSON.stringify(row),original,'Classification never rewrites original identity or platform');
 const regular={...row,contest:'普通练习赛 1',series:id};
 assert(matchesShelf(regular,id));assert(!matchesShelf(regular,'XCPC'));assert(catalogPathMatches(regular,[id]));
 assert(platformInfo(id).nativeSubmit);cases.push(id);
}
const future={id:'future::A',platform:'FutureJudge',contest:'独立杯',title:'A',url:'https://future.invalid/problem/1'};
assert.equal(platformInfo(future.platform).nativeSubmit,false);assert.notEqual(platformInfo(future.platform).badge,'CF');
assert.equal(platformFromUrl('https://qoj.ac.evil.invalid/problem/18307'),'');assert.equal(platformFromUrl('https://evil@qoj.ac/problem/18307'),'');
assert.equal(platformFromUrl('https://qoj.ac/contest/3767/problem/18307/statement/zh_cn'),'QOJ');
assert.equal(rowPlatform({url:'https://qoj.ac/problem/18307'}),'QOJ');assert.equal(normalizePlatform('qoj'),'QOJ');
assert.equal(rowPlatform({platform:'Codeforces',url:'https://qoj.ac/problem/18307'}),'Codeforces','Do not silently rewrite an explicit original identity');
assert(catalogEntries([future]).some(entry=>entry.label==='FutureJudge'));
assert.deepEqual(platformNames([future,{platform:'QOJ'},{platform:'qoj'},{platform:'AtCoder'}]),['AtCoder','QOJ','FutureJudge']);
assert.equal(new URLSearchParams(submissionQuery({platform:'QOJ',offset:100})).get('platform'),'QOJ');
assert.equal(new URLSearchParams(submissionQuery({platform:'FutureJudge'})).get('platform'),'FutureJudge');
assert(!new URLSearchParams(submissionQuery()).has('platform'),'Preserve the original unfiltered cache key');
assert.equal(trainingListPlatform({url:'https://qoj.ac/category/21'}),'QOJ');
assert.equal(trainingListPlatform({sourcePlatform:'FutureJudge'}),'FutureJudge');
assert.equal(trainingListPlatform({title:'QOJ 题单'}),null,'Titles are not source provenance');
assert.equal(trainingListPlatform({custom:true,sourcePlatform:'QOJ'}),null,'Private folders retain their identity');
const futureList={id:'future-list',sourcePlatform:'FutureJudge',topicPath:['基础'],problems:['future::A']};
assert.deepEqual(platformTrainingLists([futureList],[future])[0].topicPath,['FutureJudge','基础']);
const raw=JSON.parse(await readFile(new URL('../../data/library/problems.json',import.meta.url),'utf8')).map(item=>item.encoded||item);
const qoj=raw.filter(row=>row.platform==='QOJ');assert.equal(qoj.length,65,'Audit the unchanged public QOJ inventory');
assert(qoj.every(row=>new URL(row.url).hostname==='qoj.ac'&&/^\/problem\/\d+\/?$/.test(new URL(row.url).pathname)));
for(const row of qoj){assert(!catalogPathMatches(row,['QOJ']));assert(catalogPathMatches(row,['XCPC']));}
assert.equal(new Set(qoj.map(row=>row.url)).size,65);
const qojEntries=catalogEntries(qoj,['XCPC']);assert.equal(new Set(qojEntries.flatMap(entry=>entry.items.map(row=>row.id))).size,65);
const events=qoj.map(row=>({...row,name:row.contest,count:13}));
assert(!contestOptions(events).some(node=>node.label==='QOJ'));assert(contestOptions(events).some(node=>node.label==='XCPC'));
for(const contest of ['ICPC 2026 区域赛','CCPC 2026 省赛','2026 大学生邀请赛']){
 const row={platform:'牛客',contest};assert(catalogPathMatches(row,['XCPC']));assert(!catalogPathMatches(row,['牛客']));
}
assert(!matchesShelf({platform:'洛谷',contest:'蓝桥杯 2026 省赛',series:'蓝桥杯'},'XCPC'),'Lanqiao retains its separate competition category');
assert.equal(catalogPaths(future).length,1);
console.log(JSON.stringify({ok:true,existingPlatforms:cases,qojOriginals:qoj.length,futureDisplayOnly:true,categoryAndSourceIndependent:true,unchangedOriginalUrls:true}));
