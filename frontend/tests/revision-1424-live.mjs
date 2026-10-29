import assert from 'node:assert/strict';
import fs from 'node:fs';
import {chromium} from 'playwright';
const port=JSON.parse(fs.readFileSync('../.backups/local-1424/ui-port.json','utf8')).port;
const endpoint=process.env.TB_TEST_URL||`http://127.0.0.1:${port}`,output='../.backups/local-1424/ui';
fs.mkdirSync(output,{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});
const context=await browser.newContext({viewport:{width:1440,height:900},permissions:['clipboard-read','clipboard-write']});
const page=await context.newPage(),errors=[];
page.on('pageerror',e=>errors.push(e.message));
try {
 await page.goto(endpoint);await page.getByRole('navigation',{name:'主导航'}).waitFor();
 await page.getByRole('button',{name:'模板',exact:true}).click();
 const cards=page.locator('.template-catalog .catalog-card');await cards.first().waitFor();
 assert.equal(await cards.count(),24);
 assert.equal(await cards.getByRole('button',{name:/复制/}).count(),0);
 await page.evaluate(()=>navigator.clipboard.writeText('before-confirm'));
 await cards.first().click({button:'right'});
 await page.getByRole('alertdialog',{name:'复制模板确认'}).waitFor();
 assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),'before-confirm');
 assert.equal(await page.locator('.template-detail').count(),0);
 await page.keyboard.press('Escape');assert.equal(await page.locator('[data-popconfirm]').count(),0);
 await cards.first().click({button:'right'});await page.getByRole('button',{name:'取消复制',exact:true}).click();
 assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),'before-confirm');
 await cards.first().click({button:'right'});await page.getByRole('button',{name:'确认复制',exact:true}).click();
 await page.locator('[data-popconfirm]').waitFor({state:'detached'});
 const copied=await page.evaluate(()=>navigator.clipboard.readText());assert(copied.includes('struct'));assert(!copied.includes('//'));
 // Clipboard denial leaves the confirmation open and retryable.
 await page.evaluate(()=>{window.savedWrite=navigator.clipboard.writeText.bind(navigator.clipboard);navigator.clipboard.writeText=async()=>{throw Error('fixture denied');};});
 await cards.first().click({button:'right'});await page.getByRole('button',{name:'确认复制',exact:true}).click();
 await page.getByRole('alertdialog').getByRole('alert').waitFor();
 await page.evaluate(()=>{navigator.clipboard.writeText=window.savedWrite;});
 await page.getByRole('button',{name:'确认复制',exact:true}).click();await page.locator('[data-popconfirm]').waitFor({state:'detached'});
 const cardTitles=await cards.locator('h3').allTextContents();
 for(const viewport of [{width:1920,height:1080},{width:1366,height:768},{width:1024,height:720}]){
  await page.setViewportSize(viewport);
  for(const title of cardTitles){
   await page.getByRole('button',{name:`打开模板 ${title}`,exact:true}).click();
   await page.locator('.template-example').waitFor();
   for(const edition of ['讲解版','竞赛版']){
    if(await page.locator('.template-edition-toggle').innerText()!==edition)await page.locator('.template-edition-toggle').click();
    await page.waitForTimeout(35);
    const box=await page.evaluate(()=>{
     const detail=document.querySelector('.template-detail'),root=document.querySelector('.templates-page'),example=document.querySelector('.template-example'),pre=example.querySelector('pre'),code=document.querySelector('.template-code'),header=document.querySelector('.template-heading');
     const rect=n=>{const r=n.getBoundingClientRect();return {top:r.top,bottom:r.bottom,left:r.left,right:r.right,height:r.height};};
     return {root:[root.clientHeight,root.scrollHeight],detail:[detail.clientHeight,detail.scrollHeight],example:rect(example),pre:[pre.clientHeight,pre.scrollHeight],code:rect(code),header:rect(header),nav:rect(header.querySelector('.template-editions')),height:innerHeight,page:document.documentElement.scrollHeight};
    });
    assert(box.root[1]<=box.root[0]+2,`${title} ${edition} root scroll ${JSON.stringify(box)}`);
    assert(box.detail[1]<=box.detail[0]+2,`${title} detail scroll`);
    assert(box.example.bottom<=box.height+1&&box.example.top>box.code.bottom-1,`${title} example outside`);
    assert(box.pre[1]<=box.pre[0]+1,`${title} example clipped`);
    assert(box.code.height>150,`${title} main code too small`);
    assert(box.nav.top>=box.header.top&&box.nav.bottom<=box.header.bottom+1,`${title} header wrap`);
   }
   await page.getByRole('button',{name:'返回模板',exact:true}).click();
  }
 }
 await page.setViewportSize({width:1440,height:900});
 const geometry=async()=>page.locator('.catalog-card').evaluateAll(nodes=>nodes.map(n=>{const r=n.getBoundingClientRect(),h=n.querySelector('h3').getBoundingClientRect(),i=n.querySelector('h3 svg').getBoundingClientRect();return {left:r.left,top:r.top,width:r.width,height:r.height,indent:h.left-r.left,offset:h.top-r.top,iconTop:i.top-h.top};}));
 const templateGeometry=await geometry();
 for(const item of templateGeometry){assert(Math.abs(item.indent-templateGeometry[0].indent)<1);assert(Math.abs(item.offset-templateGeometry[0].offset)<1);assert(Math.abs(item.height-templateGeometry[0].height)<1);}
 await page.screenshot({path:output+'/template-catalog.png'});
 await cards.first().click();
 for(const theme of ['dark','light']){await page.evaluate(v=>document.documentElement.dataset.theme=v,theme);await page.screenshot({path:`${output}/template-${theme}.png`});}
 await page.evaluate(()=>document.documentElement.dataset.theme='dark');
 const before=await page.locator('.template-example').boundingBox();await page.locator('.template-code .cm-scroller').hover();await page.mouse.wheel(0,1200);await page.waitForTimeout(100);
 const after=await page.locator('.template-example').boundingBox();assert.deepEqual(after,before);
 assert(await page.locator('.template-code .cm-scroller').evaluate(n=>n.scrollTop>0));
 await page.getByRole('button',{name:'返回模板',exact:true}).click();
 await page.getByRole('button',{name:'实验室',exact:true}).click();await page.getByRole('button',{name:'打开算法 并查集',exact:true}).waitFor();
 const labGeometry=await geometry();for(const item of labGeometry){assert(Math.abs(item.indent-templateGeometry[0].indent)<1);assert(Math.abs(item.offset-templateGeometry[0].offset)<1);assert(Math.abs(item.height-templateGeometry[0].height)<1);}
 await page.screenshot({path:output+'/lab-catalog.png'});
 await page.getByRole('button',{name:'活动记录',exact:true}).click();await page.locator('.activity-continuous-grid').waitFor();
 const grid=page.getByRole('grid',{name:/全年连续训练日历/}),cell=grid.locator('[role=gridcell]');
 const all=await cell.evaluateAll(nodes=>nodes.map(n=>({day:n.dataset.date,row:Number(n.getAttribute('aria-rowindex')),col:Number(n.getAttribute('aria-colindex'))})));
 const middle=all.find(n=>n.row===2&&n.col===3);let current=middle;
 await grid.locator(`[data-date="${middle.day}"]`).focus();
 for(const [key,dr,dc] of [['ArrowDown',1,0],['ArrowUp',-1,0],['ArrowRight',0,1],['ArrowLeft',0,-1]]){
  const next=all.find(n=>n.row===current.row+dr&&n.col===current.col+dc);assert(next);
  await page.keyboard.press(key);await page.waitForTimeout(60);
  assert.equal(await page.evaluate(()=>document.activeElement.dataset.date),next.day,key);current=next;
 }
 const maxRow=Math.max(...all.map(n=>n.row)),maxCol=Math.max(...all.map(n=>n.col));
 for(const [key,edge] of [['ArrowUp',all.find(n=>n.row===1&&n.col===3)],['ArrowDown',all.find(n=>n.row===maxRow&&n.col===3)],['ArrowLeft',all.find(n=>n.col===1&&n.row===2)],['ArrowRight',all.find(n=>n.col===maxCol)]]){
  await grid.locator(`[data-date="${edge.day}"]`).focus();await page.keyboard.press(key);await page.waitForTimeout(60);assert.equal(await page.evaluate(()=>document.activeElement.dataset.date),edge.day,`edge ${key}`);
 }
 const summary=await page.locator('.activity-selected-summary').evaluate(n=>{const r=n.getBoundingClientRect(),bar=n.querySelector('.activity-progress').getBoundingClientRect(),s=getComputedStyle(n);return {width:r.width,bar:bar.width,height:bar.height,left:parseFloat(s.borderLeftWidth),background:s.backgroundColor};});
 assert(summary.bar>summary.width*.7);assert(summary.height>=10);assert(summary.left>=4);assert.notEqual(summary.background,'rgba(0, 0, 0, 0)');
 await page.screenshot({path:output+'/activity.png'});
 await page.getByRole('button',{name:'提交记录',exact:true}).click();await page.locator('.submission-log-row').first().waitFor();
 const aligned=await page.locator('.submission-log-row').evaluateAll(nodes=>nodes.filter(n=>!n.inert).map(n=>{const r=n.getBoundingClientRect(),a=n.querySelector('.submission-record-actions').getBoundingClientRect(),v=n.querySelector('.verdict').getBoundingClientRect(),c=n.querySelector('.submission-code-button').getBoundingClientRect();return {gap:r.right-a.right,verdict:v.right,code:c.left};}));
 assert(aligned.length>=4);for(const row of aligned){assert(row.gap<=18&&row.gap>=10);assert(Math.abs(row.verdict-aligned[0].verdict)<1);assert(Math.abs(row.code-aligned[0].code)<1);}
 await page.screenshot({path:output+'/submissions.png'});
 await page.getByRole('button',{name:'题单',exact:true}).click();await page.getByText('我的收藏',{exact:true}).waitFor();assert.equal(await page.getByText('我的收藏题单',{exact:true}).count(),0);
 assert.deepEqual(errors,[]);
 fs.writeFileSync(output+'/result.json',JSON.stringify({passed:true,templates:24,editions:2,viewports:3,scope:'public lists, fixed layout, confirmed context copy, grid keyboard, card and history alignment'},null,2));
 console.log('PASS 1.4.24 real App: 144 template/edition/viewport layouts; right-click confirmation/cancel/error/retry; fixed visible example/internal scroll; shared catalog alignment; spatial arrows/edges; prominent activity summary; rightmost submission columns; favorites name.');
} catch(error) {await page.screenshot({path:output+'/failure.png'});throw error;}
finally {await context.close();await browser.close();}
