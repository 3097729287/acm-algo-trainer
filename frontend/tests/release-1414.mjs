import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
import {realpathSync} from 'node:fs';
import {createServer} from 'vite';
import {chromium} from 'playwright';

const server=await createServer({server:{host:'127.0.0.1',port:0,fs:{allow:[process.cwd(),realpathSync('node_modules')]}}});
await server.listen();
const browser=await chromium.launch({channel:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1366,height:768}});
const out='../.backups/local-1414/ui',base=server.resolvedUrls.local[0],errors=[];
await mkdir(out,{recursive:true});page.on('pageerror',e=>{errors.push(e.message);console.error('Page error:',e.message);});
const open=async mode=>{await page.goto(base+'tests/release-1413-fixture.html?view='+mode);await page.waitForTimeout(160);};
try {
 await open('records');const filter=page.getByRole('combobox',{name:'提交结果分类'});await filter.click();
 assert.deepEqual(await page.getByRole('listbox').getByRole('option').allTextContents(),['全部结果','AC','WA','CE','TLE','MLE','RE','OLE','SE']);
 await page.getByRole('listbox').getByRole('option',{name:'WA',exact:true}).click();
 assert(await page.evaluate(()=>window.fixture.calls.some(x=>x.path?.startsWith('submissions?')&&new URLSearchParams(x.path.split('?')[1]).get('verdict')==='WA')));
 await filter.click();await page.getByRole('listbox').getByRole('option',{name:'AC',exact:true}).click();
 assert.equal(await filter.count(),1);await page.screenshot({path:out+'/records.png'});
 for(const theme of ['dark','light']) {
  await open('settings');await page.evaluate(theme=>{document.documentElement.dataset.theme=theme;document.documentElement.dataset.motion='off';},theme);
  assert.equal(await page.locator('.dino-outline').getAttribute('fill'),'currentColor');
  assert.equal(await page.locator('.dino-outline').getAttribute('fill-opacity'),'.06');
  await page.screenshot({path:out+'/dinosaur-'+theme+'.png'});
  for(const style of ['minimal','outlined','aurora','blueprint']) {
   await open('lists');await page.evaluate(({theme,style})=>{document.documentElement.dataset.theme=theme;document.documentElement.dataset.panelStyle=style;}, {theme,style});
   const bar=page.locator('.training-list-directory');
   assert.equal(Math.round(await bar.evaluate(n=>n.getBoundingClientRect().height)),44);
   await bar.screenshot({path:`${out}/directory-${theme}-${style}.png`});
   await page.evaluate(()=>{const panel=document.querySelector('.list-page');const ref=document.createElement('div');ref.className='header-comparison';ref.innerHTML='<table class="problem-table" style="width:100%;border-collapse:collapse"><thead><tr><th style="height:44px;padding:0;text-align:left">题目 / 来源</th></tr></thead></table>';panel.prepend(ref);document.querySelector('.training-list-directory').style.display='none';});
   await page.locator('.header-comparison thead').screenshot({path:`${out}/library-${theme}-${style}.png`});
  }
 }
 for(const width of [1024,1366,1920]) {
  await page.setViewportSize({width,height:768});await open('lectures');
  for(const heading of await page.locator('.lecture-item-heading').all()) {
   const bounds=await heading.evaluate(node=>{const title=node.querySelector('strong').getBoundingClientRect(),level=node.querySelector('.lecture-difficulty').getBoundingClientRect();return {titleCenter:title.y+title.height/2,levelCenter:level.y+level.height/2,titleRight:title.right,levelLeft:level.x};});
   assert(Math.abs(bounds.titleCenter-bounds.levelCenter)<1,JSON.stringify(bounds));assert(bounds.titleRight<bounds.levelLeft);
  }
  await page.screenshot({path:`${out}/lectures-${width}.png`});
 }
 await page.route(url=>url.pathname.startsWith('/api/'),route=>route.fulfill({contentType:'application/json',body:JSON.stringify(route.request().url().includes('/account')?{required:true,authenticated:false}:{status:'idle',currentVersion:'1.4.14'})}));
 await open('login');await page.getByRole('heading',{name:'登录 ToBe',exact:true}).waitFor();assert.equal(await page.locator('.account-logo').innerText(),'ToBe');
 await page.screenshot({path:out+'/login.png'});
 await open('startup');assert.equal(await page.locator('.startup-logo').innerText(),'ToBe');
 assert.deepEqual(errors,[]);console.log('PASS ToBe login/startup, result menu, eight header comparisons, dinosaur themes, and lecture alignment at three widths');
}finally{await browser.close();await server.close();}
