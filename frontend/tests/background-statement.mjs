import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import { chromium } from 'playwright';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const artifactDir = path.resolve(root, '..', '.backups', 'frontend-background-checks', 'artifacts');
await fs.mkdir(artifactDir, { recursive: true });
const log = [];
const report = message => { log.push(`${new Date().toISOString()} ${message}`); console.log(message); };
const server = await createServer({ root, server: { host: '127.0.0.1', port: 18779, strictPort: true, hmr: false } });
await server.listen();
let browser, context, page;
const errors = [], externalRequests = [];
try {
  browser = await chromium.launch({ channel: process.env.CI ? undefined : 'msedge', headless: true });
  context = await browser.newContext({ viewport: { width: 1200, height: 760 } });
  await context.route('**/*', route => {
    const url = new URL(route.request().url());
    if (url.origin === 'http://127.0.0.1:18779' || ['data:', 'blob:'].includes(url.protocol)) return route.continue();
    externalRequests.push(url.href);
    return route.abort('blockedbyclient');
  });
  await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
  page = await context.newPage();
  page.setDefaultTimeout(10000);
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('http://127.0.0.1:18779/tests/background-statement-fixture.html');
  const editor = page.getByRole('textbox', { name: 'C++ 代码', exact: true });
  const statement = page.locator('.wb-statement');
  const code = () => page.evaluate(() => window.backgroundStatementFixture.readCode());
  const editable = id => page.waitForFunction(value => document.querySelector('.tb-workbench')?.dataset.problemId === value && document.querySelector('.wb-heading strong')?.textContent === `Fixture ${value} 题目` && document.querySelector('.cm-content')?.getAttribute('contenteditable') === 'true', id);
  const holdPoll = async id => {
    await page.evaluate(value => window.backgroundStatementFixture.arm(value), id);
    await page.waitForFunction(value => window.backgroundStatementFixture.pending().some(row => row.id === value), id);
  };
  const screenshot = name => page.screenshot({ path: path.join(artifactDir, `background-statement-${name}.png`), animations: 'disabled' });
  const noSpinner = async () => assert.equal(await statement.locator('.wb-spinner').count(), 0, 'terminal state removes the statement spinner');

  await editable('A');
  await page.getByText('正在读取原站题面', { exact: true }).waitFor();
  assert.equal(await code(), '// saved draft A\n', 'metadata exposes the saved draft before the statement arrives');
  assert.equal(await editor.getAttribute('aria-readonly'), 'false');
  await editor.fill('// user edits while statement A is pending\nint main() { return 17; }\n');
  await holdPoll('A');
  await editor.press('Control+End');
  await editor.press('Enter');
  await editor.type('// edit with a poll already in flight');
  const userA = await code();
  await screenshot('editable-pending');
  assert.equal(await page.evaluate(() => window.backgroundStatementFixture.release('A', { draft: '// stale server draft A\n' })), 1);
  await statement.getByRole('heading', { name: 'Statement A', exact: true }).waitFor();
  assert.equal(await code(), userA, 'a late statement response cannot overwrite the current editor');
  await noSpinner();
  await screenshot('late-success');
  report('PASS: slow statements expose metadata and an editable saved draft; in-flight statement completion preserves new code.');

  await page.evaluate(() => window.backgroundStatementFixture.changeProblem('B'));
  await editable('B');
  await holdPoll('B');
  await page.evaluate(() => window.backgroundStatementFixture.changeProblem('C'));
  await editable('C');
  await statement.getByRole('heading', { name: 'Statement C', exact: true }).waitFor();
  await editor.fill('// current C code must stay on C');
  assert.equal(await page.evaluate(() => window.backgroundStatementFixture.release('B', { draft: '// late B draft\n' })), 1);
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  assert.equal(await page.locator('.wb-heading strong').textContent(), 'Fixture C 题目');
  assert.equal(await statement.getByRole('heading', { name: 'Statement B', exact: true }).count(), 0);
  assert.equal(await statement.getByRole('heading', { name: 'Statement C', exact: true }).count(), 1);
  assert.equal(await code(), '// current C code must stay on C');
  await screenshot('stale-isolated');
  report('PASS: completing B after switching to C preserves C title, statement, and code.');

  for (const [id, error, reject] of [['F', 'Local fixture statement failed', false], ['E', 'Local fixture polling exception', true]]) {
    await page.evaluate(value => window.backgroundStatementFixture.changeProblem(value), id);
    await editable(id);
    await holdPoll(id);
    await editor.fill(`// preserve ${id} draft after statement failure`);
    await page.evaluate(({ id, error, reject }) => window.backgroundStatementFixture.release(id, { markdown: '', statementLoading: false, statementAvailable: false, statementError: error }, reject ? error : ''), { id, error, reject });
    await page.getByText('题面暂时未能加载', { exact: true }).waitFor();
    await page.getByText(error, { exact: true }).waitFor();
    assert.equal(await statement.getByRole('button', { name: '重新载入', exact: true }).isVisible(), true);
    assert.equal(await editor.getAttribute('aria-readonly'), 'false');
    await noSpinner();
    const callCount = await page.evaluate(value => window.backgroundStatementFixture.calls.filter(row => row.id === value).length, id);
    await page.waitForTimeout(1500);
    assert.equal(await page.evaluate(value => window.backgroundStatementFixture.calls.filter(row => row.id === value).length, id), callCount, 'a terminal statement failure stops automatic polling');
    await screenshot(`failure-${id.toLowerCase()}`);

    // A fresh edit immediately before Retry must survive, even before autosave.
    const retryDraft = reject ? '' : `// unsaved ${id} retry draft\nint main() { return 23; }`;
    await editor.fill(retryDraft);
    await page.evaluate(value => window.backgroundStatementFixture.ready(value), id);
    await statement.getByRole('button', { name: '重新载入', exact: true }).click();
    await statement.getByRole('heading', { name: `Statement ${id}`, exact: true }).waitFor();
    await editable(id);
    assert.equal(await code(), retryDraft, 'retry preserves both nonempty and deliberately empty unsaved code');
    assert.equal(await page.evaluate(value => window.backgroundStatementFixture.calls.filter(row => row.id === value).at(-1).refresh, id), '1', 'retry explicitly refreshes the statement');
    await noSpinner();
    report(`PASS: ${reject ? 'a rejected poll' : 'an explicit statement failure'} stops spinning/polling, offers Retry, and recovers while preserving ${retryDraft ? 'unsaved' : 'deliberately empty'} code.`);
  }
  await screenshot('retry-recovered');

  const localCode = '// old unuploaded local code\nint main() { return 41; }';
  const cloudCode = '// newer synchronized cloud code\nint main() { return 42; }';
  const modifiedAt = Date.now() - 120000;
  const localKey = await page.evaluate(({ localCode, cloudCode, modifiedAt }) => {
    const fixture = window.backgroundStatementFixture;
    fixture.cloudDraft('CLOUD', cloudCode, new Date(modifiedAt + 60000).toISOString());
    const key = fixture.localDraft('CLOUD', localCode, modifiedAt);
    fixture.changeProblem('CLOUD');
    return key;
  }, { localCode, cloudCode, modifiedAt });
  await editable('CLOUD');
  assert.equal(await code(), cloudCode, 'a newer cloud draft wins over an older dirty local draft');
  const recovery = page.getByRole('button', { name: '恢复本机草稿', exact: true });
  await recovery.waitFor();
  const retained = await page.evaluate(key => Object.entries(localStorage).filter(([name]) => name.startsWith(`${key}.recovery.`)).map(([key, value]) => ({ key, ...JSON.parse(value) })), localKey);
  assert.equal(retained.length, 1, 'the old local draft has an independent persistent recovery copy');
  assert.equal(retained[0].code, localCode);
  assert.equal(retained[0].modifiedAt, modifiedAt);
  await page.waitForTimeout(1000);
  assert.equal(await page.evaluate(() => window.backgroundStatementFixture.calls.filter(row => row.path === 'draft' && row.body?.id === 'CLOUD').length), 0, 'loading a stale dirty backup never automatically overwrites the newer cloud draft');
  assert.equal(await page.evaluate(() => window.backgroundStatementFixture.drafts['solo:CLOUD']), cloudCode);
  await screenshot('newer-cloud-retains-local');
  await recovery.click();
  assert.equal(await code(), localCode, 'the preserved local draft can be explicitly recovered');
  await page.getByRole('button', { name: '撤销载入代码', exact: true }).click();
  assert.equal(await code(), cloudCode, 'undoing local recovery restores the newer cloud code');
  report('PASS: newer timestamped cloud code wins without uploading stale local edits; local edits remain recoverable with undo.');

  await page.evaluate(() => {
    const fixture = window.backgroundStatementFixture;
    fixture.cloudDraft('EMPTY', '', new Date().toISOString());
    fixture.changeProblem('EMPTY');
  });
  await editable('EMPTY');
  assert.equal(await code(), '', 'a timestamped intentionally empty cloud draft stays empty instead of loading the C++ template');
  await screenshot('empty-cloud-draft');
  report('PASS: a saved empty cloud draft remains empty.');

  const calls = await page.evaluate(() => window.backgroundStatementFixture.calls);
  assert.ok(calls.filter(row => row.id).every(row => row.background === '1'), 'all problem reads request the background metadata contract');
  assert.ok(calls.every(row => row.id || row.path === 'draft'), 'the regression never opens or submits to any site');
  assert.deepEqual(externalRequests, [], 'the test uses only localhost resources');
  assert.deepEqual(errors, [], 'the fixture has no unhandled page errors');
  report('PASS: all problem reads use background=1; no external requests, official submissions, or page errors.');
} catch (error) {
  report(`FAIL: ${error.stack || error.message}`);
  if (page) await page.screenshot({ path: path.join(artifactDir, 'background-statement-failure.png'), animations: 'disabled' }).catch(() => undefined);
  throw error;
} finally {
  if (page) {
    const events = await page.evaluate(() => ({ calls: window.backgroundStatementFixture?.calls, answers: window.backgroundStatementFixture?.answers })).catch(() => ({}));
    await fs.writeFile(path.join(artifactDir, 'background-statement-events.json'), JSON.stringify({ ...events, errors, externalRequests }, null, 2));
  }
  if (context) await context.tracing.stop({ path: path.join(artifactDir, 'background-statement-trace.zip') });
  if (browser) await browser.close();
  await server.close();
  await fs.writeFile(path.join(artifactDir, 'background-statement.log'), `${log.join('\n')}\n`);
  console.log(`Artifacts: ${artifactDir}`);
}
