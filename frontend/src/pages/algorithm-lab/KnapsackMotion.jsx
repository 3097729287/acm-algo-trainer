import { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, Pause, Play, RotateCcw } from 'lucide-react';
import { EXPEDITION, EXPEDITION_CAPACITY } from './knapsackModel.js';
import { choiceFrames } from './knapsackMotion.js';
import './knapsackMotion.css';

function useReducedMotion() {
  const [reduced, setReduced] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  useEffect(() => { const query = window.matchMedia('(prefers-reduced-motion: reduce)'), change = () => setReduced(query.matches); query.addEventListener('change', change); return () => query.removeEventListener('change', change); }, []);
  return reduced;
}

const names = items => items.length ? items.map(item => item.id).join(' + ') : '空方案';
const PHASE_NAMES = { scope: '确认这个小问题', skip: '如果不拿新物品', take: '如果拿新物品', compare: '比较后，重新选方案' };
const color = id => id === 'A' ? '#5a8fc0' : id === 'B' ? '#25866f' : '#c28c36';

function FilmControls({ index, last, playing, reduced, speed, change, play, setSpeed }) {
  return <div className="kn-motion-controls"><button type="button" className="lab-icon-button" aria-label="重看选择动画" onClick={() => change(0)}><RotateCcw size={16}/></button><button type="button" className="lab-icon-button" aria-label="选择动画上一帧" disabled={!index} onClick={() => change(index - 1)}><ArrowLeft size={16}/></button><button type="button" className="lab-button" aria-label={playing ? '暂停选择动画' : '播放选择动画'} disabled={reduced} onClick={play}>{playing ? <Pause size={15}/> : <Play size={15}/>} {playing ? '暂停' : last ? '重播动图' : '播放动图'}</button><button type="button" className="lab-button lab-button-quiet" aria-label="选择动画下一帧" disabled={last} onClick={() => change(index + 1)}>下一帧<ArrowRight size={15}/></button><label>速度<select aria-label="选择动画速度" value={speed} onChange={event => setSpeed(Number(event.target.value))}><option value={2800}>慢</option><option value={2100}>中</option><option value={1250}>快</option></select></label></div>;
}

function AnimatedBag({ items, capacity, label, active, unknown = false, impossible = false }) {
  let start = 0;
  return <div className="kn-motion-bag" data-active={active}><b>{label}</b><svg viewBox="0 0 320 108" role="img" aria-label={impossible ? '这件物品装不下，本分支不合法' : unknown ? '待你比较的方案' : `${label}：${names(items)}，占 ${items.reduce((s, item) => s + item.weight, 0)} / ${capacity} 格`}>
    <path d="M14 17 V83 Q14 94 25 94 H295 Q306 94 306 83 V17" className="kn-bag-outline"/>
    {impossible ? <text x="160" y="66" className="kn-bag-label">重量超过容量，装不下</text> : unknown ? <text x="160" y="66" className="kn-bag-question">?</text> : capacity === 0 ? <text x="160" y="64" className="kn-bag-label">容量 0：什么都不拿</text> : <>
      {Array.from({ length: capacity }, (_, i) => <rect key={i} x={23 + i * 273 / capacity} y="33" width={273 / capacity - 5} height="49" rx="4" className="kn-bag-empty"/>)}
      {items.map(item => { const x = 23 + start * 273 / capacity; start += item.weight; const width = item.weight * 273 / capacity - 5; return <g className="kn-moving-item" key={item.id}><rect x={x} y="33" width={width} height="49" rx="4" fill={color(item.id)}/><text x={x + width / 2} y="55" className="kn-item-label">{item.id}</text><text x={x + width / 2} y="72" className="kn-item-weight">占 {item.weight} 格</text></g>; })}
    </>}
  </svg><span>{impossible ? '没有合法方案' : unknown ? '先比较两种价值' : names(items)}</span></div>;
}

export function KnapsackChoiceFilm({ items = EXPEDITION, capacity = EXPEDITION_CAPACITY, focusIndex = null, conceal = false }) {
  const frames = useMemo(() => choiceFrames(items, capacity, focusIndex), [items, capacity, focusIndex]), [index, setIndex] = useState(0), [playing, setPlaying] = useState(false), [speed, setSpeed] = useState(2100);
  const reduced = useReducedMotion(), root = useRef(null), f = frames[index], last = index === frames.length - 1;
  const change = next => { setPlaying(false); setIndex(Math.max(0, Math.min(frames.length - 1, next))); };
  useEffect(() => {
    if (!playing || reduced || last) return;
    const timer = setTimeout(() => setIndex(value => value + 1), speed);
    return () => clearTimeout(timer);
  }, [playing, reduced, index, last, speed]);
  useEffect(() => { if (reduced || last) setPlaying(false); }, [reduced, last]);
  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => { if (!entry.isIntersecting) setPlaying(false); }, { threshold: .1 });
    if (root.current) observer.observe(root.current);
    const stop = () => { if(document.hidden)setPlaying(false); };
    document.addEventListener('visibilitychange',stop);
    return () => {observer.disconnect();document.removeEventListener('visibilitychange',stop);};
  }, []);
  const reading = f.phase === 'scope' ? `现在只允许 ${f.available.map(item => item.id).join('、')}，总容量 ${capacity}。之前算出的某个装法不会约束这个新问题。`
    : f.phase === 'skip' ? `不拿 ${f.item.id}：容量仍是 ${capacity}，只在 ${f.earlier.length ? f.earlier.map(item => item.id).join('、') : '没有可用物品'} 中选，价值 ${f.skip}。`
      : f.phase === 'take' ? f.take == null ? `${f.item.id} 自己就重 ${f.item.weight}，超过容量 ${capacity}；“拿”这一类没有合法方案。` : `拿 ${f.item.id}：先为它留 ${f.item.weight} 格，余下 ${f.remaining} 格从之前的物品重新选择。来源价值 ${f.source}，再加 ${f.item.id} 的价值 ${f.item.value}。`
        : conceal ? '两类覆盖全部合法装法。比较两种价值，自己填出当前答案；动画不替你提交作答。' : `比较 ${f.skip} 与 ${f.take == null ? '装不下' : f.take}，保留 ${f.result}。现在选 ${names(f.resultPlan)}；这是当前范围、当前容量下重新比较的结果。`;
  return <section ref={root} className="lab-panel knapsack-motion" aria-label="拿与不拿动态演示" data-phase={f.phase} data-frame={index} data-playing={playing}>
    <div className="kn-motion-heading"><h3>{focusIndex == null ? '看装法怎样改变：A 可以被 B + C 替换' : '让当前两种候选动起来'}</h3><span>{PHASE_NAMES[f.phase]}</span></div>
    <p className="kn-motion-contract">当前问题：只允许 {f.available.map(item => item.id).join('、')} · 容量 {capacity} 格 · 每件最多一次 · 不可拆分。{f.available.map(item => `${item.id}（重 ${item.weight}，值 ${item.value}）`).join('；')}。</p>
    <div className="kn-motion-track" role="group" aria-label="选择推演阶段">{frames.map((frame, i) => <button type="button" key={i} aria-label={`跳到${frame.available.map(item => item.id).join('、')}：${PHASE_NAMES[frame.phase]}`} aria-pressed={index === i} onClick={() => change(i)}>{frame.phase === 'scope' ? frame.available.map(item => item.id).join('') : '·'}</button>)}</div>
    <FilmControls index={index} last={last} playing={playing} reduced={reduced} speed={speed} change={change} setSpeed={setSpeed} play={() => { if(last)setIndex(0);setPlaying(value => !value); }}/>
    <div className="kn-motion-branches"><div data-focus={f.phase === 'skip' || f.phase === 'compare' && !conceal && f.winner === 'skip'}><AnimatedBag items={f.skipPlan} capacity={capacity} label={`① 不拿 ${f.item.id}`} active={f.phase === 'skip'}/><code>f[{f.i - 1}][{capacity}] = {f.skip}</code></div><div data-focus={f.phase === 'take' || f.phase === 'compare' && !conceal && f.winner === 'take'}><AnimatedBag items={f.takePlan} capacity={capacity} label={`② 拿 ${f.item.id}`} active={f.phase === 'take'} impossible={f.take == null}/><code>{f.take == null ? '装不下，不参与比较' : `f[${f.i - 1}][${f.remaining}] + ${f.item.value} = ${f.source} + ${f.item.value}`}</code></div></div>
    <div className="kn-motion-merge" aria-hidden="true"><span data-lit={f.phase === 'compare'}>↘</span><b>比较两类候选</b><span data-lit={f.phase === 'compare'}>↙</span></div>
    <div className="kn-motion-result" data-ready={f.phase === 'compare'}><AnimatedBag key={`${f.i}-${f.phase}`} items={f.phase === 'compare' && !conceal ? f.resultPlan : []} capacity={capacity} label={`当前答案 f[${f.i}][${capacity}]`} active={f.phase === 'compare'} unknown={f.phase !== 'compare' || conceal}/><strong>{f.phase === 'compare' && !conceal ? `最大价值 ${f.result}` : '最大价值 ?'}</strong></div>
    <p className="kn-motion-narration" aria-live={playing ? 'off' : 'polite'}>{reading}</p>
    {reduced && <p className="lab-caption">系统启用了减少动态效果：保留静态关键帧，请用上一帧、下一帧查看。</p>}
    <p className="lab-caption">每一组范围是独立的小问题；动画中的计算顺序不要求你按 A、B、C 的顺序装包。播放和推演不计课堂通过。</p>
  </section>;
}

export function KnapsackReadWriteMotion({ frame, speed = 1100 }) {
  const reduced = useReducedMotion();
  if (!frame) return <div className="kn-flow-poster"><span>来源答案</span><span>＋ 当前物品价值</span><span>→ 比较 → 写回目标</span><p>播放下方推演时，光点会跟随每次读取与写入。下面的数字来自同一次转移。</p></div>;
  const bad = frame.repeated && frame.improved;
  return <div className="kn-flow" data-repeated={bad} aria-label="读取到写回的动态数据流"><div className="kn-flow-scroll"><svg key={`${frame.i}-${frame.c}`} viewBox="0 0 830 235" role="img" aria-label={`读取时 dp[${frame.source}]=${frame.before[frame.source]}，加物品 ${frame.item.id} 的价值 ${frame.item.value} 得 ${frame.take}，与旧目标 ${frame.skip} 比较，写回 ${frame.result}${bad ? '；来源已经包含当前物品，造成重复使用' : ''}`}>
    <defs><marker id="kn-flow-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10Z" fill="currentColor"/></marker></defs>
    <path d="M174 70 H255 Q280 70 280 105 H353" className="kn-flow-path"/><path d="M174 170 H255 Q280 170 280 135 H353" className="kn-flow-path"/><path d="M486 120 H555" className="kn-flow-path"/><path d="M660 120 H706" className="kn-flow-path"/>
    <rect x="5" y="34" width="170" height="72" rx="8" className="kn-flow-source"/><text x="90" y="59">读取时的 dp[{frame.source}]</text><text x="90" y="87" className="kn-flow-number">{frame.before[frame.source]}</text>
    <rect x="5" y="135" width="170" height="70" rx="8" className="kn-flow-item"/><text x="90" y="161">当前 {frame.item.id} 的价值</text><text x="90" y="188" className="kn-flow-number">+ {frame.item.value}</text>
    <rect x="353" y="82" width="134" height="77" rx="8" className="kn-flow-take"/><text x="420" y="107">如果再拿 {frame.item.id}</text><text x="420" y="139" className="kn-flow-number">{frame.take}</text>
    <rect x="555" y="69" width="105" height="101" rx="8" className="kn-flow-compare"/><text x="607" y="98">max</text><text x="607" y="127">原值 {frame.skip}</text><text x="607" y="151">新候选 {frame.take}</text>
    <rect x="706" y="82" width="120" height="77" rx="8" className="kn-flow-result"/><text x="766" y="107">写回 dp[{frame.c}]</text><text x="766" y="139" className="kn-flow-number">{frame.result}</text>
    {!reduced && <><circle r="5" className="kn-flow-particle"><animateMotion dur={`${speed / 1000 * .8}s`} repeatCount="1" path="M174 70 H255 Q280 70 280 105 H353 H486 H555 H660 H706" fill="freeze"/></circle><circle r="4" className="kn-flow-particle kn-flow-value"><animateMotion dur={`${speed / 1000 * .5}s`} repeatCount="1" path="M174 170 H255 Q280 170 280 135 H353" fill="freeze"/></circle></>}
  </svg></div><p>{bad ? `来源已经含有 ${frame.item.id}，再加一次就重复了。这条亮起的数据流正是错误第一次发生的位置。` : `来源 ${frame.sourceFresh ? '已在本轮更新' : '仍属于上一轮'}；这里分开画“读取时”和“写回后”，它们描述同一次原地更新的两个时刻。`}</p></div>;
}
