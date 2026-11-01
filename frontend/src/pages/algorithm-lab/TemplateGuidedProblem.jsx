import {useState} from 'react';
import {ArrowRight,Check,NotebookPen,RotateCcw} from 'lucide-react';
import {CodeBlock,Feedback,Hints} from './LabParts.jsx';
import {parseTraceValues} from './templateTraceModels.js';
import {guidedMini} from './templateGuidedModels.js';
import {matchesTemplateProblem} from '@/lib/templateProblemMatch.js';

const STEPS=['读条件','亲手验证','连接代码','查错与迁移','自行实现'];
export default function TemplateGuidedProblem({task,draft={},update,rows,onTrain,lockedProblems=[]}){
 const step=Math.max(0,Math.min(4,Number(draft.step)||0)),[checked,setChecked]=useState(false);
 const input=draft.input??task.values.join(' '),extra=draft.extra??(task.extra||[]).join(' '),parameter=Number(draft.parameter??task.parameter);
 const parsed=parseTraceValues(input),second=parseTraceValues(extra),model=parsed.error?parsed:second.error?second:guidedMini(task.kind,parsed.values,parameter,second.values);
 const row=rows.find(r=>matchesTemplateProblem(r,task));
 const locked=lockedProblems.find(r=>matchesTemplateProblem(r,task));
 const change=delta=>{setChecked(false);update(old=>({...old,...delta}));};
 if(locked)return <section className="lab-panel"><h2>{task.title}</h2><p>本题或同源别名正在模拟赛中，交卷后可查看指导。</p><button type="button" className="lab-icon-button" aria-label="返回考场" onClick={()=>onTrain?.(locked.id)}><NotebookPen size={18}/></button></section>;
 return <section className="lab-panel template-guided" aria-label={'跟做 '+task.pid}>
  <h2>{task.title}</h2><a href={task.url} target="_blank" rel="noreferrer">原题链接 ↗</a>
  <nav className="lab-guided-steps" aria-label="跟做步骤">{STEPS.map((name,i)=><button type="button" key={name} aria-current={step===i?'step':undefined} onClick={()=>change({step:i,...(i===2||i===3?{assisted:true}:{})})}>{i+1} {name}</button>)}</nav>
  {step===0&&<><p>{task.recognize}</p><p>{task.state}</p>{task.samples.map((sample,i)=><details key={i}><summary>原站样例 {i+1}</summary><pre>{sample.input}</pre><pre>{sample.output}</pre></details>)}</>}
  {step===1&&<>
   <p>{task.changes}</p><div className="template-trace-inputs">{task.kind!=='wave'&&<label>小实验数组<input aria-label="跟做实验数组" value={input} onChange={e=>change({input:e.target.value,assisted:true})}/></label>}{!['cuts','schedule'].includes(task.kind)&&<label>{task.kind==='wave'?'项号':task.kind==='nearest'||task.kind==='lookup'?'查询值':'宽度'}<input aria-label="跟做实验参数" type="number" value={draft.parameter??task.parameter} onChange={e=>change({parameter:e.target.value,assisted:true})}/></label>}{task.extra&&<label>{task.kind==='schedule'?'对应的截止时间':'切割值集合'}<input aria-label="跟做第二组数据" value={extra} onChange={e=>change({extra:e.target.value,assisted:true})}/></label>}</div>
   <button type="button" className="lab-icon-button" aria-label="重置小实验" onClick={()=>change({input:task.values.join(' '),extra:(task.extra||[]).join(' '),parameter:task.parameter})}><RotateCcw size={17}/></button>
   {model.error?<Feedback>{model.error}</Feedback>:<><p>{model.label}</p><div className="template-trace-strip">{model.values.map((value,i)=><div key={i} data-active={!model.selected.length||model.selected.includes(i)}><small>{i}</small><strong>{value}</strong></div>)}</div><p role="status">{model.state}</p></>}
   <p className="lab-caption">下方预测固定使用本题初始数据，上方可以另改数据做对照。</p><form className="operations-predict" onSubmit={e=>{e.preventDefault();update(old=>({...old,assisted:true}));setChecked(true);}}><label>{task.question}<input aria-label="跟做预测答案" value={draft.prediction||''} onChange={e=>change({prediction:e.target.value})}/></label><button className="lab-icon-button" aria-label="验证预测" disabled={!draft.prediction?.trim()}><Check size={17}/></button></form>{checked&&<Feedback good={Number(draft.prediction)===task.answer}>{Number(draft.prediction)===task.answer?'与固定题例一致。再修改小实验的数据，观察哪个状态首先改变。':'还不一致。先核对统计的是值、位置、长度还是段数。'}</Feedback>}
  </>}
  {step===2&&<><p>{task.state}</p><p>{task.changes}</p><CodeBlock code={task.line}/><p>{task.lineReason}</p><label>把每个变量对应到题目的对象<textarea aria-label="我的状态说明" value={draft.state||''} onChange={e=>change({state:e.target.value})}/></label></>}
  {step===3&&<><p>{task.bug}</p><textarea aria-label="我的反例与修改" value={draft.bug||''} onChange={e=>change({bug:e.target.value})}/><Hints items={[task.bugReason]} id={task.pid} drafts={draft} updateDraft={(key,value)=>change({[key]:value,assisted:true})}/><details onToggle={event=>{if(event.currentTarget.open)change({assisted:true});}}><summary>参考程序</summary><CodeBlock code={task.referenceCode} copy/></details></>}
  {step===4&&<><p>根据原题独立写输入、核心算法与输出。实验草稿和核对记录会保留；自检不会产生正式 AC。</p><ul className="seq-checklist">{task.tests.map((test,i)=><li key={test}><label><input type="checkbox" checked={draft.tests?.includes(i)||false} onChange={()=>change({tests:draft.tests?.includes(i)?draft.tests.filter(x=>x!==i):[...(draft.tests||[]),i]})}/>{test}</label></li>)}</ul>{row&&onTrain&&<button type="button" className="lab-icon-button" aria-label={locked?'返回考场':'进入工作台独立实现'} onClick={()=>onTrain(row.id,locked?undefined:{assisted:!!draft.assisted})}><NotebookPen size={18}/></button>}</>}
  {step<4&&<button type="button" className="lab-icon-button" aria-label="继续跟做" onClick={()=>change({step:step+1,...(step+1===2||step+1===3?{assisted:true}:{})})}><ArrowRight size={17}/></button>}
 </section>;
}
