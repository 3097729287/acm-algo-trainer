import {createHash} from 'node:crypto';
import {codeforcesStatus} from './gameplay.mjs';

const terminal=new Set(['AC','WA','TLE','MLE','RE','CE','OLE']);
const cfVerdicts={OK:'AC',WRONG_ANSWER:'WA',TIME_LIMIT_EXCEEDED:'TLE',MEMORY_LIMIT_EXCEEDED:'MLE',RUNTIME_ERROR:'RE',COMPILATION_ERROR:'CE',IDLENESS_LIMIT_EXCEEDED:'TLE',OUTPUT_LIMIT_EXCEEDED:'OLE'};
const ncVerdicts={3:'RE',4:'WA',5:'AC',6:'TLE',7:'MLE',10:'OLE',12:'CE',13:'WA',15:'RE',16:'RE',21:'RE'};
const cache=new Map(),inflight=new Map(),gates=new Map();
const digest=value=>createHash('sha256').update(value).digest('hex');
const identity=value=>typeof value==='number'?Number.isSafeInteger(value)&&value>0?String(value):null:
 typeof value==='string'&&/^[1-9]\d{0,19}$/.test(value)?value:null;

export function teamPlatform(url){
 let target;try{target=new URL(url);}catch{return null;}
 if(target.protocol!=='https:'||target.username||target.password||target.port||target.search||target.hash)return null;
 const host=target.hostname.replace(/^www\./,'');let match;
 if(host==='codeforces.com'&&(match=/^\/(contest|gym)\/([1-9]\d*)\/problem\/([A-Z]\d?)$/.exec(target.pathname)))return {id:'codeforces',host,contest:match[2],problem:match[3]};
 if(host==='atcoder.jp'&&(match=/^\/contests\/([a-zA-Z0-9_-]{1,100})\/tasks\/([a-zA-Z0-9_-]{1,100})$/.exec(target.pathname)))return {id:'atcoder',host,contest:match[1],problem:match[2]};
 if(host==='ac.nowcoder.com'&&(match=/^\/acm\/contest\/([1-9]\d*)\/([A-Z]\d?)$/.exec(target.pathname)))return {id:'nowcoder',host,contest:match[1],problem:match[2]};
 return null;
}

export const validTeamHandle=(platform,value)=>typeof value==='string'&&(platform==='nowcoder'?/^[1-9]\d{0,19}$/:/^[a-zA-Z0-9_.-]{1,64}$/).test(value);

async function publicJson(url){
 const previous=cache.get(url);if(previous?.until>Date.now())return previous.value;
 if(inflight.has(url))return inflight.get(url);
 const work=(async()=>{
  const host=new URL(url).hostname,prior=gates.get(host)||Promise.resolve();
  let release;const slot=new Promise(done=>{release=done;});gates.set(host,prior.then(()=>slot));
  await prior;setTimeout(release,1250).unref?.();
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),7000);
  try{
   const response=await fetch(url,{signal:controller.signal,redirect:'error',headers:{Accept:'application/json','User-Agent':'ToBe team receipt verification'}});
   if(!response.ok)throw Error('public source unavailable');
   const reader=response.body.getReader(),parts=[];let size=0;
   for(;;){const {value,done}=await reader.read();if(done)break;size+=value.length;if(size>4*1024*1024){await reader.cancel();throw Error('public source too large');}parts.push(value);}
   const value=JSON.parse(Buffer.concat(parts).toString('utf8'));
   if(cache.size>=256)cache.delete(cache.keys().next().value);cache.set(url,{value,until:Date.now()+10000});return value;
  }finally{clearTimeout(timer);}
 })();inflight.set(url,work);
 try{return await work;}finally{inflight.delete(url);}
}

const timestamp=value=>{
 if(typeof value!=='number'||!Number.isFinite(value)||value<=0)return null;
 const ms=value<1e12?value*1000:value;
 return Number.isFinite(ms)?ms:null;
};

// Parse only a matching public receipt: no caller-supplied verdict, timestamp,
// URL, points or code can be used to manufacture a confirmed result.
export function parseTeamReceipt(platform,payload,{handle,submissionId,url}){
 const task=teamPlatform(url);if(!task||task.id!==platform)return null;
 let row,verdict,submittedAt,source;
 if(platform==='codeforces'){
  const rows=Array.isArray(payload)?payload:payload?.status==='OK'?payload.result:null;
  if(!Array.isArray(rows))return null;
  row=rows.find(r=>identity(r?.id)===submissionId&&identity(r.problem?.contestId)===task.contest&&r.problem.index===task.problem
    &&r.author?.members?.some(m=>typeof m.handle==='string'&&m.handle.toLowerCase()===handle.toLowerCase()));
  if(!row)return null;verdict=cfVerdicts[row.verdict];submittedAt=timestamp(row.creationTimeSeconds);source='Codeforces official API';
 }else if(platform==='atcoder'){
  if(!Array.isArray(payload))return null;
  row=payload.find(r=>identity(r?.id)===submissionId&&r.contest_id===task.contest&&r.problem_id===task.problem
    &&typeof r.user_id==='string'&&r.user_id.toLowerCase()===handle.toLowerCase());
  if(!row)return null;verdict=row.result;submittedAt=timestamp(row.epoch_second);source='AtCoder Problems public receipts';
 }else if(platform==='nowcoder'){
  if(payload?.code!==0||!Array.isArray(payload.data?.submitDataList)||!Array.isArray(payload.data?.problemData))return null;
  const ids=new Set(payload.data.problemData.filter(p=>String(p.index).toUpperCase()===task.problem).map(p=>String(p.problemId)));
  for(const group of payload.data.submitDataList){
   if(String(group?.basicInfo?.contestId)!==task.contest||group.signUpUsers?.some(u=>String(u.uid)===handle&&u.team))continue;
   row=group.submissions?.find(r=>identity(r.submissionId)===submissionId&&identity(r.uid)===handle&&ids.has(String(r.problemId)));
   if(row)break;
  }
  if(!row)return null;verdict=ncVerdicts[row.status];submittedAt=timestamp(row.submitTime);source='Nowcoder public submission board';
  if(verdict==='AC'&&typeof row.rightCaseRate==='number'&&row.rightCaseRate<1)return null;
 }
 if(!row||!terminal.has(verdict)||submittedAt===null)return null;
 return {platform,handle,submissionId,url,verdict,submittedAt,source,proofSha256:digest(JSON.stringify(row))};
}

export async function verifyTeamReceipt(request){
 const task=teamPlatform(request.url);if(!task||!validTeamHandle(task.id,request.handle))return null;
 if(task.id==='codeforces')return parseTeamReceipt(task.id,await codeforcesStatus(request.handle),request);
 if(task.id==='atcoder'){
  const from=Math.max(0,Math.floor((request.issuedAt-2000)/1000));
  const url='https://kenkoooo.com/atcoder/atcoder-api/v3/user/submissions?user='+encodeURIComponent(request.handle)+'&from_second='+from;
  return parseTeamReceipt(task.id,await publicJson(url),request);
 }
 const query=new URLSearchParams({currentContestId:task.contest,contestList:task.contest,rankScope:'ALL'});
 return parseTeamReceipt(task.id,await publicJson('https://ac.nowcoder.com/acm/contest/rank/submit-list?'+query),request);
}
