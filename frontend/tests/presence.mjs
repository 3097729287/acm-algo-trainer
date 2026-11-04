import assert from 'node:assert/strict';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const server=await createServer({cacheDir:'../.backups/next-local/presence-vite',server:{host:'127.0.0.1',port:18797,strictPort:true,hmr:false}});await server.listen();
const browser=await chromium.launch({channel:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];
page.on('pageerror',issue=>errors.push(issue.message));
try{
 await page.goto('http://127.0.0.1:18797/tests/presence-fixture.html');await page.waitForFunction(()=>window.presenceFixture?.owner);
 await page.getByLabel('在线人数',{exact:true}).getByText('在线 · —人',{exact:true}).waitFor();
 await page.evaluate(()=>presenceFixture.owner(presenceFixture.ids[0]));await page.getByLabel('在线人数',{exact:true}).getByText('在线 · 5人',{exact:true}).waitFor();
 const ranking=page.getByRole('region',{name:'排位排行榜与对战记录'});
 for(const label of ['做题中','重现赛中','从零讲中','实验室中'])await ranking.getByText(label,{exact:true}).waitFor();
 await ranking.getByText('甲 胜',{exact:true}).waitFor();assert.equal(await ranking.locator('section').count(),2);
 assert.equal(await ranking.locator('.duel-public-record').count(),1);
 for(const activity of ['replay','lecture','lab']){
  await page.evaluate(activity=>presenceFixture.activity(activity),activity);
  await page.waitForFunction(activity=>presenceFixture.calls.some(call=>call.path==='presence'&&call.body.activity===activity),activity);
 }
 await page.evaluate(()=>{presenceFixture.hold=presenceFixture.ids[0];window.dispatchEvent(new Event('focus'));});
 await page.waitForFunction(()=>presenceFixture.pending.length===1);
 await page.evaluate(()=>presenceFixture.owner(presenceFixture.ids[1],'replay'));await page.getByLabel('在线人数',{exact:true}).getByText('在线 · 2人',{exact:true}).waitFor();
 await page.evaluate(()=>presenceFixture.pending[0]({owner:presenceFixture.ids[0],available:true,count:99,users:[]}));
 await page.waitForTimeout(100);assert.equal(await page.getByLabel('在线人数',{exact:true}).innerText(),'在线 · 2人');
 await page.evaluate(()=>presenceFixture.mode('thought'));await page.waitForFunction(()=>presenceFixture.calls.some(call=>call.path==='duel/board?mode=thought'));
 await ranking.getByText('甲 胜',{exact:true}).waitFor();
 await page.setViewportSize({width:360,height:900});assert(await ranking.evaluate(node=>node.scrollWidth<=node.clientWidth+1));
 await page.evaluate(()=>{presenceFixture.fail=true;window.dispatchEvent(new Event('focus'));});await page.getByLabel('在线人数',{exact:true}).getByText('在线 · —人',{exact:true}).waitFor();
 assert.deepEqual(errors,[]);console.log('PASS presence initialization, activity labels, public result columns, account takeover/late reply, thought mode, narrow layout and offline unknown count');
}finally{await browser.close();await server.close();}
