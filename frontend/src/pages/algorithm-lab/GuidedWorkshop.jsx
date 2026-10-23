import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, Check, ExternalLink, List } from 'lucide-react';
import { GUIDED_PROBLEMS, matchesGuidedProblem, matchesTransition, bestMiniPlan } from './guidedProblems.js';
import { ChoiceCheck, Feedback, NumberCheck } from './LabParts.jsx';

const STEPS = ['找条件', '做小实验', '推到代码', '查错与迁移', '自行实现'];
const sum = (items, key) => items.reduce((total, item) => total + (item[key] || 0), 0);

function MiniExperiment({ problem, picks, onChange }) {
  const items = problem.mini.items, selected = items.filter((_, index) => picks.includes(index));
  const weight = sum(selected, 'weight'), value = sum(selected, 'value'), mass = sum(selected, 'mass');
  const total = sum(items, 'weight'), balance = problem.kind === 'balance';
  const legal = balance || (weight <= problem.mini.capacity && (problem.kind !== 'dual' || mass <= problem.mini.weightLimit));
  return <section className="lab-panel lab-guided-mini" aria-label="亲手验证小例子">
    <p>{balance ? '点一道题，把它在两个大脑之间移动。' : '点选物品，看看这个组合满足限制吗。'}{problem.kind === 'dual' ? '体积与重量上限都为 5。' : !balance && `容量上限 ${problem.mini.capacity}。`}</p>
    <div className="lab-guided-items">{items.map((item, index) => <button type="button" key={index} aria-pressed={picks.includes(index)} onClick={() => onChange(picks.includes(index) ? picks.filter(value => value !== index) : [...picks, index])}><b>{String.fromCharCode(65 + index)}</b><span>{balance ? `耗时 ${item.weight}` : problem.kind === 'dual' ? `体积 ${item.weight} · 重量 ${item.mass} · 热量 ${item.value}` : problem.kind === 'budget' ? `价格 ${item.weight} · 重要度 ${item.importance} → 收益 ${item.value}` : problem.kind === 'space' ? `体积 ${item.weight}` : `耗时 ${item.weight} · 价值 ${item.value}`}</span><small>{balance ? picks.includes(index) ? '左脑' : '右脑' : picks.includes(index) ? '已选' : '未选'}</small></button>)}</div>
    {balance ? <div className="lab-balance-bars"><div style={{ '--load': `${weight / total * 100}%` }}>左脑 {weight}</div><div style={{ '--load': `${(total - weight) / total * 100}%` }}>右脑 {total - weight}</div><strong>当前分配完成时间 max({weight}, {total - weight}) = {Math.max(weight, total - weight)}</strong></div> : <output className="lab-mini-result" data-legal={legal}>{problem.kind === 'dual' ? `体积 ${weight}/5 · 重量 ${mass}/5 · 热量 ${value}` : problem.kind === 'space' ? `已装 ${weight} · 剩余 ${problem.mini.capacity - weight}` : `消耗 ${weight}/${problem.mini.capacity} · 收益 ${value}`}{!legal && '：超出限制'}</output>}
  </section>;
}

function TransitionExercise({ problem, draft, update }) {
  const [reference, setReference] = useState(false), [result, setResult] = useState('');
  const correct = matchesTransition(draft.code || '', problem.line);
  return <form className="lab-panel lab-guided-transition" aria-label="补出关键转移" onSubmit={event => { event.preventDefault(); setResult(correct ? 'correct' : 'wrong'); update(old => ({ ...old, codeChecked: correct })); }}>
    <h3>根据状态，补出这一行</h3><p>{problem.state}</p>
    <label><span className="sr-only">关键转移代码</span><textarea spellCheck="false" rows="3" value={draft.code || ''} placeholder="写出更新这一格的 C++ 语句" onChange={event => { setResult(''); update(old => ({ ...old, code: event.target.value.slice(0, 1000), codeChecked: false })); }}/></label>
    <div className="lab-foundation-actions"><button className="lab-button" type="submit" disabled={!draft.code?.trim()}>核对这一行</button><button className="lab-text-button" type="button" onClick={() => setReference(value => !value)}>{reference ? '收起参考行' : '对照参考行'}</button></div>
    {reference && <pre className="lab-ghost-code"><code>{problem.line}</code></pre>}
    {(result || draft.codeChecked) && <Feedback good={correct && (result === 'correct' || draft.codeChecked)}>{correct ? problem.source : '核对左侧状态、扣掉的资源和加回的收益。这里的变量含义都在上方；可对照参考行。'}</Feedback>}
    {(reference || draft.codeChecked) && <dl className="lab-guided-plan"><div><dt>起点</dt><dd>{problem.initial}</dd></div><div><dt>顺序</dt><dd>{problem.loop}</dd></div><div><dt>答案</dt><dd>{problem.output}</dd></div></dl>}
  </form>;
}

export default function GuidedWorkshop({ prefs, setPrefs, rows = [], onTrain, headerActions, lockedProblems = [] }) {
  const progress = prefs.learningPaths?.knapsack?.guided || {}, index = Math.max(0, Math.min(4, Number(progress.active) || 0));
  const problem = GUIDED_PROBLEMS[index], draft = progress.problems?.[problem.pid] || {}, step = Math.max(0, Math.min(4, Number(draft.step) || 0));
  const [menu, setMenu] = useState(false), main = useRef(null);
  useEffect(() => {
    if (!menu) return;
    const close = event => { if (event.type === 'keydown' ? event.key === 'Escape' : !event.target.closest('.lab-guided .lab-menu')) {if(event.type==='keydown')event.preventDefault();setMenu(false);} };
    document.addEventListener('keydown', close); document.addEventListener('pointerdown', close);
    return () => { document.removeEventListener('keydown', close); document.removeEventListener('pointerdown', close); };
  }, [menu]);
  const patch = change => setPrefs(previous => { const knapsack = previous.learningPaths?.knapsack || {}, current = knapsack.guided || {}; return { ...previous, learningPaths: { ...previous.learningPaths, knapsack: { ...knapsack, guided: change(current) } } }; });
  const update = change => patch(current => ({ ...current, problems: { ...current.problems, [problem.pid]: change(current.problems?.[problem.pid] || {}) } }));
  const navigate = target => { patch(current => ({ ...current, active: target })); setMenu(false); main.current?.scrollIntoView({ block: 'start' }); };
  const checkProps = { drafts: draft.answers || {}, passed: draft.checked || {}, updateDraft: (id, value) => update(old => ({ ...old, answers: { ...old.answers, [id]: value }, checked: { ...old.checked, [id]: false } })), onPass: id => update(old => ({ ...old, checked: { ...old.checked, [id]: true } })) };
  const row = rows.find(value => matchesGuidedProblem(value, problem.pid));
  const lockedProblem = lockedProblems.find(value => matchesGuidedProblem(value, problem.pid));
  return <div className="algorithm-lab lab-guided" aria-label="背包 DP 跟着做题">
    <header className="lab-course-header"><h1>跟着做题</h1><span className="lab-position">{index + 1} / 5</span><aside className="lab-course-tools" aria-label="练习导航"><nav className="lab-page-navigation" aria-label="题目翻页"><button className="lab-icon-button" type="button" aria-label="上一页" title="上一题" disabled={!index} onClick={() => navigate(index - 1)}><ArrowLeft size={18}/></button><button className="lab-icon-button" type="button" aria-label="下一页" title="下一题" disabled={index === 4} onClick={() => navigate(index + 1)}><ArrowRight size={18}/></button></nav><div className="lab-menu"><button type="button" className="lab-menu-toggle" aria-label="精选题目" aria-expanded={menu} onClick={() => setMenu(value => !value)}><List size={17}/><span>题目</span></button>{menu && <nav aria-label="五道精选题">{GUIDED_PROBLEMS.map((value, i) => <button key={value.pid} type="button" aria-current={i === index ? 'step' : undefined} onClick={() => navigate(i)}><span>{i + 1}</span><b>{value.title}</b></button>)}</nav>}</div></aside><div className="lab-header-actions">{headerActions}</div></header>
    <main ref={main} className="lab-lesson" tabIndex={-1}>
      <div className="lab-story"><h2>{problem.title}</h2><p>{!lockedProblem && problem.focus} <a href={`https://www.luogu.com.cn/problem/${problem.pid}`} target="_blank" rel="noreferrer">{problem.pid} 原题<ExternalLink size={12}/></a></p></div>
      {lockedProblem ? <section className="lab-panel" aria-label="跟做指导已锁定"><p>本题正在模拟赛中，交卷后可查看跟做指导。</p>{onTrain && <button className="lab-button" type="button" onClick={() => onTrain(lockedProblem.id)}>返回考场<ArrowRight size={16}/></button>}</section> : <>
      <nav className="lab-guided-steps" aria-label="解题过程">{STEPS.map((label, i) => <button type="button" key={label} aria-current={step === i ? 'step' : undefined} onClick={() => update(old => ({ ...old, step: i, assisted: old.assisted || i === 2 || i === 3 }))}>{i + 1} {label}</button>)}</nav>
      <div key={problem.pid + ':' + step}>
        {step === 0 && <><section className="lab-panel lab-reading"><h3>哪些条件决定做法？</h3><p>{problem.parts.map((part, i) => Array.isArray(part) ? <button className="lab-keyword" type="button" key={i} aria-pressed={(draft.marks || []).includes(i)} onClick={() => update(old => ({ ...old, clue: i, marks: (old.marks || []).includes(i) ? old.marks.filter(value => value !== i) : [...(old.marks || []), i] }))}>{part[0]}</button> : part)}</p>{Array.isArray(problem.parts[draft.clue]) && <p className="lab-clue-reason">{problem.parts[draft.clue][1]}</p>}</section><ChoiceCheck id="model" title="把这道题翻译成状态" choices={[0, 1, 2].map(offset => (offset + index + 1) % 3).map(i => ({ id: String(i), label: problem.model[i], feedback: i === 0 ? problem.insight : problem.modelErrors[i - 1] }))} answer="0" {...checkProps}/></>}
        {step === 1 && <><MiniExperiment problem={problem} picks={draft.picks || []} onChange={picks => update(old => ({ ...old, picks }))}/><NumberCheck id="prediction" title={problem.prediction} answer={problem.answer} explanation={problem.reasoning} wrong="先用上方的小实验比较合法组合；检查输出问的是收益、剩余空间还是完成时间。" {...checkProps}/>{draft.checked?.prediction && <button className="lab-text-button" type="button" onClick={() => update(old => ({ ...old, picks: bestMiniPlan(problem) }))}>对照一种最优方案</button>}</>}
        {step === 2 && <TransitionExercise problem={problem} draft={draft} update={update}/>}
        {step === 3 && <><section className="lab-panel"><h3>{problem.bug.title}</h3><pre className="lab-bug-code"><code>{problem.bug.code}</code></pre><p>{problem.bug.input}</p></section><NumberCheck id="bug" title="这段错误代码会算出多少？" answer={problem.bug.answer} explanation={problem.bug.why} wrong="按错误代码实际执行，别填正确算法的答案。找出它第一次偏离状态含义的位置。" {...checkProps}/><section className="lab-panel"><label className="lab-recall"><b>{problem.recall}</b><textarea rows="3" maxLength="2000" value={draft.reason || ''} onChange={event => update(old => ({ ...old, reason: event.target.value }))} placeholder="用自己的话解释，保留给下次回看。"/></label></section></>}
        {step === 4 && <section className="lab-panel lab-implementation"><h3>现在由你完成完整程序</h3><p>{problem.complexity}</p><ul>{problem.checks.map((text, i) => <li key={text}><label><input type="checkbox" checked={(draft.tested || []).includes(i)} onChange={() => update(old => ({ ...old, tested: (old.tested || []).includes(i) ? old.tested.filter(value => value !== i) : [...(old.tested || []), i] }))}/>{text}</label></li>)}</ul><p className="lab-caption">勾选只记录你检查过的边界，正式通过以原站回执为准。</p><div className="lab-foundation-actions">{onTrain && row ? <button type="button" className="lab-button" onClick={() => onTrain(row.id, { assisted: !!draft.assisted })}>进入工作台实现<ArrowRight size={16}/></button> : <a className="lab-button" href={`https://www.luogu.com.cn/problem/${problem.pid}`} target="_blank" rel="noreferrer">打开原题，自行实现<ExternalLink size={15}/></a>}</div>{row?.accepted && <p className="lab-completed"><Check size={16}/>已取得原站通过记录</p>}</section>}
      </div>
      </>}
    </main>
  </div>;
}
