import test from 'node:test';
import assert from 'node:assert/strict';
import {randomUUID} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {startFixture as sqliteFixture} from './local-server.mjs';
import {startMySQLFixture} from './mysql-fixture.mjs';
import {preservedData,assertPreserved} from '../scripts/audit-preserved-data.mjs';
import {levelBox,rollRarity} from '../src/sticker-rewards.mjs';

async function migrate(fixture){
 const before=await preservedData(fixture.STORE.pool);
 for(const name of ['015_gameplay.sql','016_social_replies.sql']){
  const source=await readFile(new URL('../mysql/'+name,import.meta.url),'utf8');
  for(let repeat=0;repeat<2;repeat++)for(const statement of source.split(';').map(x=>x.trim()).filter(Boolean))await fixture.STORE.pool.query(statement);
 }
 assertPreserved(before,await preservedData(fixture.STORE.pool),{requireAvatar:true,requireChunks:true,requireLists:true,requireAdmin:true});
}
async function startFixture(options){
 if(process.env.TB_GAMEPLAY_MYSQL!=='1')return sqliteFixture(options);
 const fixture=await startMySQLFixture(options);
 try{await migrate(fixture);return fixture;}catch(error){await fixture.close();throw error;}
}

const now=Date.parse('2026-11-02T04:00:00Z');
async function client(f,name){
 const call=async(path,body,auth,method)=>{const response=await fetch(f.endpoint+path,{method:method||(body===undefined?'GET':'POST'),headers:{'Content-Type':'application/json',...(auth?{'X-TB-User':auth.account.userId,Authorization:'Bearer '+auth.token}:{})},...(body===undefined?{}:{body:JSON.stringify(body)})});return {status:response.status,value:await response.json()};};
 const password='sticker-fixture-only';assert.equal((await call('/v1/accounts/register',{loginId:name,nickname:name,password})).status,201);
 const signed=(await call('/v1/accounts/login',{loginId:name,password})).value;
 return {id:signed.account.userId,send:(path,body)=>call(path,body,signed),level:level=>call('/v1/profile',{publicProgress:{level,tier:'黑铁',rankTier:null,rankScore:null,titles:[]}},signed,'PUT')};
}
const post=(user,path,body)=>user.send(path,{requestId:randomUUID(),...body});
const inventory=async user=>(await user.send('/v1/stickers')).value;
const daily=async user=>{assert.equal((await post(user,'/v1/stickers/grant',{day:'2026-11-02',taskId:'ac-chain:0',xp:15})).status,200);return (await inventory(user)).units[0];};

test('box quantity, exact odds and progressive rarity are fixed for all 96 earned levels',async()=>{
 const shared=await readFile(new URL('../../../backend/resources/sticker-rewards.json',import.meta.url),'utf8');
 assert.equal(shared,await readFile(new URL('../src/sticker-rewards.json',import.meta.url),'utf8'));
 let previous=null;
 for(let level=5;level<=100;level++){
  const box=levelBox(level),p=box.probabilities;assert.equal(Object.values(p).reduce((a,b)=>a+b),10000);assert(Object.values(p).every(value=>Number.isSafeInteger(value)&&value>=0));
  if(previous){assert(box.quantity>=previous.quantity);assert(p.common<=previous.probabilities.common);assert(p.legendary>=previous.probabilities.legendary);assert(p.epic+p.legendary>=previous.probabilities.epic+previous.probabilities.legendary);}
  previous=box;
 }
 for(const level of [5,10,20,50,100]){const box=levelBox(level),counts={common:0,rare:0,epic:0,legendary:0};for(let roll=0;roll<10000;roll++)counts[rollRarity(box.probabilities,roll)]++;assert.deepEqual(counts,box.probabilities);}
 assert.equal(levelBox(5).quantity,2);assert.equal(levelBox(10).quantity,3);assert.equal(levelBox(100).quantity,8);
});

test('level entitlement backfills once, rejects inflated levels and opens the earned-level box only once',async()=>{
 const f=await startFixture({now});try{
  const a=await client(f,'box_account');await a.level(13);
  assert.equal((await post(a,'/v1/stickers/levels',{level:50})).status,409);assert.equal(Object.keys((await inventory(a)).boxes||{}).length,0);
  const grant={requestId:randomUUID(),level:13};const grants=await Promise.all(Array.from({length:12},()=>a.send('/v1/stickers/levels',grant)));assert(grants.every(item=>item.status===200));
  let state=await inventory(a);assert.equal(Object.keys(state.boxes).length,9);assert.equal(state.units.length,0);
  await a.level(50);assert.equal((await post(a,'/v1/stickers/levels',{level:50})).status,200);
  const opening={requestId:randomUUID(),boxId:'level:5'};const opened=await Promise.all(Array.from({length:12},()=>a.send('/v1/stickers/open-box',opening)));assert(opened.every(item=>item.status===200));
  state=await inventory(a);assert.equal(state.units.length,2);assert.equal(state.boxes['level:5'].drops.length,2);assert.deepEqual(state.boxes['level:5'].probabilities,levelBox(5).probabilities);
  assert.equal((await post(a,'/v1/stickers/open-box',{boxId:'level:5'})).value.opening.drops.length,2);assert.equal((await inventory(a)).units.length,2);
  assert.equal((await a.send('/v1/stickers/open-box',{...opening,boxId:'level:10'})).status,409);
  assert.equal((await post(a,'/v1/stickers/open-box',{boxId:'constructor'})).status,404);
 }finally{await f.close();}
});

test('a fixed achievement gives its exact exclusive sticker once despite retries and snapshot rollback',async()=>{
 const f=await startFixture({now});try{
  const a=await client(f,'achievement_sticker');
  const grants=await Promise.all(Array.from({length:12},()=>post(a,'/v1/stickers/achievement',{achievementId:'leader-tease'})));assert(grants.every(item=>item.status===200));
  const state=await inventory(a);assert.equal(state.units.length,1);assert.equal(state.units[0].stickerId,'achievement-duck');assert.equal(state.catalogue.find(item=>item.id==='achievement-duck').rarity,'legendary');
  assert.equal((await post(a,'/v1/stickers/achievement',{achievementId:'constructor'})).status,400);
  assert.equal((await post(a,'/v1/stickers/achievement',{achievementId:'unknown'})).status,400);
 }finally{await f.close();}
});

test('a reply and sticker transfer are atomic, persistent, private and idempotent',async()=>{
 const f=await startFixture({now});try{
  const a=await client(f,'reply_alpha'),b=await client(f,'reply_beta'),c=await client(f,'reply_other');
  const original=await post(a,'/v1/social/comments',{targetId:b.id,text:'一起加油'});assert.equal(original.status,200);
  const unit=await daily(b),request={requestId:randomUUID(),targetId:a.id,text:'收到，送你一张贴纸',replyTo:original.value.id,gift:{unitId:unit.id,revision:unit.revision}};
  const answers=await Promise.all(Array.from({length:5},()=>b.send('/v1/social/comments',request)));assert(answers.every(item=>item.status===200));
  assert(answers.every(item=>item.value.gift.unitId===unit.id));assert.equal(new Set(answers.map(item=>item.value.createdAt)).size,1);
  assert.equal((await inventory(b)).units.length,0);assert.equal((await inventory(a)).units.length,1);
  const theirs=(await b.send('/v1/social')).value.notifications.find(item=>item.id===original.value.id);assert.equal(theirs.myReplies.length,1);assert.equal(theirs.myReplies[0].text,request.text);assert.equal(theirs.myReplies[0].gift.unitId,unit.id);
  const received=(await a.send('/v1/social')).value;assert.equal(received.notifications[0].gift.unitId,unit.id);assert.equal(received.notifications[0].replyTo,original.value.id);assert.equal(received.activity.length,0);
  assert.equal((await c.send('/v1/social')).value.notifications.length,0);
  assert.equal((await b.send('/v1/social/comments',{...request,gift:{...request.gift,revision:99}})).status,409);
  assert.equal((await post(c,'/v1/social/comments',{targetId:a.id,text:'fake reply',replyTo:original.value.id})).status,400);
  assert.equal((await post(b,'/v1/stickers/place',{unitId:unit.id,revision:1,x:.3,y:.3,angle:0})).status,404);
  assert.equal((await inventory(b)).giftStats.sent,1);assert.equal((await inventory(a)).giftStats.received,1);
 }finally{await f.close();}
});

test('MySQL metadata migration preserves old accounts, comment bodies and idempotent plain-message retries',{skip:process.env.TB_GAMEPLAY_MYSQL!=='1'},async()=>{
 const f=await startMySQLFixture({now});try{
  const a=await client(f,'legacy_sender'),b=await client(f,'legacy_receiver');
  const request={requestId:randomUUID(),targetId:b.id,text:'existing private message'};
  assert.equal((await a.send('/v1/social/comments',request)).status,200);
  const old=(await b.send('/v1/social')).value.notifications[0];
  await migrate(f);
  assert.equal((await a.send('/v1/social/comments',request)).status,200);
  assert.equal((await b.send('/v1/social')).value.notifications[0].text,old.text);
  assert.equal((await post(b,'/v1/social/comments',{targetId:a.id,text:'reply after migration',replyTo:old.id})).status,200);
  assert.equal((await b.send('/v1/social')).value.notifications[0].myReplies[0].text,'reply after migration');
 }finally{await f.close();}
});

test('a stale or placed gift cannot post the message or remove the sticker',async()=>{
 const f=await startFixture({now});try{
  const a=await client(f,'gift_alpha'),b=await client(f,'gift_beta'),unit=await daily(a);
  const send=gift=>post(a,'/v1/social/comments',{targetId:b.id,text:'给你贴纸',gift});
  assert.equal((await send({unitId:unit.id,revision:99})).status,409);assert.equal((await b.send('/v1/social')).value.notifications.length,0);
  assert.equal((await post(a,'/v1/stickers/place',{unitId:unit.id,revision:0,x:.5,y:.5,angle:0})).status,200);
  assert.equal((await send({unitId:unit.id,revision:1})).status,409);assert.equal((await inventory(a)).units[0].placement.x,.5);
  assert.equal((await b.send('/v1/social')).value.notifications.length,0);
 }finally{await f.close();}
});
