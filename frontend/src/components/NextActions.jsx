import {useEffect,useId,useLayoutEffect,useMemo,useRef,useState} from 'react';
import {createPortal} from 'react-dom';
import {Check,Clock,Info,RefreshCw,X} from 'lucide-react';
import {RECOMMENDATION_KINDS} from '@/lib/recommendationKinds.js';
import {recommendationState} from '@/lib/nextActions.js';
import {KNOWLEDGE_BY_ID,LEARNING_COURSES} from '@/lib/learningCurriculum.js';
import {knowledgeState,knowledgeCoverage,startKnowledge,cancelKnowledge,rotateKnowledge,reconcileKnowledge,assignKnowledgeProblem} from '@/lib/knowledgeJourney.js';
import {dialogPointerDown,dialogBackdropClick} from '@/lib/dialogBackdrop.js';
import PopConfirm from './PopConfirm.jsx';
import './NextActions.css';

const icons=Object.fromEntries(Object.entries(RECOMMENDATION_KINDS).map(([kind,value])=>[kind,value.Icon]));
const labels=Object.fromEntries(Object.entries(RECOMMENDATION_KINDS).map(([kind,value])=>[kind,value.label]));
function RecommendationDialog({title,onClose,children,actions}){
 const node=useRef(null),id=useId();
 useEffect(()=>{const dialog=node.current;dialog.showModal();return()=>dialog.close();},[]);
 return createPortal(<dialog ref={node} className="recommendation-dialog" aria-labelledby={id} onPointerDown={dialogPointerDown} onClick={dialogBackdropClick} onCancel={event=>{event.preventDefault();onClose();}}>
  <header><h3 id={id}>{title}</h3><button type="button" className="icon-button" aria-label="关闭推荐说明" onClick={onClose}><X size={17}/></button></header>
  <div>{children}</div>{actions&&<footer>{actions}</footer>}
 </dialog>,document.body);
}
function Coverage({topic,rows,templates,ready}){
 const coverage=knowledgeCoverage(topic,rows,templates);if(!coverage)return null;
 return <dl className="knowledge-coverage" aria-label="当前学习材料覆盖">
  <div><dt>讲解</dt><dd>{coverage.lectures} 篇基础讲解</dd></div>
  <div><dt>实验</dt><dd>{coverage.experiment?'已有互动课程':'通过讲解与题目练习'}</dd></div>
  <div><dt>跟做</dt><dd>{coverage.guided?`${coverage.guided} 道完整例题`:'当前没有完整跟做题'}</dd></div>
  <div><dt>模板</dt><dd>{topic.template?!ready?'正在核对':coverage.implementation?'已有实现与操作练习':'待补齐':'按内容需要安排'}</dd></div>
  <div><dt>应用</dt><dd>{coverage.independent} 道未做过的完整题，按难度筛选</dd></div>
  <div><dt>复习</dt><dd>跨日用陌生题独立检验</dd></div>
 </dl>;
}
export default function NextActions({rows=[],training=[],insights,prefs={},setPrefs,api,availablePages=[],activeContest,onNavigate,onTrain,suspended=false,onOpenChange,reviewPlan={},preferencesReady=true}) {
 const [metadata,setMetadata]=useState({lists:[],templates:[],templatesReady:false}),[revision,setRevision]=useState(0),[now,setNow]=useState(Date.now);
 const [open,setOpen]=useState(false),[position,setPosition]=useState(null),[candidate,setCandidate]=useState(null),[information,setInformation]=useState(null),[cancelAnchor,setCancelAnchor]=useState(null);
 const root=useRef(null),flyout=useRef(null),trigger=useRef(null),touchOpened=useRef(false),closeTimer=useRef(null),ignoreFocus=useRef(false);
 const openChanged=useRef(onOpenChange);openChanged.current=onOpenChange;
 const popupId=useId(),reasonId=useId(),overlay=Boolean(candidate||information||cancelAnchor);
 useEffect(()=>{const refresh=()=>setRevision(value=>value+1);window.addEventListener('tb:training-lists-changed',refresh);return()=>window.removeEventListener('tb:training-lists-changed',refresh);},[]);
 useEffect(()=>{const update=()=>{if(!document.hidden)setNow(Date.now());};const timer=setInterval(update,60000);document.addEventListener('visibilitychange',update);return()=>{clearInterval(timer);document.removeEventListener('visibilitychange',update);};},[]);
 const scope=availablePages.join(',');
 useEffect(()=>{let alive=true;setMetadata({lists:[],templates:[],templatesReady:false});const requests=[['training-lists','lists'],['templates','templates']].filter(([page])=>availablePages.includes(page));Promise.allSettled(requests.map(async([page,key])=>[key,(await api(page))[key]||[]])).then(results=>{if(alive){const values=Object.fromEntries([['lists',[]],['templates',[]],...results.filter(item=>item.status==='fulfilled').map(item=>item.value)]);setMetadata({...values,templatesReady:results.some(item=>item.status==='fulfilled'&&item.value[0]==='templates')});}});return()=>{alive=false;};},[api,scope,revision]);
 const progression=JSON.stringify(Object.keys(LEARNING_COURSES).map(id=>[id,prefs.learningPaths?.[id]?.mode,prefs.learningPaths?.[id]?.labV1?.chapter]));
 const model=useMemo(()=>recommendationState({rows,training,insights:insights||{},prefs,...metadata,availablePages,activeContest,reviewPlan,now}),[rows,training,insights,metadata,scope,activeContest,reviewPlan,now,prefs.learnedLectures,prefs.learningPaths?.knowledgeLearning,progression]);
 const {items,journey}=model,primary=items[0],rest=items.slice(1),activeTopic=KNOWLEDGE_BY_ID[knowledgeState(prefs).activeTopicId];
 useEffect(()=>{if(setPrefs&&preferencesReady&&journey.journey)setPrefs(previous=>reconcileKnowledge(previous,journey));},[setPrefs,preferencesReady,journey]);
 const expandable=rest.length>0,expanded=Boolean(open&&!suspended&&!overlay&&primary&&expandable);
 useEffect(()=>{openChanged.current?.(expanded||overlay);},[expanded,overlay]);
 useEffect(()=>()=>openChanged.current?.(false),[]);
 useEffect(()=>{if(!primary||suspended||overlay||!expandable){clearTimeout(closeTimer.current);setOpen(false);}},[Boolean(primary),suspended,overlay,expandable]);
 const cancelClose=()=>{clearTimeout(closeTimer.current);closeTimer.current=null;};
 const contains=node=>Boolean(node&&(root.current?.contains(node)||flyout.current?.contains(node)));
 const show=()=>{cancelClose();if(!suspended&&!overlay&&expandable)setOpen(true);};
 const close=(restoreFocus=false)=>{cancelClose();setOpen(false);if(restoreFocus){ignoreFocus.current=true;trigger.current?.focus({preventScroll:true});ignoreFocus.current=false;}};
 const leave=(keepFocus=false)=>{cancelClose();closeTimer.current=setTimeout(()=>{if((!keepFocus||!contains(document.activeElement))&&!root.current?.matches(':hover')&&!flyout.current?.matches(':hover'))setOpen(false);},80);};
 useEffect(()=>()=>clearTimeout(closeTimer.current),[]);
 useEffect(()=>{
  if(!open||suspended||overlay)return;
  const outside=event=>{if(!contains(event.target))close();};
  const escape=event=>{if(event.key==='Escape'){event.preventDefault();event.stopPropagation();close(contains(document.activeElement));}};
  document.addEventListener('pointerdown',outside,true);document.addEventListener('keydown',escape,true);
  return()=>{document.removeEventListener('pointerdown',outside,true);document.removeEventListener('keydown',escape,true);};
 },[open,suspended,overlay]);
 useLayoutEffect(()=>{
  if(!expanded||!primary)return;
  const update=()=>{if(!root.current)return;const rect=root.current.getBoundingClientRect(),edge=10,width=Math.max(0,Math.min(flyout.current?.getBoundingClientRect().width||rect.width,innerWidth-edge*2)),top=Math.min(rect.bottom,Math.max(edge,innerHeight-100));setPosition({left:Math.max(edge,Math.min(rect.left,innerWidth-width-edge)),top,maxWidth:innerWidth-edge*2,maxHeight:Math.max(80,innerHeight-top-edge)});};
  update();const observer=typeof ResizeObserver==='undefined'?null:new ResizeObserver(update);if(root.current)observer?.observe(root.current);if(flyout.current)observer?.observe(flyout.current);window.addEventListener('resize',update);window.addEventListener('scroll',update,true);
  return()=>{observer?.disconnect();window.removeEventListener('resize',update);window.removeEventListener('scroll',update,true);};
 },[expanded,primary?.kind,primary?.id]);
 const start=item=>{
  close();if(item.kind==='knowledge'){item.completed?setInformation(item):setCandidate(item);return;}
  if(item.journeyTopicId)setPrefs?.(previous=>assignKnowledgeProblem(previous,{...item,id:item.problemId||item.id}));
  ['problem','stretch','review','template-problem','knowledge-review','random'].includes(item.kind)?onTrain(item.id):onNavigate(item);
 };
 const focusRow=last=>requestAnimationFrame(()=>{const buttons=flyout.current?.querySelectorAll('.next-actions-item');(last?buttons?.[buttons.length-1]:buttons?.[0])?.focus();});
 const openWithKeys=event=>{if(expandable&&(event.key==='ArrowDown'||event.key==='ArrowUp')){event.preventDefault();show();focusRow(event.key==='ArrowUp');}};
 const blur=event=>{if(!contains(event.relatedTarget))leave(true);};
 if(!preferencesReady)return <section ref={root} className="next-actions next-actions-pending" aria-label="下一步推荐做的事" aria-busy="true"><Clock size={18}/><span>正在准备下一步</span></section>;
 if(!primary)return null;
 const Icon=icons[primary.kind]||icons.problem;
 return <section ref={root} className="next-actions" aria-label="下一步推荐做的事" data-open={expanded} data-expandable={expandable} data-suspended={suspended} onPointerEnter={event=>{if(event.pointerType==='mouse')show();}} onPointerLeave={event=>{if(event.pointerType==='mouse')leave();}} onFocus={event=>{if(!ignoreFocus.current&&event.target.matches(':focus-visible'))show();}} onBlur={blur}>
  <button ref={trigger} type="button" className="next-actions-primary" data-recommendation={primary.kind} aria-label={`开始${labels[primary.kind]} ${primary.title}`} aria-describedby={reasonId} aria-expanded={expandable?expanded:undefined} aria-controls={expandable?popupId:undefined} disabled={suspended} onPointerDown={event=>{if(event.pointerType==='touch'&&expandable&&!open){touchOpened.current=true;show();}}} onClick={event=>{if(touchOpened.current){touchOpened.current=false;event.preventDefault();return;}start(primary);}} onKeyDown={openWithKeys}>
   <Icon size={18} aria-hidden="true"/><span className="next-actions-primary-copy"><strong>{primary.title}</strong></span>
  </button>
  <button type="button" className="next-action-control" aria-label="查看当前推荐依据" onClick={()=>{close();setInformation(primary);}}><Info size={14}/></button>
  {activeTopic&&<button type="button" className="next-action-control" aria-label={`取消${activeTopic.title}学习`} onClick={event=>{close();setCancelAnchor(event.currentTarget);}}><X size={15}/></button>}
  <span className="sr-only" id={reasonId}>{primary.reason}</span>
  {expanded&&createPortal(<div ref={flyout} className="next-actions-flyout" style={{...position,visibility:position?'visible':'hidden'}} onPointerEnter={event=>{if(event.pointerType==='mouse')cancelClose();}} onPointerLeave={event=>{if(event.pointerType==='mouse')leave();}} onFocus={cancelClose} onBlur={blur}>
   <section className="next-actions-popover" id={popupId} aria-label="推荐任务与依据" onKeyDown={event=>{if(!['ArrowDown','ArrowUp','Home','End'].includes(event.key))return;const buttons=[...event.currentTarget.querySelectorAll('.next-actions-item')],index=buttons.indexOf(document.activeElement);if(index<0)return;event.preventDefault();buttons[event.key==='Home'?0:event.key==='End'?buttons.length-1:(index+(event.key==='ArrowDown'?1:-1)+buttons.length)%buttons.length]?.focus();}}>
    <ul>{rest.map((item,index)=>{const ItemIcon=icons[item.kind]||icons.problem,description=`${popupId}-reason-${index}`;return <li key={`${item.kind}:${item.id}`} style={{'--task-index':index}} data-completed={item.completed||undefined}>
     <button type="button" className="next-actions-item" data-recommendation={item.kind} data-completed={item.completed||undefined} aria-label={`${item.completed?item.mastered?'已掌握':'今日已完成':'开始'+labels[item.kind]} ${item.title}`} aria-describedby={description} disabled={item.kind==='knowledge'&&!preferencesReady} onClick={()=>start(item)}><ItemIcon size={18} aria-hidden="true"/><span className="next-actions-item-copy"><strong>{item.title}</strong></span>{item.completed&&<Check size={15} aria-hidden="true"/>}</button>
     {item.kind==='knowledge'&&!item.completed&&<button type="button" className="next-action-control" aria-label="更换推荐知识点" disabled={!item.refreshable||!preferencesReady} onClick={event=>{event.stopPropagation();setPrefs?.(previous=>rotateKnowledge(previous));}}><RefreshCw size={14}/></button>}
     <button type="button" className="next-action-control" aria-label={`查看${item.title}的推荐依据`} onClick={()=>{close();setInformation(item);}}><Info size={14}/></button>
     <span className="sr-only" id={description}>{item.reason}</span>
    </li>;})}</ul>
   </section>
  </div>,document.body)}
  {candidate&&<RecommendationDialog title={`学习${candidate.title}`} onClose={()=>setCandidate(null)} actions={<><button type="button" className="secondary" onClick={()=>setCandidate(null)}>取消</button><button type="button" className="primary" onClick={()=>{setPrefs?.(previous=>startKnowledge(previous,candidate.id,{rows,templates:metadata.templates}));setCandidate(null);}}>进入学习</button></>}>
   <p>{activeTopic&&activeTopic.id!==candidate.id?`当前「${activeTopic.title}」的进度会保留。`:''}进入后，推荐会围绕「{candidate.title}」继续，按先修与每天的学习量安排；需要时可以暂停。</p>
   <Coverage topic={candidate.topic} rows={rows} templates={metadata.templates} ready={metadata.templatesReady}/>
  </RecommendationDialog>}
  {information&&<RecommendationDialog title="推荐依据" onClose={()=>setInformation(null)} actions={information.rawAction?<button type="button" className="secondary" onClick={()=>{const item=information.rawAction;setInformation(null);start(item);}}>继续当前内容</button>:null}>
   <strong>{information.title}</strong><p>{information.reason}</p>
   <Coverage topic={information.topic||KNOWLEDGE_BY_ID[information.journeyTopicId]} rows={rows} templates={metadata.templates} ready={metadata.templatesReady}/>
  </RecommendationDialog>}
  {cancelAnchor&&<PopConfirm anchor={cancelAnchor} label="取消知识点学习确认" title={`取消「${activeTopic?.title||''}」的当前学习？已有进度会保留。`} cancelLabel="继续学习" confirmLabel="取消学习" confirmTone="secondary" onCancel={()=>setCancelAnchor(null)} onConfirm={()=>{setPrefs?.(previous=>cancelKnowledge(previous));setCancelAnchor(null);}}/>}
 </section>;
}
