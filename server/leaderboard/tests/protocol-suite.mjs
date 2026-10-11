import test from 'node:test';
import assert from 'node:assert/strict';
import { randomUUID, createHash } from 'node:crypto';

const NOW = Date.parse('2026-10-08T15:59:00Z');
const key = text => createHash('sha256').update(text).digest('hex');
function identity() { return { userId: randomUUID(), token: key(randomUUID()) }; }
async function request(fixture, user, method, path, body) {
  const result = await fetch(fixture.endpoint + path, { method,
    headers: { 'X-TB-User': user.userId, Authorization: 'Bearer ' + user.token, 'Content-Type': 'application/json' },
    ...(body == null ? {} : { body: JSON.stringify(body) }) });
  return { status: result.status, value: await result.json() };
}
async function register(fixture, user, nickname = '训练者') {
  return request(fixture, user, 'POST', '/v1/profile/register', { userId: user.userId, nickname });
}
function ac(user, name, acceptedAt = '2026-10-08T10:00:00Z') {
  return { eventId: key(user.userId + name), problemKey: key(name), acceptedAt, difficulty: 1500, scope: 'official' };
}

export function protocolSuite(startFixture) {
test('official protocol rejects old local receipts and explicitly acknowledges official scope', async () => {
  const fixture = await startFixture({ now: NOW });
  try {
    const user = identity(); await register(fixture, user);
    for (const scope of ['local-reviewed', 'local', 'samples', 'run']) {
      assert.equal((await request(fixture, user, 'POST', '/v1/events', {events: [{...ac(user, 'one'), scope}]})).status, 400);
    }
    assert.equal(await fixture.countEvents(), 0);
    const accepted = await request(fixture, user, 'POST', '/v1/events', {events: [ac(user, 'one')]});
    assert.equal(accepted.value.scope, 'official');
    assert.equal(accepted.value.processed, 1);
  } finally { await fixture.close(); }
});

test('migration maintenance prevents writes while health and existing profiles remain readable', async () => {
  const fixture = await startFixture({ now: NOW });
  try {
    const user = identity(); await register(fixture, user);
    fixture.env.READ_ONLY = '1';
    assert.equal((await register(fixture, identity())).status, 503);
    assert.equal((await request(fixture, user, 'PUT', '/v1/profile', { nickname: 'changed' })).status, 503);
    assert.equal((await request(fixture, user, 'POST', '/v1/events', { events: [ac(user, 'p1')] })).status, 503);
    assert.equal((await request(fixture, user, 'GET', '/v1/profile')).value.nickname, '训练者');
    assert.equal((await fetch(fixture.endpoint + '/v1/health')).status, 200);
    assert.equal(await fixture.countEvents(), 0);
  } finally { await fixture.close(); }
});

test('unique persisted identity, authenticated ownership, nickname + full ID', async () => {
  const fixture = await startFixture({ now: NOW });
  try {
    const a = identity(), b = identity();
    assert.equal((await register(fixture, a)).status, 201);
    assert.equal((await register(fixture, b, '另一用户')).status, 201);
    assert.notEqual(a.userId, b.userId);
    assert.equal((await register(fixture, a)).status, 200);
    const stolen = { ...a, token: b.token };
    assert.equal((await register(fixture, stolen)).status, 401);
    assert.equal((await request(fixture, stolen, 'PUT', '/v1/profile', { nickname: '冒领' })).status, 401);
    assert.equal((await request(fixture, a, 'PUT', '/v1/profile', { nickname: '新昵称' })).status, 200);
    const profile = await request(fixture, a, 'GET', '/v1/profile');
    assert.equal(profile.value.displayName, '新昵称 #' + a.userId);
    assert(!JSON.stringify(profile.value).includes('token'));
    assert.equal((await request(fixture, a, 'PUT', '/v1/profile', { nickname: 'X', userId: b.userId })).status, 400);
  } finally { await fixture.close(); }
});

test('AC events are unique by original problem, retry safe, database batches roll back', async () => {
  const fixture = await startFixture({ now: NOW });
  try {
    const user = identity(); await register(fixture, user);
    const event = ac(user, 'problem1');
    for (let index = 0; index < 3; index++) assert.equal((await request(fixture, user, 'POST', '/v1/events', { events: [event] })).status, 200);
    const parallel = await Promise.all(Array.from({ length: 8 }, () => request(fixture, user, 'POST', '/v1/events', { events: [event] })));
    assert(parallel.every(value => value.status === 200));
    assert.equal((await request(fixture, user, 'POST', '/v1/events', { events: [{ ...event, eventId: key('replay') }] })).status, 200);
    let score = (await request(fixture, user, 'GET', '/v1/leaderboard?period=total')).value;
    assert.equal(score.self.count, 1);
    const invalid = { ...ac(user, 'problem2'), eventId: event.eventId };
    assert.equal((await request(fixture, user, 'POST', '/v1/events', { events: [ac(user, 'problem3'), invalid] })).status, 409);
    score = (await request(fixture, user, 'GET', '/v1/leaderboard?period=total')).value;
    assert.equal(score.self.count, 1);
    assert.equal(await fixture.countEvents(), 1);
  } finally { await fixture.close(); }
});

test('daily Beijing midnight and Sunday week, repeated later dates cannot farm', async () => {
  const fixture = await startFixture({ now: NOW });
  try {
    const user = identity(); await register(fixture, user);
    const events = [ac(user, 'today', '2026-10-08T10:00:00Z'), ac(user, 'this-week', '2026-10-05T08:00:00Z'), ac(user, 'last-week', '2026-10-03T10:00:00Z')];
    assert.equal((await request(fixture, user, 'POST', '/v1/events', { events })).status, 200);
    assert.equal((await request(fixture, user, 'GET', '/v1/leaderboard?period=daily')).value.self.count, 1);
    assert.equal((await request(fixture, user, 'GET', '/v1/leaderboard?period=weekly')).value.self.count, 2);
    assert.equal((await request(fixture, user, 'GET', '/v1/leaderboard?period=total')).value.self.count, 3);
    fixture.env.TEST_NOW = NOW + 120000;
    assert.equal((await request(fixture, user, 'GET', '/v1/leaderboard?period=daily')).value.self.count, 0);
    assert.equal((await request(fixture, user, 'POST', '/v1/events', { events: [{ ...events[0], acceptedAt: '2026-10-08T16:00:00Z' }] })).status, 200);
    assert.equal((await request(fixture, user, 'GET', '/v1/leaderboard?period=daily')).value.self.count, 0);
    // Out-of-order completion can correct a first acceptance to an earlier date.
    assert.equal((await request(fixture, user, 'POST', '/v1/events', { events: [{ ...events[0], acceptedAt: '2026-10-03T10:00:00Z' }] })).status, 200);
    assert.equal((await request(fixture, user, 'GET', '/v1/leaderboard?period=weekly')).value.self.count, 1);
  } finally { await fixture.close(); }
});

test('midnight and Sunday settle only three distinct places, atomically and without repeated XP', async () => {
  const fixture = await startFixture({ now: Date.parse('2026-10-10T15:59:59Z') });
  try {
    const users = Array.from({length: 4}, identity);
    for (let index = 0; index < users.length; index++) {
      const user = users[index]; await register(fixture, user);
      const events = Array.from({length: Math.max(1, 3-index)}, (_, i) => ac(user, `p${index}-${i}`, `2026-10-10T${index === 3 ? '11' : '10'}:00:00Z`));
      assert.equal((await request(fixture, user, 'POST', '/v1/events', {events})).status, 200);
      assert.equal((await request(fixture, user, 'GET', '/v1/rewards')).value.totalXp, 0);
    }
    const before = (await request(fixture, users[0], 'GET', '/v1/leaderboard?period=weekly')).value;
    assert.equal(before.startDate, '2026-10-04');
    assert.deepEqual(before.entries.map(row => row.rank), [1,2,3,4]);
    fixture.env.TEST_NOW += 1000;
    const retries = await Promise.all(Array.from({length: 6}, () => request(fixture, users[0], 'GET', '/v1/rewards')));
    assert(retries.every(value => value.status === 200 && value.value.totalXp === 600));
    for (const [index, xp] of [600,360,180,0].entries()) {
      const rewards = (await request(fixture, users[index], 'GET', '/v1/rewards')).value;
      assert.equal(rewards.totalXp, xp);
      assert.equal(rewards.awards.length, index < 3 ? 2 : 0);
    }
    assert.equal((await request(fixture, users[0], 'GET', '/v1/leaderboard?period=weekly')).value.self.count, 0);
    assert.equal((await request(fixture, users[0], 'GET', '/v1/leaderboard?period=daily')).value.self.count, 0);
    assert.equal((await request(fixture, users[0], 'GET', '/v1/leaderboard?period=total')).value.self.count, 3);
    // Late synchronization changes scores, but cannot rewrite a settled reward.
    await request(fixture, users[3], 'POST', '/v1/events', {events: Array.from({length: 5},(_,i)=>ac(users[3], 'late'+i,'2026-10-10T09:00:00Z'))});
    assert.equal((await request(fixture, users[3], 'GET', '/v1/rewards')).value.totalXp, 0);
    fixture.env.TEST_NOW += 3 * 86400000;
    assert.equal((await request(fixture, users[0], 'GET', '/v1/rewards')).value.totalXp, 600);
  } finally { await fixture.close(); }
});

test('daily settlement on a weekday does not grant weekly or cumulative rewards', async () => {
  const fixture = await startFixture({now: NOW});
  try {
    const user = identity(); await register(fixture,user);
    await request(fixture,user,'POST','/v1/events',{events:[ac(user,'first')]});
    fixture.env.TEST_NOW += 120000;
    const rewards = (await request(fixture,user,'GET','/v1/rewards')).value;
    assert.equal(rewards.totalXp,100);
    assert.equal(rewards.awards.length,1);
    assert.equal(rewards.awards[0].period,'daily');
    assert.equal(rewards.awards[0].startDate,'2026-10-08');
  } finally { await fixture.close(); }
});

test('only a server-granted administrator can delete scores, and replay cannot resurrect them', async () => {
  const fixture = await startFixture({now: NOW});
  try {
    const admin = identity(), user = identity(); await register(fixture,admin); await register(fixture,user);
    const events = [ac(user,'today'),ac(user,'older','2026-10-05T08:00:00Z')];
    await request(fixture,user,'POST','/v1/events',{events});
    const body = {userId:user.userId,period:'daily',confirmation:'delete'};
    assert.equal((await request(fixture,admin,'POST','/v1/admin/leaderboard/delete',body)).status,403);
    assert.equal((await request(fixture,{...admin,token:user.token},'POST','/v1/admin/leaderboard/delete',body)).status,401);
    if (fixture.STORE.pool) await fixture.STORE.pool.execute('INSERT INTO ranking_admins VALUES(?,?)',[admin.userId,new Date(NOW).toISOString()]);
    else fixture.STORE.database.prepare('INSERT INTO ranking_admins VALUES(?,?)').run(admin.userId,new Date(NOW).toISOString());
    assert.equal((await request(fixture,admin,'GET','/v1/leaderboard')).value.isAdmin,true);
    assert.equal((await request(fixture,user,'GET','/v1/leaderboard')).value.isAdmin,false);
    assert.equal((await request(fixture,admin,'POST','/v1/admin/leaderboard/delete',{...body,confirmation:''})).status,400);
    assert.equal((await request(fixture,admin,'POST','/v1/admin/leaderboard/delete',body)).value.removed,1);
    assert.equal((await request(fixture,user,'GET','/v1/leaderboard?period=total')).value.self.count,1);
    assert.equal((await request(fixture,user,'GET','/v1/leaderboard?period=daily')).value.self.count,0);
    await request(fixture,user,'POST','/v1/events',{events});
    assert.equal((await request(fixture,user,'GET','/v1/leaderboard?period=total')).value.self.count,1);
    assert.equal((await request(fixture,admin,'POST','/v1/admin/leaderboard/delete',body)).value.removed,0);
    assert.equal((await request(fixture,admin,'POST','/v1/admin/leaderboard/delete',{...body,userId:null,period:'total'})).value.removed,1);
    assert.equal((await request(fixture,user,'GET','/v1/leaderboard?period=total')).value.entries.length,0);
    // Tombstones preserve identity and original event evidence.
    assert.equal(await fixture.countEvents(),2);
    assert.equal((await request(fixture,user,'GET','/v1/profile')).status,200);
  } finally { await fixture.close(); }
});

test('ranks real users only, bounds bad payloads, excludes samples and impersonation', async () => {
  const fixture = await startFixture({ now: NOW });
  try {
    const a = identity(), b = identity(); await register(fixture, a); await register(fixture, b);
    assert.equal((await request(fixture, a, 'GET', '/v1/leaderboard')).value.entries.length, 0);
    await request(fixture, a, 'POST', '/v1/events', { events: [ac(a, 'p1'), ac(a, 'p2')] });
    await request(fixture, b, 'POST', '/v1/events', { events: [ac(b, 'p3')] });
    const scores = (await request(fixture, b, 'GET', '/v1/leaderboard')).value;
    assert.deepEqual(scores.entries.map(entry => entry.count), [2, 1]);
    assert.equal(scores.self.rank, 2);
    for (const events of [[{ ...ac(a, 'sample'), scope: 'samples' }], [{ ...ac(a, 'future'), acceptedAt: '2026-10-10T00:00:00Z' }], [{ ...ac(a, 'private'), code: 'PRIVATE CODE' }], Array(101).fill(ac(a, 'big'))]) {
      assert.equal((await request(fixture, a, 'POST', '/v1/events', { events })).status, 400);
    }
    assert.equal((await request(fixture, a, 'POST', '/v1/events', { userId: b.userId, events: [ac(a, 'p4')] })).status, 400);
    assert.equal((await request(fixture, a, 'POST', '/v1/events', { events: [ac(a, 'p4')], junk: 'x'.repeat(66000) })).status, 413);
    assert.equal((await request(fixture, a, 'GET', '/v1/leaderboard?period=invalid')).status, 400);
    assert.equal((await request(fixture, a, 'PUT', '/v1/profile', { nickname: '\u0000bad' })).status, 400);
  } finally { await fixture.close(); }
});

test('per-user rate limits are atomic and have expiry', async () => {
  const fixture = await startFixture({ now: NOW });
  try {
    fixture.env.REQUESTS_PER_USER_MINUTE = 10;
    const user = identity(); await register(fixture, user);
    for (let index = 0; index < 10; index++) assert.equal((await request(fixture, user, 'GET', '/v1/profile')).status, 200);
    assert.equal((await request(fixture, user, 'GET', '/v1/profile')).status, 429);
    fixture.env.TEST_NOW += 61000;
    assert.equal((await request(fixture, user, 'GET', '/v1/profile')).status, 200);
  } finally { await fixture.close(); }
});

}
