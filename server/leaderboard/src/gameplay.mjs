import {createHash, randomInt, randomUUID} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {AccountError} from './accounts.mjs';

const fail=(status,message)=>{throw new AccountError(status,message);};
const hash=value=>createHash('sha256').update(value).digest('hex');
const uuid=/^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i;
const catalogue=JSON.parse(readFileSync(new URL('./duel-problems.json',import.meta.url),'utf8'));
export const STICKERS=Object.freeze([
 ...['spark','leaf','drop','cloud'].map(shape=>({id:'common-'+shape,rarity:'common',shape})),
 ...['flame','bolt','sun','comet'].map(shape=>({id:'rare-'+shape,rarity:'rare',shape})),
 ...['moon','planet','crystal','butterfly'].map(shape=>({id:'epic-'+shape,rarity:'epic',shape})),
 ...['gem','crown','galaxy','phoenix'].map(shape=>({id:'legendary-'+shape,rarity:'legendary',shape})),
]);
const empty=()=>({revision:0,units:[],grants:{}});
const scalar=(n,lo,hi)=>typeof n==='number'&&Number.isFinite(n)&&n>=lo&&n<=hi;
function grantIdentity(value,now){
 if(typeof value.day!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(value.day)||!Number.isFinite(Date.parse(value.day+'T00:00:00Z'))||value.day>new Date(now+8*3600000).toISOString().slice(0,10))fail(400,'任务日期无效');
 if(typeof value.taskId!=='string'||!/^[-a-z0-9:]{1,64}$/.test(value.taskId)||!Number.isInteger(value.xp)||value.xp<1||value.xp>1000)fail(400,'任务奖励无效');
 // The authenticated desktop verifies the durable daily_missions claim first.
 // As with existing ranking events this is account evidence, not anti-cheat proof.
 return value.day+':'+value.taskId;
}
export function rewardRarity(task){
 const difficulty=Number(task.minDifficulty)||0,xp=Number(task.xp)||0;
 return difficulty>=2200||xp>=100?'legendary':difficulty>=1800||xp>=60?'epic':difficulty>=1400||xp>=30?'rare':'common';
}

let nextProviderStart=0;
async function providerSlot(){
 // Codeforces explicitly allows one API request per two seconds. Reserve a
 // bounded slot shared by all matches, rather than retrying rate-limit errors.
 const now=Date.now(),delay=Math.max(0,nextProviderStart-now);
 if(delay>6000)throw new Error('provider capacity');
 nextProviderStart=Math.max(now,nextProviderStart)+2100;
 if(delay)await new Promise(resolve=>setTimeout(resolve,delay));
}
export async function codeforcesStatus(handle){
 await providerSlot();
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),8000);
 try{
  const response=await fetch('https://codeforces.com/api/user.status?handle='+encodeURIComponent(handle)+'&from=1&count=1000',{signal:controller.signal,redirect:'error'});
  if(!response.ok)throw new Error('provider');
  const reader=response.body.getReader();let size=0;const chunks=[];
  for(;;){const {value,done}=await reader.read();if(done)break;size+=value.length;if(size>2*1024*1024){await reader.cancel();throw new Error('size');}chunks.push(value);}
  const result=JSON.parse(Buffer.concat(chunks).toString('utf8'));
  if(result.status!=='OK'||!Array.isArray(result.result))throw new Error('provider');
  return result.result;
 }finally{clearTimeout(timer);}
}

export class Gameplay {
 constructor(database,dialect='mysql',{verify=codeforcesStatus,problems=catalogue.problems}={}){
  this.db=database;this.dialect=dialect;this.verify=verify;this.problems=problems;
  this.checking=new Map();this.checked=new Map();
 }
 async available(){try{await this.db.execute('SELECT payload FROM gameplay_accounts LIMIT 0');await this.db.execute('SELECT payload FROM duel_lobby WHERE singleton=1');return true;}catch(e){if(e.code==='ER_NO_SUCH_TABLE'||/no such table/i.test(e.message))return false;throw e;}}
 lock(sql){return sql+(this.dialect==='mysql'?' FOR UPDATE':'');}
 async session(db,owner,auth,now){
  await db.execute(this.lock('SELECT user_id FROM accounts WHERE user_id=?'),[owner]);
  const [rows]=await db.execute('SELECT token_hash FROM account_sessions WHERE user_id=? AND token_hash=? AND expires_at>?',[owner,auth,Math.floor(now/1000)]);
  if(!rows.length)fail(401,'账号已在另一台设备登录，请重新登录');
 }
 async account(db,owner){
  const insert=this.dialect==='mysql'?'INSERT IGNORE':'INSERT OR IGNORE';
  await db.execute(`${insert} INTO gameplay_accounts(user_id,payload) VALUES(?,?)`,[owner,JSON.stringify(empty())]);
  const [rows]=await db.execute(this.lock('SELECT payload FROM gameplay_accounts WHERE user_id=?'),[owner]);
  return JSON.parse(rows[0].payload);
 }
 async saveAccount(db,owner,state){await db.execute('UPDATE gameplay_accounts SET payload=? WHERE user_id=?',[JSON.stringify(state),owner]);}
 async once(db,owner,kind,value,action){
  if(!uuid.test(value.requestId||''))fail(400,'请求编号无效');
  const digest=hash(JSON.stringify([kind,...Object.keys(value).sort().map(key=>[key,value[key]])]));
  const [old]=await db.execute('SELECT request_hash,response FROM gameplay_operations WHERE user_id=? AND request_id=?',[owner,value.requestId]);
  if(old.length){if(old[0].request_hash!==digest)fail(409,'请求编号已用于其他操作');return JSON.parse(old[0].response);}
  const response=await action();
  await db.execute('INSERT INTO gameplay_operations(user_id,request_id,request_hash,response) VALUES(?,?,?,?)',[owner,value.requestId,digest,JSON.stringify(response)]);
  return response;
 }
 async stickers(owner){
  const [rows]=await this.db.execute('SELECT payload FROM gameplay_accounts WHERE user_id=?',[owner]);
  return {owner,catalogue:STICKERS,...(rows.length?JSON.parse(rows[0].payload):empty())};
 }
 async stickerWrite(owner,auth,kind,value,now){
  return this.db.transaction(async db=>{
   await this.session(db,owner,auth,now);const state=await this.account(db,owner);
   return this.once(db,owner,'stickers/'+kind,value,async()=>{
    if(kind==='grant'){
     const key=grantIdentity(value,now);
     if(!Object.hasOwn(state.grants,key)){
      if(state.units.length>=20000)fail(409,'贴纸库存已满');
      const rarity=rewardRarity(value),pool=STICKERS.filter(item=>item.rarity===rarity),sticker=pool[randomInt(pool.length)];
      const unit={id:randomUUID(),stickerId:sticker.id,placement:null,revision:0};
      state.units.push(unit);state.grants[key]={unitId:unit.id,rarity,grantedAt:now};state.revision++;
     }
    }else{
     const unit=state.units.find(item=>item.id===value.unitId);
     if(!unit)fail(404,'没有找到这张贴纸');
     if(value.revision!==unit.revision)fail(409,'贴纸已在其他窗口更新，请刷新');
     if(kind==='place'){
      if(!scalar(value.x,0,1)||!scalar(value.y,0,1)||!scalar(value.angle,-180,180))fail(400,'贴纸位置无效');
      if(!unit.placement&&state.units.filter(item=>item.placement).length>=200)fail(409,'贴纸区域已满');
      unit.placement={x:value.x,y:value.y,angle:value.angle};
     }else if(kind==='recycle'){
      if(!unit.placement)fail(409,'贴纸已经回收');unit.placement=null;
     }else fail(404,'没有找到这个操作');
     unit.revision++;state.revision++;
    }
    await this.saveAccount(db,owner,state);
    return {owner,revision:state.revision,requestId:value.requestId};
   });
  });
 }
 async member(db,owner){const [rows]=await db.execute('SELECT match_id FROM duel_members WHERE user_id=?',[owner]);return rows[0]?.match_id;}
 async match(db,id){if(!id)return null;const [rows]=await db.execute('SELECT payload FROM duel_matches WHERE match_id=?',[id]);return rows.length?JSON.parse(rows[0].payload):null;}
 async saveMatch(db,room){await db.execute('UPDATE duel_matches SET payload=? WHERE match_id=?',[JSON.stringify(room),room.id]);}
 view(owner,lobby,room,now){
  const ticket=lobby.queue.find(item=>item.owner===owner);
  return {owner,serverNow:now,status:room?(room.status):ticket?'queued':'idle',ticket:ticket?.ticket||null,
   match:room?{...room,players:room.players.map(player=>({...player,online:now-player.lastSeen<20000}))}:null};
 }
 async read(owner,now){
  const [rows]=await this.db.execute('SELECT payload FROM duel_lobby WHERE singleton=1');
  return this.view(owner,JSON.parse(rows[0].payload),await this.match(this.db,await this.member(this.db,owner)),now);
 }
 async duelWrite(owner,auth,kind,value,now){
  // Network reads happen outside the write transaction. The result is bound to
  // one immutable room and revalidated with the session before committing it.
  const existing=await this.match(this.db,await this.member(this.db,owner));
  let receipts=null;
  if(kind==='poll'&&existing?.status==='active')receipts=await this.refresh(existing,now);
  return this.db.transaction(async db=>{
   const [rows]=await db.execute(this.lock('SELECT payload FROM duel_lobby WHERE singleton=1'));
   const lobby=JSON.parse(rows[0].payload);
   await this.session(db,owner,auth,now);
   // The account lock also serializes request IDs across all gameplay writes.
   const run=async()=>{
    lobby.queue=lobby.queue.filter(item=>now-item.lastSeen<30000);
    let room=await this.match(db,await this.member(db,owner));
    if(room?.status==='active'){
     const player=room.players.find(item=>item.owner===owner);player.lastSeen=now;
     if(receipts&&room.id===existing?.id){
      for(const update of receipts){
       const p=room.players.find(item=>item.owner===update.owner);
       if(update.error){p.syncError=true;continue;}
       p.syncError=false;
       const inWindow=update.items.filter(item=>Number.isSafeInteger(item.id)&&item.problem?.contestId===room.problem.contestId&&item.problem?.index===room.problem.index&&item.author?.members?.some(member=>member.handle?.toLowerCase()===p.handle.toLowerCase())&&item.creationTimeSeconds*1000>=room.startedAt&&item.creationTimeSeconds*1000<=Math.min(now,room.deadline));
       p.judging=inWindow.some(item=>!item.verdict||item.verdict==='TESTING');
       const valid=inWindow.filter(item=>['OK','WRONG_ANSWER','TIME_LIMIT_EXCEEDED','MEMORY_LIMIT_EXCEEDED','RUNTIME_ERROR','COMPILATION_ERROR','IDLENESS_LIMIT_EXCEEDED','PARTIAL'].includes(item.verdict));
       const accepted=valid.filter(item=>item.verdict==='OK').sort((a,b)=>a.creationTimeSeconds-b.creationTimeSeconds||a.id-b.id)[0];
       // Public API can be briefly incomplete. Never erase a verified receipt.
       p.attempts=Math.max(p.attempts,valid.length);
       if(accepted&&(!p.acceptedAt||accepted.creationTimeSeconds*1000<p.acceptedAt)){p.acceptedAt=accepted.creationTimeSeconds*1000;p.submissionId=accepted.id;}
      }
      room.checkedAt=now;
     }
     // A provider outage at the deadline leaves a visible pending settlement;
     // the next explicit poll can verify late-published, in-window receipts.
     if(room.players.every(p=>p.acceptedAt)||now>=room.deadline+5000&&receipts?.every(p=>!p.error)&&room.players.every(p=>!p.judging)){
      room.status='finished';const scores=room.players.map(p=>p.acceptedAt??Infinity);
      room.winner=scores[0]===scores[1]?null:room.players[scores[0]<scores[1]?0:1].owner;
     }
     await this.saveMatch(db,room);
    }
    if(kind==='join'){
     if(!/^[A-Za-z0-9_.-]{3,24}$/.test(value.handle||''))fail(400,'请先绑定 Codeforces 账号');
     if(room?.status==='active')return this.view(owner,lobby,room,now);
     let entry=lobby.queue.find(item=>item.owner===owner);
     if(entry){entry.lastSeen=now;return this.view(owner,lobby,null,now);}
     if(lobby.queue.length>=1000)fail(429,'匹配请求较多，请稍后重试');
     const peer=lobby.queue.find(item=>item.owner!==owner&&item.handle.toLowerCase()!==value.handle.toLowerCase());
     if(peer){
      lobby.queue=lobby.queue.filter(item=>item!==peer);
      const problem=this.problems[randomInt(this.problems.length)];
      const startedAt=Math.ceil(now/1000)*1000;
      room={id:randomUUID(),status:'active',startedAt,deadline:startedAt+30*60000,problem,players:[{owner:peer.owner,handle:peer.handle},{owner,handle:value.handle}].map(p=>({...p,attempts:0,acceptedAt:null,lastSeen:now})),winner:null,checkedAt:null};
      await db.execute('INSERT INTO duel_matches(match_id,payload) VALUES(?,?)',[room.id,JSON.stringify(room)]);
      for(const p of room.players){
       await db.execute('DELETE FROM duel_members WHERE user_id=?',[p.owner]);
       await db.execute('INSERT INTO duel_members(user_id,match_id) VALUES(?,?)',[p.owner,room.id]);
      }
     }else{
      lobby.queue.push({owner,handle:value.handle,ticket:value.requestId,lastSeen:now});room=null;
      await db.execute('DELETE FROM duel_members WHERE user_id=?',[owner]);
     }
    }else if(kind==='cancel'){
     lobby.queue=lobby.queue.filter(item=>item.owner!==owner||item.ticket!==value.ticket);
    }else if(kind==='poll'){
     const entry=lobby.queue.find(item=>item.owner===owner);if(entry)entry.lastSeen=now;
    }else if(kind==='dismiss'){
     if(room&&value.matchId!==room.id)fail(409,'比赛已更新，请刷新');
     if(room?.status==='active')fail(409,'比赛仍在进行');
     await db.execute('DELETE FROM duel_members WHERE user_id=?',[owner]);room=null;
    }else fail(404,'没有找到这个操作');
    await db.execute('UPDATE duel_lobby SET payload=? WHERE singleton=1',[JSON.stringify(lobby)]);
    return this.view(owner,lobby,room,now);
   };
   return kind==='poll'?run():this.once(db,owner,'duels/'+kind,value,run);
  });
 }
 async refresh(room,now){
  const cached=this.checked.get(room.id);
  if(cached&&now-cached.at<5000)return cached.value;
  if(this.checking.has(room.id))return this.checking.get(room.id);
  const operation=Promise.all(room.players.map(async player=>{
   try{return {owner:player.owner,items:await this.verify(player.handle)};}catch{return {owner:player.owner,error:true};}
  })).then(value=>{this.checked.set(room.id,{at:now,value});if(this.checked.size>256)this.checked.delete(this.checked.keys().next().value);return value;}).finally(()=>this.checking.delete(room.id));
  this.checking.set(room.id,operation);return operation;
 }
}
