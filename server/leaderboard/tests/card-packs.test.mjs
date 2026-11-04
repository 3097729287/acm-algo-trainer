import test from 'node:test';
import assert from 'node:assert/strict';
import {randomUUID} from 'node:crypto';
import {startGameplayFixture as startFixture} from './gameplay-fixture.mjs';
import {REWARDS,packBox,levelBox,dailyPackRarity,rollRarity,choosePackSticker} from '../src/sticker-rewards.mjs';
import {STICKERS} from '../src/gameplay.mjs';

const now=Date.parse('2026-11-04T04:00:00Z');
async function client(f,name){
 const call=async(path,body,auth,method)=>{
  const response=await fetch(f.endpoint+path,{method:method||(body===undefined?'GET':'POST'),headers:{'Content-Type':'application/json',...(auth?{'X-TB-User':auth.account.userId,Authorization:'Bearer '+auth.token}:{})},...(body===undefined?{}:{body:JSON.stringify(body)})});
  return {status:response.status,value:await response.json()};
 };
 await call('/v1/accounts/register',{loginId:name,nickname:name,password:'pack-fixture-only'});
 const auth=(await call('/v1/accounts/login',{loginId:name,password:'pack-fixture-only'})).value;
 return {id:auth.account.userId,send:(path,body)=>call(path,body,auth),level:level=>call('/v1/profile',{publicProgress:{level,tier:'黑铁',rankTier:null,rankScore:null,titles:[]}},auth,'PUT')};
}
const post=(user,path,body)=>user.send(path,{requestId:randomUUID(),...body});
const inventory=async user=>(await user.send('/v1/stickers')).value;

test('within an already rolled rarity, every collectible appears before duplicates and achievement exclusives stay exclusive',()=>{
 const seen=new Set();
 for(const rarity of ['common','rare','epic','legendary']){
  const pool=STICKERS.filter(item=>item.rarity===rarity&&!item.id.startsWith('achievement-'));
  for(let i=0;i<pool.length;i++){
   const sticker=choosePackSticker(STICKERS,rarity,seen,n=>n-1);
   assert(!seen.has(sticker.id));assert.equal(sticker.rarity,rarity);seen.add(sticker.id);
  }
  assert(pool.some(item=>item.id===choosePackSticker(STICKERS,rarity,seen,()=>0).id));
 }
 assert(![...seen].some(id=>id.startsWith('achievement-')));
});
test('pack quantities, exact roll weights and higher rarity outcomes are defined for all four packs',()=>{
 for(const [rarity,quantity] of Object.entries({common:3,rare:4,epic:5,legendary:6})){
  const box=packBox('fixture',rarity,{kind:'fixture'});assert.equal(box.quantity,quantity);
  const counts={common:0,rare:0,epic:0,legendary:0};for(let roll=0;roll<10000;roll++)counts[rollRarity(box.probabilities,roll)]++;
  assert.deepEqual(counts,box.probabilities);assert(counts.legendary>0);assert.equal(rollRarity(box.probabilities,9999),'legendary');
  assert.equal(box.guarantee,rarity==='common'?null:rarity);
 }
 const early=['rare','epic','rare','epic','rare','epic','rare','epic','rare','legendary','rare','epic','rare','rare','legendary','rare','epic','rare','rare','legendary'];
 for(let level=1;level<=100;level++){const box=levelBox(level),rarity=level<=20?early[level-1]:level%2?'epic':'legendary';assert.equal(box.rarity,rarity);assert.equal(box.quantity,REWARDS.cardPacks[rarity].quantity);}
 assert.equal(REWARDS.dailyPacks.maxPerDay,3);assert.equal(REWARDS.dailyPacks.probabilities.legendary,10);
});
test('daily claims create unopened packs, cap all requests at three per owner/day and remain retry safe',async()=>{
 const f=await startFixture({now});try{
  const a=await client(f,'pack_daily_a'),b=await client(f,'pack_daily_b');
  const grant={requestId:randomUUID(),day:'2026-11-04',taskId:'challenge-one',xp:60,rewardSlot:'fixed'};
  const repeated=await Promise.all(Array.from({length:8},()=>a.send('/v1/stickers/grant',grant)));assert(repeated.every(value=>value.status===200));
  for(const [slot,taskId] of [['review-0','review-random:0'],['review-1','review-random:1']])assert.equal((await post(a,'/v1/stickers/grant',{day:grant.day,taskId,xp:30,rewardSlot:slot})).status,200);
  let state=await inventory(a);assert.equal(state.units.length,0);assert.equal(Object.keys(state.boxes).length,3);
  assert.equal(state.boxes['task:'+grant.day+':'+grant.taskId].rarity,dailyPackRarity(a.id,grant.day,grant.taskId));
  assert.equal((await post(a,'/v1/stickers/grant',{day:grant.day,taskId:'without-slot-bypass',xp:100})).status,409);
  assert.equal((await post(a,'/v1/stickers/grant',{...grant,requestId:randomUUID(),taskId:'other-fixed'})).status,409);
  assert.equal((await post(b,'/v1/stickers/grant',{day:grant.day,taskId:'challenge-one',xp:60,rewardSlot:'fixed'})).status,200);
  assert.equal((await inventory(b)).units.length,0);
  assert.equal((await post(a,'/v1/stickers/grant',{day:'2026-11-03',taskId:'challenge-one',xp:60,rewardSlot:'fixed'})).status,200);
  state=await inventory(a);assert.equal(Object.keys(state.boxes).length,4);assert.equal(state.units.length,0);
 }finally{await f.close();}
});
test('five packs open atomically, keep every guarantee and a lost-response retry never draws again',async()=>{
 const f=await startFixture({now});try{
  const a=await client(f,'pack_batch_a'),b=await client(f,'pack_batch_b');await a.level(24);await post(a,'/v1/stickers/levels',{level:24});
  const request={requestId:randomUUID(),rarity:'legendary',count:5};
  const responses=await Promise.all(Array.from({length:8},()=>a.send('/v1/stickers/open-packs',request)));
  assert(responses.every(value=>value.status===200));assert(responses.every(value=>value.value.opening.drops.length===30));
  const opening=responses[0].value.opening;assert.equal(opening.packs.length,5);
  for(const box of opening.packs){assert.equal(box.drops.length,6);assert(box.drops.some(drop=>drop.rarity==='legendary'));}
  for(const value of responses)assert.deepEqual(value.value.opening,opening);
  const state=await inventory(a);assert.equal(state.units.length,30);assert.equal(new Set(state.units.map(unit=>unit.id)).size,30);
  assert.equal((await a.send('/v1/stickers/open-packs',{...request,count:1})).status,409);
  assert.equal((await post(a,'/v1/stickers/open-packs',{rarity:'legendary',count:5})).status,409);
  assert.equal((await post(b,'/v1/stickers/open-packs',{rarity:'legendary',count:1})).status,409);
  assert.equal((await inventory(a)).units.length,30);
  assert.equal((await post(a,'/v1/stickers/open-box',{boxId:opening.packs[0].id})).value.opening.drops.length,6);
  assert.equal((await inventory(a)).units.length,30);
 }finally{await f.close();}
});
test('all pack qualities enforce their floor and insufficient inventory leaves packs unopened',async()=>{
 const f=await startFixture({now});try{
  const a=await client(f,'pack_quality_a');await a.level(10);await post(a,'/v1/stickers/levels',{level:10});
  const [rows]=await f.STORE.gameplay.db.execute('SELECT payload FROM gameplay_accounts WHERE user_id=?',[a.id]);const saved=JSON.parse(rows[0].payload);
  for(const rarity of ['common','rare','epic']){const box=packBox('fixture:'+rarity,rarity,{kind:'fixture'});saved.boxes[box.id]=box;}
  await f.STORE.gameplay.saveAccount(f.STORE.gameplay.db,a.id,saved);
  const tiers=['common','rare','epic','legendary'];
  for(const rarity of tiers){const result=await post(a,'/v1/stickers/open-packs',{rarity,count:1});assert.equal(result.status,200);const box=result.value.opening.packs[0];assert.equal(box.drops.length,REWARDS.cardPacks[rarity].quantity);if(rarity!=='common')assert(box.drops.some(drop=>tiers.indexOf(drop.rarity)>=tiers.indexOf(rarity)));}
  const before=await inventory(a);assert.equal((await post(a,'/v1/stickers/open-packs',{rarity:'epic',count:5})).status,409);assert.deepEqual(await inventory(a),before);
 }finally{await f.close();}
});
