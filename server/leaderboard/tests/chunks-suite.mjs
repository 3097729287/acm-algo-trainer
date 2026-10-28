import test from 'node:test';
import assert from 'node:assert/strict';
import {gzipSync} from 'node:zlib';
import {randomUUID} from 'node:crypto';
import {chunkHash} from '../src/account-chunks.mjs';
import {session,tokenHash} from '../src/accounts.mjs';

async function call(f,auth,path,body,method=body===undefined?'GET':'POST',extra={}) {
  const response=await fetch(f.endpoint+path,{method,headers:{'Content-Type':'application/json','X-TB-State-Protocol':'1','X-TB-Chunk-Protocol':'2',...(auth?{'X-TB-User':auth.id,Authorization:'Bearer '+auth.token}:{}),...extra},...(body===undefined?{}:{body:JSON.stringify(body)})});
  return {status:response.status,value:await response.json()};
}
async function account(f,index=1) {
  const id=randomUUID(),now=f.env.TEST_NOW||Date.now(),stamp=new Date(now).toISOString();
  await f.STORE.createAccount({userId:id,nickname:'chunks-'+index,retiredHash:'a'.repeat(64),loginId:'chunks_'+index,passwordHash:'fixture-not-a-real-password',timestamp:stamp});
  const issued=session(now),user=await f.STORE.findAccount('chunks_'+index);
  await f.STORE.createSession(user,issued,stamp,true);
  return {id,token:issued.token,user};
}
const object=(text,children=[],kind='data')=>{
  children=[...new Set(children)].sort();const bytes=gzipSync(text,{level:6});
  return {hash:chunkHash(kind,bytes,children),value:{kind,data:bytes.toString('base64'),children}};
};
const put=(f,a,o)=>call(f,a,'/v2/accounts/state/objects/'+o.hash,o.value,'PUT');
const commit=(f,a,root,revision)=>call(f,a,'/v2/accounts/state',{root,revision},'PUT');

export function chunksSuite(startFixture) {
 test('bounded batches preserve dependency order and reject corrupt envelopes before writes',async()=>{
  const f=await startFixture();try{
   const a=await account(f,60),leaf=object('batch-private-source'),root=object('batch-root',[leaf.hash],'concat');
   const entries=[leaf,root].map(o=>({hash:o.hash,...o.value}));
   assert.equal((await call(f,a,'/v2/accounts/state/objects',{objects:[entries[0],{...entries[1],data:'broken'}]})).status,400);
   assert.equal((await call(f,a,'/v2/accounts/state/objects/'+leaf.hash)).status,404);
   const saved=await call(f,a,'/v2/accounts/state/objects',{objects:entries});
   assert.equal(saved.status,200);assert.deepEqual(saved.value.uploaded,[leaf.hash,root.hash]);
   assert.equal((await call(f,a,'/v2/accounts/state/objects',{objects:entries})).status,200);
   assert.equal((await call(f,a,'/v2/accounts/state/objects',{objects:[entries[0],entries[0]]})).status,400);
   assert.equal((await call(f,a,'/v2/accounts/state')).value.revision,0);
   assert.equal((await commit(f,a,root.hash,0)).status,200);
  }finally{await f.close();}
 });
 test('private chunks are immutable, owner isolated, checksum checked and committed only by CAS',async()=>{
  const f=await startFixture();try {
   const a=await account(f,1),b=await account(f,2),leaf=object('private original code'),root=object('root',[leaf.hash],'concat');
   assert.equal((await call(f,null,'/v2/accounts/state')).status,401);
   assert.equal((await put(f,a,root)).status,409,'missing dependency cannot become a visible graph');
   assert.equal((await commit(f,a,root.hash,0)).status,409);
   assert.equal((await put(f,a,leaf)).status,200);
   assert.equal((await put(f,a,leaf)).value.existing,true,'retry is idempotent');
   assert.equal((await put(f,a,root)).status,200);
   assert.equal((await commit(f,a,root.hash,0)).status,200);
   assert.equal((await commit(f,a,root.hash,0)).status,409,'stale revision cannot replace state');
   assert.equal((await call(f,a,'/v2/accounts/state')).value.root,root.hash);
   assert.equal((await call(f,a,'/v2/accounts/state',undefined,'GET',{'X-TB-State-Revision':'1'})).value.unchanged,true);
   assert.equal((await call(f,b,'/v2/accounts/state/objects/'+leaf.hash)).status,404);
   assert.deepEqual((await call(f,b,'/v2/accounts/state/missing',{hashes:[leaf.hash]})).value.missing,[leaf.hash]);
   assert.equal((await commit(f,b,root.hash,0)).status,409);
   assert.equal((await call(f,a,'/v1/accounts/state')).status,426,'old client must not read a stale legacy snapshot');
   const legacyRestore=await call(f,a,'/v1/accounts/state',undefined,'GET',{'X-TB-Chunk-Protocol':''});
   assert.equal(legacyRestore.status,401,'legacy saved restore must return to its login-screen updater');
   assert.match(legacyRestore.value.error,/updates\/stable\/index\.html/);
   assert.equal((await call(f,a,'/v2/accounts/state')).value.root,root.hash,'rejecting legacy restore must not revoke the modern session or change its root');
   assert.equal((await call(f,a,'/v1/accounts/state',{revision:1,state:{format:'tb-account-state-v1',tables:{},publicAccounts:{}}},'PUT')).status,426);
   const broken={...leaf,value:{...leaf.value,data:root.value.data}};
   assert.equal((await put(f,a,broken)).status,400);
   assert.equal((await put(f,a,{...leaf,value:{...leaf.value,children:[root.hash,root.hash]}})).status,400);
   assert.equal((await call(f,a,'/v2/accounts/state/missing',{hashes:Array(129).fill(leaf.hash)})).status,400);
   assert.equal((await put(f,a,object('x'.repeat(512),[], 'notvalid'))).status,400);
  } finally {await f.close();}
 });
 test('v1 migration preserves the exact recovery snapshot; revoked sessions fail again inside writes',async()=>{
  const f=await startFixture();try {
   const a=await account(f),now=f.env.TEST_NOW||Date.now(),stamp=new Date(now).toISOString();
   const original={format:'tb-account-state-v1',tables:{drafts:[{problem_id:'fixture',context:'',code:'never lose this',saved_at:stamp}]},publicAccounts:{}};
   await f.STORE.saveAccountState(a.id,tokenHash(a.token),Math.floor(now/1000),0,original,stamp);
   assert.equal((await call(f,a,'/v2/accounts/state')).value.revision,1);
   const leaf=object('new separated state');await put(f,a,leaf);
   assert.equal((await commit(f,a,leaf.hash,1)).value.revision,2);
   assert.deepEqual((await f.STORE.accountState(a.id)).state,original);
   const issued=session(now);await f.STORE.createSession(a.user,issued,stamp,true,true);
   await assert.rejects(()=>f.STORE.chunks.commit(a.id,tokenHash(a.token),Math.floor(now/1000),2,leaf.hash,stamp),e=>e.status===401);
   assert.equal((await put(f,a,leaf)).status,401);
   const current={...a,token:issued.token};assert.equal((await call(f,current,'/v2/accounts/state')).value.revision,2);
  }finally{await f.close();}
 });
 test('interrupted upload resumes; garbage collection retains both complete roots and all referenced code',async()=>{
  const f=await startFixture();try {
   const a=await account(f),date='2026-01-01T00:00:00.000Z',seconds=Math.floor((f.env.TEST_NOW||Date.now())/1000);
   const code=object('cold submission, still recoverable'),first=object('first',[code.hash],'concat'),second=object('second',[code.hash],'concat'),orphan=object('unfinished unreferenced old upload');
   for(const o of [code,first,second,orphan]){const value={kind:o.value.kind,bytes:Buffer.from(o.value.data,'base64'),children:o.value.children};await f.STORE.chunks.put(a.id,tokenHash(a.token),seconds,o.hash,value,date);}
   assert.deepEqual((await call(f,a,'/v2/accounts/state/missing',{hashes:[code.hash,first.hash]})).value.missing,[]);
   await commit(f,a,first.hash,0);await commit(f,a,second.hash,1);
   const removed=await f.STORE.chunks.collect(a.id,'2026-02-01T00:00:00.000Z');
   assert.equal(removed.removed,1);
   for(const o of [code,first,second])assert.equal((await call(f,a,'/v2/accounts/state/objects/'+o.hash)).status,200);
   assert.equal((await call(f,a,'/v2/accounts/state/objects/'+orphan.hash)).status,404);
  }finally{await f.close();}
 });
 test('50 simultaneous accounts retain private roots within the bounded HTTP request slot',async()=>{
  const f=await startFixture();try {
   const accounts=[];for(let i=0;i<50;i++)accounts.push(await account(f,i));
   const retry=async operation=>{for(let i=0;i<40;i++){const result=await operation();if(result.status!==429)return result;await new Promise(r=>setTimeout(r,100+Math.min(i*30,500)+Math.random()*100));}assert.fail('sync slot never became available');};
   await Promise.all(accounts.map(async(a,i)=>{
    const leaf=object('private code '+i);
    assert.equal((await retry(()=>put(f,a,leaf))).status,200);
    assert.equal((await retry(()=>commit(f,a,leaf.hash,0))).status,200);
    assert.equal((await retry(()=>call(f,a,'/v2/accounts/state'))).value.root,leaf.hash);
    assert.equal((await retry(()=>call(f,accounts[(i+1)%50],'/v2/accounts/state/objects/'+leaf.hash))).status,404);
   }));
  }finally{await f.close();}
 });
}
