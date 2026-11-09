import {AccountError} from './accounts.mjs';
import {duelPoints} from './duel-points.mjs';

export const ACTIVITIES=['online','matching','problem','replay','contest','lecture','lab','wiki','template','ranked','thought','library','lists','growth','records','settings','rankings','idle','offline'];
const absent=error=>error.code==='ER_NO_SUCH_TABLE'||/no such table/i.test(error.message);
export async function presenceSnapshot(game,now){
 try{
  const [rows]=await game.db.execute("SELECT p.user_id,p.activity FROM account_presence p JOIN account_sessions s ON s.user_id=p.user_id AND s.token_hash=p.token_hash JOIN accounts a ON a.user_id=p.user_id WHERE p.last_seen>? AND p.activity<>'offline' AND s.expires_at>? AND s.password_version=a.password_version AND a.login_id<>?", [now-90000,Math.floor(now/1000),'admin']);
  const users=rows.filter(row=>row.activity!=='idle').map(row=>({userId:row.user_id,activity:row.activity}));
  const idleUsers=rows.filter(row=>row.activity==='idle').map(row=>({userId:row.user_id,activity:'idle'}));
  // Preserve the old active-only contract. Idle clients keep their lease but
  // are exposed separately, so older clients never count them as online.
  return {available:true,serverNow:now,count:users.length,users,idleUsers};
 }catch(error){if(absent(error))return {available:false,serverNow:now,count:null,users:[],idleUsers:[]};throw error;}
}
export async function heartbeat(game,owner,auth,activity,now){
 if(!ACTIVITIES.includes(activity))throw new AccountError(400,'在线状态无效');
 await game.db.transaction(async db=>{
  await game.session(db,owner,auth,now);
  const [old]=await db.execute('SELECT user_id FROM account_presence WHERE user_id=?',[owner]);
  // A close belongs to its reporting session, and a delayed earlier heartbeat
  // must not resurrect it. Keep the existing single row as an
  // offline marker; it carries no new personal or learning data.
  if(old.length)await db.execute("UPDATE account_presence SET token_hash=?,activity=?,last_seen=? WHERE user_id=? AND last_seen<=? AND (last_seen<? OR activity<>'offline' OR ?='offline') AND (?<>'offline' OR token_hash=?)",[auth,activity,now,owner,now,now,activity,activity,auth]);
  else await db.execute('INSERT INTO account_presence(user_id,token_hash,activity,last_seen) VALUES(?,?,?,?)',[owner,auth,activity,now]);
 });
 return {owner,...await presenceSnapshot(game,now)};
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
