import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const out='../.backups/rain-rebuild-20261107/directory';await mkdir(out,{recursive:true});
const server=await createServer({server:{host:'127.0.0.1',port:0},optimizeDeps:{entries:['tests/learning-browser-fixture.html']}});await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[],checks=[];page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto(server.resolvedUrls.local[0]+'tests/learning-browser-fixture.html');await page.waitForFunction(()=>window.studyFixture);
 await page.evaluate(()=>studyFixture.open({kind:'lecture',id:studyFixture.lectures[0].id}));await page.locator('.lecture-markdown').waitFor();await page.getByRole('button',{name:'讲解目录',exact:true}).click();
 const search=page.getByRole('searchbox',{name:'搜索从零讲目录',exact:true}),bar=page.locator('.lecture-directory-toolbar'),list=page.locator('.lecture-directory>.lectures-list');await search.waitFor();
 for(const width of [1600,900,640,390])for(const scale of [1,1.8,.6]){
  await page.setViewportSize({width,height:900});
  await page.evaluate(({scale,width})=>{const pane=document.querySelector('.study-lecture:not([hidden])');for(const n of pane.querySelectorAll('.lecture-directory-toolbar,.study-single-controls'))n.style.zoom=scale;document.documentElement.style.setProperty('--ui-font-size',width>1000?'24px':'18px');},{scale,width});
  const before=await bar.boundingBox();await list.evaluate(n=>{n.scrollTop=127;});await page.waitForTimeout(30);
  const check=await list.evaluate(n=>{const b=n.getBoundingClientRect(),bar=n.previousElementSibling.getBoundingClientRect();const hits=[];for(const x of [b.left+5,b.left+b.width*.5,b.right-5]){const hit=document.elementFromPoint(x,bar.bottom-2);hits.push(!hit||!n.contains(hit));}return{top:b.top,barBottom:bar.bottom,scroll:n.scrollTop,clipped:hits.every(Boolean),barTop:bar.top};});
  assert(Math.abs(check.top-check.barBottom)<1,JSON.stringify({width,scale,check}));assert(Math.abs(check.barTop-before.y)<1);assert(check.clipped,JSON.stringify({width,scale,check}));checks.push({width,scale,...check});
 }
 await search.fill('vector');assert(await list.locator('button').count()>0);await search.fill('');await page.setViewportSize({width:1600,height:1000});await page.screenshot({path:out+'/fixed-directory.png'});
 assert.deepEqual(errors,[]);await writeFile(out+'/result.json',JSON.stringify({ok:true,checks,errors},null,2));console.log(JSON.stringify({ok:true,checks:checks.length,errors}));
}catch(error){await page.screenshot({path:out+'/failure.png'});throw error;}finally{await browser.close();await server.close();}
