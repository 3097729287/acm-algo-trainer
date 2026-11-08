import test from 'node:test';
import assert from 'node:assert/strict';
import mysql from 'mysql2/promise';
import {createHash,randomUUID} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {startMySQLFixture} from './mysql-fixture.mjs';
import {preservedData} from '../scripts/audit-preserved-data.mjs';

const hash=value=>createHash('sha256').update(value).digest('hex');
const now=Date.parse('2026-11-08T00:00:00Z');

test('isolated MySQL executes additive team migrations, native proofs and cross-account draft concurrency',async()=>{
 assert(process.env.TB_MYSQL_TEST_DATADIR,'An explicitly owned disposable datadir is required');
 const admin=await mysql.createConnection({host:'127.0.0.1',port:Number(process.env.TB_MYSQL_TEST_PORT),user:'root',password:process.env.TB_MYSQL_TEST_PASSWORD||''});
 try{
  const [[actual]]=await admin.query('SELECT @@datadir AS datadir');
  assert.equal(path.resolve(actual.datadir).toLowerCase(),path.resolve(process.env.TB_MYSQL_TEST_DATADIR).toLowerCase(),'Never create fixtures in an unverified MySQL instance');
 }finally{await admin.end();}
 const f=await startMySQLFixture({now});
 try{
  const before=await preservedData(f.STORE.pool);
  const migration=async()=>{
   for(const file of ['019_team_training.sql','020_team_native_receipts.sql']){
    const source=await readFile(new URL('../mysql/'+file,import.meta.url),'utf8');
    for(const sql of source.split(';').map(s=>s.trim()).filter(Boolean))await f.STORE.pool.query(sql);
   }
  };
  await migration();const created=await preservedData(f.STORE.pool);
  for(const [name,value]of Object.entries(before.tables))assert.deepEqual(created.tables[name],value,'preserve '+name);
  assert.equal(Object.keys(created.tables).length-Object.keys(before.tables).length,9);
  const contest={id:'codeforces:contest:123',title:'隔离 MySQL 三人赛',platform:'Codeforces',availableProblems:2,missingProblems:1,
   problems:['A','B','C'].map((letter,index)=>({id:'fixture::'+letter,letter,title:'题目 '+letter,url:'https://codeforces.com/contest/123/problem/'+letter,
    problemKey:hash('codeforces.com/contest/123/problem/'+letter),available:index!==1,problemType:'standard'}))};
  const teams=f.STORE.teams;teams.catalogue={schema:1,revision:'isolated-mysql',contests:[contest]};teams.contests=new Map([[contest.id,contest]]);
  assert(await teams.available());
  const users=[];
  for(let i=0;i<4;i++){
   const body={loginId:'mysql_team_'+i,nickname:'MySQL 队员'+i,password:'isolated-team-password'};
   const send=(name,value)=>fetch(f.endpoint+'/v1/accounts/'+name,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(value)});
   assert.equal((await send('register',body)).status,201);
   const login=await send('login',{loginId:body.loginId,password:body.password});assert.equal(login.status,200);const value=await login.json();
   users.push({owner:value.account.userId,auth:hash(value.token)});
  }
  const write=(user,action,body={},at=now)=>teams.write(user.owner,user.auth,action,{requestId:randomUUID(),...body},at);
  const [a,b,c,d]=users;
  let view=await write(a,'create',{name:'MySQL 中文🦆'});
  await write(b,'join',{inviteCode:view.team.inviteCode});await write(c,'join',{inviteCode:view.team.inviteCode});
  await assert.rejects(write(d,'join',{inviteCode:view.team.inviteCode}),{code:'TEAM_TEAM_FULL'});
  view=await teams.read(a.owner,now);
  view=await write(a,'configure',{teamRevision:view.team.revision,contestId:contest.id,durationMinutes:5});
  const configurationRevision=view.team.configurationRevision;
  await Promise.all([a,b,c].map(user=>write(user,'ready',{configurationRevision,ready:true})));
  view=await teams.read(a.owner,now);assert(view.team.members.every(p=>p.ready));
  view=await write(a,'start',{teamRevision:view.team.revision});const roomId=view.room.id;
  const claims=await Promise.allSettled([a,b,c].map(user=>write(user,'claim',{roomId},now+4000)));
  assert.equal(claims.filter(r=>r.status==='fulfilled').length,1);
  const winner=users[claims.findIndex(r=>r.status==='fulfilled')];view=await teams.read(winner.owner,now+4000);
  const leaseToken=view.room.lease.token,code='// 中文🦆\nint main() {}\n';
  await write(winner,'draft',{roomId,leaseToken,problemId:'fixture::A',revision:0,language:'cpp17',code},now+4000);
  await assert.rejects(write(winner,'draft',{roomId,leaseToken,problemId:'fixture::A',revision:0,language:'cpp17',code:'stale'},now+4001),{code:'TEAM_REVISION_CONFLICT'});
  assert.equal((await teams.read(b.owner,now+4001)).room.document.code,code);
  const grant=await write(winner,'authorize',{roomId,leaseToken,problemId:'fixture::A',revision:1,language:'cpp17',purpose:'submit',inputSha256:hash(code)},now+4002);
  teams.verifyReceipt=async request=>({...request,verdict:'AC',submittedAt:now+4002,source:'isolated-mysql-provider',proofSha256:hash('native-fixture')});
  const receipt={requestId:randomUUID(),intentId:grant.ack.authorization.id,submissionId:'19191919',handle:'mysql_fixture'};
  await teams.nativeReceipt(winner.owner,winner.auth,receipt,now+5000);await teams.nativeReceipt(winner.owner,winner.auth,receipt,now+5001);
  assert.equal((await teams.standings(now+6000)).entries[0].totalScore,1);
  const [[count]]=await f.STORE.pool.query('SELECT COUNT(*) AS n FROM team_native_receipts');assert.equal(Number(count.n),1);
  const populated=await preservedData(f.STORE.pool);await migration();const after=await preservedData(f.STORE.pool);
  assert.deepEqual(after,populated,'rerunning additive migrations preserves every old and new row');
 }finally{await f.close();}
});
