import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { createServer, preview } from 'vite';
import { chromium } from 'playwright';

// All requests and drafts belong to this fixture, including bundle verification.
const settings = { host: '127.0.0.1', port: 18779, strictPort: true };
const server = process.env.TB_UI_DIST
  ? await preview({ build: { outDir: resolve(process.env.TB_UI_DIST) }, preview: settings })
  : await createServer({ server: settings });
if (!process.env.TB_UI_DIST) await server.listen();
const browser = await chromium.launch({ channel: process.env.CI ? undefined : 'msedge', headless: true });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
page.setDefaultTimeout(15000);
await page.addInitScript(() => localStorage.setItem('tb.preferences', JSON.stringify({ theme: 'dark', fontSize: 18 })));
const errors = [], drafts = new Map(), draftWrites = [], now = () => new Date().toISOString();
page.on('pageerror', error => errors.push(error.message));
const rows = [...'ABCDEF'].map((letter, index) => ({
  id: '模拟赛布局::' + letter, contest: '模拟赛布局', problem: letter,
  title: ['神奇的背包', 'Skibidus and Fanum Tax (hard version)', 'It and le', 'Skibidus and Capping', '小红删树(easy)', 'Hard Demon Problem'][index],
  platform: '牛客', tags: ['不应泄露的考点'], difficulty: 1600, solutionAvailable: true,
}));
let contest = {
  id: 'layout-fixture', name: '模拟赛 · 6 题 / 120 分钟', status: 'running',
  duration: 120, total: 6, accepted: 1, startedAt: now(),
  deadline: new Date(Date.now() + 120 * 60000).toISOString(),
  slots: rows.map((row, index) => ({ id: row.id, title: row.title, letter: 'ABCDEF'[index],
    accepted: index === 5, verdict: index === 5 ? 'AC' : index === 1 ? 'WA' : null })),
};
const workspace = () => ({ now: now(), activeContest: contest.status === 'running' ? contest : null,
  contests: [contest], training: [], sets: [], summary: { total: 0, accepted: 0, attempts: 0, pending: 0 } });
await page.route('**/api/**', async route => {
  const request = route.request(), url = new URL(request.url()), path = url.pathname;
  if (!path.startsWith('/api/')) return route.continue();
  const body = request.method() === 'POST' ? request.postDataJSON() : null;
  if (body) assert.equal(request.headers()['x-tb-token'], 'mock-ui-fixture');
  let value;
  if (path === '/api/account') value = { required: false, authenticated: true, token: 'mock-ui-fixture', account: null };
  else if (path === '/api/data') value = { rows, categories: [], token: 'mock-ui-fixture', today: now().slice(0, 10) };
  else if (path === '/api/software-update') value = {currentVersion:'1.2.1',status:'current',autoCheck:false,canInstall:false};
  else if (path === '/api/browser-preparation') value = {available:false};
  else if (path === '/api/workspace') value = workspace();
  else if (path === '/api/inbox') value = { pending: 0, errors: [] };
  else if (path === '/api/hub' || path === '/api/insights') value = null;
  else if (path === '/api/goals') value = { goals: [] };
  else if (path === '/api/desktop/fullscreen') value = { available: false, fullscreen: false };
  else if (path === '/api/submissions') value = { submissions: [], total: 0 };
  else if (path === '/api/contest') value = { contest };
  else if (path === '/api/problem') {
    const id = url.searchParams.get('id');
    value = { id, title: rows.find(row => row.id === id)?.title, locked: false,
      markdown: '## 题目描述\n\n选择若干物品放入背包，求价值的最大值。\n\n## 输入格式\n\n两个整数 $n$ 和 $m$。',
      samples: [{ name: '样例 1', input: '1 2\n', output: '3\n' }],
      limits: { timeMs: 2000, memoryMb: 256 }, judge: { scope: 'samples', cases: 1 },
      statementAvailable: true, submissions: [], draft: drafts.get((url.searchParams.get('contestId') || 'solo') + ':' + id) || '',
    };
  } else if (path === '/api/draft') {
    draftWrites.push(body);
    await new Promise(done => setTimeout(done, 180));
    drafts.set((body.contestId || 'solo') + ':' + body.id, body.code);
    value = { savedAt: now() };
  } else if (path === '/api/contests/finish') {
    assert.equal(body.contestId, contest.id);
    contest = { ...contest, status: 'finished' };
    value = { contest, workspace: workspace() };
  } else throw new Error('Unhandled fixture request: ' + path);
  await route.fulfill({ json: value });
});
const output = resolve(process.env.SCREENSHOT_DIR || 'tests/screenshots');
const editor = page.getByRole('textbox', { name: 'C++ 代码' });
const picker = () => page.getByRole('button', { name: /^选择比赛题目/ });
const selected = async letter => {
  await page.waitForFunction(id => document.querySelector('.tb-workbench')?.dataset.problemId === id
    && document.querySelector('.cm-content')?.getAttribute('contenteditable') === 'true', '模拟赛布局::' + letter);
};
const geometry = async () => page.evaluate(() => {
  const bounds = selector => {
    const { x, y, width, height } = document.querySelector(selector).getBoundingClientRect();
    return { x, y, width, height };
  };
  return { workbench: bounds('.tb-workbench'), toolbar: bounds('.wb-toolbar'),
    body: bounds('.wb-body'), statement: bounds('.wb-statement-pane'), code: bounds('.wb-code-pane') };
});
const measurements = [];
try {
  await mkdir(output, { recursive: true });
  await page.goto('http://127.0.0.1:18779');
  await page.getByRole('button', { name: '模拟赛', exact: true }).first().waitFor();
  await page.keyboard.press('Control+5');
  await selected('A');
  for (const [width, height] of [[1920, 1080], [1366, 768], [1050, 700], [800, 600], [600, 600]]) {
    await page.setViewportSize({ width, height });
    assert.equal(await page.locator('.sidebar').isVisible(), false);
    assert.equal(await page.locator('.topbar').isVisible(), false);
    assert.equal(await page.locator('.mock-page-tabs').isVisible(), false);
    assert.equal(await page.locator('.contest-tabs,.contest-control').count(), 0);
    assert.equal(await picker().getAttribute('aria-expanded'), 'false');
    assert.equal(await page.getByRole('menu', { name: '模拟赛题目' }).count(), 0);
    const before = await geometry();
    assert.deepEqual(before.workbench, { x: 0, y: 0, width, height });
    assert.ok(before.toolbar.height <= 44, 'only one compact toolbar precedes the two panes: ' + JSON.stringify(before));
    assert.ok(before.body.height >= height - 44, 'contest chrome uses at most 44 pixels');
    assert.equal(before.statement.y, before.code.y);
    assert.ok(before.statement.x < before.code.x && before.statement.width > width * 0.4);
    assert.equal(await editor.isVisible(), true);
    assert.equal(await page.getByRole('timer', { name: '比赛剩余时间' }).isVisible(), true);
    assert.equal(await page.getByRole('button', { name: '结束比赛', exact: true }).isVisible(), true);
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    assert.ok(await page.locator('.wb-toolbar').evaluate(node => node.scrollWidth <= node.clientWidth));
    await picker().click();
    assert.equal(await page.getByRole('menuitemradio').count(), 6);
    assert.deepEqual(await geometry(), before, 'opening the picker never shrinks or moves either pane');
    assert.equal(await page.getByRole('menu').getByText('不应泄露的考点').count(), 0);
    assert.ok(await page.getByRole('menu').evaluate(node => {
      const box = node.getBoundingClientRect();
      const trigger=document.querySelector('.mock-problem-trigger').getBoundingClientRect();
      const item=node.querySelector('.mock-picker-item'),slot=item.getBoundingClientRect();
      return box.left >= 0 && box.right <= innerWidth && box.bottom <= innerHeight && box.top >= trigger.bottom
        && item.contains(document.elementFromPoint(slot.left+slot.width/2,slot.top+slot.height/2));
    }));
    await page.keyboard.press('Escape');
    assert.equal(await picker().evaluate(node => node === document.activeElement), true);
    measurements.push({ width, height, ...before });
    if (width === 1920 || width === 1050) await page.screenshot({ path: resolve(output, 'mock-focus-' + width + '.png'), animations: 'disabled' });
  }
  await page.setViewportSize({ width: 1920, height: 1080 });
  const time = await page.getByRole('timer').textContent();
  await page.waitForFunction(previous => document.querySelector('.mock-timer')?.textContent !== previous, time);

  const codeA = '// A 的草稿\nint main() { return 1; }';
  const savedA = page.waitForResponse(response => response.url().endsWith('/api/draft') && response.request().postDataJSON()?.code === codeA);
  await editor.fill(codeA);
  await editor.press('Control+s');
  await picker().click();
  await page.getByRole('menuitemradio', { name: /^B / }).click();
  await selected('B');
  await savedA;
  assert.equal(drafts.get('layout-fixture:模拟赛布局::A'), codeA);
  assert.equal(await picker().getAttribute('aria-expanded'), 'false');
  assert.equal(await picker().evaluate(node => node === document.activeElement), true);
  const codeB = '// B 的草稿\nint main() { return 2; }';
  await editor.fill(codeB);
  await page.getByRole('button', { name: '下一题', exact: true }).click();
  await selected('C');
  await picker().press('ArrowDown');
  await page.keyboard.press('Home');
  await page.keyboard.press('Enter');
  await selected('A');
  assert.equal(await editor.innerText(), codeA);
  await picker().click();
  await page.locator('.wb-statement').click();
  assert.equal(await picker().getAttribute('aria-expanded'), 'false', 'outside click dismisses the menu');
  await page.locator('.wb-statement').press('2');
  await selected('B');
  assert.equal(await editor.innerText(), codeB);
  await editor.press('3');
  assert.equal(await page.locator('.tb-workbench').getAttribute('data-problem-id'), rows[1].id, 'typing digits in the editor never switches problems');

  await picker().click();
  await page.getByRole('menuitem', { name: '模拟赛记录', exact: true }).click();
  await page.locator('.records-page').waitFor();
  assert.equal(await page.locator('.sidebar').isVisible(), true);
  await page.getByRole('button', { name: '继续比赛', exact: true }).click();
  await selected('B');
  await page.getByRole('button', { name: '返回工作台', exact: true }).click();
  assert.equal(await page.locator('.topbar').isVisible(), true);
  await page.locator('.live-contest').click();
  await selected('B');

  contest.deadline = new Date(Date.now() + 30000).toISOString();
  await page.reload();
  await page.locator('.live-contest').waitFor();
  await page.keyboard.press('Control+5');
  await selected('A');
  await page.locator('.mock-timer.urgent').waitFor();
  assert.equal(await editor.innerText(), codeA, 'reload resumes saved contest drafts');
  await page.evaluate(() => document.documentElement.dataset.theme = 'light');
  await page.setViewportSize({ width: 1050, height: 700 });
  await picker().click();
  await page.screenshot({ path: resolve(output, 'mock-picker-light-1050.png'), animations: 'disabled' });
  await page.keyboard.press('Escape');
  await page.getByRole('button', { name: '结束比赛', exact: true }).click();
  await page.getByRole('alertdialog',{name:'结束比赛确认'}).getByRole('button', { name: '继续比赛', exact: true }).click();
  assert.equal(contest.status, 'running');
  await page.getByRole('button', { name: '结束比赛', exact: true }).click();
  await page.getByRole('alertdialog',{name:'结束比赛确认'}).getByRole('button', { name: '结束并复盘', exact: true }).click();
  await page.locator('.record-detail').waitFor();
  assert.equal(await page.locator('.sidebar').isVisible(), true);
  assert.equal(await page.locator('.topbar').isVisible(), true);
  assert.equal(await page.locator('.mock-focus').count(), 0);
  assert.ok(draftWrites.every(body => body.contestId === 'layout-fixture'), 'all contest saves keep their contest identity');
  assert.deepEqual(errors, []);
  await writeFile(resolve(output, 'mock-layout-check.json'), JSON.stringify({ ok: true, bundle: process.env.TB_UI_DIST || null, measurements, errors }, null, 2));
  console.log('Mock UI: full-height split panes, overlay picker, keyboard, timer, isolated drafts, history/resume and finish passed at five viewport sizes.');
} catch (error) {
  await page.screenshot({ path: resolve(output, 'mock-layout-failure.png'), animations: 'disabled' });
  throw error;
} finally {
  await browser.close();
  await server.close();
}
