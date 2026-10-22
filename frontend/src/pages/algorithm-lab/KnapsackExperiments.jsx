import { useEffect, useMemo, useState } from 'react';
import { ArrowDown, ArrowLeft, ArrowRight, Backpack, Check, Package, Pause, Play, RotateCcw, Radio, Flashlight, HeartPulse } from 'lucide-react';
import { EXPEDITION, displayValue, table01, traceKnapsack } from './knapsackModel.js';
import { ChoiceCheck, CodeBlock, Feedback, Hints, NumberCheck } from './LabParts.jsx';

export function PackingExperiment(props) {
  const { drafts, updateDraft, onPass } = props;
  const picked = Array.isArray(drafts.packItems) ? drafts.packItems.filter(id => EXPEDITION.some(item => item.id === id)) : [];
  const items = EXPEDITION.filter(item => picked.includes(item.id)), weight = items.reduce((sum, item) => sum + item.weight, 0), value = items.reduce((sum, item) => sum + item.value, 0);
  const [feedback, setFeedback] = useState(''), icons = [Radio, Flashlight, HeartPulse], good = weight <= 4 && value === 6;
  return <>
    <div className="lab-story"><span className="lab-eyebrow">任务 001 · 出发之前</span><h2>背包只有 4 格，<br/>你会带走什么？</h2><p>三件装备各只有一件，不能拆开。让总重量不超过 4，并让总价值尽可能大。先凭直觉试试。</p></div>
    <div className="lab-pack-layout"><div className="lab-equipment" aria-label="可选装备">{EXPEDITION.map((item, i) => { const Icon = icons[i]; return <button type="button" key={item.id} className="lab-item" aria-pressed={picked.includes(item.id)} onClick={() => { updateDraft('packItems', picked.includes(item.id) ? picked.filter(id => id !== item.id) : [...picked, item.id]); setFeedback(''); }}><span className="lab-item-icon"><Icon size={29}/></span><span><small>装备 {item.id}</small><strong>{item.name}</strong><span>重量 {item.weight} · 价值 {item.value}</span></span><span className="lab-item-toggle">{picked.includes(item.id) ? <Check size={16}/> : '+'}</span></button>; })}</div>
      <div className={`lab-bag ${weight > 4 ? 'lab-bag-overflow' : ''}`}><div className="lab-bag-top"><Backpack size={23}/><span>你的背包</span><b>{weight} / 4 格</b></div><div className="lab-bag-slots" aria-label={`已占用 ${weight} 格，容量 4`}>{Array.from({ length: Math.max(4, weight) }, (_, i) => { let offset = 0; const item = items.find(candidate => { offset += candidate.weight; return i < offset; }); return <span key={i} data-item={item?.id || ''}>{item?.id || '·'}</span>; })}</div><div className="lab-pack-value"><span>当前总价值</span><strong>{value}<small>点</small></strong></div><button type="button" className="lab-button" onClick={() => { if (good) { onPass('pack'); setFeedback('装得下，而且最优！两件 2 格的装备，组合价值 3+3=6，胜过只拿对讲机的 5。你已经击败了“先拿价值最大”和“先拿性价比最高”这两种直觉。'); } else setFeedback(weight > 4 ? '超出容量了。价值再高，装不下也不是合法方案。试着取出一件。' : '这是合法方案。还有更高价值的组合吗？不妨暂时取出对讲机，把两件小装备放在一起。'); }}>检查我的方案<ArrowRight size={15}/></button></div></div>
    {feedback && <Feedback good={good}>{feedback}</Feedback>}
    <Hints id="packing" items={['对讲机的价值最高，性价比 5/3 也高于另两件的 3/2。但它会剩下 1 格。', '比较“只拿 A”和“同时拿 B、C”。物品不能拆开，剩余空间可能决定结果。']} {...props}/>
    <ChoiceCheck id="greedy" title="为什么不能一直挑性价比最高的？" choices={[
      { id: 'ratio', label: '因为性价比算错了', feedback: '5/3 确实大于 3/2。计算没有错，局部选择却会影响之后能装什么。' },
      { id: 'combination', label: '整件选择会占住容量，要比较组合', feedback: '对。选了哪件，会改变后面的选择空间。我们需要系统比较“选”和“不选”两条路，而不是只押一条路。' },
      { id: 'small', label: '以后总选重量最小的就行', feedback: '也不能保证。若容量 3，物品为 (1,1)、(3,100)，先拿小件就会错过价值 100。' },
    ]} answer="combination" {...props}/>
    <div className="lab-note"><Package size={20}/><p><b>每件只有“不拿”和“拿一次”两种选择，所以叫 0/1 背包。</b>能不能把所有组合都试一遍？可以，3 件只有 2³=8 种选法。但 100 件就有 2¹⁰⁰ 种。下一步，我们找出哪些重复的小问题可以只算一次。</p></div>
  </>;
}

export function StateExperiment(props) {
  const table = useMemo(() => table01(EXPEDITION, 4), []), [[i, c], setCell] = useState([2, 4]);
  const item = EXPEDITION[i - 1], previous = Math.max(0, i - 1), source = item ? c - item.weight : -1;
  const hidden = (row, col) => row === 3 && col === 4 && !props.passed.transition;
  return <>
    <div className="lab-story"><span className="lab-eyebrow">从“所有组合”到“同一个小问题”</span><h2>只记住以后还会用到的答案。</h2><p>先只允许选前几件物品，再分别问：如果背包容量是 0、1、2、3、4，最多能拿多少价值？相同的小问题只算一次，存进表格。这就是动态规划（DP）的出发点。</p></div>
    <div className="lab-state-definition"><span>我们约定</span><code>f[i][c]</code><p>只考虑<b>前 i 件物品</b>，总重量<b>不超过 c</b>时的最大价值。</p><small>i 是“允许考虑几件”，c 是“容量上限”，都不是必须拿到的数量。</small></div>
    <ChoiceCheck id="state" title="f[2][4] 这句话到底在问什么？" choices={[
      { id: 'exact', label: '必须拿 2 件，并且正好装满 4 格', feedback: '两个“必须”都没有出现在定义里。前 2 件是可选范围，4 是容量上限。' },
      { id: 'prefix', label: '只从 A、B 中选，总重量不超过 4 的最大价值', feedback: '正确！可以不选，也可以只选一件。状态含义决定初始化、转移以及最后读哪个格子。' },
      { id: 'weight', label: '选完所有物品后，重量恰好为 2 的价值', feedback: 'i 表示考虑前几件，c 才是容量。先把这两个轴分清楚。' },
    ]} answer="prefix" {...props}/>
    <div className="lab-panel"><div className="lab-panel-title"><h3>点一个格子，拆开它的来路</h3><small>行：可选范围 · 列：容量上限</small></div><div className="lab-table-scroll"><table className="lab-dp-table"><caption className="sr-only">0/1 背包二维状态表，点击格子查看选或不选的来源</caption><thead><tr><th scope="col">可选物品 ＼ c</th>{table[0].map((_, col) => <th key={col} scope="col">{col}</th>)}</tr></thead><tbody>{table.map((row, index) => <tr key={index}><th scope="row">{index === 0 ? '0 件 · 什么都没有' : `前 ${index} 件 · ${EXPEDITION.slice(0, index).map(item => item.id).join(' ')}`}</th>{row.map((value, col) => <td key={col}><button type="button" aria-label={`前 ${index} 件，容量 ${col}${hidden(index, col) ? '，待你推算' : `，价值 ${value}`}`} aria-pressed={i === index && c === col} data-source={i > 0 && index === previous && (col === c ? 'skip' : col === source ? 'take' : '') || ''} onClick={() => setCell([index, col])}>{hidden(index, col) ? '?' : value}</button></td>)}</tr>)}</tbody></table></div>
      {i === 0 ? <Feedback good>没有物品时，可以什么都不选。无论容量上限是多少，最大价值都是 0。这解释了第 0 行的初始化。</Feedback> : <div className="lab-transition"><div><small>不选 {item.id}</small><code>f[{i - 1}][{c}] = {table[i - 1][c]}</code><p>原来的最优方案照样合法。</p></div><span>或</span><div><small>选 {item.id}（重量 {item.weight}，价值 {item.value}）</small>{source < 0 ? <p>装不下，这条路不能走。</p> : <><code>f[{i - 1}][{source}] + {item.value} = {table[i - 1][source] + item.value}</code><p>先给它留 {item.weight} 格；剩下的 {source} 格，只能从前 {i - 1} 件中选。</p></>}</div></div>}
      <div className="lab-formula"><ArrowDown size={17}/><span>{i === 0 ? 'f[0][c] = 0' : c < item.weight ? '装不下：继承上一行' : '两种选择覆盖所有合法方案：取其中较大值'}</span></div>
    </div>
    <CodeBlock title="把“选 / 不选”翻译成式子" code={'// 第 i 件物品重量 w、价值 v；c >= w 时\nf[i][c] = max(f[i - 1][c], f[i - 1][c - w] + v);\n// 若 c < w，只能不选\nf[i][c] = f[i - 1][c];'}/>
    <NumberCheck id="transition" title="由你补上最后一个格子" prompt="只考虑 A、B、C，容量上限为 4：不选 C 时是 5；选 C 时，前两件在剩余 2 格中最多得到 3。f[3][4] 应该是多少？" answer={table[3][4]} explanation="max(5, 3+3)=6。两条路都从上一行出发，因此不会把 C 选两次。" wrong="选 C 这条路还要加上 C 自己的价值 3，再和不选时的 5 比较。" {...props}/>
    <p className="lab-caption">为什么只留每格的最优值？固定了可选范围和剩余容量，之后能做的选择完全相同；价值更低的旧方案不会在未来反超。这样的状态才足以支撑转移。</p>
  </>;
}

function TracePlayer({ items, capacity, direction }) {
  const model = useMemo(() => traceKnapsack(items, capacity, direction), [items, capacity, direction]);
  const [step, setStep] = useState(0), [playing, setPlaying] = useState(false), [speed, setSpeed] = useState(1100);
  const frame = step ? model.frames[step - 1] : null, values = frame?.after || Array(capacity + 1).fill(0), done = step === model.frames.length;
  useEffect(() => {
    if (!playing || done) return;
    const timer = setTimeout(() => setStep(value => Math.min(value + 1, model.frames.length)), speed);
    return () => clearTimeout(timer);
  }, [playing, step, done, speed, model]);
  useEffect(() => { const hide = () => { if (document.hidden) setPlaying(false); }; document.addEventListener('visibilitychange', hide); return () => document.removeEventListener('visibilitychange', hide); }, []);
  const changeStep = value => { setPlaying(false); setStep(value); };
  return <div className="lab-panel lab-trace" aria-label="一维背包执行器">
    <div className="lab-panel-title"><h3>一行数组，两种时间</h3><span>{step} / {model.frames.length} 次更新</span></div>
    <div className="lab-trace-items">{items.map((item, i) => <span key={item.id} data-current={frame?.i === i}>{item.id} · 重量 {item.weight} / 价值 {item.value}</span>)}</div>
    <div className="lab-array-scroll"><div className="lab-array" style={{ '--lab-cells': capacity + 1 }}>{values.map((value, c) => <div className="lab-array-cell" key={c} data-focus={frame?.c === c ? 'target' : frame?.source === c ? 'source' : ''}><small>c = {c}</small><strong>{value}</strong><span>{frame?.c === c ? '写入此格' : frame?.source === c ? '读取来源' : '\u00a0'}</span></div>)}</div></div>
    <div className="lab-trace-explanation" aria-live="polite">{!frame ? <p>所有 dp[c] 初始为 0：容量只是上限，什么都不拿也合法。点“下一步”，开始处理第一件物品。</p> : <><div className="lab-trace-equation"><code>dp[{frame.c}] ← max({frame.skip}, {frame.before[frame.source]} + {frame.item.value}) = {frame.result}</code></div><p>正在处理 {frame.item.id}：读取 <b>dp[{frame.source}] = {frame.before[frame.source]}</b>（{frame.sourceFresh ? '本轮已经更新过' : '本轮尚未更新，仍是上一轮的值'}），{frame.improved ? '选择加入当前物品。' : '保留原来的方案。'}</p>{frame.improved && frame.repeated ? <Feedback>来源方案已经包含 {frame.item.id}，现在又加入 {frame.item.id}。同一件被使用了两次！若每种只有一件，这就是错误；若允许无限件，这次转移才合法。</Feedback> : <p className="lab-caption">本格保留的方案：{frame.choices[frame.c].length ? frame.choices[frame.c].map(index => items[index].id).join(' + ') : '空方案'}。{direction === 'down' ? '大容量先算，较小的来源容量还没有处理到。' : '小容量先算，之后可能读到本轮的新结果。'}</p>}</>}{done && <p className="lab-trace-finish">{model.frames.length ? '本次推演结束。' : '所有物品都装不下，没有合法的更新位置。'}容量上限 {capacity} 的结果是 <b>{values[capacity]}</b>。</p>}</div>
    <ol className="lab-running-code" aria-label="当前执行的 C++ 转移代码"><li>for (int i = 0; i &lt; n; ++i) {'{'}</li><li data-active={!!frame}>{direction === 'down' ? '    for (int c = W; c >= w[i]; --c)' : '    for (int c = w[i]; c <= W; ++c)'}</li><li data-active={!!frame}>{'        dp[c] = max(dp[c], dp[c - w[i]] + v[i]);'}</li><li>{'}'}</li></ol>
    <div className="lab-player"><button type="button" className="lab-icon-button" aria-label="重置推演" onClick={() => changeStep(0)}><RotateCcw size={17}/></button><button type="button" className="lab-icon-button" aria-label="上一步" disabled={!step} onClick={() => changeStep(step - 1)}><ArrowLeft size={17}/></button><button type="button" className="lab-button" disabled={done} onClick={() => setPlaying(value => !value)}>{playing && !done ? <Pause size={15}/> : <Play size={15}/>} {playing && !done ? '暂停' : '播放'}</button><button type="button" className="lab-button lab-button-quiet" disabled={done} onClick={() => changeStep(step + 1)}>下一步<ArrowRight size={15}/></button><label className="lab-speed">速度<select aria-label="推演速度" value={speed} onChange={event => setSpeed(Number(event.target.value))}><option value={1700}>慢</option><option value={1100}>中</option><option value={550}>快</option></select></label></div>
    <label className="lab-scrubber"><span>执行位置</span><input type="range" min="0" max={model.frames.length} value={step} onChange={event => changeStep(Number(event.target.value))}/><output>{step}</output></label>
  </div>;
}

const DEFAULT_TRACE = { capacity: 4, items: EXPEDITION };
function validTrace(value) { return value && Number.isInteger(value.capacity) && value.capacity >= 0 && value.capacity <= 12 && Array.isArray(value.items) && value.items.length >= 1 && value.items.length <= 4 && value.items.every(item => item && typeof item.id === 'string' && Number.isInteger(item.weight) && item.weight >= 1 && item.weight <= 12 && Number.isInteger(item.value) && item.value >= 0 && item.value <= 99); }

export function TraceExperiment(props) {
  const { drafts, updateDraft } = props, config = validTrace(drafts.traceConfig) ? drafts.traceConfig : DEFAULT_TRACE;
  const direction = drafts.traceDirection === 'up' ? 'up' : 'down', [edit, setEdit] = useState(config), [error, setError] = useState('');
  const chooseConfig = value => { updateDraft('traceConfig', value); setEdit(value); setError(''); };
  return <>
    <div className="lab-story"><span className="lab-eyebrow">少一维，保留每件一次的约束</span><h2>循环方向，<br/>决定读到哪一轮。</h2><p>二维转移只读取上一行，所以可以把空间从 O(nW) 压成 O(W)。但在同一个数组上更新时，有的格子已经属于本轮，有的还停在上一轮。循环方向决定你会读到哪一个。</p></div>
    <div className="lab-experiment-toolbar"><div className="lab-segmented" role="group" aria-label="推演数据"><button type="button" aria-pressed={config.items.length === 3} onClick={() => chooseConfig(DEFAULT_TRACE)}>课堂背包</button><button type="button" aria-pressed={config.items.length === 1 && config.items[0].weight === 2 && config.capacity === 4 && config.items[0].value === 3} onClick={() => chooseConfig({ capacity: 4, items: [{ id: 'A', name: '一件物品', weight: 2, value: 3 }] })}>一件物品的反例</button></div><div className="lab-segmented" role="group" aria-label="容量遍历方向"><button type="button" aria-pressed={direction === 'down'} onClick={() => updateDraft('traceDirection', 'down')}>倒序 · W → w</button><button type="button" aria-pressed={direction === 'up'} onClick={() => updateDraft('traceDirection', 'up')}>正序 · w → W</button></div></div>
    <TracePlayer key={JSON.stringify(config) + direction} {...config} direction={direction}/>
    <details className="lab-custom"><summary>自己改一组数据，再看它运行</summary><form onSubmit={event => { event.preventDefault(); if (validTrace(edit)) chooseConfig(edit); else setError('容量取 0–12，重量取 1–12，价值取 0–99；所有数都要是整数。'); }}><label>容量上限<input aria-label="自定义背包容量" type="number" required min="0" max="12" step="1" value={edit.capacity} onChange={event => setEdit(value => ({ ...value, capacity: event.target.value === '' ? '' : Number(event.target.value) }))}/></label>{edit.items.map((item, index) => <div className="lab-custom-item" key={index}><b>物品 {item.id}</b>{['weight', 'value'].map(key => <label key={key}>{key === 'weight' ? '重量' : '价值'}<input aria-label={`物品 ${item.id} 的${key === 'weight' ? '重量' : '价值'}`} type="number" required min={key === 'weight' ? 1 : 0} max={key === 'weight' ? 12 : 99} step="1" value={item[key]} onChange={event => setEdit(value => ({ ...value, items: value.items.map((old, i) => i === index ? { ...old, [key]: event.target.value === '' ? '' : Number(event.target.value) } : old) }))}/></label>)}</div>)}<div className="lab-player"><button className="lab-button" type="submit">应用数据</button><button className="lab-text-button" type="button" disabled={edit.items.length >= 4} onClick={() => setEdit(value => ({ ...value, items: [...value.items, { id: String.fromCharCode(65 + value.items.length), weight: 1, value: 1 }] }))}>增加物品</button><button className="lab-text-button" type="button" disabled={edit.items.length <= 1} onClick={() => setEdit(value => ({ ...value, items: value.items.slice(0, -1) }))}>减少物品</button></div>{error && <p role="alert">{error}</p>}</form></details>
    <ChoiceCheck id="loop" title="每件物品只能选一次，容量应该怎样遍历？" choices={[
      { id: 'down', label: '从大到小，让较小的来源容量还属于上一轮', feedback: '对。c−w 比 c 小；倒序到达 c 时，dp[c−w] 还没有使用当前物品更新。它不可能已经包含当前物品。' },
      { id: 'up', label: '从小到大，方便一直把价值累加上去', feedback: '小容量先更新后，大容量就可能用它再加一件当前物品。切到“一件物品的反例”，正序播放看看。' },
    ]} answer="down" {...props}/>
    <NumberCheck id="repeat" title="你能预言这个错误吗？" prompt="只有一件物品：重量 2、价值 3，容量上限 4。如果错误地正序更新，dp[4] 最后会变成多少？" answer={6} explanation="dp[2] 先变成 3，dp[4] 再读它并加 3，得到 6。同一件用两次。允许无限件时这正是完全背包的转移，但它不符合本题每件一次的限制。" wrong="先算 c=2：dp[2]=3。再算 c=4：此时读到的 dp[2] 已经不是初始的 0。" {...props}/>
    <p className="lab-caption">教学执行器按上方固定 C++ 语句逐步计算，支持回退与改数据。完整代码的编译、运行和原站提交在做题工作台中完成。</p>
  </>;
}
