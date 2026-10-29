import {useEffect,useId,useLayoutEffect,useRef,useState} from 'react';
import {createPortal} from 'react-dom';
import {ArrowRight,BookOpen,ChevronDown,Code2,FlaskConical,FolderOpen,History,Target} from 'lucide-react';
import {nextActions} from '@/lib/nextActions.js';
import './NextActions.css';

const icons={review:History,list:FolderOpen,problem:Target,course:FlaskConical,template:Code2,'template-problem':Code2,stretch:Target,contest:BookOpen,mixed:BookOpen};
const labels={review:'间隔复习',list:'基础题单',problem:'基础练习',course:'算法实验室',template:'模板','template-problem':'模板练习',stretch:'进阶挑战',contest:'继续比赛',mixed:'混合限时训练'};

export default function NextActions({rows,training,insights,prefs,api,availablePages,activeContest,onNavigate,onTrain,suspended=false,onOpenChange,reviewPlan={}}) {
 const [metadata,setMetadata]=useState({lists:[],templates:[]}),[revision,setRevision]=useState(0);
 const [open,setOpen]=useState(false),[position,setPosition]=useState(null);
 const root=useRef(null),flyout=useRef(null),toggle=useRef(null),closeTimer=useRef(null),ignoreFocus=useRef(false);
 const openChanged=useRef(onOpenChange);openChanged.current=onOpenChange;
 const popupId=useId(),reasonId=useId();
 useEffect(()=>{const refresh=()=>setRevision(value=>value+1);window.addEventListener('tb:training-lists-changed',refresh);return()=>window.removeEventListener('tb:training-lists-changed',refresh);},[]);
 const scope=availablePages.join(',');
 useEffect(()=>{let alive=true;const requests=[['training-lists','lists'],['templates','templates']].filter(([page])=>availablePages.includes(page));Promise.allSettled(requests.map(async([page,key])=>[key,(await api(page))[key]||[]])).then(results=>{if(alive)setMetadata(Object.fromEntries([['lists',[]],['templates',[]],...results.filter(item=>item.status==='fulfilled').map(item=>item.value)]));});return()=>{alive=false;};},[api,scope,revision]);
 const items=nextActions({rows,training,insights:insights||{},prefs,...metadata,availablePages,activeContest,reviewPlan}),primary=items[0],rest=items.slice(1);
 const expandable=rest.length>0,expanded=Boolean(open&&!suspended&&primary&&expandable);
 useEffect(()=>{openChanged.current?.(expanded);},[expanded]);
 useEffect(()=>()=>openChanged.current?.(false),[]);
 useEffect(()=>{if(!primary||suspended||!expandable){clearTimeout(closeTimer.current);setOpen(false);}},[Boolean(primary),suspended,expandable]);
 const cancelClose=()=>{clearTimeout(closeTimer.current);closeTimer.current=null;};
 const contains=node=>Boolean(node&&(root.current?.contains(node)||flyout.current?.contains(node)));
 const show=()=>{cancelClose();if(!suspended&&expandable)setOpen(true);};
 const close=(restoreFocus=false)=>{
  cancelClose();setOpen(false);
  if(restoreFocus){ignoreFocus.current=true;toggle.current?.focus({preventScroll:true});ignoreFocus.current=false;}
 };
 const leave=()=>{
  cancelClose();closeTimer.current=setTimeout(()=>{
   if(!contains(document.activeElement)&&!root.current?.matches(':hover')&&!flyout.current?.matches(':hover'))setOpen(false);
  },180);
 };
 useEffect(()=>()=>clearTimeout(closeTimer.current),[]);
 useEffect(()=>{
  if(!open||suspended)return;
  const outside=event=>{if(!contains(event.target))close();};
  const escape=event=>{if(event.key==='Escape'){event.preventDefault();event.stopPropagation();close(contains(document.activeElement));}};
  document.addEventListener('pointerdown',outside,true);document.addEventListener('keydown',escape,true);
  return()=>{document.removeEventListener('pointerdown',outside,true);document.removeEventListener('keydown',escape,true);};
 },[open,suspended]);
 useLayoutEffect(()=>{
  if(!open||!primary)return;
  const update=()=>{
   if(!root.current)return;
   const rect=root.current.getBoundingClientRect(),edge=10,width=Math.max(0,Math.min(rect.width,innerWidth));
   const top=Math.min(rect.bottom,Math.max(edge,innerHeight-100));
   setPosition({left:Math.max(0,Math.min(rect.left,innerWidth-width)),top,width,maxHeight:Math.max(80,innerHeight-top-edge)});
  };
  update();const observer=typeof ResizeObserver==='undefined'?null:new ResizeObserver(update);if(root.current)observer?.observe(root.current);
  window.addEventListener('resize',update);window.addEventListener('scroll',update,true);
  return()=>{observer?.disconnect();window.removeEventListener('resize',update);window.removeEventListener('scroll',update,true);};
 },[open,primary?.kind,primary?.id]);
 const start=item=>{close();['problem','stretch','review','template-problem'].includes(item.kind)?onTrain(item.id):onNavigate(item);};
 const focusRow=last=>requestAnimationFrame(()=>{
  const buttons=flyout.current?.querySelectorAll('.next-actions-item');(last?buttons?.[buttons.length-1]:buttons?.[0])?.focus();
 });
 const openWithKeys=event=>{
  if(!expandable)return;
  if(event.key==='ArrowDown'||event.key==='ArrowUp'){event.preventDefault();show();focusRow(event.key==='ArrowUp');}
 };
 const blur=event=>{if(!contains(event.relatedTarget))leave();};
 if(!primary)return null;
 const Icon=icons[primary.kind];
 return <section ref={root} className="next-actions" aria-label="下一步推荐做的事" data-open={expanded} data-expandable={expandable} data-suspended={suspended} onMouseEnter={show} onMouseLeave={leave} onFocus={()=>{if(!ignoreFocus.current)show();}} onBlur={blur}>
  <button type="button" className="next-actions-primary" data-recommendation={primary.kind} aria-label={`开始${labels[primary.kind]} ${primary.title}`} aria-describedby={reasonId} title={`${labels[primary.kind]}：${primary.title}\n${primary.reason}`} disabled={suspended} onClick={()=>start(primary)} onKeyDown={openWithKeys}>
   <Icon size={19} aria-hidden="true"/><span className="next-actions-primary-copy"><strong>{primary.title}</strong></span>
  </button>
  <span className="sr-only" id={reasonId}>{primary.reason}</span>
  {expandable&&<button ref={toggle} type="button" className="next-actions-toggle" aria-label={expanded?'收起下一步推荐任务':'展开下一步推荐任务'} aria-expanded={expanded} aria-controls={popupId} disabled={suspended} onPointerDown={event=>{event.currentTarget.dataset.wasOpen=String(open);}} onClick={event=>{const wasOpen=event.currentTarget.dataset.wasOpen;delete event.currentTarget.dataset.wasOpen;if(wasOpen==='true'||wasOpen===undefined&&open)close();else show();}} onKeyDown={openWithKeys}><ChevronDown size={17} aria-hidden="true"/></button>}
  {expanded&&createPortal(<div ref={flyout} className="next-actions-flyout" style={{...position,visibility:position?'visible':'hidden'}} onMouseEnter={cancelClose} onMouseLeave={leave} onFocus={cancelClose} onBlur={blur}>
   <section className="next-actions-popover" id={popupId} aria-label="推荐任务与依据" onKeyDown={event=>{
    if(!['ArrowDown','ArrowUp','Home','End'].includes(event.key))return;
    const buttons=[...event.currentTarget.querySelectorAll('.next-actions-item')],index=buttons.indexOf(document.activeElement);if(index<0)return;
    event.preventDefault();buttons[event.key==='Home'?0:event.key==='End'?buttons.length-1:(index+(event.key==='ArrowDown'?1:-1)+buttons.length)%buttons.length]?.focus();
   }}>
    <ul>{rest.map((item,index)=>{const ItemIcon=icons[item.kind],description=`${popupId}-reason-${index}`;return <li key={`${item.kind}:${item.id}`} style={{'--task-index':index}}><button type="button" className="next-actions-item" data-recommendation={item.kind} aria-label={`开始${labels[item.kind]} ${item.title}`} aria-describedby={description} title={`${labels[item.kind]}：${item.title}\n${item.reason}`} onClick={()=>start(item)}><ItemIcon size={18} aria-hidden="true"/><span className="next-actions-item-copy"><strong>{item.title}</strong></span><ArrowRight size={16} aria-hidden="true"/></button><span className="sr-only" id={description}>{item.reason}</span></li>;})}</ul>
   </section>
  </div>,document.body)}
 </section>;
}
