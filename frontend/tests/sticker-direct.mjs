import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const out='../.backups/next-152/direct-ui';await mkdir(out,{recursive:true});
const vite=await createServer({cacheDir:out+'/vite',server:{host:'127.0.0.1',port:0,watch:null}});await vite.listen();
const browser=await chromium.launchPersistentContext(out+'/profile',{channel:'msedge',headless:true,viewport:{width:1440,height:1100}}),page=browser.pages()[0],errors=[];page.on('pageerror',issue=>errors.push(issue.message));page.setDefaultTimeout(7000);
const pending=()=>page.evaluate(()=>directFixture.pending()),finish=async(loss=false)=>{const next=(await pending())[0];assert(next);await page.evaluate(({id,loss})=>directFixture.complete(id,loss),{id:next.id,loss});};
const placed=id=>page.locator(`[data-unit-id="${id}"]`);
const blank=async(x=.1,y=.85)=>{const box=await page.getByRole('region',{name:'贴纸区域'}).boundingBox();await page.mouse.click(box.x+box.width*x,box.y+box.height*y);};
const drag=async(from,to)=>{await page.mouse.move(from.x,from.y);await page.mouse.down();await page.mouse.move(to.x,to.y,{steps:8});await page.mouse.up();};
try{
 await page.addInitScript(()=>{for(const owner of ['A','B'])localStorage.removeItem('tb.sticker-layout.v1:'+owner);});
 await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/sticker-direct-fixture.html`,{timeout:45000});
 await page.getByRole('button',{name:'贴纸',exact:true}).click();await placed('A-leaf').click();
 assert.equal(await page.locator('.selected-sticker').count(),1);assert.equal((await pending()).length,0,'A click selects without sending a placement');
 assert.equal(await page.locator('.sticker-edit-tools,.sticker-size-handle').count(),0);
 for(const name of ['旋转贴纸','固定贴纸','取消贴纸'])assert.equal(await page.getByRole('button',{name,exact:true}).count(),0);
 await blank();assert.equal((await pending()).length,0,'Deselecting an unchanged placement needs no round trip');
 await blank(.75,.75);await page.getByRole('button',{name:'普通 gem，库存 1',exact:true}).click();
 const started=performance.now();await blank();assert.equal(await placed('A-gem').count(),1);assert.equal(await page.locator('.selected-sticker').count(),0);assert.equal((await pending()).length,1);
 const immediateMs=performance.now()-started;assert(immediateMs<1000,'Placement is visible before any server reply');
 await placed('A-leaf').click();const original=await placed('A-leaf').boundingBox(),edge=await placed('A-leaf').locator('[data-sticker-edge=east]').boundingBox();
 await drag({x:edge.x+edge.width/2,y:edge.y+edge.height/2},{x:edge.x+edge.width/2+20,y:edge.y+edge.height/2});
 assert((await placed('A-leaf').boundingBox()).width>original.width+10,'Dragging a side resizes immediately while another write is pending');
 const corner=await placed('A-leaf').locator('[data-sticker-corner=se]').boundingBox(),rect=await placed('A-leaf').boundingBox(),center={x:rect.x+rect.width/2,y:rect.y+rect.height/2};
 const from={x:corner.x+corner.width/2,y:corner.y+corner.height/2},dx=from.x-center.x,dy=from.y-center.y;
 await drag(from,{x:center.x-dy,y:center.y+dx});
 assert(Math.abs(Number((await placed('A-leaf').getAttribute('style')).match(/rotate\(([-.\d]+)deg\)/)[1])-90)<1);
 await finish();await page.waitForFunction(()=>directFixture.pending().length===1);await finish();await page.waitForFunction(()=>directFixture.state().units.find(unit=>unit.id==='A-leaf').revision===1);
 const leaf=await page.evaluate(()=>directFixture.state().units.find(unit=>unit.id==='A-leaf'));
 assert(Math.abs(leaf.placement.angle-90)<1);assert(leaf.placement.scale>1.2);assert.equal((await page.evaluate(()=>directFixture.calls.filter(call=>call.path==='stickers/place'))).length,2,'Intermediate side/corner gestures coalesce behind the first request');
 // A lost acknowledgement keeps the same operation identity on an explicit retry.
 await blank();await placed('A-leaf').click();const leafRect=await placed('A-leaf').boundingBox();await drag({x:leafRect.x+leafRect.width/2,y:leafRect.y+leafRect.height/2},{x:leafRect.x+leafRect.width/2+70,y:leafRect.y+leafRect.height/2});await finish(true);await page.getByRole('alert').waitFor();
 const lost=await page.evaluate(()=>directFixture.calls.filter(call=>call.path==='stickers/place').at(-1).body.requestId);
 await page.evaluate(()=>window.dispatchEvent(new Event('focus')));await page.waitForFunction(()=>!document.querySelector('[role=alert]'));
 const replay=await page.evaluate(()=>directFixture.calls.filter(call=>call.path==='stickers/place').at(-1).body.requestId);assert.equal(replay,lost);assert.equal(await page.evaluate(()=>directFixture.state().units.find(unit=>unit.id==='A-leaf').revision),2);
 // A late old-owner response never paints the new account.
 await blank();await placed('A-leaf').click();const r=await placed('A-leaf').boundingBox();await drag({x:r.x+r.width/2,y:r.y+r.height/2},{x:r.x+r.width/2+30,y:r.y+r.height/2});
 await page.evaluate(()=>directFixture.owner('B'));await placed('B-leaf').waitFor();await finish();assert.equal(await page.locator('[data-unit-id^="A-"]').count(),0);
 // Cancellation stays inside the waiting control, and survives one disconnect.
 await page.getByRole('button',{name:'开始匹配',exact:true}).click();const cancel=page.getByRole('button',{name:'取消匹配',exact:true});await cancel.waitFor();
 const metrics=await cancel.evaluate(node=>{const a=node.getBoundingClientRect(),b=node.parentElement.getBoundingClientRect(),s=getComputedStyle(node);return {inside:a.left>=b.left&&a.right<=b.right&&a.top>=b.top&&a.bottom<=b.bottom,centerOffset:Math.abs((a.top+a.bottom-b.top-b.bottom)/2),border:s.borderTopWidth};});
 assert(metrics.inside&&metrics.centerOffset<1);assert.equal(metrics.border,'0px');await cancel.click();await page.getByRole('alert').filter({hasText:'isolated connection unavailable'}).waitFor();
 await page.getByRole('button',{name:'开始匹配',exact:true}).waitFor({timeout:9000});
 const cancellations=await page.evaluate(()=>directFixture.calls.filter(call=>call.path==='duel/cancel'));assert.equal(cancellations.length,2);assert.equal(cancellations[0].body.requestId,cancellations[1].body.requestId);assert.equal(cancellations[0].body.ticket,cancellations[1].body.ticket);
 assert.equal((await page.evaluate(()=>directFixture.calls.filter(call=>call.path==='duel/join'))).length,1,'Cancel recovery never rejoins');
 assert.deepEqual(errors,[]);await page.screenshot({path:out+'/direct-controls.png'});await writeFile(out+'/result.json',JSON.stringify({ok:true,immediateMs,metrics,scenarios:['single-click selection','no floating controls','placement before server reply','edge resize','corner rotation','coalesced writes','lost-response idempotency','owner isolation','aligned internal cancel','disconnect cancellation retry without join'],errors},null,2));
 console.log('PASS direct sticker placement/transform with delayed and lost replies, owner isolation, and aligned cancellation through a disconnect.');
}catch(issue){await page.screenshot({path:out+'/failure.png'});throw issue;}finally{await browser.close();await vite.close();}
