import {useCallback,useEffect,useRef,useState} from 'react';
import {createDuelSound} from './duelSound.js';
// Mounted in App, so returning to the native submission workbench keeps the
// match heartbeat and provider verification alive. No automatic join/retry.
export default function useDuel(api,owner){
 const [state,setState]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const generation=useRef(0),live=useRef(owner),pending=useRef(null),writing=useRef(null),clock=useRef(null),queue=useRef(null),audio=useRef(null),heard=useRef(new Set()),currentRoom=useRef(null);
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
  generation.current++;pending.current=null;writing.current=null;clock.current=null;queue.current=null;currentRoom.current=null;heard.current.clear();
  audio.current?.close();const sound=createDuelSound();audio.current=sound;
  setBusy(false);setState(null);setError('');if(!owner||window.__tbAdmin)return()=>sound.close();
  let alive=true;api('duel').then(value=>{if(alive)accept(value,owner);}).catch(()=>{});
  return()=>{alive=false;sound.close();};
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
  const poll=async()=>{if(pending.current||!navigator.onLine)return;const stamp=generation.current,operation={};pending.current=operation;try{const value=await api('duel/poll',{});if(alive&&stamp===generation.current)accept(value,owner);}catch(issue){if(alive&&stamp===generation.current)setError(issue.message);}finally{if(pending.current===operation)pending.current=null;}};
  const timer=setInterval(poll,state.status==='ready'?1000:state.status==='queued'?2500:5000);window.addEventListener('online',poll);
  return()=>{alive=false;clearInterval(timer);window.removeEventListener('online',poll);};
 },[api,owner,state?.status,accept]);
 const act=useCallback(async(kind,extra={})=>{
  if(writing.current)return;const requestedOwner=owner,operation={};generation.current++;writing.current=operation;setBusy(true);
  if(kind==='join'||kind==='ready')void audio.current?.unlock();
  try{const value=await api('duel/'+kind,{requestId:crypto.randomUUID(),...(kind==='join'&&state?.capabilities?.readyCheck?{readyCheck:true}:{}),...extra});if(writing.current===operation)accept(value,requestedOwner);return value;}
  catch(issue){if(live.current===requestedOwner&&writing.current===operation)setError(issue.message);}
  finally{if(writing.current===operation){writing.current=null;if(live.current===requestedOwner)setBusy(false);}}
 },[api,owner,accept,state?.capabilities?.readyCheck]);
 const reload=useCallback(async()=>{const stamp=generation.current;try{const value=await api('duel');if(stamp===generation.current)accept(value,owner);}catch(issue){if(live.current===owner&&stamp===generation.current)setError(issue.message);}},[api,owner,accept]);
 return {state:state?.owner===owner?state:null,error,busy,act,reload,clock};
}
