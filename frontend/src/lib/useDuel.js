import {useCallback,useEffect,useRef,useState} from 'react';
import {createDuelSound} from './duelSound.js';
import {loadDuelBoard} from './duelBoardCache.js';
// Mounted in App, so returning to the native submission workbench keeps the
// match heartbeat and provider verification alive. No automatic join/retry.
export default function useDuel(api,owner){
 const [state,setState]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const generation=useRef(0),live=useRef(owner),pending=useRef(null),writing=useRef(null),clock=useRef(null),queue=useRef(null),audio=useRef(null),heard=useRef(new Set()),currentRoom=useRef(null),cancellation=useRef(null);
 live.current=owner;
 const accept=useCallback((value,requestedOwner)=>{
  if(live.current!==requestedOwner||value.owner!==requestedOwner||clock.current&&value.serverNow<clock.current.server)return;
  clock.current={server:value.serverNow,local:performance.now()};
  if(value.status==='queued'){
   if(queue.current?.ticket!==value.ticket)queue.current={ticket:value.ticket,at:Number.isFinite(value.queuedAt)?value.queuedAt:value.serverNow};
   value={...value,queuedAt:queue.current.at};
  }else queue.current=null;
  currentRoom.current=value.match?.id||null;setState(value);setError('');
 },[]);
 useEffect(()=>{
  generation.current++;pending.current=null;writing.current=null;clock.current=null;queue.current=null;currentRoom.current=null;cancellation.current=null;heard.current.clear();
  audio.current?.close();const sound=createDuelSound();audio.current=sound;
  setBusy(false);setState(null);setError('');if(!owner||window.__tbAdmin)return()=>sound.close();
  let alive=true;const stamp=generation.current;api('duel').then(value=>{if(alive&&stamp===generation.current){accept(value,owner);if(value.available!==false)void loadDuelBoard(api,owner,'ranked').catch(()=>{});}}).catch(issue=>{if(alive&&stamp===generation.current)setError(issue.message);});
  return()=>{alive=false;sound.close();};
 },[api,owner,accept]);
 // Keep an explicitly requested cancellation through a temporary disconnect.
 // Reuse its request/ticket and stop extending the queue heartbeat. A lost
 // reply must never turn cancellation into another join or cancel a new queue.
 const cancel=useCallback(async(extra={})=>{
  if(writing.current||!owner)return;
  let intent=cancellation.current;
  if(!intent||intent.payload.ticket!==extra.ticket)intent={owner,payload:{requestId:crypto.randomUUID(),ticket:extra.ticket},nextAt:0};
  cancellation.current=intent;const operation={};writing.current=operation;generation.current++;setBusy(true);
  try{
   let value=await api('duel/cancel',intent.payload);
   if(live.current!==owner||writing.current!==operation||cancellation.current!==intent)return;
   // If a match was found just before cancel reached the service, declining
   // that exact ready room completes the same user's cancellation intent.
   if(value.status==='ready'&&value.match?.id){
    intent.decline??={requestId:crypto.randomUUID(),matchId:value.match.id};
    value=await api('duel/decline',intent.decline);
   }
   if(live.current===owner&&writing.current===operation&&cancellation.current===intent){cancellation.current=null;accept(value,owner);}
   return value;
  }catch(issue){
   if(live.current===owner&&writing.current===operation&&cancellation.current===intent){
    setError(issue.message);intent.nextAt=performance.now()+2500;
    if(issue.status>=400&&issue.status<500&&issue.status!==429)cancellation.current=null;
   }
  }finally{if(writing.current===operation){writing.current=null;if(live.current===owner)setBusy(false);}}
 },[api,owner,accept]);
 useEffect(()=>{
  if(state?.status!=='ready')return;
  const id=state.match.id,requestedOwner=owner;
  const notify=()=>{
   if(heard.current.has(id))return;
   // Reserve before awaiting resume so a click and response cannot overlap.
   heard.current.add(id);
   void audio.current?.play(()=>live.current===requestedOwner&&currentRoom.current===id).then(played=>{if(!played&&live.current===requestedOwner)heard.current.delete(id);});
  };
  notify();window.addEventListener('pointerdown',notify);window.addEventListener('keydown',notify);
  return()=>{window.removeEventListener('pointerdown',notify);window.removeEventListener('keydown',notify);};
 },[owner,state?.status,state?.match?.id]);
 useEffect(()=>{
  if(!['queued','ready','active'].includes(state?.status))return;
  let alive=true;
  const poll=async()=>{if(!navigator.onLine)return;if(cancellation.current){if(performance.now()>=cancellation.current.nextAt)void cancel({ticket:cancellation.current.payload.ticket});return;}if(pending.current||writing.current)return;const stamp=generation.current,operation={};pending.current=operation;try{const value=await api('duel/poll',{});if(alive&&stamp===generation.current)accept(value,owner);}catch(issue){if(alive&&stamp===generation.current)setError(issue.message);}finally{if(pending.current===operation)pending.current=null;}};
  const timer=setInterval(poll,state.status==='ready'?1000:state.status==='queued'?2500:5000);window.addEventListener('online',poll);
  return()=>{alive=false;clearInterval(timer);window.removeEventListener('online',poll);};
 },[api,owner,state?.status,accept,cancel]);
 const act=useCallback(async(kind,extra={})=>{
  if(kind==='cancel')return cancel(extra);
  if(writing.current)return;const requestedOwner=owner,operation={};generation.current++;writing.current=operation;setBusy(true);
  if(kind==='join'||kind==='ready')void audio.current?.unlock();
  try{const value=await api('duel/'+kind,{requestId:crypto.randomUUID(),...(kind==='join'&&state?.capabilities?.readyCheck?{readyCheck:true}:{}),...extra});if(writing.current===operation)accept(value,requestedOwner);return value;}
  catch(issue){if(live.current===requestedOwner&&writing.current===operation)setError(issue.message);}
  finally{if(writing.current===operation){writing.current=null;if(live.current===requestedOwner)setBusy(false);}}
 },[api,owner,accept,state?.capabilities?.readyCheck,cancel]);
 const reload=useCallback(async()=>{if(!owner||window.__tbAdmin||writing.current)return;const stamp=++generation.current;try{const value=await api('duel');if(stamp===generation.current)accept(value,owner);}catch(issue){if(live.current===owner&&stamp===generation.current)setError(issue.message);}},[api,owner,accept]);
 return {state:state?.owner===owner?state:null,error,busy,act,reload,clock};
}
