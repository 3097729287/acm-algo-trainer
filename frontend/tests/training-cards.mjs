import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const out='../.backups/local-1419/ui';fs.mkdirSync(out,{recursive:true});
const vite=await createServer({server:{host:'127.0.0.1',port:0,fs:{allow:[process.cwd(),fs.realpathSync('node_modules')]}}});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];page.on('pageerror',error=>errors.push(error.message));
const popup=()=>page.getByRole('alertdialog',{name:'删除题单确认'});
try {
  await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/training-cards-fixture.html`);
  const card=page.locator('.training-list-card');await card.waitFor();
  assert.equal(await card.locator('strong').innerText(),'搜索');assert.doesNotMatch(await card.innerText(),/洛谷|#112|算法1-7|周末|DFS/);
  assert.equal(await page.locator('.training-list-tags,.training-tag-browser').count(),0);
  assert.equal(await page.locator('.page-search-controls').innerText(),'');
  await card.click({button:'right'});assert.equal(await popup().count(),0);
  assert.equal(await card.locator('.like-burst,.training-card-actions').count(),0,'Public list cards have no hearts or empty action row');
  assert.equal(await page.evaluate(()=>trainingFixture.calls.filter(call=>call.path.startsWith('training-list-likes')).length),0,'Reading lists no longer requests unused like data');
  await card.getByRole('button',{name:'打开题单：搜索'}).click();await page.locator('.training-list-table').waitFor();
  assert.match(await page.locator('.training-list-table .tags-cell').first().innerText(),/DFS/);
  for(const status of ['AC','WA','TLE','MLE'])assert((await page.locator('.verdict').allTextContents()).includes(status));
  await page.evaluate(()=>{trainingFixture.delay=2000;trainingFixture.remount();});
  assert.equal(await page.getByText('正在读取题单…',{exact:true}).count(),0);await page.locator('.training-list-table').waitFor();
  for(const title of ['我的搜索练习','123']){
    await page.getByRole('button',{name:'全部题单',exact:true}).click();
    await page.getByRole('button',{name:'新建题单',exact:true}).click();
    const dialog=page.getByRole('dialog');await dialog.getByLabel('题单名称').fill(title);
    assert.equal(await dialog.locator('input').count(),1);assert.equal(await dialog.locator('.training-list-editor-columns').count(),0);
    assert((await dialog.boundingBox()).width<500);assert.equal(await dialog.locator('button').evaluateAll(nodes=>nodes.map(n=>n.textContent).join('')),'');
    await dialog.getByRole('button',{name:'保存',exact:true}).click();await dialog.waitFor({state:'detached'});
    const last=await page.evaluate(()=>trainingFixture.calls.filter(call=>call.path==='training-lists/save').at(-1));assert.deepEqual(last.body.problemIds,[]);
  }
  await page.getByRole('button',{name:'编辑题单',exact:true}).click();
  const editor=page.getByRole('dialog');await editor.getByRole('button',{name:'P1000 · 练习 1',exact:true}).click();await editor.getByRole('button',{name:'P1001 · 练习 2',exact:true}).click();
  await editor.getByRole('button',{name:'上移第 2 题'}).click();await editor.getByRole('button',{name:'保存',exact:true}).click();await editor.waitFor({state:'detached'});
  assert.deepEqual(await page.locator('.training-problem-row').evaluateAll(rows=>rows.map(row=>row.dataset.id)),['p1','p0']);
  await page.getByRole('button',{name:'返回上一级文件夹'}).click();await page.locator('.training-list-card').nth(1).waitFor();
  const path=await page.locator('.training-list-path').innerText();
  const own=page.locator('.training-list-card').filter({has:page.getByRole('button',{name:'打开题单：123',exact:true})});
  await own.click({button:'right'});await popup().waitFor();assert.equal(await popup().locator('button').evaluateAll(nodes=>nodes.map(n=>n.textContent).join('')),'');
  await page.keyboard.press('Escape');await popup().waitFor({state:'detached'});assert.equal(await page.locator('.training-list-path').innerText(),path);
  await own.click({button:'right'});await popup().getByRole('button',{name:'取消',exact:true}).click();assert.equal(await own.count(),1);
  for(const viewport of [{width:1440,height:900},{width:720,height:600},{width:390,height:700}]){
    await page.setViewportSize(viewport);await page.waitForTimeout(100);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    assert.equal(await page.locator('.training-list-path').evaluate(el=>getComputedStyle(el).scrollbarWidth),'none');
    const metrics=await page.locator('.training-list-card').evaluateAll(cards=>cards.map(card=>{const box=card.getBoundingClientRect(),title=card.querySelector('strong').getBoundingClientRect(),ring=card.querySelector('.training-card-progress').getBoundingClientRect(),action=card.querySelector('.training-card-actions')?.getBoundingClientRect();return {height:box.height,titleCenter:title.y+title.height/2-box.y,ringCenter:ring.y+ring.height/2-box.y,actionY:action? action.y-box.y:null};}));
    assert(metrics.every(item=>Math.abs(item.titleCenter-item.ringCenter)<1));
    assert(Math.abs(metrics[0].height-metrics[1].height)<1);assert(metrics.filter(item=>item.actionY!=null).every(item=>item.actionY>=0&&item.actionY<item.height));
    await page.screenshot({path:`${out}/cards-${viewport.width}.png`});
  }
  await page.evaluate(()=>{trainingFixture.failDelete=true;});await own.click({button:'right'});await popup().getByRole('button',{name:'确认删除'}).click();await popup().getByRole('alert').waitFor();assert.equal(await own.count(),1);
  await page.evaluate(()=>{trainingFixture.failDelete=false;});await popup().getByRole('button',{name:'确认删除'}).click();await own.waitFor({state:'detached'});
  await page.evaluate(()=>{trainingFixture.delay=0;trainingFixture.remount();});await page.locator('.training-list-card').waitFor();assert.equal(await page.getByRole('button',{name:'打开题单：123',exact:true}).count(),0);
  assert.deepEqual(errors,[]);console.log('PASS: icon-only controls, name-only creation, card alignment, cached navigation, editing, context delete/cancel/retry/persistence, public protection, no card hearts or like requests, and knowledge/verdicts.');
}catch(error){await page.screenshot({path:out+'/cards-failure.png'});throw error;}finally{await browser.close();await vite.close();}
