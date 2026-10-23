// Teaching models use 1-based closed intervals; JavaScript arrays remain 0-based.
export const total = values => values.reduce((sum, value) => sum + value, 0);

export function parseSequence(text, { positive = false, limit = 12 } = {}) {
  const words = text.trim().split(/[\s,，]+/).filter(Boolean);
  if (!words.length || words.length > limit || words.some(word => !/^-?\d+$/.test(word))) return { error: `请输入 1～${limit} 个整数，用空格或逗号分开。` };
  const values = words.map(Number);
  if (values.some(value => !Number.isSafeInteger(value) || Math.abs(value) > 99 || (positive && value <= 0))) return { error: positive ? '本实验每个数须为 1～99；负数的反例在后面单独检验。' : '本实验每个数须在 −99～99 之间。' };
  return { values };
}

export function prefix(values) {
  const result = [0];
  for (const value of values) result.push(result.at(-1) + value);
  return result;
}

export function difference(values) {
  return values.map((value, i) => value - (i ? values[i - 1] : 0));
}

export const rangeSum = (values, l, r) => prefix(values)[r] - prefix(values)[l - 1];

export function applyEvents(values, operations, wrongEnd = false) {
  const delta = Array(values.length + 1).fill(0);
  for (const { l, r, k } of operations) {
    delta[l - 1] += k;
    delta[wrongEnd ? r - 1 : r] -= k;
  }
  const additions = prefix(delta).slice(1);
  return { delta, additions, result: values.map((value, i) => value + additions[i]) };
}

export function prefix2D(grid) {
  const p = Array.from({ length: grid.length + 1 }, () => Array(grid[0].length + 1).fill(0));
  grid.forEach((row, i) => row.forEach((value, j) => { p[i + 1][j + 1] = value + p[i][j + 1] + p[i + 1][j] - p[i][j]; }));
  return p;
}

export function rectangleSum(grid, x1, y1, x2, y2) {
  const p = prefix2D(grid);
  return { terms: [p[x2][y2], p[x1 - 1][y2], p[x2][y1 - 1], p[x1 - 1][y1 - 1]], value: p[x2][y2] - p[x1 - 1][y2] - p[x2][y1 - 1] + p[x1 - 1][y1 - 1] };
}

export function rectangleEvents(rows, cols, x1, y1, x2, y2, k) {
  const d = Array.from({ length: rows + 1 }, () => Array(cols + 1).fill(0));
  d[x1 - 1][y1 - 1] += k; d[x2][y1 - 1] -= k; d[x1 - 1][y2] -= k; d[x2][y2] += k;
  return { delta: d, result: prefix2D(d).slice(1, rows + 1).map(row => row.slice(1, cols + 1)) };
}

export function pairTrace(values, target) {
  let l = 0, r = values.length - 1;
  const states = [];
  while (l < r) {
    const sum = values[l] + values[r], action = sum === target ? 'found' : sum < target ? 'left' : 'right';
    states.push({ l, r, sum, action });
    if (action === 'found') return states;
    if (action === 'left') l++; else r--;
  }
  states.push({ l, r, action: 'end' });
  return states;
}

// Deliberately accepts negatives too: the negative-number lesson runs the flawed
// extension of this positive-window method and compares it with exhaustive search.
export function shortestTrace(values, target) {
  let l = 0, r = -1, sum = 0, best = Infinity, moves = 0;
  const states = [];
  while (true) {
    if (sum >= target && l <= r) best = Math.min(best, r - l + 1);
    const action = sum >= target && l <= r ? 'shrink' : r + 1 < values.length ? 'expand' : 'end';
    states.push({ l, r, sum, best: Number.isFinite(best) ? best : 0, moves, action });
    if (action === 'end') return states;
    if (action === 'shrink') sum -= values[l++]; else sum += values[++r];
    moves++;
  }
}

export function bruteShortest(values, target) {
  let best = 0; const windows = [];
  for (let l = 0; l < values.length; l++) {
    let sum = 0;
    for (let r = l; r < values.length; r++) {
      sum += values[r]; const legal = sum >= target;
      windows.push({ l, r, sum, legal });
      if (legal && (!best || r - l + 1 < best)) best = r - l + 1;
    }
  }
  return { best, windows };
}

export function uniqueTrace(text) {
  let l = 0, r = -1, best = 0; const count = {}, states = [];
  while (true) {
    const repeated = Object.values(count).some(value => value > 1);
    if (!repeated) best = Math.max(best, r - l + 1);
    const action = repeated ? 'shrink' : r + 1 < text.length ? 'expand' : 'end';
    states.push({ l, r, count: { ...count }, best, action });
    if (action === 'end') return states;
    if (action === 'shrink') { count[text[l]]--; l++; }
    else { r++; count[text[r]] = (count[text[r]] || 0) + 1; }
  }
}

export function compactTrace(values) {
  const buffer = [...values], states = [{ read: 0, write: 0, buffer: [...buffer], action: 'start' }];
  let write = 0;
  values.forEach((value, read) => {
    const action = value === 0 ? 'skip' : 'write';
    if (value !== 0) buffer[write++] = value;
    states.push({ read: read + 1, write, buffer: [...buffer], action, value });
  });
  return states;
}

export function exactSumTrace(values, target) {
  let sum = 0, answer = 0; const frequencies = new Map([[0, 1]]), states = [];
  values.forEach((value, i) => {
    sum += value; const wanted = sum - target, hits = frequencies.get(wanted) || 0;
    answer += hits;
    states.push({ i: i + 1, sum, wanted, hits, answer, previous: [...frequencies] });
    frequencies.set(sum, (frequencies.get(sum) || 0) + 1);
  });
  return states;
}

export function matchesSequenceProblem(row, problem) {
  if (!row || !problem) return false;
  if ([row.id, ...(row.aliasIds || [])].includes(problem.id)) return true;
  try {
    const url = new URL(row.url), match = url.pathname.match(/^\/(?:problemset\/problem|contest)\/(\d+)\/(?:problem\/)?([A-Za-z]\d*)\/?$/);
    return /(^|\.)codeforces\.com$/i.test(url.hostname) && !!match && `${match[1]}${match[2].toUpperCase()}` === problem.pid;
  } catch { return false; }
}
