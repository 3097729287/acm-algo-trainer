import test from 'node:test';
import assert from 'node:assert/strict';
import {randomBytes} from 'node:crypto';
import {tokenHash,verifyPassword} from '../src/accounts.mjs';

async function sql(f,query,params=[]) {
  if(f.STORE.pool)return (await f.STORE.pool.execute(query,params))[0];
  const statement=f.STORE.database.prepare(query);
  return /^\s*SELECT/i.test(query)?statement.all(...params):statement.run(...params);
}
async function call(f,path,body,auth,method=body===undefined?'GET':'POST') {
  const response=await fetch(f.endpoint+path,{method,headers:{'Content-Type':'application/json','X-TB-State-Protocol':'1','X-TB-Chunk-Protocol':'2',...(auth?{'X-TB-User':auth.userId,Authorization:'Bearer '+auth.token}:{})},...(body===undefined?{}:{body:JSON.stringify(body)})});
  return {status:response.status,value:await response.json()};
}
const secret='isolated-long-password';
async function create(f,loginId,admin=false) {
  const registered=await call(f,'/v1/accounts/register',{loginId,nickname:'fixture-'+loginId,password:secret});
  assert.equal(registered.status,201,JSON.stringify(registered.value));
  const logged=await call(f,'/v1/accounts/login',{loginId,password:secret});
  assert.equal(logged.status,200,JSON.stringify(logged.value));
  const account={userId:logged.value.account.userId,token:logged.value.token,loginId};
  if(admin)await sql(f,'INSERT INTO ranking_admins(user_id,granted_at) VALUES(?,?)',[account.userId,new Date().toISOString()]);
  return account;
}
const payload=(target,action)=>({userId:target.userId,loginId:target.loginId,confirmation:action});
const count=async(f,table,id,column='user_id')=>Number((await sql(f,`SELECT COUNT(*) AS n FROM ${table} WHERE ${column}=?`,[id]))[0].n);
async function populate(f,target,other) {
  const id=target.userId,time='2026-10-29T01:00:00.000Z',hash='a'.repeat(64);
  await sql(f,'INSERT INTO account_state VALUES(?,?,?,?)',[id,2,JSON.stringify({fixture:'private-kept'}),time]);
  await sql(f,'INSERT INTO account_public_progress VALUES(?,?,?)',[id,'{}',time]);
  await sql(f,'INSERT INTO account_public_avatars VALUES(?,?,?,?)',[id,'fixture-avatar',hash,time]);
  await sql(f,'INSERT INTO account_chunk_heads VALUES(?,?,?,?,?)',[id,1,hash,null,time]);
  await sql(f,'INSERT INTO account_chunk_usage VALUES(?,?,?,?)',[id,1,1,'']);
  await sql(f,'INSERT INTO account_chunks VALUES(?,?,?,?,?,?,?,?)',[id,hash,'root',Buffer.from('fixture'),'[]',7,time,time]);
  for(const table of ['ac_events','official_ac_events'])await sql(f,`INSERT INTO ${table} VALUES(?,?,?,?,?,?,?)`,[id,hash,'b'.repeat(64),time,'2026-10-29',800,time]);
  await sql(f,'INSERT INTO ranking_exclusions VALUES(?,?,?)',[id,hash,time]);
  await sql(f,'INSERT INTO ranking_cycles VALUES(?,?,?,?)',['daily','2026-10-28','2026-10-29',time]);
  await sql(f,'INSERT INTO ranking_rewards VALUES(?,?,?,?,?,?,?)',[id,'daily','2026-10-28','2026-10-29',1,100,time]);
  await sql(f,'INSERT INTO training_list_likes VALUES(?,?,?,?)',[id,'fixture-list','2026-10-29',time]);
  await sql(f,'INSERT INTO social_likes VALUES(?,?,?,?)',[id,other.userId,'2026-10-29',time]);
  await sql(f,'INSERT INTO social_likes VALUES(?,?,?,?)',[other.userId,id,'2026-10-29',time]);
  await sql(f,'INSERT INTO social_notifications VALUES(?,?,?,?,?,?,?)',[crypto.randomUUID(),'like',other.userId,id,'fixture',time,null]);
}

export function adminAccountsSuite(startFixture) {
  test('account maintenance requires a live service role and returns only exact public identity fields',async()=>{
    const f=await startFixture();
    try {
      const actor=await create(f,'admin'),target=await create(f,'target_user');
      assert.equal((await call(f,'/v1/admin/accounts?q=target_user')).status,401);
      assert.equal((await call(f,'/v1/admin/accounts?q=target_user',undefined,actor)).status,403,'admin login text is not an authority');
      assert.equal((await call(f,'/v1/admin/accounts/delete',payload(target,'delete-account'),target)).status,403);
      await sql(f,'INSERT INTO ranking_admins VALUES(?,?)',[actor.userId,new Date().toISOString()]);
      const found=await call(f,'/v1/admin/accounts?q=target_user',undefined,actor);
      assert.equal(found.status,200);assert.equal(found.value.accounts.length,1);
      assert.deepEqual(Object.keys(found.value.accounts[0]).sort(),['createdAt','loginId','nickname','protected','userId']);
      assert.equal(found.value.accounts[0].userId,target.userId);assert.equal(found.value.accounts[0].protected,false);
      for(const q of [target.userId,'TB-'+target.userId.replaceAll('-','').toUpperCase()])assert.equal((await call(f,'/v1/admin/accounts?q='+q,undefined,actor)).value.accounts[0].userId,target.userId);
      assert.deepEqual((await call(f,'/v1/admin/accounts?q=missing_user',undefined,actor)).value.accounts,[]);
      assert.equal((await call(f,'/v1/admin/accounts?q='+encodeURIComponent("x' OR 1=1"),undefined,actor)).status,400);
      assert(!/password|scrypt|token|hash/i.test(JSON.stringify(found.value)));
    }finally{await f.close();}
  });
  test('reset alone admits the fixed short credential, preserves private state and revokes every old device session',async()=>{
    const f=await startFixture();
    try {
      const actor=await create(f,'admin',true),target=await create(f,'reset_user');
      await populate(f,target,actor);
      assert.equal((await call(f,'/v1/accounts/register',{loginId:'short_user',nickname:'short',password:'123456'})).status,400);
      assert.equal((await call(f,'/v1/accounts/login',{loginId:target.loginId,password:'654321'})).status,400);
      assert.equal((await call(f,'/v1/accounts/login',{loginId:target.loginId,password:'123456'})).status,401);
      const version=(await sql(f,'SELECT password_version FROM accounts WHERE user_id=?',[target.userId]))[0].password_version;
      await sql(f,'INSERT INTO account_sessions VALUES(?,?,?,?,?)',[tokenHash(randomBytes(32)),target.userId,version,Math.floor(Date.now()/1000)+3600,new Date().toISOString()]);
      assert.equal(await count(f,'account_sessions',target.userId),2);
      const wrong=await call(f,'/v1/admin/accounts/reset-password',payload(target,'delete-account'),actor);assert.equal(wrong.status,400);
      const result=await call(f,'/v1/admin/accounts/reset-password',payload(target,'reset-password'),actor);
      assert.equal(result.status,200);assert.equal(result.value.sessionsRevoked,true);
      assert(!/password|scrypt|token|hash|123456/i.test(JSON.stringify(result.value)));
      assert.equal(await count(f,'account_sessions',target.userId),0);
      const [row]=await sql(f,'SELECT password_hash,password_version FROM accounts WHERE user_id=?',[target.userId]);
      assert.equal(Number(row.password_version),Number(version)+1);assert(await verifyPassword('123456',row.password_hash));
      for(const path of ['/v1/accounts/me','/v1/accounts/state','/v2/accounts/state','/v1/profile','/v1/leaderboard','/v1/social'])assert.equal((await call(f,path,undefined,target)).status,401,path);
      for(const [path,method] of [['/v1/events','POST'],['/v1/accounts/state','PUT'],['/v2/accounts/state','PUT'],['/v1/profile','PUT']])assert.equal((await call(f,path,{},target,method)).status,401,path);
      assert.equal((await sql(f,'SELECT payload FROM account_state WHERE user_id=?',[target.userId]))[0].payload,JSON.stringify({fixture:'private-kept'}));
      assert.equal(await count(f,'account_chunks',target.userId),1);assert.equal(await count(f,'ranking_rewards',target.userId),1);
      assert.equal((await call(f,'/v1/accounts/login',{loginId:target.loginId,password:secret})).status,401);
      const logged=await call(f,'/v1/accounts/login',{loginId:target.loginId,password:'123456'});assert.equal(logged.status,200);
      const auth={userId:target.userId,token:logged.value.token};
      assert.equal((await call(f,'/v1/accounts/password',{oldPassword:'123456',newPassword:'123456'},auth)).status,400);
      assert.equal((await call(f,'/v1/accounts/password',{oldPassword:'123456',newPassword:'renewed-long-password'},auth)).status,200);
      const audit=await sql(f,'SELECT * FROM account_admin_actions');assert.equal(audit.length,1);assert.equal(audit[0].action,'reset-password');
      assert(!/123456|password_hash|scrypt|token/i.test(JSON.stringify(audit)));
    }finally{await f.close();}
  });
  test('self, named admin and other service administrators cannot be deleted or reset',async()=>{
    const f=await startFixture();
    try {
      const actor=await create(f,'admin',true),other=await create(f,'staff_admin',true);
      for(const target of [actor,other])for(const [path,confirm] of [['delete','delete-account'],['reset-password','reset-password']]) {
        assert.equal((await call(f,'/v1/admin/accounts/'+path,payload(target,confirm),actor)).status,403);
        assert.equal(await count(f,'accounts',target.userId),1);
      }
      assert.equal((await call(f,'/v1/admin/accounts?q=staff_admin',undefined,actor)).value.accounts[0].protected,true);
      assert.equal((await sql(f,'SELECT COUNT(*) AS n FROM account_admin_actions'))[0].n,0);
    }finally{await f.close();}
  });
  test('account deletion removes owned cloud data and target social edges while preserving unrelated accounts and audit',async()=>{
    const f=await startFixture();
    try {
      const actor=await create(f,'admin',true),target=await create(f,'delete_user'),other=await create(f,'other_user');
      await populate(f,target,other);
      const result=await call(f,'/v1/admin/accounts/delete',payload(target,'delete-account'),actor);
      assert.equal(result.status,200,JSON.stringify(result.value));assert.equal(result.value.deleted,true);
      for(const table of ['users','accounts','account_state','account_sessions','account_login_days','account_public_progress','account_public_avatars','account_chunk_heads','account_chunk_usage','account_chunks','account_nicknames','official_ac_events','ac_events','ranking_exclusions','ranking_rewards'])assert.equal(await count(f,table,target.userId),0,table);
      assert.equal(await count(f,'training_list_likes',target.userId,'actor_id'),0);
      assert.equal(Number((await sql(f,'SELECT COUNT(*) AS n FROM social_likes WHERE actor_id=? OR recipient_id=?',[target.userId,target.userId]))[0].n),0);
      assert.equal(Number((await sql(f,'SELECT COUNT(*) AS n FROM social_notifications WHERE actor_id=? OR recipient_id=?',[target.userId,target.userId]))[0].n),0);
      for(const auth of [actor,other])assert.equal((await call(f,'/v1/accounts/me',undefined,auth)).status,200);
      assert.equal((await call(f,'/v1/accounts/me',undefined,target)).status,401);
      assert.equal((await call(f,'/v1/accounts/login',{loginId:target.loginId,password:secret})).status,401);
      const audit=await sql(f,'SELECT actor_id,target_id,action FROM account_admin_actions');
      assert.deepEqual(audit.map(r=>({...r})),[{actor_id:actor.userId,target_id:target.userId,action:'delete-account'}]);
      const recreated=await create(f,target.loginId);assert.notEqual(recreated.userId,target.userId);
      assert.equal(await count(f,'account_state',recreated.userId),0);
    }finally{await f.close();}
  });
  test('stale role/session and a stale target identity fail in the storage transaction',async()=>{
    const f=await startFixture();
    try {
      const actor=await create(f,'admin',true),target=await create(f,'guard_user'),seconds=Math.floor(Date.now()/1000),time=new Date().toISOString();
      const args=[actor.userId,tokenHash(actor.token),seconds];
      await sql(f,'DELETE FROM ranking_admins WHERE user_id=?',[actor.userId]);
      await assert.rejects(()=>f.STORE.accountAdmin.remove(...args,payload(target,'delete-account'),time),error=>error.status===403);
      await sql(f,'INSERT INTO ranking_admins VALUES(?,?)',[actor.userId,time]);
      await assert.rejects(()=>f.STORE.accountAdmin.remove(...args,{...payload(target,'delete-account'),loginId:'wrong_user'},time),error=>error.status===409);
      await sql(f,'DELETE FROM account_sessions WHERE user_id=?',[actor.userId]);
      await assert.rejects(()=>f.STORE.accountAdmin.remove(...args,payload(target,'delete-account'),time),error=>error.status===401);
      assert.equal(await count(f,'accounts',target.userId),1);
    }finally{await f.close();}
  });
  test('a dependency failure rolls back partial account deletion and cannot create a success audit',async()=>{
    const f=await startFixture();
    try {
      const actor=await create(f,'admin',true),target=await create(f,'rollback_user');await populate(f,target,actor);
      const database=f.STORE.accountAdmin.database,original=database.transaction;
      database.transaction=action=>original.call(database,connection=>action({execute:(query,params)=>{
        if(query==='DELETE FROM accounts WHERE user_id=?')throw Error('isolated dependency failure');
        return connection.execute(query,params);
      }}));
      assert.equal((await call(f,'/v1/admin/accounts/delete',payload(target,'delete-account'),actor)).status,503);
      database.transaction=original;
      for(const table of ['accounts','account_state','account_chunks','ranking_rewards','official_ac_events'])assert.equal(await count(f,table,target.userId),1,table);
      assert.equal(await count(f,'account_sessions',target.userId),1);
      assert.equal(Number((await sql(f,'SELECT COUNT(*) AS n FROM account_admin_actions'))[0].n),0);
      assert.equal((await call(f,'/v1/accounts/me',undefined,target)).status,200);
    }finally{await f.close();}
  });
  test('missing additive migration disables maintenance without hiding ordinary service health',async()=>{
    const f=await startFixture();
    try {
      const actor=await create(f,'admin',true);
      await sql(f,'DROP TABLE account_admin_actions');
      const health=await call(f,'/v1/health');assert.equal(health.status,200);assert.equal(health.value.adminAccountProtocol,0);
      assert.equal((await call(f,'/v1/admin/accounts?q=admin',undefined,actor)).status,503);
      assert.equal((await call(f,'/v1/accounts/me',undefined,actor)).status,200);
    }finally{await f.close();}
  });
  test('an initially valid administrator session that expires during password hashing cannot reset a target',async()=>{
    const f=await startFixture({now:Date.now()});
    let release;
    try {
      const actor=await create(f,'admin',true),target=await create(f,'hash_expiry_user');
      const prior=(await sql(f,'SELECT password_hash,password_version FROM accounts WHERE user_id=?',[target.userId]))[0];
      const expiry=Number((await sql(f,'SELECT expires_at FROM account_sessions WHERE user_id=?',[actor.userId]))[0].expires_at);
      let enter;const entered=new Promise(resolve=>enter=resolve),gate=new Promise(resolve=>release=resolve);
      const original=f.STORE.accountAdmin.passwordHash;
      f.STORE.accountAdmin.passwordHash=async value=>{enter();await gate;return original(value);};
      const pending=call(f,'/v1/admin/accounts/reset-password',payload(target,'reset-password'),actor);
      let timer;
      try {
        // The original HTTP authentication has already succeeded. An earlier
        // response/failure must fail this causal test instead of hanging it.
        await Promise.race([entered,pending.then(result=>{throw Error('Reset returned before the controlled hash gate: '+result.status);}),
          new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('Controlled hash gate was not reached')),15000);})]);
      }finally{clearTimeout(timer);}
      f.env.TEST_NOW=(expiry+1)*1000;release();
      const result=await pending;assert.equal(result.status,401,JSON.stringify(result.value));
      const after=(await sql(f,'SELECT password_hash,password_version FROM accounts WHERE user_id=?',[target.userId]))[0];
      assert.deepEqual({...after},{...prior});assert.equal(await count(f,'account_sessions',target.userId),1);
      assert.equal(Number((await sql(f,'SELECT COUNT(*) AS n FROM account_admin_actions'))[0].n),0);
    }finally{release?.();await f.close();}
  });
  test('waiting for a target cannot extend administrator authority past session expiry for delete or reset',async()=>{
    const f=await startFixture({now:Date.now()});
    try {
      const actor=await create(f,'admin',true),target=await create(f,'target_expiry_user');
      const initial=f.env.TEST_NOW,expiry=Number((await sql(f,'SELECT expires_at FROM account_sessions WHERE user_id=?',[actor.userId]))[0].expires_at);
      const original=f.STORE.accountAdmin.target;
      f.STORE.accountAdmin.target=async function(...args){const result=await original.apply(this,args);f.env.TEST_NOW=(expiry+1)*1000;return result;};
      for(const [path,action] of [['delete','delete-account'],['reset-password','reset-password']]) {
        f.env.TEST_NOW=initial;
        const result=await call(f,'/v1/admin/accounts/'+path,payload(target,action),actor);
        assert.equal(result.status,401,JSON.stringify(result.value));
        assert.equal(await count(f,'accounts',target.userId),1);assert.equal(await count(f,'account_sessions',target.userId),1);
      }
      assert.equal(Number((await sql(f,'SELECT COUNT(*) AS n FROM account_admin_actions'))[0].n),0);
    }finally{await f.close();}
  });
}
