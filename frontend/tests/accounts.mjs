import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdtemp, mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { once } from 'node:events';
import { chromium } from 'playwright';
import { startFixture } from '../../server/leaderboard/tests/local-server.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const folder = path.join(root, '.backups/registered-accounts');
await mkdir(folder, { recursive: true });
const state = await mkdtemp(path.join(folder, 'ui-state-'));
const service = await startFixture();
const environment = { ...process.env, TB_OFFLINE: '1', TB_STATE_DIR: state, TB_PACKAGE_PORT: '0',
  TB_BACKUP_DIR: path.join(state, 'backups'), TB_LIBRARY_DB: path.join(state, 'tb-library.sqlite3'),
  TB_ARCHIVE_ROOT: path.join(state, 'imports'), TB_TEST_ACCOUNTS_ENDPOINT: service.endpoint,
  PYTHONIOENCODING: 'utf-8' };
let processHandle, browser, probe;
const wait = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds));
try {
  if (process.env.TB_ACCOUNT_TEST_EXE) {
    const report = path.join(state, 'probe.json');
    processHandle = spawn(process.env.TB_ACCOUNT_TEST_EXE, ['--serve-account-check', report], { env: environment, windowsHide: true });
    for (let i = 0; i < 300; i++) {
      try { probe = JSON.parse(await readFile(report, 'utf8')); break; } catch { await wait(100); }
      if (processHandle.exitCode != null) throw new Error('Frozen account probe exited early');
    }
    assert(probe?.ok && probe.frozen);
  } else {
    const python = process.env.TB_TEST_PYTHON || process.env.TB_PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
    processHandle = spawn(python, [path.join(root, 'frontend/tests/accounts-server.py'), service.endpoint], { env: environment, windowsHide: true, stdio: ['pipe', 'pipe', 'pipe'] });
    let output = '';
    processHandle.stderr.on('data', value => { output += value.toString(); });
    probe = await new Promise((resolve, reject) => {
      let line = '';
      const timeout = setTimeout(() => reject(new Error('Account UI server timed out')), 30000);
      processHandle.stdout.on('data', value => { line += value.toString(); if (line.includes('\n')) { clearTimeout(timeout); resolve(JSON.parse(line.split('\n')[0])); } });
      processHandle.once('exit', code => { clearTimeout(timeout); reject(new Error('Account UI server failed: ' + code + ' ' + output)); });
    });
  }
  const base = probe.baseUrl;
  assert.equal(new URL(base).hostname, '127.0.0.1'); assert.notEqual(new URL(base).port, '18765');
  browser = await chromium.launch({ channel: process.env.CI ? undefined : 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = []; page.on('pageerror', issue => errors.push(issue.message)); page.setDefaultTimeout(15000);
  const get = async name => { const result = await page.request.get(base + '/api/' + name); assert.equal(result.status(), 200); return result.json(); };
  const post = async (name, body) => { const auth = await get('account'); const result = await page.request.post(base + '/api/' + name, { data: body, headers: { 'X-TB-Token': auth.token } }); assert.equal(result.status(), 200, await result.text()); return result.json(); };
  await page.goto(base);
  await page.getByRole('heading', { name: '登录 TB' }).waitFor();
  assert.equal(await page.locator('.nav-item').count(), 0);
  assert.equal((await page.request.get(base + '/api/data')).status(), 401);
  assert.equal(await page.getByText('忘记密码', { exact: true }).count(), 0);
  await page.getByRole('tab', { name: '注册', exact: true }).click();
  await page.getByLabel('昵称', { exact: true }).fill('星河');
  await page.getByLabel('登录号', { exact: true }).fill('ui_account_a');
  await page.getByLabel('密码', { exact: true }).fill('fixture-password');
  await page.getByLabel('确认密码', { exact: true }).fill('incorrect-password');
  await page.getByRole('button', { name: '注册账号', exact: true }).click();
  await page.getByRole('alert').getByText('两次输入的密码不一致').waitFor();
  await page.getByLabel('确认密码', { exact: true }).fill('fixture-password');
  await page.getByRole('button', { name: '注册账号', exact: true }).click();
  await page.getByText('注册成功，请用登录号和密码登录。').waitFor();
  assert.equal(await page.locator('.nav-item').count(), 0);
  await page.getByLabel('密码', { exact: true }).fill('incorrect-password');
  await page.getByRole('button', { name: '登录', exact: true }).click();
  await page.getByText('登录号或密码错误', { exact: true }).waitFor();
  await page.getByLabel('密码', { exact: true }).fill('fixture-password');
  let releaseStale, staleReady, staleDone;
  const held = new Promise(resolve => { releaseStale = resolve; });
  const captured = new Promise(resolve => { staleReady = resolve; });
  const completed = new Promise(resolve => { staleDone = resolve; });
  let capturedOnce = false;
  const staleAccount = async route => {
    if (capturedOnce) return route.continue();
    capturedOnce = true;
    const response = await route.fetch();
    assert.equal((await response.json()).authenticated, false);
    staleReady();
    await held;
    await route.fulfill({ response });
    staleDone();
  };
  await page.route('**/api/account', staleAccount);
  try {
    await page.evaluate(() => window.dispatchEvent(new Event('focus')));
    await captured;
    await page.getByRole('button', { name: '登录', exact: true }).click();
    await page.locator('.nav-item').first().waitFor();
  } finally { releaseStale(); }
  await completed;
  await page.waitForTimeout(200);
  assert.ok(await page.locator('.nav-item').count(), 'A stale account poll cannot undo a successful login');
  await page.unroute('**/api/account', staleAccount);
  const a = await get('account'); assert.equal(a.account.nickname, '星河');
  const library = await get('data'), problemId = library.rows[0].id;
  await post('training/start', { id: problemId });
  await page.evaluate(id => localStorage.setItem(`tb.draft.v2.solo.${encodeURIComponent(id)}`, JSON.stringify({ code: 'old private browser draft', dirty: true, version: 1, owner: 'legacy' })), problemId);
  await page.reload();
  await page.locator('tr[data-id] .problem-title').first().click();
  const editor = page.getByRole('textbox', { name: 'C++ 代码', exact: true });
  await editor.waitFor();
  await page.waitForFunction(() => document.querySelector('.cm-content')?.textContent.includes('old private browser draft'));
  assert((await editor.innerText()).includes('old private browser draft'));
  await page.getByRole('button', { name: '返回列表', exact: true }).click();
  await page.getByRole('button', { name: '偏好设置', exact: true }).click();
  await page.getByRole('tab', { name: '账号与身份', exact: true }).click();
  await page.getByText('登录号：ui_account_a', { exact: true }).waitFor();
  await page.getByLabel('用户昵称', { exact: true }).fill('新昵称');
  await page.getByRole('button', { name: '保存昵称', exact: true }).click();
  await page.getByText('昵称已保存。').waitFor();
  assert.equal((await get('profile')).profile.displayName, '新昵称');
  await page.getByLabel('原密码', { exact: true }).fill('fixture-password');
  await page.getByLabel('新密码', { exact: true }).fill('next-fixture-password');
  await page.getByLabel('确认新密码', { exact: true }).fill('next-fixture-password');
  await page.getByRole('button', { name: '修改密码', exact: true }).click();
  await page.getByText('密码已修改，其他设备需要重新登录。').waitFor();
  await page.getByRole('button', { name: '退出账号', exact: true }).click();
  await page.getByRole('heading', { name: '登录 TB' }).waitFor();
  assert.equal((await page.request.get(base + '/api/workspace')).status(), 401);
  await post('account/register', { loginId: 'ui_account_b', nickname: '另一个账号', password: 'fixture-password' });
  await page.getByLabel('登录号', { exact: true }).fill('ui_account_b');
  await page.getByLabel('密码', { exact: true }).fill('fixture-password');
  await page.getByRole('button', { name: '登录', exact: true }).click();
  await page.locator('.nav-item').first().waitFor();
  assert.equal((await get('workspace')).summary.total, 0);
  await post('training/start', { id: problemId });
  await page.reload();
  await page.locator('tr[data-id] .problem-title').first().click();
  await editor.waitFor();
  await page.waitForFunction(() => document.querySelector('.cm-content')?.getAttribute('contenteditable') === 'true');
  assert(!(await editor.innerText()).includes('old private browser draft'));
  await page.getByRole('button', { name: '返回列表', exact: true }).click();
  await post('account/logout', {});
  await page.reload();
  await page.getByRole('heading', { name: '登录 TB' }).waitFor();
  await page.getByLabel('登录号', { exact: true }).fill('ui_account_a');
  await page.getByLabel('密码', { exact: true }).fill('next-fixture-password');
  await page.getByRole('button', { name: '登录', exact: true }).click();
  await page.locator('.nav-item').first().waitFor();
  assert.equal((await get('problem?id=' + encodeURIComponent(problemId))).draft, 'old private browser draft');
  await post('account/logout', {}); await page.reload();
  await page.getByRole('heading', { name: '登录 TB' }).waitFor();
  await page.setViewportSize({ width: 390, height: 844 });
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= 390));
  await page.screenshot({ path: path.join(state, 'login-mobile.png'), fullPage: true });
  assert.deepEqual(errors, []);
  console.log(JSON.stringify({ ok: true, frozen: Boolean(probe.frozen), wholeAppLogin: true, registration: true,
    passwordChange: true, accountIsolation: true, legacyBrowserDrafts: true, mobile: true, state }));
} finally {
  await browser?.close();
  if (processHandle && processHandle.exitCode == null) {
    const ended = once(processHandle, 'exit');
    if (process.env.TB_ACCOUNT_TEST_EXE) await writeFile(path.join(state, 'probe.stop'), 'stop');
    else processHandle.stdin.end('stop\n');
    await Promise.race([ended, wait(15000)]);
    if (processHandle.exitCode == null) processHandle.kill();
  }
  await service.close();
}
