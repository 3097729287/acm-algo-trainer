import {taskNeighbours} from '@/lib/taskNavigation.js';
import {useEffect,useRef,useState} from 'react';
import {createPortal} from 'react-dom';
import {ArrowLeft,ArrowRight,Check,Clock,Shuffle,X} from 'lucide-react';
import {trainingDay} from '@/lib/trainingDate.js';
import {dialogPointerDown,dialogBackdropClick} from '@/lib/dialogBackdrop.js';
import './LearningSummary.css';

export function WeeklyLearningTasks({plan,onOpen,onPostpone,onReplace,compact=false}) {
 if(!plan)return null;
 const tasks=Array.isArray(plan.tasks)?plan.tasks:[];
 if(!tasks.length)return <p className="summary-muted">这份记录没有周计划任务。</p>;
 return <section className={'summary-week'+(compact?' summary-week-compact':'')} aria-label="本周学习任务">
  <div className="summary-week-title"><strong>本周学习任务</strong><span>{plan.week?plan.week+' 起 · ':''}{tasks.filter(t=>t.status==='done').length}/{tasks.length}</span></div>
  <div className="summary-table-scroll"><table><thead><tr><th>日期</th><th>顺序与任务</th><th>预计用时</th><th>完成状态</th></tr></thead><tbody>
   {tasks.map(task=><tr key={task.key} data-done={task.status==='done'}><td>{task.date?.slice(5)||'—'}{task.kind==='calendar-contest'&&<small>{new Date(task.event.startAt).toLocaleTimeString('zh-CN',{timeZone:'Asia/Shanghai',hour:'2-digit',minute:'2-digit',hour12:false})}</small>}</td><td>{onOpen?<button type="button" className="summary-link" onClick={()=>onOpen(task)}>{task.order}. {task.title}<ArrowRight size={14}/></button>:<span>{task.order}. {task.title}</span>}{!compact&&<small>{task.condition}</small>}</td><td>{task.minutes}分钟</td><td>{task.status==='done'?<span className="summary-done"><Check size={14}/>已完成</span>:<><span>{task.kind==='calendar-contest'?{upcoming:'尚未开始',live:'进行中',ended:'已结束，未完成'}[task.availability]:'待完成'}</span>{onPostpone&&task.kind!=='calendar-contest'&&<button type="button" className="summary-link" aria-label={'推迟 '+task.title} onClick={()=>onPostpone(task)}><Clock size={14}/></button>}{onReplace&&task.kind==='problem'&&<button className="summary-link" aria-label={'换题 '+task.title} onClick={()=>onReplace(task)}><Shuffle size={14}/></button>}</>}</td></tr>)}
  </tbody></table></div>
  {plan.waiting?.length>0&&<p className="summary-muted">{plan.waiting.length}项等待后续预算，按优先顺序接续。</p>}
  {plan.gaps?.map(gap=><p key={gap} className="summary-muted">{gap}</p>)}
 </section>;
}

// Only the task's question or reflection uses a modal. Planning lives in Tasks;
// there is no movable, pinned or automatically reopened study window.
export default function LearningTaskDialog({model,api,onOpenTask,navigationPlan}){
 const [task,setTask]=useState(null),[quiz,setQuiz]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),dialog=useRef(null),generation=useRef(0),current=useRef({model,api});current.current={model,api};
 useEffect(()=>{
  const requested=async event=>{const task=event.detail;if(!['quiz','reflection'].includes(task?.kind))return;const epoch=++generation.current;setTask(task);setQuiz(null);setError('');current.current.model.setOpen(true);if(task.kind==='quiz')try{const quiz=await current.current.api('learning-summary/quiz?id='+encodeURIComponent(task.id));if(epoch===generation.current)setQuiz(quiz);}catch(issue){if(epoch===generation.current)setError(issue.message);}};
  window.addEventListener('tb:learning-summary-task',requested);return()=>{generation.current++;window.removeEventListener('tb:learning-summary-task',requested);};
 },[]);
 useEffect(()=>{if(!model.snapshot||!model.open){generation.current++;setTask(null);}},[Boolean(model.snapshot),model.open]);
 useEffect(()=>{const node=dialog.current;if(task&&model.open&&node){node.showModal();return()=>node.close();}},[task,model.open]);
 const close=()=>{generation.current++;model.setOpen(false);setTask(null);};
 const submit=async(action,fields)=>{setBusy(true);setError('');try{const result=await model.update(action,fields);close();const next=result?.plan?.tasks.find(item=>item.status!=='done'&&item.date<=trainingDay());if(next)onOpenTask(next);}catch(issue){setError(issue.message);}finally{setBusy(false);}};
 if(!task||!model.open)return null;
 const navigation=taskNeighbours({planId:model.snapshot?.plan?.id,taskKey:task.key},navigationPlan||model.snapshot?.plan),navigate=target=>{if(target){close();onOpenTask(target);}};
 return createPortal(<dialog ref={dialog} className="learning-task-dialog" aria-label={task.kind==='quiz'?'原理检查':'任务复盘'} onCancel={event=>{event.preventDefault();close();}} onPointerDown={dialogPointerDown} onClick={dialogBackdropClick}><header><button type="button" className="icon-button" aria-label="上一项" disabled={!navigation.previous} onClick={()=>navigate(navigation.previous)}><ArrowLeft size={17}/></button><h2>{task.title||'原理检查'}</h2><button type="button" className="task-text" disabled={!navigation.next} onClick={()=>navigate(navigation.next)}>{navigation.label}<ArrowRight size={16}/></button><button className="icon-button" aria-label="关闭任务" onClick={close}><X size={18}/></button></header>{error&&<p role="alert" className="connection-error">{error}</p>}{task.kind==='quiz'?(quiz?<section className="summary-quiz"><h3>{quiz.question}</h3><div className="summary-quiz-options">{quiz.options.map((answer,index)=><button key={index} disabled={busy} onClick={()=>submit('quiz',{topicId:quiz.topicId,answer:index})}>{answer}</button>)}</div></section>:<p role="status">正在读取检查题…</p>):<form onSubmit={event=>{event.preventDefault();submit(task.contestId?'reflect':'complete',{key:task.key,...(task.contestId?{note:new FormData(event.currentTarget).get('note')}:{})});}}>{task.contestId&&<label>这次训练的卡点与下一步<textarea name="note" required minLength={5} maxLength={2000}/></label>}<button className="primary" disabled={busy}>完成并继续下一项<ArrowRight size={16}/></button></form>}</dialog>,document.body);
}
