import test from 'node:test';
import assert from 'node:assert/strict';
import { randomUUID, createHash } from 'node:crypto';
import { tokenHash } from '../src/accounts.mjs';

async function call(f, path, body, auth, method = body === undefined ? 'GET' : 'POST') {
  const response = await fetch(f.endpoint + path, { method, headers: { 'Content-Type': 'application/json',
    ...(auth ? { 'X-TB-User': auth.userId, Authorization: 'Bearer ' + auth.token } : {}) },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }) });
  return { status: response.status, value: await response.json() };
}
const signup = { nickname: '星河', loginId: 'star_user', password: 'a-long-fixture-password' };
const credential = result => ({ userId: result.value.account.userId, token: result.value.token });

export function accountsSuite(startFixture) {
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
      assert.equal((await call(f, '/v1/accounts/me', undefined, a)).status, 200);
      assert.equal((await call(f, '/v1/accounts/password', { oldPassword: 'wrong-password', newPassword: 'next-password' }, a)).status, 400);
      const changed = await call(f, '/v1/accounts/password', { oldPassword: signup.password, newPassword: 'next-password' }, a);
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
}
