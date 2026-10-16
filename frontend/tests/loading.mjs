import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { createServer } from 'vite';

const vite = await createServer({ server: { host: '127.0.0.1', port: 18779, strictPort: true } });
await vite.listen();
const browser = await chromium.launch({ channel: process.env.CI ? undefined : 'msedge', headless: true });
try {
  const page = await browser.newPage();
  let reads = 0;
  await page.route('**/api/**', async route => {
    if (!new URL(route.request().url()).pathname.startsWith('/api/')) return route.continue();
    if (route.request().method() === 'GET') reads++;
    await new Promise(resolve => setTimeout(resolve, 50));
    await route.fulfill({ json: { value: reads, token: 'fixture' } });
  });
  await page.goto('http://127.0.0.1:18779/tests/corpus-reading.html');
  reads = 0;
  const result = await page.evaluate(async () => {
    const { request } = await import('/src/api/client.js');
    const both = await Promise.all([request('loading-fixture'), request('loading-fixture')]);
    const fresh = await request('loading-fixture');
    const old = request('old-fixture');
    await request('draft', { id: 'fixture', code: 'new' }, 'fixture');
    const afterWrite = await request('old-fixture');
    return { both, fresh, old: await old, afterWrite };
  });
  assert.equal(result.both[0].value, result.both[1].value);
  assert.equal(result.fresh.value, result.both[0].value + 1);
  assert.equal(result.afterWrite.value, result.old.value + 1);
  assert.equal(reads, 4);
  console.log('Concurrent reads shared; completed reads and writes remain fresh.');
} finally {
  await browser.close();
  await vite.close();
}
