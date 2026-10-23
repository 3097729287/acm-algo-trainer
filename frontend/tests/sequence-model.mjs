import assert from 'node:assert/strict';
import { applyEvents, bruteShortest, compactTrace, difference, exactSumTrace, matchesSequenceProblem, pairTrace, parseSequence, prefix, rectangleEvents, rectangleSum, shortestTrace, total, uniqueTrace } from '../src/pages/algorithm-lab/sequenceModel.js';
import { SEQUENCE_PROBLEMS } from '../src/pages/algorithm-lab/sequenceProblems.js';

let seed = 20261023, checks = 0;
const random = n => { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed % n; };
const equal = (a, b) => { assert.deepEqual(a, b); checks++; };
for (let trial = 0; trial < 1200; trial++) {
  const n = 1 + random(10), a = Array.from({ length: n }, () => random(19) - 9), p = prefix(a);
  equal(prefix(difference(a)).slice(1), a);
  equal(difference(p.slice(1)), a);
  for (let l = 0; l < n; l++) for (let r = l; r < n; r++) equal(p[r + 1] - p[l], total(a.slice(l, r + 1)));
  const operations = Array.from({ length: random(12) }, () => { const l = 1 + random(n), r = l + random(n - l + 1); return { l, r, k: random(19) - 9 }; });
  const expected = [...a]; for (const { l, r, k } of operations) for (let i = l - 1; i < r; i++) expected[i] += k;
  equal(applyEvents(a, operations).result, expected);
  equal(applyEvents(a, operations).additions.at(-1), 0);
  const sorted = [...a].sort((x, y) => x - y), target = random(31) - 15, trace = pairTrace(sorted, target), candidates = [];
  for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) if (sorted[i] + sorted[j] === target) candidates.push([i, j]);
  equal(trace.at(-1).action === 'found', candidates.length > 0);
  assert.ok(trace.length <= n); checks++;
  for (const s of trace) {
    if (s.action === 'left') for (let j = s.l + 1; j <= s.r; j++) { assert.notEqual(sorted[s.l] + sorted[j], target); checks++; }
    if (s.action === 'right') for (let i = s.l; i < s.r; i++) { assert.notEqual(sorted[i] + sorted[s.r], target); checks++; }
  }
  const nonnegative = a.map(Math.abs), S = 1 + random(30), window = shortestTrace(nonnegative, S);
  equal(window.at(-1).best, bruteShortest(nonnegative, S).best);
  assert.ok(window.at(-1).moves <= 2 * n); checks++;
  for (const state of window) equal(state.sum, total(nonnegative.slice(state.l, state.r + 1)));
  const text = a.map(x => String.fromCharCode(97 + Math.abs(x) % 4)).join('');
  let longest = 0; for (let i = 0; i < n; i++) for (let j = i; j < n; j++) if (new Set(text.slice(i, j + 1)).size === j - i + 1) longest = Math.max(longest, j - i + 1);
  equal(uniqueTrace(text).at(-1).best, longest);
  const compact = compactTrace(a).at(-1); equal(compact.buffer.slice(0, compact.write), a.filter(x => x !== 0));
  let exact = 0; for (let i = 0; i < n; i++) for (let j = i; j < n; j++) if (total(a.slice(i, j + 1)) === target) exact++;
  equal(exactSumTrace(a, target).at(-1).answer, exact);
  const h = 1 + random(5), w = 1 + random(5), grid = Array.from({ length: h }, () => Array.from({ length: w }, () => random(21) - 10));
  const x1 = 1 + random(h), x2 = x1 + random(h - x1 + 1), y1 = 1 + random(w), y2 = y1 + random(w - y1 + 1), k = random(15) - 7;
  let rect = 0; for (let i = x1 - 1; i < x2; i++) for (let j = y1 - 1; j < y2; j++) rect += grid[i][j];
  equal(rectangleSum(grid, x1, y1, x2, y2).value, rect);
  equal(rectangleEvents(h, w, x1, y1, x2, y2, k).result, grid.map((row, i) => row.map((_, j) => i + 1 >= x1 && i + 1 <= x2 && j + 1 >= y1 && j + 1 <= y2 ? k : 0)));
}
equal(shortestTrace([1, -1, 5], 5).at(-1).best, 3);
equal(bruteShortest([1, -1, 5], 5).best, 1);
equal(exactSumTrace([0, 0, 0], 0).at(-1).answer, 6);
equal(applyEvents([2, 5, 1], [{ l: 2, r: 2, k: 3 }], true).result, [2, 5, 1]);
for (const text of ['', '1 x', '1.5', '100', '1e2', 'Infinity', '1 '.repeat(13)]) assert.ok(parseSequence(text).error);
equal(parseSequence('−1').error !== undefined, true); // Unicode minus is rejected clearly.
equal(parseSequence('-1, 0，2').values, [-1, 0, 2]);
assert.ok(parseSequence('0 1', { positive: true }).error);
for (const problems of Object.values(SEQUENCE_PROBLEMS)) {
  equal(problems.map(p => p.rating), problems.map(p => p.rating).sort((a, b) => a - b));
  for (const problem of problems) {
    equal(matchesSequenceProblem({ id: 'different', url: problem.url.replace('/problemset/problem/', '/contest/').replace(/\/(\w+)$/, '/problem/$1') }, problem), true);
    equal(matchesSequenceProblem({ id: 'local-alias', aliasIds: [problem.id] }, problem), true);
    equal(matchesSequenceProblem({ url: problem.url.replace('codeforces.com', 'codeforces.com.evil.example') }, problem), false);
  }
}
console.log(JSON.stringify({ status: 'passed', randomizedCases: 1200, assertions: checks, negativeCounterexample: { flawed: 3, correct: 1 } }));
