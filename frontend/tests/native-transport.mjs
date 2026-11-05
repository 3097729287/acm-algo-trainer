import assert from 'node:assert/strict';
import { isNativeRuntime, nativeRequest, invokeRequest } from '../src/api/nativeTransport.js';

assert.equal(isNativeRuntime({}), false);
assert.equal(isNativeRuntime({ __TAURI_INTERNALS__: {} }), true);
assert.equal(isNativeRuntime({ __TAURI__: {} }), true);
const request = nativeRequest('submissions?id=A%3A%3AB&id=C%2B%2B&q=%E4%B8%AD%E6%96%87', undefined, 'session', 'owner', 'id');
assert.deepEqual({ ...request.query }, { id: ['A::B', 'C++'], q: ['中文'] });
assert.equal(request.method, 'GET');
assert.equal(Object.hasOwn(request, 'body'), false);
assert.equal(nativeRequest('draft', { id: 'A', code: '' }, 'session', 'owner', 'id').method, 'POST');
for (const path of ['https://example.com/', '../draft', '/api/draft', 'draft#fragment', 'draft//save', 'draft/']) {
  assert.throws(() => nativeRequest(path, {}, '', '', 'id'));
}
for (const body of [null, [], 'text', false]) assert.throws(() => nativeRequest('draft', body, '', '', 'id'));
const pollution = nativeRequest('data?__proto__=safe&constructor=also-safe', undefined, '', '', 'id');
assert.deepEqual(pollution.query.__proto__, ['safe']);

let calls = 0, fetches = 0;
globalThis.fetch = () => { fetches++; throw new Error('Native must not use HTTP'); };
const scope = { __tbAccountUserId: 'owner', dispatchEvent() {}, __TAURI__: { core: { invoke: async (command, { request }) => {
  calls++; assert.equal(command, 'api_request');
  return { version: 1, id: request.id, ok: true, data: { savedAt: 'actual' } };
} } } };
assert.deepEqual(await invokeRequest('draft', { id: 'A', code: 'code' }, 'token', scope), { savedAt: 'actual' });
assert.equal(calls, 1); assert.equal(fetches, 0);

scope.__TAURI__.core.invoke = async (_, { request }) => ({ version: 1, id: request.id, ok: false,
  error: { status: 409, code: 'CONFLICT', message: 'changed', retryable: false } });
await assert.rejects(invokeRequest('initial-code/save', {}, 'token', scope), error => error.status === 409 && error.code === 'CONFLICT');
scope.__TAURI__.core.invoke = async () => { throw { status: 503, code: 'STORAGE_BUSY', message: 'busy', retryable: true }; };
await assert.rejects(invokeRequest('draft', {}, 'token', scope), error => error.retryable && error.status === 503);
scope.__TAURI__.core.invoke = async (_, { request }) => ({ version: 1, id: request.id + '-wrong', ok: true, data: {} });
await assert.rejects(invokeRequest('preferences', undefined, 'token', scope), error => error.code === 'IPC_PROTOCOL');
scope.__TAURI__.core.invoke = async (_, { request }) => {
  scope.__tbAccountUserId = 'different'; return { version: 1, id: request.id, ok: true, data: {} };
};
await assert.rejects(invokeRequest('preferences', undefined, 'token', scope), error => error.code === 'ACCOUNT_CHANGED');
await assert.rejects(invokeRequest('preferences', undefined, '', {}), error => error.code === 'IPC_UNAVAILABLE');
assert.equal(fetches, 0);

// Verify the existing public entrypoint deduplicates simultaneous native reads
// and invalidates the read generation when any mutation starts.
let resolveRead;
globalThis.window = { __TAURI_INTERNALS__: {}, __tbAccountUserId: 'owner', dispatchEvent() {},
  __TAURI__: { core: { invoke: (_, { request }) => {
    calls++;
    if (request.method === 'POST') return Promise.resolve({ version: 1, id: request.id, ok: true, data: {} });
    return new Promise(resolve => { resolveRead = () => resolve({ version: 1, id: request.id, ok: true, data: {} }); });
  } } } };
const { request: shared } = await import('../src/api/client.js');
const a = shared('preferences'), b = shared('preferences');
assert.equal(a, b);resolveRead();await a;
const oldRead = shared('preferences'), finishOld = resolveRead;
await shared('draft', { code: 'value' });
const newRead = shared('preferences');assert.notEqual(oldRead, newRead);
finishOld();resolveRead();await Promise.all([oldRead,newRead]);
assert.equal(fetches, 0);
console.log('Native transport: serialization, errors, owner isolation, request coalescing, no HTTP fallback passed');
