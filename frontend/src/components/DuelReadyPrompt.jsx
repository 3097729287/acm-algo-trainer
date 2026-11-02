import {useEffect,useId,useLayoutEffect,useRef,useState} from 'react';
import {createPortal} from 'react-dom';
import {Check,Swords,X} from 'lucide-react';
import '../pages/DuelPage.css';

export default function DuelReadyPrompt({duel}){
 const {state,busy,error,act,clock}=duel;
 const [view,setView]=useState(null),[leaving,setLeaving]=useState(false),shown=useRef(null);
 const room=view?.match,open=Boolean(view),box=useRef(null),title=useId(),description=useId(),[,tick]=useState(0);
 useLayoutEffect(()=>{
  const present=value=>{shown.current=value;setView(value);};
  if(state?.status==='ready'){present(state);setLeaving(false);return;}
  if(state?.status==='active'&&shown.current?.owner===state.owner&&shown.current.match.id===state.match.id){
   present(state);setLeaving(true);
   const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches||document.documentElement.dataset.motion==='off';
   const timer=setTimeout(()=>present(null),reduced?0:460);return()=>clearTimeout(timer);
  }
  present(null);setLeaving(false);
 },[state]);
 useEffect(()=>{if(!open)return;const timer=setInterval(()=>tick(value=>value+1),100);return()=>clearInterval(timer);},[open]);
 useEffect(()=>{
  if(!open)return;const previous=document.activeElement,node=box.current;
  node.querySelector('button')?.focus();
  const keys=event=>{
   if(event.key==='Escape'){event.preventDefault();event.stopImmediatePropagation();}
   if(event.key!=='Tab')return;
   const controls=[...node.querySelectorAll('button:not(:disabled)')];
   if(!controls.length){event.preventDefault();node.focus();return;}
   const index=controls.indexOf(document.activeElement),next=event.shiftKey?(index<=0?controls.length-1:index-1):(index+1)%controls.length;
   event.preventDefault();controls[next].focus();
  };
  window.addEventListener('keydown',keys,true);
  return()=>{window.removeEventListener('keydown',keys,true);if(previous?.isConnected)previous.focus();};
 },[open,room?.id]);
 if(!open)return null;
 const mine=room.players.find(player=>player.owner===view.owner),confirmed=mine?.readyAt!=null;
 const now=clock.current?clock.current.server+performance.now()-clock.current.local:view.serverNow;
 const remaining=Math.max(0,room.readyDeadline-now),duration=Math.max(1,room.readyDeadline-room.foundAt);
 return createPortal(<div className={'duel-ready-overlay'+(leaving?' is-entering-match':'')}><section ref={box} className={'duel-ready-dialog'+(confirmed?' is-accepted':'')} role="alertdialog" aria-modal="true" aria-labelledby={title} aria-describedby={description} tabIndex={-1} data-match-id={room.id}>
  <div className="duel-ready-seal" aria-hidden="true"><svg viewBox="0 0 180 180"><circle className="duel-seal-track" cx="90" cy="90" r="81"/><circle className="duel-seal-time" cx="90" cy="90" r="81" pathLength="100" strokeDasharray={`${remaining/duration*100} 100`} transform="rotate(-90 90 90)"/><circle className="duel-seal-inner" cx="90" cy="90" r="66"/></svg><span key={confirmed?'accepted':'found'} className="duel-ready-symbol">{confirmed?<Check size={48}/>:<Swords size={44}/>}</span></div>
  <h2 id={title}>{confirmed?'对局已接受':'已找到对手'}</h2>
  <p id={description} role="status">{leaving?'双方已接受，进入对局':confirmed?'正在等待对手接受对局':'接受后开始本轮对战'}</p>
  <div className="duel-ready-members" aria-label={`${room.players.filter(player=>player.readyAt!=null).length} / 2 人已接受`}>{room.players.map(player=><i key={player.owner} className={player.readyAt!=null?'confirmed':''} aria-hidden="true"/>)}</div>
  <time className="duel-ready-countdown" aria-label="接受对局剩余时间">{leaving?'':Math.ceil(remaining/1000)+'s'}</time>
  <div className="duel-ready-actions"><button type="button" className="primary duel-accept" disabled={busy||confirmed||remaining===0||leaving} onClick={()=>act('ready',{matchId:room.id})}>{confirmed?<Check size={19}/>:<Swords size={19}/>}<span>{confirmed?'已接受':'接受对局'}</span></button><button type="button" className="icon-button duel-decline" title="拒绝本轮对局" aria-label="拒绝本轮对局" disabled={busy||remaining===0||leaving} onClick={()=>act('decline',{matchId:room.id})}><X size={19}/></button></div>
  {error&&<p className="connection-error" role="alert">{error}</p>}
 </section></div>,document.body);
}
