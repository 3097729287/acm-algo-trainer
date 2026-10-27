import assert from 'node:assert/strict';import fs from 'node:fs';import {createServer} from 'vite';import {chromium} from 'playwright';
const out='../.backups/local-1420/ui';fs.mkdirSync(out,{recursive:true});
const vite=await createServer({server:{host:'127.0.0.1',port:0,fs:{allow:[process.cwd(),fs.realpathSync('node_modules')]}}});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];
page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(10000);
await page.addInitScript(()=>localStorage.setItem('tb:list-likes:v2:revision1420',JSON.stringify({available:true,likes:{'luogu-112':{total:7,likedToday:false}}})));
try{
 await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/revision-1420.html`);
 await page.getByRole('button',{name:'新建题单',exact:true}).waitFor();
 await page.locator('.catalog-folder-row').filter({has:page.locator('strong',{hasText:'我的收藏题单'})}).click();
 await page.locator('.training-problem-row').waitFor();assert.deepEqual(await page.locator('.training-problem-row').evaluateAll(rows=>rows.map(row=>row.dataset.id)),['p1']);
 assert.equal(await page.locator('.training-list-mode').count(),0);assert.equal(await page.getByRole('button',{name:'新建题单',exact:true}).count(),0);
 await page.getByRole('button',{name:'全部题单',exact:true}).click();await page.locator('.catalog-folder-row').filter({has:page.locator('strong',{hasText:'基础',exact:true})}).click();
 const heart=page.locator('.like-burst');await heart.waitFor();assert.equal(await heart.locator('.like-burst-count').textContent(),'7');
 await heart.click();await page.waitForFunction(()=>document.querySelector('.like-burst-count')?.textContent==='8');assert.equal(await heart.isDisabled(),false);
 await heart.click();await page.waitForFunction(()=>document.querySelector('.like-burst-count')?.textContent==='7');
 await page.evaluate(()=>fixture.add(['p0','p3']));let dialog=page.getByRole('dialog',{name:'加入题单'});await dialog.waitFor();
 await dialog.getByRole('button',{name:'新建题单',exact:true}).click();await dialog.getByLabel('新题单名称').fill('直接新建');await dialog.getByRole('button',{name:'保存新题单'}).click();
 await dialog.getByRole('checkbox').waitFor();assert.equal(await dialog.getByRole('checkbox').isChecked(),true);await dialog.getByRole('button',{name:'添加',exact:true}).click();await dialog.waitFor({state:'detached'});
 await page.getByRole('button',{name:'全部题单',exact:true}).click();await page.locator('.catalog-folder-row').filter({has:page.locator('strong',{hasText:'我的题单',exact:true})}).click();await page.getByRole('button',{name:'打开题单：直接新建',exact:true}).click();
 const ids=()=>page.locator('.training-problem-row').evaluateAll(rows=>rows.map(row=>row.dataset.id));assert.deepEqual(await ids(),['p0','p3']);
 await page.getByRole('button',{name:'切换添加时间排序方向'}).click();assert.deepEqual(await ids(),['p3','p0']);
 await page.getByRole('button',{name:'筛选题单题目',exact:true}).click();await page.getByRole('combobox',{name:'题单知识点筛选'}).click();await page.getByRole('listbox',{name:'题单知识点筛选'}).getByRole('option',{name:'分治',exact:true}).click();await page.getByRole('button',{name:'关闭筛选',exact:true}).click();assert.deepEqual(await ids(),['p3']);
 await page.screenshot({path:out+'/list-filter.png'});
 await page.evaluate(()=>fixture.screen('mock'));await page.getByRole('button',{name:'生成试卷',exact:true}).click();await page.locator('.paper-slot').nth(12).waitFor();
 const boxes=await page.locator('.paper-slot').evaluateAll(nodes=>nodes.map(n=>{const r=n.getBoundingClientRect();return {x:r.x,y:r.y,height:r.height};}));assert(boxes.every(r=>Math.abs(r.height-56)<1));assert(boxes.every(r=>r.x===boxes[0].x));assert(await page.locator('.paper-slots').evaluate(n=>n.scrollHeight>n.clientHeight));
 await page.locator('.paper-slots').hover();await page.mouse.wheel(0,600);await page.waitForTimeout(100);assert(await page.locator('.paper-slots').evaluate(n=>n.scrollTop>0));await page.screenshot({path:out+'/mock-rows.png'});
 await page.evaluate(()=>fixture.screen('activity'));await page.getByRole('gridcell').first().waitFor();assert.deepEqual(await page.locator('.activity-month-marker').allTextContents(),['+14','+9','+6','+3']);
 assert.equal(await page.locator('.activity-day[data-shade="5"]').count(),5);
 for(const color of ['#9b8afb','#65a4e5','#64c6b0','#d4aa65']){await page.evaluate(value=>document.documentElement.style.setProperty('--accent',value),color);assert.equal(await page.locator('.activity-progress-segment').first().evaluate(n=>getComputedStyle(n).getPropertyValue('--activity-color').trim()),color);}
 assert.equal(await page.locator('.activity-selected-summary [role="meter"]').getAttribute('aria-valuemax'),'10');
 await page.screenshot({path:out+'/calendar.png'});assert.deepEqual(errors,[]);console.log('PASS revision 1.4.20: cached toggle likes, favorites, create-and-add, ordering/filtering, equal scroll rows and accent calendar.');
}finally{await browser.close();await vite.close();}
