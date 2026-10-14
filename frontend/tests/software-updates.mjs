import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { createServer } from 'vite';
const server = await createServer({ server: { host: '127.0.0.1', port: 0 } });
await server.listen();
const browser = await chromium.launch({ channel: process.env.CI ? undefined : 'msedge', headless: true });
try {
  const page = await browser.newPage();
  const errors = []; page.on('pageerror', error => errors.push(error.message));
  await page.goto(server.resolvedUrls.local[0] + 'tests/software-updates-fixture.html');
  const panel = page.getByRole('region', { name: '软件版本更新' });
  await page.getByRole('complementary', { name: '软件更新提示' }).waitFor();
  await page.getByRole('button', { name: '稍后更新' }).click();
  assert.equal(await page.getByRole('complementary', { name: '软件更新提示' }).count(), 0);
  await panel.getByRole('checkbox').uncheck();
  await panel.getByRole('button', { name: '下载更新 v0.10.0' }).click();
  await panel.getByRole('button', { name: '保存并替换更新' }).click();
  await panel.getByRole('alert').waitFor();
  assert.match(await panel.getByRole('alert').innerText(), /草稿尚未保存/);
  assert.equal(await page.evaluate(() => window.updaterCalls.some(item => item.path.endsWith('/install'))), false);
  await page.evaluate(() => { window.saveAllowed = true; });
  await panel.getByRole('button', { name: '保存并替换更新' }).click();
  await page.getByRole('status').filter({ hasText: '正在关闭 TB' }).waitFor();
  const installs = await page.evaluate(() => window.updaterCalls.filter(item => item.path.endsWith('/install')));
  assert.deepEqual(installs, [{ path: 'software-update/install', draftSaved: true }]);
  assert.deepEqual(errors, []);
  console.log('Software update UI: notice, postpone, preference, download, blocked unsaved draft, save-before-install passed.');
} finally { await browser.close(); await server.close(); }
