import {useCallback,useEffect,useRef,useState} from 'react';

const actions=new Set(['create','join','leave','configure','ready','start','claim','release','select','finish']);
const liveRoom=room=>['countdown','active'].includes(room?.status);
const pendingKey=owner=>`tb:team:pending:${owner}`;
const openKey=owner=>`tb:team:open:${owner}`;
const issue=(message,code='TEAM_OWNER_CHANGED')=>Object.assign(new Error(message),{status:409,code});
const read=key=>{try{return JSON.parse(localStorage.getItem(key));}catch{return null;}};
const store=(key,value)=>{try{value===null?localStorage.removeItem(key):localStorage.setItem(key,JSON.stringify(value));}catch{/* The account SQLite journal remains authoritative for native submits. */}};

// The controller lives in App so membership heartbeats and deadline updates
// continue while the user visits another section. Only an open workbench
// renews this account's editor lease.
export default function useTeamTraining(api,owner){
 const [state,setState]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[connected,setConnected]=useState(false),[opened,setOpened]=useState(null),[tick,setTick]=useState(0);
 const current=useRef(null),account=useRef(owner),clock=useRef(null),generation=useRef(0),readGeneration=useRef(0),reading=useRef(null),writing=useRef(null),pending=useRef(null),openRoom=useRef(null),chain=useRef(Promise.resolve()),native=useRef(new Map());
 account.current=owner;openRoom.current=opened;
 const accept=useCallback((value,expected)=>{
  if(account.current!==expected||value?.owner!==expected||!Number.isFinite(value.serverNow))throw issue('账号已切换，请重新读取');
  if(clock.current&&value.serverNow<clock.current.server)return false;
  clock.current={server:value.serverNow,local:performance.now()};current.current=value;
  if(openRoom.current&&value.room?.id!==openRoom.current){openRoom.current=null;setOpened(null);}
  setState(value);setConnected(true);setError('');return true;
 },[]);
 const reload=useCallback(async()=>{
  if(!owner||window.__tbAdmin||reading.current||writing.current)return;
  const sequence=generation.current,readStamp=readGeneration.current,operation={};reading.current=operation;
  try{
   const view=current.current,room=view?.room;
   const value=view?.team?await api('team-training/poll',{...(room?{roomId:room.id}:{}),
     ...(room&&openRoom.current===room.id&&room.lease?.owner===owner&&room.lease.token?{leaseToken:room.lease.token}:{})}):await api('team-training/state');
   if(sequence===generation.current&&readStamp===readGeneration.current&&reading.current===operation)accept(value,owner);
   return value;
  }catch(e){if(account.current===owner&&sequence===generation.current){setError(e.message);setConnected(false);}}
  finally{if(reading.current===operation)reading.current=null;}
 },[api,owner,accept]);
 const enqueue=useCallback(operation=>{
  const expected=owner,sequence=generation.current;
  const next=chain.current.catch(()=>undefined).then(()=>{
   if(account.current!==expected||sequence!==generation.current)throw issue('账号已切换，请重新读取');
   return operation(expected);
  });chain.current=next;return next;
 },[owner]);
 const act=useCallback((kind,extra={})=>enqueue(async expected=>{
  if(!actions.has(kind))throw issue('团队操作无效','TEAM_REQUEST_INVALID');
  let intent=pending.current;
  if(intent&&intent.kind!==kind)throw issue('请先重试尚未确认的团队操作','TEAM_OPERATION_PENDING');
  if(!intent){
   if(kind==='start'||kind==='ready'&&extra.ready){const {saveBeforeUpdate}=await import('../app/Workbench.jsx');await saveBeforeUpdate();}
   const view=current.current,room=view?.room;
   const body={requestId:crypto.randomUUID(),...extra};
   if(['leave','configure','ready','start'].includes(kind))body.teamRevision=view?.team?.revision;
   if(kind==='ready')body.configurationRevision=view?.team?.configurationRevision;
   if(['claim','release','select','finish'].includes(kind))body.roomId=room?.id;
   if(['release','select'].includes(kind))body.leaseToken=room?.lease?.token;
   intent={kind,body};pending.current=intent;store(pendingKey(expected),intent);
  }
  const operation={};readGeneration.current++;writing.current=operation;setBusy(true);
  try{
   const value=await api('team-training/'+kind,intent.body);accept(value,expected);
   pending.current=null;store(pendingKey(expected),null);return value;
  }catch(e){
   if(account.current===expected){setError(e.message);setConnected(false);
    if(e.status>=400&&e.status<500&&e.status!==429){pending.current=null;store(pendingKey(expected),null);}}
   throw e;
  }finally{if(writing.current===operation){writing.current=null;if(account.current===expected)setBusy(false);}}
 }),[api,enqueue,accept]);
 const enter=useCallback(()=>enqueue(async expected=>{
  const room=current.current?.room;if(!room)throw issue('没有进行中的团队比赛','TEAM_ROOM_CHANGED');
  const operation={};readGeneration.current++;writing.current=operation;setBusy(true);
  try{
   const {saveBeforeUpdate}=await import('../app/Workbench.jsx');await saveBeforeUpdate();
   const value=await api('team-training/workbench/enter',{roomId:room.id});accept(value,expected);
   setOpened(room.id);store(openKey(expected),room.id);return value;
  }catch(e){if(account.current===expected)setError(e.message);throw e;}
  finally{if(writing.current===operation){writing.current=null;if(account.current===expected)setBusy(false);}}
 }),[api,enqueue,accept]);
 const close=useCallback(()=>{
  const room=current.current?.room;setOpened(null);openRoom.current=null;store(openKey(owner),null);
  if(liveRoom(room)&&room.lease?.owner===owner)void act('release').catch(()=>undefined);
 },[owner,act]);

 useEffect(()=>{
  generation.current++;reading.current=null;writing.current=null;pending.current=owner?read(pendingKey(owner)):null;
  if(pending.current&&!actions.has(pending.current.kind))pending.current=null;
  chain.current=Promise.resolve();current.current=null;clock.current=null;native.current=new Map();
  setState(null);setError('');setBusy(false);setConnected(false);setOpened(null);
  if(owner&&!window.__tbAdmin)void reload();
 },[owner,api,reload]);
 useEffect(()=>{
  if(!owner||window.__tbAdmin)return;
  const timer=setInterval(()=>{
   if(writing.current||reading.current)return;
   if(pending.current)void act(pending.current.kind).catch(()=>undefined);else void reload();
  },liveRoom(state?.room)?2500:state?.team?7500:25000);
  const refresh=()=>{if(!writing.current)void reload();};
  window.addEventListener('focus',refresh);window.addEventListener('online',refresh);
  return()=>{clearInterval(timer);window.removeEventListener('focus',refresh);window.removeEventListener('online',refresh);};
 },[owner,state?.team?.id,state?.room?.status,act,reload]);
 useEffect(()=>{
  if(!liveRoom(state?.room))return;
  const timer=setInterval(()=>setTick(t=>t+1),500);return()=>clearInterval(timer);
 },[state?.room?.status]);
 useEffect(()=>{
  const saved=owner&&read(openKey(owner));
  if(saved&&state?.room?.id===saved&&liveRoom(state.room)&&!opened&&!busy)void enter().catch(()=>undefined);
 },[owner,state?.room?.id,opened,busy,enter]);

 const workbenchApi=useCallback(async(path,body)=>{
  const expected=owner,view=current.current,room=view?.room;
  if(account.current!==expected||!room||openRoom.current!==room.id)throw issue('团队比赛已切换，请重新进入','TEAM_ROOM_CHANGED');
  const parsed=new URL(path,'http://local.invalid/'),name=parsed.pathname.slice(1);
  // Status/receipt reads remain bound by the existing native session owner.
  if(!body&&name==='problem'){
   const query=new URLSearchParams({id:parsed.searchParams.get('id'),roomId:room.id});
   if(parsed.searchParams.get('refresh')==='1')query.set('refresh','1');
   const answer=await api('team-training/workbench/problem?'+query);
   if(account.current!==expected)throw issue('账号已切换，请重新读取');
   if(answer.sharedState)accept(answer.sharedState,expected);return answer;
  }
  if(!body&&name==='submissions'){
   parsed.searchParams.set('contestId','team-'+room.id);return api('submissions?'+parsed.searchParams);
  }
  if(body&&name==='draft'||body&&name==='submissions'||body&&name.startsWith('official/')&&['official/open','official/submit'].includes(name)){
   const action=name==='draft'?'draft':name==='submissions'?'run':name==='official/open'?'official-open':'official-submit';
   if(name==='submissions'&&body.mode!=='run')throw issue('团队比赛请使用原站提交','TEAM_NATIVE_REQUIRED');
   return enqueue(async bound=>{
    const latest=current.current?.room,stamp=clock.current;
    const now=stamp?stamp.server+performance.now()-stamp.local:Infinity;
    if(!connected||latest?.id!==room.id||latest.status!=='active'||latest.lease?.owner!==bound||latest.lease.until<=now)
     throw issue('编辑控制已变更，代码已保留','TEAM_EDITOR_CHANGED');
    const payload={requestId:crypto.randomUUID(),roomId:room.id,leaseToken:latest.lease.token,id:body.id,
      revision:body.documentRevision,language:body.language,code:body.code,
      ...(action==='run'?{input:body.input||'',sampleRun:body.sampleRun}:{} )};
    const key=`${room.id}:${body.id}:${action}`;
    if(action.startsWith('official-')){
     const sha=[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(body.code)))].map(n=>n.toString(16).padStart(2,'0')).join('');
     const prior=native.current.get(key)||read(`tb:team:native:${bound}:${key}`);
     if(prior&&prior.sha===sha&&prior.revision===payload.revision)payload.requestId=prior.requestId;
     const intent={sha,revision:payload.revision,requestId:payload.requestId};native.current.set(key,intent);store(`tb:team:native:${bound}:${key}`,intent);
    }
    const operation={};readGeneration.current++;writing.current=operation;
    try{
     const answer=await api('team-training/workbench/'+action,payload);
     if(account.current!==bound)throw issue('账号已切换，请重新读取');
     if(answer.sharedState)accept(answer.sharedState,bound);
     if(action.startsWith('official-')&&answer.sessionId){const intent=native.current.get(key);if(intent){intent.sessionId=answer.sessionId;store(`tb:team:native:${bound}:${key}`,intent);}}
     if(action.startsWith('official-')&&answer.status==='finished'&&answer.submissionId){native.current.delete(key);store(`tb:team:native:${bound}:${key}`,null);}
     return answer;
    }catch(e){if(account.current===bound){
      if(e.code==='TEAM_AUTHORIZATION_EXPIRED'){native.current.delete(key);store(`tb:team:native:${bound}:${key}`,null);}
      setError(e.message);setConnected(false);
    }throw e;}
    finally{if(writing.current===operation)writing.current=null;}
   });
  }
  if(body&&name==='problem/translate')return api('team-training/workbench/translate',{roomId:room.id,id:body.id});
  const answer=await api(path,body);
  if(account.current!==expected)throw issue('账号已切换，请重新读取');
  if(!body&&name==='official/status'&&answer.status==='finished'){
   for(const [key,intent] of native.current)if(intent.sessionId===answer.sessionId){native.current.delete(key);store(`tb:team:native:${expected}:${key}`,null);}
  }
  return answer;
 },[api,owner,accept,enqueue,connected]);
 const serverNow=clock.current?clock.current.server+performance.now()-clock.current.local:Date.now();
 const room=state?.owner===owner?state.room:null;
 const canEdit=Boolean(connected&&room?.status==='active'&&room.lease?.owner===owner&&room.lease.until>serverNow);
 return {state:state?.owner===owner?state:null,error,busy,connected,opened,serverNow,canEdit,act,reload,enter,close,workbenchApi,
  read:async path=>{const answer=await api('team-training/'+path);if(account.current!==owner||answer.owner!==owner)throw issue('账号已切换');return answer;},tick};
}
