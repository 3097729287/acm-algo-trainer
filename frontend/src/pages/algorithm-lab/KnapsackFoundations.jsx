import { useMemo, useState } from 'react';
import { EXPEDITION, EXPEDITION_CAPACITY as CAPACITY, packingPlan, table01 } from './knapsackModel.js';
import { BagSlots } from './LabParts.jsx';

export function InitializationDemo() {
  const table = useMemo(() => table01(EXPEDITION, CAPACITY), []), [row, setRow] = useState(0);
  const calculations = [[],
    ['f[1][3] = f[0][3] = 0', 'f[1][5] = max(f[0][5], f[0][1] + 7) = max(0, 0 + 7) = 7'],
    ['f[2][3] = max(f[1][3], f[1][0] + 5) = max(0, 0 + 5) = 5', 'f[2][5] = max(f[1][5], f[1][2] + 5) = max(7, 0 + 5) = 7'],
    ['f[3][5] = max(f[2][5], f[2][3] + 3) = max(7, 5 + 3) = 8'],
  ];
  return <section className="lab-initialization" aria-label="从初始值逐行计算">
    <h3>最早的答案从哪里来？</h3><p>先找不用计算就能确定的情况。本例总重量只需不超过容量，允许什么都不拿，而且每件重量都大于 0。</p>
    <dl className="lab-base-cases">
      <div><dt><code>f[0][0] = 0</code></dt><dd>没有物品，容量也是 0。唯一装法是空背包，价值为 0。</dd></div>
      <div><dt><code>f[0][c] = 0</code></dt><dd>没有物品，即使容量有 {CAPACITY} 格，也只能不拿。比如 <code>f[0][{CAPACITY}] = 0</code>。</dd></div>
      <div><dt><code>f[i][0] = 0</code></dt><dd>容量为 0，任何一件都放不下。比如 <code>f[1][0] = 0</code>：只允许 A，但 A 重 4 格，只能不拿。</dd></div>
    </dl>
    <p>这就是<b>初始化</b>：第 0 行和第 0 列可以直接填 0，依据来自题意。其他格子先留空，再用已知答案计算。</p>
    <div className="lab-table-scroll"><table className="lab-dp-table lab-initial-table"><caption className="sr-only">初始时仅第零行和第零列已知，其余格子待计算。点按钮逐行计算。</caption><thead><tr><th scope="col">允许使用</th>{table[0].map((_, c) => <th scope="col" key={c}>{c} 格</th>)}</tr></thead><tbody>{table.map((values, i) => <tr key={i}><th scope="row">{i === 0 ? '没有物品' : EXPEDITION.slice(0, i).map(item => item.id).join('、')}</th>{values.map((value, c) => <td key={c} data-known={i === 0 || c === 0 ? 'base' : i <= row ? 'computed' : 'pending'}>{i === 0 || c === 0 || i <= row ? value : '·'}</td>)}</tr>)}</tbody></table></div>
    <div className="lab-foundation-actions"><button type="button" className="lab-button" disabled={row === EXPEDITION.length} onClick={() => setRow(value => value + 1)}>计算第 {Math.min(row + 1, EXPEDITION.length)} 行</button><button type="button" className="lab-text-button" disabled={row === 0} onClick={() => setRow(0)}>重看起点</button></div>
    <div className="lab-initial-calculation" aria-live="polite">{row === 0 ? <p>这些 0 直接由题意确定，不需要再找“上一步”。接着读取第 1 条输入 A：重量 4，价值 7。</p> : <><p>第 {row} 行处理第 {row} 条输入：{EXPEDITION[row - 1].id}，重量 {EXPEDITION[row - 1].weight}，价值 {EXPEDITION[row - 1].value}。{row === 1 ? '容量 3 装不下 A，沿用第 0 行的 0；容量 5 装得下，再比较拿与不拿。' : '用到的每个 f 格子都在已算完的上一行。'}</p>{calculations[row].map(line => <code key={line}>{line}</code>)}</>}</div>
    <p>为什么能这样一行行算？第 0 行已由题意确定；新一行把所有合法装法分成“拿当前物品”和“不拿”两类，每类都用上一行的正确答案，取较大值就得到这一格的最优值。按第 0、1、2、3 行计算，就不会读到尚未算出的答案。</p>
  </section>;
}

export function RowReuseDemo() {
  const table = useMemo(() => table01(EXPEDITION, CAPACITY), []), [stage, setStage] = useState(0);
  const item = EXPEDITION[2], old = table[2], target = stage === 2 ? 4 : 5, source = target - item.weight;
  const values = old.map((value, c) => c === 5 || (stage === 2 && c === 4) ? table[3][c] : value);
  return <section className="lab-panel lab-row-reuse" aria-label="从两行到一行">
    <h3>先看清：每个容量各有自己的方案</h3>
    <p>沿用容量 {CAPACITY} 的背包：A 重 4、价值 7，B 重 3、价值 5，C 重 2、价值 3，每件最多一次。先看只允许 A、B 时已经算出的两个答案：</p>
    <div className="lab-independent-plans" aria-label="不同容量的独立方案">{[3, 5].map(c => <div key={c} data-capacity={c}><b>容量上限 {c}</b><code>f[2][{c}] = {old[c]}</code><BagSlots items={packingPlan(EXPEDITION.slice(0, 2), c)} capacity={c}/><span>{c === 3 ? '只拿 B，重量 3，价值 5。' : '只拿 A，重量 4，价值 7。'}</span></div>)}</div>
    <p>这两个答案同时保留，各自回答不同的问题。容量 5 的最优方案有 A，容量 3 的最优方案却是 B。</p>
    <h3>更新容量 5：比较两个完整方案的价值</h3>
    <p>接着读取 C（重量 2、价值 3）。保留原答案是 A，价值 7；另一个方案从容量 3 的答案 B 出发，加上 C，重量 3 + 2 = 5，价值 5 + 3 = 8。较大的 8 成为新答案。</p>
    <p>如果保留 A，确实放不下 C。但这里是用 B + C 替换 A；代码没有把 C 塞进装了 A 的背包。“不拿 C / 拿 C”指这两类候选方案，<code>max</code> 比较的是它们的价值。</p>
    <h3>从两行变成一行，旧答案还能读到吗？</h3>
    {stage === 0 ? <>
      <div className="lab-table-scroll"><table className="lab-dp-table lab-reuse-table"><thead><tr><th scope="col">容量上限 →</th>{old.map((_, c) => <th key={c}>{c}</th>)}</tr></thead><tbody><tr><th scope="row">旧行：只允许 A、B</th>{old.map((value, c) => <td key={c} data-focus={c === 5 || c === 3 ? 'source' : ''}>{value}</td>)}</tr><tr><th scope="row">新行：允许 A、B、C</th>{old.map((_, c) => <td key={c} data-focus={c === 5 ? 'target' : ''}>{c === 0 ? 0 : c === 5 ? table[3][5] : '·'}</td>)}</tr></tbody></table></div>
      <p><code>f[3][5] = max(f[2][5], f[2][3] + 3) = max(7, 5 + 3) = 8</code></p>
      <p>这个格子只读旧行的容量 5、容量 3。更早的“只允许 A”那一行用不到了，所以先只保留旧行和新行。</p>
    </> : <>
      <p>把旧行先放进数组 <code>dp[c]</code>，然后逐格写入新行。下面标“新”的位置已写入 C 这一轮的答案，标“旧”的仍是只允许 A、B 时的答案。</p>
      <div className="lab-array-scroll"><div className="lab-array" style={{ '--lab-cells': CAPACITY + 1 }}>{values.map((value, c) => <div key={c} className="lab-array-cell" data-focus={c === target ? 'target' : c === source ? 'source' : ''}><small>dp[{c}]</small><strong>{value}</strong><span>{c === 5 || (stage === 2 && c === 4) ? '新：允许 A、B、C' : '旧：只允许 A、B'}</span></div>)}</div></div>
      <p><code>dp[{target}] = max(dp[{target}], dp[{source}] + 3)</code></p>
      <p>读取更新前的数：<code>max({old[target]}, {old[source]} + 3) = {table[3][target]}</code>。只覆盖 <code>dp[{target}]</code>，<code>dp[{source}]</code> 仍保留旧行的 {old[source]}。</p>
      <p>{stage === 1 ? <>下一格算容量 4，只需旧的 <code>dp[4]</code> 和 <code>dp[2]</code>，不会再用旧的 <code>dp[5]</code>。所以容量 5 的旧位置可以直接覆盖。</> : <>再算容量 3 时，需要旧的 <code>dp[3]</code>、<code>dp[1]</code>，它们也都还没有被覆盖。</>}</p>
    </>}
    <div className="lab-foundation-actions"><button type="button" className="lab-button" onClick={() => setStage(value => (value + 1) % 3)}>{stage === 0 ? '把两行合并到 dp 数组' : stage === 1 ? '继续算容量 4' : '重看两行'}</button></div>
    {stage > 0 && <p>这就是倒序安全的原因：每次读取的是当前位置和更小的容量，先覆盖大容量，后面需要的小容量旧答案仍在。数组里虽然混有两轮答案，读到的来源始终是旧的一轮。</p>}
  </section>;
}
