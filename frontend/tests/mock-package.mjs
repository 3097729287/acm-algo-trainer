import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const root = resolve(fileURLToPath(new URL('../..', import.meta.url)));
assert.ok(process.env.PROBE_PATH && process.env.MOCK_UI_RECORD, 'Supply an isolated --serve-check report and a disposable record path.');
const probe = JSON.parse((await readFile(process.env.PROBE_PATH, 'utf8')).replace(/^\uFEFF/, ''));
assert.ok(probe.ok && probe.frozen);
assert.ok(resolve(probe.state).startsWith(resolve(root, '.backups') + sep), 'Only disposable development state is permitted.');
const recordPath = resolve(process.env.MOCK_UI_RECORD);
assert.ok(recordPath.startsWith(resolve(root, '.backups') + sep));
const target = new URL(probe.baseUrl);
assert.equal(target.protocol, 'http:');
assert.equal(target.hostname, '127.0.0.1');
assert.ok(target.port && target.port !== '18765');
const base = target.origin, resume = process.env.MOCK_UI_PHASE === 'resume';
const browser = await chromium.launch({ channel: process.env.CI ? undefined : 'msedge', headless: true });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
page.setDefaultTimeout(15000);
const errors = [];
page.on('pageerror', error => errors.push(error.message));
let token;
const get = async path => {
  const response = await page.request.get(base + '/api/' + path);
  assert.equal(response.ok(), true, path + ': ' + response.status());
  return response.json();
};
const post = async (path, body) => {
  const response = await page.request.post(base + '/api/' + path, { data: body, headers: { 'X-TB-Token': token, Origin: base } });
  assert.equal(response.ok(), true, path + ': ' + await response.text());
  return response.json();
};
const savedProblem = (contestId, id) => get('problem?id=' + encodeURIComponent(id) + '&contestId=' + encodeURIComponent(contestId));
const select = async slot => {
  await page.getByRole('button', { name: /^选择比赛题目/ }).click();
  await page.getByRole('menuitemradio').filter({ hasText: slot.title }).click();
  await page.waitForFunction(id => document.querySelector('.tb-workbench')?.dataset.problemId === id
    && document.querySelector('.cm-content')?.getAttribute('contenteditable') === 'true', slot.id);
};
const editor = page.getByRole('textbox', { name: 'C++ 代码' });
const screenshotDir = process.env.SCREENSHOT_DIR;
try {
  const catalog = await get('data');
  token = catalog.token;
  assert.equal((await get('profile')).profile.userId, probe.profile.userId, 'Never test another installation or personal profile.');
  let record;
  if (resume) {
    record = JSON.parse(await readFile(recordPath, 'utf8'));
    const current = (await get('workspace')).activeContest;
    assert.equal(current.id, record.contest.id);
    assert.equal(current.deadline, record.contest.deadline);
    assert.equal((await savedProblem(current.id, current.slots[0].id)).draft, record.codeA);
    assert.equal((await savedProblem(current.id, current.slots[1].id)).draft, record.codeB);
  } else {
    assert.equal((await get('workspace')).activeContest, null);
    const plan = (await post('contests/preview', { mode: 'comprehensive', count: 6, duration: 120,
      min: 0, max: 10000, excludeSolved: false, reviewedOnly: false, rules: 'acm' })).plan;
    assert.equal(plan.slots.length, 6);
    const contest = (await post('contests/start', { previewId: plan.previewId,
      ids: plan.slots.map(slot => slot.id), duration: 120, name: '模拟赛界面隔离验证' })).contest;
    record = { contest, codeA: '// isolated mock A\nint main() { return 1; }', codeB: '// isolated mock B\nint main() { return 2; }' };
    await writeFile(recordPath, JSON.stringify(record, null, 2));
  }
  await page.goto(base);
  await page.locator('.live-contest').waitFor();
  await page.keyboard.press('Control+5');
  await page.waitForFunction(() => document.querySelector('.mock-focus .cm-content')?.getAttribute('contenteditable') === 'true');
  assert.equal(await page.locator('.sidebar').isVisible(), false);
  assert.equal(await page.locator('.topbar').isVisible(), false);
  assert.equal(await page.getByRole('timer', { name: '比赛剩余时间' }).isVisible(), true);
  assert.equal(await page.getByRole('button', { name: '题解', exact: true }).count(), 0);
  const locked = await page.request.get(base + '/api/solution?id=' + encodeURIComponent(record.contest.slots[0].id));
  assert.equal(locked.status(), 403);
  for (const [width, height] of [[1920, 1080], [1050, 700]]) {
    await page.setViewportSize({ width, height });
    assert.ok(await page.locator('.wb-toolbar').evaluate(node => node.getBoundingClientRect().height <= 44));
    assert.ok(await page.locator('.wb-body').evaluate(node => node.getBoundingClientRect().height >= innerHeight - 44));
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  }
  if (resume) assert.equal(await editor.innerText(), record.codeA);
  else {
    const saved = page.waitForResponse(response => response.url().endsWith('/api/draft') && response.request().postDataJSON()?.code === record.codeA);
    await editor.fill(record.codeA);
    await editor.press('Control+s');
    await saved;
  }
  await select(record.contest.slots[1]);
  if (resume) assert.equal(await editor.innerText(), record.codeB);
  else {
    const saved = page.waitForResponse(response => response.url().endsWith('/api/draft') && response.request().postDataJSON()?.code === record.codeB);
    await editor.fill(record.codeB);
    await editor.press('Control+s');
    await saved;
  }
  await select(record.contest.slots[0]);
  assert.equal(await editor.innerText(), record.codeA);
  assert.equal((await savedProblem(record.contest.id, record.contest.slots[1].id)).draft, record.codeB);
  if (screenshotDir) {
    await mkdir(screenshotDir, { recursive: true });
    await page.screenshot({ path: resolve(screenshotDir, 'mock-packaged-' + (resume ? 'resume' : 'start') + '.png'), animations: 'disabled' });
  }
  if (resume) {
    await page.getByRole('button', { name: '结束比赛', exact: true }).click();
    await page.getByRole('dialog').getByRole('button', { name: '结束并复盘', exact: true }).click();
    await page.locator('.record-detail').waitFor();
    assert.equal(await page.locator('.sidebar').isVisible(), true);
    assert.equal((await get('workspace')).activeContest, null);
  }
  assert.deepEqual(errors, []);
  const result = { ok: true, phase: resume ? 'resume' : 'start', program: probe.root,
    state: probe.state, contestId: record.contest.id, draftsPreserved: true, errors };
  if (screenshotDir) await writeFile(resolve(screenshotDir, 'mock-packaged-' + result.phase + '.json'), JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result));
} finally {
  await browser.close();
}
