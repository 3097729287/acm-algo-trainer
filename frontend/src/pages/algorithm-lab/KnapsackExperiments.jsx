import { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, Pause, Play, RotateCcw } from 'lucide-react';
import { EXPEDITION, EXPEDITION_CAPACITY, traceKnapsack } from './knapsackModel.js';
import { ChoiceCheck, Feedback, NumberCheck } from './LabParts.jsx';
import { RowReuseDemo } from './KnapsackFoundations.jsx';

function TracePlayer({ items, capacity, direction }) {
  const model = useMemo(() => traceKnapsack(items, capacity, direction), [items, capacity, direction]);
  const array = useRef(null);
  const [step, setStep] = useState(0), [playing, setPlaying] = useState(false), [speed, setSpeed] = useState(1100);
  const frame = step ? model.frames[step - 1] : null, values = frame?.after || Array(capacity + 1).fill(0), done = step === model.frames.length;
  useEffect(() => {
    if (!playing || done) return;
    const timer = setTimeout(() => setStep(value => Math.min(value + 1, model.frames.length)), speed);
    return () => clearTimeout(timer);
  }, [playing, step, done, speed, model]);
  useEffect(() => { const hide = () => { if (document.hidden) setPlaying(false); }; document.addEventListener('visibilitychange', hide); return () => document.removeEventListener('visibilitychange', hide); }, []);
  useEffect(() => {
    const container = array.current;
    if (!container || !frame) return;
    const target = container.querySelector('[data-focus=target]'), source = container.querySelector('[data-focus=source]');
    if (!target || !source) return;
    const left = Math.min(target.offsetLeft, source.offsetLeft);
    const right = Math.max(target.offsetLeft + target.offsetWidth, source.offsetLeft + source.offsetWidth);
    if (right - left <= container.clientWidth) container.scrollLeft = Math.max(0, right - container.clientWidth + 2);
    else container.scrollLeft = target.offsetLeft;
  }, [frame]);
  const changeStep = value => { setPlaying(false); setStep(value); };
  const planName = picks => picks.length ? picks.map(index => items[index].id).join(' + ') : '空背包';
  return <div className="lab-panel lab-trace" aria-label="一维背包执行器">
    <div className="lab-panel-title"><h3>逐格更新 dp 数组</h3><span>{step} / {model.frames.length} 次更新</span></div>
    <p className="lab-trace-conditions">当前容量 {capacity}，物品共 {items.length} 件，每件最多一次。代码的 W 是容量，w[i]、v[i] 是第 i 条输入的重量、价值；这里从 1 编号。</p>
    <div className="lab-trace-items">{items.map((item, i) => <div key={item.id} data-current={frame?.i === i}><b>{item.id}</b><span>重量 <code>w[{i + 1}] = {item.weight}</code></span><span className="lab-item-value" data-active={frame?.i === i}>价值 <code>v[{i + 1}] = {item.value}</code>{frame?.i === i && <small>参与本步比较</small>}</span></div>)}</div>
    <p className="lab-caption">每个格子对应一个容量上限，各自保存最大价值。数字下方附上对应的一种装法。</p>
    <div className="lab-array-scroll" ref={array}><div className="lab-array" style={{ '--lab-cells': capacity + 1 }}>{values.map((value, c) => <div className="lab-array-cell" key={c} data-capacity={c} data-focus={frame?.c === c ? 'target' : frame?.source === c ? 'source' : ''}><small>dp[{c}]</small><strong>{value}</strong><span className="lab-array-plan">{frame ? planName(frame.choices[c]) : '空背包'}</span><span>{frame?.c === c ? '写入比较结果' : frame?.source === c ? '读取来源答案' : '\u00a0'}</span><em>{!frame ? '未处理物品' : c >= frame.item.weight && (direction === 'down' ? c >= frame.c : c <= frame.c) ? '本轮已更新' : '仍是上一轮'}</em></div>)}</div></div>
    <div className="lab-trace-explanation" aria-live="polite">{!frame ? <p>dp 起初存的是第 0 行：还没有处理任何物品，所有容量的最大价值都是 0。点“下一步”，读取第 1 条物品数据。</p> : <>
      <div className="lab-trace-equation"><code><span className="lab-term-target">dp[{frame.c}]</span> ← max(dp[{frame.c}], <span className="lab-term-source">dp[{frame.source}]</span> + <span className="lab-term-value">v[{frame.i + 1}]</span>)</code></div>
      <div className="lab-trace-candidates" aria-label="写入前比较的两个价值">
        <div data-candidate="keep"><b>保留原答案</b><code>dp[{frame.c}] = {frame.skip}</code><span>容量 {frame.c} 的原方案：{planName(frame.skipChoices)}。</span></div>
        <div data-candidate="add"><b>来源答案 + {frame.item.id} 的价值</b><code><span className="lab-term-source">dp[{frame.source}]</span> + <span className="lab-term-value">v[{frame.i + 1}]</span> = <span className="lab-term-source">{frame.before[frame.source]}</span> + <span className="lab-term-value">{frame.item.value}</span> = {frame.take}</code><span>来源方案 {planName(frame.sourceChoices)}，加上 {frame.item.id}。给它留出 {frame.item.weight} 格，来源容量是 {frame.c} − {frame.item.weight} = {frame.source}。</span></div>
      </div>
      <p className="lab-trace-values">比较 <code>max({frame.skip}, {frame.before[frame.source]} + {frame.item.value}) = {frame.result}</code>，把 {frame.result} 写入 <code>dp[{frame.c}]</code>。上方格子显示写入后的数值，卡片显示读取时的数值。</p>
      <p>来源 <b>dp[{frame.source}]</b> {frame.sourceFresh ? '本轮已经更新过，读到的是新值' : '本轮尚未更新，读到的仍是上一轮的旧值'}。</p>
      {frame.improved && frame.repeated ? <Feedback>来源方案已经包含 {frame.item.id}，现在又加入 {frame.item.id}。同一件被使用了两次！本题每件最多一次，这个结果不合法。</Feedback> : <p className="lab-caption">本格保留的方案：{frame.choices[frame.c].length ? frame.choices[frame.c].map(index => items[index].id).join(' + ') : '空方案'}。{direction === 'down' ? '先覆盖较大的格子，较小的来源仍是旧答案。' : '小容量先被覆盖，后面可能读到已经使用本件的新答案。'}</p>}
    </>}{done && <p className="lab-trace-finish">{model.frames.length ? '本次推演结束。' : '所有物品都装不下，没有合法的更新位置。'}容量上限 {capacity} 的结果是 <b>{values[capacity]}</b>。</p>}</div>
    <ol className="lab-running-code" aria-label="当前执行的 C++ 转移代码"><li>for (int i = 1; i &lt;= n; ++i) {'{'}</li><li data-active={!!frame}>{direction === 'down' ? '    for (int c = W; c >= w[i]; --c)' : '    for (int c = w[i]; c <= W; ++c)'}</li><li data-active={!!frame}>{'        dp[c] = max(dp[c], dp[c - w[i]] + v[i]);'}</li><li>{'}'}</li></ol>
    <div className="lab-player"><button type="button" className="lab-icon-button" aria-label="重置推演" onClick={() => changeStep(0)}><RotateCcw size={17}/></button><button type="button" className="lab-icon-button" aria-label="上一步" disabled={!step} onClick={() => changeStep(step - 1)}><ArrowLeft size={17}/></button><button type="button" className="lab-button" disabled={done} onClick={() => setPlaying(value => !value)}>{playing && !done ? <Pause size={15}/> : <Play size={15}/>} {playing && !done ? '暂停' : '播放'}</button><button type="button" className="lab-button lab-button-quiet" disabled={done} onClick={() => changeStep(step + 1)}>下一步<ArrowRight size={15}/></button><label className="lab-speed">速度<select aria-label="推演速度" value={speed} onChange={event => setSpeed(Number(event.target.value))}><option value={1700}>慢</option><option value={1100}>中</option><option value={550}>快</option></select></label></div>
    <label className="lab-scrubber"><span>执行位置</span><input type="range" min="0" max={model.frames.length} value={step} onChange={event => changeStep(Number(event.target.value))}/><output>{step}</output></label>
  </div>;
}

const CLASS_TRACE = { capacity: EXPEDITION_CAPACITY, items: EXPEDITION };
const DEFAULT_TRACE = { capacity: 4, items: [{ id: 'X', name: '单件示例', weight: 2, value: 3 }] };
function validTrace(value) { return value && Number.isInteger(value.capacity) && value.capacity >= 0 && value.capacity <= 12 && Array.isArray(value.items) && value.items.length >= 1 && value.items.length <= 4 && value.items.every(item => item && typeof item.id === 'string' && Number.isInteger(item.weight) && item.weight >= 1 && item.weight <= 12 && Number.isInteger(item.value) && item.value >= 0 && item.value <= 99); }

export function TraceExperiment(props) {
  const { drafts, updateDraft } = props, config = validTrace(drafts.traceConfig) ? drafts.traceConfig : DEFAULT_TRACE;
  const direction = drafts.traceDirection === 'up' ? 'up' : 'down', [edit, setEdit] = useState(config), [error, setError] = useState('');
  const chooseConfig = value => { updateDraft('traceConfig', value); setEdit(value); setError(''); };
  return <>
    <div className="lab-story"><h2>为什么容量要倒着算？</h2><p>接着把上一节的二维表放进更少的格子。先看计算新答案时要保留什么，再看哪些旧位置可以覆盖。</p></div>
    <RowReuseDemo/>
    <h3 className="lab-subheading">再换一个极小例子，检验覆盖顺序</h3><p className="lab-caption">下面默认只有一件 X：重量 2、价值 3，容量 4，每件最多一次。这样能直接看出重复使用的错误；也可以切回课堂背包核对完整过程。</p>
    <div className="lab-experiment-toolbar"><div className="lab-segmented" role="group" aria-label="推演数据"><button type="button" aria-pressed={JSON.stringify(config) === JSON.stringify(CLASS_TRACE)} onClick={() => chooseConfig(CLASS_TRACE)}>课堂背包</button><button type="button" aria-pressed={JSON.stringify(config) === JSON.stringify(DEFAULT_TRACE)} onClick={() => chooseConfig(DEFAULT_TRACE)}>一件物品的反例</button></div><div className="lab-segmented" role="group" aria-label="容量遍历方向"><button type="button" aria-pressed={direction === 'down'} onClick={() => updateDraft('traceDirection', 'down')}>倒序 · W → w</button><button type="button" aria-pressed={direction === 'up'} onClick={() => updateDraft('traceDirection', 'up')}>正序 · w → W</button></div></div>
    <TracePlayer key={JSON.stringify(config) + direction} {...config} direction={direction}/>
    <details className="lab-custom"><summary>自己改一组数据，再看它运行</summary><form onSubmit={event => { event.preventDefault(); if (validTrace(edit)) chooseConfig(edit); else setError('容量取 0–12，重量取 1–12，价值取 0–99；所有数都要是整数。'); }}><label>容量上限<input aria-label="自定义背包容量" type="number" required min="0" max="12" step="1" value={edit.capacity} onChange={event => setEdit(value => ({ ...value, capacity: event.target.value === '' ? '' : Number(event.target.value) }))}/></label>{edit.items.map((item, index) => <div className="lab-custom-item" key={index}><b>物品 {item.id}</b>{['weight', 'value'].map(key => <label key={key}>{key === 'weight' ? '重量' : '价值'}<input aria-label={`物品 ${item.id} 的${key === 'weight' ? '重量' : '价值'}`} type="number" required min={key === 'weight' ? 1 : 0} max={key === 'weight' ? 12 : 99} step="1" value={item[key]} onChange={event => setEdit(value => ({ ...value, items: value.items.map((old, i) => i === index ? { ...old, [key]: event.target.value === '' ? '' : Number(event.target.value) } : old) }))}/></label>)}</div>)}<div className="lab-player"><button className="lab-button" type="submit">应用数据</button><button className="lab-text-button" type="button" disabled={edit.items.length >= 4} onClick={() => setEdit(value => ({ ...value, items: [...value.items, { id: String.fromCharCode(65 + value.items.length), weight: 1, value: 1 }] }))}>增加物品</button><button className="lab-text-button" type="button" disabled={edit.items.length <= 1} onClick={() => setEdit(value => ({ ...value, items: value.items.slice(0, -1) }))}>减少物品</button></div>{error && <p role="alert">{error}</p>}</form></details>
    <ChoiceCheck id="loop" title="每件物品只能选一次，容量应该怎样遍历？" choices={[
      { id: 'down', label: '从大到小，让较小的来源容量还属于上一轮', feedback: '对。c−w 比 c 小；倒序到达 c 时，dp[c−w] 还没有使用当前物品更新。它不可能已经包含当前物品。' },
      { id: 'up', label: '从小到大，方便一直把价值累加上去', feedback: '小容量先更新后，大容量就可能用它再加一件当前物品。切到“一件物品的反例”，正序播放看看。' },
    ]} answer="down" {...props}/>
    <NumberCheck id="repeat" title="你能预言这个错误吗？" prompt="只有一件物品：重量 2、价值 3，容量上限 4。如果错误地正序更新，dp[4] 最后会变成多少？" answer={6} explanation="dp[2] 先变成 3，dp[4] 再读它并加 3，得到 6。同一件用两次。允许无限件时这正是完全背包的转移，但它不符合本题每件一次的限制。" wrong="先算 c=2：dp[2]=3。再算 c=4：此时读到的 dp[2] 已经不是初始的 0。" {...props}/>
  </>;
}
