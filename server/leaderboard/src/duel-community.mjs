import {AccountError} from './accounts.mjs';
import {duelPoints} from './duel-points.mjs';

export const ACTIVITIES=['online','matching','problem','replay','contest','lecture','lab','wiki','template','ranked','thought','library','lists','growth','records','settings','rankings','idle','offline'];
const absent=error=>error.code==='ER_NO_SUCH_TABLE'||/no such table/i.test(error.message);
const LEASE_MS=90000,leaseId=/^[A-Za-z0-9_-]{11}$/;
const base64=bytes=>btoa(String.fromCharCode(...bytes)).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
function unpack(value){
 const [activity,lease,...extra]=String(value||'').split('~');
 return ACTIVITIES.includes(activity)&&(!lease||leaseId.test(lease))&&!extra.length?{activity,lease:lease||null}:{activity:'offline',lease:null};
}
function packed(activity,lease){const value=activity+'~'+lease;if(value.length>20)throw new AccountError(400,'在线活动过长');return value;}
async function mac(secret,values){
 if(typeof secret!=='string'||!secret)throw new AccountError(503,'在线实例验证暂不可用');
 const key=await crypto.subtle.importKey('raw',new TextEncoder().encode(secret),{name:'HMAC',hash:'SHA-256'},false,['sign','verify']);
 return new Uint8Array(await crypto.subtle.sign('HMAC',key,new TextEncoder().encode(JSON.stringify(values))));
}
async function version(row,secret,owner){
 if(!row)return '';
 const lease=unpack(row.activity).lease;
 return lease||base64((await mac(secret,['presence-row-v2',owner,row.token_hash,row.activity,String(row.last_seen)])).slice(0,8));
}
async function ticket(secret,owner,auth,expected,id){return id+'.'+base64(await mac(secret,['presence-lease-v2',owner,auth,expected,id]));}
async function verifiedLease(secret,owner,auth,request){
 const expected=request.presenceExpected,lease=request.presenceLease;
 if(typeof expected!=='string'||expected!==''&&!leaseId.test(expected)||typeof lease!=='string'||!/^[-\w]{11}\.[-\w]{43}$/.test(lease))throw new AccountError(400,'在线实例凭证无效');
 const id=lease.slice(0,11),proof=await ticket(secret,owner,auth,expected,id);
 // Constant-time verification is provided by WebCrypto, including malformed
 // tickets. Neither the authentication token nor this proof is public output.
 const key=await crypto.subtle.importKey('raw',new TextEncoder().encode(secret),{name:'HMAC',hash:'SHA-256'},false,['verify']);
 const signature=Uint8Array.from(atob(lease.slice(12).replace(/-/g,'+').replace(/_/g,'/')+'='),c=>c.charCodeAt(0));
 if(proof.length!==lease.length||!await crypto.subtle.verify('HMAC',key,signature,new TextEncoder().encode(JSON.stringify(['presence-lease-v2',owner,auth,expected,id]))))throw new AccountError(400,'在线实例凭证无效');
 return {id,expected};
}
export async function presenceSnapshot(game,now){
 try{
  const [raw]=await game.db.execute("SELECT p.user_id,p.activity FROM account_presence p JOIN account_sessions s ON s.user_id=p.user_id AND s.token_hash=p.token_hash JOIN accounts a ON a.user_id=p.user_id WHERE p.last_seen>? AND s.expires_at>? AND s.password_version=a.password_version AND a.login_id<>?", [now-LEASE_MS,Math.floor(now/1000),'admin']);
  const rows=raw.map(row=>({userId:row.user_id,activity:unpack(row.activity).activity}));
  const users=rows.filter(row=>!['idle','offline'].includes(row.activity));
  const idleUsers=rows.filter(row=>row.activity==='idle');
  // Preserve the old active-only contract. Idle clients keep their lease but
  // are exposed separately, so older clients never count them as online.
  return {available:true,serverNow:now,count:users.length,users,idleUsers};
 }catch(error){if(absent(error))return {available:false,serverNow:now,count:null,users:[],idleUsers:[]};throw error;}
}
export async function heartbeat(game,owner,auth,activity,now,request={},secret){
 if(!ACTIVITIES.includes(activity))throw new AccountError(400,'在线状态无效');
 const phase=request.presencePhase;
 if(phase===undefined&&(request.presenceLease!==undefined||request.presenceExpected!==undefined))throw new AccountError(400,'在线实例阶段无效');
 if(phase!==undefined&&!['prepare','recover','activate','beat','close'].includes(phase))throw new AccountError(400,'在线实例阶段无效');
 if(phase==='prepare'&&(request.presenceLease!==undefined||request.presenceExpected!==undefined)||phase==='close'&&activity!=='offline'||['activate','beat'].includes(phase)&&activity==='offline')throw new AccountError(400,'在线实例活动无效');
 let state='legacy',prepared;
 const claim=phase&&phase!=='prepare'?await verifiedLease(secret,owner,auth,request):null;
 await game.db.transaction(async db=>{
  // session() already locks the account row on MySQL. All generations of this
  // owner, including a previously absent presence row, therefore serialize.
  await game.session(db,owner,auth,now);
  const [old]=await db.execute('SELECT token_hash,activity,last_seen FROM account_presence WHERE user_id=?',[owner]);
  const row=old[0],current=unpack(row?.activity),write=async value=>{
   if(row)await db.execute('UPDATE account_presence SET token_hash=?,activity=?,last_seen=? WHERE user_id=?',[auth,value,now,owner]);
   else await db.execute('INSERT INTO account_presence(user_id,token_hash,activity,last_seen) VALUES(?,?,?,?)',[owner,auth,value,now]);
  };
  if(phase==='prepare'||phase==='recover'){
   if(phase==='recover'&&row&&current.activity!=='offline'&&now-Number(row.last_seen)<LEASE_MS){state='superseded';return;}
   const expected=await version(row,secret,owner),id=base64(crypto.getRandomValues(new Uint8Array(8)));
   prepared={presenceLease:await ticket(secret,owner,auth,expected,id),presenceExpected:expected};state='prepared';return;
  }
  if(phase){
   const own=current.lease===claim.id&&row?.token_hash===auth;
   if(phase==='activate'){
    if(own){state=current.activity==='offline'?'superseded':'active';return;}
    if(await version(row,secret,owner)!==claim.expected){state='superseded';return;}
    await write(packed(activity,claim.id));state='active';return;
   }
   if(phase==='close'){
    if(own){if(current.activity!=='offline')await write(packed('offline',claim.id));state='closed';return;}
    // Close can win before its activation arrives. The tombstone changes the
    // version, so the delayed activation cannot revive the closed generation.
    if(await version(row,secret,owner)===claim.expected){await write(packed('offline',claim.id));state='closed';return;}
    state='superseded';return;
   }
   if(!own||current.activity==='offline'){state='superseded';return;}
   await write(packed(activity,claim.id));state='active';return;
  }
  if(current.lease){
   // Old clients remain compatible after the lease/tombstone expires. Their
   // rejected beats never refresh it, and a late legacy close never clears it.
   if(now-Number(row.last_seen)>=LEASE_MS&&activity!=='offline')await write(activity);
   return;
  }
  // A close belongs to its reporting session, and a delayed earlier heartbeat
  // must not resurrect it. Keep the existing single row as an
  // offline marker; it carries no new personal or learning data.
  if(old.length)await db.execute("UPDATE account_presence SET token_hash=?,activity=?,last_seen=? WHERE user_id=? AND last_seen<=? AND (last_seen<? OR activity<>'offline' OR ?='offline') AND (?<>'offline' OR token_hash=?)",[auth,activity,now,owner,now,now,activity,activity,auth]);
  else await db.execute('INSERT INTO account_presence(user_id,token_hash,activity,last_seen) VALUES(?,?,?,?)',[owner,auth,activity,now]);
 });
 return {owner,presenceProtocol:2,presenceState:state,...prepared,...await presenceSnapshot(game,now)};
}
export async function rankedRating(db,owner){
 const [rows]=await db.execute('SELECT rating FROM ranked_duel_ratings WHERE user_id=?',[owner]);
 return rows[0]?.rating??1000;
}
export async function prepareRanked(db,players,now){
 for(const player of players){
  const [rows]=await db.execute('SELECT rating FROM ranked_duel_ratings WHERE user_id=?',[player.owner]);
  if(!rows.length)await db.execute('INSERT INTO ranked_duel_ratings(user_id,rating,games,wins,updated_at) VALUES(?,1000,0,0,?)',[player.owner,now]);
  player.rating=rows[0]?.rating??1000;
 }
}
export async function settleRanked(db,room,now){
 if(room.rankedPolicy!==1)return;
 const [old]=await db.execute('SELECT match_id FROM ranked_duel_records WHERE match_id=?',[room.id]);if(old.length)return;
 const [a,b]=room.players,changes=duelPoints(a.rating,b.rating,room.winner===a.owner?'A':room.winner===b.owner?'B':'draw');
 room.finishedAt=now;room.ratingChanges={[a.owner]:changes[0],[b.owner]:changes[1]};
 for(const p of room.players)await db.execute('UPDATE ranked_duel_ratings SET rating=rating+?,games=games+1,wins=wins+?,updated_at=? WHERE user_id=?',[room.ratingChanges[p.owner],room.winner===p.owner?1:0,now,p.owner]);
 await db.execute('INSERT INTO ranked_duel_records(match_id,finished_at,payload) VALUES(?,?,?)',[room.id,now,JSON.stringify(room)]);
}
export async function duelBoard(game,owner,mode,now,before=null,beforeId=''){
 if(!['ranked','thought'].includes(mode))throw new AccountError(400,'对战模式无效');
 if(before!==null&&(!Number.isSafeInteger(before)||before<0)||beforeId&&!/^[a-f0-9-]{36}$/i.test(beforeId))throw new AccountError(400,'对战记录位置无效');
 const thought=mode==='thought',ratings=thought?'pk_ratings':'ranked_duel_ratings',records=thought?'pk_records':'ranked_duel_records';
 const counts=thought?'0 AS games,0 AS wins':'r.games,r.wins';
 const [rows]=await game.db.execute(`SELECT r.user_id,u.nickname,r.rating,${counts} FROM ${ratings} r JOIN users u ON u.user_id=r.user_id JOIN accounts a ON a.user_id=r.user_id WHERE a.login_id<>? ${thought?'':'AND r.games>0'} ORDER BY r.rating DESC,r.user_id LIMIT 100`,['admin']);
 const dayStart=Math.floor((now+8*3600000)/86400000)*86400000-8*3600000;
 const [history]=await game.db.execute(`SELECT match_id,finished_at,payload FROM ${records} WHERE finished_at>=? AND finished_at<? ${before===null?'':'AND (finished_at<? OR (finished_at=? AND match_id<?))'} ORDER BY finished_at DESC,match_id DESC LIMIT 51`,[dayStart,dayStart+86400000,...(before===null?[]:[before,before,beforeId])]);
 const presence=await presenceSnapshot(game,now),active=new Map(presence.users.map(p=>[p.userId,p.activity])),idle=new Set(presence.idleUsers.map(p=>p.userId));
 const entries=rows.map((r,i)=>({rank:i+1,userId:r.user_id,nickname:r.nickname,rating:r.rating,games:r.games,wins:r.wins,...(presence.available?{online:active.has(r.user_id),idle:idle.has(r.user_id),activity:active.get(r.user_id)||(idle.has(r.user_id)?'idle':null)}:{})}));
 const batch=history.slice(0,50),userIds=new Set(),rooms=batch.map(row=>{const room=JSON.parse(row.payload);room.players.forEach(p=>userIds.add(p.owner));return {row,room};}),names=new Map();
 if(userIds.size){const [users]=await game.db.execute(`SELECT user_id,nickname FROM users WHERE user_id IN (${[...userIds].map(()=>'?').join(',')})`,[...userIds]);users.forEach(u=>names.set(u.user_id,u.nickname));}
 return {owner,mode,serverNow:now,timezone:'Asia/Shanghai',date:new Date(dayStart+8*3600000).toISOString().slice(0,10),entries,rating:await rankedOrThoughtRating(game.db,ratings,owner),records:rooms.map(({row,room})=>({id:row.match_id,finishedAt:row.finished_at,winner:room.winner??null,judgeFailed:room.judgeFailed===true,players:room.players.map(p=>({userId:p.owner,nickname:names.get(p.owner)||p.nickname||p.handle||'—',rating:p.rating,change:room.ratingChanges?.[p.owner]??0}))})),next:history.length>50?{before:batch.at(-1).finished_at,beforeId:batch.at(-1).match_id}:null};
}
async function rankedOrThoughtRating(db,table,owner){const [rows]=await db.execute(`SELECT rating FROM ${table} WHERE user_id=?`,[owner]);return rows[0]?.rating??1000;}
