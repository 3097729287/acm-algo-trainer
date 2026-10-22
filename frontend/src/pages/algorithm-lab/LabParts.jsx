import { useState } from 'react';
import { Check, ChevronRight, Clipboard, Lightbulb } from 'lucide-react';

export function Feedback({ good = false, children }) {
  return <div className={`lab-feedback ${good ? 'lab-feedback-good' : ''}`} role="status"><span aria-hidden="true">{good ? <Check size={17}/> : <Lightbulb size={17}/>}</span><div>{children}</div></div>;
}

export function Hints({ items, id, drafts, updateDraft }) {
  const level = Math.min(items.length, Number(drafts[`hint:${id}`]) || 0);
  return <div className="lab-hints">{items.slice(0, level).map((text, i) => <p key={i}>{text}</p>)}{level < items.length && <button type="button" className="lab-text-button" onClick={() => updateDraft(`hint:${id}`, level + 1)}><Lightbulb size={15}/>{level === 0 ? '提示' : level === items.length - 1 ? '完整思路' : '再提示一点'}</button>}</div>;
}

export function ChoiceCheck({ id, title, prompt, choices, answer, drafts, updateDraft, passed, onPass }) {
  const value = drafts[id] || '', [result, setResult] = useState('');
  const chosen = choices.find(item => item.id === value), correct = result === 'correct' || (!result && passed[id] && value === answer);
  return <form className="lab-check" aria-label={title} onSubmit={event => { event.preventDefault(); setResult(value === answer ? 'correct' : 'incorrect'); if (value === answer) onPass(id); }}>
    <h3>{title}</h3>{prompt && <p>{prompt}</p>}
    <fieldset><legend className="sr-only">{title}</legend>{choices.map(choice => <label className="lab-choice" key={choice.id}><input type="radio" name={id} value={choice.id} checked={value === choice.id} onChange={() => { setResult(''); updateDraft(id, choice.id); }}/><span>{choice.label}</span></label>)}</fieldset>
    <button className="lab-button" disabled={!value} type="submit">检查判断<ChevronRight size={15}/></button>
    {(result || correct) && <Feedback good={correct}>{chosen?.feedback || '先选择一个答案，再检查判断。'}</Feedback>}
  </form>;
}

export function NumberCheck({ id, title, prompt, answer, hints = [], drafts, updateDraft, passed, onPass, explanation, wrong = '先列出合法方案，再比较。需要时可以逐层打开提示。' }) {
  const value = String(drafts[id] ?? ''), [result, setResult] = useState('');
  const matches = typeof answer === 'number' ? /^\d+$/.test(value.trim()) && Number(value.trim()) === answer : value.trim() === answer;
  const correct = result === 'correct' || (!result && passed[id] && matches);
  return <form className="lab-check" aria-label={title} onSubmit={event => { event.preventDefault(); setResult(matches ? 'correct' : 'incorrect'); if (matches) onPass(id); }}>
    <h3>{title}</h3><p>{prompt}</p>
    <div className="lab-answer-row"><label><span className="sr-only">{title}的答案</span><input type="text" inputMode={typeof answer === 'number' ? 'numeric' : 'text'} maxLength={24} value={value} placeholder={typeof answer === 'number' ? '输入你的结果' : '输入结果或“不可达”'} onChange={event => { setResult(''); updateDraft(id, event.target.value); }}/></label><button className="lab-button" type="submit" disabled={!value.trim()}>验证结果<ChevronRight size={15}/></button></div>
    {(result || correct) && <Feedback good={correct}>{correct ? explanation : wrong}</Feedback>}
    {hints.length > 0 && <Hints items={hints} id={id} drafts={drafts} updateDraft={updateDraft}/>}
  </form>;
}

export function BagSlots({ items, capacity, unknown = false }) {
  const weight = items.reduce((sum, item) => sum + item.weight, 0);
  return <div className="lab-bag-slots" style={{ '--bag-capacity': Math.max(1, capacity) }} aria-label={unknown ? '待你推算最优装法' : `容量 ${capacity} 格，${items.length ? items.map(item => item.name || item.id).join('、') : '什么都不拿'}，占用 ${weight} 格`}>
    {unknown ? <span className="lab-bag-unknown">待你推算</span> : capacity === 0 ? <span className="lab-bag-empty">容量为 0，什么都放不下</span> : <>{items.map(item => <span key={item.id} data-item={item.id} style={{ gridColumn: `span ${Math.min(item.weight, Math.max(capacity, 1))}` }}><b>{item.id} {item.name}</b><small>{item.weight} 格</small></span>)}{Array.from({ length: Math.max(0, capacity - weight) }, (_, i) => <span className="lab-empty-slot" key={`empty-${i}`} aria-label="空余 1 格">空</span>)}</>}
  </div>;
}

export function CodeBlock({ code, title = 'C++17', copy = false }) {
  const [status, setStatus] = useState('');
  return <div className="lab-code"><div className="lab-code-heading"><span>{title}</span>{copy && <button className="lab-text-button" type="button" onClick={async () => { try { await navigator.clipboard.writeText(code); setStatus('已复制'); } catch { setStatus('可在下面选中代码复制'); } }}><Clipboard size={14}/>{status || '复制代码'}</button>}</div><pre tabIndex={0} aria-label={title}><code>{code}</code></pre>{status && <span className="sr-only" role="status">{status}</span>}</div>;
}
