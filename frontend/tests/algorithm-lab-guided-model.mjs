import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { GUIDED_PROBLEMS, matchesGuidedProblem, matchesTransition, bestMiniPlan } from '../src/pages/algorithm-lab/guidedProblems.js';
import { enumerate01 } from '../src/pages/algorithm-lab/knapsackModel.js';
process.env.TB_OFFLINE = '1';
assert.ok(matchesGuidedProblem({ id: 'canonical', aliasIds: ['lab:luogu:P1048'] }, 'P1048'));
assert.ok(matchesGuidedProblem({ id: 'legacy', url: 'https://luogu.com.cn/problem/P1048/?source=fixture' }, 'P1048'));
assert.ok(!matchesGuidedProblem({ id: 'other', url: 'https://example.com/problem/P1048' }, 'P1048'));
const root = fileURLToPath(new URL('../../', import.meta.url)), output = path.join(root, '.backups/v135-lab/model');
await mkdir(output, { recursive: true });
const detail = JSON.parse(await readFile(path.join(root, 'data/library/detailed_solutions.json'), 'utf8'));
const statements = JSON.parse(await readFile(path.join(root, 'data/library/statements.json'), 'utf8'));
const bruteDual = (items, h, t) => {
  let best = 0;
  for (let mask = 0; mask < 2 ** items.length; mask++) {
    let volume = 0, mass = 0, value = 0;
    items.forEach((item, i) => { if (mask & (1 << i)) { volume += item.weight; mass += item.mass; value += item.value; } });
    if (volume <= h && mass <= t) best = Math.max(best, value);
  }
  return best;
};
let randomSeed = 135, executions = 0;
const random = max => { randomSeed = (Math.imul(randomSeed, 1664525) + 1013904223) >>> 0; return randomSeed % max; };
for (const p of GUIDED_PROBLEMS) {
  assert.ok(matchesTransition(p.line, p.line));
  assert.ok(!matchesTransition(p.line.replace('max', 'min'), p.line));
  const sample = p.mini;
  let expected = p.kind === 'dual' ? bruteDual(sample.items, sample.capacity, sample.weightLimit) : enumerate01(sample.items, sample.capacity);
  if (p.kind === 'space') expected = sample.capacity - expected;
  if (p.kind === 'balance') expected = sample.items.reduce((total, item) => total + item.weight, 0) - expected;
  assert.equal(expected, p.answer, `${p.pid}: interactive example`);
  const chosen = bestMiniPlan(p).map(index => sample.items[index]);
  const chosenWeight = chosen.reduce((sum, item) => sum + item.weight, 0), chosenValue = chosen.reduce((sum, item) => sum + item.value, 0);
  assert.ok(p.kind === 'balance' || chosenWeight <= sample.capacity);
  assert.ok(p.kind !== 'dual' || chosen.reduce((sum, item) => sum + item.mass, 0) <= sample.weightLimit);
  const comparison = p.kind === 'balance' ? Math.max(chosenWeight, sample.items.reduce((sum, item) => sum + item.weight, 0) - chosenWeight) : p.kind === 'space' ? sample.capacity - chosenWeight : chosenValue;
  assert.equal(comparison, p.answer, `${p.pid}: optional optimal-plan comparison`);
  const identity = `lab:luogu:${p.pid}`, markdown = detail.find(value => value.problem_id === identity).markdown;
  assert.ok(markdown.includes('这是教学小例，不是原题样例'));
  const cpp = markdown.match(/### 参考代码\s*\n+```cpp\n([\s\S]*?)```/)[1];
  const source = path.join(output, `${p.pid}.cpp`), exe = path.join(output, `${p.pid}.exe`);
  await writeFile(source, cpp);
  execFileSync(process.env.TB_CPP || 'g++', ['-std=c++17', '-O2', source, '-o', exe], { timeout: 60000, windowsHide: true, stdio: 'pipe' });
  const run = (input, answer) => { assert.equal(execFileSync(exe, [], { input, encoding: 'utf8', windowsHide: true, timeout: 5000 }).trim(), String(answer).trim(), p.pid + '\n' + input); executions++; };
  for (const test of statements.find(value => value.problem_id === identity).content.samples) run(test.input, test.output);
  for (let n = 0; n < 50; n++) {
    const count = 1 + random(7), capacity = 1 + random(12), items = Array.from({ length: count }, () => ({ weight: 1 + random(14), mass: 1 + random(14), value: 1 + random(30), importance: 1 + random(5) }));
    if (p.kind === 'balance') {
      const groups = Array.from({ length: 4 }, () => Array.from({ length: 1 + random(7) }, () => 1 + random(10)));
      let answer = 0;
      for (const group of groups) {
        const total = group.reduce((a, b) => a + b, 0);
        let best = Infinity;
        for (let mask = 0; mask < 2 ** group.length; mask++) { const left = group.reduce((a, value, i) => a + ((mask & (1 << i)) ? value : 0), 0); best = Math.min(best, Math.max(left, total - left)); }
        answer += best;
      }
      run(`${groups.map(g => g.length).join(' ')}\n${groups.map(g => g.join(' ')).join('\n')}\n`, answer);
    } else if (p.kind === 'dual') run(`${capacity} ${capacity}\n${count}\n${items.map(item => `${item.weight} ${item.mass} ${item.value}`).join('\n')}\n`, bruteDual(items, capacity, capacity));
    else if (p.kind === 'space') run(`${capacity}\n${count}\n${items.map(item => item.weight).join('\n')}\n`, capacity - enumerate01(items.map(item => ({ ...item, value: item.weight })), capacity));
    else if (p.kind === 'budget') run(`${capacity} ${count}\n${items.map(item => `${item.weight} ${item.importance}`).join('\n')}\n`, enumerate01(items.map(item => ({ ...item, value: item.weight * item.importance })), capacity));
    else run(`${capacity} ${count}\n${items.map(item => `${item.weight} ${item.value}`).join('\n')}\n`, enumerate01(items, capacity));
  }
}
const report = { ok: true, guidedProblems: 5, independentlyCheckedMiniatures: 5, actualCppExecutions: executions, originalSiteSubmissions: 0 };
await writeFile(path.join(output, 'result.json'), JSON.stringify(report, null, 2));
console.log('PASS guided models:', report);
