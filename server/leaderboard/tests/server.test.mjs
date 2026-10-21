import test from 'node:test';
import assert from 'node:assert/strict';
import { listenFixture } from './listen.mjs';
import { request as httpRequest } from 'node:http';
import { randomUUID } from 'node:crypto';
import { createApiServer } from '../src/server.mjs';
import { SQLiteStore } from './sqlite-store.mjs';

async function fixture(options) {
  const STORE = new SQLiteStore();
  const env = { STORE, RATE_LIMIT_SALT: 'test', TEST_NOW: Date.parse('2026-10-08T10:00:00Z') };
  const server = createApiServer(env, options);
  await listenFixture(server);
  return { env, endpoint: `http://127.0.0.1:${server.address().port}`,
    async close() { await new Promise(resolve => server.close(resolve)); await STORE.close(); } };
}

test('health reflects database availability', async () => {
  const f = await fixture();
  try {
    const ready = await fetch(f.endpoint + '/v1/health');
    assert.equal(ready.status, 200);
    const health = await ready.json();
    assert.equal(health.version, '1.2.1');
    assert.equal(health.socialProtocol, 1);
    f.env.STORE = { async health() { throw new Error('private database details'); } };
    const response = await fetch(f.endpoint + '/v1/health');
    assert.equal(response.status, 503);
    assert(!(await response.text()).includes('private'));
  } finally { await f.close(); }
});

test('public callers cannot spoof proxy headers to bypass IP registration limits', async () => {
  const f = await fixture();
  try {
    for (let i = 0; i < 11; i++) {
      const id = randomUUID();
      const response = await fetch(f.endpoint + '/v1/accounts/register', { method: 'POST',
        headers: { 'Content-Type': 'application/json',
          'X-TB-Client-IP': `192.0.2.${i}`, 'X-Forwarded-For': `192.0.2.${i}` },
        body: JSON.stringify({ loginId: 'user_' + id.slice(0, 8), nickname: 'test-' + id.slice(0, 8), password: 'fixture-password' }) });
      assert.equal(response.status, i < 10 ? 201 : 429);
      await response.text();
    }
  } finally { await f.close(); }
});

test('HTTP adapter rejects oversized declared and chunked bodies', async () => {
  const f = await fixture();
  try {
    const response = await fetch(f.endpoint + '/v1/events', { method: 'POST', body: 'x'.repeat(65537) });
    assert.equal(response.status, 413);
    await response.text();
    const status = await new Promise((resolve, reject) => {
      const request = httpRequest(f.endpoint + '/v1/events', { method: 'POST', headers: { 'Transfer-Encoding': 'chunked' } }, response => {
        response.resume(); response.on('end', () => resolve(response.statusCode));
      });
      request.on('error', reject);
      request.write('x'.repeat(32768)); request.end('x'.repeat(32769));
    });
    assert.equal(status, 413);
  } finally { await f.close(); }
});

test('state requests are authenticated before large bodies and bounded without blocking heartbeats', async () => {
  const f = await fixture();
  let release;
  try {
    const denied = await fetch(f.endpoint + '/v1/accounts/state', {method:'PUT',body:'unauthenticated'});
    assert.equal(denied.status,401); await denied.text();
    const signup = {loginId:'bounded_state_user',nickname:'bounded',password:'fixture-password'};
    await fetch(f.endpoint+'/v1/accounts/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(signup)}).then(r=>r.text());
    const login = await fetch(f.endpoint+'/v1/accounts/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({loginId:signup.loginId,password:signup.password})}).then(r=>r.json());
    const headers = {'X-TB-User':login.account.userId,Authorization:'Bearer '+login.token};
    const dense = '{"revision":0,"state":{"format":"tb-account-state-v1","tables":{"drafts":[' + '{},'.repeat(1000000) + '{}]},"publicAccounts":{}}}';
    const rejected = await fetch(f.endpoint+'/v1/accounts/state',{method:'PUT',headers:{...headers,'Content-Type':'application/json'},body:dense});
    assert.equal(rejected.status,413); await rejected.text();
    const oversized = await new Promise((resolve,reject)=>{
      const request=httpRequest(f.endpoint+'/v1/accounts/state',{method:'PUT',headers:{...headers,'Content-Type':'application/json','Content-Length':20*1024*1024}},response=>{
        response.resume(); response.on('end',()=>resolve(response.statusCode));
      });
      request.on('error',reject); request.end('invalid-json');
    });
    assert.equal(oversized,413,'20 MiB declared input is rejected before reading or parsing it');
    const original = f.env.STORE.accountState.bind(f.env.STORE);
    let entered;
    const started = new Promise(resolve=>{entered=resolve;});
    const held = new Promise(resolve=>{release=resolve;});
    f.env.STORE.accountState = async id=>{entered(); await held; return original(id);};
    const pending = fetch(f.endpoint+'/v1/accounts/state',{headers});
    await started;
    const parallel = await fetch(f.endpoint+'/v1/accounts/state',{headers});
    assert.equal(parallel.status,429); await parallel.text();
    const heartbeat = await fetch(f.endpoint+'/v1/accounts/me',{headers});
    assert.equal(heartbeat.status,200); await heartbeat.text();
    release();
    const first = await pending;
    assert.equal(first.status,200); await first.text();
    const later = await fetch(f.endpoint+'/v1/accounts/state',{headers});
    assert.equal(later.status,200); await later.text();
  } finally { release?.(); await f.close(); }
});
