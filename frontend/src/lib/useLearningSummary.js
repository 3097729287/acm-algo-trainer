import {useCallback,useEffect,useRef,useState} from 'react';
import {studyClock} from './learningSummaryModel.js';

export default function useLearningSummary(api,owner,enabled,learning) {
 const [snapshot,setSnapshot]=useState(null),[open,setOpen]=useState(false),[error,setError]=useState('');
 const current=useRef(null),generation=useRef(0),queue=useRef(Promise.resolve()),learningMode=useRef(learning),timerClock=useRef(null);
 learningMode.current=learning;
 useEffect(()=>{setOpen(false);},[owner]);
 useEffect(()=>{timerClock.current?.reset();},[learning]);
 const accept=useCallback((value,epoch)=>{if(epoch===generation.current){current.current=value;setSnapshot(value);setError('');}return value;},[]);
 const refresh=useCallback(()=>{
  const epoch=generation.current;
  const run=queue.current.catch(()=>{}).then(()=>api('learning-summary/refresh',{})).then(value=>accept(value,epoch));
  queue.current=run;return run;
 },[api,accept]);
 const update=useCallback((action,fields={})=>{
  const epoch=generation.current;
  const run=queue.current.catch(()=>{}).then(async()=>{
   if(epoch!==generation.current)return null;
   let state=current.current||await api('learning-summary');
   try{return accept(await api('learning-summary/update',{...fields,action,revision:state.revision}),epoch);}
   catch(issue){if(issue.status===409)accept(await api('learning-summary'),epoch);throw issue;}
  });
  queue.current=run;return run;
 },[api,accept]);
 useEffect(()=>{
  const epoch=++generation.current;current.current=null;setSnapshot(null);setError('');queue.current=Promise.resolve();
  if(!enabled)return;
  let live=true;
  api('learning-summary').then(value=>{if(live){accept(value,epoch);return refresh();}}).catch(issue=>{if(live)setError(issue.message);});
  const timer=setInterval(()=>{if(document.visibilityState==='visible')refresh().catch(()=>{});},30000);
  const changed=()=>refresh().catch(()=>{});
  window.addEventListener('tb:learning-progress',changed);
  return()=>{live=false;generation.current++;clearInterval(timer);window.removeEventListener('tb:learning-progress',changed);};
 },[api,owner,enabled,accept,refresh]);
 useEffect(()=>{
  if(!enabled)return;
  const clock=studyClock(),epoch=generation.current;let intervals=[],pending=false,lastEvent=0,flight=null;
  timerClock.current=clock;
  const visible=()=>document.visibilityState==='visible'&&document.hasFocus();
  const interaction=event=>{
   if(!event.isTrusted)return;
   const monotonic=performance.now();if(monotonic-lastEvent<750)return;lastEvent=monotonic;
   const span=clock.interact(Date.now()/1000,Boolean(learningMode.current&&visible()));
   if(span)intervals.push(span);
  };
  const reset=()=>clock.reset();
  const flush=async()=>{
   if(pending){await flight;return flush();}
   if(!intervals.length||epoch!==generation.current)return;
   const batch=intervals.slice(0,128);pending=true;
   try{flight=api('learning-summary/time',{intervals:batch});await flight;if(epoch===generation.current)intervals.splice(0,batch.length);}
   catch{/* Retain intervals for the next local connection; never add idle time. */}
   finally{pending=false;}
  };
  const events=['keydown','pointerdown','pointermove','wheel','touchstart','scroll'];
  for(const name of events)document.addEventListener(name,interaction,{passive:true,capture:true});
  window.addEventListener('blur',reset);document.addEventListener('visibilitychange',reset);
  const beforeExit=event=>event.detail?.waitUntil?.(flush());window.addEventListener('tb-before-update',beforeExit);
  const timer=setInterval(flush,10000);
  return()=>{clearInterval(timer);for(const name of events)document.removeEventListener(name,interaction,true);window.removeEventListener('blur',reset);document.removeEventListener('visibilitychange',reset);window.removeEventListener('tb-before-update',beforeExit);};
 },[api,owner,enabled]);
 return {snapshot,open,setOpen,error,refresh,update};
}
