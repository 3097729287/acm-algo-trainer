import {useCallback,useEffect,useRef,useState} from 'react';

const paths={join:'match/join',cancel:'match/cancel',draft:'game/draft',submit:'game/submit',dismiss:'game/dismiss'};
const active=status=>['queued','countdown','active','judging'].includes(status);
const cacheKey=(owner,id)=>`tb:pk:draft:${owner}:${id}`;
function readDraft(owner,id){try{const v=JSON.parse(localStorage.getItem(cacheKey(owner,id)));return v&&typeof v.text==='string'&&[...v.text].length<=2000&&Number.isInteger(v.revision)?v:null;}catch{return null;}}
function storeDraft(owner,editor){if(!owner||!editor?.id)return;try{localStorage.setItem(cacheKey(owner,editor.id),JSON.stringify({text:editor.text,revision:editor.revision}));}catch{/* Server-confirmed drafts remain available. */}}

// Kept in App: navigating away never stops the match or discards an answer.
export default function useThoughtDuel(api,owner){
 const [state,setState]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[saving,setSaving]=useState(false),[editor,setEditorState]=useState(null),[uncertain,setUncertain]=useState(false);
 const live=useRef(owner),generation=useRef(0),writing=useRef(null),reading=useRef(null),clock=useRef(null),snapshot=useRef(null),draft=useRef(null),intent=useRef(null),recover=useRef(false);
 live.current=owner;
 const setEditor=useCallback(value=>{draft.current=value;setEditorState(value);},[]);
 const accept=useCallback((value,requestedOwner,saved=null)=>{
  if(live.current!==requestedOwner||value?.owner!==requestedOwner||!Number.isFinite(value.serverNow)||clock.current&&value.serverNow<clock.current.server)return;
  clock.current={server:value.serverNow,local:performance.now()};snapshot.current=value;recover.current=false;setState(value);setError('');
  const room=value.match,me=room?.players?.find(p=>p.owner===requestedOwner);
  if(room&&me&&typeof me.text==='string'){
   const current=draft.current?.id===room.id?draft.current:null,cache=current?null:readDraft(requestedOwner,room.id);
   let next=current||{id:room.id,text:me.text,revision:me.revision,dirty:false,conflict:false};
   const locked=me.submittedAt!==null||['judging','finished'].includes(room.status);
   if(locked)next={id:room.id,text:me.text,revision:me.revision,dirty:false,conflict:false};
   else if(!current&&cache&&cache.text!==me.text)next={id:room.id,text:cache.text,revision:me.revision,dirty:true,conflict:cache.revision!==me.revision};
   else if(saved&&room.id===saved.matchId&&me.text===saved.text)next={...next,revision:me.revision,dirty:next.text!==me.text,conflict:false};
   else if(!next.dirty||next.text===me.text)next={id:room.id,text:me.text,revision:me.revision,dirty:false,conflict:false};
   else if(next.revision!==me.revision)next={...next,conflict:true};
   setEditor(next);if(next.dirty&&!next.conflict)storeDraft(requestedOwner,next);
   if(locked&&intent.current?.kind==='submit'){intent.current=null;setUncertain(false);}
  }
 },[setEditor]);
 const reload=useCallback(async()=>{
  if(!owner||window.__tbAdmin||writing.current)return;
  const stamp=generation.current,operation={};if(reading.current)return;reading.current=operation;
  try{const value=await api('pk/v1/state');if(generation.current===stamp&&reading.current===operation)accept(value,owner);return value;}
  catch(issue){if(live.current===owner&&generation.current===stamp){setError(issue.message);recover.current=true;}}
  finally{if(reading.current===operation)reading.current=null;}
 },[api,owner,accept]);
 useEffect(()=>{
  generation.current++;writing.current=null;reading.current=null;clock.current=null;snapshot.current=null;intent.current=null;recover.current=false;setState(null);setEditor(null);setError('');setBusy(false);setSaving(false);setUncertain(false);
  if(owner&&!window.__tbAdmin)void reload();
 },[owner,api,reload,setEditor]);
 const act=useCallback(async(kind,extra={})=>{
  if(!owner||writing.current||!paths[kind])return;
  const current=snapshot.current,answer=draft.current;
  let pending=intent.current;
  if(!pending||pending.kind!==kind){
   if(pending)return;
   const body={requestId:crypto.randomUUID(),...extra};
   if(['submit','draft'].includes(kind)){
    if(!answer||answer.conflict)return;
    Object.assign(body,{matchId:answer.id,text:answer.text,revision:answer.revision});
   }
   if(kind==='cancel')body.ticket=current?.ticket;
   if(kind==='dismiss')body.matchId=current?.match?.id;
   pending={kind,body,owner};
  }
  const operation={};writing.current=operation;generation.current++;
  if(['cancel','submit','draft'].includes(kind))intent.current=pending;
  kind==='draft'?setSaving(true):setBusy(true);setError('');
  try{
   const value=await api('pk/v1/'+paths[kind],pending.body);
   if(live.current===owner&&writing.current===operation){
    accept(value,owner,['submit','draft'].includes(kind)?pending.body:null);
    if(intent.current===pending){intent.current=null;setUncertain(false);}
   }return value;
  }catch(issue){
   if(live.current===owner&&writing.current===operation){
    setError(issue.message);
    recover.current=true;
    if(issue.status>=400&&issue.status<500&&issue.status!==429){if(intent.current===pending)intent.current=null;setUncertain(false);}
    else if(kind==='submit')setUncertain(true);
   }
  }finally{
   if(writing.current===operation){writing.current=null;if(live.current===owner){setBusy(false);setSaving(false);}}
  }
 },[api,owner,accept]);
 useEffect(()=>{
  if(!owner||window.__tbAdmin)return;
  let alive=true;
  const poll=async()=>{
   if(!alive||!navigator.onLine||writing.current||reading.current)return;
   if(intent.current){void act(intent.current.kind);return;}
   if(!active(snapshot.current?.status)){void reload();return;}
   const stamp=generation.current,operation={};reading.current=operation;
   try{const value=await api('pk/v1/game/poll',{});if(alive&&stamp===generation.current&&reading.current===operation)accept(value,owner);}
   catch(issue){if(alive&&live.current===owner&&stamp===generation.current)setError(issue.message);}
   finally{if(reading.current===operation)reading.current=null;}
  };
  // Idle failures also recover a lost join reply without issuing another join.
  const timer=setInterval(()=>{if(active(snapshot.current?.status)||intent.current||recover.current)void poll();},state?.status==='countdown'?500:['active','queued'].includes(state?.status)?2500:1500);
  window.addEventListener('online',poll);window.addEventListener('focus',poll);
  return()=>{alive=false;clearInterval(timer);window.removeEventListener('online',poll);window.removeEventListener('focus',poll);};
 },[api,owner,act,accept,reload,state?.status]);
 useEffect(()=>{
  if(!editor?.dirty||editor.conflict||saving||busy||uncertain||state?.status!=='active')return;
  const timer=setTimeout(()=>void act('draft'),800);return()=>clearTimeout(timer);
 },[editor,saving,busy,uncertain,state?.status,act]);
 const setText=useCallback(text=>{
  const current=draft.current;if(!current||intent.current?.kind==='submit')return;
  const next={...current,text:[...text].slice(0,2000).join(''),dirty:true};setEditor(next);storeDraft(owner,next);
 },[owner,setEditor]);
 const loadServer=useCallback(()=>{
  const room=snapshot.current?.match,me=room?.players?.find(p=>p.owner===owner);if(!me)return;
  const next={id:room.id,text:me.text,revision:me.revision,dirty:false,conflict:false};setEditor(next);storeDraft(owner,next);
 },[owner,setEditor]);
 const keepLocal=useCallback(()=>{
  const room=snapshot.current?.match,me=room?.players?.find(p=>p.owner===owner),current=draft.current;if(!me||!current||current.id!==room.id)return;
  const next={...current,revision:me.revision,dirty:true,conflict:false};setEditor(next);storeDraft(owner,next);
 },[owner,setEditor]);
 return {state:state?.owner===owner?state:null,error,busy,saving:saving||intent.current?.kind==='draft',uncertain,act,reload,clock,editor,setText,loadServer,keepLocal,api};
}
