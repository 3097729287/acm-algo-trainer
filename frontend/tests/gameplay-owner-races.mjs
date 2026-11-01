import assert from 'node:assert/strict';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const vite=await createServer({server:{host:'127.0.0.1',port:0,watch:null}});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];
page.setDefaultTimeout(5000);
page.on('pageerror',error=>errors.push(error.message));
const find=async(owner,path)=>{await page.waitForFunction(({owner,path})=>gameplayRaces.pending().some(p=>p.owner===owner&&p.path===path),{owner,path});return page.evaluate(({owner,path})=>gameplayRaces.pending().find(p=>p.owner===owner&&p.path===path).id,{owner,path});};
const finish=id=>page.evaluate(id=>gameplayRaces.finish(id),id);
try{
 await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/gameplay-owner-fixture.html`);
 await page.getByRole('button',{name:'开始匹配',exact:true}).click();const old=await find('A','duel/join');
 await page.getByRole('button',{name:'账号 B',exact:true}).click();await page.getByRole('button',{name:'开始匹配',exact:true}).click();const current=await find('B','duel/join');
 await finish(old);assert(await page.getByRole('button',{name:'开始匹配',exact:true}).isDisabled(),'Old write must not release the new owner busy state');
 await finish(current);await page.getByRole('button',{name:'取消匹配',exact:true}).waitFor();assert(await page.getByRole('button',{name:'取消匹配',exact:true}).isEnabled());
 const choose=async()=>{await page.getByRole('button',{name:'贴纸',exact:true}).click();const box=await page.getByRole('region',{name:'贴纸区域'}).boundingBox();await page.mouse.click(box.x+box.width*.5,box.y+box.height*.5);await page.locator('.sticker-choice').click();await page.keyboard.press('Enter');};
 await page.getByRole('button',{name:'账号 A',exact:true}).click();await choose();const firstPlace=await find('A','stickers/place');
 await page.getByRole('button',{name:'账号 B',exact:true}).click();await choose();const secondPlace=await find('B','stickers/place');
 await page.evaluate(()=>{gameplayRaces.deferRead('B','stickers');window.dispatchEvent(new Event('focus'));});const stale=await find('B','stickers');
 await finish(firstPlace);assert(await page.getByRole('button',{name:'固定贴纸',exact:true}).isDisabled());
 await finish(secondPlace);await page.waitForFunction(()=>document.querySelectorAll('.placed-sticker:not(.selected-sticker)').length===1);
 await finish(stale);assert.equal(await page.locator('.placed-sticker:not(.selected-sticker)').count(),1,'Stale inventory must not undo a confirmed placement');
 assert.equal(await page.locator('.selected-sticker').count(),0);assert.equal(await page.getByRole('alert').count(),0);assert.equal(await page.getByLabel('当前账号').textContent(),'B');
 assert.deepEqual(errors,[]);console.log('PASS real React owner switches, overlapping delayed writes, busy isolation and stale-inventory ordering; no official I/O');
}finally{await browser.close();await vite.close();}
