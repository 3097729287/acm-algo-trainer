import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
import { chromium } from 'playwright';
import { CHAPTERS } from '../src/pages/algorithm-lab/knapsackCourse.js';
import { GUIDED_PROBLEMS } from '../src/pages/algorithm-lab/guidedProblems.js';

process.env.TB_OFFLINE = '1';
const repo = fileURLToPath(new URL('../../', import.meta.url));
const output = path.join(repo, '.backups/algorithm-lab-standalone-20261022/ui');
const installed = path.resolve(process.env.TB_LAB_INSTALLED || path.resolve(repo, '../../版本/算法实验室体验版'));
const archive = path.resolve(installed, '../算法实验室-独立体验版.zip');
const fresh = path.join(output, 'fresh-install');
await mkdir(fresh, { recursive: true });
execFileSync('powershell.exe', ['-NoProfile', '-Command', 'Expand-Archive -LiteralPath $env:TB_LAB_PACKAGE_ZIP -DestinationPath $env:TB_LAB_FRESH_DIR -Force'], {
  env: { ...process.env, TB_LAB_PACKAGE_ZIP: archive, TB_LAB_FRESH_DIR: fresh }, windowsHide: true, stdio: 'pipe',
});
const entry = path.join(fresh, '开始体验.html'), html = await readFile(entry, 'utf8');
const info = JSON.parse(await readFile(path.join(fresh, 'BUILD-INFO.json'), 'utf8'));
assert.equal(createHash('sha256').update(html).digest('hex'), info.files['开始体验.html']);
assert.equal(html, await readFile(path.join(installed, '开始体验.html'), 'utf8'));
assert.ok(!/<script[^>]+src=|<link[^>]+href=/.test(html), 'no external runtime assets');
assert.ok(!html.includes(repo), 'package has no absolute developer path');
assert.ok(!html.includes('algorithmLabFixture'), 'package has no fixture state');
const browser = await chromium.launch({ channel: process.env.CI ? undefined : 'msedge', headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 1060 }, offline: true });
const page = await context.newPage(), errors = [], requests = [];
page.setDefaultTimeout(10000);
context.on('request', request => { if (!request.url().startsWith('file:')) requests.push(request.url()); });
page.on('pageerror', error => errors.push(error.message));
page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
const key = 'tb.knapsack.standalone.v1';
const saved = () => page.evaluate(storageKey => JSON.parse(localStorage.getItem(storageKey) || '{}'), key);
const passed = async () => (await saved()).learningPaths?.knapsack?.labV1?.passed || {};
async function chapter(title) {
  const toggle = page.getByRole('button', { name: '目录', exact: true });
  if (await toggle.getAttribute('aria-expanded') !== 'true') await toggle.click();
  await page.getByRole('navigation', { name: '课程章节', exact: true }).getByRole('button').filter({ hasText: title }).click();
  assert.equal(await toggle.getAttribute('aria-expanded'), 'false');
}
async function choice(title, answer) {
  const form = page.getByRole('form', { name: title, exact: true });
  await form.getByRole('radio', { name: answer, exact: true }).check();
  await form.getByRole('button', { name: '检查判断', exact: true }).click();
  await form.locator('.lab-feedback-good').waitFor();
}
async function number(title, answer) {
  const form = page.getByRole('form', { name: title, exact: true });
  await form.getByRole('textbox').fill(answer);
  await form.getByRole('button', { name: '验证结果', exact: true }).click();
  await form.locator('.lab-feedback-good').waitFor();
}
async function shot(name, element) {
  if (element) await element.screenshot({ path: path.join(output, `${name}.png`) });
  else { await page.evaluate(() => scrollTo(0, 0)); await page.screenshot({ path: path.join(output, `${name}.png`) }); }
}
async function noOverflow() { assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false, `page overflow in ${(await saved()).learningPaths?.knapsack?.labV1?.chapter}`); }
const cell = (items, capacity) => page.getByRole('button', { name: new RegExp(`^可选${items}，容量 ${capacity} 格，`) });

try {
  await page.goto(pathToFileURL(entry).href);
  await page.getByRole('region', { name: '背包 DP', exact: true }).getByRole('button', { name: '学算法', exact: true }).click();
  await page.getByRole('heading', { name: /背包只有 5 格/ }).waitFor();
  assert.deepEqual(await passed(), {}, 'fresh package starts with no progress');
  assert.equal(await page.getByRole('navigation', { name: '课程章节' }).count(), 0, 'menu starts collapsed');
  assert.equal(await page.locator('.lab-lesson-footer').count(), 0, 'bottom navigation is removed');
  assert.equal(await page.getByRole('button', { name: '上一页', exact: true }).isDisabled(), true);
  await page.getByRole('button', { name: '下一页', exact: true }).click();
  await page.getByRole('heading', { name: /把大问题拆小/ }).waitFor();
  await page.locator('.lab-lesson').evaluate(node => { node.scrollTop = node.scrollHeight; });
  const nextPage = await page.getByRole('button', { name: '下一页', exact: true }).boundingBox();
  const lessonBox = await page.locator('.lab-lesson').boundingBox();
  assert.ok(nextPage.y >= 0 && nextPage.y + nextPage.height <= lessonBox.y + 1, 'top navigation remains visible above the independently scrolling lesson');
  await page.getByRole('button', { name: '上一页', exact: true }).click();
  assert.equal(await page.locator('progress,.lab-sidebar,.lab-check-label').count(), 0);
  assert.ok(!/从一次选择|课堂检验|本节|任务 001|装备 A/.test(await page.locator('body').innerText()));
  await shot('packing-fresh');
  await page.getByRole('button', { name: '目录', exact: true }).click();
  assert.equal(await page.getByRole('navigation', { name: '课程章节' }).getByRole('button').count(), 7);
  await shot('menu');
  await page.keyboard.press('Escape');
  assert.equal(await page.getByRole('button', { name: '目录', exact: true }).getAttribute('aria-expanded'), 'false');
  await page.getByRole('button', { name: /^A 对讲机/ }).click();
  await page.getByRole('button', { name: '检查我的方案', exact: true }).click();
  assert.equal((await passed()).pack, undefined);
  await page.getByRole('button', { name: /^B 照明灯/ }).click();
  await page.getByRole('button', { name: '检查我的方案', exact: true }).click();
  assert.match(await page.locator('.lab-feedback').innerText(), /超过 5 格/);
  assert.equal((await passed()).pack, undefined);
  await page.getByRole('button', { name: /^A 对讲机/ }).click();
  await page.getByRole('button', { name: /^C 急救包/ }).click();
  await page.getByRole('button', { name: '检查我的方案', exact: true }).click();
  assert.equal((await passed()).pack, true);
  assert.equal(await page.locator('.lab-bag-slots [data-item]').count(), 2, 'each whole item appears once');
  const greedy = page.getByRole('form', { name: '为什么不能一直挑性价比最高的？' });
  await greedy.getByRole('radio', { name: '因为性价比算错了', exact: true }).check();
  await greedy.getByRole('button', { name: '检查判断', exact: true }).click();
  assert.equal((await passed()).greedy, undefined);
  await choice('为什么不能一直挑性价比最高的？', '整件选择会占住容量，要比较组合');
  await shot('packing-solved');

  await chapter('读懂表格');
  assert.match(await page.locator('.lab-example').innerText(), /还是上一节的背包/);
  assert.match(await page.locator('.lab-example').innerText(), /容量 5 格 · 每件最多一次 · 不可拆分/);
  assert.equal(await page.locator('.lab-example>div>span').count(), 3);
  assert.match(await page.locator('.lab-scope-focus').innerText(), /只允许 A，容量上限 5 格/);
  assert.equal(await page.locator('[data-branch=skip] [data-item]').count(), 0, 'A may be skipped even when it is the only available item');
  assert.equal(await page.locator('[data-branch=take] [data-item=A]').count(), 1);
  assert.equal(await page.locator('.lab-cell-detail [data-item=A]').count(), 1);
  assert.equal(await page.locator('.lab-state-table .lab-dp-table').isVisible(), false, 'actual choices come before the abstract table');
  assert.equal(await page.locator('.lab-formula-content').isVisible(), true, 'the required derivation starts expanded');
  assert.match(await page.locator('.lab-base-cases').innerText(), /f\[0\]\[0\] = 0.*f\[0\]\[c\] = 0.*f\[1\]\[0\] = 0/s);
  assert.equal(await page.locator('.lab-initial-table [data-known=base]').count(), 9);
  assert.equal(await page.locator('.lab-initial-table [data-known=pending]').count(), 15);
  assert.deepEqual(await page.locator('.lab-initial-table [data-known=base]').allTextContents(), Array(9).fill('0'));
  for (let row = 1; row <= 3; row++) {
    await page.getByRole('button', { name: `计算第 ${row} 行`, exact: true }).click();
    assert.equal(await page.locator('.lab-initial-table [data-known=pending]').count(), (3 - row) * 5);
  }
  assert.match(await page.locator('.lab-initial-calculation').innerText(), /f\[3\]\[5\] = max\(f\[2\]\[5\], f\[2\]\[3\] \+ 3\) = max\(7, 5 \+ 3\) = 8/);
  await shot('initialization', page.locator('.lab-initialization'));
  await page.getByRole('button', { name: '重看起点', exact: true }).click();
  await shot('scope-a', page.getByRole('region', { name: '装包答案表', exact: true }));
  await page.getByRole('group', { name: '逐步增加可选物品', exact: true }).getByRole('button', { name: /^2\s*只允许 A、B$/ }).click();
  assert.equal(await page.locator('[data-branch=skip] [data-item=A]').count(), 1);
  assert.equal(await page.locator('[data-branch=take] [data-item=B]').count(), 1);
  assert.equal(await page.locator('[data-branch=take] [data-item=A]').count(), 0, 'adding B does not commit the previously optimal A');
  assert.match(await page.locator('[data-branch=take]').innerText(), /A 重 4 格，.*装不下/);
  assert.match(await page.locator('.lab-cell-detail').innerText(), /只拿 A/);
  await shot('scope-b', page.getByRole('region', { name: '装包答案表', exact: true }));
  assert.match(await page.locator('.lab-formula-content').innerText(), /当前问题：只允许 A、B，容量上限 5 格/);
  assert.match(await page.locator('.lab-symbol-meaning').innerText(), /i = 2.*A、B.*i 不表示已经拿了几件/s);
  assert.match(await page.locator('[data-formula-branch=take]').innerText(), /f\[1\]\[2\] \+ 5 = 0 \+ 5 = 5/);
  assert.match(await page.locator('.lab-complete-equation').innerText(), /^f\[2\]\[5\] = max\(f\[1\]\[5\], f\[1\]\[2\] \+ 5\)/);
  assert.match(await page.locator('.lab-formula-content').innerText(), /本行读取第 2 条输入：重量 3，价值 5/);
  await shot('formula-b', page.locator('.lab-formula-details'));
  await page.getByText('把这些答案记成表格', { exact: true }).click();
  assert.deepEqual(await page.locator('.lab-state-table .lab-dp-table tbody th').allTextContents(), ['没有可用物品', '只允许 A', '只允许 A、B', '只允许 A、B、C']);
  assert.equal(await page.locator('.lab-dp-table [data-source=skip]').count(), 1);
  assert.equal(await page.locator('.lab-dp-table [data-source=take]').count(), 1);
  assert.equal(await page.locator('.lab-dp-table [data-source=skip]').evaluate(node => getComputedStyle(node).borderTopStyle), 'solid');
  await cell('A、B', 3).click();
  assert.equal(await page.locator('.lab-cell-detail [data-item=A]').count(), 0);
  assert.equal(await page.locator('.lab-cell-detail [data-item=B]').count(), 1, 'A can be omitted while the allowed range is A and B');
  assert.match(await page.locator('.lab-cell-detail').innerText(), /这一次就没有拿 A/);
  assert.match(await page.locator('.lab-formula-content').innerText(), /当前问题：只允许 A、B，容量上限 3 格/);
  await cell('没有物品', 4).click();
  assert.match(await page.locator('.lab-cell-detail').innerText(), /什么都不拿，价值为 0/);
  assert.equal(await page.locator('.lab-packing-breakdown').count(), 0);
  assert.match(await page.locator('.lab-formula-content').innerText(), /f\[0\]\[4\] = 0/);
  await cell('A', 4).click();
  assert.match(await page.locator('[data-branch=take]').innerText(), /剩余 0 格/);
  assert.equal(await page.locator('.lab-dp-table [data-source=skip]').locator('strong').innerText(), '0');
  assert.equal(await page.locator('.lab-dp-table [data-source=take]').locator('strong').innerText(), '0');
  await cell('A', 2).click();
  assert.match(await page.locator('[data-branch=take]').innerText(), /装不下/);
  assert.equal(await page.locator('.lab-dp-table [data-source=take]').count(), 0);
  await cell('A', 0).click();
  assert.match(await page.locator('.lab-cell-detail').innerText(), /容量为 0/);
  await cell('A、B、C', 5).click();
  assert.match(await page.locator('.lab-formula-content').innerText(), /本行读取第 3 条输入：重量 2，价值 3/);
  assert.equal(await page.locator('[data-formula-branch=skip] b').innerText(), '① 如果不拿 C', 'formula follows the current example rather than jumping to B');
  assert.match(await page.locator('.lab-cell-detail').innerText(), /最大价值：\?/);
  assert.equal(await page.locator('.lab-cell-detail [data-item]').count(), 0, 'prediction does not reveal the winning plan');
  assert.match(await page.locator('[data-branch=skip]').innerText(), /价值 7/);
  assert.match(await page.locator('[data-branch=take]').innerText(), /价值 5 \+ 3/);
  assert.equal(await page.locator('[data-branch=take] [data-item=B]').count(), 1);
  assert.equal(await page.locator('[data-branch=take] [data-item=C]').count(), 1);
  await shot('table-choice', page.getByRole('region', { name: '装包答案表', exact: true }));
  const scopeCheck = page.getByRole('form', { name: '允许使用 A、B 时，A 必须先拿吗？', exact: true });
  await scopeCheck.getByRole('radio', { name: '必须先拿 A，再用剩余空间考虑 B', exact: true }).check();
  await scopeCheck.getByRole('button', { name: '检查判断', exact: true }).click();
  assert.equal((await passed()).state, undefined, 'the forced-A misconception does not pass');
  await choice('允许使用 A、B 时，A 必须先拿吗？', 'A 可以不拿；只拿 A、只拿 B、都不拿都可以比较');
  const transition = page.getByRole('form', { name: '补上「A、B、C / 5 格」', exact: true });
  await transition.getByRole('textbox').fill('7');
  await transition.getByRole('button', { name: '验证结果', exact: true }).click();
  assert.equal((await passed()).transition, undefined);
  await number('补上「A、B、C / 5 格」', '8');
  assert.equal(await page.locator('.lab-cell-detail [data-item=B]').count(), 1);
  assert.equal(await page.locator('.lab-cell-detail [data-item=C]').count(), 1);
  assert.match(await page.locator('.lab-cell-detail').innerText(), /最大价值：8/);
  assert.match(await page.locator('.lab-formula-content').innerText(), /i − 1 = 2.*c − w = 3/);
  assert.match(await page.locator('.lab-complete-equation').innerText(), /^f\[3\]\[5\] = max\(f\[2\]\[5\], f\[2\]\[3\] \+ 3\)\s*= max\(7, 5 \+ 3\) = 8/);
  await shot('formula', page.locator('.lab-formula-details'));

  await chapter('理解倒序');
  assert.equal(await page.locator('.lab-independent-plans [data-capacity="3"] [data-item=B]').count(), 1);
  assert.equal(await page.locator('.lab-independent-plans [data-capacity="5"] [data-item=A]').count(), 1);
  assert.match(await page.locator('.lab-row-reuse').innerText(), /用 B \+ C 替换 A/);
  await shot('two-rows', page.locator('.lab-row-reuse'));
  await page.getByRole('button', { name: '把两行合并到 dp 数组', exact: true }).click();
  assert.match(await page.locator('.lab-row-reuse').innerText(), /dp\[5\] = max\(dp\[5\], dp\[3\] \+ 3\)/);
  assert.match(await page.locator('.lab-row-reuse .lab-array-cell[data-focus=source]').innerText(), /dp\[3\].*5.*旧/s);
  await page.getByRole('button', { name: '继续算容量 4', exact: true }).click();
  assert.match(await page.locator('.lab-row-reuse .lab-array-cell[data-focus=source]').innerText(), /dp\[2\].*0.*旧/s);
  await shot('row-reuse', page.locator('.lab-row-reuse'));
  await page.getByRole('button', { name: '重看两行', exact: true }).click();
  await page.getByRole('button', { name: '课堂背包', exact: true }).click();
  await page.getByRole('slider', { name: '执行位置', exact: true }).fill('6');
  assert.match(await page.locator('.lab-trace-equation').innerText(), /dp\[5\] ← max\(dp\[5\], dp\[3\] \+ v\[3\]\)/);
  assert.match(await page.locator('[data-candidate=keep]').innerText(), /dp\[5\] = 7.*原方案：A/s);
  assert.match(await page.locator('[data-candidate=add]').innerText(), /dp\[3\] \+ v\[3\] = 5 \+ 3 = 8.*来源方案 B，加上 C/s);
  assert.match(await page.locator('.lab-trace-items [data-current=true] .lab-item-value').innerText(), /v\[3\] = 3.*参与本步比较/s);
  assert.equal(await page.locator('.lab-trace .lab-array-cell[data-capacity="5"] .lab-array-plan').innerText(), 'B + C');
  const valueColor = await page.locator('.lab-trace-equation .lab-term-value').evaluate(node => getComputedStyle(node).color);
  assert.equal(await page.locator('.lab-item-value[data-active=true]').evaluate(node => getComputedStyle(node).color), valueColor, 'value input and equation use the same visible mark');
  await shot('trace-class-comparison', page.locator('.lab-trace'));
  await page.getByRole('button', { name: '一件物品的反例', exact: true }).click();
  await page.getByRole('button', { name: '下一步', exact: true }).click();
  assert.match(await page.locator('.lab-trace-equation').innerText(), /dp\[4\] ← max\(dp\[4\], dp\[2\] \+ v\[1\]\)/);
  assert.equal(await page.locator('.lab-trace [data-focus=source]').evaluate(node => getComputedStyle(node).borderTopStyle), 'solid');
  await page.getByRole('button', { name: '重置推演', exact: true }).click();
  await page.getByRole('button', { name: '正序 · w → W', exact: true }).click();
  for (let n = 0; n < 3; n++) await page.getByRole('button', { name: '下一步', exact: true }).click();
  assert.match(await page.locator('.lab-trace-explanation').innerText(), /同一件被使用了两次/);
  assert.equal(await page.locator('.lab-array-cell').last().locator('strong').innerText(), '6');
  await shot('trace');
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
  await choice('每件物品只能选一次，容量应该怎样遍历？', '从大到小，让较小的来源容量还属于上一轮');
  await number('你能预言这个错误吗？', '6');
  await page.getByText('自己改一组数据，再看它运行', { exact: true }).click();
  await page.getByRole('spinbutton', { name: '自定义背包容量', exact: true }).fill('0');
  await page.getByRole('button', { name: '应用数据', exact: true }).click();
  assert.match(await page.locator('.lab-trace-explanation').innerText(), /没有合法的更新位置/);
  await page.getByRole('button', { name: '课堂背包', exact: true }).click();

  await chapter('写出 C++');
  for (const [label, value] of [['① 初始状态', 'zero'], ['② 容量循环', 'up'], ['③ 选这件时的来源', 'remaining'], ['④ 最终答案', 'capacity']]) await page.getByRole('combobox', { name: label, exact: true }).selectOption(value);
  await page.getByRole('button', { name: '用反例检验模板', exact: true }).click();
  assert.equal((await passed()).template, undefined);
  assert.ok(await page.locator('.lab-test-results [data-correct=false]').count() > 0);
  await page.getByRole('combobox', { name: '② 容量循环', exact: true }).selectOption('down');
  await page.getByRole('button', { name: '用反例检验模板', exact: true }).click();
  assert.equal((await passed()).template, true);
  assert.equal(await page.locator('.lab-test-results [data-correct=false]').count(), 0);
  await shot('cpp');
  await chapter('找出错误');
  for (const [title, answer] of [['01 / 一件变成了两件', '改成倒序，保留上一轮的来源状态'], ['02 / 不存在的方案也有价值？', '只有 dp[0]=0，其余不可达；先检查来源'], ['03 / 恰好能装下，却没选上', '改为 c >= w，c-w=0 也是合法来源']]) {
    const bug = page.getByRole('region', { name: title, exact: true });
    await bug.getByRole('radio', { name: answer, exact: true }).check();
    await bug.getByRole('button', { name: '应用修复并复测', exact: true }).click();
    await bug.locator('.lab-feedback-good').waitFor();
  }
  await chapter('辨认模型');
  for (const [title, answer] of [['周末任务安排', '0/1 背包：时间作容量'], ['换个目标，还能直接套吗？', '完全背包，正序取最小'], ['可以切开的补给', '按单位重量收益从高到低装'], ['模型对了，规模呢？', '先换枚举维度，考虑折半枚举']]) await choice(title, answer);
  await chapter('独立练习');
  await page.getByRole('form', { name: '01 / 自己完成一个新背包', exact: true }).getByRole('button', { name: '提示', exact: true }).click();
  assert.equal((await passed())['practice-basic'], undefined);
  await number('01 / 自己完成一个新背包', '12');
  await number('02 / 一句话改变了初始化', '不可达');
  await number('03 / 题面里没有背包', '2');
  assert.equal(Object.keys(await passed()).length, 17);
  await page.getByText('拓展题：神奇的背包 · 洛谷入门赛 50 F', { exact: true }).click();
  assert.equal(await page.getByRole('link', { name: '打开原题', exact: true }).getAttribute('href'), 'https://www.luogu.com.cn/problem/P17162');
  await page.reload();
  await page.getByRole('heading', { name: /换三道题/ }).waitFor();
  assert.equal(Object.keys(await passed()).length, 17);
  assert.equal(await page.getByRole('form', { name: '01 / 自己完成一个新背包', exact: true }).getByRole('textbox').inputValue(), '12');
  assert.equal(await page.locator('.lab-mission').first().locator('.lab-hints p').count(), 1);

  for (const width of [1440, 1024, 390]) {
    await page.setViewportSize({ width, height: width === 390 ? 844 : 1060 });
    for (const item of CHAPTERS) { await chapter(item.title); await noOverflow(); }
    await chapter('先装一次背包');
    await shot(`packing-${width}`);
    await chapter('读懂表格');
    await page.getByText('把这些答案记成表格', { exact: true }).click();
    if (width === 390) assert.deepEqual(await page.locator('.lab-table-scroll').evaluateAll(nodes => nodes.map(node => node.scrollWidth > node.clientWidth + 1)), [false, false], 'all six table capacities fit on mobile');
    await shot(`table-${width}`);
    await chapter('理解倒序');
    await page.getByRole('button', { name: '把两行合并到 dp 数组', exact: true }).click();
    await page.getByRole('button', { name: '课堂背包', exact: true }).click();
    await page.getByRole('slider', { name: '执行位置', exact: true }).fill('6');
    await noOverflow();
    assert.equal(await page.locator('.lab-trace .lab-array-scroll').evaluate(node => {
      const outer = node.getBoundingClientRect();
      return [...node.querySelectorAll('[data-focus=source],[data-focus=target]')].every(cell => {
        const bounds = cell.getBoundingClientRect();
        return bounds.left >= outer.left - 1 && bounds.right <= outer.right + 1;
      });
    }), true, 'the current source and result are visible together');
    await shot(`trace-${width}`, page.locator('.lab-trace'));
  }
  await chapter('读懂表格');
  await page.getByRole('button', { name: '切换浅色主题', exact: true }).click();
  assert.equal(await page.locator('html').getAttribute('data-theme'), 'light');
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await noOverflow();
  await shot('light-mobile');
  await page.reload();
  assert.equal(await page.locator('html').getAttribute('data-theme'), 'light');
  assert.equal((await saved()).standaloneTheme, 'light');
  await page.setViewportSize({ width: 1440, height: 1060 });
  await shot('light-table');

  // A previous preview's choices survive a same-browser upgrade. No personal DB is used.
  const upgradeContext = await browser.newContext({ offline: true });
  const legacy = { favorites: ['retained'], learningPaths: { knapsack: { idea: true, labV1: { chapter: 'state', passed: { pack: true, state: false, transition: true }, drafts: { packItems: ['A'], 'hint:packing': 1, transition: '6', traceConfig: { capacity: 4, items: [{ id: 'A', weight: 3, value: 5 }, { id: 'B', weight: 2, value: 3 }, { id: 'C', weight: 2, value: 3 }] } } } } } };
  await upgradeContext.addInitScript(value => { if (!localStorage.getItem('tb.knapsack.standalone.v1')) localStorage.setItem('tb.algorithm-lab.preview.v1', JSON.stringify(value)); }, legacy);
  const upgradePage = await upgradeContext.newPage();
  await upgradePage.goto(pathToFileURL(entry).href);
  await upgradePage.getByRole('heading', { name: /把大问题拆小/ }).waitFor();
  assert.equal(await upgradePage.getByRole('form', { name: '补上「A、B、C / 5 格」', exact: true }).getByRole('textbox').inputValue(), '', 'the old numeric answer does not count for the revised example');
  await upgradePage.getByRole('radio', { name: 'A 可以不拿；只拿 A、只拿 B、都不拿都可以比较', exact: true }).check();
  const restored = await upgradePage.evaluate(storageKey => JSON.parse(localStorage.getItem(storageKey)), key);
  assert.equal(restored.learningPaths.knapsack.labV1.passed.pack, true);
  assert.equal(restored.learningPaths.knapsack.labV1.passed.transition, undefined);
  assert.equal(restored.learningPaths.knapsack.labV1.drafts.traceConfig, undefined, 'old canned classroom data is retired');
  assert.equal(restored.learningPaths.knapsack.labV1.exampleRevision, 2);
  assert.equal(restored.learningPaths.knapsack.labV1.drafts.packItems[0], 'A');
  assert.deepEqual(restored.favorites, ['retained']);
  await upgradePage.reload();
  await upgradePage.getByRole('heading', { name: /把大问题拆小/ }).waitFor();
  await upgradeContext.close();

  const customContext = await browser.newContext({ offline: true });
  const customTrace = { capacity: 7, items: [{ id: 'Z', weight: 3, value: 9 }] };
  await customContext.addInitScript(value => {
    if (!localStorage.getItem('tb.knapsack.standalone.v1')) localStorage.setItem('tb.knapsack.standalone.v1', JSON.stringify({ learningPaths: { knapsack: { labV1: { chapter: 'trace', passed: { loop: true }, drafts: { traceConfig: value } } } } }));
  }, customTrace);
  const customPage = await customContext.newPage();
  await customPage.goto(pathToFileURL(entry).href);
  assert.match(await customPage.locator('.lab-trace-conditions').innerText(), /当前容量 7，物品共 1 件/);
  assert.match(await customPage.locator('.lab-trace-items').innerText(), /Z.*w\[1\] = 3.*v\[1\] = 9/s);
  await customContext.close();

  const blockedStorage = await browser.newContext({ offline: true });
  await blockedStorage.addInitScript(() => { Storage.prototype.setItem = () => { throw Error('Storage disabled for test'); }; });
  const limited = await blockedStorage.newPage();
  await limited.goto(pathToFileURL(entry).href);
  await limited.getByText('浏览器禁止保存，关闭页面后本次进度会丢失。', { exact: true }).waitFor();
  await limited.getByRole('region', { name: '背包 DP', exact: true }).getByRole('button', { name: '学算法', exact: true }).click();
  await limited.getByRole('button', { name: /^A 对讲机/ }).click();
  assert.match(await limited.locator('.lab-bag-top').innerText(), /4 \/ 5 格/);
  await blockedStorage.close();

  await chapter('独立练习');
  await page.getByRole('button', { name: '进入跟着做题', exact: true }).click();
  for (let index = 0; index < GUIDED_PROBLEMS.length; index++) {
    const p = GUIDED_PROBLEMS[index];
    await page.getByRole('heading', { name: p.title, exact: true }).waitFor();
    await page.locator('.lab-keyword').first().click();
    assert.ok((await page.locator('.lab-clue-reason').innerText()).length > 5);
    const modelCheck = page.getByRole('form', { name: '把这道题翻译成状态', exact: true });
    await modelCheck.getByRole('radio', { name: p.model[1], exact: true }).check();
    await modelCheck.getByRole('button', { name: '检查判断', exact: true }).click();
    assert.match(await modelCheck.locator('.lab-feedback').innerText(), new RegExp(p.modelErrors[0].slice(0, 5)));
    await choice('把这道题翻译成状态', p.model[0]);
    await page.getByRole('button', { name: '2 做小实验', exact: true }).click();
    for (const item of await page.locator('.lab-guided-items button').all()) await item.click();
    if (p.kind !== 'balance') assert.match(await page.locator('.lab-mini-result').innerText(), /超出限制/);
    await number(p.prediction, String(p.answer));
    await page.getByRole('button', { name: '对照一种最优方案', exact: true }).click();
    await shot(`guided-${p.pid}`);
    await page.getByRole('button', { name: '3 推到代码', exact: true }).click();
    const code = page.getByRole('textbox', { name: '关键转移代码', exact: true });
    await code.fill('dp[0] = 0;');
    await page.getByRole('button', { name: '核对这一行', exact: true }).click();
    assert.equal(await page.locator('.lab-guided-transition .lab-feedback-good').count(), 0);
    await code.fill(p.line);
    await page.getByRole('button', { name: '核对这一行', exact: true }).click();
    await page.locator('.lab-guided-transition .lab-feedback-good').waitFor();
    assert.equal(await page.locator('.lab-guided-plan').isVisible(), true);
    await page.getByRole('button', { name: '4 查错与迁移', exact: true }).click();
    await number('这段错误代码会算出多少？', String(p.bug.answer));
    await page.getByRole('textbox').last().fill('我先看资源、次数和真正的目标，再核对状态与来源。');
    await page.getByRole('button', { name: '5 自行实现', exact: true }).click();
    await page.getByRole('checkbox').first().check();
    const checkboxSize = await page.getByRole('checkbox').first().boundingBox();
    assert.ok(checkboxSize.width <= 20 && checkboxSize.height <= 20, 'implementation checklist uses compact native checkboxes');
    assert.equal(await page.getByRole('link', { name: '打开原题，自行实现', exact: true }).getAttribute('href'), `https://www.luogu.com.cn/problem/${p.pid}`);
    assert.equal(await page.locator('.lab-guided main pre').count(), 0, 'handoff leaves the complete program for the learner');
    if (index < 4) await page.getByRole('button', { name: '下一页', exact: true }).click();
  }
  assert.equal(await page.getByRole('button', { name: '下一页', exact: true }).isDisabled(), true);
  await page.reload();
  await page.getByRole('heading', { name: 'NASA 的食物计划', exact: true }).waitFor();
  assert.equal(await page.getByRole('checkbox').first().isChecked(), true);
  await page.getByRole('button', { name: '4 查错与迁移', exact: true }).click();
  assert.match(await page.getByRole('textbox').last().inputValue(), /我先看资源/);
  for (const width of [1440, 1024, 390]) {
    await page.setViewportSize({ width, height: 1060 });
    for (const name of ['1 找条件', '2 做小实验', '3 推到代码', '4 查错与迁移', '5 自行实现']) { await page.getByRole('button', { name, exact: true }).click(); await noOverflow(); }
    await shot(`guided-implementation-${width}`);
  }
  await page.getByRole('button', { name: '返回学算法', exact: true }).click();
  assert.deepEqual(requests, [], 'offline course makes no HTTP or API requests');
  assert.deepEqual(errors, []);
  const report = { status: 'passed', entry: 'extracted ZIP via file://', offline: true, freshInstall: true, previewUpgrade: true, revisedExampleMigration: true, customTraceRetained: true, unavailableStorage: true, scopeNotSelection: true, previousPackingNotCommitted: true, independentCapacityPlans: true, baseCasesAndRowOrder: true, defaultOpenCompleteEquation: true, twoRowsToOne: true, symbolicTraceAndValueInput: true, formulaFollowsCurrentExample: true, fixedPageNavigation: true, guidedProblems: 5, keywordExperimentsCodeAndCounterexamples: true, learnerImplementationHandoff: true, guidedDraftsPersist: true, checkpoints: 17, widths: [1440, 1024, 390], themes: ['dark', 'light'], reducedMotion: true, standaloneIsolatedFromApi: true, networkRequests: requests.length, errors };
  await writeFile(path.join(output, 'result.json'), JSON.stringify(report, null, 2));
  console.log('PASS:', report);
} catch (error) {
  await page.screenshot({ path: path.join(output, 'failure.png') }).catch(() => {});
  await writeFile(path.join(output, 'failure.json'), JSON.stringify({ error: String(error), errors, requests }, null, 2));
  throw error;
} finally { await browser.close(); }
