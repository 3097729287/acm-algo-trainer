import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { createServer } from 'vite';
import { chromium } from 'playwright';
const vite = await createServer({ server: { host: '127.0.0.1', port: 18778, strictPort: true } });
await vite.listen();
const browser = await chromium.launch({ channel: process.env.CI ? undefined : 'msedge', headless: true });
const page = await browser.newPage({ viewport: { width: 1600, height: 1100 } });
const errors = [];
page.on('pageerror', e => errors.push(e.message));
try {
  await page.clock.install({ time: new Date('2026-10-15T04:00:00Z') });
  await page.goto('http://127.0.0.1:18778/tests/catalog-activity-fixture.html');
  await page.getByRole('button',{name:'筛选比赛',exact:true}).click();
  const filters=page.locator('.filter-popover');
  const classification=filters.getByRole('combobox',{name:'筛选比赛分类'}),folders=page.getByRole('listbox',{name:'筛选比赛分类'});
  await classification.press('Space');
  const rootNames=await folders.getByRole('option').allTextContents();
  for(const name of ['全部比赛','牛客','洛谷','Codeforces','AtCoder','ACM','蓝桥杯 B 组'])assert(rootNames.includes(name),name);
  await page.keyboard.press('Escape');
  const shelf=async name=>{
    if(!await filters.isVisible())await page.getByRole('button',{name:'筛选比赛',exact:true}).click();
    await classification.press('Space');
    while(await folders.getByRole('button',{name:'返回上一级',exact:true}).count())await folders.getByRole('button',{name:'返回上一级',exact:true}).click();
    const label={CF:'Codeforces',AC:'AtCoder'}[name]||name;
    await folders.getByRole('option',{name:label,exact:true}).click();
    if(label!=='全部比赛')await folders.getByRole('option',{name:`选择「${label}」`,exact:true}).click();
  };
  await shelf('牛客');assert.deepEqual(await page.locator('.competition-card-title strong').allTextContents(),['周赛 10','周赛 2']);
  await shelf('CF');assert.equal(await page.locator('.competition-card').count(),1,'ACM mirror is exclusive to ACM');
  await shelf('ACM');assert.equal(await page.locator('.competition-card').count(),1);
  assert.equal(await page.locator('.competition-difficulty').count(),0);
  assert.equal(await page.locator('.competition-problem-token').textContent(),'A');
  await shelf('蓝桥杯');assert.equal(await page.locator('.competition-card').count(),1);
  await shelf('全部比赛');assert.equal(await page.locator('.competition-card').count(),7);
  await page.keyboard.press('Escape');
  const activity = page.getByLabel('训练活动', { exact: true });
  assert.deepEqual(await activity.locator('thead th').allTextContents(), ['日期', 'AC']);
  assert.equal((await activity.innerText()).includes('次提交'), false);
  assert.equal((await activity.innerText()).includes('本地通过'), false);
  const today = '2026-10-15';
  for (const [index, amount] of [0, 1, 2, 4, 7].entries()) {
    const key = today.slice(0, 8) + String(index + 1).padStart(2, '0');
    const cell = activity.getByRole('gridcell', { name: `${key}，${amount} 题通过`, exact: true });
    assert.match(await cell.getAttribute('class'), new RegExp(`activity-level-${index}(?:\\s|$)`));
    await cell.click();
    assert.equal(await activity.locator('.activity-selected-count b').innerText(),String(amount));
  }
  await mkdir('tests/screenshots', { recursive: true });
  await page.screenshot({ path: 'tests/screenshots/catalog-activity-v17.png', fullPage: true });
  await page.setViewportSize({ width: 800, height: 900 });
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
  assert.deepEqual(errors, []);
  console.log('Catalog/activity passed: natural order, folder categories and parent selection, official passes only, five count styles.');
} finally { await browser.close(); await vite.close(); }
