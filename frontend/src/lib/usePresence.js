import {useCallback,useEffect,useRef,useState} from 'react';
import {observeUserInput,observeNativeInput} from './userInput.js';
export const PRESENCE_IDLE_MS=5*60*1000;
export const ACTIVITY_LABELS={online:'在线',matching:'匹配中',problem:'做题中',replay:'重现赛中',contest:'模拟赛中',lecture:'从零讲中',lab:'实验室中',wiki:'阅读维基中',template:'模板学习中',ranked:'排位对战中',thought:'思维对决中',library:'浏览题库中',lists:'浏览题单中',growth:'查看成长中',records:'查看记录中',settings:'设置中',rankings:'查看排行榜中'};
export function currentActivity({page,practice,studyKind,contest,duel,thought}){
 if(['countdown','active','judging'].includes(thought?.status))return 'thought';
 if(['ready','active'].includes(duel?.status))return 'ranked';
 if(duel?.status==='queued'||thought?.status==='queued')return 'matching';
 if(['active','running'].includes(contest?.status))return contest.config?.strategy==='replay'||contest.config?.mode==='replay'||contest.mode==='replay'||contest.strategy==='replay'?'replay':'contest';
 if(practice)return 'problem';if(studyKind)return ({solution:'problem',problem:'problem',lecture:'lecture',lab:'lab',template:'template',wiki:'wiki'})[studyKind]||'online';
 return ({mine:'online',library:'library',lists:'lists',lectures:'lecture',paths:'lab',templates:'template',wiki:'wiki',duel:'online',progress:'growth',records:'records',activity:'records',rankings:'rankings',settings:'settings'})[page]||'online';
}
export default function usePresence(api,owner,activity){
 const [saved,setSaved]=useState(null),live=useRef(owner),current=useRef(activity),pending=useRef(null),sequence=useRef(0),clock=useRef({owner,lastInput:performance.now()}),sent=useRef(null),closing=useRef(false),native=useRef(null),rearm=useRef(null),lease=useRef({owner,ticket:null,state:'new'});
 if(clock.current.owner!==owner){clock.current={owner,lastInput:performance.now()};closing.current=false;lease.current={owner,ticket:null,state:'new'};}
 live.current=owner;current.current=activity;
 const desired=()=>performance.now()-clock.current.lastInput>=PRESENCE_IDLE_MS?'idle':current.current;
 const beat=useCallback(async()=>{
  if(!owner||window.__tbAdmin||!navigator.onLine||pending.current||closing.current)return;
  const request={},seq=sequence.current;let reported;pending.current=request;
  try{
   await native.current?.sample();
   if(live.current!==owner||seq!==sequence.current||closing.current)return;
   let ticket=lease.current.ticket,value;
   if(!ticket||lease.current.state==='superseded'){
    const prepared=await api('presence',{activity:desired(),presencePhase:ticket?'recover':'prepare',presenceOwner:owner,...(ticket||{})});
    if(live.current!==owner||seq!==sequence.current||closing.current)return;
    if(prepared.presenceProtocol!==2||prepared.owner!==owner)throw new Error('在线实例连接尚未就绪');
    if(prepared.presenceState!=='prepared'){
     lease.current.state='superseded';setSaved({owner,value:prepared});return;
    }
    if(!/^[A-Za-z0-9_-]{11}\.[A-Za-z0-9_-]{43}$/.test(prepared.presenceLease||'')||!(prepared.presenceExpected===''||/^[A-Za-z0-9_-]{11}$/.test(prepared.presenceExpected||'')))throw new Error('在线实例凭证无效');
    ticket={presenceLease:prepared.presenceLease,presenceExpected:prepared.presenceExpected};lease.current.ticket=ticket;lease.current.state='prepared';
   }
   reported=desired();sent.current=reported;
   value=await api('presence',{activity:reported,presencePhase:lease.current.state==='prepared'?'activate':'beat',presenceOwner:owner,...ticket});
   if(live.current===owner&&seq===sequence.current&&!closing.current&&value.owner===owner){lease.current.state=value.presenceState==='active'?'active':'superseded';setSaved({owner,value});}
  }
  catch{if(live.current===owner&&seq===sequence.current)setSaved(null);}
  finally{if(pending.current===request){pending.current=null;if(!closing.current&&reported!==undefined&&live.current===owner&&seq===sequence.current&&desired()!==reported)void beat();}}
 },[api,owner]);
 useEffect(()=>{sequence.current++;pending.current=null;setSaved(null);void beat();const timer=setInterval(beat,25000);window.addEventListener('online',beat);window.addEventListener('focus',beat);return()=>{sequence.current++;clearInterval(timer);window.removeEventListener('online',beat);window.removeEventListener('focus',beat);};},[beat]);
 useEffect(()=>{
  if(!owner||window.__tbAdmin)return;
  let timer;
  const check=()=>{timer=null;const remaining=PRESENCE_IDLE_MS-(performance.now()-clock.current.lastInput);if(remaining>0)timer=setTimeout(check,remaining);else void beat();};
  const schedule=()=>{if(timer===null)timer=setTimeout(check,Math.max(0,PRESENCE_IDLE_MS-(performance.now()-clock.current.lastInput)));};
  rearm.current=schedule;
  const stop=observeUserInput(()=>{const idle=desired()==='idle'||sent.current==='idle';clock.current.lastInput=performance.now();schedule();if(idle)void beat();});
  timer=setTimeout(check,Math.max(0,PRESENCE_IDLE_MS-(performance.now()-clock.current.lastInput)));
  return()=>{stop();clearTimeout(timer);if(rearm.current===schedule)rearm.current=null;};
 },[owner,beat]);
 useEffect(()=>{
  if(!owner||window.__tbAdmin)return;
  let disposed=false;
  const stop=observeNativeInput(api,when=>{
   if(disposed||live.current!==owner||closing.current||when<=clock.current.lastInput)return;
   const idle=desired()==='idle'||sent.current==='idle';clock.current.lastInput=when;rearm.current?.();if(idle)void beat();
  });
  native.current=stop;
  return()=>{disposed=true;stop();if(native.current===stop)native.current=null;};
 },[api,owner,beat]);
 useEffect(()=>{
  if(!owner||window.__tbAdmin)return;
  const close=()=>{
   if(live.current!==owner||closing.current)return;
   closing.current=true;const seq=++sequence.current;
   // This request is best effort. It never blocks the local draft-save and
   // close barrier, never logs the user out, and is bound to the current token.
   const ticket=lease.current.ticket;
   if(ticket)void api('presence',{activity:'offline',presencePhase:'close',presenceOwner:owner,...ticket}).then(value=>{if(live.current===owner&&seq===sequence.current&&closing.current&&value.owner===owner)setSaved({owner,value});}).catch(()=>{});
  };
  const reopen=()=>{if(live.current===owner&&closing.current){closing.current=false;sequence.current++;pending.current=null;lease.current={owner,ticket:null,state:'new'};void beat();}};
  window.addEventListener('tb-desktop-closing',close);window.addEventListener('pagehide',close);window.addEventListener('pageshow',reopen);
  return()=>{window.removeEventListener('tb-desktop-closing',close);window.removeEventListener('pagehide',close);window.removeEventListener('pageshow',reopen);};
 },[api,owner,beat]);
 useEffect(()=>{void beat();},[activity,beat]);
 return saved&&saved.owner===owner?saved.value:null;
}
