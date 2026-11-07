import {useEffect,useLayoutEffect,useRef,useState} from 'react';
import {createPortal} from 'react-dom';
import {ArrowRight,Check} from 'lucide-react';
import {planActions} from '@/lib/learningSummaryModel.js';
import './TaskContinuation.css';

export default function TaskContinuation({owner,snapshot,training=[],actions=[],content,onOpen,update,suspended=false,insideStudy=false}){
 const live=useRef(owner),[busy,setBusy]=useState(false),[error,setError]=useState('');live.current=owner;
 const [host,setHost]=useState(null);useLayoutEffect(()=>setHost(insideStudy?document.getElementById('tb-study-continuation'):null),[insideStudy]);
 useEffect(()=>{setBusy(false);setError('');},[owner]);
 const manual=(snapshot?.plan?.tasks||[]).find(task=>task.status!=='done'&&task.id===content?.id&&task.kind==='lecture'&&content?.kind==='lecture');
 const fresh=item=>item.id!==content?.id&&item.id!=='summary'&&!item.completed&&!(item.kind==='problem'&&training.some(row=>row.id===item.id&&row.accepted));
 const finish=async()=>{const started=owner;setBusy(true);setError('');try{const value=await update('complete',{key:manual.key});if(live.current!==started||!value)return;const next=(planActions(value)||[])[0]||(!value?.plan?actions.find(item=>item.id!==manual.id&&fresh(item)):null);if(next)onOpen(next);}catch(issue){if(live.current===started)setError(issue.message);}finally{if(live.current===started)setBusy(false);}};
 if(!insideStudy||!host||suspended||!manual)return null;
 return createPortal(<div className="task-flow-bar" role="region" aria-label="接续学习"><span>{manual.title}</span><button disabled={busy} onClick={finish}><Check size={15}/>完成并继续<ArrowRight size={15}/></button>{error&&<span role="alert">{error}</span>}</div>,host);
}
