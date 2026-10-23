import { useMemo, useRef, useState } from 'react';
import { EXPEDITION, EXPEDITION_CAPACITY as CAPACITY, EXPEDITION_OPTIMUM, packingPlan, table01 } from './knapsackModel.js';
import { BagSlots, ChoiceCheck, CodeBlock, NumberCheck } from './LabParts.jsx';
import { InitializationDemo } from './KnapsackFoundations.jsx';
import { KnapsackChoiceFilm } from './KnapsackMotion.jsx';

export function ExampleBrief() {
  return <div className="lab-example" aria-label="沿用上一节的例子">
    <p><b>还是上一节的背包</b><span>容量 {CAPACITY} 格 · 每件最多一次 · 不可拆分</span></p>
    <div>{EXPEDITION.map(item => <span key={item.id}><b>{item.id} {item.name}</b><small>重量 {item.weight} · 价值 {item.value}</small></span>)}</div>
  </div>;
}

const names = items => items.length ? items.map(item => item.id).join('、') : '没有物品';
const scope = items => items.length ? `只允许 ${names(items)}` : '没有可用物品';

function StateFormula({ i, c, available, earlier, item, remaining, skip, take, answer, unknown, sourceValue }) {
  return <details className="lab-formula-details" open><summary>把当前问题写成公式</summary><div className="lab-formula-content">
    <h3>当前问题：{scope(available)}，容量上限 {c} 格</h3>
    <p>给答案表取名 <code>f</code>，这个问题的答案就写成 <code>f[{i}][{c}]</code>。</p>
    <div className="lab-symbol-meaning"><p><code>i = {i}</code>：这一行允许使用{available.length ? ` ${names(available)}，共 ${i} 件` : ' 0 件物品'}。从中可以任意挑选，<b>i 不表示已经拿了几件。</b></p><p><code>c = {c}</code>：总重量不能超过 {c} 格。</p></div>
    <InitializationDemo/>
    {i === 0 ? <p>没有物品可拿，最大价值为 0，所以 <code>f[0][{c}] = 0</code>。表格第一行的数字都是这个意思。</p> : <>
      <h3>本行读取第 {i} 条输入：重量 {item.weight}，价值 {item.value}</h3>
      <p>这条记录的名字是 {item.id}。下面按“不拿这件”和“拿这件”比较价值，装不下的那类不参与比较；没有规定它必须先被放进背包。</p>
      <div className="lab-complete-equation" aria-label="当前格子的完整等式"><code>f[{i}][{c}] = {remaining < 0 ? `f[${i - 1}][${c}]` : `max(f[${i - 1}][${c}], f[${i - 1}][${remaining}] + ${item.value})`}</code><code>= {remaining < 0 ? skip : `max(${skip}, ${sourceValue} + ${item.value})`}{!unknown && remaining >= 0 && ` = ${answer}`}</code></div>
      <div className="lab-formula-parts">
        <div data-formula-branch="skip"><b>① 如果不拿 {item.id}</b><code>f[{i - 1}][{c}] = {skip}</code><span>{scope(earlier)}，容量仍是 {c} 格。</span></div>
        <div data-formula-branch="take"><b>② 如果拿 {item.id}</b>{remaining < 0 ? <span>{item.id} 重 {item.weight} 格，超过容量 {c}，这类装法不合法。</span> : <><code>f[{i - 1}][{remaining}] + {item.value} = {sourceValue} + {item.value}{!unknown && ` = ${take}`}</code><span>{item.id} 占 {item.weight} 格。剩余 {remaining} 格中，{earlier.length ? `仍只允许 ${names(earlier)}，其最大价值是 ${sourceValue}` : '没有其他物品可拿，价值为 0'}；再加 {item.id} 自己的价值 {item.value}。</span></>}</div>
      </div>
      <p>{take === null ? <>装不下这件物品，只能沿用 <code>f[{i - 1}][{c}]</code>。</> : <><code>max</code> 表示取两项中较大的价值，两张卡片就是等式右侧的两个候选值。</>}</p>
      <h3>把这次计算换成通用写法</h3>
      <p>第 <code>i</code> 条输入的重量记作 <code>w</code>，价值记作 <code>v</code>。本例 <code>w = {item.weight}</code>，<code>v = {item.value}</code>。</p>
      <p><code>i − 1 = {i - 1}</code> 对应{earlier.length ? `只允许 ${names(earlier)}` : '没有可用物品'}。{remaining >= 0 && <><code>c − w = {remaining}</code> 是拿 {item.id} 后留给其他物品的容量。</>}</p>
      <div className="lab-formula-parts"><div><b>不拿本步新增的物品</b><code>f[i - 1][c]</code><span>只用之前已经允许的物品，容量不变。</span></div><div><b>拿本步新增的物品</b><code>f[i - 1][c - w] + v</code><span>给它留出 w 格；剩余空间只用之前已经允许的物品，再加上它的价值。</span></div></div>
      <CodeBlock title="装得下时比较两类装法；装不下时只能不拿" code={'if (c >= w) {\n    f[i][c] = max(f[i - 1][c], f[i - 1][c - w] + v);\n} else {\n    f[i][c] = f[i - 1][c];\n}'}/>
      <p>每个格子只回答自己的物品范围、容量条件下的最大价值；使用答案时，要核对这两个条件。没有物品时，所有容量的最大价值都是 0。</p>
    </>}
  </div></details>;
}

export default function StateExperiment(props) {
  const table = useMemo(() => table01(EXPEDITION, CAPACITY), []);
  const [[i, c], setCell] = useState([1, CAPACITY]);
  const question = useRef(null);
  const available = EXPEDITION.slice(0, i), earlier = available.slice(0, -1), item = available.at(-1);
  const remaining = item ? c - item.weight : -1;
  const plan = packingPlan(available, c), skipPlan = packingPlan(earlier, c), takePlan = remaining >= 0 ? packingPlan(earlier, remaining) : [];
  const hidden = (row, col) => row === 3 && col === CAPACITY && !props.passed.transition;
  const unknown = hidden(i, c), skip = i ? table[i - 1][c] : 0, take = remaining >= 0 ? table[i - 1][remaining] + item.value : null;
  return <>
    <div className="lab-story"><h2>把大问题拆小，再记下答案。</h2><p>为不同物品范围、不同容量分别求最大价值。每个小问题各有自己的装法，之前某个答案用了 A，不代表其他问题也必须保留 A。</p></div>
    <section className="lab-panel lab-state-panel" aria-label="装包答案表">
      <ExampleBrief/>
      <p className="lab-input-order">A、B、C 只是输入记录的名字。按这个顺序计算，逐件保证最多用一次；程序用重量检查容量，用价值比较好坏。调换输入顺序，最终最大价值相同，计算的中间答案会不同。</p>
      <div className="lab-scope-steps" role="group" aria-label="逐步增加可选物品">{EXPEDITION.map((candidate, index) => <button key={candidate.id} type="button" aria-pressed={i === index + 1} onClick={() => setCell([index + 1, CAPACITY])}><span>{index + 1}</span>只允许 {names(EXPEDITION.slice(0, index + 1))}</button>)}</div>
      <div className="lab-cell-question lab-scope-focus" ref={question} tabIndex={-1}><h3>{scope(available)}，容量上限 {c} 格</h3>{item && <span>读取第 {i} 条输入</span>}</div>
      {i > 0 && <div className="lab-packing-breakdown">
          <p>第 {i} 条输入的重量是 {item.weight}，价值是 {item.value}。<b>所有合法装法，分成“拿这件”和“不拿这件”两类。</b></p>
          <div className="lab-packing-options">
            <div data-branch="skip"><h4>① 如果不拿 {item.id}</h4><p>{earlier.length ? `${names(earlier)} 仍然可选，容量还是 ${c} 格。${skipPlan.length ? `最好拿 ${names(skipPlan)}。` : '可以什么都不拿。'}` : '没有其他物品可拿，背包是空的。'}</p><BagSlots items={skipPlan} capacity={c}/><strong>价值 {skip}</strong></div>
            <div data-branch="take"><h4>② 如果拿 {item.id}</h4>{remaining < 0 ? <p>{item.id} 重 {item.weight} 格，超过 {c} 格，装不下。</p> : <><p>{item.id} 占 {item.weight} 格，剩余 {remaining} 格。{!earlier.length ? '没有其他物品可拿。' : takePlan.length ? `还能从 ${names(earlier)} 中拿 ${names(takePlan)}，价值 ${table[i - 1][remaining]}。` : `${earlier.map(old => `${old.id} 重 ${old.weight} 格`).join('、')}，都装不下，所以其他物品不拿。`}</p><BagSlots items={[...takePlan, item]} capacity={c}/><strong>价值 {table[i - 1][remaining]} + {item.value}{!unknown && ` = ${take}`}</strong></>}</div>
          </div>
      </div>}
      <div className="lab-cell-detail" aria-live="polite"><div className="lab-cell-question"><h3>{unknown ? '比较两类装法，把较大的价值填进 ?' : i === 0 ? '什么都不拿，价值为 0' : take === null ? `只能不拿 ${item.id}` : `比较 ${skip} 和 ${take}，保留较大的 ${table[i][c]}`}</h3><span>{unknown ? '最大价值：?' : `最大价值：${table[i][c]}`}</span></div><BagSlots items={unknown ? [] : plan} capacity={c} unknown={unknown}/>{!unknown && i > 0 && <p>最终装法：{plan.length ? `只拿 ${names(plan)}` : '什么都不拿'}。{i > 1 && !plan.some(pick => pick.id === 'A') && '这一次就没有拿 A。'}</p>}</div>
      <details className="lab-state-table"><summary>把这些答案记成表格</summary>
        <p className="lab-table-help">行里列出允许使用的物品，列头是容量上限，数字是最大价值。每个格子都重新比较装法。</p>
        <div className="lab-table-scroll"><table className="lab-dp-table">
          <caption className="sr-only">行表示允许使用的物品，不表示已经拿了这些物品。列表示容量上限，数字表示最大价值。点击查看对应装法。</caption>
          <thead><tr><th scope="col">允许使用 ↓</th>{table[0].map((_, col) => <th key={col} scope="col">{col} 格</th>)}</tr></thead>
          <tbody>{table.map((row, index) => <tr key={index}><th scope="row">{scope(EXPEDITION.slice(0, index))}</th>{row.map((value, col) => {
            const current = i === index && c === col;
            const source = i > 0 && index === i - 1 ? col === c ? 'skip' : col === remaining ? 'take' : '' : '';
            return <td key={col}><button type="button" aria-label={`可选${names(EXPEDITION.slice(0, index))}，容量 ${col} 格，${hidden(index, col) ? '待你推算' : `最大价值 ${value}`}`} aria-pressed={current} data-source={source} onClick={() => { setCell([index, col]); question.current?.scrollIntoView({ block: 'start' }); question.current?.focus({ preventScroll: true }); }}><strong>{hidden(index, col) ? '?' : value}</strong><small>{current ? '当前' : source === 'skip' ? '① 不拿' : source === 'take' ? '② 剩余' : '\u00a0'}</small></button></td>;
          })}</tr>)}</tbody>
        </table></div><p className="lab-caption">①、② 的格子分别提供上方两类装法中用到的答案。点任意格子，可在上方查看它的计算。</p>
      </details>
    </section>
    <ChoiceCheck id="state" title="允许使用 A、B 时，A 必须先拿吗？" choices={[
      { id: 'exact', label: '必须先拿 A，再用剩余空间考虑 B', feedback: '“只允许 A”是之前那个小问题的条件。现在允许 A、B，需要重新比较；拿 B 的方案可以不含 A。' },
      { id: 'prefix', label: 'A 可以不拿；只拿 A、只拿 B、都不拿都可以比较', feedback: '对。A、B 是允许使用的范围。容量 5 时只拿 A 最优；若容量只有 3，只拿 B 最优。A 并没有被提前固定在背包里。' },
      { id: 'weight', label: '必须把 A 和 B 都拿走', feedback: '允许使用不代表必须使用。而且 A、B 总重量 4 + 3 = 7，超过 5 格。' },
    ]} answer="prefix" {...props}/>
    <NumberCheck id="transition" title="补上「A、B、C / 5 格」" prompt="不拿第 3 件时，A、B 里最好只拿 A，价值 7。拿第 3 件时，它占 2 格，余下 3 格可拿 B，价值 5 + 3。最大价值是多少？" answer={EXPEDITION_OPTIMUM} explanation="最大价值是 8，装法为 B + C。这里比较的是装法的价值，输入顺序没有规定拿取先后。" wrong="比较不拿时的 7，与拿时的 5 + 3，保留较大的。" {...props} onPass={id => { props.onPass(id); setCell([3, CAPACITY]); }}/>
    {i > 0 && <KnapsackChoiceFilm key={`${i}:${c}:${unknown}`} capacity={c} focusIndex={i} conceal={unknown}/>}
    <StateFormula i={i} c={c} available={available} earlier={earlier} item={item} remaining={remaining} skip={skip} take={take} sourceValue={remaining >= 0 ? table[i - 1][remaining] : null} answer={table[i][c]} unknown={unknown}/>
  </>;
}
