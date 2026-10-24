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
  const editorialRows = (await get('data')).rows;
  const details = JSON.parse(await readFile(join(root, 'data/library/detailed_solutions.json'), 'utf8'));
  assert.equal(solution.markdown, defaults.find(row => row.problem_id === pid).markdown);
  assert.equal(solution.detailedSolution.markdown, details.find(row => row.problem_id === pid).markdown);

  await page.goto(url);
  await page.getByRole('heading', { name: '从第一道题开始', exact: true }).waitFor();
  await page.keyboard.press('Control+2');
  const open = async title => {
    await page.getByRole('textbox', { name: '搜索题目', exact: true }).fill(title);
    const identity = title === 'Rank Subsequence' ? pid : editorialRows.find(row => row.title === title && row.solutionAvailable)?.id;
    assert.ok(identity, 'The test must open an exact problem with a bundled editorial');
    await page.locator(`tr[data-id=${JSON.stringify(identity)}]`).getByRole('button', { name: '题解 ' + title, exact: true }).click();
    await page.getByRole('group', { name: '题解版本' }).waitFor();
  };
  await open('Rank Subsequence');
  const panel = page.getByRole('complementary', { name: '题解阅读' });
  const defaultButton = panel.getByRole('button', { name: '默认题解', exact: true });
  const detailedButton = panel.getByRole('button', { name: '详细题解', exact: true });
  assert.equal(await defaultButton.getAttribute('aria-pressed'), 'true');
  assert.equal(await panel.getByText('左秩、右秩到底是什么？', { exact: true }).count(), 0);
  await panel.locator('.reader-content .markdown').first().waitFor();
  const defaultText = await panel.locator('.reader-content').innerText();
  assert(defaultText.trim(),'the default editorial has finished loading before comparison');
  await detailedButton.focus();
  await page.keyboard.press('Enter');
  await panel.getByRole('heading', { name: '左秩、右秩到底是什么？', exact: true }).waitFor();
  assert.equal(await detailedButton.getAttribute('aria-pressed'), 'true');
  assert((await panel.locator('table').count())>=4,'The detailed worked-example tables remain available');
  assert((await panel.locator('pre').count())>=4,'Original code and added foundation examples remain available');
  assert.equal(await panel.locator('.solution-full').count(), 0, 'Detailed content must not be automatically summarized');
  await panel.getByRole('heading',{name:'把推导对应到代码',exact:true}).waitFor();
  assert.equal(await panel.locator('.markdown h3').count(), 5, 'Problem-specific reasoning and reference code remain outside the foundation disclosures');
  assert.equal(await panel.locator('.lecture-disclosure').count(), 3);
  assert.equal(await panel.locator('.lecture-disclosure[open]').count(), 0, 'Detailed foundations start collapsed');
  assert.ok(!(await panel.innerText()).includes('reusable-foundations'), 'Authoring comments never appear as prose');
  await defaultButton.click();
  assert.equal(await panel.locator('.reader-content').innerText(), defaultText);
  await detailedButton.click();
  await panel.getByRole('button', { name: '收起题解', exact: true }).click();
  await open('Rank Subsequence');
  assert.equal(await defaultButton.getAttribute('aria-pressed'), 'true', 'Reopening starts from the original default');
  // Public content keeps growing. Make the missing-detail response explicit
  // without deleting an editorial from the real library or personal state.
  const missingId = editorialRows.find(row => row.title === 'String Construction' && row.solutionAvailable).id;
  await page.route('**/api/solution?*', async route => {
    if (new URL(route.request().url()).searchParams.get('id') !== missingId) return route.continue();
    const response = await route.fetch();
    const body = await response.json();
    await route.fulfill({response,json:{...body,detailedSolution:null}});
  });
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
  await panel.getByRole('button', { name: '退出题解全屏', exact: true }).click();
  await panel.getByRole('button', { name: '收起题解', exact: true }).click();
  await open('小月的回声');
  for (const variant of ['default','detailed']) {
    await (variant==='default'?defaultButton:detailedButton).click();
    await panel.getByRole('heading',{name:variant==='default'?'三个条件为什么足够让答案加一':'先用一个真实区间写出要检查的等式',exact:true}).waitFor();
    assert.equal(await panel.locator('.lecture-disclosure[open]').count(),0,'Each variant starts with closed foundation lessons');
    assert.ok(!(await panel.innerText()).includes('reusable-foundations'));
    assert.ok((await panel.innerText()).includes('重复确认'),'The redundant length check is explained honestly');
    assert.ok((await panel.innerText()).includes('a[l] == v'),'The guessed value is checked against the actual array');
    const expected=(variant==='default'?defaults:details).find(row=>row.problem_id==='remote:nowcoder:141877::D').markdown.match(/^```cpp\s*\n([\s\S]*?)^```/m)[1];
    assert.equal((await panel.locator('.markdown pre code').last().textContent()).trimEnd(),expected.trimEnd(),'The original reference program remains visible and exact');
    for (const [theme,width] of [['light',1480],['dark',1050],['light',390]]) {
      await page.setViewportSize({width,height:920});
      await page.evaluate(theme=>{document.documentElement.dataset.theme=theme;},theme);
      const figures=panel.locator('.markdown .reading-image-open');
      assert.equal(await figures.count(),variant==='default'?1:3,'Problem diagrams stay outside closed lessons');
      for (let index=0;index<await figures.count();index++) {
        await figures.nth(index).scrollIntoViewIfNeeded();
        await figures.nth(index).locator('img').evaluate(img=>img.decode());
        await figures.nth(index).screenshot({path:join(screenshots,`echo-${variant}-${theme}-${width}-${index}.png`)});
      }
      assert.equal(await panel.locator('.katex-error,.reading-image-missing').count(),0);
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
    }
    const foundation=panel.locator('.lecture-disclosure').filter({hasText:'前缀和'}).first();
    await foundation.locator('summary').click();
    await foundation.locator('.lecture-disclosure-body').waitFor();
    assert.ok(!(await foundation.innerText()).includes('reusable-foundations'));
    await foundation.locator('summary').click();
  }
  await page.setViewportSize({width:1480,height:920});
  await panel.getByRole('button',{name:'收起题解',exact:true}).click();
  await open('Range Search Query');
  await panel.getByRole('heading',{name:'为什么检查一个起点就足够回答 Yes 或 No',exact:true}).waitFor();
  assert.equal(await panel.locator('.concise-solution').count(),0,'A low-rating default editorial does not hide its worked proof and diagram');
  assert.equal(await panel.locator('.lecture-disclosure[open]').count(),0);
  assert.ok(await panel.locator('.markdown img').count()>0,'Its diagram is part of the visible main article');

  // The real API protects the combined response, including the new detailed body.
  const catalog = await get('data');
  const contest = catalog.rows.find(row => row.id === pid)?.contest;
  assert.ok(contest, 'Use the current display name while preserving the original problem identity');
  const preview = await page.request.post(url + '/api/contests/preview', {
    headers: { 'X-TB-Token': catalog.token }, data: { mode: 'replay', contest, duration: 30 },
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
  console.log('Detailed solutions passed: exact SQLite bodies, switching, collapsed foundations in both variants, hidden author markers, Echo diagrams/proof, keyboard, default reset, missing state, light/dark/narrow/fullscreen and contest lock.');
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
