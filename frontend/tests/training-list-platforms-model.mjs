import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {trainingListPlatform,platformTrainingLists,platformListState} from '../src/lib/trainingListPlatforms.js';
import {organizeTrainingLists} from '../src/lib/trainingListCatalog.js';
import {buildTrainingCurriculum,filterTrainingListsScope,CURRICULUM_STAGES} from '../src/lib/trainingCurriculum.js';
const cases=[
 [{url:'https://www.luogu.com.cn/training/100',title:'牛客字样不改变真实来源'},'洛谷'],
 [{url:'https://ac.nowcoder.com/discuss/817596',platform:'洛谷'},'牛客'],
 [{title:'洛谷 牛客 入门题单'},null],
 [{url:'https://evil-luogu.com.cn/training/100'},null],
 [{url:'https://ac.nowcoder.com.evil.invalid/discuss/1'},null],
 [{sourcePlatform:'洛谷'},'洛谷'],[{platform:'Nowcoder'},'牛客'],
 [{custom:true,url:'https://www.luogu.com.cn/training/100'},null],
];
for(const [list,expected]of cases)assert.equal(trainingListPlatform(list),expected);
const raw=JSON.parse(await readFile(new URL('../../data/library/training_lists.json',import.meta.url),'utf8'));
const rows=JSON.parse(await readFile(new URL('../../data/library/problems.json',import.meta.url),'utf8')).map(item=>item.encoded||item);
const original=filterTrainingListsScope(organizeTrainingLists(raw),rows);
assert.equal(original.filter(list=>trainingListPlatform(list)==='洛谷').length,563);
assert.equal(original.filter(list=>trainingListPlatform(list)==='牛客').length,1);
const displayed=platformTrainingLists(original,rows);
const nowcoder=displayed.find(list=>list.id==='nowcoder-817596-sequential-verified');
assert.deepEqual(nowcoder.topicPath,['牛客']);assert.equal(nowcoder.problems.length,14);
assert.deepEqual(nowcoder.problems,original.find(list=>list.id===nowcoder.id).problems);
assert.equal(nowcoder.url,'https://ac.nowcoder.com/discuss/817596');assert(!('officialLikes'in nowcoder));assert(!('favorites'in nowcoder));
const onlyLuogu=buildTrainingCurriculum(original.filter(list=>trainingListPlatform(list)==='洛谷'),rows);
assert.deepEqual(displayed.filter(list=>list.topicPath[0]==='洛谷').map(list=>list.id),onlyLuogu.map(list=>list.id));
const previous=buildTrainingCurriculum(original,rows),nextIds=new Set(displayed.map(list=>list.id));
assert(previous.every(list=>nextIds.has(list.id)),'Keep every existing generated curriculum ID in the actual public seed');
assert.strictEqual(platformTrainingLists(original,rows,'source'),original,'Source mode preserves collection/category identities');
for(const stage of CURRICULUM_STAGES)assert.deepEqual(platformListState({mode:'algorithm',folder:[stage],trail:['curriculum:0']}).folder,['洛谷',stage]);
for(const state of [{mode:'algorithm',folder:[]},{mode:'algorithm',folder:['我的题单']},{mode:'source',folder:['01 编程基础']}])assert.strictEqual(platformListState(state),state);
console.log(JSON.stringify({ok:true,sourceCases:cases.length,realLuoguSources:563,realNowcoderSources:1,nowcoderProblems:14,curriculumIdsPreserved:previous.length,sourceModeUnchanged:true,legacyStagePathsMigrated:CURRICULUM_STAGES.length}));
