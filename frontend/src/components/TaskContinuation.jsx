import {useEffect,useLayoutEffect,useRef,useState} from 'react';
import {createPortal} from 'react-dom';
import {ArrowRight,Check,X} from 'lucide-react';
import {planActions} from '@/lib/learningSummaryModel.js';
import './TaskContinuation.css';

export default function TaskContinuation({owner,snapshot,training=[],actions=[],content,onOpen,update,suspended=false,insideStudy=false}){
 const previous=useRef(null),live=useRef(owner),continued=useRef(new Set()),[completion,setCompletion]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState('');live.current=owner;
 const [host,setHost]=useState(null);useLayoutEffect(()=>setHost(insideStudy?document.getElementById('tb-study-continuation'):null),[insideStudy]);
 useEffect(()=>{
  const before=previous.current,done=new Map((snapshot?.plan?.tasks||[]).filter(task=>task.status==='done').map(task=>[task.key,task.title])),accepted=new Map(training.filter(row=>row.accepted).map(row=>[row.id,row.title]));
  if(before?.owner===owner){if(before.ready&&snapshot&&!suspended){const task=[...done].find(([key])=>!before.done.has(key)&&!continued.current.has(key)),problem=[...accepted].find(([id])=>!before.accepted.has(id));if(task||problem)setCompletion({owner,id:(task||problem)[0],title:(task||problem)[1]||'这项任务'});}}
  else{setCompletion(null);continued.current.clear();}
  previous.current={owner,done,accepted,ready:Boolean(snapshot)&&!suspended};
 },[owner,snapshot,training,suspended]);
 const planned=planActions(snapshot)||[],manual=(snapshot?.plan?.tasks||[]).find(task=>task.status!=='done'&&task.id===content?.id&&task.kind==='lecture'&&content.kind==='lecture');
 const fresh=item=>item.id!==completion?.id&&item.id!==content?.id&&item.id!=='summary'&&!item.completed&&!(item.kind==='problem'&&training.some(row=>row.id===item.id&&row.accepted));
 const next=planned.find(fresh)||actions.find(fresh);
 const finish=async()=>{const started=owner;continued.current.add(manual.key);setBusy(true);setError('');try{const value=await update('complete',{key:manual.key});if(live.current!==started||!value)return;const next=(planActions(value)||[])[0]||actions.find(item=>item.id!==manual.id&&fresh(item));setCompletion(null);if(next)onOpen(next);}catch(issue){continued.current.delete(manual.key);if(live.current===started)setError(issue.message);}finally{if(live.current===started)setBusy(false);}};
 if(suspended||!manual&&(!completion||completion.owner!==owner||!next))return null;
 const bar=<div className="task-flow-bar" role="region" aria-label="接续学习">{manual?<><span>{manual.title}</span><button disabled={busy} onClick={finish}><Check size={15}/>完成并继续<ArrowRight size={15}/></button></>:<><span><Check size={15}/>已完成 {completion.title}</span><button onClick={()=>{setCompletion(null);onOpen(next);}}>下一项：{next.title}<ArrowRight size={15}/></button><button className="task-flow-dismiss" aria-label="收起接续提示" onClick={()=>setCompletion(null)}><X size={14}/></button></>}{error&&<span role="alert">{error}</span>}</div>;
 return host?createPortal(bar,host):bar;
}
