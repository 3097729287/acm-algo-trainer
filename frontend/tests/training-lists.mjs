import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import fs from 'node:fs';
import { chromium } from 'playwright';
import { createServer } from 'vite';

const out = '../.backups/luogu-training/ui';
await mkdir(out, { recursive: true });
const vite = await createServer({ server: { host: '127.0.0.1', port: 0, fs: { allow: [process.cwd(), fs.realpathSync('node_modules')] } } });
await vite.listen();
const browser = await chromium.launch({ channel: process.env.CI ? undefined : 'msedge', headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
page.setDefaultTimeout(12000);
const errors = [], writes = [], now = () => new Date().toISOString();
page.on('pageerror', error => errors.push(error.message));
await page.addInitScript(() => localStorage.setItem('tb.preferences', JSON.stringify({ theme: 'light', fontSize: 15, navSchema: 2, navOrder: ['mine', 'library', 'paths'], onboardingCompleted: true, libraryPageSize: 10 })));
const rows = Array.from({ length: 60 }, (_, i) => ({ id: `task-${i}`, aliasIds: i === 0 ? ['old-task-0'] : [], title: `练习 ${i + 1}`, url: `https://www.luogu.com.cn/problem/P${1000 + i}`, contest: '洛谷专题练习', problem: `P${1000 + i}`, platform: '洛谷', tags: ['模拟'], knowledge: '模拟', difficulty: 800, solutionAvailable: false, statementAvailable: true }));
const ref = (i, sections = []) => ({ pid: `P${1000 + i}`, problemId: i === 0 ? 'old-task-0' : rows[i].id, url: rows[i].url, sections });
const category = (id, name, order, position) => ({ id, name, order, position });
const list = (id, title, problems, extra = {}) => ({ id, title, problems, available: true, children: [], aggregateChildren: false, categories: [category('basic', '深入浅出基础篇', 0, Number(id.at(-1)) || 0)], url: `https://www.luogu.com.cn/training/${id.replace(/\D/g, '') || '100'}`, ...extra });
const lists = [
  list('list-1', '【入门1】顺序结构', rows.map((_, i) => ref(i))),
  list('list-2', '背包问题', [ref(0), ref(1), ref(2)], { categories: [category('select', '精选用户分享', 1, 0)] }),
  list('list-3', '动态规划专题', [], { aggregateChildren: true, children: ['list-2'], categories: [category('select', '精选用户分享', 1, 1)] }),
  list('list-4', '图论专题', [ref(3, ['最短路']), ref(4, ['最短路']), ref(5, ['生成树'])]),
  list('list-5', '暂不可用的公开题单', [], { available: false }),
];
const training = [{ id: 'task-0', accepted: true, verdict: 'AC', activeAt: now() }];
const workspace = () => ({ training, sets: [], contests: [], activeContest: null, goals: { goals: [] }, goalTasks: [], summary: { total: training.length, accepted: 1, todayAccepted: 0, historicalAccepted: 1, streak: 1 }, now: now() });
let failLists = true;
await page.route('**/api/**', async route => {
  const request = route.request(), url = new URL(request.url()), path = url.pathname, body = request.method() === 'POST' ? request.postDataJSON() : null;
  if (!path.startsWith('/api/')) return route.continue();
  if (body) { assert.equal(request.headers()['x-tb-token'], 'fixture'); writes.push({ path, body }); }
  let value;
  if (path === '/api/account') value = { required: false, authenticated: true, token: 'fixture', account: null };
  else if (path === '/api/data') value = { rows, categories: [], token: 'fixture', revision: 'training-fixture', today: now().slice(0, 10) };
  else if (path === '/api/workspace') value = workspace();
  else if (path === '/api/software-update') value = { currentVersion: '1.4.3', status: 'current', autoCheck: false, canInstall: false };
  else if (path === '/api/desktop/fullscreen') value = { available: false, fullscreen: false };
  else if (path === '/api/hub') value = { settings: { accounts: {} }, accounts: [], sync: {}, updates: {}, notifications: [] };
  else if (path === '/api/insights') value = { summary: {}, growth: { level: 1, totalXp: 0 }, knowledge: [], achievements: [], activity: [], assessment: { platforms: [] }, dailyTasks: { tasks: [] } };
  else if (path === '/api/training-lists') {
    if (failLists) { failLists = false; return route.fulfill({ status: 503, json: { error: '测试读取失败' } }); }
    value = { lists };
  } else if (path === '/api/training/start') {
    assert.ok(rows.some(row => row.id === body.id));
    if (!training.some(row => row.id === body.id)) training.push({ id: body.id, accepted: false, activeAt: now() });
    value = { workspace: workspace() };
  } else if (path === '/api/problem') value = { id: url.searchParams.get('id'), title: rows.find(row => row.id === url.searchParams.get('id')).title, locked: false, markdown: '## 题目描述\n\n输出整数 $n$。', samples: [{ name: '样例 1', input: '1\n', output: '1\n' }], limits: { timeMs: 1000, memoryMb: 128 }, judge: { scope: 'samples', cases: 1 }, statementAvailable: true, draft: '', submissions: [] };
  else if (path === '/api/draft') value = { savedAt: now() };
  else if (path === '/api/submissions') value = { submissions: [], total: 0 };
  else throw Error('Unexpected fixture request: ' + path);
  await route.fulfill({ json: value });
});
const content = () => page.locator('.training-list-content');
const folder = title => content().getByRole('button').filter({ has: page.locator('strong', { hasText: title }) }).first();
const sourceMode = async () => { await page.getByLabel('题单目录方式').selectOption('source'); };
const home = async () => page.getByRole('button', { name: '全部题单', exact: true }).click();
const search = () => page.getByRole('textbox', { name: '搜索题单或题目', exact: true });
const noOverflow = async () => {
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
  assert.ok(await content().evaluate(node => node.scrollWidth <= node.clientWidth + 1));
};

try {
  await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}`);
  await page.locator('.sidebar').getByRole('button', { name: '题单', exact: true }).click();
  await page.getByRole('alert').filter({ hasText: '测试读取失败' }).waitFor();
  await page.getByRole('button', { name: '重新读取', exact: true }).click();
  await folder('动态规划').waitFor();
  const navigation = await page.locator('.sidebar nav button').allTextContents();
  assert.equal(navigation.findIndex(text => text.includes('题单')), navigation.findIndex(text => text === '题库') + 1, 'existing navigation gains entry after library');
  await folder('动态规划').click();
  await folder('背包').click();
  await folder('背包问题').click();
  assert.equal(await page.locator('.training-list-table tbody tr').count(), 3);
  assert.match(await page.locator('.training-list-heading p').textContent(), /1 \/ 3/);
  await page.keyboard.press('Escape');
  await folder('背包问题').waitFor();
  await home();
  await search().fill('P1001');
  await folder('顺序结构').waitFor();
  await folder('背包问题').waitFor();
  await search().fill('没有这样的题');
  await page.getByText('没有匹配的题单或题目', { exact: true }).waitFor();
  await page.getByRole('button', { name: '清除筛选' }).click();
  await sourceMode();
  await folder('深入浅出基础篇').click();
  await folder('顺序结构').click();
  assert.equal(await page.locator('.training-list-table tbody tr').count(), 10);
  await page.getByRole('button', { name: '题单下一页', exact: true }).click();
  await page.getByRole('button', { name: '练习 11', exact: true }).waitFor();
  await content().evaluate(node => { node.scrollTop = 120; });
  const scrollTop = await content().evaluate(node => node.scrollTop);
  await page.getByRole('button', { name: '练习 15', exact: true }).click();
  await page.getByRole('textbox', { name: 'C++ 代码' }).waitFor();
  assert.equal(writes.findLast(write => write.path === '/api/training/start').body.id, 'task-14');
  await page.locator('.wb-next-button').click();
  await page.waitForFunction(() => document.querySelector('.wb-heading')?.textContent.includes('练习 16'));
  assert.equal(writes.findLast(write => write.path === '/api/training/start').body.id, 'task-15');
  await page.getByRole('button', { name: '返回列表', exact: true }).click();
  await page.getByRole('button', { name: '练习 11', exact: true }).waitFor();
  assert.match(await page.locator('[aria-label="题单分页"]').textContent(), /第 2 \/ 6 页/);
  assert.equal(await content().evaluate(node => node.scrollTop), scrollTop);
  await page.getByLabel('题单通过状态').selectOption('accepted');
  assert.equal(await page.locator('.training-list-table tbody tr').count(), 1);
  await page.getByLabel('题单通过状态').selectOption('');
  await home();
  await folder('深入浅出基础篇').click();
  await folder('图论专题').click();
  await folder('最短路').click();
  assert.equal(await page.locator('.training-list-table tbody tr').count(), 2);
  await page.getByRole('button', { name: '返回上一级题单目录' }).click();
  await page.getByRole('button', { name: '全部题目 3 题', exact: true }).click();
  assert.equal(await page.locator('.training-list-table tbody tr').count(), 3);
  for (const width of [1440, 1050, 390]) {
    await page.setViewportSize({ width, height: 900 });
    for (const theme of ['light', 'dark']) {
      await page.evaluate(theme => { document.documentElement.dataset.theme = theme; }, theme);
      await noOverflow();
      assert.ok(await page.locator('.training-lists-page').evaluate(node => node.clientWidth > node.parentElement.clientWidth * .9), 'the page fills the workspace at every width');
      assert.equal(await page.locator('.training-list-table th:visible').count(), 3);
      assert.ok(await page.locator('.training-list-table').evaluate(table => [...table.querySelectorAll('td')].every(cell => cell.getBoundingClientRect().right <= table.getBoundingClientRect().right + 1)), 'all columns remain visible');
      await page.screenshot({ path: `${out}/problems-${width}-${theme}.png`, fullPage: true });
    }
  }
  await page.setViewportSize({ width: 1440, height: 900 });
  await home();
  await folder('精选用户分享').click();
  await folder('动态规划专题').click();
  await page.getByRole('button', { name: '全部题目 3 题', exact: true }).click();
  assert.equal(await page.locator('.training-list-table tbody tr').count(), 3);
  await home();
  await page.screenshot({ path: `${out}/folders.png`, fullPage: true });
  assert.deepEqual(errors, []);
  assert.ok(writes.every(write => ['/api/training/start', '/api/draft'].includes(write.path)));
  console.log('PASS: retry, navigation migration, algorithms, sources, chapters, search, progress, pagination, workbench next/return, six layouts; zero official submissions');
} finally {
  await browser.close();
  await vite.close();
}
