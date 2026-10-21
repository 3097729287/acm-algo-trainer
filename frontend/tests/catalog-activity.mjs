import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { createServer } from 'vite';
import { chromium } from 'playwright';
const vite = await createServer({ server: { host: '127.0.0.1', port: 18778, strictPort: true } });
await vite.listen();
const browser = await chromium.launch({ channel: process.env.CI ? undefined : 'msedge', headless: true });
const page = await browser.newPage({ viewport: { width: 1600, height: 1100 } });
const errors = [];
page.on('pageerror', e => errors.push(e.message));
try {
  await page.clock.install({ time: new Date('2026-10-15T04:00:00Z') });
  await page.goto('http://127.0.0.1:18778/tests/catalog-activity-fixture.html');
  const tabs = page.getByRole('tablist', { name: '比赛题库分类' });
  assert.deepEqual(await tabs.getByRole('tab').allTextContents(), ['全部比赛', '牛客', '洛谷', 'Codeforces', 'AtCoder', 'XCPC 历年', '蓝桥杯 B 组历年']);
  assert.equal(await page.getByLabel('比赛平台', { exact: true }).count(), 0);
  await tabs.getByRole('tab', { name: '牛客', exact: true }).click();
  assert.deepEqual(await page.locator('.competition-card-title strong').allTextContents(), ['周赛 10', '周赛 2']);
  await tabs.getByRole('tab', { name: 'Codeforces', exact: true }).click();
  assert.equal(await page.locator('.competition-card').count(), 2);
  await tabs.getByRole('tab', { name: 'XCPC 历年', exact: true }).click();
  assert.equal(await page.locator('.competition-card').count(), 1);
  assert.equal(await page.locator('.competition-difficulty').count(), 0, 'unknown difficulty has no placeholder');
  assert.equal(await page.locator('.competition-problem-token').textContent(), 'A', 'unknown difficulty shows only its problem letter');
  assert.equal(await page.locator('.competition-platform').count(), 0, 'competition cards do not repeat platform labels');
  await tabs.getByRole('tab', { name: '蓝桥杯 B 组历年', exact: true }).click();
  assert.equal(await page.locator('.competition-card').count(), 1);
  await tabs.getByRole('tab', { name: '全部比赛', exact: true }).click();
  assert.equal(await page.locator('.competition-card').count(), 7);
  const activity = page.getByLabel('训练活动', { exact: true });
  assert.deepEqual(await activity.locator('thead th').allTextContents(), ['日期', '通过题数']);
  assert.equal((await activity.innerText()).includes('次提交'), false);
  assert.equal((await activity.innerText()).includes('本地通过'), false);
  const today = '2026-10-15';
  for (const [index, amount] of [0, 1, 2, 4, 7].entries()) {
    const key = today.slice(0, 8) + String(index + 1).padStart(2, '0');
    const cell = activity.getByRole('gridcell', { name: `${key}，${amount} 题通过`, exact: true });
    assert.match(await cell.getAttribute('class'), new RegExp(`activity-level-${index}(?:\\s|$)`));
    await cell.click();
    assert.match(await activity.locator('.activity-day-detail .activity-pass-count').getAttribute('class'), new RegExp(`activity-pass-${index}(?:\\s|$)`));
  }
  await mkdir('tests/screenshots', { recursive: true });
  await page.screenshot({ path: 'tests/screenshots/catalog-activity-v17.png', fullPage: true });
  await page.setViewportSize({ width: 800, height: 900 });
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
  assert.deepEqual(errors, []);
  console.log('Catalog/activity passed: natural order, seven shelves, no platform selector, official passes only, five count styles.');
} finally { await browser.close(); await vite.close(); }
