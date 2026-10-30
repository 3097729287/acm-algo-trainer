import assert from 'node:assert/strict';
import {chooseMockValue} from './mock-mode-selection.mjs';
import { spawn } from 'node:child_process';
import { mkdtemp, mkdir, rm, realpath, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { basename, join, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import { chromium } from 'playwright';
import {completeContest} from '../src/lib/completeContest.js';
import { catalogSegments } from '../src/lib/contestCatalog.js';
import {organizeCategories} from '../src/models/model.js';
import {canonicalKnowledgeName,knowledgeFilterNames,rowKnowledgeNames} from '../src/lib/knowledgeNames.js';

const root = resolve(fileURLToPath(new URL('../..', import.meta.url)));
const seededSolutions = JSON.parse(await readFile(join(root, 'data/library/solutions.json'), 'utf8'));
const state = await mkdtemp(join(tmpdir(), 'tb-api-e2e-'));
const service = spawn(process.env.TB_PYTHON || 'python', [join(root, 'frontend/tests/local-api-server.py')], {
  cwd: root, windowsHide: true,
  env: { ...process.env, TB_STATE_DIR: state, TB_OFFLINE: '1', DSH_HOME: join(state, 'absent'), PYTHONIOENCODING: 'utf-8' },
});
let stderr = '';
service.stderr.on('data', part => { stderr += part; });
let vite, browser, page;
const errors = [];
try {
  const apiUrl = await new Promise((done, fail) => {
    const timer = setTimeout(() => fail(new Error('API startup timed out: ' + stderr)), 30000);
    service.stdout.on('data', part => {
      const match = String(part).match(/http:\/\/127\.0\.0\.1:\d+/);
      if (match) { clearTimeout(timer); done(match[0]); }
    });
    service.on('exit', code => { clearTimeout(timer); fail(new Error('API exited ' + code + ': ' + stderr)); });
  });
  process.env.TB_API_URL = apiUrl;
  vite = await createServer({ server: { host: '127.0.0.1', port: 0 } });
  await vite.listen();
  const frontendUrl = `http://127.0.0.1:${vite.httpServer.address().port}`;
  browser = await chromium.launch({ channel: process.env.CI ? undefined : 'msedge', headless: true });
  page = await browser.newPage({ viewport: { width: 1480, height: 920 } });
  page.setDefaultTimeout(30000);
  await page.addInitScript(() => localStorage.setItem('tb.preferences', JSON.stringify({ theme: 'light', fontSize: 15, accent: 'teal' })));
  page.on('pageerror', error => errors.push(error.message));
  const catalog = await (await page.request.get(frontendUrl + '/api/data')).json();
  assert.ok(catalog.rows.length >= 607);
  const editorialIds=new Set(seededSolutions.map(row=>row.problem_id));
  const reachableEditorials=new Set(catalog.rows.filter(row=>row.solutionAvailable).flatMap(row=>row.aliasIds||[row.id]));
  assert([...editorialIds].every(id=>reachableEditorials.has(id)),'all bundled editorials remain reachable after original-task deduplication');
  assert(catalog.rows.filter(row=>row.solutionAvailable).every(row=>(row.aliasIds||[row.id]).some(id=>editorialIds.has(id))),'every displayed editorial has a real public source');
  const problem = catalog.rows.find(row => row.title === 'Xterfusion');
  const solution = await (await page.request.get(frontendUrl + '/api/solution?id=' + encodeURIComponent(problem.id))).json();
  assert.equal(solution.markdown, seededSolutions.find(record => record.problem_id === problem.id).markdown, 'the complete bundled solution reaches the API');
  assert(solution.lectures.length>=1,'The existing editorial keeps its linked foundation lessons');
  assert.equal(new Set(solution.lectures.map(item=>item.id)).size,solution.lectures.length);
  await page.goto(frontendUrl);
  await page.getByRole('heading', { name: '从第一道题开始', exact: true }).waitFor();
  await page.keyboard.press('Control+2');
  await page.getByRole('textbox', { name: '搜索题目', exact: true }).fill('Xterfusion');
  await page.locator('.problem-table .problem-title').first().click();
  await page.getByRole('textbox', { name: 'C++ 代码' }).waitFor();
  const code = '// SQL draft preservation\nint main(){return 0;}\n';
  const editor = page.getByRole('textbox', { name: 'C++ 代码' });
  await editor.fill(code);
  await editor.press('Control+s');
  await page.waitForFunction(() => document.querySelector('.wb-save-state')?.textContent.includes('已保存') || document.body.innerText.includes('草稿已保存'));
  // This write went through the separate frontend's proxy with a real session token.
  const current = await (await page.request.get(frontendUrl + '/api/problem?id=' + encodeURIComponent(problem.id))).json();
  assert.equal(current.draft, code);
  assert.equal(await page.locator('.wb-heading').getByRole('button', { name: '官方提交', exact: true }).count(), 0);
  assert.equal(await page.locator('.wb-run-actions').getByRole('button', { name: '官方提交', exact: true }).count(), 0);
  assert.equal(await page.locator('.wb-run-actions').getByRole('button', { name: '本地提交', exact: true }).count(), 0);
  assert.equal(await page.locator('.wb-run-actions').getByRole('button', { name: '提交', exact: true }).count(), 1);
  assert.equal(await page.locator('.wb-run-actions').getByRole('button', { name: '运行样例', exact: true }).count(), 1);
  await page.getByRole('button', { name: '题解', exact: true }).click();
  await page.locator('.reader-panel .markdown').first().waitFor();
  await page.locator('.reader-panel .lesson-reader-link > button:first-child').first().waitFor();
  const linkedLecture = solution.lectures[0];
  assert.ok((await page.locator('.reader-panel .lesson-reader-link > button:first-child').allTextContents())
    .some(title=>title.includes(linkedLecture.displayTitle || linkedLecture.concept || linkedLecture.title)));
  await editor.fill('#include <bits/stdc++.h>\nusing namespace std;\n\nint main() {\n    ios::sync_with_stdio(false);\n    cin.tie(nullptr);\n\n    return 0;\n}\n');
  await mkdir('tests/screenshots', { recursive: true });
  await page.screenshot({ path: 'tests/screenshots/workbench-real.png', animations: 'disabled' });
  for (const width of [2048, 1050]) {
    await page.setViewportSize({ width, height: width === 1050 ? 760 : 1152 });
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    await page.screenshot({ path: `tests/screenshots/workbench-real-${width}.png`, animations: 'disabled' });
  }
  await page.setViewportSize({ width: 1480, height: 920 });
  await page.keyboard.press('Escape');
  await page.keyboard.press('Escape');
  await page.locator('.nav-item').filter({hasText: '成长'}).click();
  assert.equal(await page.locator('.daily-task').count(), 0);
  await page.getByRole('button', {name: '每日任务', exact: true}).click();
  await page.getByRole('dialog').getByRole('heading', {name: '每日任务', exact: true}).first().waitFor();
  await page.getByRole('dialog').locator('.daily-task').first().waitFor();
  assert.equal(await page.locator('.daily-task').count(), 6);
  await page.keyboard.press('Escape');
  await page.waitForFunction(() => !document.querySelector('[role="dialog"]'));
  assert.equal(await page.locator('.progress-recommendations').count(),0);
  const heights = await page.evaluate(() => {
    const left=document.querySelector('.knowledge-radar').getBoundingClientRect();
    const right=document.querySelector('.growth-account-hero').getBoundingClientRect();
    return {left:left.height,right:right.height};
  });
  assert.ok(heights.left>250&&heights.right>200,JSON.stringify(heights));
  const taxonomyNames=['思维与策略','动态规划','基础技巧','数据结构','图论','数学与计数','字符串','搜索','计算几何','专题方法'];
  const knowledgeRows=catalog.rows.map(row=>({identity:row.url||row.id,names:rowKnowledgeNames(row)}));
  const leaves=node=>node.children?.length?node.children.flatMap(leaves):[canonicalKnowledgeName(node.name)];
  const domainCounts=organizeCategories(catalog.categories).map((domain,order)=>{
    const scope=new Set(knowledgeFilterNames(domain).map(canonicalKnowledgeName));
    const available=new Set(knowledgeRows.filter(row=>[...row.names].some(name=>scope.has(name))).map(row=>row.identity)).size;
    const hasTopics=leaves(domain).some(name=>knowledgeRows.some(row=>row.names.has(name)));
    return {name:domain.name,available,order,hasTopics};
  }).filter(domain=>domain.hasTopics);
  assert.deepEqual(domainCounts.map(domain=>domain.name).sort(),[...taxonomyNames].sort(),'all expected real-library domains remain represented');
  const expectedDomains=domainCounts.sort((a,b)=>b.available-a.available||a.order-b.order).map(domain=>domain.name);
  const visibleDomains=await page.locator('.knowledge-radar .radar-node').evaluateAll(nodes=>nodes.map(node=>node.getAttribute('aria-label').split('，')[0]));
  assert.equal(new Set(visibleDomains).size,visibleDomains.length,'a domain is not duplicated to fill radar slots');
  assert.deepEqual([...visibleDomains].sort(),[...taxonomyNames].sort(),'radar retains the complete organized domain set');
  assert.deepEqual(visibleDomains,expectedDomains,'radar sorts distinct available originals before rendering, with taxonomy order only for ties');
  await page.screenshot({path: 'tests/screenshots/growth-real.png', animations: 'disabled'});
  assert.equal(await page.locator('.knowledge-drawer-toggle').count(),0);
  assert.equal(await page.getByRole('tab', {name: '目标计划', exact: true}).count(),0);
  await page.locator('#growth-goals').scrollIntoViewIfNeeded();
  await page.getByRole('button', {name: '新建目标', exact: true}).click();
  const goalEditor = page.getByRole('dialog', {name: '新建目标', exact: true});
  await goalEditor.waitFor();
  const deadline = new Date(Date.now() + 2 * 86400000).toISOString().slice(0,10);
  await page.getByLabel('目标截止日期').fill(deadline);
  await page.getByRole('button', {name: '保存目标', exact: true}).click();
  await goalEditor.waitFor({state:'hidden'});
  assert.equal(await page.locator('.goal-card,.goal-daily-task,.goal-contest-grid').count(),0, 'Goals use compact controls and the shared daily task list.');
  assert.equal(await page.locator('#growth-goals .goal-form').count(),0);
  assert.equal(await page.locator('.goal-week-plan > div').count(),0);
  const savedGoals = (await (await page.request.get(frontendUrl + '/api/goals')).json()).goals;
  assert.equal(savedGoals[0].deadline,deadline);
  assert.ok(savedGoals[0].warnings.length, 'An unrealistic deadline retains its planning warning in the API.');
  const assigned = savedGoals[0].dailyTask.problems;
  const joined = (await (await page.request.get(frontendUrl + '/api/workspace')).json()).training;
  assert.ok(assigned.length && assigned.every(problem => joined.some(row => row.id === problem.id)), 'Daily recommendations join real training automatically.');
  await page.getByRole('button', {name: '每日任务', exact: true}).click();
  assert.equal(await page.locator('.daily-goal-row').count(),0);
  await page.keyboard.press('Escape');
  await page.keyboard.press('Control+1');
  await page.locator('.queue-heading').filter({hasText:'今日目标'}).waitFor();
  for(const problem of assigned)assert.equal(await page.locator('.problem-table tr[data-id]').evaluateAll((rows,id)=>rows.some(row=>row.dataset.id===id),problem.id),true);
  assert.equal(await page.locator('.workspace-area').getAttribute('data-page'), 'mine');
  assert.equal(await page.getByRole('tab', { name: '今日待办', exact: true }).count(), 0);
  await page.keyboard.press('Control+1');
  await page.getByLabel('清空我的训练').click();
  await page.getByRole('alertdialog',{name:'清空我的训练确认'}).getByRole('button', {name: '取消', exact: true}).click();
  const beforeClear = await (await page.request.get(frontendUrl + '/api/workspace')).json();
  const beforeClearDraft = (await (await page.request.get(frontendUrl + '/api/problem?id=' + encodeURIComponent(problem.id))).json()).draft;
  assert.ok(beforeClear.summary.total > 0);
  await page.getByLabel('清空我的训练').click();
  await page.getByRole('alertdialog',{name:'清空我的训练确认'}).getByRole('button', {name: /确认清空/}).click();
  await page.getByRole('alertdialog',{name:'清空我的训练确认'}).waitFor({state:'detached'});
  assert.equal((await (await page.request.get(frontendUrl + '/api/workspace')).json()).summary.total,0);
  assert.equal((await (await page.request.get(frontendUrl + '/api/problem?id=' + encodeURIComponent(problem.id))).json()).draft,beforeClearDraft);
  await page.keyboard.press('Control+4');
  await page.getByRole('button',{name:'筛选比赛',exact:true}).click();
  const menu=page.locator('.filter-popover');
  const contests=new Map();for(const row of catalog.rows.filter(row=>!row.catalogHidden)){const key=row.platform+'::'+row.contest;if(!contests.has(key))contests.set(key,[]);contests.get(key).push(row);}
  const full=[...contests.values()].filter(completeContest);
  const provincial=full.find(rows=>{
    const [family,kind,year]=catalogSegments(rows[0]);
    return family==='XCPC'&&kind==='省赛'&&/^20\d{2}年$/.test(year);
  });
  assert(provincial,'Use a currently complete public XCPC provincial contest');
  const [folder,stage,yearFolder]=catalogSegments(provincial[0]),year=yearFolder.replace('年','');
  assert.equal(await menu.getByRole('combobox',{name:'筛选比赛分类',exact:true}).count(),0);
  await page.getByLabel('比赛年份',{exact:true}).selectOption(year);
  await page.getByRole('button',{name:'关闭筛选',exact:true}).click();
  await page.getByRole('button',{name:'比赛文件夹浏览',exact:true}).click();
  await page.locator('.catalog-folder-row').filter({has:page.getByText(folder,{exact:true})}).click();
  await page.locator('.catalog-folder-row').filter({has:page.getByText(stage,{exact:true})}).click();
  await page.locator('.catalog-folder-row').filter({has:page.getByText(yearFolder,{exact:true})}).click();
  await page.locator('.competition-card').first().waitFor();
  assert.equal(await page.locator('.competition-card').filter({hasText:provincial[0].contest}).count(),1);
  for(const rows of [...contests.values()].filter(rows=>!completeContest(rows)&&catalogSegments(rows[0]).slice(0,3).join('/')===[folder,stage,yearFolder].join('/')))
    assert.equal(await page.locator('.competition-card').filter({hasText:rows[0].contest}).count(),0,'Incomplete events must not become playable cards');
  await page.screenshot({path: 'tests/screenshots/verified-provincial-history.png', animations: 'disabled'});
  await page.keyboard.press('Control+5');
  await page.getByRole('button', {name: '重现赛', exact: true}).click();
  assert.equal(await page.getByRole('textbox', {name: '搜索题目', exact: true}).count(),0,'replay has no irrelevant search box');
  const collected = catalog.rows.filter(row => row.contest === '入门赛 49');
  await page.getByRole('button',{name:'训练筛选',exact:true}).click();
  assert.equal(await page.getByLabel('模拟赛最低难度',{exact:true}).count(),0,'replay keeps every problem in the event regardless of difficulty');
  await page.keyboard.press('Escape');
  await chooseMockValue(page,'重现赛','入门赛 49');
  const previewResponse=page.waitForResponse(response=>response.url().endsWith('/api/contests/preview')&&response.request().method()==='POST');
  await page.getByRole('button', {name:'生成试卷',exact:true}).click();
  const replay = (await (await previewResponse).json()).plan;
  assert.equal(replay.slots.length,collected.length);
  assert.deepEqual(replay.slots.map(slot=>slot.id),collected.sort((a,b)=>a.problem.localeCompare(b.problem)).map(row=>row.id));
  await page.getByRole('button',{name:'训练筛选',exact:true}).click();
  assert.equal(await page.getByLabel('模拟赛赛制').count(),0,'replay uses the original published rules');
  assert.equal(await page.getByLabel('模拟赛时长').inputValue(),String(replay.duration),'replay retains the selected event duration');
  assert.equal(await page.getByLabel('编译错误计罚时').isChecked(),false);
  await page.keyboard.press('Escape');
  await page.setViewportSize({width:1050,height:700});
  await page.evaluate(()=>{document.documentElement.style.setProperty('--ui-font-size','18px');localStorage.setItem('tb.preferences',JSON.stringify({...JSON.parse(localStorage.getItem('tb.preferences')),fontSize:18}));});
  await page.reload();
  await page.locator('.sidebar nav .nav-item').first().waitFor();
  const nav = await page.locator('.sidebar nav').evaluate(node=>({scroll:node.scrollHeight,client:node.clientHeight,bottom:node.getBoundingClientRect().bottom,items:[...node.querySelectorAll('.nav-item')].map(item=>item.getBoundingClientRect().bottom)}));
  assert.ok(nav.scroll<=nav.client+1 && nav.items.every(bottom=>bottom<=700),JSON.stringify(nav));
  assert.equal(await page.locator('.sidebar .knowledge-search,.sidebar .sidebar-section-title,.sidebar .knowledge-tools').count(),0);
  await page.screenshot({path:'tests/screenshots/sidebar-small.png',animations:'disabled'});
  assert.deepEqual(errors, []);
  console.log('End-to-end passed: independent API, ' + seededSolutions.length + ' SQLite solutions, precise lecture, saved draft through Vite, submit placement and responsive workbench.');
} catch (error) {
  console.error('Browser errors:', errors, '\nAPI stderr:', stderr);
  if (page) {
    console.error('Page:', (await page.locator('body').innerText()).slice(0, 4000));
    await mkdir('tests/screenshots', { recursive: true });
    await page.screenshot({ path: 'tests/screenshots/e2e-failure.png' });
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
  assert.ok(actual.startsWith(temporaryRoot + sep) && basename(actual).startsWith('tb-api-e2e-'));
  await rm(actual, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 });
}
