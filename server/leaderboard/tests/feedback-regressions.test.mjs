import test from 'node:test';
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {startFixture} from './local-server.mjs';
import {originalAvatarPng} from './original-avatar-fixture.mjs';
import {readFile} from 'node:fs/promises';
import {originalAvatarProxy,ORIGINAL_AVATAR_PROXY} from '../scripts/prepare-avatar-proxy.mjs';
const now=Date.parse('2026-11-03T08:00:00Z');
test('the upload proxy changes only the exact profile route and preserves all other configuration',async()=>{
 const current=await readFile(new URL('../Caddyfile',import.meta.url),'utf8'),previous=current.replace(ORIGINAL_AVATAR_PROXY,'');
 assert.notEqual(previous,current);assert.equal(originalAvatarProxy(previous),current);assert.equal(originalAvatarProxy(current),current);
 assert.throws(()=>originalAvatarProxy(previous+previous));assert.throws(()=>originalAvatarProxy(previous.replace('max_size 65536','max_size 70000')));
});
async function client(f,loginId){
 const password='isolated-feedback-password';
 const call=async(path,body,method=body===undefined?'GET':'POST',auth)=>{
  const response=await fetch(f.endpoint+path,{method,headers:{'Content-Type':'application/json',...auth?{'X-TB-User':auth.account.userId,Authorization:'Bearer '+auth.token}:{}},...body===undefined?{}:{body:JSON.stringify(body)}});
  return {status:response.status,value:await response.json()};
 };
 assert.equal((await call('/v1/accounts/register',{loginId,nickname:loginId,password})).status,201);
 const auth=(await call('/v1/accounts/login',{loginId,password})).value;
 return {id:auth.account.userId,call:(path,body,method)=>call(path,body,method,auth)};
}
test('management permission preserves a regular training account, scores and social controls; named admin stays excluded',async()=>{
 const f=await startFixture({now});try{
  const player=await client(f,'normal_staff'),other=await client(f,'normal_player'),admin=await client(f,'admin');
  for(const user of [player,admin])f.STORE.database.prepare('INSERT INTO ranking_admins VALUES(?,?)').run(user.id,new Date(now).toISOString());
  for(const [i,user] of [player,admin].entries()){
   const hash=createHash('sha256').update('original-problem-'+i).digest('hex');
   assert.equal((await user.call('/v1/events',{events:[{eventId:hash,problemKey:hash,acceptedAt:new Date(now-60000).toISOString(),scope:'official',difficulty:800}]})).status,200);
  }
  for(const period of ['daily','weekly','total']){
   const board=await player.call('/v1/leaderboard?period='+period);assert.equal(board.status,200);
   assert.equal(board.value.self.userId,player.id);assert.equal(board.value.self.count,1);assert.equal(board.value.socialAvailable,true);
   assert(board.value.entries.some(item=>item.userId===player.id));assert(!board.value.entries.some(item=>item.userId===admin.id));
   assert.equal((await admin.call('/v1/leaderboard?period='+period)).value.self,null);
   assert.equal((await other.call('/v1/leaderboard?period='+period)).value.entries.find(item=>item.userId===player.id).count,1);
  }
  assert.equal(await f.countEvents(),2);assert.equal(f.STORE.database.prepare('SELECT COUNT(*) AS n FROM ranking_admins').get().n,2);
 }finally{await f.close();}
});
test('original avatar bytes and full pixel dimensions survive actual HTTP publishing and fetching',async()=>{
 const f=await startFixture({now});try{
  const owner=await client(f,'portrait_owner'),viewer=await client(f,'portrait_viewer'),png=originalAvatarPng();
  assert(png.length>48*1024);assert.equal(png.readUInt32BE(16),512);
  const avatar='data:image/png;base64,'+png.toString('base64');
  const result=await owner.call('/v1/profile',{avatarData:avatar},'PUT');assert.equal(result.status,200);
  const fetched=await viewer.call('/v1/avatars/'+owner.id);assert.equal(fetched.status,200);assert.equal(fetched.value.avatarData,avatar);
  assert.equal(fetched.value.avatarHash,createHash('sha256').update(avatar).digest('hex'));
  assert.equal((await owner.call('/v1/profile')).value.originalAvatarProtocol,1);
  assert(!(await viewer.call('/v1/leaderboard')).value.entries.some(row=>Object.hasOwn(row,'avatarData')));
 }finally{await f.close();}
});
test('placing and recycling include confirmed inventory without bloating durable operation receipts',async()=>{
 const f=await startFixture({now});try{
  const owner=await client(f,'sticker_recycle');
  assert.equal((await owner.call('/v1/stickers/grant',{requestId:randomUUID(),day:'2026-11-03',taskId:'ac-chain:0',xp:30})).status,200);
  const claimed=(await owner.call('/v1/stickers')).value;
  assert.equal(claimed.units.length,0,'Claiming a task stores an unopened pack');
  const box=Object.values(claimed.boxes).find(item=>!item.opened);
  const opened=await owner.call('/v1/stickers/open-box',{requestId:randomUUID(),boxId:box.id});
  assert.equal(opened.status,200);
  const unit=opened.value.inventory.units[0];
  const placed=await owner.call('/v1/stickers/place',{requestId:randomUUID(),unitId:unit.id,revision:unit.revision,x:.5,y:.5,angle:0});
  assert.equal(placed.status,200);assert(placed.value.inventory.units[0].placement);
  const requestId=randomUUID(),body={requestId,unitId:unit.id,revision:placed.value.inventory.units[0].revision};
  const result=await owner.call('/v1/stickers/recycle',body);assert.equal(result.status,200);assert.equal(result.value.inventory.units[0].placement,null);
  assert.equal((await owner.call('/v1/stickers/recycle',body)).value.inventory.units.length,box.quantity);
  const receipt=JSON.parse(f.STORE.database.prepare('SELECT response FROM gameplay_operations WHERE user_id=? AND request_id=?').get(owner.id,requestId).response);
  assert(!Object.hasOwn(receipt,'inventory'));assert.equal(receipt.requestId,requestId);
 }finally{await f.close();}
});
