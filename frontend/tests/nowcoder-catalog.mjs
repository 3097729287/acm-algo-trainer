import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {organizeNowcoderTrainingLists} from '../src/lib/nowcoderTrainingLists.js';
import {trainingIndex} from '../src/lib/trainingLists.js';
const originals=JSON.parse(readFileSync(new URL('../../data/library/training_lists.json',import.meta.url),'utf8'));
const lists=organizeNowcoderTrainingLists(originals),nowcoder=lists.filter(list=>list.id.startsWith('nowcoder-'));
assert.equal(nowcoder.length,72);
assert.deepEqual(nowcoder.filter(list=>!list.catalogHidden).sort((a,b)=>a.curriculumOrder-b.curriculumOrder).map(list=>list.displayTitle),['语法与算法入门','算法基础精选','算法进阶']);
const before=trainingIndex(originals,[]),after=trainingIndex(lists,[]);
for(const original of originals){
 const current=lists.find(list=>list.id===original.id);
 assert.deepEqual(current.problems,original.problems);assert.deepEqual(current.children,original.children);
 assert.equal(current.url,original.url);
 assert.deepEqual(after.all(original.id),before.all(original.id));
 if(!original.id.startsWith('nowcoder-'))assert.deepEqual(current,original);
}
assert.equal(lists.find(list=>list.id==='nowcoder-contest-27589').displayTitle,'KMP · 基础与应用');
assert.equal(lists.find(list=>list.id==='nowcoder-contest-28258').displayTitle,'树形 DP · 例题');
console.log('PASS Nowcoder has three ordered root directories, consistent titles, retained child order, source identities and all problem memberships');
