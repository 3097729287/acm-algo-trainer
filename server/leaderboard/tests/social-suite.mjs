import test from 'node:test';
import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';

async function call(f,path,body,auth,method=body===undefined?'GET':'POST') {
  const response=await fetch(f.endpoint+path,{method,headers:{'Content-Type':'application/json','X-TB-State-Protocol':'1',...(auth?{'X-TB-User':auth.userId,Authorization:'Bearer '+auth.token}:{})},...(body===undefined?{}:{body:JSON.stringify(body)})});
  return {status:response.status,value:await response.json()};
}
async function login(f,name) {
  const value={loginId:name,nickname:name,password:'social-fixture-password'};
  assert.equal((await call(f,'/v1/accounts/register',value)).status,201);
  const response=await call(f,'/v1/accounts/login',{loginId:name,password:value.password});
  assert.equal(response.status,200);
  return {userId:response.value.account.userId,token:response.value.token};
}
export function socialSuite(startFixture) {
  test('daily hearts are atomic, irrevocable, shared across periods and reset at Beijing midnight',async()=>{
    const f=await startFixture({now:Date.parse('2026-10-20T15:59:00Z')});
    try {
      const actor=await login(f,'heart_actor'),target=await login(f,'heart_target');
      const attempts=await Promise.all(Array.from({length:8},()=>call(f,'/v1/social/likes',{targetId:target.userId},actor)));
      assert(attempts.every(result=>result.status===200));assert.equal(attempts.filter(result=>result.value.created).length,1);
      for(const period of ['daily','weekly','total']) {
        const result=await call(f,'/v1/leaderboard?period='+period,undefined,actor);
        assert.equal(result.value.socialAvailable,true);
        assert.deepEqual(result.value.entries.find(row=>row.userId===target.userId).likes,{total:1,likedToday:true});
      }
      assert.equal((await call(f,'/v1/social/likes',{targetId:target.userId},actor,'DELETE')).status,404);
      let inbox=(await call(f,'/v1/social',undefined,target)).value;
      assert.equal(inbox.totalLikes,1);assert.equal(inbox.notifications.length,1);assert.equal(inbox.unreadCount,1);
      assert.equal(inbox.notifications[0].actor.nickname,'heart_actor');
      f.env.TEST_NOW=Date.parse('2026-10-20T16:01:00Z');
      const next=await call(f,'/v1/social/likes',{targetId:target.userId},actor);
      assert.deepEqual(next.value.likes,{total:2,likedToday:true});
      assert.equal((await call(f,'/v1/social',undefined,target)).value.totalLikes,2);
    } finally {await f.close();}
  });
  test('private comments are retry safe, owner readable, bounded and never leak into public activity',async()=>{
    const f=await startFixture({now:Date.now()});
    try {
      const actor=await login(f,'comment_actor'),target=await login(f,'comment_target'),other=await login(f,'comment_other');
      const content={targetId:target.userId,text:'加油 🐈\n一起训练 <script>unsafe()</script>',requestId:randomUUID()};
      const first=await call(f,'/v1/social/comments',content,actor);
      assert.equal(first.status,200);assert.equal(first.value.created,true);
      assert.equal((await call(f,'/v1/social/comments',content,actor)).value.created,false);
      assert.equal((await call(f,'/v1/social/comments',{...content,text:'different'},actor)).status,409);
      const inbox=(await call(f,'/v1/social',undefined,target)).value;
      assert.equal(inbox.notifications[0].text,content.text);assert.equal(inbox.unreadCount,1);assert.equal(inbox.activity.length,0);
      assert.equal((await call(f,'/v1/social',undefined,other)).value.notifications.length,0);
      await call(f,'/v1/social/read',{ids:[first.value.id]},other);
      assert.equal((await call(f,'/v1/social',undefined,target)).value.unreadCount,1);
      await call(f,'/v1/social/read',{ids:[first.value.id]},target);
      assert.equal((await call(f,'/v1/social',undefined,target)).value.unreadCount,0);
      for(const value of [{...content,requestId:randomUUID(),text:' '},{...content,requestId:randomUUID(),text:'猫'.repeat(501)},{...content,targetId:actor.userId}]) assert.equal((await call(f,'/v1/social/comments',value,actor)).status,400);
      assert.equal((await call(f,'/v1/social/likes',{targetId:target.userId})).status,401);
      await login(f,'comment_actor_new');
      await call(f,'/v1/accounts/login',{loginId:'comment_actor',password:'social-fixture-password'});
      assert.equal((await call(f,'/v1/social/likes',{targetId:target.userId},actor)).status,401);
    } finally {await f.close();}
  });
  test('read-all includes notifications beyond the visible 100 and cannot clear another inbox',async()=>{
    const f=await startFixture({now:Date.now()});
    try {
      const actor=await login(f,'read_actor'),target=await login(f,'read_target'),other=await login(f,'read_other');
      await f.STORE.social.database.transaction(async connection=>{
        for(let index=0;index<107;index++) await connection.execute(
          'INSERT INTO social_notifications(id,kind,actor_id,recipient_id,body,created_at) VALUES(?,?,?,?,?,?)',
          [randomUUID(),'comment',actor.userId,index<105?target.userId:other.userId,'训练加油',new Date(f.env.TEST_NOW+index*1000).toISOString()]);
      });
      let inbox=(await call(f,'/v1/social',undefined,target)).value;
      assert.equal(inbox.notifications.length,100);assert.equal(inbox.unreadCount,105);
      for(const value of [{all:false},{all:1},{all:'true'},{all:null},{all:true,ids:[]},
        {all:true,userId:other.userId},{all:true,targetId:other.userId},{all:true,recipientId:other.userId},
        {},{ids:Array.from({length:101},()=>randomUUID())},{ids:[42]},{ids:['invalid']}]) {
        assert.equal((await call(f,'/v1/social/read',value,target)).status,400);
      }
      assert.equal((await call(f,'/v1/social/read',{all:true})).status,401);
      assert.equal((await call(f,'/v1/social',undefined,target)).value.unreadCount,105);
      // Existing batch mode can mark the visible page, leaving older unread
      // messages. Read-all must operate on the complete authenticated inbox.
      assert.equal((await call(f,'/v1/social/read',{ids:inbox.notifications.map(item=>item.id)},target)).status,200);
      inbox=(await call(f,'/v1/social',undefined,target)).value;
      assert.equal(inbox.unreadCount,5);assert(inbox.notifications.every(item=>item.read));
      assert.equal((await call(f,'/v1/social/read',{all:true},target)).status,200);
      assert.equal((await call(f,'/v1/social',undefined,target)).value.unreadCount,0);
      assert.equal((await call(f,'/v1/social',undefined,other)).value.unreadCount,2);
      assert.equal((await call(f,'/v1/social/read',{all:true},target)).status,200);
      assert.equal((await call(f,'/v1/social',undefined,other)).value.unreadCount,2);
    } finally {await f.close();}
  });
  test('public heart activity never reveals another recipient private read receipts',async()=>{
    const f=await startFixture({now:Date.now()});
    try {
      const actor=await login(f,'public_actor'),target=await login(f,'public_target'),observer=await login(f,'public_observer');
      assert.equal((await call(f,'/v1/social/likes',{targetId:target.userId},actor)).status,200);
      const before=(await call(f,'/v1/social',undefined,observer)).value.activity;
      assert.equal(before.length,1);
      assert.deepEqual(Object.keys(before[0]).sort(),['id','kind','actor','recipient','createdAt'].sort());
      assert.equal((await call(f,'/v1/social/read',{all:true},target)).status,200);
      assert.equal((await call(f,'/v1/social',undefined,target)).value.notifications[0].read,true);
      const after=(await call(f,'/v1/social',undefined,observer)).value.activity;
      assert.deepEqual(after,before);
      assert(!('read' in after[0]));assert(!('text' in after[0]));
    } finally {await f.close();}
  });
  test('missing social tables disable only interactions; existing accounts, rankings and snapshots remain readable',async()=>{
    const f=await startFixture({now:Date.now()});
    try {
      const auth=await login(f,'legacy_social');
      const state={format:'tb-account-state-v1',tables:{drafts:[{problem_id:'private::A',context:'',code:'user code',saved_at:'2026-10-20T00:00:00Z'}]},publicAccounts:{}};
      assert.equal((await call(f,'/v1/accounts/state',{revision:0,state},auth,'PUT')).status,200);
      if(f.STORE.database) {
        f.STORE.database.exec('DROP TABLE social_notifications; DROP TABLE social_likes;');
      } else {
        await f.STORE.pool.query('DROP TABLE social_notifications');await f.STORE.pool.query('DROP TABLE social_likes');
      }
      f.STORE.social.checkedAt=0;
      assert.equal((await call(f,'/v1/health')).status,200);
      assert.equal((await call(f,'/v1/social',undefined,auth)).value.available,false);
      assert.equal((await call(f,'/v1/leaderboard',undefined,auth)).value.socialAvailable,false);
      assert.equal((await call(f,'/v1/social/likes',{targetId:randomUUID()},auth)).status,503);
      assert.deepEqual((await call(f,'/v1/accounts/state',undefined,auth)).value.state,state);
    } finally {await f.close();}
  });
  test('additional SQL columns do not shift account or interaction writes',async()=>{
    const f=await startFixture({now:Date.now()});
    try {
      const sqls=["ALTER TABLE users ADD COLUMN future_data VARCHAR(80) NOT NULL DEFAULT 'preserved'", "ALTER TABLE social_likes ADD COLUMN future_data VARCHAR(80) NOT NULL DEFAULT 'preserved'"];
      for(const sql of sqls) {
        if(f.STORE.database)f.STORE.database.exec(sql);else await f.STORE.pool.query(sql);
      }
      // Production uses explicit column names, so adding fields never shifts values.
      const actor=await login(f,'future_actor'),target=await login(f,'future_target');
      assert.equal((await call(f,'/v1/social/likes',{targetId:target.userId},actor)).value.created,true);
      assert.equal((await call(f,'/v1/social',undefined,target)).value.totalLikes,1);
    } finally {await f.close();}
  });
}
