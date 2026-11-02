import assert from 'node:assert/strict';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const vite=await createServer({server:{host:'127.0.0.1',port:0,watch:null}});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[];page.on('pageerror',error=>errors.push(error.message));
try{
 await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/settings-interactions-fixture.html`);
 const compass=page.locator('[data-scene-interactive=compass]');await compass.waitFor();
 await compass.click();const first=Number(await page.locator('.compass-needle').getAttribute('data-spin-speed'));
 await compass.click();assert(Number(await page.locator('.compass-needle').getAttribute('data-spin-speed'))>first);
 assert.equal(await page.evaluate(()=>window.sceneEntered),undefined);
 await page.waitForFunction(()=>!document.querySelector('.scene-compass').closest('svg').dataset.interacting,{timeout:8000});
 for(const kind of ['cloud','dino']){
  const item=page.locator(`[data-scene-interactive=${kind}]`).first();
  await item.evaluate(node=>{node.style.animation='none';node.style.left='30px';node.style.top='40px';node.style.bottom='auto';node.style.opacity='1';for(const a of node.getAnimations({subtree:true}))a.pause();});
  const hit=item.locator(kind==='dino'?'.dino-eyes circle':'path').first(),box=await hit.boundingBox(),before=await item.boundingBox();
  await page.mouse.move(box.x+box.width/2,box.y+box.height/2);await page.mouse.down();await page.mouse.move(box.x+box.width/2+35,box.y+box.height/2+12,{steps:5});await page.mouse.up();
  const after=await item.boundingBox();assert(Math.abs(after.x-before.x-35)<15,kind);assert.equal(await page.evaluate(()=>window.sceneEntered),undefined,kind);
  if(kind==='cloud'){
   await page.waitForFunction(()=>document.querySelector('[data-scene-interactive=cloud]').dataset.sceneState==='drifting');
   await page.waitForTimeout(220);const drift=await item.boundingBox();assert(Math.abs(drift.x-after.x)>1,'Cloud continues moving after release');
  }else{
   await page.waitForFunction(()=>document.querySelector('[data-scene-interactive=dino]').dataset.sceneState==='dead');
   await page.waitForFunction(()=>document.querySelector('[data-scene-interactive=dino]').dataset.sceneState==='walking');
   assert.equal(await item.getAttribute('data-dead'),null,'A high fall retires the dinosaur and a new one walks in');
  }
 }
 const balloon=page.locator('.balloon-flight');await balloon.evaluate(node=>{node.style.animation='none';node.style.bottom='20px';node.style.opacity='1';});
 const originalString=await balloon.locator('.balloon-string').getAttribute('d');
 await page.locator('[data-scene-interactive=balloon]').click();assert.equal(await balloon.getAttribute('data-popped'),'true');
 const burst=page.locator('.balloon-pop-burst');assert.equal(await burst.locator(':scope>path').count(),15);assert.equal(await burst.locator('.balloon-string').getAttribute('d'),originalString);
 assert(await burst.locator(':scope>path').evaluateAll(paths=>paths.every(path=>path.getAttribute('d').endsWith('Z')&&path.getAttribute('fill')==='currentColor')),'Burst uses torn rubber pieces instead of a ring of strokes');
 const ropeBefore=await burst.locator('g').boundingBox();await page.waitForTimeout(180);const ropeAfter=await burst.locator('g').boundingBox();assert(ropeAfter.y>ropeBefore.y+8,'The original lower string falls independently');assert.equal(await page.evaluate(()=>window.sceneEntered),undefined);
 await page.waitForFunction(()=>!document.querySelector('.balloon-flight').dataset.popped);
 await page.locator('.settings-tile[data-section=guide]>button').click({position:{x:20,y:20}});assert.equal(await page.evaluate(()=>window.sceneEntered),'guide');
 assert.deepEqual(errors,[]);console.log('PASS compass acceleration/decay, cloud and dinosaur drag, balloon-head pop, graphic clicks stay on page and blank area opens its setting');
}finally{await browser.close();await vite.close();}
