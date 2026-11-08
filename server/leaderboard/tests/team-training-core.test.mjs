import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash, randomUUID} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {startFixture} from './local-server.mjs';
import {TeamTraining} from '../src/team-training.mjs';

const hash = value => createHash('sha256').update(value).digest('hex');
const now = Date.parse('2026-11-08T00:00:00Z');
const catalogue = {schema: 1, revision: 'isolated-catalogue', contests: [{id: 'codeforces:contest:123',
  title: 'Isolated partial contest', platform: 'Codeforces', problems: ['A', 'B', 'C'].map((letter, index) => ({
    id: 'fixture::' + letter, letter, title: 'Fixture ' + letter, url: 'https://codeforces.com/contest/123/problem/' + letter,
    problemKey: hash('codeforces.com/contest/123/problem/' + letter), available: index !== 1, problemType: 'standard'}))}]};

async function setup() {
  const fixture = await startFixture({now});
  const database = fixture.STORE.database;
  if (!database.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='team_lobby'").get())
    database.exec(readFileSync(new URL('./team-schema.sql', import.meta.url), 'utf8'));
  const execute = async (sql, args = []) => {
    const statement = database.prepare(sql);
    return /^\s*SELECT/i.test(sql) ? [statement.all(...args)] : [{affectedRows: Number(statement.run(...args).changes)}];
  };
  let pending = Promise.resolve();
  const transaction = action => {
    const next = pending.then(async () => {
      database.exec('BEGIN IMMEDIATE');
      try { const value = await action({execute});database.exec('COMMIT');return value; }
      catch (error) { database.exec('ROLLBACK');throw error; }
    });
    pending = next.catch(() => {});return next;
  };
  const team = new TeamTraining({execute, transaction}, 'sqlite', {catalogue});
  const accounts = [];
  for (let i = 0; i < 4; i++) {
    const loginId = 'team_core_' + i, password = 'team-isolated-password';
    const send = (path, body) => fetch(fixture.endpoint + path, {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
    const registered = await send('/v1/accounts/register', {loginId, nickname: loginId, password});
    assert.equal(registered.status, 201);
    const response = await send('/v1/accounts/login', {loginId, password});assert.equal(response.status, 200);
    const signed = await response.json();
    accounts.push({owner: signed.account.userId, token: signed.token, auth: hash(signed.token)});
  }
  const write = (account, action, body = {}, at = now) => team.write(account.owner, account.auth, action, {requestId: randomUUID(), ...body}, at);
  return {fixture, database, team, accounts, write};
}

async function readyRoom(f) {
  const [a, b, c] = f.accounts;
  let state = await f.write(a, 'create', {name: '三人练习'});
  const inviteCode = state.team.inviteCode;
  await f.write(b, 'join', {inviteCode});await f.write(c, 'join', {inviteCode});
  state = await f.team.read(a.owner, now);
  state = await f.write(a, 'configure', {teamRevision: state.team.revision, contestId: catalogue.contests[0].id, durationMinutes: 5});
  for (const account of [a, b, c]) state = await f.write(account, 'ready', {teamRevision: state.team.revision, ready: true});
  return f.write(a, 'start', {teamRevision: state.team.revision});
}

test('concurrent preparation shares one configuration token; native authorization binds the saved code and lease', async()=>{
  const f=await setup();
  try{
    const [a,b,c]=f.accounts;
    let value=await f.write(a,'create',{name:'并发准备'});
    await f.write(b,'join',{inviteCode:value.team.inviteCode});await f.write(c,'join',{inviteCode:value.team.inviteCode});
    value=await f.team.read(a.owner,now);
    value=await f.write(a,'configure',{teamRevision:value.team.revision,contestId:catalogue.contests[0].id,durationMinutes:5});
    const configurationRevision=value.team.configurationRevision;
    await Promise.all([a,b,c].map(account=>f.write(account,'ready',{ready:true,configurationRevision})));
    value=await f.team.read(a.owner,now);assert(value.team.members.every(m=>m.ready));
    value=await f.write(a,'configure',{teamRevision:value.team.revision,contestId:catalogue.contests[0].id,durationMinutes:6});
    await assert.rejects(f.write(b,'ready',{ready:true,configurationRevision}),{code:'TEAM_REVISION_CONFLICT'});
    for(const account of [a,b,c])value=await f.write(account,'ready',{ready:true,configurationRevision:value.team.configurationRevision});
    value=await f.write(a,'start',{teamRevision:value.team.revision});const roomId=value.room.id;
    value=await f.write(a,'claim',{roomId},now+4000);const leaseToken=value.room.lease.token;
    const code='// 中文🦆\nint main() {}';
    value=await f.write(a,'draft',{roomId,leaseToken,problemId:'fixture::A',revision:0,language:'cpp17',code},now+4000);
    const request={roomId,leaseToken,problemId:'fixture::A',revision:1,language:'cpp17',inputSha256:hash(code),purpose:'submit'};
    const granted=await f.write(a,'authorize',request,now+4000);
    assert.equal(granted.ack.authorization.inputSha256,hash(code));assert.equal(granted.ack.authorization.expiresAt,now+19000);
    assert.equal(granted.ack.authorization.url,catalogue.contests[0].problems[0].url);
    await assert.rejects(f.write(b,'authorize',request,now+4000),{code:'TEAM_EDITOR_CHANGED'});
    await assert.rejects(f.write(a,'authorize',{...request,inputSha256:hash('other code')},now+4000),{code:'TEAM_DOCUMENT_CHANGED'});
    await assert.rejects(f.write(a,'authorize',{...request,revision:0},now+4000),{code:'TEAM_DOCUMENT_CHANGED'});
    await assert.rejects(f.write(a,'authorize',request,now+20000),{code:'TEAM_EDITOR_CHANGED'});
    const foreign=await f.team.history(c.owner,now+5000,roomId,'fixture::C');assert.equal(foreign.room.problemId,'fixture::C');assert.equal(foreign.room.document.code,'');
    assert.equal((await f.team.read(a.owner,now+5000)).room.problemId,'fixture::A','history reads must not change the live selection');
    await assert.rejects(f.team.history(f.accounts[3].owner,now+5000,roomId,'fixture::A'),{status:403});
  }finally{await f.fixture.close();}
});

test('verified repeat AC counts once per room task; pending, old, forged and cross-owner receipts never score',async()=>{
  const f=await setup();
  try{
    const [a,b]=f.accounts;let state=await readyRoom(f),roomId=state.room.id;
    f.database.prepare('INSERT INTO official_ac_events(user_id,problem_key,event_id,accepted_at,accepted_day,difficulty,received_at) VALUES(?,?,?,?,?,?,?)')
      .run(a.owner,catalogue.contests[0].problems[0].problemKey,hash('old-real-first'),new Date(now-86400000).toISOString(),'2026-11-07',1200,new Date(now).toISOString());
    state=await f.write(a,'claim',{roomId},now+4000);const leaseToken=state.room.lease.token;
    await f.write(a,'draft',{roomId,leaseToken,problemId:'fixture::A',revision:0,language:'cpp17',code:'int main() {}'},now+4000);
    const grant=await f.write(a,'authorize',{roomId,leaseToken,problemId:'fixture::A',revision:1,language:'cpp17',purpose:'submit',inputSha256:hash('int main() {}')},now+4000);
    const intentId=grant.ack.authorization.id,body={requestId:randomUUID(),intentId,submissionId:'123456',handle:'fixtureCF'};
    let calls=0;
    f.team.verifyReceipt=async request=>{calls++;if(calls===1)throw Error('isolated public source outage');return {
      ...request,verdict:'AC',submittedAt:now+4000,source:'isolated-public-provider',proofSha256:hash('isolated-native-proof')};};
    assert.equal((await f.team.nativeReceipt(a.owner,a.auth,body,now+5000)).receipt.status,'pending');
    assert.equal((await f.team.read(a.owner,now+5000)).room.score.totalScore,0);
    await assert.rejects(f.team.nativeReceipt(a.owner,a.auth,{...body,verdict:'AC'},now+5000),{code:'TEAM_RECEIPT_INVALID'});
    await assert.rejects(f.team.nativeReceipt(b.owner,b.auth,body,now+5000),{code:'TEAM_INTENT_INVALID'});
    const confirmed=await f.team.nativeReceipt(a.owner,a.auth,body,now+5000);assert.equal(confirmed.receipt.verdict,'AC');
    assert.equal((await f.team.read(a.owner,now+5000)).room.score.totalScore,1);
    await f.team.nativeReceipt(a.owner,a.auth,body,now+6000);assert.equal(calls,2,'acknowledged retries do not query the provider again');
    assert.equal(f.database.prepare('SELECT COUNT(*) AS n FROM team_native_receipts').get().n,1);
    assert.equal(f.database.prepare('SELECT COUNT(*) AS n FROM official_ac_events').get().n,1,'repeat room facts must not duplicate first-AC rewards');
    assert.equal((await f.team.standings(now+6000)).entries[0].totalScore,1);
    await assert.rejects(f.team.nativeReceipt(a.owner,a.auth,{...body,submissionId:'123457'},now+6000),{code:'TEAM_RECEIPT_ALREADY_BOUND'});
    const otherGrant=await f.write(a,'authorize',{roomId,leaseToken,problemId:'fixture::A',revision:1,language:'cpp17',purpose:'submit',inputSha256:hash('int main() {}')},now+6000);
    const second={...body,requestId:randomUUID(),intentId:otherGrant.ack.authorization.id,submissionId:'123457'};
    f.team.verifyReceipt=async request=>({...request,verdict:'AC',submittedAt:now-1000,source:'isolated-public-provider'});
    await assert.rejects(f.team.nativeReceipt(a.owner,a.auth,second,now+7000),{code:'TEAM_RECEIPT_MISMATCH'});
    f.team.verifyReceipt=async request=>({...request,verdict:'WA',submittedAt:now+6000,source:'isolated-public-provider'});
    await f.team.nativeReceipt(a.owner,a.auth,second,now+7000);
    assert.equal((await f.team.read(a.owner,now+7000)).room.score.totalScore,1);
  }finally{await f.fixture.close();}
});

test('authenticated accounts join exactly one team; concurrent joins cannot exceed three', async () => {
  const f = await setup();
  try {
    const [a, ...others] = f.accounts;
    const requestId = randomUUID();
    const first = await f.write(a, 'create', {name: '真实账号隔离测试', requestId});
    const duplicate = await f.write(a, 'create', {name: '真实账号隔离测试', requestId});
    assert.equal(duplicate.team.id, first.team.id);
    await assert.rejects(f.write(a, 'create', {name: '换一支队伍', requestId}), {status: 409});
    const joins = await Promise.allSettled(others.map(account => f.write(account, 'join', {inviteCode: first.team.inviteCode})));
    assert.equal(joins.filter(r => r.status === 'fulfilled').length, 2);
    assert.equal(joins.filter(r => r.status === 'rejected')[0].reason.code, 'TEAM_TEAM_FULL');
    const current = await f.team.read(a.owner, now);assert.equal(current.team.members.length, 3);
    const joined = others[joins.findIndex(r => r.status === 'fulfilled')];
    await assert.rejects(f.write(joined, 'create', {name: '重复入队'}), {status: 409});
    await assert.rejects(f.team.write(a.owner, 'wrong-session', 'leave', {requestId: randomUUID(), teamRevision: current.team.revision}, now), {status: 401});
    assert.equal(f.database.prepare('SELECT COUNT(*) AS n FROM teams').get().n, 1);
    assert.equal(f.database.prepare('SELECT COUNT(*) AS n FROM official_ac_events').get().n, 0);
  } finally { await f.fixture.close(); }
});

test('server time, single editor, Unicode CAS drafts, expired lease recovery and missing task guard', async () => {
  const f = await setup();
  try {
    const [a, b, c] = f.accounts;
    let state = await readyRoom(f);const roomId = state.room.id;
    assert.equal(state.room.status, 'countdown');
    assert.equal(state.room.problems.length, 3);assert.equal(state.room.problems[1].available, false);
    await assert.rejects(f.write(a, 'claim', {roomId}), {status: 409});
    const at = now + 3000;
    const claims = await Promise.allSettled([a, b].map(account => f.write(account, 'claim', {roomId}, at)));
    assert.equal(claims.filter(r => r.status === 'fulfilled').length, 1);
    const editor = [a, b][claims.findIndex(r => r.status === 'fulfilled')];
    const viewer = editor === a ? b : a;
    state = await f.team.read(editor.owner, at);const leaseToken = state.room.lease.token;
    const publicLease = (await f.team.read(viewer.owner, at)).room.lease;
    assert.equal(publicLease.token, undefined);
    const body = {roomId, leaseToken, problemId: 'fixture::A', revision: 0, code: '// 中文🦆\nint main() {}', language: 'cpp17'};
    const writes = await Promise.allSettled([f.write(editor, 'draft', body, at), f.write(editor, 'draft', {...body, code: '// stale'}, at)]);
    assert.equal(writes.filter(r => r.status === 'fulfilled').length, 1);
    state = await f.team.read(editor.owner, at);assert.equal(state.room.document.code, body.code);
    assert.equal(state.room.document.revision, 1);
    await assert.rejects(f.write(viewer, 'draft', {...body, revision: 1}, at), {status: 409});
    await assert.rejects(f.write(editor, 'select', {roomId, leaseToken, problemId: 'fixture::B'}, at), {status: 422});
    await assert.rejects(f.write(editor, 'draft', {...body, revision: 1, code: '中'.repeat(22000)}, at), {status: 400});
    const recovered = await f.write(c, 'claim', {roomId}, at + 15001);
    assert.equal(recovered.room.lease.owner, c.owner);
    await assert.rejects(f.write(editor, 'draft', {...body, revision: 1}, at + 15001), {status: 409});
    assert.equal((await f.team.read(c.owner, at + 15001)).room.document.code, body.code);
    await assert.rejects(f.write(c, 'leave', {teamRevision: state.team.revision}, at + 15001), {status: 409});
    const expired = await f.team.read(a.owner, state.room.deadline);
    assert.equal(expired.room.status, 'finished');assert.equal(expired.room.lease, null);
    await assert.rejects(f.write(c, 'draft', {...body, leaseToken: recovered.room.lease.token, revision: 1}, state.room.deadline), {status: 409});
  } finally { await f.fixture.close(); }
});

test('only stored official AC facts score; old private code remains limited to actual participants', async () => {
  const f = await setup();
  try {
    const [a, b, c, outsider] = f.accounts;
    let state = await readyRoom(f);const roomId = state.room.id, at = now + 4000;
    state = await f.write(a, 'claim', {roomId}, at);
    await f.write(a, 'draft', {roomId, leaseToken: state.room.lease.token, problemId: 'fixture::A', revision: 0, code: 'private shared code', language: 'python3'}, at);
    const add = (owner, key, when) => f.database.prepare('INSERT INTO official_ac_events(user_id,problem_key,event_id,accepted_at,accepted_day,difficulty,received_at) VALUES(?,?,?,?,?,?,?)')
      .run(owner, key, hash(owner + key), new Date(when).toISOString(), '2026-11-08', 1200, new Date(at).toISOString());
    add(a.owner, catalogue.contests[0].problems[0].problemKey, at);
    add(b.owner, catalogue.contests[0].problems[0].problemKey, at + 1);
    add(c.owner, catalogue.contests[0].problems[2].problemKey, now - 1000);
    add(outsider.owner, catalogue.contests[0].problems[2].problemKey, at);
    state = await f.team.read(a.owner, at + 2);assert.equal(state.room.score.totalScore, 1);
    await assert.rejects(f.team.history(outsider.owner, at, roomId), {status: 403});
    state = await f.write(a, 'finish', {roomId}, at + 5);
    assert.equal(state.room.status, 'finished');assert.equal(state.room.document.code, 'private shared code');
    const oldMemberHistory = await f.team.history(b.owner, at + 6, roomId);assert.equal(oldMemberHistory.room.document.code, 'private shared code');
    await f.write(b, 'leave', {teamRevision: state.team.revision}, at + 6);
    const joined = await f.write(outsider, 'join', {inviteCode: state.team.inviteCode}, at + 7);
    assert.equal(joined.team.members.length, 3);assert.equal(joined.room, null);
    await assert.rejects(f.team.history(outsider.owner, at + 7, roomId), {status: 403});
    assert.equal((await f.team.history(b.owner, at + 8, roomId)).room.document.code, 'private shared code');
    assert.equal(f.database.prepare('SELECT COUNT(*) AS n FROM team_rooms').get().n, 1);
  } finally { await f.fixture.close(); }
});

test('production HTTP routes bind the authenticated owner and preserve a full 64 KiB escaped draft', async () => {
  const f = await setup();
  try {
    f.fixture.STORE.teams = f.team;
    const [a, b, c, outsider] = f.accounts;
    const send = async (account, path, body) => {
      const response = await fetch(f.fixture.endpoint + '/v1/team-training/' + path, {
        method: body === undefined ? 'GET' : 'POST', headers: {'Content-Type': 'application/json',
          'X-TB-User': account.owner, Authorization: 'Bearer ' + account.token},
        ...(body === undefined ? {} : {body: JSON.stringify({requestId: randomUUID(), ...body})})});
      return {status: response.status, value: await response.json()};
    };
    const post = async (account, path, body = {}) => {
      const result = await send(account, path, body);assert.equal(result.status, 200, JSON.stringify(result.value));return result.value;
    };
    assert.equal((await (await fetch(f.fixture.endpoint + '/v1/health')).json()).teamTrainingProtocol, 1);
    assert.equal((await send(a, 'create', {name: '伪造成绩', totalScore: 999})).status, 400);
    assert.equal((await send(a, 'catalogue')).value.contests[0].id, catalogue.contests[0].id);
    let state = await post(a, 'create', {name: 'HTTP 三人队'});
    await post(b, 'join', {inviteCode: state.team.inviteCode});state = await post(c, 'join', {inviteCode: state.team.inviteCode});
    state = await post(a, 'configure', {teamRevision: state.team.revision, contestId: catalogue.contests[0].id, durationMinutes: 5});
    for (const account of [a, b, c]) state = await post(account, 'ready', {teamRevision: state.team.revision, ready: true});
    state = await post(a, 'start', {teamRevision: state.team.revision});
    f.fixture.env.TEST_NOW = state.room.startedAt;
    state = await post(a, 'claim', {roomId: state.room.id});
    const code = '\\'.repeat(65536), requestId = randomUUID();
    const body = {requestId, roomId: state.room.id, leaseToken: state.room.lease.token,
      problemId: 'fixture::A', revision: 0, language: 'cpp17', code};
    const saved = await post(a, 'draft', body);assert.equal(saved.room.document.code, code);
    assert.equal(saved.ack.inputSha256, hash(code));
    const duplicate = await post(a, 'draft', body);assert.equal(duplicate.room.document.revision, 1);
    const stale = await send(a, 'draft', {...body, requestId: randomUUID(), code: 'stale'});
    assert.equal(stale.status, 409);assert.equal(stale.value.code, 'TEAM_REVISION_CONFLICT');
    assert.equal((await send(b, 'state')).value.room.document.code, code);
    assert.equal((await send(outsider, 'state')).value.room, null);
    assert.equal((await send(outsider, 'history/' + state.room.id)).status, 403);
    const board = (await send(outsider, 'standings')).value;
    assert.equal(board.entries[0].totalScore, 0);
    assert(!JSON.stringify(board).includes(state.team.inviteCode));
    const spoof = await send({...a, owner: outsider.owner}, 'state');assert.equal(spoof.status, 401);
    assert.equal(spoof.value.code, 'TEAM_SESSION_EXPIRED');
  } finally { await f.fixture.close(); }
});

test('profile changes wait for an in-flight shared transaction in the SQLite HTTP fixture', async () => {
  const f = await setup();let release, running;
  try {
    const [a] = f.accounts;
    let entered;const inside = new Promise(resolve => {entered = resolve;});
    const hold = new Promise(resolve => {release = resolve;});
    running = f.fixture.STORE.teams.transaction(async () => {entered();await hold;});
    await inside;
    let completed = false;
    const profile = fetch(f.fixture.endpoint + '/v1/profile', {method: 'PUT',
      headers: {'Content-Type': 'application/json', 'X-TB-User': a.owner, Authorization: 'Bearer ' + a.token},
      body: JSON.stringify({nickname: '串行资料更新'})}).then(async response => {
      completed = true;return {status: response.status, value: await response.json()};
    });
    await new Promise(resolve => setTimeout(resolve, 40));
    assert.equal(completed, false, 'Profile write must wait for the transaction queue');
    release();await running;const result = await profile;
    assert.equal(result.status, 200);assert.equal(result.value.nickname, '串行资料更新');
  } finally {release?.();await running;await f.fixture.close();}
});
