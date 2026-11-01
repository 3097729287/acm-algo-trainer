import {useCallback,useEffect,useRef,useState} from 'react';
// Mounted in App, so returning to the native submission workbench keeps the
// match heartbeat and provider verification alive. No automatic join/retry.
export default function useDuel(api,owner){
 const [state,setState]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const generation=useRef(0),live=useRef(owner),pending=useRef(null),writing=useRef(null),clock=useRef(null);
 live.current=owner;
 const accept=useCallback((value,requestedOwner)=>{if(live.current!==requestedOwner||value.owner!==requestedOwner||clock.current&&value.serverNow<clock.current.server)return;clock.current={server:value.serverNow,local:performance.now()};setState(value);setError('');},[]);
 useEffect(()=>{generation.current++;pending.current=null;writing.current=null;clock.current=null;setBusy(false);setState(null);setError('');if(!owner||window.__tbAdmin)return;let alive=true;api('duel').then(value=>{if(alive)accept(value,owner);}).catch(()=>{});return()=>{alive=false;};},[api,owner,accept]);
 useEffect(()=>{
  if(!['queued','active'].includes(state?.status))return;
  let alive=true;
  const poll=async()=>{if(pending.current||!navigator.onLine)return;const stamp=generation.current,operation={};pending.current=operation;try{const value=await api('duel/poll',{});if(alive&&stamp===generation.current)accept(value,owner);}catch(issue){if(alive&&stamp===generation.current)setError(issue.message);}finally{if(pending.current===operation)pending.current=null;}};
  const timer=setInterval(poll,5000);window.addEventListener('online',poll);
  return()=>{alive=false;clearInterval(timer);window.removeEventListener('online',poll);};
 },[api,owner,state?.status,accept]);
 const act=useCallback(async(kind,extra={})=>{
  if(writing.current)return;const requestedOwner=owner,operation={};generation.current++;writing.current=operation;setBusy(true);
  try{const value=await api('duel/'+kind,{requestId:crypto.randomUUID(),...extra});if(writing.current===operation)accept(value,requestedOwner);return value;}
  catch(issue){if(live.current===requestedOwner&&writing.current===operation)setError(issue.message);}
  finally{if(writing.current===operation){writing.current=null;if(live.current===requestedOwner)setBusy(false);}}
 },[api,owner,accept]);
 const reload=useCallback(async()=>{const stamp=generation.current;try{const value=await api('duel');if(stamp===generation.current)accept(value,owner);}catch(issue){if(live.current===owner&&stamp===generation.current)setError(issue.message);}},[api,owner,accept]);
 return {state,error,busy,act,reload,clock};
}
