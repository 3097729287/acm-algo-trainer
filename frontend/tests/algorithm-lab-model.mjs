import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { EXPEDITION, TEMPLATE_CASES, cppTemplate, enumerate01, solveExactly, table01, templateResults, traceKnapsack } from '../src/pages/algorithm-lab/knapsackModel.js';

process.env.TB_OFFLINE = '1';
const output = fileURLToPath(new URL('../../.backups/algorithm-lab-20261022/model/', import.meta.url));
await mkdir(output, { recursive: true });
let seed = 0x507ac1, comparisons = 0;
const random = max => { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed % max; };
function enumerateUnlimited(items, capacity, i = 0) {
  if (i === items.length) return 0;
  let best = 0;
  for (let count = 0; count * items[i].weight <= capacity; count++)
    best = Math.max(best, count * items[i].value + enumerateUnlimited(items, capacity - count * items[i].weight, i + 1));
  return best;
}

const randomCases = [];
for (let test = 0; test < 600; test++) {
  const capacity = random(13), items = Array.from({ length: random(7) }, (_, i) => ({ id: String(i), weight: 1 + random(15), value: random(31) }));
  const table = table01(items, capacity), down = traceKnapsack(items, capacity, 'down'), up = traceKnapsack(items, capacity, 'up');
  for (let c = 0; c <= capacity; c++) {
    const expected = enumerate01(items, c);
    assert.equal(table.at(-1)[c], expected);
    assert.equal(down.values[c], expected);
    assert.equal(solveExactly(items, c), enumerate01(items, c, true));
    assert.equal(up.values[c], enumerateUnlimited(items, c));
    comparisons += 4;
  }
  for (const frame of down.frames) {
    assert.equal(frame.sourceFresh, false);
    assert.equal(frame.repeated, false);
    assert.equal(new Set(frame.choices[frame.c]).size, frame.choices[frame.c].length);
    assert.equal(frame.choices[frame.c].reduce((total, i) => total + items[i].value, 0), frame.result);
    assert.ok(frame.choices[frame.c].reduce((total, i) => total + items[i].weight, 0) <= frame.c);
    comparisons += 5;
  }
  randomCases.push({ name: `generated ${test}`, capacity, items });
}

assert.equal(table01(EXPEDITION, 4).at(-1)[4], 6);
const counterexample = traceKnapsack([{ id: 'A', weight: 2, value: 3 }], 4, 'up');
assert.equal(counterexample.values[4], 6);
assert.equal(counterexample.frames.at(-1).repeated, true);
assert.equal(counterexample.frames.at(-1).sourceFresh, true);
assert.deepEqual(counterexample.frames.at(-1).choices[4], [0, 0]);
assert.equal(solveExactly([{ weight: 2, value: 5 }], 3), -Infinity);
assert.equal(solveExactly([{ weight: 2, value: 5 }], 2), 5);

let validConfigurations = 0;
for (const init of ['zero', 'negative']) for (const direction of ['down', 'up']) for (const source of ['remaining', 'same']) for (const result of ['capacity', 'count']) {
  const tests = templateResults({ init, direction, source, output: result });
  if (tests.every(test => test.actual === test.expected)) validConfigurations++;
}
assert.equal(validConfigurations, 1, 'the lesson counterexamples must reject every incorrect builder combination');

const sourceFile = path.join(output, 'knapsack.cpp'), executable = path.join(output, process.platform === 'win32' ? 'knapsack.exe' : 'knapsack');
await writeFile(sourceFile, cppTemplate(), 'utf8');
const compiler = process.env.TB_CPP || 'g++';
execFileSync(compiler, ['-std=c++17', '-O2', sourceFile, '-o', executable], { timeout: 60000, windowsHide: true, stdio: 'pipe' });
const cppCases = [...TEMPLATE_CASES, { name: 'empty input set', capacity: 0, items: [] }, ...randomCases.slice(0, 30)];
for (const test of cppCases) {
  const input = `${test.items.length} ${test.capacity}\n${test.items.map(item => `${item.weight} ${item.value}`).join('\n')}\n`;
  const actual = execFileSync(executable, [], { input, encoding: 'utf8', timeout: 5000, windowsHide: true }).trim();
  assert.equal(actual, String(enumerate01(test.items, test.capacity)), `compiled C++: ${test.name}`);
}
const report = { status: 'passed', generatedCases: 600, assertionsAgainstIndependentEnumeration: comparisons, builderConfigurations: 16, validConfigurations, compiledCppCases: cppCases.length, officialSubmissions: 0 };
await writeFile(path.join(output, 'result.json'), JSON.stringify(report, null, 2));
console.log('PASS:', report);
