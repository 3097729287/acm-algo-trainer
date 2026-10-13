import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdtemp, mkdir, readFile, realpath, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { basename, join, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import { chromium } from 'playwright';

const root = resolve(fileURLToPath(new URL('../..', import.meta.url)));
const state = await mkdtemp(join(tmpdir(), 'tb-detailed-ui-'));
const screenshots = join(root, 'frontend/tests/screenshots');
const service = spawn(process.env.TB_PYTHON || 'python', [join(root, 'frontend/tests/local-api-server.py')], {
  cwd: root, windowsHide: true,
  env: { ...process.env, TB_STATE_DIR: state, TB_OFFLINE: '1', PYTHONIOENCODING: 'utf-8' },
});
let stderr = '', vite, browser, page;
service.stderr.on('data', chunk => { stderr += chunk; });
const errors = [];
try {
  const apiUrl = await new Promise((done, fail) => {
    const timer = setTimeout(() => fail(new Error('API startup timeout: ' + stderr)), 30000);
    service.stdout.on('data', chunk => {
      const match = String(chunk).match(/http:\/\/127\.0\.0\.1:\d+/);
      if (match) { clearTimeout(timer); done(match[0]); }
    });
    service.on('exit', code => { clearTimeout(timer); fail(new Error('API exited: ' + code + stderr)); });
  });
  process.env.TB_API_URL = apiUrl;
  vite = await createServer({ root: join(root, 'frontend'), server: { host: '127.0.0.1', port: 0 } });
  await vite.listen();
  const url = `http://127.0.0.1:${vite.httpServer.address().port}`;
  browser = await chromium.launch({ channel: process.env.CI ? undefined : 'msedge', headless: true });
  page = await browser.newPage({ viewport: { width: 1480, height: 920 } });
  page.setDefaultTimeout(20000);
  page.on('pageerror', error => errors.push(error.message));
  const pid = 'Div.2 1112::C';
  const get = async path => (await page.request.get(url + '/api/' + path)).json();
  const solution = await get('solution?id=' + encodeURIComponent(pid));
  const defaults = JSON.parse(await readFile(join(root, 'data/library/solutions.json'), 'utf8'));
  const details = JSON.parse(await readFile(join(root, 'data/library/detailed_solutions.json'), 'utf8'));
  assert.equal(solution.markdown, defaults.find(row => row.problem_id === pid).markdown);
  assert.equal(solution.detailedSolution.markdown, details.find(row => row.problem_id === pid).markdown);

  await page.goto(url);
  await page.getByRole('heading', { name: '从第一道题开始', exact: true }).waitFor();
  await page.keyboard.press('Control+2');
  const open = async title => {
    await page.getByRole('textbox', { name: '搜索题目', exact: true }).fill(title);
    await page.getByRole('button', { name: '题解 ' + title, exact: true }).click();
    await page.getByRole('group', { name: '题解版本' }).waitFor();
  };
  await open('Rank Subsequence');
  const panel = page.getByRole('complementary', { name: '题解阅读' });
  const defaultButton = panel.getByRole('button', { name: '默认题解', exact: true });
  const detailedButton = panel.getByRole('button', { name: '详细题解', exact: true });
  assert.equal(await defaultButton.getAttribute('aria-pressed'), 'true');
  assert.equal(await panel.getByText('1. 左秩、右秩到底是什么？', { exact: true }).count(), 0);
  const defaultText = await panel.locator('.reader-content').innerText();
  await detailedButton.focus();
  await page.keyboard.press('Enter');
  await panel.getByRole('heading', { name: '1. 左秩、右秩到底是什么？', exact: true }).waitFor();
  assert.equal(await detailedButton.getAttribute('aria-pressed'), 'true');
  assert.equal(await panel.locator('table').count(), 4);
  assert.equal(await panel.locator('pre').count(), 4);
  assert.equal(await panel.locator('.solution-full').count(), 0, 'Detailed content must not be automatically summarized');
  assert.equal(await panel.locator('.markdown h3').count(), 8);
  await defaultButton.click();
  assert.equal(await panel.locator('.reader-content').innerText(), defaultText);
  await detailedButton.click();
  await panel.getByRole('button', { name: '收起题解', exact: true }).click();
  await open('Rank Subsequence');
  assert.equal(await defaultButton.getAttribute('aria-pressed'), 'true', 'Reopening starts from the original default');
  await open('String Construction');
  await detailedButton.click();
  await panel.getByRole('heading', { name: '详细题解待补充', exact: true }).waitFor();
  assert.equal(await panel.locator('.markdown').count(), 0, 'Missing details must not repeat the default body');
  await panel.getByRole('button', { name: '返回默认题解', exact: true }).click();
  await panel.locator('.markdown').first().waitFor();
  await detailedButton.click();
  await open('Rank Subsequence');
  assert.equal(await defaultButton.getAttribute('aria-pressed'), 'true', 'A different problem starts from its default');
  await detailedButton.click();
  await mkdir(screenshots, { recursive: true });
  for (const [theme, width] of [['light', 1480], ['dark', 1050], ['light', 375]]) {
    await page.setViewportSize({ width, height: 920 });
    await page.evaluate(theme => { document.documentElement.dataset.theme = theme; }, theme);
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    assert.ok(await detailedButton.isVisible());
    await page.screenshot({ path: join(screenshots, `detailed-solutions-${theme}-${width}.png`), animations: 'disabled' });
  }
  await page.setViewportSize({ width: 1480, height: 920 });
  await panel.getByRole('button', { name: '题解全屏', exact: true }).click();
  await page.locator('.reader-full').waitFor();
  assert.equal(await detailedButton.getAttribute('aria-pressed'), 'true');
  await page.screenshot({ path: join(screenshots, 'detailed-solutions-full.png'), animations: 'disabled' });

  // The real API protects the combined response, including the new detailed body.
  const catalog = await get('data');
  const preview = await page.request.post(url + '/api/contests/preview', {
    headers: { 'X-TB-Token': catalog.token }, data: { mode: 'replay', contest: 'Div.2 1112', duration: 30 },
  });
  assert.equal(preview.status(), 200, await preview.text());
  const { plan } = await preview.json();
  const start = await page.request.post(url + '/api/contests/start', {
    headers: { 'X-TB-Token': catalog.token }, data: { ids: plan.slots.map(slot => slot.id), duration: plan.duration, previewId: plan.previewId },
  });
  assert.equal(start.status(), 200, await start.text());
  const locked = await page.request.get(url + '/api/solution?id=' + encodeURIComponent(pid));
  assert.equal(locked.status(), 403);
  assert.ok(!(await locked.text()).includes('第三个样例'));
  assert.deepEqual(errors, []);
  console.log('Detailed solutions passed: exact SQLite bodies, switching, keyboard, default reset, missing state, light/dark/narrow/fullscreen and contest lock.');
} catch (error) {
  console.error('Browser errors:', errors, 'API stderr:', stderr);
  if (page) {
    await mkdir(screenshots, { recursive: true });
    await page.screenshot({ path: join(screenshots, 'detailed-solutions-failure.png') });
  }
  throw error;
} finally {
  await browser?.close();
  await vite?.close();
  if (service.exitCode === null) {
    const closed = new Promise(done => service.once('exit', done));
    service.kill();
    await closed;
  }
  const actual = await realpath(state), temporaryRoot = await realpath(tmpdir());
  assert.ok(actual.startsWith(temporaryRoot + sep) && basename(actual).startsWith('tb-detailed-ui-'));
  await rm(actual, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 });
}
