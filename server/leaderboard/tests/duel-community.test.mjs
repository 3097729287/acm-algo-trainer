import test from 'node:test';
import assert from 'node:assert/strict';
import {randomUUID} from 'node:crypto';
import {startGameplayFixture} from './gameplay-fixture.mjs';
const start=Date.parse('2026-11-04T04:00:00Z');
async function client(f,name){
 const call=async(path,body,auth)=>{const r=await fetch(f.endpoint+path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json',...(auth?{'X-TB-User':auth.account.userId,Authorization:'Bearer '+auth.token}:{})},...(body===undefined?{}:{body:JSON.stringify(body)})});return {status:r.status,value:await r.json()};};
 await call('/v1/accounts/register',{loginId:name,nickname:name,password:'community-fixture-only'});const auth=(await call('/v1/accounts/login',{loginId:name,password:'community-fixture-only'})).value;
 return {id:auth.account.userId,send:(path,body)=>call(path,body,auth),post:(path,body)=>call(path,{requestId:randomUUID(),...body},auth)};
}
test('presence is authenticated, enum bounded, expires, and exposes only public activity',async()=>{
 const f=await startGameplayFixture({now:start});try{
  const a=await client(f,'present_a'),b=await client(f,'present_b');
  assert.equal((await a.send('/v1/presence',{activity:'problem',title:'private title'})).status,400);
  assert.equal((await a.send('/v1/presence',{activity:'private title'})).status,400);
  let result=await a.send('/v1/presence',{activity:'problem'});assert.equal(result.status,200);assert.equal(result.value.count,1);
  result=await b.send('/v1/presence',{activity:'replay'});assert.equal(result.value.count,2);assert.deepEqual(result.value.users.find(u=>u.userId===a.id),{userId:a.id,activity:'problem'});
  let board=(await b.send('/v1/leaderboard?period=total')).value;assert.equal(board.entries.find(u=>u.userId===a.id)?.activity,'problem');assert(!JSON.stringify(result.value).includes('token'));
  f.env.TEST_NOW=start+90001;result=await b.send('/v1/presence',{activity:'lecture'});assert.equal(result.value.count,1);assert.equal(result.value.users[0].activity,'lecture');
  await a.send('/v1/presence',{activity:'lab'});await a.send('/v1/accounts/logout',{});result=await b.send('/v1/presence',{activity:'lab'});assert.equal(result.value.count,1,'A revoked session is offline immediately');
 }finally{await f.close();}
});
test('ranked results commit points and public records once, with loser floor and no AC/XP changes',async()=>{
 const f=await startGameplayFixture({now:start});try{
  const a=await client(f,'ranked_a'),b=await client(f,'ranked_b'),observer=await client(f,'ranked_viewer');
  await a.post('/v1/duels/join',{handle:'Alpha'});const match=(await b.post('/v1/duels/join',{handle:'Beta'})).value.match;
  const stored=await f.STORE.gameplay.match(f.STORE.gameplay.db,match.id);stored.players.forEach(p=>p.rating=0);await f.STORE.gameplay.saveMatch(f.STORE.gameplay.db,stored);
  await f.STORE.gameplay.db.execute('UPDATE ranked_duel_ratings SET rating=0');
  f.STORE.gameplay.verify=async handle=>handle==='Alpha'?[{id:101,problem:{contestId:match.problem.contestId,index:match.problem.index},author:{members:[{handle}]},creationTimeSeconds:(match.startedAt+10000)/1000,verdict:'OK'}]:[];
  f.env.TEST_NOW=match.deadline+6000;
  const results=await Promise.all([a.send('/v1/duels/poll',{}),b.send('/v1/duels/poll',{}),a.send('/v1/duels/poll',{})]);assert(results.every(r=>r.status===200));
  const board=(await observer.send('/v1/duels/board?mode=ranked')).value;assert.equal(board.records.length,1);assert.equal(board.records[0].winner,a.id);assert.equal(board.entries.find(u=>u.userId===a.id).rating,20);assert.equal(board.entries.find(u=>u.userId===b.id).rating,0);
  assert.equal(board.records[0].players.find(u=>u.userId===a.id).change,20);assert(!('text' in board.records[0].players[0]));assert.equal(await f.countEvents(),0);
  await a.send('/v1/duels/poll',{});assert.equal((await observer.send('/v1/duels/board?mode=ranked')).value.records.length,1);
  const [counts]=await f.STORE.gameplay.db.execute('SELECT games FROM ranked_duel_ratings');assert(counts.every(r=>r.games===1));
  f.env.TEST_NOW=Date.parse('2026-11-04T16:00:01Z');const next=(await observer.send('/v1/duels/board?mode=ranked')).value;assert.equal(next.records.length,0);assert.equal(next.entries.length,2,'Ranked points persist across the Beijing day boundary');
 }finally{await f.close();}
});
