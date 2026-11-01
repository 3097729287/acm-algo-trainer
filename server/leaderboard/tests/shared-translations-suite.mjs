import assert from 'node:assert/strict';
import test from 'node:test';
import {createHash,randomUUID} from 'node:crypto';

export function sharedTranslationsSuite(startFixture){
 test('public translations bind the exact source, preserve formulas and expose no account or provider secrets',async()=>{
  const fixture=await startFixture({now:Date.parse('2026-10-08T12:00:00Z')});
  async function call(user,method,path,value){const response=await fetch(fixture.endpoint+path,{method,headers:{'Content-Type':'application/json',...(user?{'X-TB-User':user.userId,Authorization:'Bearer '+user.token}:{})},...(value===undefined?{}:{body:JSON.stringify(value)})});return {status:response.status,value:await response.json()};}
  async function user(nickname){const loginId='tb_'+randomUUID().replaceAll('-','').slice(0,24);assert.equal((await call(null,'POST','/v1/accounts/register',{loginId,nickname,password:'fixture-password-123'})).status,201);const result=await call(null,'POST','/v1/accounts/login',{loginId,password:'fixture-password-123'});assert.equal(result.status,200);return {userId:result.value.account.userId,token:result.value.token};}
  try {
   const alice=await user('译文甲'),bob=await user('译文乙');
   const original='Given a positive integer $n$, print its value.';
   const identity={url:'https://codeforces.com/contest/1/problem/A',sourceHash:createHash('sha256').update('complete-prose-v4\n'+original).digest('hex'),format:'complete-prose-v4',language:'zh-CN'};
   const query='/v1/translations?'+new URLSearchParams(identity);
   assert.equal((await call(null,'GET',query)).status,401);
   assert.equal((await call(bob,'GET',query)).value.translation,null);
   const body={...identity,original,markdown:'给定一个正整数 $n$，输出它的值。'};
   assert.equal((await call(alice,'POST','/v1/translations',{...body,apiKey:'must-not-be-accepted'})).status,400);
   assert.equal((await call(alice,'POST','/v1/translations',{...body,sourceHash:'0'.repeat(64)})).status,400);
   assert.equal((await call(alice,'POST','/v1/translations',{...body,markdown:'给定一个正整数，输出它的值。'})).status,400);
   assert.equal((await call(alice,'POST','/v1/translations',body)).status,200);
   const received=(await call(bob,'GET',query)).value.translation;
   assert.equal(received.markdown,body.markdown);assert.equal(received.sourceHash,identity.sourceHash);
   assert.equal(Object.hasOwn(received,'contributorId'),false);assert.equal(Object.hasOwn(received,'original'),false);
   assert.equal((await call(bob,'GET','/v1/translations?'+new URLSearchParams({...identity,sourceHash:'1'.repeat(64)}))).value.translation,null);
  } finally {await fixture.close();}
 });
}
