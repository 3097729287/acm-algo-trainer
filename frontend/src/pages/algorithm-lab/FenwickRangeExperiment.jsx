import {useMemo,useState} from 'react';
import {ArrowLeft,Check,RotateCcw} from 'lucide-react';
import {rangeFenwick} from './fenwickRangeModel.js';
import {Feedback} from './LabParts.jsx';
export default function FenwickRangeExperiment({draft={},update}){
 const [input,setInput]=useState((draft.values||[2,1,3,0,4]).join(' ')),[params,setParams]=useState('1 4 5'),[guess,setGuess]=useState(''),[checked,setChecked]=useState(false),[error,setError]=useState('');
 const values=draft.values||[2,1,3,0,4],operations=draft.operations||[],end=draft.end??values.length;
 const frame=useMemo(()=>rangeFenwick(values,operations,end),[values,operations,end]);
 const execute=event=>{event.preventDefault();try{if(operations.length>=30)throw Error('本例最多追加 30 次操作，可撤回或重置。');const parts=params.trim().split(/\s+/);if(parts.length!==3||parts.some(x=>! /^-?\d+$/.test(x)))throw Error('依次输入左端、右端、增量。');const next=[...operations,parts.map(Number)];rangeFenwick(values,next,end);update({...draft,operations:next});setError('');setChecked(false);}catch(issue){setError(issue.message);}};
 return <section className="lab-panel operations-experiment" aria-label="双树状数组区间加实验">
  <div className="lab-panel-title"><h3>区间加与区间和</h3><div className="operations-controls"><button type="button" className="lab-icon-button" aria-label="撤回区间加" disabled={!operations.length} onClick={()=>{update({...draft,operations:operations.slice(0,-1)});setChecked(false);}}><ArrowLeft size={17}/></button><button type="button" className="lab-icon-button" aria-label="重置区间加实验" onClick={()=>{update({});setError('');setChecked(false);}}><RotateCcw size={17}/></button></div></div>
  <p>给数组的 [l,r) 每一项加上增量。差分只在 l 加一次、r 减一次；第二棵树额外保存“位置 × 差分”，用于把点值累加成区间和。</p>
  <form className="operations-input" onSubmit={event=>{event.preventDefault();try{const next=input.trim().split(/\s+/).map(Number);rangeFenwick(next,[],next.length);update({values:next,operations:[],end:next.length});setError('');setChecked(false);}catch(issue){setError(issue.message);}}}><label>初始数组<input aria-label="区间加初始数组" value={input} onChange={e=>setInput(e.target.value)}/></label><button type="submit" className="lab-icon-button" aria-label="应用区间加数组"><Check size={17}/></button></form>
  <p>当前数组：[{frame.a.join(', ')}]；差分：[{frame.difference.join(', ')}]。</p>
  <form className="operations-input" onSubmit={execute}><label>l r 增量<input aria-label="区间加参数" value={params} onChange={e=>setParams(e.target.value)}/></label><button type="submit" className="lab-icon-button" aria-label="执行区间加"><Check size={17}/></button></form>
  <label>前缀长度 k <input type="number" aria-label="查询前缀长度" min="0" max={values.length} value={end} onChange={event=>{const k=Number(event.target.value);if(Number.isInteger(k)&&k>=0&&k<=values.length){update({...draft,end:k});setChecked(false);}}}/></label>
  <p>前 k 项之和 = k × Σ差分 − Σ(位置 × 差分) = {end} × {frame.differencePrefix} − {frame.weightedPrefix} = {frame.sum}。外部位置从 0 开始，表中树状数组下标从 1 开始。</p>
  <div className="operations-table"><table><thead><tr><th>内部 i</th><th>管辖外部区间</th><th>B1 差分和</th><th>B2 加权差分和</th></tr></thead><tbody>{frame.b1.slice(1).map((v,j)=>{const i=j+1;return <tr key={i} data-active={frame.path.includes(i)}><th>{i}</th><td>[{i-(i&-i)}, {i})</td><td>{v}</td><td>{frame.b2[i]}</td></tr>;})}</tbody></table></div>
  <p>k 大于 0 时，只读 B1 的前缀得到第 k−1 项的值；k=0 时是空和 0。它计算的是单项，区间和仍需两棵树的组合式；把 k 改成 0 或加入负增量可检查边界。</p>
  <form className="operations-predict" onSubmit={e=>{e.preventDefault();setChecked(true);}}><label>若只用一棵树查询差分前缀，本次会得到多少？<input aria-label="预测差分前缀" value={guess} onChange={e=>{setGuess(e.target.value);setChecked(false);}}/></label><button type="submit" className="lab-icon-button" aria-label="核对差分前缀"><Check size={17}/></button></form>
  {checked&&<Feedback good={guess.trim()===String(frame.differencePrefix)}>{guess.trim()===String(frame.differencePrefix)?`差分前缀是 ${frame.differencePrefix}；数组前缀和是 ${frame.sum}，两者数的对象不同。`:'沿高亮块累加 B1，再比较当前数组的对应单项。'}</Feedback>}
  {error&&<p role="alert">{error}</p>}
 </section>;
}
