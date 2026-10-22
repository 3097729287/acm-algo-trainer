import { useMemo, useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { EXPEDITION, packingPlan, table01 } from './knapsackModel.js';
import { BagSlots, ChoiceCheck, CodeBlock, NumberCheck } from './LabParts.jsx';

export function ExampleBrief() {
  return <div className="lab-example" aria-label="沿用上一节的例子">
    <p><b>还是上一节的背包</b><span>容量 4 格 · 每件最多一次 · 不可拆分</span></p>
    <div>{EXPEDITION.map(item => <span key={item.id}><b>{item.id} {item.name}</b><small>重量 {item.weight} · 价值 {item.value}</small></span>)}</div>
  </div>;
}

const names = items => items.length ? items.map(item => item.id).join('、') : '没有物品';

export default function StateExperiment(props) {
  const table = useMemo(() => table01(EXPEDITION, 4), []);
  const [[i, c], setCell] = useState([2, 4]), [explain, setExplain] = useState(false);
  const available = EXPEDITION.slice(0, i), earlier = available.slice(0, -1), item = available.at(-1);
  const remaining = item ? c - item.weight : -1;
  const plan = packingPlan(available, c), skipPlan = packingPlan(earlier, c), takePlan = remaining >= 0 ? packingPlan(earlier, remaining) : [];
  const hidden = (row, col) => row === 3 && col === 4 && !props.passed.transition;
  const unknown = hidden(i, c), skip = i ? table[i - 1][c] : 0, take = remaining >= 0 ? table[i - 1][remaining] + item.value : null;
  return <>
    <div className="lab-story"><h2>把装包的答案，记进表格。</h2><p>先问小一点的问题：只给部分物品，或把背包缩小，最好能装出多少价值？把答案记下来，后面就可以直接用。</p></div>
    <section className="lab-panel lab-state-panel" aria-label="装包答案表">
      <ExampleBrief/>
      <div className="lab-panel-title"><h3>每个格子，都是一个装包问题</h3></div>
      <p className="lab-table-help">行决定能选哪些物品，列决定容量上限。点格子，查看装法；数字是最大价值。</p>
      <div className="lab-table-scroll"><table className="lab-dp-table">
        <caption className="sr-only">沿用容量 4、A B C 各一件的例子。行是可选物品，列是容量上限，数字是最大价值。</caption>
        <thead><tr><th scope="col">可选物品 ↓</th>{table[0].map((_, col) => <th key={col} scope="col">{col} 格</th>)}</tr></thead>
        <tbody>{table.map((row, index) => <tr key={index}><th scope="row">{names(EXPEDITION.slice(0, index))}</th>{row.map((value, col) => {
          const current = i === index && c === col;
          const source = explain && i > 0 && index === i - 1 ? col === c ? 'skip' : col === remaining ? 'take' : '' : '';
          return <td key={col}><button type="button" aria-label={`可选${names(EXPEDITION.slice(0, index))}，容量 ${col} 格，${hidden(index, col) ? '待你推算' : `最大价值 ${value}`}`} aria-pressed={current} data-source={source} onClick={() => setCell([index, col])}><strong>{hidden(index, col) ? '?' : value}</strong><small>{current ? '当前' : source === 'skip' ? '① 不拿' : source === 'take' ? '② 剩余' : '\u00a0'}</small></button></td>;
        })}</tr>)}</tbody>
      </table></div>
      <div className="lab-cell-detail" aria-live="polite">
        <div className="lab-cell-question"><h3>{i ? `只从 ${names(available)} 中选，重量不超过 ${c} 格` : `没有物品，容量上限 ${c} 格`}</h3><span>{unknown ? '最大价值：?' : `最大价值：${table[i][c]}`}</span></div>
        <BagSlots items={unknown ? [] : plan} capacity={c} unknown={unknown}/>
        {!unknown && <p>{plan.length ? `一种最优装法：${plan.map(pick => pick.name).join(' + ')}。` : '什么都不拿，价值为 0。'}{i > 0 && '不必把物品全拿走，也不必装满。'}</p>}
      </div>
      {i > 0 && <>
        <button className="lab-text-button lab-breakdown-toggle" type="button" aria-expanded={explain} aria-controls="lab-packing-breakdown" onClick={() => setExplain(value => !value)}>{explain ? '收起计算过程' : '这个答案怎么算？'}<ChevronDown size={15}/></button>
        {explain && <div id="lab-packing-breakdown" className="lab-packing-breakdown">
          <p>处理最后一件 <b>{item.id} {item.name}</b>，只有两种选择。上表的 ①、② 标出了要用的旧答案。</p>
          <div className="lab-packing-options">
            <div data-branch="skip"><h4>① 不拿 {item.id}</h4><p>{c} 格全部留给{earlier.length ? ` ${names(earlier)}` : '空方案'}。</p><BagSlots items={skipPlan} capacity={c}/><strong>价值 {skip}</strong></div>
            <div data-branch="take"><h4>② 拿 {item.id}</h4>{remaining < 0 ? <p>{item.id} 重 {item.weight} 格，超过 {c} 格，装不下。</p> : <><p>{item.id} 占 {item.weight} 格，剩余 {remaining} 格只从{earlier.length ? ` ${names(earlier)} 中选` : '空方案得到 0'}。</p><BagSlots items={[...takePlan, item]} capacity={c}/><strong>价值 {table[i - 1][remaining]} + {item.value}{!unknown && ` = ${take}`}</strong></>}</div>
          </div>
          <p className="lab-comparison">{unknown ? '比较两种装法的价值，把较大的填进 ?。' : take === null ? `只能不拿 ${item.id}，所以记下 ${skip}。` : `比较 ${skip} 和 ${take}，记下较大的 ${table[i][c]}。`}</p>
        </div>}
      </>}
    </section>
    <ChoiceCheck id="state" title="表中「A、B / 4 格」的 5 表示什么？" choices={[
      { id: 'exact', label: '必须拿 A、B，并且正好装满 4 格', feedback: '这一行只是可选范围。A、B 一起拿重 5 格，超过了容量。' },
      { id: 'prefix', label: '只从 A、B 中选，重量不超过 4 时的最大价值', feedback: '对。此时只拿 A，重量 3、价值 5，剩 1 格也合法。' },
      { id: 'weight', label: '已经装了 4 格，物品总重量是 5', feedback: '表内记的是最大价值，容量上限写在列头。' },
    ]} answer="prefix" {...props}/>
    <NumberCheck id="transition" title="补上「A、B、C / 4 格」" prompt="不拿 C：从 A、B 中选，最好是 5。拿 C：先占 2 格，剩下 2 格可拿 B，得到 3 + 3。该把哪个价值记进表格？" answer={6} explanation="记下 6：拿 B 和 C，总重量 4，总价值 6。两条路都只在 A、B 中找旧答案，所以 C 只用了一次。" wrong="比较不拿 C 的 5，与拿 C 后的 3 + 3，保留较大的。" {...props} onPass={id => { props.onPass(id); setCell([3, 4]); setExplain(true); }}/>
    <details className="lab-formula-details"><summary>最后，把刚才的过程写成公式</summary>
      <div className="lab-formula-content">
        <h3>先给表格取一个名字：f</h3><p><code>f[2][4] = 5</code> 就是刚才「A、B / 4 格」的格子：<b>只从前 2 件物品中选，重量不超过 4，最大价值是 5。</b></p>
        <p>把具体数字换成变量：<code>i</code> 是可选的前几件，<code>c</code> 是容量上限。<code>f[i][c]</code> 就是这一个格子的答案。</p>
        <h3>把“拿 B / 不拿 B”写出来</h3>
        <div className="lab-formula-parts"><div><b>不拿 B</b><code>f[1][4] = 5</code><span>只从 A 中选，容量还是 4。</span></div><div><b>拿 B</b><code>f[1][2] + 3 = 3</code><span>B 占 2 格；剩 2 格从 A 中选，再加 B 的价值 3。</span></div></div>
        <p><code>max(5, 3)</code> 表示取两者中较大的数，所以 <code>f[2][4] = 5</code>。</p>
        <h3>同样的办法，处理第 i 件</h3>
        <p>这一件重量叫 <code>w</code>，价值叫 <code>v</code>。<code>i − 1</code> 表示前面的物品，<code>c − w</code> 表示拿它后剩下的容量。</p>
        <div className="lab-formula-parts"><div><b>不拿这一件</b><code>f[i - 1][c]</code><span>可选物品少一件，容量不变。</span></div><div><b>拿这一件</b><code>f[i - 1][c - w] + v</code><span>先留出它的重量，再把它的价值加回来。</span></div></div>
        <CodeBlock title="装得下时比较两种选择；装不下时只能不拿" code={'if (c >= w) {\n    f[i][c] = max(f[i - 1][c], f[i - 1][c - w] + v);\n} else {\n    f[i][c] = f[i - 1][c];\n}'}/>
        <p>没有物品时，每种容量的最大价值都是 0，所以表格第 0 行全为 0。逐行算完后，<code>f[3][4]</code> 就是开头那只背包的答案。</p>
      </div>
    </details>
  </>;
}
