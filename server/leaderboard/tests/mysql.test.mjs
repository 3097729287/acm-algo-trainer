import test from 'node:test';
import assert from 'node:assert/strict';
import { randomUUID, createHash } from 'node:crypto';
import { gzipSync, gunzipSync } from 'node:zlib';
import { protocolSuite } from './protocol-suite.mjs';
import { accountsSuite } from './accounts-suite.mjs';
import { startMySQLFixture } from './mysql-fixture.mjs';
import { socialSuite } from './social-suite.mjs';
import { snapshotFromSQL } from '../scripts/export-sqlite.mjs';
import { importSnapshot } from '../scripts/import-snapshot.mjs';
import { readFile } from 'node:fs/promises';
import { tokenHash } from '../src/accounts.mjs';

protocolSuite(startMySQLFixture);
accountsSuite(startMySQLFixture);
socialSuite(startMySQLFixture);

test('MySQL concurrent rate limits allocate each count once and expiry cleanup works', async () => {
  const fixture = await startMySQLFixture();
  try {
    const counts = await Promise.all(Array.from({ length: 24 }, () => fixture.STORE.incrementLimit('concurrent', 100)));
    assert.deepEqual(counts.sort((a, b) => a - b), Array.from({ length: 24 }, (_, i) => i + 1));
    await fixture.STORE.cleanup(101);
    assert.equal(await fixture.STORE.incrementLimit('concurrent', 200), 1);
  } finally { await fixture.close(); }
});

test('MySQL preserves Unicode nicknames and authentication hashes across connections', async () => {
  const fixture = await startMySQLFixture();
  try {
    const id = randomUUID(), now = new Date().toISOString();
    await fixture.STORE.createUser(id, '训练者 🐈', 'a'.repeat(64), now);
    await fixture.STORE.createUser(id, 'replacement', 'b'.repeat(64), now);
    const user = await fixture.STORE.findUser(id);
    assert.equal(user.nickname, '训练者 🐈');
    assert.equal(user.token_hash, 'a'.repeat(64));
    assert.equal(user.created_at, now);
  } finally { await fixture.close(); }
});

test('Snapshot migration preserves identities and records; refuses overwrite and rolls back invalid data', async () => {
  const fixture = await startMySQLFixture();
  try {
    const schema = await readFile(new URL('./schema.sql', import.meta.url), 'utf8');
    const id = randomUUID(), timestamp = '2026-10-08T10:00:00.000Z';
    const sql = schema + `\nINSERT INTO users VALUES('${id}','训练者 🐈','${'a'.repeat(64)}','${timestamp}','${timestamp}');
      INSERT INTO ac_events VALUES('${id}','${'b'.repeat(64)}','${'c'.repeat(64)}','${timestamp}','2026-10-08',1500,'${timestamp}');`;
    const snapshot = snapshotFromSQL(sql);
    const invalid = structuredClone(snapshot);
    invalid.events.push({ ...invalid.events[0], problem_key: 'd'.repeat(64) });
    await assert.rejects(() => importSnapshot(fixture.STORE, invalid));
    assert.equal(await fixture.STORE.findUser(id), null);
    assert.equal(await fixture.countEvents(), 0);
    assert.deepEqual(await importSnapshot(fixture.STORE, snapshot), { users: 1, events: 1 });
    assert.equal((await fixture.STORE.findUser(id)).token_hash, 'a'.repeat(64));
    assert.equal((await fixture.STORE.rankings(id, null)).own, null);
    assert.equal((await fixture.STORE.pool.query('SELECT COUNT(*) AS n FROM ac_events'))[0][0].n, 1);
    await assert.rejects(() => importSnapshot(fixture.STORE, snapshot), /Destination must be empty/);
    assert.equal(await fixture.countEvents(), 0);
  } finally { await fixture.close(); }
});

test('MySQL compressed learning state survives idempotent migration, concurrent CAS and device takeover', async () => {
  const f = await startMySQLFixture({now:Date.now()});
  try {
    const signup={loginId:'compressed_state_user',nickname:'跨机源码 🐈',password:'fixture-password'};
    async function call(path,body,auth,method=body===undefined?'GET':'POST') {
      const response=await fetch(f.endpoint+path,{method,headers:{'Content-Type':'application/json','X-TB-State-Protocol':'1',
        ...(auth?{'X-TB-User':auth.userId,Authorization:'Bearer '+auth.token}:{})},
        ...(body===undefined?{}:{body:JSON.stringify(body)})});
      return {status:response.status,value:await response.json()};
    }
    await call('/v1/accounts/register',signup);
    const first=await call('/v1/accounts/login',{loginId:signup.loginId,password:signup.password});
    assert.equal(first.status,200);
    const auth={userId:first.value.account.userId,token:first.value.token};
    const timestamp=new Date(f.env.TEST_NOW).toISOString();
    const logical={format:'tb-account-state-v1',tables:{
      drafts:[{problem_id:'private::A',context:'',code:'// 中文源码 evidence\n'.repeat(32000),saved_at:timestamp}],
      achievement_xp_claims:[{achievement_id:'official-count',unlocked_at:null,awarded_xp:30,claimed_at:timestamp}],
      account_preferences:[{key:'favorites',value:'["private::A"]',updated_at:timestamp}],
      account_problem_facts:[{problem_id:'private::A',value:JSON.stringify({row:{id:'private::A',title:'私有题目'},statement:{markdown:'题面 🐈',samples:[{input:'2\n',output:'2\n'}]}}),updated_at:timestamp}],
    },publicAccounts:{}};
    const raw=Buffer.from(JSON.stringify(logical));
    const envelope={format:'tb-account-state-gzip-v1',payload:gzipSync(raw).toString('base64'),
      sha256:createHash('sha256').update(raw).digest('hex'),uncompressedBytes:raw.length};
    assert(raw.length>500000);
    assert(envelope.payload.length<raw.length/10);
    const saved=await call('/v1/accounts/state',{revision:0,state:envelope},auth,'PUT');
    assert.equal(saved.status,200); assert.equal(saved.value.revision,1);
    const progress={level:7,tier:'钻石',rankTier:null,rankScore:null,titles:[]};
    assert.equal((await call('/v1/profile',{publicProgress:progress},auth,'PUT')).status,200);
    const migration=await readFile(new URL('../mysql/005_account_state.sql',import.meta.url),'utf8');
    for (const sql of migration.split(';').map(value=>value.trim()).filter(Boolean)) await f.STORE.pool.query(sql);
    const publicMigration=await readFile(new URL('../mysql/006_public_progress.sql',import.meta.url),'utf8');
    for (const sql of publicMigration.split(';').map(value=>value.trim()).filter(Boolean)) await f.STORE.pool.query(sql);
    assert.deepEqual(await f.STORE.publicProgress(auth.userId),progress);
    const afterMigration=await f.STORE.accountState(auth.userId);
    assert.equal(afterMigration.revision,1);
    assert.deepEqual(JSON.parse(gunzipSync(Buffer.from(afterMigration.state.payload,'base64')).toString('utf8')),logical);
    const attempts=await Promise.allSettled([1,2].map(()=>f.STORE.saveAccountState(auth.userId,tokenHash(auth.token),
      Math.floor(f.env.TEST_NOW/1000),1,envelope,timestamp)));
    assert.equal(attempts.filter(result=>result.status==='fulfilled').length,1);
    assert.equal(attempts.filter(result=>result.status==='rejected'&&result.reason.status===409).length,1);
    assert.equal((await f.STORE.accountState(auth.userId)).revision,2);
    const second=await call('/v1/accounts/login',{loginId:signup.loginId,password:signup.password});
    const next={userId:second.value.account.userId,token:second.value.token};
    assert.equal((await call('/v1/accounts/me',undefined,auth)).status,401);
    await assert.rejects(()=>f.STORE.saveAccountState(auth.userId,tokenHash(auth.token),
      Math.floor(f.env.TEST_NOW/1000),2,envelope,timestamp),error=>error.status===401);
    const received=await call('/v1/accounts/state',undefined,next);
    assert.equal(received.status,200); assert.deepEqual(received.value.state,envelope);
    const [sessions]=await f.STORE.pool.execute('SELECT COUNT(*) AS n FROM account_sessions WHERE user_id=?',[auth.userId]);
    assert.equal(Number(sessions[0].n),1);
  } finally { await f.close(); }
});
