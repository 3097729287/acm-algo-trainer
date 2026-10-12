import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdtemp, mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import { startFixture } from '../../server/leaderboard/tests/local-server.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const folder = path.join(root, '.backups/ranking-connection-fix');
await mkdir(folder, { recursive: true });
const state = await mkdtemp(path.join(folder, 'client-state-'));
const fixture = await startFixture();
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
let mode = 'slow', slowCompleted = false, processHandle, browser;
const rankings = fixture.STORE.rankings.bind(fixture.STORE), rewards = fixture.STORE.rewards.bind(fixture.STORE);
fixture.STORE.rankings = async (id, range) => {
  if (range && Date.parse(range.end) - Date.parse(range.start) > 86400000) {
    if (mode === 'slow') { await wait(5400); slowCompleted = true; }
    if (mode === 'failedBoard') throw new Error('Fixture board unavailable');
  }
  return rankings(id, range);
};
fixture.STORE.rewards = async id => {
  if (mode === 'failedRewards') throw new Error('Fixture rewards unavailable');
  return rewards(id);
};
const env = { ...process.env, TB_OFFLINE: '1', TB_STATE_DIR: state, TB_PACKAGE_PORT: '0',
  TB_LIBRARY_DB: path.join(state, 'tb-library.sqlite3'), TB_ARCHIVE_ROOT: path.join(state, 'imports'),
  TB_BACKUP_DIR: path.join(state, 'backups'), TB_TEST_ACCOUNTS_ENDPOINT: fixture.endpoint, PYTHONIOENCODING: 'utf-8' };
try {
  const frozen = Boolean(process.env.TB_ACCOUNT_TEST_EXE);
  let probe;
  if (frozen) {
    const report = path.join(state, 'probe.json');
    processHandle = spawn(process.env.TB_ACCOUNT_TEST_EXE, ['--serve-account-check', report], { env, windowsHide: true });
    for (let i = 0; i < 300; i++) {
      try { probe = JSON.parse(await readFile(report, 'utf8')); break; } catch { await wait(100); }
      assert.equal(processHandle.exitCode, null, 'Frozen check exited early');
    }
    assert(probe?.ok && probe.frozen);
  } else {
    const python = process.env.TB_TEST_PYTHON || 'python';
    processHandle = spawn(python, [path.join(root, 'frontend/tests/accounts-server.py'), fixture.endpoint],
      { env, windowsHide: true, stdio: ['pipe', 'pipe', 'pipe'] });
    probe = await new Promise((resolve, reject) => {
      let line = '';
      const timeout = setTimeout(() => reject(new Error('Client check did not start')), 30000);
      processHandle.stdout.on('data', value => { line += value; if (line.includes('\n')) { clearTimeout(timeout); resolve(JSON.parse(line.split('\n')[0])); } });
      processHandle.once('exit', code => { clearTimeout(timeout); reject(new Error('Client exited: ' + code)); });
    });
  }
  const base = probe.baseUrl;
  assert.equal(new URL(base).hostname, '127.0.0.1'); assert.notEqual(new URL(base).port, '18765');
  browser = await chromium.launch({ channel: process.env.CI ? undefined : 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  page.setDefaultTimeout(20000);
  const errors = []; page.on('pageerror', error => errors.push(error.message));
  const get = async route => { const response = await page.request.get(base + '/api/' + route); assert.equal(response.status(), 200); return response.json(); };
  const post = async (route, data) => { const auth = await get('account'); const response = await page.request.post(base + '/api/' + route, { data, headers: { 'X-TB-Token': auth.token } }); assert.equal(response.status(), 200); return response.json(); };
  await post('account/register', { loginId: 'ranking_fixture', nickname: '排行验证者', password: 'fixture-password' });
  await post('account/login', { loginId: 'ranking_fixture', password: 'fixture-password' });
  await page.goto(base);
  await page.getByRole('button', { name: '排行榜', exact: true }).click();
  await page.getByRole('heading', { name: '服务已连接', exact: true }).waitFor();
  const until = async status => {
    for (let i = 0; i < 200; i++) {
      const value = await get('leaderboard?period=daily');
      if (value.status === status) return value;
      await wait(100);
    }
    throw new Error('Ranking never reached ' + status);
  };
  assert.equal((await until('ready')).hasSnapshot, true);
  assert(slowCompleted, 'Slow response was not exercised');
  mode = 'failedBoard'; await post('leaderboard/sync', {});
  assert.equal((await until('error')).hasSnapshot, true);
  await page.getByRole('button', { name: '同步与刷新', exact: true }).click();
  await page.getByRole('heading', { name: '榜单已读取', exact: true }).waitFor();
  assert.equal(await page.getByText('排行榜暂时无法连接', { exact: true }).count(), 0);
  await page.getByText('部分数据刷新未完成，后台将重试。', { exact: false }).waitFor();
  await page.screenshot({ path: path.join(state, 'partial-ranking.png'), fullPage: true });
  mode = 'failedRewards'; await post('leaderboard/sync', {});
  assert.equal((await until('error')).hasSnapshot, true);
  for (const period of ['daily', 'weekly', 'total']) assert.equal((await get('leaderboard?period=' + period)).hasSnapshot, true);
  mode = 'ready'; await post('leaderboard/sync', {}); await until('ready');
  await page.getByRole('button', { name: '同步与刷新', exact: true }).click();
  await page.getByRole('heading', { name: '服务已连接', exact: true }).waitFor();
  assert.deepEqual(errors, []);
  console.log(JSON.stringify({ ok: true, frozen, slowResponseSeconds: 5.4, emptyBoardPreserved: true,
    partialFailurePreserved: true, rewardsFailurePreserved: true, recovery: true, state }));
} finally {
  await browser?.close();
  if (processHandle && processHandle.exitCode == null) {
    const ended = once(processHandle, 'exit');
    if (process.env.TB_ACCOUNT_TEST_EXE) await writeFile(path.join(state, 'probe.stop'), 'stop');
    else processHandle.stdin.end('stop\n');
    await Promise.race([ended, wait(15000)]);
    if (processHandle.exitCode == null) processHandle.kill();
  }
  await fixture.close();
}
