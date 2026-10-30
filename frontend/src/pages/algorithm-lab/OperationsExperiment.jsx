import {useMemo,useState} from 'react';
import {ArrowLeft,ArrowRight,Check,RotateCcw} from 'lucide-react';
import {operationTrace} from './operationModels.js';
import {Feedback} from './LabParts.jsx';

const Button=({label,children,...props})=><button type="button" className="lab-icon-button" aria-label={label} title={label} {...props}>{children}</button>;
function Lines({frame:f,values}) {
 const ys=f.lines.flatMap(([k,b])=>values.map(x=>k*x+b)),lo=Math.min(0,...ys),hi=Math.max(1,...ys),y=value=>195-(value-lo)/(hi-lo)*175;
 return <><p>已加入直线：{f.lines.map(([k,b])=>`y=${k}x+${b}`).join('；')||'无'}。</p><svg className="operations-lines" viewBox="0 0 440 230" role="img" aria-label="各直线在登记横坐标上的取值"><line x1="30" x2="410" y1={y(0)} y2={y(0)}/>{f.lines.map(([k,b],i)=><polyline key={i} points={values.map(x=>`${40+x*85},${y(k*x+b)}`).join(' ')} className={'line-'+i}/>) }{f.results.filter(([,value])=>value!=null).map(([x,value])=><g key={x}><circle cx={40+x*85} cy={y(value)} r="5"/><text x={40+x*85} y="222">{x}</text></g>)}</svg><table><thead><tr><th>x</th><th>最小 y</th></tr></thead><tbody>{f.results.map(([x,value])=><tr key={x}><th>{x}</th><td>{value??'空值'}</td></tr>)}</tbody></table></>;
}
function State({kind,frame:f,values}) {
 if(kind==='dsu')return <><p>集合数 {f.components}；根处 size 才代表整组大小。</p><table><thead><tr><th>对象 v</th><th>parent[v]</th><th>根处大小</th></tr></thead><tbody>{f.parent.map((p,i)=><tr key={i} data-active={f.active.includes(i)}><th>{i}</th><td>{p}</td><td>{p===i?f.size[i]:'—'}</td></tr>)}</tbody></table></>;
 if(kind==='fenwick')return <><p>当前原数组（外部下标 0 开始）：[{f.a.join(', ')}]</p><table><thead><tr><th>内部 i</th><th>管辖的外部区间</th><th>tree[i]</th></tr></thead><tbody>{f.tree.slice(1).map((sum,j)=>{const i=j+1;return <tr key={i} data-active={f.active.includes(i)}><th>{i}</th><td>[{i-(i&-i)}, {i})</td><td>{sum}</td></tr>;})}</tbody></table></>;
 if(kind==='segment-tree')return <><p>当前原数组：[{f.a.join(', ')}]。lazy 已计入本结点 sum，尚未传给孩子。</p><table><thead><tr><th>结点</th><th>区间</th><th>sum</th><th>lazy</th></tr></thead><tbody>{f.tree.filter(Boolean).map(n=><tr key={n.p} data-active={f.active.includes(n.p)}><th>{n.p}</th><td>[{n.l},{n.r})</td><td>{n.sum}</td><td>{n.lazy}</td></tr>)}</tbody></table></>;
 if(kind==='trie')return <><p>词库份数 {f.words.length}：{f.words.join(', ')||'空'}。</p><table><thead><tr><th>路径</th><th>经过 passing</th><th>结束 ending</th></tr></thead><tbody>{f.nodes.map((n,i)=><tr key={i} data-active={f.active.includes(i)}><th>{n.path||'根 / 空串'}</th><td>{n.pass}</td><td>{n.end}</td></tr>)}</tbody></table></>;
 if(kind==='binary-lifting')return <><p>后继 next = [{values.join(', ')}]；up[v][j] 是走 2^j 步后的终点。</p><table><thead><tr><th>起点 v</th>{[1,2,4,8].map(n=><th key={n}>{n} 步</th>)}</tr></thead><tbody>{f.up.map((row,v)=><tr key={v}><th>{v}</th>{row.slice(0,4).map((to,j)=><td key={j} data-active={f.active.includes(j)}>{to}</td>)}</tr>)}</tbody></table></>;
 if(kind==='li-chao')return <Lines frame={f} values={values}/>;
 if(kind==='dinic')return <><p>当前流量 {f.flow}。矩阵记录还可沿该方向推送的残量，包含撤回旧流的反向边。</p><table><thead><tr><th>从 / 到</th>{f.residual.map((_,i)=><th key={i}>{i}</th>)}</tr></thead><tbody>{f.residual.map((row,u)=><tr key={u}><th>{u}</th>{row.map((cap,v)=><td key={v} data-active={f.path.some(([a,b])=>a===u&&b===v)}>{cap}</td>)}</tr>)}</tbody></table>{f.cut&&<p>最小割源侧：{f.cut.join(', ')}。跨向其余点的原容量之和等于 {f.flow}。</p>}</>;
 return null;
}

export default function OperationsExperiment({topic,draft={},update}) {
 const frames=useMemo(()=>operationTrace(topic.id,topic.values,[...topic.scripts,...(draft.operations||[])]),[topic,draft.operations]);
 const index=Math.min(frames.length-1,Math.max(0,Number(draft.frame)||0)),frame=frames[index];
 const [answer,setAnswer]=useState(draft.answer||''),[checked,setChecked]=useState(false),[operation,setOperation]=useState(topic.scripts[0][0]),[parameters,setParameters]=useState(''),[error,setError]=useState('');
 const choices={dsu:['unite','same','size'],fenwick:['add','prefix','sum'],'segment-tree':['addRange','sum'],trie:['insert','erase','count','prefix'],'binary-lifting':['jump'],'li-chao':['line','query'],dinic:[]}[topic.id];
 const append=()=>{
  try{
   let args=parameters.trim().split(/\s+/).filter(Boolean);
   if(topic.id==='trie'){if(args.length>1||args.some(x=>!/^[a-z]*$/.test(x))||parameters.length>24)throw Error('输入一个小写单词，最多 24 个字符；留空表示空串。');args=[parameters.trim()];}
   else{
    const count={unite:2,same:2,size:1,add:2,prefix:1,sum:2,addRange:3,jump:2,line:2,query:1}[operation];
    if(args.length!==count||args.some(x=>! /^-?\d+$/.test(x)||!Number.isSafeInteger(Number(x))||Math.abs(Number(x))>1000000))throw Error(`此操作需要 ${count} 个整数，以空格分隔，绝对值不超过 1000000。`);
    args=args.map(Number);const n=topic.values.length;
    const index=x=>Number.isInteger(x)&&x>=0&&x<n;
    if(topic.id==='dsu'&&!args.every(index)||topic.id==='binary-lifting'&&(!index(args[0])||args[1]<0)||topic.id==='fenwick'&&(operation==='add'?!index(args[0]):operation==='prefix'?args[0]<0||args[0]>n:args[0]<0||args[0]>args[1]||args[1]>n)||topic.id==='segment-tree'&&(args[0]<0||args[0]>args[1]||args[1]>n))throw Error('下标超出本例范围；区间使用 [l,r)。');
   }
   if((draft.operations||[]).length>=30)throw Error('本例最多追加 30 次操作，可重置后重试。');
   const operations=[...(draft.operations||[]),[operation,...args]],all=operationTrace(topic.id,topic.values,[...topic.scripts,...operations]);
   update({...draft,operations,frame:all.length-1});setError('');setChecked(false);
  }catch(e){setError(e.message);}
 };
 const move=i=>{setChecked(false);update({...draft,frame:i});};
 const final=frames.at(-1),goal=topic.id==='dsu'?final.components:topic.id==='fenwick'||topic.id==='segment-tree'?final.a.reduce((a,b)=>a+b,0):topic.id==='trie'?final.words.length:topic.id==='binary-lifting'?final.target:topic.id==='dinic'?final.flow:final.results.at(-1)[1];
 return <section className="lab-panel operations-experiment" aria-label={`${topic.title}操作实验`}>
  <div className="lab-panel-title"><h3>逐步执行操作</h3><div className="operations-controls"><Button label="上一步" disabled={!index} onClick={()=>move(index-1)}><ArrowLeft size={17}/></Button><Button label="下一步" disabled={index===frames.length-1} onClick={()=>move(index+1)}><ArrowRight size={17}/></Button><Button label="重置实验" onClick={()=>{update({...draft,frame:0,operations:[]});setError('');setChecked(false);}}><RotateCcw size={17}/></Button></div></div>
  <p>{index===0?'初始状态':frame.log.at(-1)}</p><div className="operations-table"><State kind={topic.id} frame={frame} values={topic.values}/></div>
  <ol aria-label="本例操作序列">{[...topic.scripts,...(draft.operations||[])].map((op,i)=><li key={i}>{op.join(' ')}</li>)}</ol>
  {choices.length>0&&<form className="operations-input" onSubmit={e=>{e.preventDefault();append();}}><label>追加操作<select aria-label="操作类型" value={operation} onChange={e=>setOperation(e.target.value)}>{choices.map(op=><option key={op}>{op}</option>)}</select></label><label>参数<input aria-label="操作参数" value={parameters} onChange={e=>setParameters(e.target.value)}/></label><Button type="submit" label="执行操作"><Check size={17}/></Button></form>}{error&&<p role="alert">{error}</p>}
  <form className="operations-predict" onSubmit={e=>{e.preventDefault();setChecked(true);}}><label>执行完全部操作后，{topic.id==='dsu'?'集合数':topic.id==='fenwick'||topic.id==='segment-tree'?'数组总和':topic.id==='trie'?'词库份数':topic.id==='binary-lifting'?'最后一次跳跃终点':topic.id==='dinic'?'总流量':'最后一个坐标的最小值'}是多少？<input aria-label="预测最终结果" value={answer} onChange={e=>{setAnswer(e.target.value);update({...draft,answer:e.target.value});setChecked(false);}}/></label><Button type="submit" label="核对推演" disabled={!answer.trim()}><Check size={17}/></Button></form>
  {checked&&<Feedback good={answer.trim()===String(goal)}>{answer.trim()===String(goal)?`结果为 ${goal}。用单步状态检查每次变化及查询读取的位置。`:'结果还不一致。逐步执行，并区分修改、查询和查询的返回值。'}</Feedback>}
 </section>;
}
