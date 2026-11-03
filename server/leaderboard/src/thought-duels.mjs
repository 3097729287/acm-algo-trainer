import {createHash,randomInt,randomUUID} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {AccountError} from './accounts.mjs';
import {blankVerdict,validateVerdict} from './pk-judge.mjs';
import {duelPoints} from './duel-points.mjs';

const catalogue=JSON.parse(readFileSync(new URL('./thought-problems.json',import.meta.url),'utf8')).problems;
const uuid=/^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i;
export class PkError extends AccountError{constructor(status,code,message){super(status,message);this.code=code;}}
const fail=(status,code,message)=>{throw new PkError(status,'PK_'+code,message);};
const text=value=>{if(typeof value!=='string'||[...value].length>2000||/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/u.test(value))fail(400,'ANSWER_INVALID','作答须为不超过 2000 字的文本');return value.replaceAll('\r\n','\n');};
const tolerance=(joined,now)=>Math.min(500,50+Math.floor(Math.max(0,now-joined)/15000)*50);
const event=(room,type,at,extra={})=>room.events.push({id:room.events.length+1,type:'pk:'+type,at,...extra});
const hash=value=>createHash('sha256').update(JSON.stringify(Object.keys(value).sort().map(key=>[key,value[key]]))).digest('hex');

export class ThoughtDuels{
 constructor(db,dialect='mysql',{problems=catalogue,judge=null,enabled=false,now=()=>Date.now(),log=entry=>process.stderr.write(JSON.stringify(entry)+'\n')}={}){
  this.db=db;this.dialect=dialect;this.problems=problems;this.judge=judge;this.enabled=enabled;this.now=now;this.log=log;this.running=new Map();this.maintenance=null;this.closed=false;
 }
 configure({enabled=false,judge=null,now=this.now}={}){this.enabled=enabled;this.judge=judge;this.now=now;}
 get ready(){return this.enabled&&!!this.judge&&this.problems.length>0;}
 async available(){try{for(const table of ['pk_lobby','pk_ratings','pk_queue','pk_matches','pk_members','pk_records','pk_operations'])await this.db.execute(`SELECT 1 FROM ${table} LIMIT 0`);return true;}catch(e){if(e.code==='ER_NO_SUCH_TABLE'||/no such table/i.test(e.message))return false;throw e;}}
 async transaction(action){return this.db.transaction(async db=>{await db.execute('SELECT singleton FROM pk_lobby WHERE singleton=1'+(this.dialect==='mysql'?' FOR UPDATE':''));return action(db);});}
 async session(db,owner,auth,now){
  await db.execute('SELECT user_id FROM accounts WHERE user_id=?'+(this.dialect==='mysql'?' FOR UPDATE':''),[owner]);
  const [rows]=await db.execute('SELECT s.token_hash FROM account_sessions s JOIN accounts a ON a.user_id=s.user_id WHERE s.user_id=? AND s.token_hash=? AND s.expires_at>? AND s.password_version=a.password_version',[owner,auth,Math.floor(now/1000)]);
  if(!rows.length)fail(401,'SESSION_EXPIRED','登录已失效，请重新登录');
 }
 async room(db,id){if(!id)return null;const [rows]=await db.execute('SELECT payload FROM pk_matches WHERE match_id=?',[id]);return rows.length?JSON.parse(rows[0].payload):null;}
 async member(db,owner){const [rows]=await db.execute('SELECT match_id FROM pk_members WHERE user_id=?',[owner]);return rows[0]?.match_id;}
 async save(db,room,now){const due=room.status==='countdown'?room.startedAt:room.status==='active'?room.deadline:room.status==='judging'?(room.judgeLeaseUntil||now):now;await db.execute('UPDATE pk_matches SET status=?,updated_at=?,due_at=?,payload=? WHERE match_id=?',[room.status,now,due,JSON.stringify(room),room.id]);}
 async rating(db,owner){const [rows]=await db.execute('SELECT rating FROM pk_ratings WHERE user_id=?',[owner]);return rows[0]?.rating??1000;}
 viewRoom(owner,room,now){
  if(!room)return null;
  return {id:room.id,status:room.status,startedAt:room.startedAt,deadline:room.deadline,finishedAt:room.finishedAt??null,problem:room.status==='countdown'?null:{id:room.problem.id,title:room.problem.title,url:room.problem.url,difficulty:room.problem.difficulty,markdown:room.problem.displayMarkdown||room.problem.markdown,originalMarkdown:room.problem.markdown,limits:room.problem.limits},
   players:room.players.map(p=>({owner:p.owner,nickname:p.nickname,avatarHash:p.avatarHash,rating:p.rating,online:now-p.lastSeen<25000,submittedAt:p.submittedAt,revision:p.owner===owner?p.revision:undefined,...(p.owner===owner||room.status==='finished'?{text:p.text}:{})})),events:room.events,
   ...(room.status==='finished'?{verdict:room.verdict,winner:room.winner,ratingChanges:room.ratingChanges,judgeFailed:room.judgeFailed}:{}),owner};
 }
 async view(db,owner,now){
  const [queued]=await db.execute('SELECT * FROM pk_queue WHERE user_id=?',[owner]);const q=queued[0],room=await this.room(db,await this.member(db,owner));
  return {owner,serverNow:now,enabled:this.ready,capabilities:{thoughtMode:1,maxLength:2000,durationSeconds:900},rating:await this.rating(db,owner),status:room?.status||(q?'queued':'idle'),ticket:q?.ticket??null,queuedAt:q?.joined_at??null,range:q?{min:q.min_difficulty,max:q.max_difficulty}:null,tolerance:q?tolerance(q.joined_at,now):50,match:this.viewRoom(owner,room,now)};
 }
 async read(owner,now,{advance=true}={}){
  if(!await this.available())return {owner,serverNow:now,enabled:false,status:'idle',rating:1000,match:null,capabilities:{thoughtMode:1,maxLength:2000,durationSeconds:900}};
  if(advance)await this.maintain(now);return this.transaction(db=>this.view(db,owner,now));
 }
 async pair(db,now){
  await db.execute('DELETE FROM pk_queue WHERE last_seen<?',[now-25000]);
  if(!this.ready)return;
  const [queue]=await db.execute('SELECT * FROM pk_queue ORDER BY joined_at,user_id');
  const used=new Set();
  for(let i=0;i<queue.length;i++){
   const a=queue[i];if(used.has(a.user_id))continue;
   const candidates=queue.slice(i+1).filter(b=>!used.has(b.user_id)&&a.min_difficulty===b.min_difficulty&&a.max_difficulty===b.max_difficulty&&Math.abs(a.rating-b.rating)<=Math.max(tolerance(a.joined_at,now),tolerance(b.joined_at,now)));
   candidates.sort((x,y)=>Math.abs(x.rating-a.rating)-Math.abs(y.rating-a.rating)||x.joined_at-y.joined_at);
   const b=candidates[0];if(!b)continue;
   const pool=this.problems.filter(p=>p.difficulty>=a.min_difficulty&&p.difficulty<=a.max_difficulty);if(!pool.length)continue;
   const players=[];
   for(const q of [a,b]){const [users]=await db.execute('SELECT u.nickname,a.hash AS avatar_hash FROM users u LEFT JOIN account_public_avatars a ON a.user_id=u.user_id WHERE u.user_id=?',[q.user_id]);players.push({owner:q.user_id,nickname:users[0]?.nickname||'—',avatarHash:users[0]?.avatar_hash||null,rating:q.rating,lastSeen:q.last_seen,text:'',revision:0,submittedAt:null});}
   const room={id:randomUUID(),status:'countdown',startedAt:now+3000,deadline:now+3000+900000,problem:pool[randomInt(pool.length)],players,events:[],judgeAttempts:0};event(room,'match_success',now,{startsAt:room.startedAt});
   await db.execute('INSERT INTO pk_matches(match_id,status,updated_at,due_at,payload) VALUES(?,?,?,?,?)',[room.id,room.status,now,room.startedAt,JSON.stringify(room)]);
   for(const q of [a,b]){used.add(q.user_id);await db.execute('DELETE FROM pk_queue WHERE user_id=?',[q.user_id]);await db.execute('INSERT INTO pk_members(user_id,match_id) VALUES(?,?)',[q.user_id,room.id]);}
  }
 }
 async settle(db,room,verdict,now,judgeFailed=false){
  if(room.status==='finished')return;
  room.status='finished';room.finishedAt=now;room.verdict=verdict;room.judgeFailed=judgeFailed;room.winner=verdict.winner==='draw'?null:room.players[verdict.winner==='A'?0:1].owner;
  const [a,b]=room.players;
  const [aChange,bChange]=duelPoints(a.rating,b.rating,judgeFailed?'draw':verdict.winner);
  room.ratingChanges={[a.owner]:aChange,[b.owner]:bChange};
  for(const p of room.players)await db.execute('UPDATE pk_ratings SET rating=rating+? WHERE user_id=?',[room.ratingChanges[p.owner],p.owner]);
  event(room,'game_over',now);delete room.judgeToken;delete room.judgeLeaseUntil;
  await this.save(db,room,now);
  await db.execute('INSERT INTO pk_records(match_id,player_a,player_b,finished_at,payload) VALUES(?,?,?,?,?)',[room.id,a.owner,b.owner,now,JSON.stringify(room)]);
 }
 async advance(db,room,now){
  if(room.status==='countdown'&&now>=room.startedAt){room.status='active';event(room,'game_start',room.startedAt);await this.save(db,room,now);}
  if(room.status==='active'&&(now>=room.deadline||room.players.every(p=>p.submittedAt!==null))){
   for(const p of room.players)if(p.submittedAt===null){p.submittedAt=room.deadline;event(room,'opponent_submitted',room.deadline,{owner:p.owner,automatic:true});}
   room.status='judging';event(room,'judging',now);await this.save(db,room,now);
   if(room.players.every(p=>!p.text.trim()))await this.settle(db,room,blankVerdict(),now);
  }
 }
 async maintain(now=this.now()){
  if(this.closed)return;if(this.maintenance)return this.maintenance;
  const work=this.transaction(async db=>{
   await this.pair(db,now);
   const [rows]=await db.execute("SELECT payload FROM pk_matches WHERE status IN ('countdown','active','judging') AND due_at<=? ORDER BY due_at LIMIT 100",[now]);const jobs=[];
   for(const row of rows){const room=JSON.parse(row.payload);await this.advance(db,room,now);if(room.status==='judging'&&(!room.judgeLeaseUntil||room.judgeLeaseUntil<=now))jobs.push(room.id);}
   return jobs;
  });this.maintenance=work;
  try{const jobs=await work;for(const id of jobs)this.launch(id);}finally{if(this.maintenance===work)this.maintenance=null;}
 }
 launch(id){
  if(this.closed||this.running.has(id)||this.running.size>=2)return;
  const work=this.runJudge(id).catch(()=>{this.log({event:'pk:judge_error',matchId:id,code:'PK_JUDGE_INTERNAL'});}).finally(()=>this.running.delete(id));this.running.set(id,work);
 }
 async runJudge(id){
  for(;;){
   const now=this.now(),claim=await this.transaction(async db=>{
    const room=await this.room(db,id);if(!room||room.status!=='judging'||room.judgeLeaseUntil>now)return null;
    if(room.judgeAttempts>=4||!this.judge){await this.settle(db,room,{...blankVerdict(),reason:'AI 裁判暂不可用，本局平局，积分不变'},now,true);return null;}
    room.judgeToken=randomUUID();room.judgeLeaseUntil=now+60000;room.judgeAttempts++;await this.save(db,room,now);return room;
   });if(!claim)return;
   let verdict=null;
   try{verdict=validateVerdict(await this.judge(claim.problem,claim.players.map(p=>p.text)),claim.players.map(p=>p.text));}catch{this.log({event:'pk:judge_retry',matchId:id,attempt:claim.judgeAttempts,code:'PK_JUDGE_INVALID'});}
   const retry=await this.transaction(async db=>{
    const current=await this.room(db,id);if(!current||current.status!=='judging'||current.judgeToken!==claim.judgeToken)return false;
    if(verdict){await this.settle(db,current,verdict,this.now());return false;}
    delete current.judgeToken;delete current.judgeLeaseUntil;await this.save(db,current,this.now());return true;
   });if(!retry)return;
  }
 }
 async write(owner,auth,kind,value,now){
  if(!await this.available())fail(503,'UNAVAILABLE','思维对决服务尚未启用');
  if(kind==='join'&&!this.ready)fail(503,'DISABLED','思维对决服务尚未启用');
  await this.maintain(now);
  const result=await this.transaction(async db=>{
   await this.session(db,owner,auth,now);
   const fields={join:['requestId','minDifficulty','maxDifficulty'],cancel:['requestId','ticket'],poll:[],draft:['requestId','matchId','text','revision'],submit:['requestId','matchId','text','revision'],dismiss:['requestId','matchId']}[kind];
   if(!fields||!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).some(key=>!fields.includes(key)))fail(400,'REQUEST_INVALID','思维对决请求无效');
   if(kind!=='poll'){
    if(!uuid.test(value.requestId||''))fail(400,'REQUEST_INVALID','请求编号无效');
    const digest=hash({kind,...value});const [old]=await db.execute('SELECT request_hash FROM pk_operations WHERE user_id=? AND request_id=?',[owner,value.requestId]);
    if(old.length){if(old[0].request_hash!==digest)fail(409,'REQUEST_REUSED','请求编号已用于其他操作');return this.view(db,owner,now);}
   }
   let room=await this.room(db,await this.member(db,owner));
   if(kind==='join'){
    if(room)fail(409,'ROOM_EXISTS','请先返回匹配');
    const [old]=await db.execute('SELECT ticket FROM pk_queue WHERE user_id=?',[owner]);
    if(!old.length){
     const lo=value.minDifficulty??800,hi=value.maxDifficulty??1500;
     if(!Number.isInteger(lo)||!Number.isInteger(hi)||lo<800||hi>3500||lo>hi||lo%100||hi%100||!this.problems.some(p=>p.difficulty>=lo&&p.difficulty<=hi))fail(400,'RANGE_INVALID','该分数段暂无可用题目');
     const [count]=await db.execute('SELECT COUNT(*) AS n FROM pk_queue');if(count[0].n>=2000)fail(503,'QUEUE_FULL','匹配人数较多，请稍后重试');
     const insert=this.dialect==='mysql'?'INSERT IGNORE':'INSERT OR IGNORE';await db.execute(`${insert} INTO pk_ratings(user_id,rating) VALUES(?,1000)`,[owner]);
     await db.execute('INSERT INTO pk_queue(user_id,ticket,rating,joined_at,last_seen,min_difficulty,max_difficulty) VALUES(?,?,?,?,?,?,?)',[owner,randomUUID(),await this.rating(db,owner),now,now,lo,hi]);
    }await this.pair(db,now);
   }else if(kind==='cancel'){
    if(!uuid.test(value.ticket||''))fail(400,'TICKET_INVALID','匹配编号无效');
    await db.execute('DELETE FROM pk_queue WHERE user_id=? AND ticket=?',[owner,value.ticket]);
   }else if(kind==='poll'){
    await db.execute('UPDATE pk_queue SET last_seen=? WHERE user_id=?',[now,owner]);await this.pair(db,now);
    if(room){room.players.find(p=>p.owner===owner).lastSeen=now;await this.advance(db,room,now);await this.save(db,room,now);}
   }else{
    if(!room||room.id!==value.matchId||!room.players.some(p=>p.owner===owner))fail(409,'ROOM_CHANGED','对局已变化，请刷新');
    if(kind==='dismiss'){
     if(room.status!=='finished')fail(409,'ROOM_ACTIVE','本局尚未结束');await db.execute('DELETE FROM pk_members WHERE user_id=? AND match_id=?',[owner,room.id]);
    }else{
     await this.advance(db,room,now);const p=room.players.find(p=>p.owner===owner);
     if(room.status!=='active'||now>=room.deadline||p.submittedAt!==null)fail(409,'ANSWER_LOCKED','答卷已锁定');
     if(!Number.isInteger(value.revision)||value.revision!==p.revision)fail(409,'DRAFT_CHANGED','答卷已在其他窗口更新，请刷新');
     p.text=text(value.text);p.revision++;p.lastSeen=now;
     if(kind==='submit'){p.submittedAt=now;event(room,'opponent_submitted',now,{owner});}
     await this.advance(db,room,now);await this.save(db,room,now);
    }
   }
   if(kind!=='poll')await db.execute('INSERT INTO pk_operations(user_id,request_id,request_hash) VALUES(?,?,?)',[owner,value.requestId,hash({kind,...value})]);
   return this.view(db,owner,now);
  });
  if(result.status==='judging')this.launch(result.match.id);return result;
 }
 async history(owner,now,id=null){
  if(!await this.available())return {owner,records:[]};
  if(id&&!uuid.test(id))fail(400,'ROOM_INVALID','对局编号无效');
  const [rows]=await this.db.execute('SELECT payload FROM pk_records WHERE (player_a=? OR player_b=?)'+(id?' AND match_id=?':' ORDER BY finished_at DESC LIMIT 20'),id?[owner,owner,id]:[owner,owner]);
  if(id&&!rows.length)fail(404,'RECORD_NOT_FOUND','没有找到这场对局');
  return id?{owner,match:this.viewRoom(owner,JSON.parse(rows[0].payload),now)}:{owner,records:rows.map(row=>{const room=JSON.parse(row.payload);return {id:room.id,problem:room.problem.title,finishedAt:room.finishedAt,winner:room.winner,judgeFailed:room.judgeFailed,ratingChange:room.ratingChanges[owner],players:room.players.map(p=>({owner:p.owner,nickname:p.nickname}))};})};
 }
 start(){if(this.timer)return;this.timer=setInterval(()=>{if(!this.closed)this.available().then(ok=>ok&&this.maintain()).catch(()=>this.log({event:'pk:maintenance_error',code:'PK_MAINTENANCE'}));},1000);this.timer.unref();}
 async close(){this.closed=true;clearInterval(this.timer);await this.maintenance?.catch(()=>{});await Promise.allSettled([...this.running.values()]);}
}
