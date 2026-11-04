import {useEffect,useLayoutEffect,useRef,useState} from 'react';
import {createPortal} from 'react-dom';
import {ArrowRight,Check,ClipboardList,Clock,Maximize2,Minimize2,Pin,PinOff,RefreshCw,Settings2,X,ChevronDown,ChevronUp,History,Trash2,Shuffle} from 'lucide-react';
import {changedParagraphs} from '@/lib/learningSummaryModel.js';
import './LearningSummary.css';

export function WeeklyLearningTasks({plan,onOpen,onPostpone,onReplace,compact=false}) {
 if(!plan)return null;
 return <section className={'summary-week'+(compact?' summary-week-compact':'')} aria-label="本周学习任务">
  <div className="summary-week-title"><strong>本周学习任务</strong><span>{plan.week} 起 · {plan.tasks.filter(t=>t.status==='done').length}/{plan.tasks.length}</span></div>
  <div className="summary-table-scroll"><table><thead><tr><th>日期</th><th>顺序与任务</th><th>预计用时</th><th>完成状态</th></tr></thead><tbody>
   {plan.tasks.map(task=><tr key={task.key} data-done={task.status==='done'}><td>{task.date.slice(5)}</td><td><button type="button" className="summary-link" onClick={()=>onOpen(task)}>{task.order}. {task.title}<ArrowRight size={14}/></button>{!compact&&<small>{task.condition}</small>}</td><td>{task.minutes}分钟</td><td>{task.status==='done'?<span className="summary-done"><Check size={14}/>已完成</span>:<><span>待完成</span>{onPostpone&&<button type="button" className="summary-link" aria-label={'推迟 '+task.title} onClick={()=>onPostpone(task)}><Clock size={14}/></button>}{onReplace&&task.kind==='problem'&&<button className="summary-link" aria-label={'换题 '+task.title} onClick={()=>onReplace(task)}><Shuffle size={14}/></button>}</>}</td></tr>)}
  </tbody></table></div>
  {plan.waiting?.length>0&&<p className="summary-muted">{plan.waiting.length}项等待后续预算，按优先顺序接续。</p>}
  {plan.gaps?.map(gap=><p key={gap} className="summary-muted">{gap}</p>)}
 </section>;
}

function Configuration({snapshot,update,onClose,onError}) {
 const [config,setConfig]=useState(()=>snapshot.config),[tracks,setTracks]=useState(()=>snapshot.plan?.tracks||snapshot.proposal?.tracks||[]),[saving,setSaving]=useState(false);
 const patch=value=>setConfig(old=>({...old,...value}));
 const submit=async event=>{event.preventDefault();setSaving(true);try{const value=await update('configure',{config,...(tracks.length?{tracks}:{})});onClose(value);}catch(issue){onError(issue.message);}finally{setSaving(false);}};
 return <form className="summary-config" onSubmit={submit} aria-label="目标与时间设置">
  <label>目标类型<select value={config.goal.kind} onChange={event=>patch({goal:{...config.goal,kind:event.target.value}})}><option value="xcpc">ICPC／CCPC 奖牌</option><option value="cf">Codeforces 分数</option><option value="lanqiao">蓝桥杯奖项</option><option value="topic">专题学习</option></select></label>
  <label>具体目标<input required maxLength={160} value={config.goal.title} onChange={event=>patch({goal:{...config.goal,title:event.target.value}})}/></label>
  <label>截止日期（可留空）<input type="date" value={config.goal.deadline||''} onChange={event=>patch({goal:{...config.goal,deadline:event.target.value}})}/></label>
  <div className="summary-config-row">{[['weekdayMinutes','工作日每日分钟'],['weekendMinutes','周末每日分钟']].map(([key,label])=><label key={key}>{label}<input required type="number" min="0" max="720" value={config[key]??''} onChange={event=>patch({[key]:event.target.value===''?null:Number(event.target.value)})}/></label>)}</div>
  <fieldset><legend>休息日</legend>{['一','二','三','四','五','六','日'].map((title,index)=><label key={index}><input type="checkbox" checked={config.restDays.includes(index)} onChange={event=>patch({restDays:event.target.checked?[...config.restDays,index]:config.restDays.filter(d=>d!==index)})}/>周{title}</label>)}</fieldset>
  <fieldset><legend>学习主线（共用总时间，最多五条）</legend><div className="summary-topic-options">{snapshot.availableTopics.map(topic=><label key={topic.id}><input type="checkbox" checked={tracks.includes(topic.id)} disabled={!tracks.includes(topic.id)&&tracks.length>=5} onChange={event=>setTracks(old=>event.target.checked?[...old,topic.id]:old.filter(id=>id!==topic.id))}/>{topic.title}</label>)}</div></fieldset>
  <label className="summary-check"><input type="checkbox" checked={config.team} onChange={event=>patch({team:event.target.checked})}/>团队备赛</label>{config.team&&<label>本人职责<input value={config.role} maxLength={80} onChange={event=>patch({role:event.target.value})}/></label>}
  <div className="summary-actions"><button type="button" onClick={onClose}>返回文章</button><button type="submit" className="primary" disabled={saving}>{saving?'正在整理…':'生成安排'}</button></div>
 </form>;
}

const difficultyReasons={meaning:'题意没理解',idea:'没有思路',implementation:'知道方法但写不出',bug:'代码出错',forgot:'旧知识忘了',schedule:'任务安排不合适',easy:'任务太简单',hard:'任务太难',verify:'不知道怎样检验',transfer:'学习后仍不会做题'};

export default function LearningSummary({model,api,onOpenTask,currentProblem,currentContent,rows=[]}) {
 const {snapshot,open,setOpen,update}=model;
 const [article,setArticle]=useState([]),[configuration,setConfiguration]=useState(false),[difficulty,setDifficulty]=useState(false),[history,setHistory]=useState(false),[historical,setHistorical]=useState(null),[quiz,setQuiz]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[topic,setTopic]=useState('');
 const [view,setView]=useState({mode:'float',pinned:true,collapsed:false,detailed:false,tone:'平实',follow:true,x:80,y:70,width:760,height:650,scrollTop:0});
 const root=useRef(null),content=useRef(null),snapshotRef=useRef(snapshot),viewRef=useRef(view),restored=useRef(false),seenTimer=useRef(null),viewTimer=useRef(null),seen=useRef({}),drag=useRef(null);
 snapshotRef.current=snapshot;viewRef.current=view;
 useEffect(()=>{restored.current=false;setArticle([]);setConfiguration(false);setHistorical(null);setQuiz(null);setHistory(false);setError('');},[Boolean(snapshot)]);
 useEffect(()=>{if(!snapshot||restored.current)return;restored.current=true;setView(old=>({...old,...snapshot.view}));setArticle(snapshot.article||[]);},[snapshot]);
 useEffect(()=>{if(!article.length&&snapshot?.article?.length)setArticle(snapshot.article);},[snapshot?.article,article.length]);
 useLayoutEffect(()=>{if(open&&content.current)content.current.scrollTop=viewRef.current.scrollTop||0;},[open,view.mode,configuration,historical?.id]);
 useEffect(()=>{
  if(!open||!view.follow||!snapshot||!currentProblem&&!currentContent||snapshot?.activeContest)return;
  const row=rows.find(r=>r.id===currentProblem),matches=snapshot.availableTopics.filter(t=>snapshot.topics.find(p=>p.id===t.id)?.evidence?.some(e=>e.problemId===currentProblem)||row&&row.tags?.some(tag=>t.tags?.includes(tag))||currentContent&&(currentContent.kind==='lab'&&t.course===currentContent.id||currentContent.kind==='template'&&t.template===currentContent.id||currentContent.kind==='lecture'&&t.lectures?.includes(currentContent.id)));
  const track=matches.find(t=>snapshot.plan?.tracks.includes(t.id))||matches[0];if(track)setTopic(track.id);
 },[open,currentProblem,currentContent?.id,view.follow,snapshot?.plan?.id]);
 useEffect(()=>{if(!open||view.mode==='full'||view.pinned)return;const outside=event=>{if(!root.current?.contains(event.target))setOpen(false);};document.addEventListener('pointerdown',outside);return()=>document.removeEventListener('pointerdown',outside);},[open,view.mode,view.pinned]);
 useEffect(()=>{
  const key=event=>{if(open&&event.key==='Escape'&&!event.target.closest('input,select,textarea')){event.preventDefault();if(configuration)setConfiguration(false);else if(difficulty)setDifficulty(false);else if(historical)setHistorical(null);else if(quiz)setQuiz(null);else setOpen(false);}};
  document.addEventListener('keydown',key);return()=>document.removeEventListener('keydown',key);
 },[open,configuration,difficulty,historical,quiz,setOpen]);
 useEffect(()=>()=>{clearTimeout(seenTimer.current);clearTimeout(viewTimer.current);},[]);
 const saveView=next=>{const value={...viewRef.current,...next};viewRef.current=value;setView(value);clearTimeout(viewTimer.current);viewTimer.current=setTimeout(()=>update('view',{view:viewRef.current}).catch(issue=>setError(issue.message)),500);};
 const act=async(action,fields={})=>{setBusy(true);setError('');try{const value=await update(action,fields);if(value?.article)setArticle(value.article);return value;}catch(issue){setError(issue.message);}finally{setBusy(false);}};
 const acknowledge=paragraph=>{
  if(snapshotRef.current?.seen?.[paragraph.id]===paragraph.hash)return;
  seen.current[paragraph.id]=paragraph.hash;clearTimeout(seenTimer.current);seenTimer.current=setTimeout(()=>{const paragraphs=seen.current;seen.current={};update('seen',{paragraphs}).catch(()=>{});},250);
 };
 const applyArticle=()=>{const scroll=content.current?.scrollTop||0;setArticle(snapshot.article);requestAnimationFrame(()=>{if(content.current)content.current.scrollTop=scroll;});};
 const openTask=async task=>{
  if(task.kind==='quiz'){try{setQuiz(await api('learning-summary/quiz?id='+encodeURIComponent(task.id)));}catch(issue){setError(issue.message);}return;}
  if(task.kind==='mixed'){
   if(task.contestId&&task.status!=='done'){onOpenTask(task);if(!view.pinned)setOpen(false);return;}
   try{setBusy(true);const result=await api('learning-summary/start',{key:task.key,planId:snapshotRef.current.plan.id});await model.refresh();onOpenTask({...task,contestId:result.contest.id});if(!view.pinned)setOpen(false);}catch(issue){setError(issue.message);}finally{setBusy(false);}return;
  }
  if(task.kind==='reflection')return;
  onOpenTask(task);if(!view.pinned)setOpen(false);
 };
 const postpone=task=>{const current=new Date(task.date+'T00:00:00+08:00');current.setUTCDate(current.getUTCDate()+1);act('postpone',{key:task.key,date:new Date(current.getTime()+8*3600000).toISOString().slice(0,10)});};
 useEffect(()=>{
  const requested=event=>{setOpen(true);if(event.detail?.id!=='summary')openTask(event.detail);};
  window.addEventListener('tb:learning-summary-task',requested);return()=>window.removeEventListener('tb:learning-summary-task',requested);
 },[snapshot?.revision,view.pinned]);
 if(!open)return null;
 const floating=view.mode!=='full',changed=Boolean(snapshot&&article.length&&snapshot.article.some(p=>article.find(a=>a.id===p.id)?.hash!==p.hash)),display=historical?.article||article,unread=new Set(changedParagraphs(display,snapshot?.seen)),plan=historical?.plan||snapshot?.plan;
 const rect=floating?{left:Math.max(0,Math.min(view.x,innerWidth-280)),top:Math.max(0,Math.min(view.y,innerHeight-44)),width:Math.min(view.width,innerWidth),height:view.collapsed?44:Math.min(view.height,innerHeight-Math.max(0,Math.min(view.y,innerHeight-44)))}:{};
 const selected=snapshot?.topics?.find(t=>t.id===topic);
 return createPortal(<section ref={root} className={'learning-summary '+(floating?'summary-floating':'summary-full')+(view.collapsed?' summary-collapsed':'')} style={rect} role="dialog" aria-label="学习进度与周计划" data-pinned={view.pinned} onPointerMove={event=>{if(!drag.current||!root.current?.hasPointerCapture(event.pointerId))return;const {x,y,px,py,width,height,resize}=drag.current;if(resize)saveView({width:Math.max(360,Math.min(innerWidth-x,width+event.clientX-px)),height:Math.max(200,Math.min(innerHeight-y,height+event.clientY-py))});else saveView({x:Math.max(0,Math.min(innerWidth-280,x+event.clientX-px)),y:Math.max(0,Math.min(innerHeight-44,y+event.clientY-py))});}} onPointerUp={()=>{drag.current=null;}}>
  <header className="summary-header" onPointerDown={event=>{if(!floating||event.button!==0||event.target.closest('button'))return;drag.current={...viewRef.current,px:event.clientX,py:event.clientY};root.current.setPointerCapture(event.pointerId);}}><ClipboardList size={18}/><strong>学习进度与周计划</strong><span className="summary-spacer"/>
   <button className="summary-icon" aria-label="目标与时间设置" title="目标与时间" onClick={()=>setConfiguration(v=>!v)}><Settings2 size={17}/></button>
   <button className="summary-icon" aria-label={view.pinned?'取消置顶':'在 ToBe 内置顶'} title="在 ToBe 内置顶" onClick={()=>saveView({pinned:!view.pinned})}>{view.pinned?<Pin size={17}/>:<PinOff size={17}/>}</button>
   <button className="summary-icon" aria-label={floating?'全屏阅读规划':'恢复浮窗'} onClick={()=>saveView({mode:floating?'full':'float',collapsed:false})}>{floating?<Maximize2 size={17}/>:<Minimize2 size={17}/>}</button>
   {floating&&<button className="summary-icon" aria-label={view.collapsed?'展开规划':'收起为标题条'} onClick={()=>saveView({collapsed:!view.collapsed})}>{view.collapsed?<ChevronDown size={17}/>:<ChevronUp size={17}/>}</button>}
   <button className="summary-icon" aria-label="关闭学习规划" onClick={()=>setOpen(false)}><X size={18}/></button>
  </header>
  {!view.collapsed&&<><nav className="summary-controls" aria-label="规划阅读设置"><button className="summary-link" onClick={()=>{setHistorical(null);setTopic('');}}>整体规划</button><select aria-label="当前专题" value={topic} onChange={e=>setTopic(e.target.value)}><option value="">所有主线</option>{snapshot?.availableTopics?.map(t=><option key={t.id} value={t.id}>{t.title}</option>)}</select><label><input type="checkbox" checked={view.follow} onChange={e=>saveView({follow:e.target.checked})}/>跟随当前内容</label><label><input type="checkbox" checked={view.detailed} onChange={e=>saveView({detailed:e.target.checked})}/>详细</label><select aria-label="规划语气" value={view.tone} onChange={e=>saveView({tone:e.target.value})}><option>平实</option><option>鼓励</option><option>直接</option></select><button className="summary-icon" aria-label="查看历史规划" onClick={()=>setHistory(v=>!v)}><History size={17}/></button></nav>
  <main ref={content} className="summary-content" onScroll={event=>{saveView({scrollTop:Math.round(event.currentTarget.scrollTop)});}}>
   {(error||model.error)&&<p className="connection-error" role="alert">{error||model.error}</p>}
   {!snapshot?<p role="status">正在读取已保存规划…</p>:configuration?<Configuration snapshot={snapshot} update={update} onClose={value=>{if(value?.article)setArticle(value.article);setConfiguration(false);}} onError={setError}/>:<>
    {changed&&!historical&&<button className="summary-update" onClick={applyArticle}><RefreshCw size={15}/>说明有更新，点此查看</button>}
    {snapshot.activeContest&&<p className="summary-muted">正在限时训练，保留此前规划；本场分析交卷后更新。</p>}
    {snapshot.stalled&&!snapshot.activeContest&&<button className="summary-update" onClick={()=>setDifficulty(true)}>这几天没有新的推进，先选择遇到的情况<ArrowRight size={15}/></button>}
    {historical&&<p className="summary-muted">历史快照 · {historical.at} · {historical.reason}<button className="summary-link" onClick={()=>setHistorical(null)}>回到当前</button></p>}
    {history&&<div className="summary-history">{snapshot.history.length?snapshot.history.map(item=><div key={item.id}><button className="summary-link" onClick={async()=>{try{setHistorical(await api('learning-summary/history?id='+item.id));}catch(issue){setError(issue.message);}}}>{item.week||item.at.slice(0,10)} · {item.reason}</button><button className="summary-icon" aria-label={'删除历史 '+item.id} title="仅删除此文章及计划快照" onClick={()=>act('delete-history',{id:item.id})}><Trash2 size={15}/></button></div>):<p>周结束、阶段完成或采纳调整时保留快照。</p>}</div>}
    {selected&&<section className="summary-topic"><h2>{selected.title}</h2><p>{selected.label}；独立应用 {selected.independent} 题，延迟检验 {selected.retained} 题，综合迁移另行检验。</p><button className="summary-link" onClick={()=>openTask({kind:'quiz',id:topic})}>我已经会了／检查判断<ArrowRight size={14}/></button>{view.detailed&&selected.evidence.map(e=><button key={e.problemId} className="summary-link" onClick={()=>onOpenTask({kind:'problem',id:e.problemId,title:e.problemId})}>{e.problemId} · {e.date.slice(0,10)} · {e.firstPass?'一次通过':`${e.failures}次失败后通过`}</button>)}</section>}
    <article className="summary-article" aria-label="完整学习规划">{display.map(p=><section key={p.id} data-updated={!historical&&unread.has(p.id)||undefined} onPointerEnter={()=>acknowledge(p)} onFocus={()=>acknowledge(p)} tabIndex={0}><h2>{p.title}</h2><p>{view.tone==='鼓励'&&p.id==='next'?'先把眼前这一步做好。':''}{view.tone==='直接'?p.text.replace('你的总目标是','目标：').replace('你反馈','反馈'):p.text}</p>{p.id==='next'&&!historical&&plan?.tasks.find(t=>t.status!=='done')&&<button className="summary-link" onClick={()=>openTask(plan.tasks.find(t=>t.status!=='done'))}>进入这项任务<ArrowRight size={14}/></button>}{view.detailed&&p.id==='progress'&&<p className="summary-muted">依据来自正式提交、操作练习和复习；公开历史的独立性未知时只用于定位起点。有效学习时长累计 {Math.floor((snapshot.effectiveSeconds||0)/60)} 分钟，不据此提升掌握阶段。</p>}</section>)}</article>
    {!display.length&&<p>先设置目标与可用时间，整理符合已有证据的起点。</p>}
    {!snapshot.config.weekdayMinutes&&snapshot.config.weekdayMinutes!==0&&<button className="primary" onClick={()=>setConfiguration(true)}>设置可用时间</button>}
    {snapshot.proposal&&!historical&&<section className="summary-proposal" aria-label="待采纳方案"><h2>待采纳方案</h2><p>{snapshot.proposal.reason}</p>{snapshot.proposal.allocations.map(a=><p key={a.id}>{a.title}：本周 {a.minutes} 分钟；独立应用、隔日保持与综合迁移分别验证，周期待有足够证据后估算。</p>)}<p>共享周预算 {snapshot.proposal.days.reduce((s,d)=>s+d.minutes,0)} 分钟。{snapshot.plan?'采纳后按新分配推进，当前已学事实保留。':'采纳后整周任务进入“我的训练”。'}</p><div className="summary-actions"><button className="primary" disabled={busy} onClick={()=>act('accept',{proposalId:snapshot.proposal.id})}>采纳并开始</button><button disabled={busy} onClick={()=>act('dismiss')}>暂不采纳</button></div></section>}
    <WeeklyLearningTasks plan={plan} onOpen={openTask} onPostpone={historical?null:postpone} onReplace={historical?null:task=>act('replace',{key:task.key})}/>
    {!historical&&plan?.tasks.filter(t=>['lecture','reflection'].includes(t.kind)&&t.status!=='done').map(task=><button key={task.key} className="summary-link summary-confirm" disabled={busy} onClick={()=>act('complete',{key:task.key})}><Check size={15}/>确认{task.kind==='lecture'?'已读':'完成复盘'}：{task.title}</button>)}
    {!historical&&plan?.tasks.filter(t=>t.kind==='mixed'&&t.contestId&&t.status!=='done'&&!snapshot.activeContest).map(task=><form key={task.key} className="summary-quiz" onSubmit={async event=>{event.preventDefault();const data=new FormData(event.currentTarget);await act('reflect',{key:task.key,note:data.get('note')});}}><label>综合检验复盘<textarea name="note" required minLength={5} maxLength={2000} placeholder="记录实际卡点、边界或下次调整"/></label><button type="submit" disabled={busy}>保存复盘</button></form>)}
    {quiz&&<section className="summary-quiz" aria-label="原理检查"><h2>{quiz.question}</h2>{quiz.options.map((answer,index)=><button key={index} disabled={busy} onClick={async()=>{const result=await act('quiz',{topicId:quiz.topicId,answer:index});if(result)setQuiz(null);}}>{answer}</button>)}</section>}
    {!historical&&<><button className="summary-link" onClick={()=>setDifficulty(v=>!v)}>遇到困难<ArrowRight size={15}/></button>{difficulty&&<div className="summary-difficulty">{Object.entries(difficultyReasons).map(([reason,title])=><button key={reason} disabled={busy} onClick={async()=>{await act('difficulty',{reason});setDifficulty(false);applyArticle();}}>{title}</button>)}</div>}</>}
   </>}
  </main></>}
  {floating&&!view.collapsed&&<div className="summary-resize" role="separator" aria-label="调整规划窗口大小" onPointerDown={event=>{event.preventDefault();event.stopPropagation();drag.current={...viewRef.current,px:event.clientX,py:event.clientY,resize:true};root.current.setPointerCapture(event.pointerId);}}/>}
 </section>,document.body);
}
