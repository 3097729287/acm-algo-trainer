import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const server=await createServer({server:{host:'127.0.0.1',port:0,watch:null}});await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:430,height:700}}),errors=[];page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(8000);
try{
 await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/tests/ability-evidence-fixture.html`);
 const trigger=page.getByRole('button',{name:'能力分依据',exact:true});await trigger.click();const popup=page.getByRole('dialog',{name:'能力分依据',exact:true});await popup.waitFor();
 assert.match(await popup.innerText(),/95% 模型区间 960–1520/);assert.match(await popup.innerText(),/有效证据权重 4.5/);assert.match(await popup.innerText(),/独立完成 5\/6/);
 assert.equal(await popup.getByRole('row').count(),7);assert.equal(await popup.getByRole('cell',{name:'Codeforces 官方',exact:true}).count(),4);assert.equal(await popup.getByRole('cell',{name:'0.25',exact:true}).count(),2);
 const bounds=await popup.boundingBox();assert(bounds.x>=12&&bounds.x+bounds.width<=418&&bounds.y>=12&&bounds.y+bounds.height<=688);assert(await popup.evaluate(node=>node.scrollHeight>node.clientHeight),'small viewport scrolls long evidence, instead of losing rows');
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);assert(await popup.evaluate(node=>node===document.activeElement));
 const table=popup.getByRole('region',{name:'作答证据表，可横向滚动'});await table.focus();await page.keyboard.press('ArrowRight');await page.waitForFunction(()=>document.querySelector('.ability-evidence-table').scrollLeft>0);
 await mkdir('tests/screenshots/ability-evidence',{recursive:true});await page.screenshot({path:'tests/screenshots/ability-evidence/narrow-430-font22.png'});
 await page.keyboard.press('Escape');assert.equal(await popup.count(),0);assert(await trigger.evaluate(node=>node===document.activeElement));
 await trigger.click();await page.setViewportSize({width:1100,height:850});await popup.waitFor();const wide=await popup.boundingBox();assert(wide.x>=12&&wide.x+wide.width<=1088);await page.mouse.click(2,2);assert.equal(await popup.count(),0);
 assert.deepEqual(errors,[]);console.log('PASS actual six-source evidence, interval/source/weight rows, viewport-clamped portal, 430/font22, scroll/focus/Esc/outside/resize');
}finally{await browser.close();await server.close();}
