import test from 'node:test';
import assert from 'node:assert/strict';
import {randomUUID} from 'node:crypto';
import {startGameplayFixture} from './gameplay-fixture.mjs';
import {STICKERS} from '../src/gameplay.mjs';
import {backgroundWeights,resolveScene} from '../src/sticker-scenes.mjs';
import {normalizeBackgroundState} from '../src/sticker-catalogue.mjs';

const now=Date.parse('2026-11-04T12:00:00Z');
async function client(f,name){
 let auth;
 const send=async(path,body,method)=>{const response=await fetch(f.endpoint+path,{method:method||(body===undefined?'GET':'POST'),headers:{'Content-Type':'application/json',...(auth?{'X-TB-User':auth.account.userId,Authorization:'Bearer '+auth.token}:{})},...(body===undefined?{}:{body:JSON.stringify(body)})});return {status:response.status,value:await response.json()};};
 await send('/v1/accounts/register',{loginId:name,nickname:name,password:'scene-fixture-only'});
 auth=(await send('/v1/accounts/login',{loginId:name,password:'scene-fixture-only'})).value;
 return {id:auth.account.userId,send,post:(path,body)=>send(path,{requestId:randomUUID(),...body}),read:async()=>(await send('/v1/stickers')).value};
}
async function seed(f,user,stickers){
 const db=f.STORE.gameplay.db;
 await db.execute("INSERT INTO gameplay_accounts(user_id,payload) VALUES(?,?)",[user.id,JSON.stringify({revision:0,grants:{},units:stickers.map((id,i)=>({id:randomUUID(),stickerId:id,revision:0,placement:{x:.2+i*.08,y:.6,angle:0,scale:1}}))})]);return user.read();
}
const evidence=(changes={})=>({version:1,contestKey:'replay:'+'a'.repeat(64),replayId:'contest-'+'b'.repeat(32),duration:120,originalDuration:120,startedAt:now-7200000,finishedAt:now,difficulty:1800,total:5,accepted:[0,1].map(i=>({problemKey:'p:'+String(i).repeat(64),submissionId:'official-'+i,submittedAt:now-4000000+i*1000,scope:'official',verdict:'AC'})),...changes});

test('backgrounds never enter ordinary packs; both contest difficulty and additional ACs improve their rarity weights',()=>{
 assert.equal(STICKERS.filter(s=>s.kind==='background').length,14);
 assert.equal(new Set(STICKERS.filter(s=>s.kind==='background').map(item=>item.theme)).size,14);
 assert(backgroundWeights(2200,2).legendary>backgroundWeights(1000,2).legendary);
 assert(backgroundWeights(1800,6).legendary>backgroundWeights(1800,2).legendary);
 assert.equal(resolveScene({items:[{stickerId:'x',unitId:'old'},{stickerId:'x',unitId:'other'}]},[{id:'new',stickerId:'x'}]).missing.length,1);
});
test('historic background rarity aliases preserve every owned unit, placement, discovery and preset',()=>{
 const original={revision:12,units:['common','rare','epic','legendary'].map((rarity,index)=>({id:'unit-'+index,stickerId:'background-night-'+rarity,revision:index,placement:index===1?{x:.5,y:.5,angle:0,scale:1}:null})),discoveredStickers:['background-night-common','background-night-legendary'],scenePresets:[{id:'preset-one',items:[{unitId:'unit-1',stickerId:'background-night-rare',placement:{x:.5,y:.5,angle:0,scale:1}}]}]};
 const before=structuredClone(original),migrated=normalizeBackgroundState(original);
 assert.deepEqual(original,before);assert.equal(migrated.units.length,4);
 assert.deepEqual(migrated.units.map(unit=>unit.id),before.units.map(unit=>unit.id));
 assert(migrated.units.every(unit=>unit.stickerId==='background-night-common'));
 assert.deepEqual(migrated.units[1].placement,before.units[1].placement);
 assert.deepEqual(migrated.discoveredStickers,['background-night-common']);
 assert.equal(resolveScene(migrated.scenePresets[0],migrated.units).missing.length,0);
 assert.deepEqual(normalizeBackgroundState(migrated),migrated);
});
test('background draw is a single, durable card per owner/original contest despite response loss, concurrent retries and repeated replays',async()=>{
 const f=await startGameplayFixture({now});try{
  const a=await client(f,'scene_reward_a'),b=await client(f,'scene_reward_b'),body={requestId:randomUUID(),evidence:evidence()};
  const results=await Promise.all(Array.from({length:5},()=>a.send('/v1/stickers/replay-background',body)));assert(results.every(r=>r.status===200));
  assert.equal(new Set(results.map(r=>r.value.backgroundReward.id)).size,1);let state=await a.read();assert.equal(state.units.length,0);assert.equal(Object.keys(state.boxes).length,0);assert.equal(Object.keys(state.backgroundRewards).length,1);const reward=Object.values(state.backgroundRewards)[0];assert.equal(reward.openedAt,null);
  const retry=await a.post('/v1/stickers/replay-background',{evidence:evidence({replayId:'contest-'+'c'.repeat(32)})});assert.equal(retry.status,200);assert.equal((await a.read()).units.length,0);
  assert.equal((await b.post('/v1/stickers/replay-background',{evidence:evidence()})).status,200);assert.equal((await b.read()).units.length,0);
  assert.equal((await b.post('/v1/stickers/open-background',{rewardId:reward.id})).status,404);
  const open={requestId:randomUUID(),rewardId:reward.id},opened=await Promise.all(Array.from({length:5},()=>a.send('/v1/stickers/open-background',open)));assert(opened.every(r=>r.status===200));assert.equal(new Set(opened.map(r=>r.value.opening.drops[0].id)).size,1);assert.equal(opened[0].value.opening.drops.length,1);assert.equal(opened[0].value.opening.kind,'background');assert.equal((await a.read()).units.length,1);assert.equal((await a.post('/v1/stickers/open-background',{rewardId:reward.id})).value.opening.drops[0].id,opened[0].value.opening.drops[0].id);
  for(const change of [{duration:60},{accepted:[evidence().accepted[0]]},{finishedAt:now-4000000},{accepted:evidence().accepted.map(a=>({...a,verdict:'SAMPLE_PASS'}))},{accepted:[evidence().accepted[0],evidence().accepted[0]]}])assert.equal((await a.post('/v1/stickers/replay-background',{evidence:evidence(change)})).status,400);
  assert.equal((await a.read()).units.length,1);
 }finally{await f.close();}
});
test('scene save/switch, individual clothing and shape-specific scale are transactional and owner bound',async()=>{
 const f=await startGameplayFixture({now});try{
  const a=await client(f,'scene_layout_a'),b=await client(f,'scene_layout_b');let state=await seed(f,a,['scene-person','scene-tree','epic-butterfly','background-night-rare','background-room-epic']);
  const [person,tree,butterfly,bg1,bg2]=state.units;
  assert.equal((await a.post('/v1/stickers/outfit',{unitId:tree.id,revision:0,appearance:{hat:'cap'}})).status,400);
  const clothing=await a.post('/v1/stickers/outfit',{unitId:person.id,revision:0,appearance:{hat:'cap',accessory:'bag',top:'rose',trousers:'skirt',shoes:'white'}});assert.equal(clothing.status,200);state=clothing.value.inventory;
  assert.equal((await a.post('/v1/stickers/place',{unitId:tree.id,revision:0,x:.6,y:.6,angle:0,scale:5})).status,200);
  assert.equal((await a.post('/v1/stickers/place',{unitId:butterfly.id,revision:0,x:.4,y:.4,angle:0,scale:5})).status,400);
  state=(await a.post('/v1/stickers/place',{unitId:bg1.id,revision:0,x:.5,y:.5,angle:0,scale:1})).value.inventory;
  assert.equal(state.units.filter(u=>u.placement&&u.stickerId.startsWith('background-')).length,1);
  const request={requestId:randomUUID(),inventoryRevision:state.revision,name:'我的小屋'};
  const saves=await Promise.all([a.send('/v1/stickers/scene-save',request),a.send('/v1/stickers/scene-save',request)]);assert(saves.every(r=>r.status===200));state=await a.read();assert.equal(state.scenePresets.length,1);const preset=state.scenePresets[0];
  assert.equal((await b.post('/v1/stickers/scene-apply',{presetId:preset.id,inventoryRevision:0})).status,404);
  const changed=await a.post('/v1/stickers/place',{unitId:bg2.id,revision:1,x:.5,y:.5,angle:0,scale:1});assert.equal(changed.status,200);state=changed.value.inventory;
  const applied=await a.post('/v1/stickers/scene-apply',{presetId:preset.id,inventoryRevision:state.revision});assert.equal(applied.status,200);state=applied.value.inventory;
  assert.equal(state.units.find(u=>u.id===bg1.id).placement.scale,1);assert.equal(state.units.find(u=>u.id===bg2.id).placement,null);assert.equal(state.units.find(u=>u.id===person.id).appearance.hat,'cap');
  const stale=await a.post('/v1/stickers/scene-delete',{presetId:preset.id,inventoryRevision:0});assert.equal(stale.status,409);assert.equal((await a.read()).scenePresets.length,1);
 }finally{await f.close();}
});
test('gifting warns before a preset loses an irreplaceable unit, preserves the preset and restores it after receiving the same card again',async()=>{
 const f=await startGameplayFixture({now});try{
  const a=await client(f,'scene_gift_a'),b=await client(f,'scene_gift_b');let state=await seed(f,a,['scene-tree']),unit=state.units[0];
  let answer=await a.post('/v1/stickers/scene-save',{name:'树下',inventoryRevision:state.revision});state=answer.value.inventory;const preset=state.scenePresets[0];
  answer=await a.post('/v1/stickers/recycle',{unitId:unit.id,revision:unit.revision});state=answer.value.inventory;unit=state.units[0];
  const message={targetId:b.id,text:'送你一棵树',gift:{unitId:unit.id,revision:unit.revision}};
  assert.equal((await a.post('/v1/social/comments',message)).status,409);assert.equal((await a.read()).units.length,1);
  const request={requestId:randomUUID(),...message,gift:{...message.gift,presetRevision:state.revision}};
  const results=await Promise.all([a.send('/v1/social/comments',request),a.send('/v1/social/comments',request)]);assert(results.every(r=>r.status===200));state=await a.read();assert.equal(state.units.length,0);assert.equal(state.scenePresets.length,1);
  answer=await a.post('/v1/stickers/scene-apply',{presetId:preset.id,inventoryRevision:state.revision});assert.equal(answer.status,200);assert.deepEqual(answer.value.scene.missing,['scene-tree']);
  const received=(await b.read()).units[0];assert.equal((await b.post('/v1/social/comments',{targetId:a.id,text:'还给你',gift:{unitId:received.id,revision:received.revision}})).status,200);
  state=await a.read();answer=await a.post('/v1/stickers/scene-apply',{presetId:preset.id,inventoryRevision:state.revision});assert.equal(answer.value.scene.missing.length,0);assert(answer.value.inventory.units[0].placement);
 }finally{await f.close();}
});
