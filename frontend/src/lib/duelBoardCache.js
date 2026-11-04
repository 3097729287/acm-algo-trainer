import {trainingDay} from './trainingDate.js';
// Confirmed public display data only. Queue, match and reward authority never
// come from this cache. Both owner and mode are checked on every use.
const entries=new Map(),inflight=new WeakMap(),prefix='tb.duel-board.v1:',MAX_AGE=5*60*1000;
const key=(owner,mode)=>owner+':'+mode;
function valid(value,owner,mode,now,exactDay=true){
 return value?.owner===owner&&value.mode===mode&&/^\d{4}-\d{2}-\d{2}$/.test(value.date)&&(!exactDay||value.date===trainingDay(now))&&Array.isArray(value.entries)&&Array.isArray(value.records)&&value.entries.length<=100&&value.records.length<=100;
}
export function readDuelBoard(owner,mode,now=Date.now()){
 if(!owner||!['ranked','thought'].includes(mode))return null;
 const id=key(owner,mode);let saved=entries.get(id);
 if(!saved)try{const raw=localStorage.getItem(prefix+id);if(raw?.length<250000)saved=JSON.parse(raw);}catch{}
 if(!saved||!Number.isFinite(saved.at)||now<saved.at||now-saved.at>MAX_AGE||!valid(saved.value,owner,mode,now)){entries.delete(id);return null;}
 entries.set(id,saved);return saved.value;
}
function save(value,owner,mode){
 if(!valid(value,owner,mode,Date.now()))return;
 const saved={at:Date.now(),value:{...value,records:value.records.slice(0,50),entries:value.entries.slice(0,100),next:value.next||null}},id=key(owner,mode);
 if(entries.size>=8)entries.delete(entries.keys().next().value);entries.set(id,saved);
 try{const raw=JSON.stringify(saved);if(raw.length<250000)localStorage.setItem(prefix+id,raw);}catch{}
}
export function loadDuelBoard(api,owner,mode,{before=null}={}){
 let pending=inflight.get(api);if(!pending){pending=new Map();inflight.set(api,pending);}
 const id=key(owner,mode)+':'+JSON.stringify(before||null);
 if(pending.has(id))return pending.get(id);
 const path=`duel/board?mode=${mode}${before?'&before='+before.before+'&beforeId='+encodeURIComponent(before.beforeId):''}`;
 const request=Promise.resolve().then(()=>api(path)).then(value=>{
  if(!valid(value,owner,mode,Date.now(),false))throw new Error('对战榜单账号或日期不匹配');
  if(!before)save(value,owner,mode);return value;
 }).finally(()=>{if(pending.get(id)===request)pending.delete(id);});
 pending.set(id,request);return request;
}
