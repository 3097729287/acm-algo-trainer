import test from 'node:test';
import assert from 'node:assert/strict';
import {randomUUID} from 'node:crypto';
import {startFixture as sqliteFixture} from './local-server.mjs';
import {startMySQLFixture} from './mysql-fixture.mjs';
import {readFile} from 'node:fs/promises';
import {preservedData,assertPreserved} from '../scripts/audit-preserved-data.mjs';

async function startFixture(options){
 if(process.env.TB_GAMEPLAY_MYSQL!=='1')return sqliteFixture(options);
 const fixture=await startMySQLFixture(options);
 try{
  const before=await preservedData(fixture.STORE.pool);
  const source=await readFile(new URL('../mysql/015_gameplay.sql',import.meta.url),'utf8');
  for(let repeat=0;repeat<2;repeat++)for(const statement of source.split(';').map(x=>x.trim()).filter(Boolean))await fixture.STORE.pool.query(statement);
  assertPreserved(before,await preservedData(fixture.STORE.pool),{requireAvatar:true,requireChunks:true,requireLists:true,requireAdmin:true});
  return fixture;
 }catch(error){await fixture.close();throw error;}
}

const start=Date.parse('2026-11-02T01:00:00Z');
async function client(f,name){
 const send=async(path,body,auth)=>{
  const response=await fetch(f.endpoint+path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json',...(auth?{'X-TB-User':auth.account.userId,Authorization:'Bearer '+auth.token}:{})},...(body===undefined?{}:{body:JSON.stringify(body)})});
  return {status:response.status,value:await response.json()};
 };
 const password='isolated-fixture-password';
 assert.equal((await send('/v1/accounts/register',{loginId:name,nickname:name,password})).status,201);
 const signed=await send('/v1/accounts/login',{loginId:name,password});assert.equal(signed.status,200);
 return {auth:signed.value,send:(path,body)=>send(path,body,signed.value)};
}
const post=(client,path,value)=>client.send(path,{requestId:randomUUID(),...value});
const grant=(a,extra={})=>post(a,'/v1/stickers/grant',{day:'2026-11-02',taskId:'ac-chain:0',xp:15,...extra});

test('account inventory: concurrent duplicate awards, CAS placement, response loss, recycle and ownership',async()=>{
 const f=await startFixture({now:start});
 try{
  const a=await client(f,'stickers_a'),b=await client(f,'stickers_b');
  const claims=await Promise.all(Array.from({length:12},()=>grant(a)));
  assert(claims.every(x=>x.status===200));
  let state=(await a.send('/v1/stickers')).value;assert.equal(state.units.length,1);assert.equal(Object.keys(state.grants).length,1);
  assert.equal((await b.send('/v1/stickers')).value.units.length,0);
  const unit=state.units[0],operation={requestId:randomUUID(),unitId:unit.id,revision:0,x:.2,y:.7,angle:30};
  assert.equal((await a.send('/v1/stickers/place',operation)).status,200);
  assert.equal((await a.send('/v1/stickers/place',operation)).status,200,'retry after lost response');
  assert.equal((await a.send('/v1/stickers/place',{...operation,x:.9})).status,409,'request ID cannot change meaning');
  assert.equal((await post(b,'/v1/stickers/recycle',{unitId:unit.id,revision:1})).status,404);
  const races=await Promise.all([post(a,'/v1/stickers/place',{unitId:unit.id,revision:1,x:.8,y:.3,angle:0}),post(a,'/v1/stickers/recycle',{unitId:unit.id,revision:1})]);
  assert.deepEqual(races.map(x=>x.status).sort(),[200,409]);
  state=(await a.send('/v1/stickers')).value;assert.equal(state.units.length,1);assert.equal(state.units[0].revision,2);
  if(state.units[0].placement)assert.equal((await post(a,'/v1/stickers/recycle',{unitId:unit.id,revision:2})).status,200);
  state=(await a.send('/v1/stickers')).value;assert.equal(state.units.length,1);assert.equal(state.units[0].placement,null);
  // Replaying a claim after restoring an old private learning snapshot cannot mint inventory.
  await grant(a);assert.equal((await a.send('/v1/stickers')).value.units.length,1);
  for(const [xp,expected] of [[30,'rare'],[60,'epic'],[100,'legendary']]){await grant(a,{taskId:'ac-chain:'+xp,xp});state=(await a.send('/v1/stickers')).value;assert.equal(state.grants['2026-11-02:ac-chain:'+xp].rarity,expected);}
  const login=await fetch(f.endpoint+'/v1/accounts/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({loginId:'stickers_a',password:'isolated-fixture-password'})});assert.equal(login.status,200);
  assert.equal((await grant(a,{taskId:'ac-chain:999'})).status,401,'revoked device cannot award');
 }finally{await f.close();}
});

test('two independent HTTP clients: immediate shared start, duplicate join, cancelled ticket and real-provider verifier',async()=>{
 const f=await startFixture({now:start});
 try{
  const a=await client(f,'duel_alpha'),b=await client(f,'duel_beta');
  const join={requestId:randomUUID(),handle:'Alpha'};
  const first=await a.send('/v1/duels/join',join);assert.equal(first.value.status,'queued');
  assert.equal((await a.send('/v1/duels/join',join)).value.ticket,first.value.ticket);
  const matched=await post(b,'/v1/duels/join',{handle:'Beta'});assert.equal(matched.value.status,'active');
  const room=matched.value.match,other=(await a.send('/v1/duels')).value.match;
  assert.equal(other.id,room.id);assert.equal(other.startedAt,room.startedAt);assert.deepEqual(other.problem,room.problem);
  assert(room.problem.difficulty>=800&&room.problem.difficulty<=1500);
  const cancelled=await post(a,'/v1/duels/cancel',{ticket:first.value.ticket});assert.equal(cancelled.value.match.id,room.id,'cancel racing with match returns the authoritative match');
  f.env.TEST_NOW=start+25000;
  const disconnected=(await a.send('/v1/duels')).value;assert(disconnected.match.players.every(p=>!p.online));assert.equal(disconnected.match.id,room.id);
  f.STORE.gameplay.verify=async handle=>[
   {id:1,problem:{contestId:room.problem.contestId,index:room.problem.index},creationTimeSeconds:(start-1000)/1000,verdict:'OK',author:{members:[{handle}]}},
   {id:2,problem:{contestId:room.problem.contestId,index:room.problem.index},creationTimeSeconds:(start+21000)/1000,verdict:handle==='Alpha'?'OK':'WRONG_ANSWER',author:{members:[{handle}]}},
   {id:3,problem:{contestId:room.problem.contestId,index:room.problem.index},creationTimeSeconds:(start+22000)/1000,verdict:'OK',author:{members:[{handle:'Unrelated'}]}},
  ];
  const polled=await a.send('/v1/duels/poll',{});assert.equal(polled.status,200);
  assert.equal(polled.value.match.players[0].acceptedAt,start+21000);assert.equal(polled.value.match.players[1].acceptedAt,null);
  f.env.TEST_NOW=start+31000;
  f.STORE.gameplay.verify=async handle=>[{id:handle==='Alpha'?2:4,problem:{contestId:room.problem.contestId,index:room.problem.index},creationTimeSeconds:(start+(handle==='Alpha'?21000:30000))/1000,verdict:'OK',author:{members:[{handle}]}}];
  const finished=await b.send('/v1/duels/poll',{});assert.equal(finished.value.status,'finished');assert.equal(finished.value.match.winner,a.auth.account.userId);
  assert.deepEqual((await a.send('/v1/duels')).value.match,finished.value.match);
  const count=f.STORE.database?f.STORE.database.prepare('SELECT COUNT(*) n FROM duel_matches').get().n:(await f.STORE.pool.query('SELECT COUNT(*) n FROM duel_matches'))[0][0].n;
  assert.equal(Number(count),1);
 }finally{await f.close();}
});

test('stale cancellation, queue expiry and settlement during provider outage are recoverable',async()=>{
 const f=await startFixture({now:start});
 try{
  const a=await client(f,'reconnect_a'),b=await client(f,'reconnect_b');
  const first=await post(a,'/v1/duels/join',{handle:'Alpha'});
  await post(a,'/v1/duels/cancel',{ticket:first.value.ticket});
  const second=await post(a,'/v1/duels/join',{handle:'Alpha'});
  const stale=await post(a,'/v1/duels/cancel',{ticket:first.value.ticket});assert.equal(stale.value.ticket,second.value.ticket);
  f.env.TEST_NOW=start+31000;
  const expired=await post(b,'/v1/duels/join',{handle:'Beta'});assert.equal(expired.value.status,'queued');
  const newMatch=await post(a,'/v1/duels/join',{handle:'Alpha'});assert.equal(newMatch.value.status,'active');
  f.env.TEST_NOW=newMatch.value.match.deadline+1000;
  f.STORE.gameplay.verify=async()=>{throw Error('fixture provider outage');};
  const pending=await a.send('/v1/duels/poll',{});assert.equal(pending.value.status,'active');assert(pending.value.match.players.every(p=>p.syncError));
  f.env.TEST_NOW+=6000;f.STORE.gameplay.verify=async()=>[];
  const settled=await b.send('/v1/duels/poll',{});assert.equal(settled.value.status,'finished');assert.equal(settled.value.match.winner,null);
 }finally{await f.close();}
});

test('a submission made before the deadline stays pending while the original judge is testing',async()=>{
 const f=await startFixture({now:start});
 try{
  const a=await client(f,'judging_a'),b=await client(f,'judging_b');
  await post(a,'/v1/duels/join',{handle:'Alpha'});
  const joined=await post(b,'/v1/duels/join',{handle:'Beta'}),room=joined.value.match;
  f.env.TEST_NOW=room.deadline+6000;
  const receipt={id:701,problem:{contestId:room.problem.contestId,index:room.problem.index},creationTimeSeconds:(room.deadline-1000)/1000,author:{members:[{handle:'Alpha'}]}};
  f.STORE.gameplay.verify=async handle=>handle==='Alpha'?[{...receipt,verdict:'TESTING'}]:[];
  const pending=await a.send('/v1/duels/poll',{});
  assert.equal(pending.value.status,'active');assert.equal(pending.value.match.players[0].judging,true);
  f.env.TEST_NOW+=6000;
  f.STORE.gameplay.verify=async handle=>handle==='Alpha'?[{...receipt,verdict:'OK'}]:[];
  const finished=await b.send('/v1/duels/poll',{});
  assert.equal(finished.value.status,'finished');assert.equal(finished.value.match.winner,a.auth.account.userId);
  assert.equal(finished.value.match.players[0].acceptedAt,room.deadline-1000);
 }finally{await f.close();}
});
