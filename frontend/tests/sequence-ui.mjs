import assert from 'node:assert/strict';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { pathToFileURL, fileURLToPath } from 'node:url';
import path from 'node:path';
import { chromium } from 'playwright';
import { createServer } from 'vite';
import { SEQUENCE_COURSES } from '../src/pages/algorithm-lab/sequenceCode.js';
import { SEQUENCE_PROBLEMS } from '../src/pages/algorithm-lab/sequenceProblems.js';

process.env.TB_OFFLINE = '1';
const frontend = fileURLToPath(new URL('../', import.meta.url)), repo = path.resolve(frontend, '..');
const out = path.join(repo, '.backups/sequence-lab-20261023/ui'); await mkdir(out, { recursive: true });
const installed = path.resolve(repo, '../../版本/算法实验室体验版/开始体验.html');
const browser = await chromium.launch({ channel: process.env.CI ? undefined : 'msedge', headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 1050 }, offline: true });
const page = await context.newPage(), errors = [], requests = [];
page.on('pageerror', e => errors.push(e.message));
context.on('request', request => { if (!request.url().startsWith('file:')) requests.push(request.url()); });
page.setDefaultTimeout(10000);
const saved = () => page.evaluate(() => JSON.parse(localStorage.getItem('tb.knapsack.standalone.v1') || '{}'));
const back = async () => { const button = page.getByRole('button', { name: '返回算法实验室', exact: true }); if (await button.count()) await button.click(); };
const openCourse = async title => { await back(); await page.getByRole('region', { name: title, exact: true }).getByRole('button', { name: '学算法', exact: true }).click(); };
const chapter = async title => { await page.getByRole('button', { name: '目录', exact: true }).click(); await page.getByRole('navigation', { name: '课程章节' }).getByRole('button').filter({ hasText: title }).click(); };
const shot = async name => page.screenshot({ path: path.join(out, name+'.png'), fullPage: true });
const noOverflow = async () => assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), 'page must not overflow horizontally');

try {
  await page.goto(pathToFileURL(installed).href);
  await page.getByRole('heading', { name: '算法实验室', exact: true }).waitFor();
  assert.equal(await page.getByRole('button', { name: '学算法', exact: true }).count(), 3);
  await shot('catalog-dark');
  await openCourse('前缀和与差分');
  await page.getByRole('button', { name: '完成这份总账' }).click();
  assert.match(await page.getByRole('region', { name: '前缀和实验' }).innerText(), /14 − \(3\) = 11/);
  await page.getByLabel('区间左端 l', { exact: true }).selectOption('1');
  await page.getByLabel('区间右端 r', { exact: true }).selectOption('1');
  assert.match(await page.getByRole('region', { name: '前缀和实验' }).innerText(), /3 − \(0\) = 3/);
  await page.getByLabel('修改实验数组', { exact: true }).fill('2 -3 5'); await page.getByRole('button', { name: '应用数组', exact: true }).click();
  await page.getByRole('button', { name: '完成这份总账' }).click();
  await page.getByLabel('区间右端 r', { exact: true }).selectOption('3');
  assert.match(await page.getByRole('region', { name: '前缀和实验' }).innerText(), /4 − \(0\) = 4/);
  await page.getByLabel('修改实验数组', { exact: true }).fill('1 nope'); await page.getByRole('button', { name: '应用数组', exact: true }).click();
  await page.getByRole('alert').waitFor();
  assert.deepEqual((await saved()).learningPaths['prefix-difference'].labV1.drafts.sumArray, [2,-3,5]);
  await shot('prefix-negative');
  await chapter('累计与变化，互相还原'); await page.getByRole('checkbox').check();
  assert.match(await page.getByRole('status').innerText(), /每格都偏移/); await shot('inverse-lost-origin');
  await chapter('只在边界下指令');
  await page.getByLabel('开始 l', { exact: true }).selectOption('6'); await page.getByLabel('增量 k', { exact: true }).fill('3');
  await page.getByRole('button', { name: '记下这次区间加' }).click();
  await page.getByRole('slider', { name: '扫描到的位置' }).fill('7');
  const results = page.getByRole('list', { name: '最终值 a[i] + add（第 7 格不输出）' });
  assert.match(await results.innerText(), /12/); await page.getByRole('checkbox').check(); assert.ok(!(await results.innerText()).includes('12'));
  await shot('difference-singleton');
  await chapter('矩形里的加减法');
  await page.getByLabel('上边 x1', { exact: true }).selectOption('1'); await page.getByLabel('左边 y1', { exact: true }).selectOption('1');
  await page.getByRole('button', { name: '给矩形加 3', exact: true }).click(); await page.getByRole('img').waitFor(); await shot('plane-four-corners');
  await page.getByRole('button', { name: '查询矩形和', exact: true }).click();
  await page.getByRole('button', { name: '目录', exact: true }).click(); await page.keyboard.press('Escape');
  assert.equal(await page.getByRole('button', { name: '目录', exact: true }).getAttribute('aria-expanded'), 'false');
  assert.equal(await page.getByRole('heading', { name: '前缀和与差分', exact: true }).count(), 1);
  await back();
  await page.getByRole('textbox', { name: '搜索算法' }).fill('双指针'); assert.equal(await page.getByRole('button', { name: '学算法', exact: true }).count(), 1);
  await page.getByRole('textbox', { name: '搜索算法' }).fill('');
  await openCourse('双指针算法');
  await page.getByRole('button', { name: '让 L 右移' }).click(); assert.match(await page.locator('.lab-feedback').innerText(), /请指出/);
  await page.getByRole('button', { name: '让 R 左移' }).click(); assert.match(await page.locator('.lab-feedback').innerText(), /整列候选/);
  await page.getByRole('button', { name: '让 L 右移' }).click(); await shot('pair-elimination');
  await page.getByLabel('修改有序数组', { exact: true }).fill('-2 0 2 2'); await page.getByRole('button', { name: '应用数组', exact: true }).click();
  await page.getByLabel('目标 target').fill('0'); assert.match(await page.getByRole('status').first().innerText(), /找到/);
  await chapter('让窗口伸缩'); await page.getByRole('button', { name: '缩：移去最左格' }).click(); assert.match(await page.locator('.lab-feedback').innerText(), /还不够/);
  await page.getByRole('slider', { name: '推演步数' }).fill(await page.getByRole('slider', { name: '推演步数' }).getAttribute('max'));
  assert.match(await page.getByRole('region', { name: '滑动窗口实验' }).innerText(), /最终答案 2/); await shot('window-final');
  await chapter('窗口里还可以放什么'); await page.getByLabel('修改字符串', { exact: true }).fill('abba');
  await page.getByRole('slider', { name: '推演步数' }).fill('3'); assert.match(await page.getByRole('region', { name: '无重复字符窗口' }).innerText(), /b：2/);
  await page.getByRole('button', { name: '单步', exact: true }).click(); assert.match(await page.getByRole('region', { name: '无重复字符窗口' }).innerText(), /b：2/);
  await page.getByRole('button', { name: '单步', exact: true }).click(); assert.match(await page.getByRole('region', { name: '无重复字符窗口' }).innerText(), /b：1/);
  await chapter('一个读，一个写'); const compactSlider = page.getByRole('slider', { name: '推演步数' }); await compactSlider.fill(await compactSlider.getAttribute('max'));
  assert.match(await page.getByRole('region', { name: '快慢指针压缩' }).innerText(), /有效结果 \[3, 1, 4\]/); await shot('compact-final');
  await chapter('负数推翻了哪句话'); assert.match(await page.getByRole('region', { name: '负数反例' }).innerText(), /错误策略输出 3，穷举输出 1/); await shot('negative-counterexample');

  let pages = 0;
  for (const [theme, width] of [['dark',1440],['light',1440],['dark',390],['light',390]]) {
    await page.setViewportSize({ width, height: 960 });
    await page.evaluate(theme => document.documentElement.dataset.theme=theme, theme);
    for (const [id, course] of Object.entries(SEQUENCE_COURSES)) {
      await openCourse(course.title);
      for (const [chapterId, name] of course.chapters) {
        await chapter(name); await noOverflow(); await shot(`${id}-${chapterId}-${theme}-${width}`); pages++;
      }
      await page.getByRole('button', { name: '跟着做五道题' }).click();
      for (const problem of SEQUENCE_PROBLEMS[id]) {
        await page.getByRole('button', { name: '目录', exact: true }).click(); await page.getByRole('navigation', { name: '五道精选题' }).getByRole('button').filter({ hasText: problem.title }).click();
        await page.getByRole('button', { name: '2 亲手验证', exact: true }).click();
        const form = page.getByRole('form', { name: problem.question, exact: true }); await form.getByRole('textbox').fill(String(problem.answer)); await form.getByRole('button').click();
        await form.locator('.lab-feedback-good').waitFor();
        await page.getByRole('button', { name: '3 连接代码', exact: true }).click();
        await page.getByLabel('关键 C++ 语句', { exact: true }).fill(problem.line); await page.getByRole('button', { name: '对照教学写法' }).click();
        await page.locator('.lab-feedback-good').waitFor();
        await page.getByLabel('关键 C++ 语句', { exact: true }).fill('wrong'); assert.equal(await page.locator('.lab-feedback-good').count(), 0);
        await page.getByRole('button', { name: '4 查错与迁移', exact: true }).click();
        const bug = page.getByRole('form', { name: '错误程序会得到多少？', exact: true }); await bug.getByRole('textbox').fill(String(problem.bugAnswer)); await bug.getByRole('button').click(); await bug.locator('.lab-feedback-good').waitFor();
        await noOverflow(); await shot(`${problem.pid}-${theme}-${width}`); pages++;
      }
    }
  }
  await page.reload(); assert.equal((await saved()).learningPaths['two-pointers'].guided.problems['701C'].recall, undefined);
  assert.equal((await saved()).learningPaths['prefix-difference'].labV1.drafts.sumStep, 3);
  assert.equal((await saved()).learningPaths['two-pointers'].guided.problems['701C'].answers.bugAnswer, '2');
  assert.deepEqual(errors, []); assert.deepEqual(requests, []);

  // Main component with real row identity matching and a disposable onTrain sink.
  const server = await createServer({ root: frontend, server: { host:'127.0.0.1',port:0 }, logLevel:'error' }); await server.listen();
  try {
    const online = await browser.newContext({ viewport: { width:1440,height:1000 } }), main = await online.newPage();
    main.on('pageerror', e => errors.push(e.message));
    const address = server.httpServer.address(); await main.goto(`http://127.0.0.1:${address.port}/tests/sequence-fixture.html`);
    await main.waitForFunction(() => !!window.sequenceFixture);
    const first = SEQUENCE_PROBLEMS['prefix-difference'][0];
    await main.getByRole('region', { name:'前缀和与差分',exact:true }).getByRole('button',{name:'学算法',exact:true}).click();
    await main.evaluate(id => window.sequenceFixture.seed(p=>({...p,learningPaths:{...p.learningPaths,'prefix-difference':{mode:'guided',guided:{active:0}}}})),first.id);
    await main.getByRole('button',{name:'5 自行实现',exact:true}).click(); await main.getByRole('button',{name:'进入工作台实现'}).click();
    assert.deepEqual(await main.evaluate(()=>window.sequenceTraining),{id:'existing:363B',options:{assisted:false}});
    await main.getByRole('button',{name:'3 连接代码',exact:true}).click(); await main.getByRole('button',{name:'5 自行实现',exact:true}).click(); await main.getByRole('button',{name:'进入工作台实现'}).click();
    assert.deepEqual(await main.evaluate(()=>window.sequenceTraining),{id:'existing:363B',options:{assisted:true}});
    await main.evaluate(()=>window.sequenceFixture.lock([{id:'locked:alias',url:'https://codeforces.com/contest/363/problem/B'}]));
    await main.getByRole('heading',{name:'跟做指导已锁定'}).waitFor(); assert.equal(await main.getByRole('navigation',{name:'解题过程'}).count(),0);
    await main.getByRole('button',{name:'返回考场'}).click(); assert.equal((await main.evaluate(()=>window.sequenceTraining)).id,'locked:alias');
    await main.evaluate(()=>window.sequenceFixture.lock([])); await main.getByRole('button',{name:'5 自行实现',exact:true}).waitFor();
    await online.close();
  } finally { await server.close(); }
  assert.deepEqual(errors, []);
  const report = { status:'passed', model:'file:// offline course plus main component integration', screenshots:pages+9, pageVariants:pages, themes:['dark','light'], widths:[1440,390], officialSubmissions:0, errors, requests };
  await writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2)); console.log(JSON.stringify(report));
} finally { await browser.close(); }
