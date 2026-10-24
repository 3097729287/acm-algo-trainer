import assert from 'node:assert/strict';
import fs from 'node:fs';
import { algorithmPath, matchesTrainingProblem, trainingIndex } from '../src/lib/trainingLists.js';
import { organizeTrainingLists, compareTrainingLists, CATEGORY_ORDER } from '../src/lib/trainingListCatalog.js';

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

const original = JSON.parse(fs.readFileSync(new URL('../../data/library/training_lists.json', import.meta.url), 'utf8'));
const before = JSON.stringify(original);
const organized = organizeTrainingLists(original), byId = new Map(organized.map(row => [row.id, row]));
assert.equal(organized.length, original.length);
assert.equal(JSON.stringify(original), before, 'organizing must not change source rosters or titles');
assert.equal(new Set(organized.map(row => row.id)).size, original.length);
for (const row of organized) {
  assert.equal(row.topicPath.length, 2, row.id);
  assert.ok(CATEGORY_ORDER.includes(row.topicPath[0]), row.id);
  assert.ok(row.displayTitle.length >= 2, row.id);
  assert.ok(row.originalTitle && row.url && row.sourceLabel, row.id);
  assert.ok(!/[\u202a-\u202e\u2066-\u2069]|菜鸡|蒟蒻|从入门到入土/.test(row.displayTitle), row.displayTitle);
}
for (const [id, path] of [
  ['7768', '字符串/模式匹配'], ['4790', '字符串/后缀结构'], ['5322', '字符串/后缀结构'],
  ['22566', '字符串/回文算法'], ['379836', '字符串/字符串哈希'], ['82023', '动态规划/数位动态规划'],
  ['4575', '数学/概率与期望'], ['6358', '数学/数论'], ['8174', '图论/连通性'],
  ['247303', '图论/生成树'], ['20236', '图论/拓扑排序与 2-SAT'], ['4837', '图论/最短路'],
  ['559292', '动态规划/动态规划优化'], ['288889', '搜索/启发式搜索'],
  ['1792', '教材配套/算法竞赛入门经典'], ['9349', '待补充信息/关联题单'],
]) assert.equal(byId.get('luogu-' + id).topicPath.join('/'), path, id);
assert.match(byId.get('luogu-551').displayTitle, /C\+\+/);
assert.match(byId.get('luogu-560').displayTitle, /C\/C\+\+/);
assert.equal(byId.get('luogu-104').displayTitle, '字符串基础 · 入门');
assert.equal(byId.get('luogu-1016093').available, false, 'unavailable source keeps its real status');
const sorted = ['203', '104'].map(id => byId.get('luogu-' + id)).sort(compareTrainingLists);
assert.equal(sorted[0].id, 'luogu-104');
assert.deepEqual(trainingIndex(organized, [a, b]).stats(organized.map(row => row.id)), trainingIndex(original, [a, b]).stats(original.map(row => row.id)));
console.log(`PASS: ${original.length} lists categorized, named, source-preserved; known cross-topic errors covered`);
