import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdtemp, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { startFixture } from '../../server/leaderboard/tests/local-server.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const folder = path.join(root, '.backups/v110-leaderboard');
await mkdir(folder, { recursive: true });
const state = await mkdtemp(path.join(folder, 'client-state-'));
const fixture = await startFixture();
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const save = fixture.STORE.savePublicProfile.bind(fixture.STORE);
const uploads = [];
fixture.STORE.savePublicProfile = async (...args) => { uploads.push(args[4]); return save(...args); };
let child;
try {
  child = spawn(process.env.TB_TEST_PYTHON || 'python', [path.join(root, 'frontend/tests/accounts-server.py'), fixture.endpoint], {
    env: { ...process.env, TB_OFFLINE: '1', TB_STATE_DIR: state, TB_PACKAGE_PORT: '0',
      TB_LIBRARY_DB: path.join(state, 'tb-library.sqlite3'), TB_ARCHIVE_ROOT: path.join(state, 'imports'),
      TB_BACKUP_DIR: path.join(state, 'backups'), TB_TEST_ACCOUNTS_ENDPOINT: fixture.endpoint, PYTHONIOENCODING: 'utf-8' },
    windowsHide: true, stdio: ['pipe', 'pipe', 'pipe'],
  });
  const probe = await new Promise((resolve, reject) => {
    let line = '';
    const timeout = setTimeout(() => reject(new Error('Client did not start')), 30000);
    child.stdout.on('data', value => { line += value; if (line.includes('\n')) { clearTimeout(timeout); resolve(JSON.parse(line.split('\n')[0])); } });
    child.once('exit', code => { clearTimeout(timeout); reject(new Error('Client exited: ' + code)); });
  });
  const base = probe.baseUrl;
  assert.equal(new URL(base).hostname, '127.0.0.1');
  async function get(route) {
    const response = await fetch(base + '/api/' + route);
    assert.equal(response.status, 200); return response.json();
  }
  async function post(route, data) {
    const auth = await get('account');
    const response = await fetch(base + '/api/' + route, { method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-TB-Token': auth.token }, body: JSON.stringify(data) });
    assert.equal(response.status, 200); return response.json();
  }
  async function ready() {
    for (let index = 0; index < 300; index++) {
      const value = await get('leaderboard?period=daily');
      if (value.status === 'ready') return value;
      if (value.status === 'error') throw new Error(value.error);
      await wait(100);
    }
    throw new Error('Ranking sync did not finish');
  }
  await post('account/register', { loginId: 'public_progress_fixture', nickname: '成长验证者', password: 'fixture-password' });
  await post('account/login', { loginId: 'public_progress_fixture', password: 'fixture-password' });
  const board = await ready();
  const expected = (await get('insights')).publicProgress;
  const actual = await fixture.STORE.publicProgress(board.self.userId);
  assert(actual && Number.isInteger(actual.level));
  if (expected) assert.deepEqual(actual, expected);
  assert.deepEqual(board.self.publicProgress, actual);
  assert.equal(board.self.count, 0);
  assert.match(board.self.publicId, /^TB-[0-9A-F]{32}$/);
  assert.equal(uploads.length, 1);
  await post('leaderboard/sync', {}); await ready();
  assert.equal(uploads.length, 1, 'Unchanged summaries should not be uploaded again');
  assert(!JSON.stringify(board).includes('public_progress_fixture'));
  const report = { publicProgressUploaded: true, unchangedUploadSkipped: true, zeroAcVisible: true,
    publicIdWithoutLogin: true, summary: actual, isolatedState: state };
  await writeFile(path.join(folder, 'client-public-progress-report.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report));
} finally {
  if (child && child.exitCode == null) {
    const ended = once(child, 'exit'); child.stdin.end('stop\n');
    await Promise.race([ended, wait(15000)]);
    if (child.exitCode == null) child.kill();
  }
  await fixture.close();
}
