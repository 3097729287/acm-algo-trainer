import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import { chromium } from 'playwright';

process.env.TB_OFFLINE = '1';
const output = fileURLToPath(new URL('../../.backups/algorithm-lab-20261022/ui/', import.meta.url));
await mkdir(output, { recursive: true });
const vite = await createServer({ server: { host: '127.0.0.1', port: 0, hmr: false } });
await vite.listen();
const origin = `http://127.0.0.1:${vite.httpServer.address().port}`;
const browser = await chromium.launch({ channel: process.env.CI ? undefined : 'msedge', headless: true });
const errors = [], unexpected = [], requests = [], context = await browser.newContext({ viewport: { width: 1500, height: 1060 } });
const page = await context.newPage();
page.setDefaultTimeout(12000);
page.on('pageerror', error => errors.push(error.message));
await context.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : (unexpected.push(route.request().url()), route.abort()));
const chapter = title => ({async click(){if(!(await page.getByRole('navigation',{name:'课程章节',exact:true}).isVisible()))await page.locator('.lab-menu-toggle').click();await page.getByRole('navigation',{name:'课程章节',exact:true}).getByRole('button').filter({hasText:title}).click();}});
const passed = () => page.evaluate(() => window.algorithmLabFixture.prefs.learningPaths.knapsack.labV1?.passed || {});
async function checkChoice(title, answer) {
  const form = page.getByRole('form', { name: title, exact: true });
  await form.getByRole('radio', { name: answer, exact: true }).check();
  await form.getByRole('button', { name: '检查判断', exact: true }).click();
  await form.locator('.lab-feedback-good').waitFor();
}
async function checkNumber(title, value) {
  const form = page.getByRole('form', { name: title, exact: true });
  await form.getByRole('textbox').fill(value);
  await form.getByRole('button', { name: '验证结果', exact: true }).click();
  await form.locator('.lab-feedback-good').waitFor();
}
async function shot(name) { await page.screenshot({ path: `${output}/${name}.png`, fullPage: false }); }
async function noPageOverflow() { assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false, 'no document overflow'); const box = await page.locator('.learning-paths-page').evaluate(node => ({ width: innerWidth, scroll: node.scrollWidth, client: node.clientWidth, chapter: node.querySelector('.lab-sidebar [aria-current=step]')?.textContent, offenders: [...node.querySelectorAll('*')].filter(child => child.getBoundingClientRect().right > node.getBoundingClientRect().right + 2).slice(0, 10).map(child => ({ tag: child.tagName, class: child.className })) })); assert.ok(box.scroll <= box.client + 1, `no course-wide horizontal overflow: ${JSON.stringify(box)}`); }

try {
  await page.goto(`${origin}/tests/algorithm-lab-fixture.html`);
  await page.getByRole('heading', { name: '算法路线', exact: true }).waitFor();
  const difficulties = await page.locator('.learning-path-grid>button').evaluateAll(nodes => nodes.map(node => Number(node.dataset.difficulty)));
  assert.deepEqual(difficulties, [900, 1300, 1300, 1400, 1500, 1500, 1700, 1900]);
  assert.deepEqual(await passed(), {});
  await shot('catalog');
  await page.getByRole('button', { name: '从背包 DP 开始', exact: true }).click();
  await page.getByRole('heading', { name: /背包只有 4 格/ }).waitFor();
  assert.deepEqual(await passed(), {}, 'reading a page does not complete a checkpoint');
  await page.getByRole('button', { name: /装备 A/ }).click();
  await page.getByRole('button', { name: '检查我的方案', exact: true }).click();
  assert.equal((await passed()).pack, undefined, 'suboptimal legal pack does not pass');
  await page.getByRole('button', { name: /装备 B/ }).click();
  await page.getByRole('button', { name: '检查我的方案', exact: true }).click();
  assert.equal((await passed()).pack, undefined, 'overweight pack does not pass');
  await page.getByRole('button', { name: /装备 A/ }).click();
  await page.getByRole('button', { name: /装备 C/ }).click();
  await page.getByRole('button', { name: '检查我的方案', exact: true }).click();
  assert.equal((await passed()).pack, true);
  await checkChoice('为什么不能一直挑性价比最高的？', '整件选择会占住容量，要比较组合');
  await shot('packing');

  await chapter('一起发明状态').click();
  await page.getByRole('button', { name: '前 0 件，容量 4，价值 0', exact: true }).click();
  assert.match(await page.locator('.lab-panel .lab-feedback').innerText(), /没有物品/);
  await checkChoice('f[2][4] 这句话到底在问什么？', '只从 A、B 中选，总重量不超过 4 的最大价值');
  await page.getByRole('button', { name: '前 3 件，容量 4，待你推算', exact: true }).click();
  assert.equal(await page.locator('.lab-dp-table [data-source=skip]').count(), 1);
  assert.equal(await page.locator('.lab-dp-table [data-source=take]').count(), 1);
  await checkNumber('由你补上最后一个格子', '6');
  await page.getByRole('button', { name: '前 3 件，容量 4，价值 6', exact: true }).waitFor();
  await shot('state');

  await chapter('看清循环的时间').click();
  await page.getByRole('button', { name: '一件物品的反例', exact: true }).click();
  await page.getByRole('button', { name: '正序 · w → W', exact: true }).click();
  for (let i = 0; i < 3; i++) await page.getByRole('button', { name: '下一步', exact: true }).click();
  assert.match(await page.locator('.lab-trace-explanation').innerText(), /同一件被使用了两次/);
  assert.equal(await page.locator('.lab-array-cell').last().locator('strong').innerText(), '6');
  await shot('forward-counterexample');
  await page.getByRole('button', { name: '上一步', exact: true }).click();
  assert.equal(await page.locator('.lab-scrubber output').innerText(), '2');
  await page.getByRole('button', { name: '重置推演', exact: true }).click();
  assert.equal(await page.locator('.lab-scrubber output').innerText(), '0');
  await page.getByRole('button', { name: '倒序 · W → w', exact: true }).click();
  await page.getByRole('button', { name: '播放', exact: true }).click();
  await page.waitForFunction(() => Number(document.querySelector('.lab-scrubber output').textContent) >= 1);
  await page.getByRole('button', { name: '暂停', exact: true }).click();
  await page.getByRole('slider', { name: '执行位置', exact: true }).fill('3');
  assert.equal(await page.locator('.lab-array-cell').last().locator('strong').innerText(), '3');
  await checkChoice('每件物品只能选一次，容量应该怎样遍历？', '从大到小，让较小的来源容量还属于上一轮');
  await checkNumber('你能预言这个错误吗？', '6');
  await page.getByText('自己改一组数据，再看它运行', { exact: true }).click();
  await page.getByRole('spinbutton', { name: '自定义背包容量', exact: true }).fill('0');
  await page.getByRole('button', { name: '应用数据', exact: true }).click();
  assert.match(await page.locator('.lab-trace-explanation').innerText(), /没有合法的更新位置/);
  assert.equal(await page.locator('.lab-array-cell').count(), 1);
  await page.getByRole('button', { name: '课堂背包', exact: true }).click();

  await chapter('搭出 C++ 模板').click();
  for (const [label, value] of [['① 初始状态', 'zero'], ['② 容量循环', 'up'], ['③ 选这件时的来源', 'remaining'], ['④ 最终答案', 'capacity']]) await page.getByRole('combobox', { name: label, exact: true }).selectOption(value);
  await page.getByRole('button', { name: '用反例检验模板', exact: true }).click();
  assert.equal((await passed()).template, undefined);
  assert.ok(await page.locator('.lab-test-results [data-correct=false]').count() > 0);
  await page.getByRole('combobox', { name: '② 容量循环', exact: true }).selectOption('down');
  await page.getByRole('button', { name: '用反例检验模板', exact: true }).click();
  assert.equal((await passed()).template, true);
  assert.equal(await page.locator('.lab-test-results [data-correct=false]').count(), 0);
  await shot('template');

  await chapter('给错误找证据').click();
  for (const [title, answer] of [['01 / 一件变成了两件', '改成倒序，保留上一轮的来源状态'], ['02 / 不存在的方案也有价值？', '只有 dp[0]=0，其余不可达；先检查来源'], ['03 / 恰好能装下，却没选上', '改为 c >= w，c-w=0 也是合法来源']]) {
    const bug = page.getByRole('region', { name: title, exact: true });
    await bug.getByRole('radio', { name: answer, exact: true }).check();
    await bug.getByRole('button', { name: '应用修复并复测', exact: true }).click();
    await bug.locator('.lab-feedback-good').waitFor();
  }

  await chapter('在陌生题里认出来').click();
  for (const [title, answer] of [['周末任务安排', '0/1 背包：时间作容量'], ['换个目标，还能直接套吗？', '完全背包，正序取最小'], ['可以切开的补给', '按单位重量收益从高到低装'], ['模型对了，规模呢？', '先换枚举维度，考虑折半枚举']]) await checkChoice(title, answer);
  await shot('recognition');

  await chapter('把扶手慢慢放开').click();
  const mission = page.getByRole('form', { name: '01 / 自己完成一个新背包', exact: true });
  await mission.getByRole('button', { name: /给我一个提示/ }).click();
  assert.equal(await mission.locator('.lab-hints p').count(), 1);
  assert.equal((await passed())['practice-basic'], undefined);
  await checkNumber('01 / 自己完成一个新背包', '12');
  await checkNumber('02 / 一句话改变了初始化', '不可达');
  await checkNumber('03 / 题面里没有背包', '2');
  assert.equal(Object.keys(await passed()).length, 17);
  await page.getByRole('button', { name: '在 C++ 工作台中练习', exact: true }).click();
  assert.deepEqual(await page.evaluate(() => window.algorithmLabFixture.trained), ['入门赛 50::F']);
  await page.getByRole('button', { name: '收起', exact: true }).click();
  const before = await page.evaluate(() => window.algorithmLabFixture.prefs);
  assert.equal(before.learningPaths.knapsack.idea, true, 'legacy reading mark retained');
  assert.deepEqual(before.favorites, ['retained']);
  await page.reload();
  await page.getByRole('heading', { name: /先说清模型/ }).waitFor();
  assert.equal(Object.keys(await passed()).length, 17);
  assert.equal(await page.getByRole('form', { name: '01 / 自己完成一个新背包', exact: true }).getByRole('textbox').inputValue(), '12');
  assert.equal(await page.locator('.lab-mission').first().locator('.lab-hints p').count(), 1);
  await noPageOverflow();

  for (const size of [{ width: 1024, height: 768 }, { width: 390, height: 844 }]) {
    await page.setViewportSize(size);
    for (const title of ['先装一次背包', '一起发明状态', '看清循环的时间', '搭出 C++ 模板', '给错误找证据', '在陌生题里认出来', '把扶手慢慢放开']) { await chapter(title).click(); await noPageOverflow(); }
    await shot(`width-${size.width}`);
  }
  await page.getByRole('button', { name: '切换深浅主题', exact: true }).click();
  assert.equal(await page.locator('html').getAttribute('data-theme'), 'light');
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.evaluate(() => document.documentElement.dataset.motion = 'off');
  await chapter('先装一次背包').click();
  await noPageOverflow();
  await shot('light-mobile');
  await page.setViewportSize({ width: 1500, height: 1060 });
  await chapter('看清循环的时间').click();
  await shot('light-trace');

  // Exercise the actual App navigation, private-preferences upload/reload and
  // workbench round trip. API fixtures never touch a user's database or OJ.
  const app = await context.newPage();
  app.setDefaultTimeout(12000);
  app.on('console', message => { if (message.type() === 'error') console.log('App console:', message.text()); });
  app.on('pageerror', error => errors.push(error.message));
  const userId = '00000000-0000-4000-8000-000000000041', timestamp = new Date().toISOString();
  let remote = { onboardingCompleted: true, theme: 'dark', accent: 'teal', learningPaths: { knapsack: { idea: true }, 'prefix-sums': { idea: true } }, favorites: ['unrelated'] };
  const row = { id: '入门赛 50::F', title: '神奇的背包', difficulty: 1150, platform: '洛谷', tags: ['背包 DP'], url: 'https://www.luogu.com.cn/problem/P17162', solutionAvailable: true };
  const prefixRows = [{ ...row, id: 'fixture::2200', title: '包含 2200 的候选题', tags: ['前缀和'], difficulty: 2200 }, { ...row, id: 'fixture::2201', title: '超出题解范围', tags: ['前缀和'], difficulty: 2201 }];
  const workspace = { training: [], sets: [], contests: [], activeContest: null, goals: { goals: [] }, goalTasks: [], summary: { total: 0, accepted: 0, attempts: 0, todayAccepted: 0, due: 0, pending: 0, streak: 0 }, now: timestamp };
  await app.route('**/api/**', async route => {
    if (!new URL(route.request().url()).pathname.startsWith('/api/')) return route.continue();
    const request = route.request(), url = new URL(request.url()), body = request.method() === 'POST' ? request.postDataJSON() : null;
    const path = url.pathname;
    let value;
    if (path === '/api/account') value = { authenticated: true, required: false, usesOriginalWorkspace: true, token: 'lab-fixture', account: { userId, nickname: '课堂检验', loginId: 'lab-fixture' } };
    else if (path === '/api/preferences') { if (body) { assert.equal(request.headers()['x-tb-token'], 'lab-fixture'); remote = body.preferences; requests.push(path); } value = { preferences: remote, updatedAt: timestamp }; }
    else if (path === '/api/data') value = { rows: [row, ...prefixRows], categories: [], token: 'lab-fixture', today: timestamp.slice(0, 10) };
    else if (path === '/api/workspace') value = workspace;
    else if (path === '/api/training/start') { requests.push(path); value = { workspace }; }
    else if (path === '/api/problem') value = { ...row, markdown: '## 题目描述\n\n每种物品只有一件，或有无限件。无限种类至多选一种。', samples: [], limits: { timeMs: 2000, memoryMb: 256 }, judge: { scope: 'samples', cases: 0 }, statementAvailable: true, draft: '', submissions: [] };
    else if (path === '/api/draft') value = { savedAt: timestamp };
    else if (path === '/api/insights') value = { summary: {}, growth: { level: 1, currentLevelXp: 0, nextLevelXp: 100 }, achievements: [], knowledge: [], recommendations: [], activity: [], assessment: {}, dailyTasks: { tasks: [] } };
    else if (path === '/api/goals') value = { goals: [], contestPlan: { contests: [] } };
    else if (path === '/api/hub') value = null;
    else if (path === '/api/inbox') value = { pending: 0, errors: [] };
    else if (path === '/api/lectures') value = { lectures: [] };
    else if (path === '/api/social') value = { available: false, activity: [], notifications: [] };
    else if (path === '/api/software-update') value = { currentVersion: '1.3.3', status: 'current', autoCheck: false, canInstall: false };
    else if (path === '/api/browser-preparation') value = { available: false };
    else if (path === '/api/desktop/fullscreen') value = { available: false, fullscreen: false };
    else if (path === '/api/translation/settings') value = { provider: 'custom', model: 'fixture', configured: false, keyStored: false, providers: [] };
    else { unexpected.push(path); value = {}; }
    await route.fulfill({ json: value });
  });
  await app.goto(origin);
  const nav = app.getByRole('navigation', { name: '主导航', exact: true });
  await nav.getByRole('button', { name: '算法实验室', exact: true }).click();
  await app.getByRole('button', { name: /前缀和/ }).click();
  await app.getByRole('tab', { name: /精选练习/ }).click();
  await app.getByText('包含 2200 的候选题', { exact: true }).waitFor();
  assert.equal(await app.getByText('超出题解范围', { exact: true }).count(), 0);
  await app.getByRole('button', { name: '返回全部算法', exact: true }).click();
  await app.getByRole('button', { name: '从背包 DP 开始', exact: true }).click();
  const appChapters = app.getByRole('navigation', { name: '课程章节', exact: true });
  await appChapters.getByRole('button', { name: /在陌生题里认出来/ }).click();
  const appQuestion = app.getByRole('form', { name: '周末任务安排', exact: true });
  await appQuestion.getByRole('radio', { name: '0/1 背包：时间作容量', exact: true }).check();
  await appQuestion.getByRole('button', { name: '检查判断', exact: true }).click();
  await app.waitForFunction(() => Boolean(JSON.parse(localStorage.getItem('tb.preferences.v2.00000000-0000-4000-8000-000000000041') || '{}').learningPaths?.knapsack?.labV1?.passed?.['signal-time']));
  for (let i = 0; i < 50 && !remote.learningPaths?.knapsack?.labV1?.passed?.['signal-time']; i++) await new Promise(resolve => setTimeout(resolve, 100));
  assert.equal(remote.learningPaths.knapsack.labV1.passed['signal-time'], true);
  assert.equal(remote.learningPaths.knapsack.idea, true);
  assert.equal(remote.learningPaths['prefix-sums'].idea, true);
  assert.deepEqual(remote.favorites, ['unrelated']);
  await app.reload();
  await nav.getByRole('button', { name: '算法实验室', exact: true }).click();
  await app.getByRole('heading', { name: /看到新题/ }).waitFor();
  await appChapters.getByRole('button', { name: /把扶手慢慢放开/ }).click();
  await app.getByRole('button', { name: '在 C++ 工作台中练习', exact: true }).click();
  await app.locator('.tb-workbench').waitFor();
  assert.equal(requests.filter(path => path === '/api/training/start').length, 1);
  await app.keyboard.press('Escape');
  await app.getByRole('heading', { name: /先说清模型/ }).waitFor();
  await app.screenshot({ path: `${output}/app-workbench-return.png` });
  await app.close();

  assert.deepEqual(errors, []);
  assert.deepEqual(unexpected, []);
  const report = { status: 'passed', checkpoints: 17, widths: [1500, 1024, 390], themes: ['dark', 'light'], reducedMotion: true, preferenceWrites: requests.filter(path => path === '/api/preferences').length, workbenchRoundTrip: true, boundary2200Included: true, officialSubmissions: 0, errors };
  await writeFile(`${output}/result.json`, JSON.stringify(report, null, 2));
  console.log('PASS:', report);
} catch (error) {
  await page.screenshot({ path: `${output}/failure.png`, fullPage: false }).catch(() => {});
  await writeFile(`${output}/failure.json`, JSON.stringify({ error: String(error), errors, unexpected }, null, 2));
  throw error;
} finally {
  await browser.close();
  await vite.close();
}
