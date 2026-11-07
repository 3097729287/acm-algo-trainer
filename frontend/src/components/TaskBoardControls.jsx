import {useEffect,useRef,useState} from 'react';
import {createPortal} from 'react-dom';
import {Check,X} from 'lucide-react';
import TimeBudget,{studyMinutes} from './TimeBudget.jsx';
import {dialogPointerDown,dialogBackdropClick} from '@/lib/dialogBackdrop.js';
import {opacityStyle} from '@/lib/surfaceOpacity.js';
import './TaskBoardControls.css';

export const MASTERY_STAGES=['阅读学习','原理检查','跟练实现','独立实现','独立解题','间隔复习','综合检验'];
export function masteryStage(topic){const level=Math.max(0,Math.min(6,Number.isInteger(topic?.level)?topic.level:0));return level===6&&topic.mixed?7:level;}
export function TopicMastery({topic}){
 const stage=masteryStage(topic),percent=Math.round(stage/MASTERY_STAGES.length*100);
 return <div className="topic-mastery"><div><span>掌握程度</span><strong>{percent}%</strong></div><div className="topic-mastery-bar" role="progressbar" aria-label={(topic?.title||'专题')+'掌握程度'} aria-valuemin={0} aria-valuemax={7} aria-valuenow={stage} aria-valuetext={`已完成 ${stage} / 7 阶段`}>{MASTERY_STAGES.map((title,index)=><i key={title} data-complete={index<stage} aria-hidden="true"/>)}</div></div>;
}
export function BoardDialog({title,onClose,busy=false,children,className=''}){
 const dialog=useRef(null);
 useEffect(()=>{const node=dialog.current,previous=document.activeElement;node.showModal();return()=>{node.close();if(previous?.isConnected)previous.focus({preventScroll:true});};},[]);
 return createPortal(<dialog ref={dialog} className={'task-settings-dialog '+className} style={opacityStyle('popups')} aria-label={title} onCancel={event=>{event.preventDefault();if(!busy)onClose();}} onPointerDown={dialogPointerDown} onClick={event=>{if(!busy)dialogBackdropClick(event);}}><header><h2>{title}</h2><button type="button" className="task-icon" aria-label={'关闭'+title} disabled={busy} onClick={onClose}><X size={18}/></button></header>{children}</dialog>,document.body);
}
export function TimeSettings({snapshot,onSave,onClose}){
 const [minutes,setMinutes]=useState(()=>studyMinutes(snapshot.config.weekdayMinutes)),[weekend,setWeekend]=useState(()=>studyMinutes(snapshot.config.weekendMinutes)),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const save=async event=>{event.preventDefault();setBusy(true);setError('');try{await onSave({config:{...snapshot.config,weekdayMinutes:minutes,weekendMinutes:weekend}});onClose();}catch(issue){setError(issue.message);}finally{setBusy(false);}};
 return <BoardDialog title="可用时间" onClose={onClose} busy={busy}><form onSubmit={save}><fieldset disabled={busy}><legend>平日</legend><TimeBudget value={minutes} onChange={setMinutes} label="平日可用时间"/></fieldset><fieldset disabled={busy}><legend>周末</legend><TimeBudget value={weekend} onChange={setWeekend} label="周末可用时间"/></fieldset>{error&&<p role="alert" className="connection-error">{error}</p>}<footer><button type="button" className="task-text" disabled={busy} onClick={onClose}>取消</button><button className="task-primary" disabled={busy}>{busy?'正在安排…':snapshot.plan?'更新安排':'按这个安排'}<Check size={15}/></button></footer></form></BoardDialog>;
}
export function MainlineSettings({snapshot,onSave,onClose}){
 const [goal,setGoal]=useState(()=>({...snapshot.config.goal})),[tracks,setTracks]=useState(()=>snapshot.plan?.tracks||snapshot.recommendation?.tracks||[]),[recommended,setRecommended]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const save=async event=>{event.preventDefault();setBusy(true);setError('');try{await onSave({config:{...snapshot.config,goal,weekdayMinutes:studyMinutes(snapshot.config.weekdayMinutes),weekendMinutes:studyMinutes(snapshot.config.weekendMinutes)},...(recommended?{recommended:true}:{tracks})});onClose();}catch(issue){setError(issue.message);}finally{setBusy(false);}};
 return <BoardDialog title="更换主线" onClose={onClose} busy={busy}><form onSubmit={save}><label>训练方向<select value={goal.kind} disabled={busy} onChange={event=>setGoal(value=>({...value,kind:event.target.value}))}>{[['xcpc','XCPC'],['cf','Codeforces'],['lanqiao','蓝桥杯'],['topic','专题训练']].map(([id,title])=><option key={id} value={id}>{title}</option>)}</select></label><label>训练目标<input value={goal.title} required maxLength={160} disabled={busy} onChange={event=>setGoal(value=>({...value,title:event.target.value}))}/></label><fieldset disabled={busy}><legend>学习主线</legend><label className="task-check"><input type="checkbox" checked={recommended} onChange={event=>setRecommended(event.target.checked)}/>按当前进度推荐</label>{!recommended&&<div className="task-track-options">{snapshot.availableTopics.map(topic=><label key={topic.id}><input type="checkbox" checked={tracks.includes(topic.id)} disabled={!tracks.includes(topic.id)&&tracks.length>=5} onChange={event=>setTracks(previous=>event.target.checked?[...previous,topic.id]:previous.filter(id=>id!==topic.id))}/>{topic.title}</label>)}</div>}</fieldset>{error&&<p role="alert" className="connection-error">{error}</p>}<footer><button type="button" className="task-text" disabled={busy} onClick={onClose}>取消</button><button className="task-primary" disabled={busy||!goal.title.trim()||!recommended&&!tracks.length}>更换并更新安排<Check size={15}/></button></footer></form></BoardDialog>;
}
export function TopicDetails({topic,rows=[],onClose,onCheck}){
 const stage=masteryStage(topic),byId=new Map(rows.map(row=>[row.id,row]));
 return <BoardDialog title={topic.title} onClose={onClose}><TopicMastery topic={topic}/><ol className="topic-stage-list">{MASTERY_STAGES.map((title,index)=><li key={title} data-complete={index<stage}><span>{index<stage?<Check size={14}/>:index+1}</span>{title}</li>)}</ol><p className="task-muted">每完成一个阶段点亮一格；七格全部点亮后，当前主线完成，可更换下一条主线。</p><div className="topic-evidence-summary"><span>解题记录 {topic.independent||0} 题</span><span>间隔复习 {topic.retained||0} 题</span></div>{topic.evidence?.length>0&&<ul className="topic-evidence-list">{topic.evidence.map((item,index)=><li key={item.problemId+':'+index}><span>{byId.get(item.problemId)?.title||item.problemId}</span><time dateTime={item.date}>{item.date?.slice(0,10)}</time></li>)}</ul>}<footer><button className="task-primary" onClick={()=>{onClose();onCheck({kind:'quiz',id:topic.id,title:topic.title});}}>检查判断</button></footer></BoardDialog>;
}
