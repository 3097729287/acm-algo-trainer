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
    assert.equal((await fetch(f.endpoint + '/v1/health')).status, 200);
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
        body: JSON.stringify({ loginId: 'user_' + id.slice(0, 8), nickname: 'test', password: 'fixture-password' }) });
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
