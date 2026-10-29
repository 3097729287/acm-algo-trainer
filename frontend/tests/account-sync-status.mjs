import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import { chromium } from 'playwright';

process.env.TB_OFFLINE = '1';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const artifactDir = path.resolve(root, '..', '.backups', 'frontend-background-checks', 'account-sync-status');
await fs.mkdir(artifactDir, { recursive: true });
const log = [], errors = [], blockedRequests = [];
const report = message => { log.push(`${new Date().toISOString()} ${message}`); console.log(message); };
const server = await createServer({ root, server: { host: '127.0.0.1', port: 0, hmr: false } });
await server.listen();
const base = server.resolvedUrls.local[0];
const origin = new URL(base).origin;
let browser, context, page;
try {
  browser = await chromium.launch({ channel: process.env.CI ? undefined : 'msedge', headless: true });
  context = await browser.newContext({ viewport: { width: 900, height: 420 } });
  await context.route('**/*', route => {
    const url = new URL(route.request().url());
    if (url.origin === origin && !url.pathname.startsWith('/api/')) return route.continue();
    blockedRequests.push(url.href);
    return route.abort('blockedbyclient');
  });
  await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
  page = await context.newPage();
  page.setDefaultTimeout(5000);
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(`${base}tests/account-sync-status-fixture.html?state=pending`);
  await page.getByLabel('账号数据同步中',{exact:true}).waitFor();
  assert.equal(await page.getByLabel('账号数据同步中',{exact:true}).innerText(),'');
  await page.getByLabel('账号数据同步中',{exact:true}).hover();
  assert.equal(await page.getByLabel('账号数据同步中',{exact:true}).evaluate(node=>node.closest('.tooltip-anchor').title),'同步中');
  await page.evaluate(()=>window.accountSyncStatusFixture.update({status:'ready',pending:false}));
  await page.getByLabel('账号数据已同步',{exact:true}).waitFor();
  assert.equal(await page.getByLabel('账号数据已同步',{exact:true}).locator('svg.lucide-check').count(),1);
  await page.getByLabel('账号数据已同步',{exact:true}).waitFor({state:'hidden',timeout:5000});
  await page.evaluate(()=>window.accountSyncStatusFixture.update({status:'error',pending:true,error:'事件模拟：连接已中断'}));
  await page.getByLabel('账号数据待同步',{exact:true}).waitFor();
  assert.equal(await page.getByLabel('账号数据同步中',{exact:true}).count(),0);
  await page.getByLabel('账号数据待同步',{exact:true}).hover();
  assert.equal(await page.getByLabel('账号数据待同步',{exact:true}).evaluate(node=>node.closest('.tooltip-anchor').title),'事件模拟：连接已中断');
  await page.evaluate(()=>window.accountSyncStatusFixture.update(undefined));
  assert.equal(await page.locator('.sync-status-icon').count(),0);
  report('PASS: spinner + hover tooltip, durable error precedence, completion icon toast and automatic disappearance.');
  assert.deepEqual(errors, [], 'no unhandled browser errors');
  assert.deepEqual(blockedRequests, [], 'fixture attempts no API or external requests');
  report('PASS: no API requests, external requests, or unhandled browser errors.');
} catch (error) {
  report(`FAIL: ${error.stack || error.message}`);
  if (page) await page.screenshot({ path: path.join(artifactDir, 'failure.png'), animations: 'disabled' }).catch(() => undefined);
  throw error;
} finally {
  if (context) await context.tracing.stop({ path: path.join(artifactDir, 'trace.zip') });
  if (browser) await browser.close();
  await server.close();
  await fs.writeFile(path.join(artifactDir, 'events.json'), JSON.stringify({ errors, blockedRequests }, null, 2));
  await fs.writeFile(path.join(artifactDir, 'account-sync-status.log'), `${log.join('\n')}\n`);
  console.log(`Artifacts: ${artifactDir}`);
}
