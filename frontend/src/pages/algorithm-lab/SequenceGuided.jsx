import { useState } from 'react';
import { ArrowRight, ExternalLink } from 'lucide-react';
import { applyEvents, prefix, rangeSum, total, matchesSequenceProblem } from './sequenceModel.js';
import { Decision, NumSelect, Panel, Prediction, Story, Strip } from './SequenceExperiments.jsx';
import { Feedback } from './LabParts.jsx';

export const GUIDED_STEPS = ['读条件', '亲手验证', '连接代码', '查错与迁移', '自行实现'];

function RangeMini({ problem, draft, update }) {
  const mini = problem.mini, [sorted, setSorted] = useState(false);
  const a = mini.a || mini.people?.map(p => p[0]) || [...(mini.text || '')], n = a.length;
  const l = Math.min(n, draft.miniL || 1), r = problem.kind === 'fence' ? Math.min(n, l + mini.k - 1) : Math.max(l, Math.min(n, draft.miniR || n));
  const values = sorted ? [...a].sort((x, y) => x - y) : a;
  const slice = values.slice(l - 1, r), sum = typeof values[0] === 'number' ? total(slice) : 0;
  return <Panel title="移动边界，先找一个合法方案" aria-label="跟做区间实验"><div className="seq-controls"><NumSelect label="小实验左端" value={l} max={problem.kind === 'fence' ? n - mini.k + 1 : n} onChange={value => update(old => ({ ...old, miniL: value }))}/>{problem.kind !== 'fence' && <NumSelect label="小实验右端" value={r} min={l} max={n} onChange={value => update(old => ({ ...old, miniR: value }))}/>}{problem.kind === 'stones' && <label className="seq-toggle"><input type="checkbox" checked={sorted} onChange={event => setSorted(event.target.checked)}/>切到排序副本</label>}</div><Strip values={values} label={problem.kind === 'friends' ? '朋友的财富（已按财富排序）' : problem.kind === 'pokemon' ? '房间内的种类' : sorted ? '排序副本' : '原顺序'} selected={i => i + 1 >= l && i + 1 <= r}/>
    {problem.kind === 'fence' && <p className="seq-equation">固定长 {mini.k}，区间 [{l},{r}]，和 {rangeSum(values, l, r)}。试完所有起点再比较。</p>}
    {problem.kind === 'stones' && <p className="seq-equation">{sorted ? '排序副本' : '原顺序'}的 [{l},{r}]：{slice.join(' + ')} = {sum}</p>}
    {problem.kind === 'books' && <Feedback good={sum <= mini.budget}>当前耗时 {sum} / 预算 {mini.budget}，长度 {r - l + 1}。{sum <= mini.budget ? '可以完整读完。尝试还能否变长。' : '已经超时，不能把这个长度记成合法答案。'}</Feedback>}
    {problem.kind === 'friends' && <Feedback good={a[r - 1] - a[l - 1] < mini.d}>财富差 {a[r - 1]}−{a[l - 1]}={a[r - 1] - a[l - 1]}，必须严格小于 {mini.d}。友谊值总和 {total(mini.people.slice(l - 1, r).map(p => p[1]))}。</Feedback>}
    {problem.kind === 'pokemon' && <><div className="seq-frequency">{[...new Set(mini.text)].map(c => <span key={c}>{c}：{slice.filter(x => x === c).length}</span>)}</div><Feedback good={new Set(slice).size === new Set(a).size}>当前覆盖 {new Set(slice).size} / {new Set(a).size} 种，长度 {r - l + 1}。只有种类集齐后，才拿这个长度尝试更新最小值。</Feedback></>}
  </Panel>;
}

function CoffeeMini({ problem, draft, update }) {
  const mini = problem.mini, selected = draft.recipes || mini.ranges.map((_, i) => i), operations = selected.map(i => ({ l: mini.ranges[i][0], r: mini.ranges[i][1], k: 1 })), coverage = applyEvents(Array(mini.n).fill(0), operations).result, good = coverage.map(v => Number(v >= mini.threshold));
  return <Panel title="配方可以开关，检查阈值前后各在数什么" aria-label="覆盖阈值实验"><div className="seq-tabs">{mini.ranges.map(([l, r], i) => <button key={i} type="button" aria-pressed={selected.includes(i)} onClick={() => update(old => ({ ...old, recipes: selected.includes(i) ? selected.filter(x => x !== i) : [...selected, i] }))}>配方 {i + 1}：[{l},{r}]</button>)}</div><Strip values={coverage} label="每个温度被几份配方推荐"/><Strip values={good} label={`至少 ${mini.threshold} 份才记为 1`}/><Strip values={prefix(good)} start={0} label="合格温度数量的前缀"/><p className="seq-equation">当前总共 {total(good)} 个温度合格。下方预测使用三份配方全部开启的数据。</p></Panel>;
}

function GregMini({ problem, draft, update }) {
  const mini = problem.mini, selected = draft.commands || [0, 1], times = applyEvents(Array(mini.operations.length).fill(0), selected.map(i => ({ l: mini.commands[i][0], r: mini.commands[i][1], k: 1 }))).result;
  const model = applyEvents(mini.a, mini.operations.map((op, i) => ({ ...op, k: op.k * times[i] })));
  return <Panel title="先沿操作编号累计，再沿数组位置累计" aria-label="两层差分实验"><p>原数组 [1,2,3]。操作 1：数组 [1,2] 加 1；操作 2：数组 [2,3] 加 2；操作 3：数组 [1,3] 加 1。</p><div className="seq-tabs">{mini.commands.map(([l, r], i) => <button type="button" key={i} aria-pressed={selected.includes(i)} onClick={() => update(old => ({ ...old, commands: selected.includes(i) ? selected.filter(x => x !== i) : [...selected, i] }))}>指令 {i + 1}：执行操作 {l}～{r}</button>)}</div><Strip values={times} label="第一层：各操作被执行几次（下标是操作编号）"/><Strip values={model.delta} label="第二层：数组增量事件（下标是数组位置）"/><Strip values={model.result} label="累计第二层后，加回原数组"/><p className="lab-caption">下方预测使用两条指令全部开启的数据。</p></Panel>;
}

function WeightedMini({ problem, draft, update }) {
  const a = draft.permutation || problem.mini.a, counts = applyEvents(Array(a.length).fill(0), problem.mini.ranges.map(([l, r]) => ({ l, r, k: 1 }))).result;
  return <Panel title="交换两格，观察谁的贡献更值钱" aria-label="位置贡献配对实验"><Strip values={counts} label="位置被查询的次数：由查询本身决定"/><Strip values={a} label="当前位置放的数值"/><div className="seq-controls">{a.slice(0, -1).map((_, i) => <button key={i} type="button" className="lab-button lab-button-quiet" onClick={() => { const next = [...a]; [next[i], next[i + 1]] = [next[i + 1], next[i]]; update(old => ({ ...old, permutation: next })); }}>交换第 {i + 1}、{i + 2} 格</button>)}</div><p className="seq-equation">{a.map((v, i) => `${v}×${counts[i]}`).join(' + ')} = {total(a.map((v, i) => v * counts[i]))}</p><p>位置次数不动，只调整数值。若把更大的数从低次数换到高次数，总贡献会发生什么变化？</p></Panel>;
}

function CardsMini({ problem, draft, update }) {
  const a = problem.mini.a, moves = draft.moves || [], l = moves.filter(m => m === 'left').length, r = a.length - 1 - moves.filter(m => m === 'right').length;
  let left = 0, right = a.length - 1; const scores = [0, 0];
  moves.forEach((m, i) => { scores[i % 2] += m === 'left' ? a[left++] : a[right--]; });
  const [error, setError] = useState('');
  const take = side => { if (l > r) return; if ((side === 'left' ? a[l] : a[r]) < Math.max(a[l], a[r])) { setError('规则要求取当前两端较大的一张。只比较当前还剩的端点。'); return; } setError(''); update(old => ({ ...old, moves: [...moves, side] })); };
  return <Panel title="按规则取牌，看看不变量是否一直成立" aria-label="两端取牌实验"><Strip values={a} label="亮色范围恰好是尚未取走的牌" selected={i => i >= l && i <= r}/><p className="seq-equation">先手 {scores[0]}，后手 {scores[1]}。{l <= r ? `现在轮到${moves.length % 2 ? '后手' : '先手'}` : '牌已取完'}</p><div className="seq-controls"><button className="lab-button" type="button" disabled={l > r} onClick={() => take('left')}>取最左</button><button className="lab-button lab-button-quiet" type="button" disabled={l > r} onClick={() => take('right')}>取最右</button><button className="lab-text-button" type="button" onClick={() => { update(old => ({ ...old, moves: [] })); setError(''); }}>重新取牌</button></div>{error && <Feedback>{error}</Feedback>}</Panel>;
}

function PairMini({ problem, draft, update }) {
  const { a, low, high } = problem.mini, threshold = draft.threshold ?? high, pairs = a.flatMap((x, i) => a.map((y, j) => ({ i, j, sum: x + y })).filter(p => p.i < p.j));
  return <Panel title="调阈值，观察 F(X) 包住哪些位置对" aria-label="位置对累计计数实验"><NumSelect label="阈值 X" value={threshold} min={0} max={8} onChange={value => update(old => ({ ...old, threshold: value }))}/><Strip values={a} label="有序数组，重复数值仍有不同下标"/><div className="seq-window-grid">{pairs.map(p => <div key={`${p.i}:${p.j}`} data-legal={p.sum <= threshold}><b>位置 ({p.i + 1},{p.j + 1})</b><span>和 {p.sum}{p.sum <= threshold ? ' ≤ X' : ' > X'}</span></div>)}</div><p className="seq-equation">F({threshold}) = {pairs.filter(p => p.sum <= threshold).length}。目标 [{low},{high}] 应取 F({high})−F({low - 1})。</p></Panel>;
}

const MINIS = { coffee: CoffeeMini, greg: GregMini, weighted: WeightedMini, cards: CardsMini, pairs: PairMini };
export default function SequenceGuided({ problem, draft, update, rows, lockedProblems, onTrain }) {
  const step = Math.max(0, Math.min(4, Number(draft.step) || 0)), Mini = MINIS[problem.kind] || RangeMini;
  const checks = { drafts: draft.answers || {}, updateDraft: (id, value) => update(old => ({ ...old, answers: { ...old.answers, [id]: value }, checked: { ...old.checked, [id]: false } })), onCheck: id => update(old => ({ ...old, checked: { ...old.checked, [id]: true } })) };
  const [codeResult, setCodeResult] = useState(''), code = draft.code || '', same = code.replace(/[\s;]/g, '') === problem.line.replace(/[\s;]/g, '');
  const locked = lockedProblems.find(row => matchesSequenceProblem(row, problem)), row = rows.find(row => matchesSequenceProblem(row, problem));
  return <><Story title={problem.title}>{problem.pid} · Codeforces 官方 rating {problem.rating} · {problem.focus} <a href={problem.url} target="_blank" rel="noreferrer">原题<ExternalLink size={12}/></a></Story>
    {locked ? <Panel title="跟做指导已锁定"><p>本题或它的同源别名正在模拟赛中，交卷后可查看指导。</p>{onTrain && <button type="button" className="lab-button" onClick={() => onTrain(locked.id)}>返回考场</button>}</Panel> : <><nav className="lab-guided-steps" aria-label="解题过程">{GUIDED_STEPS.map((name, i) => <button key={name} type="button" aria-current={step === i ? 'step' : undefined} onClick={() => update(old => ({ ...old, step: i, assisted: old.assisted || i === 2 || i === 3 }))}>{i + 1} {name}</button>)}</nav>
    {step === 0 && <><Panel title="先把问题说准确"><p>{problem.statement}</p><p className="lab-caption">{problem.ranges}</p><div className="seq-tabs">{problem.clues.map(([text], i) => <button type="button" aria-pressed={draft.clue === i} key={text} onClick={() => update(old => ({ ...old, clue: i }))}>{text}</button>)}</div>{Number.isInteger(draft.clue) && <p className="lab-clue-reason">{problem.clues[draft.clue]?.[1]}</p>}</Panel><Decision {...checks} id="model" title="哪个表示保留了题目需要的信息？" answer="0" options={[1, 0, 2].map(i => ({ id: String(i), label: problem.model[i], reason: i === 0 ? problem.insight : `检查当前允许的操作与目标。${problem.insight}` }))}/></>}
    {step === 1 && <><Mini key={problem.pid} problem={problem} draft={draft} update={update}/><Prediction {...checks} id="miniAnswer" title={problem.question} answer={problem.answer} explanation={problem.calculation}/></>}
    {step === 2 && <Panel title="只补这一处，完整程序由你实现"><p>{problem.state}</p><form aria-label="关键代码对照" onSubmit={event => { event.preventDefault(); setCodeResult(same ? 'ok' : 'other'); update(old => ({ ...old, codeChecked: same })); }}><label className="seq-code-input">写出这条关键 C++ 语句<textarea aria-label="关键 C++ 语句" value={code} rows={3} maxLength={1000} spellCheck={false} onChange={event => { setCodeResult(''); update(old => ({ ...old, code: event.target.value, codeChecked: false })); }}/></label><div className="seq-controls"><button type="submit" className="lab-button" disabled={!code.trim()}>对照教学写法</button><button type="button" className="lab-text-button" onClick={() => update(old => ({ ...old, reference: !old.reference }))}>{draft.reference ? '收起参考行' : '看参考行'}</button></div></form>{draft.reference && <pre className="lab-ghost-code"><code>{problem.line}</code></pre>}{(codeResult || draft.codeChecked) && <Feedback good={same}>{same ? problem.lineReason : '没有匹配这条教学写法。这里只忽略空白和分号，不是 C++ 编译评测；等价写法请在工作台编译运行，或对照参考行。'}</Feedback>}<p>{problem.lineReason}</p></Panel>}
    {step === 3 && <><Panel title="先执行错误写法，不要填正确答案"><p>{problem.bug}</p></Panel><Prediction {...checks} id="bugAnswer" title="错误程序会得到多少？" answer={problem.bugAnswer} explanation={problem.bugWhy}/><Panel title="换一个条件，再解释一次"><label className="seq-code-input">{problem.recall}<textarea rows={3} maxLength={2000} value={draft.recall || ''} onChange={event => update(old => ({ ...old, recall: event.target.value }))} placeholder="用自己的话保留推理，下次可以回来对照。"/></label></Panel></>}
    {step === 4 && <Panel title="现在交给你独立实现"><p>{problem.complexity}</p><p>先自己写输入、核心循环与输出，再用下列边界检查。跟做记录保留在本专题，正式通过由原站回执判断。</p><ul className="seq-checklist">{problem.tests.map((text, i) => <li key={text}><label><input type="checkbox" checked={(draft.tested || []).includes(i)} onChange={() => update(old => ({ ...old, tested: (old.tested || []).includes(i) ? old.tested.filter(x => x !== i) : [...(old.tested || []), i] }))}/>{text}</label></li>)}</ul>{onTrain && row ? <button type="button" className="lab-button" onClick={() => onTrain(row.id, { assisted: !!draft.assisted })}>进入工作台实现<ArrowRight size={16}/></button> : <a className="lab-button" href={problem.url} target="_blank" rel="noreferrer">打开原题，自行实现<ExternalLink size={15}/></a>}<p className="lab-caption">自检勾选与课堂核对不产生 AC、经验或掌握度。直接跳到实现且未进入代码/查错指导，不补造辅助证据。</p></Panel>}
    </>}
  </>;
}
