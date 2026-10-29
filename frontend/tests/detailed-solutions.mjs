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
    if(await page.getByRole('button',{name:'收起题解',exact:true}).count())await page.getByRole('button',{name:'收起题解',exact:true}).click();
    if(await page.getByRole('button',{name:'返回列表',exact:true}).count())await page.getByRole('button',{name:'返回列表',exact:true}).click();
    await page.getByRole('textbox', { name: '搜索题目', exact: true }).fill(title);
    const identity = title === 'Rank Subsequence' ? pid : editorialRows.find(row => row.title === title && row.solutionAvailable)?.id;
    assert.ok(identity, 'The test must open an exact problem with a bundled editorial');
    await page.locator(`tr[data-id=${JSON.stringify(identity)}]`).getByRole('button', { name: title, exact: true }).click();
    await page.getByRole('button',{name:'题解',exact:true}).click();
    await page.getByRole('button', { name: '切换为详细题解', exact: true }).waitFor();
  };
  await open('Rank Subsequence');
  const panel = page.getByRole('complementary', { name: '题解阅读' });
  const defaultButton = panel.getByRole('button', { name: '切换为默认题解', exact: true });
  const detailedButton = panel.getByRole('button', { name: '切换为详细题解', exact: true });
  assert.equal(await detailedButton.getAttribute('aria-pressed'), 'false');
  assert.equal(await panel.getByText('左秩、右秩到底是什么？', { exact: true }).count(), 0);
  await panel.locator('.reader-content .markdown').first().waitFor();
  const defaultText = await panel.locator('.reader-content').innerText();
  assert(defaultText.trim(),'the default editorial has finished loading before comparison');
  await detailedButton.focus();
  await page.keyboard.press('Enter');
  await panel.getByRole('heading', { name: '左秩、右秩到底是什么？', exact: true }).waitFor();
  assert.equal(await defaultButton.getAttribute('aria-pressed'), 'true');
  let tableCount = await panel.locator('table').count(), codeCount = await panel.locator('pre').count();
  assert.equal(await panel.locator('.solution-full').count(), 0, 'Detailed content must not be automatically summarized');
  await panel.getByRole('heading',{name:'把推导对应到代码',exact:true}).waitFor();
  assert.equal(await panel.locator('.markdown h3').count(), 5, 'Problem-specific reasoning and reference code remain outside the foundation disclosures');
  const foundations = panel.locator('.lesson-reader-link > button:first-child');
  assert.equal(await foundations.count(), 3, 'All three foundation lessons remain directly accessible');
  const foundationNames = await foundations.allTextContents();
  const detailedText = await panel.locator('.reader-content').innerText();
  for (const name of foundationNames) {
    await panel.locator('.lesson-reader-link > button:first-child').filter({hasText: name}).click();
    await panel.getByRole('button', { name: '返回上一级', exact: true }).waitFor();
    const lesson = panel.locator('[aria-label="从零讲正文"]');
    assert.ok((await lesson.innerText()).trim().length > 100, 'The full foundation article opens within the reader');
    tableCount += await lesson.locator('table').count();
    codeCount += await lesson.locator('pre').count();
    assert.ok(!(await lesson.innerText()).includes('reusable-foundations'));
    await page.keyboard.press('Backspace');
    await panel.locator('[aria-label="题解正文"]').waitFor();
    assert.equal(await panel.locator('.reader-content').innerText(), detailedText, 'Backspace returns to the same complete detailed article');
  }
  assert.ok(tableCount >= 4, 'Detailed examples and linked foundation tables remain available');
  assert.ok(codeCount >= 4, 'Original code and linked foundation examples remain available');
  assert.ok(!(await panel.innerText()).includes('reusable-foundations'), 'Authoring comments never appear as prose');
  await defaultButton.click();
  assert.equal(await panel.locator('.reader-content').innerText(), defaultText);
  await detailedButton.click();
  await panel.getByRole('button', { name: '收起题解', exact: true }).click();
  await open('Rank Subsequence');
  assert.equal(await detailedButton.getAttribute('aria-pressed'), 'false', 'Reopening starts from the original default');
  // Public content keeps growing. Make the missing-detail response explicit
  // without deleting an editorial from the real library or personal state.
  const missingId = editorialRows.find(row => row.title === 'String Construction' && row.solutionAvailable).id;
  await page.route('**/api/solution?*', async route => {
    if (new URL(route.request().url()).searchParams.get('id') !== missingId) return route.continue();
    const response = await route.fetch();
    const body = await response.json();
    await route.fulfill({response,json:{...body,detailedSolution:null,
      methods:body.methods?.map(method=>({...method,detailedSolution:null}))}});
  });
  await open('String Construction');
  await detailedButton.click();
  await panel.getByRole('status').filter({hasText: '详细题解待补充'}).waitFor();
  assert.ok((await panel.locator('.markdown').allTextContents()).every(text=>!text.trim()), 'Missing details must not repeat any default article text');
  await defaultButton.click();
  await panel.locator('.markdown').first().waitFor();
  await detailedButton.click();
  await open('Rank Subsequence');
  assert.equal(await detailedButton.getAttribute('aria-pressed'), 'false', 'A different problem starts from its default');
  await detailedButton.click();
  await mkdir(screenshots, { recursive: true });
  for (const [theme, width] of [['light', 1480], ['dark', 1050], ['light', 375]]) {
    await page.setViewportSize({ width, height: 920 });
    await page.evaluate(theme => { document.documentElement.dataset.theme = theme; }, theme);
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    assert.ok(await defaultButton.isVisible());
    await page.screenshot({ path: join(screenshots, `detailed-solutions-${theme}-${width}.png`), animations: 'disabled' });
  }
  await page.setViewportSize({ width: 1480, height: 920 });
  await panel.getByRole('button', { name: '题解全屏', exact: true }).click();
  await page.locator('.reader-full').waitFor();
  assert.equal(await defaultButton.getAttribute('aria-pressed'), 'true');
  await page.screenshot({ path: join(screenshots, 'detailed-solutions-full.png'), animations: 'disabled' });
  await panel.getByRole('button', { name: '退出题解全屏', exact: true }).click();
  await panel.getByRole('button', { name: '收起题解', exact: true }).click();
  await open('小月的回声');
  for (const variant of ['default','detailed']) {
    if (variant === 'detailed') await detailedButton.click();
    await panel.getByRole('heading',{name:variant==='default'?'三个条件为什么足够让答案加一':'先用一个真实区间写出要检查的等式',exact:true}).waitFor();
    assert.equal(await panel.locator('[aria-label="从零讲正文"]').count(),0,'Each variant starts at the editorial with foundation lessons linked');
    assert.equal(await panel.locator('.lesson-reader-link').count(),4,'All four supporting foundation lessons remain accessible');
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
        await figures.nth(index).locator('img').evaluate(img=>img.decode());
        await figures.nth(index).screenshot({path:join(screenshots,`echo-${variant}-${theme}-${width}-${index}.png`)});
      }
      assert.equal(await panel.locator('.katex-error,.reading-image-missing').count(),0);
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
    }
    const imageTrigger=panel.locator('.markdown .reading-image-open').first();
    await imageTrigger.click();
    const imageDialog=page.locator('.reading-image-dialog[open]');
    await imageDialog.waitFor({state:'visible'});
    await page.keyboard.press('Escape');
    await imageDialog.waitFor({state:'hidden'});
    assert.ok(await panel.isVisible(),'Escape closes the topmost native image dialog without closing its reader');
    assert.ok(await imageTrigger.evaluate(node=>document.activeElement===node),'Closing the image restores focus to its trigger');
    await panel.locator('.lesson-reader-link > button:first-child').filter({hasText:'前缀和'}).first().click();
    const foundation=panel.locator('[aria-label="从零讲正文"]');
    await foundation.waitFor();
    assert.ok((await foundation.innerText()).trim().length > 100);
    assert.ok(!(await foundation.innerText()).includes('reusable-foundations'));
    await panel.getByRole('button', {name:'返回题解',exact:true}).click();
    await panel.getByRole('heading',{name:variant==='default'?'三个条件为什么足够让答案加一':'先用一个真实区间写出要检查的等式',exact:true}).waitFor();
  }
  await page.setViewportSize({width:1480,height:920});
  await page.keyboard.press('Escape');
  await panel.waitFor({state:'hidden'});
  await open('Range Search Query');
  await panel.getByRole('heading',{name:'为什么检查一个起点就足够回答 Yes 或 No',exact:true}).waitFor();
  assert.equal(await panel.locator('.concise-solution').count(),0,'A low-rating default editorial does not hide its worked proof and diagram');
  assert.equal(await panel.locator('[aria-label="从零讲正文"]').count(),0);
  assert.ok(await panel.locator('.markdown img').count()>0,'Its diagram is part of the visible main article');

  // The real API protects the combined response, including the new detailed body.
  const catalog = await get('data');
  const events = (await get('contests/events')).events;
  const event = events.find(event => event.complete && catalog.rows.some(row => row.contest === event.name && row.solutionAvailable));
  assert.ok(event, 'Only a verified complete contest can start a replay');
  const protectedProblem = catalog.rows.find(row => row.contest === event.name && row.solutionAvailable);
  const protectedSolution = await get('solution?id=' + encodeURIComponent(protectedProblem.id));
  assert.ok(protectedSolution.markdown && protectedSolution.detailedSolution?.markdown, 'The protected response includes both editorial variants');
  const preview = await page.request.post(url + '/api/contests/preview', {
    headers: { 'X-TB-Token': catalog.token }, data: { mode: 'replay', contest: event.name, duration: 30 },
  });
  assert.equal(preview.status(), 200, await preview.text());
  const { plan } = await preview.json();
  const start = await page.request.post(url + '/api/contests/start', {
    headers: { 'X-TB-Token': catalog.token }, data: { ids: plan.slots.map(slot => slot.id), duration: plan.duration, previewId: plan.previewId },
  });
  assert.equal(start.status(), 200, await start.text());
  const locked = await page.request.get(url + '/api/solution?id=' + encodeURIComponent(protectedProblem.id));
  assert.equal(locked.status(), 403);
  const lockedBody = await locked.json();
  assert.deepEqual(Object.keys(lockedBody), ['error'], 'The locked response exposes neither editorial variant nor method metadata');
  assert.deepEqual(errors, []);
  console.log('Detailed solutions passed: exact SQLite bodies, icon switching, full linked foundations and return stack, hidden author markers, Echo diagrams/proof, keyboard, default reset, missing state, light/dark/narrow/fullscreen and contest lock.');
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
