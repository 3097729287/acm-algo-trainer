import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { createServer } from 'vite';
import { mkdir } from 'node:fs/promises';
import { openSettings } from './settings-navigation.mjs';

const server = await createServer({ server: { host: '127.0.0.1', port: 0 } });
await server.listen();
const browser = await chromium.launch({ channel: process.env.CI ? undefined : 'msedge', headless: true });
const page = await browser.newPage({ viewport: { width: 1480, height: 920 } });
page.setDefaultTimeout(10000);
const errors = [];
page.on('pageerror', error => errors.push(error.message));
const rows = Array.from({ length: 10037 }, (_, index) => ({
  id: `fixture::${index}`, contest: '分页测试', problem: String(index), title: `分页练习 ${String(index).padStart(5, '0')}`,
  tags: ['前缀和'], knowledge: '前缀和', platform: index % 2 ? 'AtCoder' : 'Codeforces',
  difficulty: 1000, contestDate: '2026-10-01', url: 'https://example.com/problem', solutionAvailable: true,
}));
const now = () => new Date().toISOString();
const workspace = () => ({ training: [{ id: rows[0].id, queue: 'fill', verdict: 'WA' }], sets: [], contests: [], activeContest: null,
  summary: { total: 1, accepted: 0, attempts: 1, due: 1, pending: 0 }, now: now() });
const formula = String.raw`F(i, j) = a_i \cdot \prod_{k=1}^{j} a_k = a_i \cdot \left(a_1 \cdot a_2 \cdot \ldots \cdot a_j\right)`;
const markdown = `## 题目描述\n\n\\(${formula}\\)\n\n$$$a_i$$$\n\n\\[${formula}\\]\n\n\`\\(literal\\)\`\n\n\`\`\`cpp\n// \\(code\\) $$$code$$$\n\`\`\``;
await page.route('**/api/**', async route => {
  const request = route.request(), url = new URL(request.url()), path = url.pathname;
  if (!path.startsWith('/api/')) return route.continue();
  let value;
  if (path === '/api/account') value = { required: false, authenticated: true, token: 'fixture', account: null };
  else if(path==='/api/contest-calendar')value={contests:[],refreshing:false,importing:false};
  else if(path==='/api/content-update')value={revision:0,status:'current',error:''};
  else if (path === '/api/software-update') value = {currentVersion:'0.10.0', status:'current', autoCheck:true, canInstall:false};
  else if (path === '/api/browser-preparation') value = {available:false};
  else if (path === '/api/data') value = { rows, categories: [], token: 'fixture', today: now().slice(0, 10) };
  else if (path === '/api/goals') value = { goals: [] };
  else if (path === '/api/lectures') value = { lectures: [] };
  else if (path === '/api/desktop/fullscreen') value = { available: false, fullscreen: false };
  else if (path === '/api/workspace') value = workspace();
  else if (path === '/api/inbox') value = { pending: 0, errors: [] };
  else if (path === '/api/hub' || path === '/api/insights') value = null;
  else if (path === '/api/social') value = { available: false, totalLikes: 0, unreadCount: 0, notifications: [] };
  else if (path === '/api/training/start') { assert.equal(request.headers()['x-tb-token'], 'fixture'); value = { workspace: workspace() }; }
  else if (path === '/api/problem') value = { id: url.searchParams.get('id'), title: '公式练习', markdown, samples: [], limits: {},
    judge: { scope: 'samples', cases: 0 }, statementAvailable: true, draft: '', submissions: [] };
  else if (path === '/api/solution') value = { id: url.searchParams.get('id'), markdown, lectures: [] };
  else if (path === '/api/draft') value = { savedAt: now() };
  else if(path==='/api/usage'||path==='usage') value={days:[],totalSeconds:0,maxDailySeconds:0,maxDailyDate:null};
  else throw new Error(`Unhandled fixture: ${path}`);
  await route.fulfill({ json: value });
});
const tableRows = page.locator('.problem-table tbody tr[data-id]');
const pagination = page.getByRole('navigation', { name: '题库分页' });
async function status(pageNumber, total, size) {
  const count = Math.max(0, Math.min(size, total - (pageNumber - 1) * size));
  await page.waitForFunction(expected => {
    const pagination = document.querySelector('[aria-label="题库分页"]');
    return pagination?.querySelector('[role="status"]')?.textContent === `共 ${expected.total} 题`
      && pagination?.querySelector('[aria-label="跳转页码"]')?.value === String(expected.pageNumber)
      && document.querySelectorAll('.problem-table tbody tr[data-id]').length === expected.count;
  }, { pageNumber, total, count });
}
async function selected(id) {
  await page.waitForFunction(expected => document.querySelector('.problem-table tr[data-selected="true"]')?.dataset.id === expected, id);
}
try {
  await page.goto(`http://127.0.0.1:${server.httpServer.address().port}`);
  await page.getByRole('navigation', { name: '主导航' }).waitFor();
  assert.equal(await page.locator('.sidebar nav kbd, .sidebar nav .nav-badge').count(), 0, 'Navigation has no misleading numbers');
  await page.keyboard.press('Control+2');
  await page.waitForFunction(() => document.querySelectorAll('.problem-table tbody tr[data-id]').length > 5);
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  const fittedSize = await tableRows.count();
  await status(1, rows.length, fittedSize);
  assert.ok(fittedSize < 50, 'A large library mounts only the rows fitting this window');
  assert.ok(await page.getByLabel('题库上一页').isDisabled());
  const firstIds = await tableRows.evaluateAll(nodes => nodes.map(node => node.dataset.id));
  await page.getByLabel('题库下一页').click();
  await status(2, rows.length, fittedSize);
  const secondIds = await tableRows.evaluateAll(nodes => nodes.map(node => node.dataset.id));
  assert.equal(new Set([...firstIds, ...secondIds]).size, 2 * fittedSize);
  await page.getByRole('region', { name: '题目列表', exact: true }).focus();
  assert.equal(await page.locator('.problem-table tr[data-selected="true"]').count(), 0, 'focus alone does not mark a row');
  await page.keyboard.press('Home');
  await selected(firstIds[0]);
  await page.keyboard.press('PageDown');
  await status(Math.floor(10 / fittedSize) + 1, rows.length, fittedSize);
  await selected([...firstIds, ...secondIds][10]);
  await page.keyboard.press('PageUp');
  await selected(firstIds[0]);
  for (let index = 0; index < fittedSize; index++) await page.keyboard.press('ArrowDown');
  await status(2, rows.length, fittedSize);
  await selected(secondIds[0]);
  await page.keyboard.press('ArrowUp');
  await status(1, rows.length, fittedSize);
  await selected(firstIds.at(-1));
  await page.keyboard.press('ArrowDown');
  await status(2, rows.length, fittedSize);
  await selected(secondIds[0]);
  await page.keyboard.press('End');
  await status(Math.ceil(rows.length / fittedSize), rows.length, fittedSize);
  assert.equal(await tableRows.count(), rows.length % fittedSize || fittedSize);
  assert.ok(await page.getByLabel('题库下一页').isDisabled());
  await page.keyboard.press('Home');
  await status(1, rows.length, fittedSize);
  await selected(firstIds[0]);
  for (let index = 1; index < fittedSize; index++) await page.keyboard.press('ArrowDown');
  await selected(firstIds.at(-1));
  const priorScroll = await page.locator('.table-scroll').evaluate(node => node.scrollTop);
  await page.keyboard.press('Enter');
  await page.getByRole('button', { name: '下一题', exact: true }).click();
  await page.waitForFunction(expected => document.querySelector('.tb-workbench')?.dataset.problemId === expected, secondIds[0]);
  await page.getByRole('button', { name: '返回列表', exact: true }).click();
  await status(1, rows.length, fittedSize);
  assert.equal(await page.locator('.problem-table tr[data-selected="true"]').count(), 0, 'returning from practice clears special row marks');
  assert.ok(Math.abs(await page.locator('.table-scroll').evaluate(node => node.scrollTop) - priorScroll) < 2, 'returning restores the original list scroll position');
  await openSettings(page,'交互与导航');
  assert.equal(await page.getByLabel('题库每页题数',{exact:true}).count(), 0, 'Adaptive pagination has no obsolete page-size setting');
  assert.equal(await page.getByText('题库每页题数',{exact:true}).count(), 0);
  await page.locator('.sidebar').getByRole('button',{name:'题库',exact:true}).click();
  await status(1, rows.length, fittedSize);
  await page.setViewportSize({ width: 1480, height: 620 });
  await page.waitForFunction(prior => document.querySelectorAll('.problem-table tbody tr[data-id]').length < prior, fittedSize);
  const smallerSize = await tableRows.count();
  assert.ok(smallerSize > 0, 'A short window still shows a usable page');
  await status(1, rows.length, smallerSize);
  await page.setViewportSize({ width: 1480, height: 920 });
  await status(1, rows.length, fittedSize);
  await page.getByLabel('题库下一页').click();
  await status(2, rows.length, fittedSize);
  await page.getByRole('textbox', { name: '搜索题目', exact: true }).fill('分页练习00000');
  await status(1, 1, fittedSize);
  assert.equal(await tableRows.count(), 1);
  assert.ok(await page.getByLabel('题库上一页').isDisabled());
  assert.ok(await page.getByLabel('题库下一页').isDisabled());
  await page.getByRole('textbox', { name: '搜索题目', exact: true }).fill('没有这道题');
  await status(1, 0, fittedSize);
  assert.equal(await tableRows.count(), 0);
  await page.getByRole('textbox', { name: '搜索题目', exact: true }).fill('分页练习00000');
  await status(1, 1, fittedSize);
  await page.locator('.problem-title').first().click();
  await page.locator('.wb-statement .katex').first().waitFor();
  assert.equal(await page.locator('.wb-statement .katex').count(), 3);
  assert.equal(await page.locator('.wb-statement .katex-error').count(), 0);
  await page.evaluate(() => document.fonts.ready);
  assert.ok(await page.evaluate(() => document.fonts.check('16px KaTeX_Main')), 'KaTeX fonts are available');
  assert.ok((await page.locator('.wb-statement pre').textContent()).includes('\\(code\\) $$$code$$$'));
  await page.getByRole('button', { name: '题解', exact: true }).click();
  await page.locator('.reader-panel .katex').first().waitFor();
  assert.equal(await page.locator('.reader-panel .katex').count(), 3);
  assert.equal(await page.locator('.reader-panel .katex-error').count(), 0);
  await mkdir('tests/screenshots', { recursive: true });
  await page.screenshot({ path: 'tests/screenshots/issues-math.png', animations: 'disabled' });
  await page.getByRole('button', { name: '收起题解', exact: true }).click();
  await page.keyboard.press('Control+2');
  await pagination.waitFor();
  await page.screenshot({ path: 'tests/screenshots/issues-pagination.png', animations: 'disabled' });
  for (const width of [1480, 1050, 700]) {
    await page.setViewportSize({ width, height: 760 });
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    assert.ok(await pagination.evaluate(node => node.scrollWidth <= node.clientWidth + 1));
  }
  assert.deepEqual(errors, []);
  console.log('Issues #20, #21, #23 passed: bounded library rows, page controls, filtering/keyboard navigation, sidebar numbers, statement/solution math and responsive layout.');
} finally {
  await browser.close();
  await server.close();
}
