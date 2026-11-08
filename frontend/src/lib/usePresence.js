import {useCallback,useEffect,useRef,useState} from 'react';
import {observeUserInput} from './userInput.js';
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
 const [saved,setSaved]=useState(null),live=useRef(owner),current=useRef(activity),pending=useRef(null),sequence=useRef(0),clock=useRef({owner,lastInput:performance.now()}),sent=useRef(null);
 if(clock.current.owner!==owner)clock.current={owner,lastInput:performance.now()};
 live.current=owner;current.current=activity;
 const desired=()=>performance.now()-clock.current.lastInput>=PRESENCE_IDLE_MS?'idle':current.current;
 const beat=useCallback(async()=>{
  if(!owner||window.__tbAdmin||!navigator.onLine||pending.current)return;
  const request={},seq=sequence.current,reported=desired();pending.current=request;sent.current=reported;
  try{const value=await api('presence',{activity:reported});if(live.current===owner&&seq===sequence.current&&value.owner===owner)setSaved({owner,value});}
  catch{if(live.current===owner&&seq===sequence.current)setSaved(null);}
  finally{if(pending.current===request){pending.current=null;if(live.current===owner&&seq===sequence.current&&desired()!==reported)void beat();}}
 },[api,owner]);
 useEffect(()=>{sequence.current++;pending.current=null;setSaved(null);void beat();const timer=setInterval(beat,25000);window.addEventListener('online',beat);window.addEventListener('focus',beat);return()=>{sequence.current++;clearInterval(timer);window.removeEventListener('online',beat);window.removeEventListener('focus',beat);};},[beat]);
 useEffect(()=>{
  if(!owner||window.__tbAdmin)return;
  let timer;
  const check=()=>{timer=null;const remaining=PRESENCE_IDLE_MS-(performance.now()-clock.current.lastInput);if(remaining>0)timer=setTimeout(check,remaining);else void beat();};
  const stop=observeUserInput(()=>{const idle=desired()==='idle'||sent.current==='idle';clock.current.lastInput=performance.now();if(timer===null)timer=setTimeout(check,PRESENCE_IDLE_MS);if(idle)void beat();});
  timer=setTimeout(check,Math.max(0,PRESENCE_IDLE_MS-(performance.now()-clock.current.lastInput)));
  return()=>{stop();clearTimeout(timer);};
 },[owner,beat]);
 useEffect(()=>{void beat();},[activity,beat]);
 return saved&&saved.owner===owner?saved.value:null;
}
