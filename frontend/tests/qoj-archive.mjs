// Real local API and App against a disposable offline workspace; no site POST.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
const info=JSON.parse(fs.readFileSync('../.backups/local-1423/steering-ui-port.json','utf8'));
const base='http://127.0.0.1:'+info.port,output='../.backups/local-1423/ui';
const browser=await chromium.launch({channel:'msedge',headless:true});
const context=await browser.newContext({viewport:{width:1440,height:900}}),page=await context.newPage();
const errors=[],external=[];page.on('pageerror',error=>errors.push(error.message));
await context.route('https://qoj.ac/**',route=>{external.push(route.request().url());return route.abort();});
try{
 const data=await(await context.request.get(base+'/api/data')).json();
 assert.equal(data.rows.filter(p=>p.platform==='QOJ').length,39);
 assert(!data.rows.some(p=>/全球总决赛|北欧大学生|大田区域赛|莫斯科分区赛/.test(p.contest||'')));
 const events=(await(await context.request.get(base+'/api/contests/events')).json()).events;
 for(const place of ['济南','郑州','重庆']){
  const name='CCPC 2025 '+place+'区域赛',event=events.find(p=>p.name===name);
  assert(event,name);assert.equal(event.count,13);assert.equal(event.expectedCount,13);assert.equal(event.complete,true);
  const response=await context.request.post(base+'/api/contests/preview',{headers:{'X-TB-Token':data.token,Origin:base},data:{mode:'replay',contest:name}});
  const value=await response.json();assert(response.ok(),JSON.stringify(value));
  assert.equal(value.plan.slots.length,13);assert.equal(value.plan.duration,300);
  assert.deepEqual(value.plan.slots.map(p=>p.letter),[...'ABCDEFGHIJKLM']);
  assert(value.plan.slots.every(p=>p.judgeScope==='samples'));
 }
 await page.goto(base);await page.getByRole('navigation',{name:'主导航'}).waitFor();
 await page.getByRole('button',{name:'题库',exact:true}).click();
 await page.getByRole('textbox',{name:'搜索题目',exact:true}).fill('Cipher');
 const row=page.locator('tr[data-id="xcpc-qoj::15032"]');await row.waitFor();
 assert.equal(await row.locator('.platform-symbol').innerText(),'QJ');
 await row.getByRole('button',{name:'Cipher',exact:true}).click();
 await page.getByRole('textbox',{name:'C++ 代码',exact:true}).waitFor();
 await page.waitForFunction(()=>document.querySelector('.reading-image img')?.naturalWidth>0);
 assert.equal(await page.getByRole('button',{name:'中文',exact:true}).isDisabled(),true);
 assert((await page.locator('.wb-statement pre').allTextContents()).some(value=>value.includes('1000000007 1000000009')));
 await page.screenshot({path:output+'/qoj-cipher-workbench.png'});
 await page.getByRole('button',{name:'放大图片：原题题面第 1 页',exact:true}).click();
 await page.locator('.reading-image-dialog[open]').waitFor();await page.keyboard.press('Escape');
 assert.equal(await page.locator('.reading-image-dialog[open]').count(),0);
 await page.getByRole('textbox',{name:'C++ 代码',exact:true}).waitFor();
 await page.getByRole('button',{name:'返回列表',exact:true}).click();
 assert.equal(await page.getByRole('textbox',{name:'搜索题目',exact:true}).inputValue(),'Cipher');
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 console.log('PASS 39 QOJ tasks, 3 complete 13-slot/300-minute replay previews, sample-only judging, offline PDF rendering and zoom, honest translation state and retained search filter.');
}catch(error){await page.screenshot({path:output+'/qoj-archive-failure.png'});throw error;}
finally{await page.unrouteAll({behavior:'wait'});await context.close();await browser.close();}
