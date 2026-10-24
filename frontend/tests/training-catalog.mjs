import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';
import { createServer } from 'vite';

const source = JSON.parse(fs.readFileSync('../data/library/training_lists.json', 'utf8'));
const rows = JSON.parse(fs.readFileSync('../data/library/problems.json', 'utf8')).map(row => row.encoded);
const out = '../.backups/training-catalog-ui';
fs.mkdirSync(out, { recursive: true });
const vite = await createServer({ server: { host: '127.0.0.1', port: 0, fs: { allow: [process.cwd(), fs.realpathSync('node_modules')] } } });
await vite.listen();
const browser = await chromium.launch({ channel: process.env.CI ? undefined : 'msedge', headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
page.setDefaultTimeout(15000);
const errors = [];
page.on('pageerror', issue => errors.push(issue.message));
await page.addInitScript(() => localStorage.setItem('tb.preferences', JSON.stringify({ theme: 'light', fontSize: 15, navSchema: 2, navOrder: ['mine', 'library', 'paths'], onboardingCompleted: true, libraryPageSize: 50 })));
const now = new Date().toISOString();
await page.route('**/api/**', async route => {
  const path = new URL(route.request().url()).pathname;
  if (!path.startsWith('/api/')) return route.continue();
  assert.equal(route.request().method(), 'GET', 'browsing does not mutate learning data');
  let value;
  if (path === '/api/account') value = { required: false, authenticated: true, token: 'fixture', account: null };
  else if (path === '/api/data') value = { rows, categories: [], token: 'fixture', revision: 'catalog-full', today: now.slice(0, 10) };
  else if (path === '/api/workspace') value = { training: [], sets: [], contests: [], activeContest: null, goals: { goals: [] }, goalTasks: [], summary: {}, now };
  else if (path === '/api/software-update') value = { currentVersion: '1.4.7', status: 'current', autoCheck: false, canInstall: false };
  else if (path === '/api/desktop/fullscreen') value = { available: false, fullscreen: false };
  else if (path === '/api/hub') value = { settings: { accounts: {} }, accounts: [], sync: {}, updates: {}, notifications: [] };
  else if (path === '/api/insights') value = { summary: {}, growth: {}, knowledge: [], achievements: [], activity: [], assessment: { platforms: [] }, dailyTasks: { tasks: [] } };
  else if (path === '/api/training-lists') value = { lists: source };
  else throw Error(path);
  await route.fulfill({ json: value });
});
const content = () => page.locator('.training-list-content');
const folder = title => content().locator('button.catalog-folder-row').filter({ has: page.locator('strong').filter({ hasText: title }) }).first();
const home = () => page.getByRole('button', { name: '全部题单', exact: true }).click();
try {
  await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}`);
  await page.locator('.sidebar').getByRole('button', { name: '题单', exact: true }).click();
  await folder('字符串').waitFor();
  assert.match(await page.locator('.training-list-heading p').textContent(), /563 个题单/);
  assert.equal(await content().locator('button.catalog-folder-row').count(), 14);
  await page.screenshot({ path: out + '/all-categories.png', fullPage: true });
  await folder('字符串').click();
  for (const name of ['字符串基础', '字符串哈希', '模式匹配', '字典树', '后缀结构', '回文算法', '综合练习']) await folder(name).waitFor();
  assert.equal(await content().locator('strong small').count(), 0, 'subject directory contains only topic folders');
  for (const width of [1440, 1050, 390]) {
    await page.setViewportSize({ width, height: 900 });
    for (const theme of ['light', 'dark']) {
      await page.evaluate(theme => document.documentElement.dataset.theme = theme, theme);
      await page.waitForTimeout(350);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
      assert.ok(await content().evaluate(node => node.scrollWidth <= node.clientWidth + 1));
      await page.screenshot({ path: `${out}/strings-${width}-${theme}.png`, fullPage: true });
    }
  }
  await page.setViewportSize({ width: 1440, height: 900 });
  await folder('模式匹配').click();
  await folder('KMP 与 AC 自动机 · 基础练习').waitFor();
  await folder('AC 自动机 · 专项练习').waitFor();
  await page.screenshot({ path: out + '/matching.png', fullPage: true });
  await folder('KMP 与 AC 自动机 · 基础练习').click();
  assert.match(await page.locator('.training-list-heading h2').textContent(), /KMP 与 AC 自动机/);
  await page.getByRole('button', { name: '全部题目 20 题', exact: true }).click();
  assert.equal(await page.locator('.training-list-table tbody tr').count(), 20);
  await page.keyboard.press('Escape');
  await page.keyboard.press('Escape');
  await folder('AC 自动机 · 专项练习').waitFor();
  await home();
  await page.getByRole('textbox', { name: '搜索题单或题目', exact: true }).fill('菜鸡L_C_A');
  await folder('KMP 与 AC 自动机 · 基础练习').waitFor();
  assert.equal(await content().locator('button.catalog-folder-row').count(), 1, 'original title remains searchable');
  await home();
  await folder('教材配套').click();
  await folder('算法竞赛入门经典').click();
  await folder('第 3 章 · 例题与习题').waitFor();
  await home();
  await folder('待补充信息').click();
  await folder('关联题单').click();
  await folder('关联题单 · 9349').waitFor();
  assert.ok((await content().textContent()).includes('暂不可用'));
  assert.deepEqual(errors, []);
  console.log('PASS: all 563 lists, fourteen categories, subject folders, normalized names, original search, rosters, unavailable sources and six layouts');
} finally {
  await browser.close();
  await vite.close();
}
