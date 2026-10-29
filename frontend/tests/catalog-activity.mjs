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
  await page.getByRole('button',{name:'比赛文件夹浏览',exact:true}).click();
  const folders=page.getByRole('region',{name:'比赛层级浏览'});
  await folders.getByText('牛客',{exact:true}).waitFor();
  const rootNames=await folders.locator('.catalog-folder-row strong').allTextContents();
  for(const name of ['牛客','洛谷','Codeforces','AtCoder','XCPC','蓝桥杯 B 组'])assert(rootNames.includes(name),name+': '+JSON.stringify(rootNames));
  const shelf=async name=>{
    if(name==='全部比赛'){await page.getByRole('button',{name:'比赛文件夹浏览',exact:true}).click();return;}
    await page.getByRole('button',{name:'全部平台',exact:true}).click();
    const root={CF:'Codeforces',ACM:'XCPC',蓝桥杯:'蓝桥杯 B 组'}[name]||name;
    await folders.locator('.catalog-folder-row').filter({has:page.getByText(root,{exact:true})}).click();
    for(let depth=0;await page.locator('.competition-card').count()===0;depth++){
      assert(depth<6,'nonempty shelf must lead to actual contests');
      const label=await folders.locator('.catalog-folder-row').evaluateAll(nodes=>nodes.find(node=>Number(node.querySelector('span')?.textContent)>0)?.querySelector('strong')?.textContent);
      assert(label,'expected a nonempty child folder');
      await folders.locator('.catalog-folder-row').filter({has:page.getByText(label,{exact:true})}).click();
    }
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
  for (const [index, amount] of [0, 2, 4, 6, 8, 10].entries()) {
    const key = today.slice(0, 8) + String(index + 1).padStart(2, '0');
    const cell = activity.getByRole('gridcell', { name: `${key}，${amount} 题通过`, exact: true });
    assert.equal(await cell.getAttribute('data-band'),index===0?'0':'1');
    assert.equal(await cell.getAttribute('data-shade'),String(index));
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
