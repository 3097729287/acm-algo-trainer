// Real production HTTP adapter, SQLite persistence and receive-order barriers.
// No TEST_NOW is used for ordering; all traffic stays on disposable loopback.
import test from 'node:test';
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {mkdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {randomUUID} from 'node:crypto';
import {startFixture} from './local-server.mjs';
import {ACTIVITIES} from '../src/duel-community.mjs';

async function harness(options){
 const fixture=await startFixture(options),gates=new Map();
 const proxy=createServer(async(req,res)=>{
  try{
   const buffers=[];for await(const part of req)buffers.push(part);const body=Buffer.concat(buffers),gate=gates.get(req.headers['x-fixture-hold']);
   if(gate){gate.arrived();await gate.wait;}
   const headers={...req.headers};delete headers.host;delete headers.connection;delete headers['x-fixture-hold'];
   const reply=await fetch(fixture.endpoint+req.url,{method:req.method,headers,...(body.length?{body}:{})});
   res.writeHead(reply.status,{'content-type':'application/json'});res.end(await reply.text());
  }catch{res.writeHead(500);res.end('{}');}
 });
 await new Promise(resolve=>proxy.listen(0,'127.0.0.1',resolve));
 const endpoint='http://127.0.0.1:'+proxy.address().port;
 function hold(name){let arrived,release;const gate={arrival:new Promise(resolve=>arrived=resolve),wait:new Promise(resolve=>release=resolve)};gate.arrived=arrived;gate.release=release;gates.set(name,gate);return gate;}
 async function call(path,body,auth,gate){
  const encoded=body===undefined?undefined:JSON.stringify(body);
  if(path==='/v1/presence')assert(Buffer.byteLength(encoded)<=256);
  const reply=await fetch(endpoint+path,{method:body===undefined?'GET':'POST',headers:{'content-type':'application/json',...(auth?{'X-TB-User':auth.account.userId,Authorization:'Bearer '+auth.token}:{}),...(gate?{'X-Fixture-Hold':gate}:{})},...(encoded?{body:encoded}:{})});
  return {status:reply.status,value:await reply.json()};
 }
 async function account(name='lease_owner'){
  assert.equal((await call('/v1/accounts/register',{loginId:name,nickname:name,password:'presence-fixture-only'})).status,201);
  const auth=(await call('/v1/accounts/login',{loginId:name,password:'presence-fixture-only'})).value;
  return client(auth);
 }
 function client(auth){
  const send=(body,gate)=>call('/v1/presence',body,auth,gate);
  return {auth,id:auth.account.userId,send,async prepare(){const reply=await send({activity:'problem',presencePhase:'prepare'});assert.equal(reply.status,200);assert.equal(reply.value.presenceState,'prepared');return {presenceLease:reply.value.presenceLease,presenceExpected:reply.value.presenceExpected};},
   phase:(ticket,presencePhase,activity='problem',gate)=>send({...ticket,presencePhase,activity},gate),
   board:()=>call('/v1/leaderboard?period=total',undefined,auth)};
 }
 return {...fixture,hold,account,client,async login(name){return client((await call('/v1/accounts/login',{loginId:name,password:'presence-fixture-only'})).value);},async row(owner){return (await fixture.STORE.gameplay.db.execute('SELECT activity,last_seen FROM account_presence WHERE user_id=?',[owner]))[0][0];},async close(){proxy.closeIdleConnections();await new Promise(resolve=>proxy.close(resolve));await fixture.close();}};
}
function publicOnly(reply,ticket){const value=JSON.stringify(reply);assert(!value.includes('~'));assert(!value.includes('presenceLease'));assert(!value.includes(ticket.presenceLease.slice(0,11)));assert(!value.includes('token_hash'));}

test('same token: real late close and beat cannot overwrite the newly activated instance',async()=>{
 const f=await harness();try{
  const a=await f.account(),old=await a.prepare();await a.phase(old,'activate');
  const close=f.hold('old-close'),beat=f.hold('old-beat');
  const lateClose=a.phase(old,'close','offline','old-close'),lateBeat=a.phase(old,'beat','problem','old-beat');
  await Promise.all([close.arrival,beat.arrival]);
  const current=await a.prepare();assert.equal((await a.phase(current,'activate','lecture')).value.presenceState,'active');const before=await f.row(a.id);
  close.release();assert.equal((await lateClose).value.presenceState,'superseded');
  beat.release();const reply=await lateBeat;assert.equal(reply.value.presenceState,'superseded');
  assert.deepEqual(await f.row(a.id),before);assert(reply.value.users.some(row=>row.userId===a.id&&row.activity==='lecture'));publicOnly(reply.value,current);
 }finally{await f.close();}
});

test('close before delayed activation creates a persistent offline tombstone, including replayed activate/close',async()=>{
 const f=await harness();try{
  const a=await f.account(),ticket=await a.prepare(),gate=f.hold('activate');
  const delayed=a.phase(ticket,'activate','problem','activate');await gate.arrival;
  assert.equal((await a.phase(ticket,'close','offline')).value.presenceState,'closed');const before=await f.row(a.id);assert(before.activity.startsWith('offline~'));
  gate.release();assert.equal((await delayed).value.presenceState,'superseded');
  assert.equal((await a.phase(ticket,'activate')).value.presenceState,'superseded');
  await new Promise(resolve=>setTimeout(resolve,15));await a.phase(ticket,'close','offline');
  assert.deepEqual(await f.row(a.id),before,'Repeated close neither revives nor extends the tombstone');
  const next=await a.prepare();assert.equal((await a.phase(next,'activate')).value.presenceState,'active');
  assert.equal((await a.phase(ticket,'close','offline')).value.presenceState,'superseded');
 }finally{await f.close();}
});

test('two prepares and actual late activation are fenced; recovery never steals another active lease',async()=>{
 const f=await harness();try{
  const a=await f.account(),first=await a.prepare(),second=await a.prepare(),gate=f.hold('first-activate');
  const delayed=a.phase(first,'activate','problem','first-activate');await gate.arrival;
  await a.phase(second,'activate','lab');gate.release();assert.equal((await delayed).value.presenceState,'superseded');
  const denied=await a.phase(first,'recover');assert.equal(denied.value.presenceState,'superseded');assert(!denied.value.presenceLease);
  await a.phase(second,'close','offline');
  const recovered=await a.phase(first,'recover');assert.equal(recovered.value.presenceState,'prepared');
  const next={presenceLease:recovered.value.presenceLease,presenceExpected:recovered.value.presenceExpected};
  assert.equal((await a.phase(next,'activate','wiki')).value.presenceState,'active');
  assert.equal((await a.phase(first,'activate')).value.presenceState,'superseded');
 }finally{await f.close();}
});

test('active/idle/closed public contracts never expose packed values or lease credentials',async()=>{
 const f=await harness();try{
  const a=await f.account(),b=await f.account('lease_observer');await b.send({activity:'lecture'});
  assert(ACTIVITIES.every(activity=>activity.length<=8));
  const ticket=await a.prepare();let result=await a.phase(ticket,'activate','rankings');assert.equal((await f.row(a.id)).activity.length,20);
  assert.equal(result.value.count,2);publicOnly(result.value,ticket);
  result=await a.phase(ticket,'beat','idle');assert.equal(result.value.count,1);assert.deepEqual(result.value.idleUsers,[{userId:a.id,activity:'idle'}]);publicOnly(result.value,ticket);
  let row=(await b.board()).value.entries.find(row=>row.userId===a.id);assert.equal(row.online,false);assert.equal(row.idle,true);assert.equal(row.activity,'idle');publicOnly((await b.board()).value,ticket);
  result=await a.phase(ticket,'close','offline');assert.equal(result.value.count,1);assert.deepEqual(result.value.idleUsers,[]);
  row=(await b.board()).value.entries.find(row=>row.userId===a.id);assert.equal(row.online,false);assert.equal(row.idle,false);assert.equal(row.activity,null);
  assert.equal((await a.phase(ticket,'beat','problem')).value.presenceState,'superseded');
 }finally{await f.close();}
});

test('legacy clients retain plain rows and recover only after a packed lease/tombstone expires',async()=>{
 const f=await harness();try{
  const a=await f.account();await a.send({activity:'problem'});assert.equal((await f.row(a.id)).activity,'problem');
  const ticket=await a.prepare();await a.phase(ticket,'activate','lab');const before=await f.row(a.id);
  for(const activity of ['problem','idle','offline'])await a.send({activity});
  assert.deepEqual(await f.row(a.id),before,'Legacy requests neither take over nor refresh an active lease');
  await a.phase(ticket,'close','offline');const closed=await f.row(a.id);await a.send({activity:'problem'});assert.deepEqual(await f.row(a.id),closed);
  // Persisted-age fixture only: request-order tests above use real Date.now.
  await f.STORE.gameplay.db.execute('UPDATE account_presence SET last_seen=? WHERE user_id=?',[Date.now()-90001,a.id]);
  const expired=await f.row(a.id);await a.send({activity:'offline'});assert.deepEqual(await f.row(a.id),expired,'An obsolete legacy close cannot extend the hold');
  await a.send({activity:'problem'});assert.equal((await f.row(a.id)).activity,'problem');
  assert.equal((await a.phase(ticket,'beat','idle')).value.presenceState,'superseded');
  const current=await a.prepare();await a.phase(current,'activate','lab');
  await f.STORE.gameplay.db.execute('UPDATE account_presence SET last_seen=? WHERE user_id=?',[Date.now()-90001,a.id]);
  await a.send({activity:'idle'});assert.equal((await f.row(a.id)).activity,'idle');
 }finally{await f.close();}
});

test('server-issued proof is owner/session bound, body bounded and no arbitrary client timestamp is accepted',async()=>{
 const f=await harness();try{
  const a=await f.account(),b=await f.account('other_lease_owner'),ticket=await a.prepare();
  assert.equal((await b.phase(ticket,'activate')).status,400);
  const forged={...ticket,presenceLease:ticket.presenceLease.slice(0,15)+(ticket.presenceLease[15]==='A'?'B':'A')+ticket.presenceLease.slice(16)};
  assert.equal((await a.phase(forged,'activate')).status,400);
  assert.equal((await a.send({...ticket,presencePhase:'activate',activity:'problem',clientNow:Date.now()+99999999})).status,400);
  assert.equal((await a.send({activity:'online',presencePhase:'close',...ticket})).status,400);
  assert.equal((await a.send({activity:'problem',presencePhase:'prepare',...ticket})).status,400);
  await a.phase(ticket,'activate');assert.equal((await a.phase(ticket,'beat','problem')).value.presenceState,'active');
 }finally{await f.close();}
});

test('lease and tombstone survive a real SQLite restart with the same existing auth token',async()=>{
 const folder=new URL('../../../.backups/presence-lease-20261110/',import.meta.url);await mkdir(folder,{recursive:true});
 const database=fileURLToPath(new URL('restart-'+randomUUID()+'.sqlite3',folder));
 let f=await harness({database}),auth,ticket,id;
 try{const a=await f.account();auth=a.auth;id=a.id;ticket=await a.prepare();await a.phase(ticket,'activate');await a.phase(ticket,'close','offline');}finally{await f.close();}
 f=await harness({database});try{
  const a=f.client(auth);assert((await f.row(id)).activity.startsWith('offline~'));
  assert.equal((await a.phase(ticket,'activate')).value.presenceState,'superseded');
  const next=await a.prepare();assert.equal((await a.phase(next,'activate','template')).value.presenceState,'active');
  assert.equal((await a.phase(ticket,'close','offline')).value.presenceState,'superseded');
 }finally{await f.close();}
});

test('same owner with a renewed auth token cannot replay the previous session ticket',async()=>{
 const f=await harness();try{
  const old=await f.account(),ticket=await old.prepare();await old.phase(ticket,'activate');
  const current=await f.login('lease_owner');assert.equal(current.id,old.id);
  assert.equal((await current.phase(ticket,'close','offline')).status,400);
  assert.equal((await old.phase(ticket,'beat','problem')).status,401);
  const next=await current.prepare();assert.equal((await current.phase(next,'activate','lab')).value.presenceState,'active');
 }finally{await f.close();}
});
