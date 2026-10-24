import assert from 'node:assert/strict';
import { algorithmPath, matchesTrainingProblem, trainingIndex } from '../src/lib/trainingLists.js';

const a = { id: 'a', aliasIds: ['old-a'], url: 'https://www.luogu.com.cn/problem/P1', title: '背包练习', accepted: true };
const b = { id: 'b', url: 'https://www.luogu.com.cn/problem/P2', title: '第二题', accepted: false };
const ref = (pid, problemId) => ({ pid, problemId, url: `https://www.luogu.com.cn/problem/${pid}`, sections: [] });
const lists = [
  { id: 'parent', title: '综合训练', problems: [], children: ['one', 'two'], categories: [] },
  { id: 'one', title: '背包', problems: [ref('P1', 'old-a'), ref('P1', 'a')], children: ['parent'], categories: [], aggregateChildren: false },
  { id: 'two', title: '动态规划', problems: [ref('P1', 'old-a'), ref('P2', 'b'), ref('P3', null)], children: ['parent'], categories: [] },
];
const index = trainingIndex(lists, [a, b]);
assert.equal(index.own.get('one').length, 1, 'aliases count once within a list');
assert.equal(index.all('parent').length, 3, 'cycles and overlaps count each original once');
assert.equal(index.all('one').length, 1, 'roster recommendation links do not widen its scope');
assert.deepEqual(index.stats(['parent', 'one', 'two']), { total: 3, accepted: 1 });
assert.ok(matchesTrainingProblem(index.all('one')[0], 'P1 背包', 'accepted'));
assert.ok(!matchesTrainingProblem(index.all('one')[0], '', 'pending'));
assert.deepEqual(algorithmPath('【算法1-6】二分查找与二分答案'), ['基础算法', '二分与三分']);
assert.deepEqual(algorithmPath('背包问题（简单）'), ['动态规划', '背包']);
assert.deepEqual(algorithmPath('某个无法核实的专题'), ['综合训练']);
console.log('Training list identity, hierarchy, cycle, search and progress checks passed');
