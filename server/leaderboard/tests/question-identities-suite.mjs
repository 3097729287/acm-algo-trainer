import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash,randomUUID} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {REVIEWED_QUESTION_PAIRS,questionIdentity,problemKeyIdentity} from '../src/question-identities.mjs';

const hash=s=>createHash('sha256').update(s).digest('hex');
const LG='luogu.com.cn/problem/P10865',CF='codeforces.com/gym/105139/problem/H';
const now=Date.parse('2026-11-09T07:00:00Z'),day='2026-11-09',old='2026-11-06T07:00:00Z';
async function user(f,name){
 let auth;
 const request=async(path,body)=>{
  const r=await fetch(f.endpoint+path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json',...(auth?{'X-TB-User':auth.account.userId,Authorization:'Bearer '+auth.token}:{})},...(body===undefined?{}:{body:JSON.stringify(body)})});
  const value=await r.json();assert(r.ok,`local HTTP ${path}: ${r.status}`);return value;
 };
 await request('/v1/accounts/register',{loginId:name,nickname:name,password:'identity-local-fixture'});
 auth=await request('/v1/accounts/login',{loginId:name,password:'identity-local-fixture'});
 return {id:auth.account.userId,request,post:async(path,body={})=>request(path,{requestId:randomUUID(),...body})};
}
const event=(identity,at,tag='')=>({eventId:hash(identity+'|'+at+'|'+tag),problemKey:hash(identity),acceptedAt:at,difficulty:1200,scope:'official'});
async function rows(db,sql,args=[]){return (await db.execute(sql,args))[0];}
async function raw(db){return rows(db,'SELECT user_id,problem_key,event_id,accepted_at,accepted_day,difficulty,received_at FROM official_ac_events ORDER BY user_id,problem_key');}
async function prepareTeams(f){
 if(f.STORE.pool){for(const file of ['019_team_training.sql','020_team_native_receipts.sql'])for(const sql of (await readFile(new URL('../mysql/'+file,import.meta.url),'utf8')).split(';').map(s=>s.trim()).filter(Boolean))await f.STORE.pool.query(sql);}
 assert(await f.STORE.teams.available());
}

export function questionIdentitiesSuite(startFixture){
 test('reviewed identities bind exactly the confirmed pair, never neighboring tasks or navigation URLs',()=>{
  assert.equal(REVIEWED_QUESTION_PAIRS.length,1);assert.equal(questionIdentity(CF),LG);assert.equal(questionIdentity(LG),LG);assert.equal(problemKeyIdentity(hash(CF)),hash(LG));
  for(const other of ['luogu.com.cn/problem/P10866','codeforces.com/gym/105139/problem/I','https://codeforces.com/gym/105139/problem/H','codeforces.com/contest/105139/problem/H']){
   assert.equal(questionIdentity(other),other);assert.equal(problemKeyIdentity(hash(other)),hash(other));
  }
 });
 test('real HTTP old and new alias receipts share one first AC across day/week boundaries while all original rows remain',async()=>{
  const f=await startFixture({now});try{
   const a=await user(f,'pair_forward'),b=await user(f,'pair_reverse'),db=f.STORE.dominance.database;
   await a.request('/v1/events',{events:[event(LG,old)]});const initial=await raw(db);
   await a.request('/v1/events',{events:[event(CF,'2026-11-09T06:00:00Z')]});
   for(const period of ['daily','weekly','total']){const board=await a.request('/v1/leaderboard?period='+period);assert.equal(board.self.count,period==='total'?1:0);}
   const stored=await raw(db);assert.equal(stored.length,2);assert.deepEqual(stored.find(r=>r.problem_key===hash(LG)),initial[0]);
   await b.request('/v1/events',{events:[event(CF,'2026-11-09T06:00:00Z','reverse')]});
   await b.request('/v1/events',{events:[event(LG,old,'reverse')]});
   assert.equal((await b.request('/v1/leaderboard?period=daily')).self.count,0);assert.equal((await b.request('/v1/leaderboard?period=total')).self.count,1);
   // A neighboring task remains a separate real first acceptance.
   await b.request('/v1/events',{events:[event('codeforces.com/gym/105139/problem/I','2026-11-09T06:01:00Z')]});
   assert.equal((await b.request('/v1/leaderboard?period=total')).self.count,2);
   await db.execute('INSERT INTO ranking_admins(user_id,granted_at) VALUES(?,?)',[b.id,new Date(now).toISOString()]);
   const deleted=await b.request('/v1/admin/leaderboard/delete',{userId:a.id,period:'daily',confirmation:'delete'});
   assert.equal(deleted.removed,0,'an old question mirrored today cannot turn daily deletion into an all-time deletion');
   assert.equal((await a.request('/v1/leaderboard?period=total')).self.count,1);
   const beforeExclusion=await raw(db);
   await db.execute('INSERT INTO ranking_exclusions(user_id,problem_key,deleted_at) VALUES(?,?,?)',[a.id,hash(CF),new Date(now).toISOString()]);
   assert.equal((await a.request('/v1/leaderboard?period=total')).self.count,0);assert.deepEqual(await raw(db),beforeExclusion);
  }finally{await f.close();}
 });
 test('legacy duplicate hashes cannot inflate new ranking XP or leadership and old awarded history stays byte-for-byte intact',async()=>{
  const f=await startFixture({now});try{
   const a=await user(f,'pair_legacy'),b=await user(f,'pair_new_two'),c=await user(f,'pair_new_mirror'),db=f.STORE.dominance.database;
   const insert=async(who,key,at,id)=>db.execute('INSERT INTO official_ac_events VALUES(?,?,?,?,?,?,?)',[who.id,hash(key),hash(id),at,at.slice(0,10),1200,'2026-11-09T07:00:00.000Z']);
   await insert(a,LG,'2026-11-06T07:00:00.000Z','old-lg');await insert(a,CF,'2026-11-09T06:00:00.000Z','old-cf');
   await insert(c,LG,'2026-11-09T05:00:00.000Z','legacy-tie-lg');await insert(c,CF,'2026-11-09T05:00:00.000Z','legacy-tie-cf');
   await b.request('/v1/events',{events:[event('unrelated-real-1','2026-11-09T06:01:00Z'),event('unrelated-real-2','2026-11-09T06:02:00Z')]});
   await db.execute("INSERT INTO ranking_cycles(period,start_date,end_date,settled_at) VALUES('daily','2026-11-06','2026-11-07',?)",['2026-11-07T01:00:00.000Z']);
   await db.execute("INSERT INTO ranking_rewards(user_id,period,start_date,end_date,position,xp,settled_at) VALUES(?,'daily','2026-11-06','2026-11-07',1,100,?)",[a.id,'2026-11-07T01:00:00.000Z']);
   const historical=await rows(db,"SELECT * FROM ranking_rewards WHERE start_date='2026-11-06'");const rawBefore=await raw(db);
   assert.equal((await c.request('/v1/leaderboard?period=daily')).self.count,1);assert.equal((await a.request('/v1/leaderboard?period=daily')).self.count,0);assert.equal((await b.request('/v1/leaderboard?period=daily')).self.rank,1);
   f.env.TEST_NOW=Date.parse('2026-11-10T00:01:00+08:00');await b.request('/v1/profile');
   assert.equal((await a.request('/v1/rewards')).totalXp,100,'old first XP is retained, mirror adds no new period XP');
   const newRewards=await rows(db,"SELECT user_id,position,xp FROM ranking_rewards WHERE period='daily' AND start_date=? ORDER BY position",[day]);
   assert.equal(newRewards[0].user_id,b.id);assert.equal(Number(newRewards[0].xp),100);assert(!newRewards.some(r=>r.user_id===a.id));
   const leaders=await rows(db,"SELECT user_id,score FROM ranking_leader_days WHERE period='daily' AND ranking_day=?",[day]);assert.equal(leaders[0].user_id,b.id);
   for(const period of ['weekly','total']){const leaders=await rows(db,'SELECT user_id,score FROM ranking_leader_days WHERE period=? AND ranking_day=?',[period,day]);assert.equal(leaders[0].user_id,b.id);assert.equal(Number(leaders[0].score),2);}
   assert.deepEqual(await rows(db,"SELECT * FROM ranking_rewards WHERE start_date='2026-11-06'"),historical);assert.deepEqual(await raw(db),rawBefore);
   const after=await rows(db,'SELECT * FROM ranking_rewards ORDER BY user_id,period,start_date');await b.request('/v1/profile');assert.deepEqual(await rows(db,'SELECT * FROM ranking_rewards ORDER BY user_id,period,start_date'),after);
  }finally{await f.close();}
 });
 test('team keeps all twelve original contest slots including H and counts only real room-window receipts despite the global earlier mirror',async()=>{
  const f=await startFixture({now});try{
   await prepareTeams(f);const [a,b,c]=await Promise.all(['pair_team_a','pair_team_b','pair_team_c'].map(name=>user(f,name))),teams=f.STORE.teams,db=f.STORE.dominance.database;
   const contest={id:'codeforces:gym:105139',title:'Isolated H identity window fixture',platform:'Codeforces',problems:'ABCDEFGHIJKL'.split('').map(letter=>({id:letter==='H'?'remote:codeforces:105139::H':'fixture-hubei::'+letter,letter,title:letter,url:`https://codeforces.com/gym/105139/problem/${letter}`,problemKey:hash(`codeforces.com/gym/105139/problem/${letter}`),available:true,problemType:'standard'}))};
   teams.catalogue={schema:1,revision:'isolated-identity',contests:[contest]};teams.contests=new Map([[contest.id,contest]]);
   await a.request('/v1/events',{events:[event(LG,old)]});
   let state=await a.post('/v1/team-training/create',{name:'Identity local team'});await b.post('/v1/team-training/join',{inviteCode:state.team.inviteCode});await c.post('/v1/team-training/join',{inviteCode:state.team.inviteCode});
   state=await a.request('/v1/team-training/state');state=await a.post('/v1/team-training/configure',{teamRevision:state.team.revision,contestId:contest.id,durationMinutes:5});
   for(const actor of [a,b,c])await actor.post('/v1/team-training/ready',{configurationRevision:state.team.configurationRevision,ready:true});
   state=await a.request('/v1/team-training/state');state=await a.post('/v1/team-training/start',{teamRevision:state.team.revision});
   const room=state.room,id='remote:codeforces:105139::H';assert.equal(room.problems.length,12);assert.equal(room.problems.find(p=>p.id===id).url,'https://codeforces.com/gym/105139/problem/H');assert.equal(room.score.totalScore,0);
   f.env.TEST_NOW=now+5000;
   await a.request('/v1/events',{events:[event(CF,new Date(now+4000).toISOString())]});
   state=await a.request('/v1/team-training/state');assert.equal(state.room.score.totalScore,1);assert.equal(state.room.score.solved[0].id,id);
   assert.equal((await a.request('/v1/leaderboard?period=daily')).self.count,0);assert.equal((await a.request('/v1/leaderboard?period=total')).self.count,1);
   assert.equal((await a.request('/v1/team-training/standings')).entries[0].totalScore,1);
   // A client already canonicalizing to LG must still match the original CF H slot.
   await b.request('/v1/events',{events:[event(LG,new Date(now+4001).toISOString(),'canonical')]});
   assert.equal((await a.request('/v1/team-training/state')).room.score.totalScore,1);
   // A verified later AC can exist only in native room receipts when global
   // first AC had been acknowledged earlier. That must continue to score H.
   const nativeRoom=room.id,receipt=hash('local-native-only');
   await db.execute('INSERT INTO team_native_receipts(receipt_key,room_id,problem_id,user_id,intent_id,verdict,accepted_at,verified_at,proof) VALUES(?,?,?,?,?,?,?,?,?)',[receipt,nativeRoom,id,c.id,randomUUID(),'AC',new Date(now+4500).toISOString(),now+5000,'{"source":"isolated-verified-receipt-row"}']);
   assert.equal((await a.request('/v1/team-training/state')).room.score.totalScore,1);assert.equal((await a.request('/v1/team-training/standings')).entries[0].totalScore,1);
  }finally{await f.close();}
 });
 test('new replay background evidence cannot use both mirror hashes as two different tasks; existing rewards are retained',async()=>{
  const f=await startFixture({now});try{
   const a=await user(f,'pair_background');
   const evidence={version:1,contestKey:'replay:'+hash('pair-evidence'),replayId:'contest-'+hash('pair-run').slice(0,32),duration:120,originalDuration:120,startedAt:now-7200000,finishedAt:now,difficulty:1800,total:12,accepted:[LG,CF].map((key,i)=>({problemKey:'p:'+hash(key),submissionId:'local-native-'+i,submittedAt:now-4000000+i*1000,scope:'official',verdict:'AC'}))};
   // Use fetch directly here because this authenticated rejection is expected.
   const signed=await a.request('/v1/accounts/login',{loginId:'pair_background',password:'identity-local-fixture'});
   const send=async(e,requestId=randomUUID())=>fetch(f.endpoint+'/v1/stickers/replay-background',{method:'POST',headers:{'Content-Type':'application/json','X-TB-User':signed.account.userId,Authorization:'Bearer '+signed.token},body:JSON.stringify({requestId,evidence:e})});
   assert.equal((await send(evidence)).status,400);
   for(const keys of [REVIEWED_QUESTION_PAIRS[0].sourceUrls,[LG,REVIEWED_QUESTION_PAIRS[0].sourceUrls[1]],[REVIEWED_QUESTION_PAIRS[0].sourceUrls[0],CF]]){
    const legacy=structuredClone(evidence);legacy.accepted.forEach((row,i)=>row.problemKey='p:'+hash(keys[i]));assert.equal((await send(legacy)).status,400);
   }
   const real=structuredClone(evidence);real.accepted[1].problemKey='p:'+hash('codeforces.com/gym/105139/problem/I');const response=await send(real);assert.equal(response.status,200);const reward=(await response.json()).backgroundReward;
   assert.equal((await send(real)).status,200);
   const r=await fetch(f.endpoint+'/v1/stickers',{headers:{'X-TB-User':signed.account.userId,Authorization:'Bearer '+signed.token}});const value=await r.json();assert(value.backgroundRewards[reward.id]);assert.equal(Object.keys(value.backgroundRewards).length,1);
   // An already granted historical reward remains readable and openable even
   // if its old evidence would no longer qualify for a new grant.
   const db=f.STORE.gameplay.db,[row]=await rows(db,'SELECT payload FROM gameplay_accounts WHERE user_id=?',[a.id]),state=JSON.parse(row.payload),legacyId=randomUUID(),legacyContest='replay:'+hash('legacy-mirror-reward');
   const historical={id:legacyId,contestKey:legacyContest,grantedAt:now-86400000,accepted:2,difficulty:1800,openedAt:null};
   state.backgroundRewards[legacyId]=historical;state.replayBackgroundGrants[legacyContest]={rewardId:legacyId};
   await db.execute('UPDATE gameplay_accounts SET payload=? WHERE user_id=?',[JSON.stringify(state),a.id]);
   const read=await fetch(f.endpoint+'/v1/stickers',{headers:{'X-TB-User':signed.account.userId,Authorization:'Bearer '+signed.token}});assert.deepEqual((await read.json()).backgroundRewards[legacyId],historical);
   const open=await fetch(f.endpoint+'/v1/stickers/open-background',{method:'POST',headers:{'Content-Type':'application/json','X-TB-User':signed.account.userId,Authorization:'Bearer '+signed.token},body:JSON.stringify({requestId:randomUUID(),rewardId:legacyId})});assert.equal(open.status,200);assert.equal((await open.json()).opening.drops.length,1);
  }finally{await f.close();}
 });
}
