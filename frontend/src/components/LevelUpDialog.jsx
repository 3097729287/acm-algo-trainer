import {useLayoutEffect,useRef} from 'react';
import {createPortal} from 'react-dom';
import {ArrowRight,Check,ChevronRight,LockOpen,X} from 'lucide-react';
import {newlyUnlocked,nextUnlock,canOpenPage} from '@/lib/featureUnlocks.js';
import './LevelUpDialog.css';

export default function LevelUpDialog({notice,pages,preferences,onPresented,onClose,onOpen}){
 const card=useRef(null),returnFocus=useRef(document.activeElement),close=useRef(onClose);close.current=onClose;
 useLayoutEffect(()=>{
  const node=card.current;node.querySelector('button')?.focus({preventScroll:true});
  const key=event=>{if(event.key==='Escape'){event.preventDefault();event.stopImmediatePropagation();close.current();}else if(event.key==='Tab'){const elements=[...node.querySelectorAll('button:not(:disabled),a[href],[tabindex="0"]')].filter(element=>element.getBoundingClientRect().height>0),first=elements[0],last=elements.at(-1);if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus();}}};
  document.addEventListener('keydown',key,true);return()=>{document.removeEventListener('keydown',key,true);if(returnFocus.current?.isConnected)returnFocus.current.focus({preventScroll:true});};
 },[]);
 useLayoutEffect(()=>{const visible=()=>{if(!document.hidden)onPresented(notice.to);};visible();document.addEventListener('visibilitychange',visible);return()=>document.removeEventListener('visibilitychange',visible);},[notice.to,onPresented]);
 const unlocked=newlyUnlocked(notice.from,notice.to).filter(item=>canOpenPage(item.id,notice.to,preferences)),next=nextUnlock(notice.to),groups=[...new Set(unlocked.map(item=>item.level))];
 const growth=notice.growth||{},capped=notice.to>=100,progress=capped?100:Math.max(0,Math.min(100,Number(growth.nextLevelXp)>0?Number(growth.currentLevelXp)/Number(growth.nextLevelXp)*100:0));
 const open=id=>{onClose();onOpen(id);};
 return createPortal(<div className="level-up-overlay" data-level-up><section ref={card} role="dialog" aria-modal="true" aria-labelledby="level-up-title" className="level-up-dialog">
  <header><h2 id="level-up-title">等级提升</h2><button type="button" className="icon-button" aria-label="关闭等级提升" title="关闭等级提升 · Esc" onClick={onClose}><X size={19}/></button></header>
  <div className="level-up-body">
   <div className="level-up-emblem" aria-hidden="true"><svg viewBox="0 0 200 200"><circle className="level-up-track" cx="100" cy="100" r="82"/><circle className="level-up-ring" cx="100" cy="100" r="82" pathLength="100" style={{'--level-progress':progress}}/><circle className="level-up-halo" cx="100" cy="100" r="94"/></svg><div className="level-up-center level-up-old"><small>Lv.</small><strong>{notice.from}</strong></div><div className="level-up-center level-up-current"><small>Lv.</small><strong>{notice.to}</strong></div></div>
   <div className="level-up-number" aria-label={`等级从 ${notice.from} 提升到 ${notice.to}`}><span>Lv.{notice.from}</span><ArrowRight size={17}/><strong>Lv.{notice.to}</strong></div>
   <p className="level-up-xp">{capped?'Lv.100 · 已达等级上限':`${Number(growth.currentLevelXp||0).toLocaleString()} / ${Number(growth.nextLevelXp||0).toLocaleString()} XP`}</p>
   {groups.length>0&&<div className="level-up-features"><h3>新解锁</h3>{groups.map(level=><div className="level-up-group" key={level}><small>Lv.{level}</small><div>{unlocked.filter(item=>item.level===level).map(item=>{const Icon=pages.find(page=>page.id===item.id)?.icon;return <button type="button" key={item.id} style={{'--unlock-delay':`${650+unlocked.indexOf(item)*70}ms`}} onClick={()=>open(item.id)} aria-label={`打开新解锁板块 ${item.label}`}><span className="level-up-card-icon"><LockOpen className="level-up-lock" size={21}/>{Icon&&<Icon className="level-up-feature-icon" size={22}/>}</span><strong>{item.label}</strong><ChevronRight size={16}/></button>;})}</div></div>)}</div>}
   {next.length>0&&<p className="level-up-next">Lv.{next[0].level}：{next.map(item=>item.label).join('、')}</p>}
  </div>
  <footer><button type="button" className="icon-button primary" aria-label="继续学习" title="继续学习" onClick={onClose}><Check size={21}/></button></footer>
 </section></div>,document.body);
}
