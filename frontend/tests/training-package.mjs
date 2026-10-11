import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const root = resolve(fileURLToPath(new URL('../..', import.meta.url)));
assert.ok(process.env.PROBE_PATH && process.env.TRAINING_UI_RECORD && process.env.SCREENSHOT_DIR);
const probe = JSON.parse(await readFile(process.env.PROBE_PATH, 'utf8'));
assert.ok(probe.ok && probe.frozen);
assert.ok(resolve(probe.state).startsWith(resolve(root, '.backups') + sep), 'All writes require disposable state.');
const base = new URL(probe.baseUrl);
assert.equal(base.hostname, '127.0.0.1');
assert.ok(base.port && base.port !== '18765');
const browser = await chromium.launch({ channel: process.env.CI ? undefined : 'msedge', headless: true });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
page.setDefaultTimeout(15000);
await page.addInitScript(() => localStorage.setItem('tb.preferences', JSON.stringify({ theme: 'dark', fontSize: 18, accent: 'violet', navOrder: ['mine', 'today', 'library'], navGroups: { mine: '训练与待办', today: '训练与待办' } })));
const errors = [];
page.on('pageerror', issue => errors.push(issue.message));
const get = async path => {
  const response = await page.request.get(new URL('/api/' + path, base).href);
  assert.equal(response.ok(), true, path);
  return response.json();
};
let token;
const post = async (path, body) => {
  const response = await page.request.post(new URL('/api/' + path, base).href, { data: body, headers: { Origin: base.origin, 'X-TB-Token': token } });
  assert.equal(response.ok(), true, path + ': ' + await response.text());
  return response.json();
};
const recordPath = resolve(process.env.TRAINING_UI_RECORD);
const phase = process.env.TRAINING_UI_PHASE;
try {
  const data = await get('data');
  token = data.token;
  assert.equal((await get('profile')).profile.userId, probe.profile.userId);
  if (phase === 'prepare') {
    assert.equal((await get('workspace')).summary.total, 0);
    const ids = ['周赛 163::A', 'ABC 469::A'];
    assert.ok(ids.every(id => data.rows.some(row => row.id === id)));
    for (const id of ids) await post('training/start', { id });
    const code = '// disposable upgrade draft\nint main() { return 0; }\n';
    await post('draft', { id: ids[0], code });
    const deadline = new Date(Date.now() + 365 * 86400000).toISOString().slice(0, 10);
    const goals = (await post('goals/save', { title: 'CF 2200', kind: 'cf', deadline, currentRating: 1200, targetRating: 2200, dailyMinutes: 90 })).goals;
    await writeFile(recordPath, JSON.stringify({ ids, code, goals: goals.map(goal => ({ id: goal.id, title: goal.title, deadline: goal.deadline, progress: goal.progress })), profile: probe.profile.userId, summary: (await get('workspace')).summary, submissions: (await get('submissions')).total }, null, 2));
    console.log('Prepared existing disposable training, draft, goal and identity with the previous installed interface.');
  } else {
    if (phase === 'upgrade') {
      const record = JSON.parse(await readFile(recordPath, 'utf8'));
      assert.equal(probe.profile.userId, record.profile);
      assert.deepEqual((await get('workspace')).summary, record.summary);
      assert.equal((await get('problem?id=' + encodeURIComponent(record.ids[0]))).draft, record.code);
      assert.equal((await get('submissions')).total, record.submissions);
      assert.deepEqual((await get('goals')).goals.map(goal => ({ id: goal.id, title: goal.title, deadline: goal.deadline, progress: goal.progress })), record.goals);
    } else {
      assert.equal(phase, 'fresh');
      assert.equal((await get('workspace')).summary.total, 0);
    }
    await page.goto(base.href);
    await page.getByRole('button', { name: '我的训练', exact: true }).waitFor();
    assert.equal(await page.getByRole('tab', { name: '今日待办', exact: true }).count(), 0);
    assert.equal(await page.locator('.sidebar').getByText('快捷操作', { exact: true }).count(), 0);
    if (phase === 'upgrade') {
      await page.getByLabel('目标每日任务').waitFor();
      await page.locator('.problem-table tr[data-id]').first().waitFor();
      assert.equal(await page.locator('.problem-table tr[data-id]').count(), 2);
      assert.ok(await page.getByLabel('目标每日任务').evaluate(node => node.getBoundingClientRect().height < 140));
      const details = page.locator('.training-goal-details');
      assert.equal(await details.getAttribute('open'), null, 'recommended problems and warnings start collapsed');
      await details.locator('summary').click();
      assert.equal(await details.getAttribute('open'), '');
      await details.locator('summary').click();
    } else await page.getByRole('heading', { name: '从第一道题开始', exact: true }).waitFor();
    await mkdir(process.env.SCREENSHOT_DIR, { recursive: true });
    await page.screenshot({ path: resolve(process.env.SCREENSHOT_DIR, `training-${phase}-1920.png`), animations: 'disabled' });
    await page.getByRole('button', { name: '成就', exact: true }).click();
    const achievements = page.getByRole('dialog');
    await achievements.getByText('首次 AC', { exact: true }).waitFor();
    const copy = await achievements.innerText();
    assert.ok(!copy.includes('官方'), copy);
    assert.ok(!copy.includes('样例通过不计入'), copy);
    assert.equal(await achievements.locator('.progress-achievement').count(), 18, 'all existing achievement definitions remain');
    await page.screenshot({ path: resolve(process.env.SCREENSHOT_DIR, `achievements-${phase}-1920.png`), animations: 'disabled' });
    await page.keyboard.press('Escape');
    await page.keyboard.press('Control+5');
    await page.getByRole('group', { name: '组题方式', exact: true }).waitFor();
    const modeRows = await page.locator('.mock-mode-options button').evaluateAll(nodes => nodes.map(node => node.getBoundingClientRect().y));
    assert.equal(new Set(modeRows).size, 1);
    await page.screenshot({ path: resolve(process.env.SCREENSHOT_DIR, `mock-types-${phase}-1920.png`), animations: 'disabled' });
    await page.keyboard.press('Control+0');
    assert.equal(await page.getByLabel('导航名称 today').count(), 0);
    await page.getByRole('button', { name: '快捷操作', exact: true }).click();
    await page.getByRole('dialog', { name: '快捷操作', exact: true }).waitFor();
    assert.equal(await page.getByRole('dialog').getByRole('button', { name: /打开今日待办/ }).count(), 0);
    await page.keyboard.press('Escape');
    await page.screenshot({ path: resolve(process.env.SCREENSHOT_DIR, `settings-${phase}-1920.png`), animations: 'disabled' });
    assert.deepEqual(errors, []);
    await writeFile(resolve(process.env.SCREENSHOT_DIR, `package-${phase}.json`), JSON.stringify({ ok: true, frozen: true, phase, problems: data.rows.length, sourceState: probe.state, summary: (await get('workspace')).summary, verified: ['unified training', 'compact goal and expandable recommendations', 'all 18 AC achievement descriptions', 'four mock types on one row', 'commands in settings', 'legacy preferences compatibility', ...(phase === 'upgrade' ? ['training, goal, draft, identity and history preserved'] : ['fresh personal state'])] }, null, 2));
    console.log(`Packaged ${phase} UI passed against the existing frozen backend with isolated personal state.`);
  }
} finally { await browser.close(); }
