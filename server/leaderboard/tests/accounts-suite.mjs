import test from 'node:test';
import assert from 'node:assert/strict';
import { randomUUID, createHash } from 'node:crypto';
import { tokenHash } from '../src/accounts.mjs';

async function call(f, path, body, auth, method = body === undefined ? 'GET' : 'POST') {
  const response = await fetch(f.endpoint + path, { method, headers: { 'Content-Type': 'application/json', 'X-TB-State-Protocol': '1',
    ...(auth ? { 'X-TB-User': auth.userId, Authorization: 'Bearer ' + auth.token } : {}) },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }) });
  return { status: response.status, value: await response.json() };
}
const signup = { nickname: '星河', loginId: 'star_user', password: 'a-long-fixture-password' };
const credential = result => ({ userId: result.value.account.userId, token: result.value.token });

export function accountsSuite(startFixture) {
  test('public avatars are shared by hash, XP is bounded and private state stays private', async()=>{
    const f=await startFixture();
    const avatar='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jPqEAAAAASUVORK5CYII=';
    try {
      await call(f,'/v1/accounts/register',signup);
      await call(f,'/v1/accounts/register',{...signup,loginId:'another_user',nickname:'另一个人'});
      const a=credential(await call(f,'/v1/accounts/login',{loginId:signup.loginId,password:signup.password}));
      const b=credential(await call(f,'/v1/accounts/login',{loginId:'another_user',password:signup.password}));
      const progress={level:9,tier:'黑铁',rankTier:null,rankScore:null,titles:[],currentLevelXp:75,nextLevelXp:200};
      const saved=await call(f,'/v1/profile',{publicProgress:progress,avatarData:avatar},a,'PUT');
      assert.equal(saved.status,200);assert.match(saved.value.avatarHash,/^[a-f0-9]{64}$/);
      const board=await call(f,'/v1/leaderboard?period=total',undefined,b);
      const user=board.value.entries.find(item=>item.userId===a.userId);
      assert.equal(user.avatarHash,saved.value.avatarHash);assert.deepEqual(user.publicProgress,progress);
      assert(!JSON.stringify(board).includes(avatar),'images do not bloat ranking payloads');
      assert.equal((await call(f,'/v1/avatars/'+a.userId,undefined,b)).value.avatarData,avatar);
      assert.equal((await call(f,'/v1/avatars/'+a.userId)).status,401);
      const {currentLevelXp,nextLevelXp,...legacy}=progress;
      await call(f,'/v1/profile',{publicProgress:legacy},a,'PUT');
      assert.equal((await call(f,'/v1/profile',undefined,a)).value.publicProgress.currentLevelXp,75);
      for(const bad of ['https://example.com/a.png','data:image/svg+xml;base64,PHN2Zy8+',avatar.replace('image/png','image/jpeg'),'x'.repeat(49*1024)])assert.equal((await call(f,'/v1/profile',{avatarData:bad},a,'PUT')).status,400);
      assert.equal((await call(f,'/v1/profile',{publicProgress:{...progress,currentLevelXp:201}},a,'PUT')).status,400);
      await call(f,'/v1/profile',{avatarData:''},a,'PUT');
      assert.deepEqual((await call(f,'/v1/avatars/'+a.userId,undefined,b)).value,{avatarData:'',avatarHash:null});
      assert.equal((await call(f,'/v1/avatars/'+b.userId,undefined,a)).value.avatarData,'');
    } finally {await f.close();}
  });
  test('one ranking query returns at most 100 visible rows while preserving a caller outside that page', async () => {
    const f = await startFixture();
    try {
      const ids = [];
      for (let index = 0; index < 102; index++) {
        const userId = randomUUID(), timestamp = new Date(Date.parse('2026-10-16T00:00:00Z') + index * 1000).toISOString();
        await f.STORE.createAccount({ userId, nickname: 'fixture-' + index, retiredHash: 'a'.repeat(64), loginId: 'fixture_' + index,
          passwordHash: 'unused-fixture-hash', timestamp });
        await f.STORE.recordLogin(userId, '2026-10-16', timestamp);
        ids.push(userId);
      }
      const board = await f.STORE.rankings(ids[101], { start: '2026-10-16', end: '2026-10-17' }, '2026-10-16');
      assert.equal(board.rows.length, 100);
      assert.deepEqual(board.rows.map(row => row.rank), Array.from({ length: 100 }, (_, index) => index + 1));
      assert.equal(board.own.user_id, ids[101]); assert.equal(board.own.rank, 102); assert.equal(board.own.count, 0);
      const absent = await f.STORE.rankings(ids[101], { start: '2026-10-17', end: '2026-10-18' }, '2026-10-17');
      assert.deepEqual(absent.rows, []); assert.equal(absent.own, null);
    } finally { await f.close(); }
  });
  test('rankings publish bounded growth and a stable public ID without exposing login or private state', async () => {
    const f = await startFixture({ now: Date.now() });
    try {
      await call(f, '/v1/accounts/register', signup);
      const auth = credential(await call(f, '/v1/accounts/login', { loginId: signup.loginId, password: signup.password }));
      let board = (await call(f, '/v1/leaderboard', undefined, auth)).value;
      assert.equal(board.self.publicProgress, null);
      assert.equal(board.self.publicId, 'TB-' + auth.userId.replaceAll('-', '').toUpperCase());
      const progress = { level: 10, tier: '王者', rankTier: '黄金', rankScore: 1560,
        titles: [{ id: 'ac-500', name: '破题先锋', category: 'ac', target: 500 }, { id: 'streak-30', name: '月度恒心', category: 'streak', target: 30 }] };
      assert.equal((await call(f, '/v1/profile', { publicProgress: progress }, auth, 'PUT')).status, 200);
      assert.deepEqual((await call(f, '/v1/profile', undefined, auth)).value.publicProgress, progress);
      await call(f, '/v1/profile', { nickname: '新的昵称' }, auth, 'PUT');
      // Ranking reads join the small summary table and must not read/decompress
      // private state, even when a login snapshot is large or unavailable.
      f.STORE.accountState = () => { throw new Error('Private state must not be read by rankings'); };
      board = (await call(f, '/v1/leaderboard', undefined, auth)).value;
      assert.equal(board.self.nickname, '新的昵称');
      assert.deepEqual(board.self.publicProgress, progress);
      assert.equal(board.self.count, 0);
      assert(!JSON.stringify(board).includes(signup.loginId));
      assert(!JSON.stringify(board).includes('loginId'));
      const previousId = board.self.publicId;
      const next = credential(await call(f, '/v1/accounts/login', { loginId: signup.loginId, password: signup.password }));
      assert.equal((await call(f, '/v1/profile', { publicProgress: progress }, auth, 'PUT')).status, 401);
      await assert.rejects(() => f.STORE.savePublicProfile(auth.userId, tokenHash(auth.token), Math.floor(f.env.TEST_NOW / 1000), 'stale', progress, new Date().toISOString()), error => error.status === 401);
      board = (await call(f, '/v1/leaderboard', undefined, next)).value;
      assert.equal(board.self.publicId, previousId);
      assert.equal(board.self.nickname, '新的昵称');
      assert.deepEqual(board.self.publicProgress, progress);
    } finally { await f.close(); }
  });
  test('public growth rejects unknown fields, excess medals and malformed values without partial profile writes', async () => {
    const f = await startFixture({ now: Date.now() });
    try {
      await call(f, '/v1/accounts/register', signup);
      const auth = credential(await call(f, '/v1/accounts/login', { loginId: signup.loginId, password: signup.password }));
      const progress = { level: 7, tier: '钻石', rankTier: null, rankScore: null, titles: [] };
      const title = { id: 'ac-500', name: '破题先锋', category: 'ac', target: 500 };
      const invalid = [null, [], {}, { ...progress, level: 0 }, { ...progress, level: 7.5 }, { ...progress, level: 101 },
        { ...progress, tier: 'x'.repeat(25) }, { ...progress, tier: '\u0000bad' }, { ...progress, rankScore: -1 },
        { ...progress, rankScore: 1 }, { ...progress, rankTier: '王者', rankScore: 1000001 },
        { ...progress, loginId: signup.loginId }, { ...progress, titles: Array(3).fill(title) },
        { ...progress, titles: [title, { ...title, id: 'ac-1000', target: 1000 }] },
        { ...progress, titles: [{ ...title, name: 'x'.repeat(25) }] },
        { ...progress, titles: [{ ...title, secret: 'PRIVATE' }] }];
      for (const publicProgress of invalid) assert.equal((await call(f, '/v1/profile', { nickname: 'must not save', publicProgress }, auth, 'PUT')).status, 400);
      assert.equal((await call(f, '/v1/profile', {}, auth, 'PUT')).status, 400);
      assert.equal((await call(f, '/v1/profile', { publicProgress: progress, userId: randomUUID() }, auth, 'PUT')).status, 400);
      let profile = (await call(f, '/v1/profile', undefined, auth)).value;
      assert.equal(profile.nickname, signup.nickname); assert.equal(profile.publicProgress, null);
      assert.equal((await call(f, '/v1/profile', { publicProgress: progress }, auth, 'PUT')).status, 200);
      profile = (await call(f, '/v1/profile', undefined, auth)).value;
      assert.deepEqual(profile.publicProgress, progress);
    } finally { await f.close(); }
  });
  test('concurrent signup and password changes cannot overwrite another account or keep old sessions', async () => {
    const f = await startFixture({ now: Date.now() });
    try {
      const created = await Promise.all([call(f, '/v1/accounts/register', signup), call(f, '/v1/accounts/register', signup)]);
      assert.deepEqual(created.map(value => value.status).sort(), [201, 409]);
      const first = await call(f, '/v1/accounts/login', { loginId: signup.loginId, password: signup.password });
      const auth = credential(first);
      const changes = await Promise.all(['next-password-a', 'next-password-b'].map(newPassword =>
        call(f, '/v1/accounts/password', { oldPassword: signup.password, newPassword }, auth)));
      assert.equal(changes.filter(value => value.status === 200).length, 1);
      assert(changes.every(value => [200, 401, 409].includes(value.status)));
      assert.equal((await call(f, '/v1/accounts/me', undefined, auth)).status, 401);
      const winner = changes.find(value => value.status === 200);
      assert.equal((await call(f, '/v1/accounts/me', undefined, credential(winner))).status, 200);
    } finally { await f.close(); }
  });
  test('registration requires nickname, login ID and password; duplicate and malformed fields fail', async () => {
    const f = await startFixture();
    try {
      for (const bad of [{ ...signup, nickname: '' }, { ...signup, loginId: 'a b' }, { ...signup, password: 'short' },
        { ...signup, userId: randomUUID() }, { ...signup, nickname: '\u0000bad' }]) {
        assert.equal((await call(f, '/v1/accounts/register', bad)).status, 400);
      }
      const result = await call(f, '/v1/accounts/register', signup);
      assert.equal(result.status, 201); assert.equal(result.value.account.displayName, '星河');
      assert(!JSON.stringify(result.value).includes('password')); assert(!result.value.token);
      assert.equal((await call(f, '/v1/accounts/register', { ...signup, loginId: 'STAR_USER' })).status, 409);
      assert.equal((await call(f, '/v1/profile/register', {})).status, 410);
      assert.equal((await call(f, '/v1/leaderboard')).status, 401);
      const account = await f.STORE.findAccount('star_user');
      assert(account.password_hash.startsWith('scrypt$')); assert(!account.password_hash.includes(signup.password));
    } finally { await f.close(); }
  });
  test('nicknames are unique across registration and rename, including normalized Unicode and races', async () => {
    const f = await startFixture();
    try {
      assert.equal((await call(f, '/v1/accounts/register', {...signup, nickname:'星河 TB'})).status,201);
      const duplicate = await call(f, '/v1/accounts/register', {...signup,loginId:'second_user',nickname:'星河　ＴＢ'});
      assert.equal(duplicate.status,409); assert.match(duplicate.value.error,/昵称/);
      assert.equal((await call(f,'/v1/accounts/register',{...signup,loginId:'second_user',nickname:'另一个昵称'})).status,201);
      const login=await call(f,'/v1/accounts/login',{loginId:'second_user',password:signup.password});
      const auth=credential(login);
      assert.equal((await call(f,'/v1/profile',{nickname:' 星河 tb '},auth,'PUT')).status,409);
      assert.equal((await call(f,'/v1/profile',undefined,auth,'GET')).value.nickname,'另一个昵称');
      assert.equal((await call(f,'/v1/profile',{nickname:'另一个昵称'},auth,'PUT')).status,200);
      const race=await Promise.all(['racer_one','racer_two'].map(loginId=>call(f,'/v1/accounts/register',{...signup,loginId,nickname:'同一个新昵称'})));
      assert.deepEqual(race.map(item=>item.status).sort(),[201,409]);
    } finally { await f.close(); }
  });
  test('unchanged authenticated state resumes without reading the large snapshot', async () => {
    const f = await startFixture();
    try {
      await call(f,'/v1/accounts/register',signup);
      const auth=credential(await call(f,'/v1/accounts/login',{loginId:signup.loginId,password:signup.password}));
      const state={format:'tb-account-state-v1',tables:{drafts:[{problem_id:'fixture',context:'',code:'x'.repeat(20000),saved_at:new Date().toISOString()}]},publicAccounts:{}};
      assert.equal((await call(f,'/v1/accounts/state',{revision:0,state},auth,'PUT')).status,200);
      let reads=0;const original=f.STORE.accountState.bind(f.STORE);
      f.STORE.accountState=(...args)=>{reads++;return original(...args);};
      const headers={'X-TB-User':auth.userId,Authorization:'Bearer '+auth.token,'X-TB-State-Revision':'1'};
      const answer=await fetch(f.endpoint+'/v1/accounts/state',{headers});
      assert.deepEqual(await answer.json(),{revision:1,unchanged:true});assert.equal(reads,0);
      const mismatch=await fetch(f.endpoint+'/v1/accounts/state',{headers:{...headers,'X-TB-State-Revision':'2'}});
      assert.deepEqual((await mismatch.json()).state,state);assert.equal(reads,1);
      const unauthenticated=await fetch(f.endpoint+'/v1/accounts/state',{headers:{'X-TB-State-Revision':'1'}});
      assert.equal(unauthenticated.status,401);
    } finally { await f.close(); }
  });
  test('login, logout, session expiry and changing password revoke old credentials', async () => {
    const f = await startFixture({ now: Date.now() });
    try {
      await call(f, '/v1/accounts/register', signup);
      for (const loginId of ['missing_user', signup.loginId]) {
        const wrong = await call(f, '/v1/accounts/login', { loginId, password: 'incorrect-password' });
        assert.equal(wrong.status, 401); assert.equal(wrong.value.error, '登录号或密码错误');
      }
      const first = await call(f, '/v1/accounts/login', { loginId: 'STAR_USER', password: signup.password });
      const second = await call(f, '/v1/accounts/login', { loginId: signup.loginId, password: signup.password });
      assert.equal(first.status, 200);
      const a = credential(first), b = credential(second);
      assert.equal((await call(f, '/v1/accounts/me', undefined, a)).status, 401, 'A new login revokes the previous device');
      assert.equal((await call(f, '/v1/accounts/me', undefined, b)).status, 200);
      assert.equal((await call(f, '/v1/accounts/password', { oldPassword: 'wrong-password', newPassword: 'next-password' }, b)).status, 400);
      const changed = await call(f, '/v1/accounts/password', { oldPassword: signup.password, newPassword: 'next-password' }, b);
      assert.equal(changed.status, 200);
      for (const old of [a, b]) assert.equal((await call(f, '/v1/accounts/me', undefined, old)).status, 401);
      assert.equal((await call(f, '/v1/accounts/login', { loginId: signup.loginId, password: signup.password })).status, 401);
      const current = credential(changed);
      const stored = await f.STORE.findSession(current.userId, tokenHash(current.token), Math.floor(f.env.TEST_NOW / 1000));
      assert(stored); assert(!JSON.stringify(stored).includes(current.token));
      assert.equal((await call(f, '/v1/accounts/logout', {}, current)).status, 200);
      assert.equal((await call(f, '/v1/accounts/me', undefined, current)).status, 401);
      const third = await call(f, '/v1/accounts/login', { loginId: signup.loginId, password: 'next-password' });
      f.env.TEST_NOW = third.value.expiresAt * 1000;
      assert.equal((await call(f, '/v1/accounts/me', undefined, credential(third))).status, 401);
      assert.equal((await call(f, '/v1/accounts/forgot-password', {})).status, 401);
    } finally { await f.close(); }
  });
  test('legacy records and admin role can be claimed only once with the original secret', async () => {
    const f = await startFixture({ now: Date.now() });
    try {
      const old = { userId: randomUUID(), token: 'legacy-secret-'.repeat(4) }, timestamp = new Date().toISOString();
      await f.STORE.createUser(old.userId, '旧昵称', tokenHash(old.token), timestamp);
      if (f.STORE.pool) await f.STORE.pool.execute('INSERT INTO ranking_admins VALUES(?,?)', [old.userId, timestamp]);
      else f.STORE.database.prepare('INSERT INTO ranking_admins VALUES(?,?)').run(old.userId, timestamp);
      const key = createHash('sha256').update('old-problem').digest('hex');
      await f.STORE.recordEvents(old.userId, [{ problemKey: key, eventId: key, acceptedAt: timestamp, day: timestamp.slice(0, 10), difficulty: 800 }], timestamp);
      assert.equal((await call(f, '/v1/profile', undefined, old)).status, 401);
      assert.equal((await call(f, '/v1/accounts/register', signup, { ...old, token: 'wrong-secret'.repeat(4) })).status, 401);
      const claimed = await call(f, '/v1/accounts/register', signup, old);
      assert.equal(claimed.value.account.userId, old.userId); assert.equal(claimed.value.account.isAdmin, true);
      assert.equal((await call(f, '/v1/accounts/register', { ...signup, loginId: 'another_user' }, old)).status, 401);
      const login = await call(f, '/v1/accounts/login', { loginId: signup.loginId, password: signup.password });
      const board = await call(f, '/v1/leaderboard?period=total', undefined, credential(login));
      assert.equal(board.value.self.count, 1); assert.equal(board.value.entries[0].nickname, '星河');
      assert.equal(await f.countEvents(), 1);
    } finally { await f.close(); }
  });
  test('login attempts are limited per account and do not disclose password hashes', async () => {
    const f = await startFixture({ now: Date.now() });
    try {
      await call(f, '/v1/accounts/register', signup);
      const answers = await Promise.all(Array.from({ length: 12 }, () => call(f, '/v1/accounts/login', { loginId: signup.loginId, password: 'incorrect-password' })));
      assert.equal(answers.filter(value => value.status === 401).length, 10);
      assert.equal(answers.filter(value => value.status === 429).length, 2);
      assert(!JSON.stringify(answers).includes('scrypt'));
    } finally { await f.close(); }
  });
  test('account state is private, revision guarded, durable across takeover, and rejects secrets', async () => {
    const f = await startFixture({ now: Date.now() });
    try {
      await call(f, '/v1/accounts/register', signup);
      const first = await call(f, '/v1/accounts/login', { loginId: signup.loginId, password: signup.password });
      const a = credential(first);
      const state = { format: 'tb-account-state-v1', tables: { drafts: [{problem_id: 'fixture::A', context: '', code: 'private code', saved_at: new Date().toISOString()}] }, publicAccounts: {} };
      assert.deepEqual((await call(f, '/v1/accounts/state', undefined, a)).value, {revision: 0, state: null});
      const saved = await call(f, '/v1/accounts/state', {revision: 0, state}, a, 'PUT');
      assert.equal(saved.status, 200); assert.equal(saved.value.revision, 1);
      const legacy = await fetch(f.endpoint + '/v1/accounts/login', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({loginId:signup.loginId,password:signup.password})});
      assert.equal(legacy.status,426); await legacy.text();
      assert.equal((await call(f,'/v1/accounts/me',undefined,a)).status,200,'A rejected old client does not revoke the active device');
      assert.equal((await call(f, '/v1/accounts/state', {revision: 0, state}, a, 'PUT')).status, 409);
      assert.equal((await call(f, '/v1/accounts/state', {revision: 1, state: {...state, tables: {...state.tables, ranking_profile: [{auth_token: 'secret'}]}}}, a, 'PUT')).status, 400);
      assert.equal((await call(f, '/v1/accounts/state', {revision: 1, state: {...state, publicAccounts: {codeforces: {platform: 'codeforces', handle: 'fixture', cookie: 'secret'}}}}, a, 'PUT')).status, 400);
      const second = await call(f, '/v1/accounts/login', { loginId: signup.loginId, password: signup.password });
      assert.equal((await call(f, '/v1/accounts/state', undefined, a)).status, 401);
      const b = credential(second);
      assert.deepEqual((await call(f, '/v1/accounts/state', undefined, b)).value, {revision: 1, state});
      // A request authenticated before takeover is checked again in the write transaction.
      await assert.rejects(() => f.STORE.saveAccountState(a.userId, tokenHash(a.token), Math.floor(f.env.TEST_NOW / 1000), 1, state, new Date().toISOString()), error => error.status === 401);
      await call(f, '/v1/accounts/register', {...signup, loginId: 'other_user', nickname: 'other user'});
      const other = credential(await call(f, '/v1/accounts/login', {loginId: 'other_user', password: signup.password}));
      assert.equal((await call(f, '/v1/accounts/state', undefined, other)).value.state, null);
      assert(!JSON.stringify((await call(f, '/v1/leaderboard', undefined, b)).value).includes('private code'));
    } finally { await f.close(); }
  });
  test('a user logged in today appears with zero AC, survives restart, and heartbeat marks a new Beijing day', async () => {
    const f = await startFixture({ now: Date.parse('2026-10-15T15:59:59Z') });
    try {
      await call(f, '/v1/accounts/register', signup);
      const auth = credential(await call(f, '/v1/accounts/login', {loginId: signup.loginId, password: signup.password}));
      let board = (await call(f, '/v1/leaderboard', undefined, auth)).value;
      assert.equal(board.entries.length, 1); assert.equal(board.entries[0].count, 0);
      assert.equal(board.self.count, 0);
      f.env.TEST_NOW += 1000;
      board = (await call(f, '/v1/leaderboard', undefined, auth)).value;
      assert.equal(board.entries.length, 0);
      assert.equal((await call(f, '/v1/accounts/me', undefined, auth)).status, 200);
      board = (await call(f, '/v1/leaderboard', undefined, auth)).value;
      assert.equal(board.entries.length, 1); assert.equal(board.entries[0].count, 0);
      const rewards = (await call(f, '/v1/rewards', undefined, auth)).value;
      assert.equal(rewards.totalXp, 0, 'Zero-AC login receives no medal XP');
    } finally { await f.close(); }
  });
  test('legacy login checks cloud activation again under the account lock', async () => {
    const f = await startFixture({now:Date.now()});
    try {
      await call(f,'/v1/accounts/register',signup);
      const auth=credential(await call(f,'/v1/accounts/login',{loginId:signup.loginId,password:signup.password}));
      const original=f.STORE.stateRevision.bind(f.STORE);
      let activated=false;
      f.STORE.stateRevision=async id=>{
        const revision=await original(id);
        if (!activated && revision===0) {
          activated=true;
          await f.STORE.saveAccountState(id,tokenHash(auth.token),Math.floor(f.env.TEST_NOW/1000),0,
            {format:'tb-account-state-v1',tables:{},publicAccounts:{}},new Date(f.env.TEST_NOW).toISOString());
        }
        return revision;
      };
      const old=await fetch(f.endpoint+'/v1/accounts/login',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({loginId:signup.loginId,password:signup.password})});
      assert.equal(old.status,426); await old.text();
      assert.equal((await call(f,'/v1/accounts/me',undefined,auth)).status,200,'Rejected legacy login must not kick the synchronized device');
    } finally { await f.close(); }
  });
}
