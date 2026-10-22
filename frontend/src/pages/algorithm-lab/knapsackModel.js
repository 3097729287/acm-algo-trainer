// Small, deterministic teaching models. These execute the displayed transitions,
// not arbitrary C++; official training continues through the existing workbench.
export const EXPEDITION = [
  { id: 'A', name: '对讲机', weight: 3, value: 5 },
  { id: 'B', name: '照明灯', weight: 2, value: 3 },
  { id: 'C', name: '急救包', weight: 2, value: 3 },
];

export function table01(items, capacity) {
  const table = [Array(capacity + 1).fill(0)];
  for (const item of items) {
    const previous = table.at(-1);
    table.push(previous.map((skip, c) => c < item.weight ? skip : Math.max(skip, previous[c - item.weight] + item.value)));
  }
  return table;
}

// Recover an actual packing so a table value always has a concrete meaning.
export function packingPlan(items, capacity) {
  const table = table01(items, capacity), picked = [];
  let remaining = capacity;
  for (let i = items.length; i > 0; i--) {
    if (table[i][remaining] > table[i - 1][remaining]) {
      picked.unshift(items[i - 1]);
      remaining -= items[i - 1].weight;
    }
  }
  return picked;
}

export function traceKnapsack(items, capacity, direction = 'down') {
  const values = Array(capacity + 1).fill(0), choices = values.map(() => []), versions = values.map(() => -1), frames = [];
  items.forEach((item, i) => {
    const capacities = Array.from({ length: Math.max(0, capacity - item.weight + 1) }, (_, c) => c + item.weight);
    if (direction === 'down') capacities.reverse();
    for (const c of capacities) {
      const source = c - item.weight, before = [...values], sourceChoices = [...choices[source]], skip = values[c], take = values[source] + item.value;
      const improved = take > skip, repeated = sourceChoices.includes(i), sourceFresh = versions[source] === i;
      if (improved) { values[c] = take; choices[c] = [...sourceChoices, i]; }
      versions[c] = i;
      frames.push({ i, item, c, source, before, after: [...values], skip, take, improved, repeated, sourceFresh, sourceChoices,
        choices: choices.map(picks => [...picks]), result: values[c] });
    }
  });
  return { frames, values: [...values], choices: choices.map(picks => [...picks]) };
}

export function solveExactly(items, capacity) {
  const dp = Array(capacity + 1).fill(-Infinity); dp[0] = 0;
  for (const { weight, value } of items)
    for (let c = capacity; c >= weight; c--)
      if (dp[c - weight] !== -Infinity) dp[c] = Math.max(dp[c], dp[c - weight] + value);
  return dp[capacity];
}

export function enumerate01(items, capacity, exact = false) {
  let best = exact ? -Infinity : 0;
  for (let mask = 0; mask < 2 ** items.length; mask++) {
    let weight = 0, value = 0;
    items.forEach((item, i) => { if (mask & (1 << i)) { weight += item.weight; value += item.value; } });
    if (exact ? weight === capacity : weight <= capacity) best = Math.max(best, value);
  }
  return best;
}

export const TEMPLATE_CASES = [
  { name: '一件物品不能用两次', capacity: 4, items: [{ weight: 2, value: 3 }] },
  { name: '装不下时可以什么都不拿', capacity: 3, items: [{ weight: 5, value: 9 }] },
  { name: '容量正好相等也要更新', capacity: 2, items: [{ weight: 2, value: 7 }] },
  { name: '最优解需要组合', capacity: 4, items: EXPEDITION },
  { name: '价值可能超过 int', capacity: 4, items: [{ weight: 2, value: 2000000000 }, { weight: 2, value: 2000000000 }] },
];

export function simulateTemplate(items, capacity, config) {
  const dp = Array(capacity + 1).fill(config.init === 'zero' ? 0 : -Infinity); dp[0] = 0;
  for (const { weight, value } of items) {
    const capacities = Array.from({ length: Math.max(0, capacity - weight + 1) }, (_, c) => c + weight);
    if (config.direction === 'down') capacities.reverse();
    for (const c of capacities) dp[c] = Math.max(dp[c], dp[config.source === 'remaining' ? c - weight : c] + value);
  }
  return dp[config.output === 'capacity' ? capacity : items.length] ?? null;
}

export function templateResults(config) {
  return TEMPLATE_CASES.map(test => ({ ...test, expected: enumerate01(test.items, test.capacity), actual: simulateTemplate(test.items, test.capacity, config) }));
}

export function cppTemplate(config = { init: 'zero', direction: 'down', source: 'remaining', output: 'capacity' }) {
  const init = config.init ? config.init === 'zero' ? 'vector<long long> dp(W + 1, 0);' : 'vector<long long> dp(W + 1, -(1LL << 60));\n    dp[0] = 0;' : '/* ① 初始化 dp */';
  const loop = config.direction ? config.direction === 'down' ? 'for (int c = W; c >= w; --c)' : 'for (int c = w; c <= W; ++c)' : '/* ② 容量循环 */';
  const source = config.source ? config.source === 'remaining' ? 'dp[c - w]' : 'dp[c]' : '/* ③ 从哪里转移？ */';
  const output = config.output ? config.output === 'capacity' ? 'dp[W]' : 'dp[n]' : '/* ④ 输出哪个状态？ */';
  return `#include <iostream>\n#include <vector>\n#include <algorithm>\nusing namespace std;\n\nint main() {\n    int n, W;\n    cin >> n >> W;\n    ${init}\n    for (int i = 0; i < n; ++i) {\n        int w;\n        long long v;\n        cin >> w >> v;\n        ${loop}\n            dp[c] = max(dp[c], ${source} + v);\n    }\n    cout << ${output} << '\\n';\n    return 0;\n}`;
}

export const displayValue = value => value === -Infinity ? '不可达' : value == null ? '越界' : String(value);
