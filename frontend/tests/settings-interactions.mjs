import assert from 'node:assert/strict';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const vite=await createServer({cacheDir:'../.backups/next-local/settings-interactions-vite',server:{host:'127.0.0.1',port:0,watch:null}});await vite.listen();
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
 const burst=page.locator('.balloon-pop-burst'),rubber=page.locator('.balloon-rubber-fragments');assert.equal(await rubber.locator(':scope>path').count(),15);assert.equal(await burst.locator('.balloon-string').getAttribute('d'),originalString);
 assert(await rubber.locator(':scope>path').evaluateAll(paths=>paths.every(path=>path.getAttribute('d').includes('Q')&&path.getAttribute('fill')==='currentColor'&&path.getAttribute('stroke')==='none')),'The established curved, filled rubber fragments are retained');
 const ropeBefore=await burst.locator('.balloon-string').boundingBox();await page.waitForTimeout(180);const ropeAfter=await burst.locator('.balloon-string').boundingBox();assert(ropeAfter.y>ropeBefore.y+8,'The original lower string falls independently');assert.equal(await page.evaluate(()=>window.sceneEntered),undefined);
 assert.equal(await burst.evaluate(node=>getComputedStyle(node).overflow),'hidden','The original effect is clipped at the tile boundary');
 await page.waitForFunction(()=>!document.querySelector('.balloon-flight').dataset.popped);
 await page.locator('.scene-globe').evaluate(node=>{for(const animation of node.getAnimations({subtree:true})){if(animation.animationName!=='planet-rotation'){animation.pause();animation.currentTime=9000;}}});
 const globe=page.locator('[data-scene-interactive=globe]');await globe.click({force:true});const firstSpeed=Number(await page.locator('.globe-turn').getAttribute('data-spin-speed'));await globe.click({force:true});assert(Number(await page.locator('.globe-turn').getAttribute('data-spin-speed'))>firstSpeed);
 const building=page.locator('[data-scene-interactive=building]').first();await building.dispatchEvent('click');assert.equal(await building.getAttribute('data-uprooted'),'true');
 assert.notEqual(await page.locator('.scene-globe').getAttribute('data-scene-state'),'exploded','Removing a house cancels only the full-city waiting explosion');
 await page.waitForTimeout(700);assert.equal(await building.evaluate(node=>getComputedStyle(node).visibility),'hidden','The replacement house is delayed');
 await page.waitForFunction(()=>!document.querySelector('[data-scene-interactive=building]').dataset.uprooted);
 await page.locator('.scene-globe').evaluate(node=>{for(const animation of node.getAnimations({subtree:true})){if(animation.animationName!=='planet-rotation'){animation.pause();animation.currentTime=1500;}}});
 for(let i=0;i<7;i++)await globe.dispatchEvent('click');await page.waitForFunction(()=>document.querySelector('.scene-globe').dataset.sceneState==='exploded');
 assert.equal(await page.locator('.globe-click-burst').count(),0,'Globe clicks use the established city explosion');
 assert.equal(await page.locator('.globe-fragment').count(),12);assert.equal(await page.locator('.globe-shockwave').evaluate(node=>getComputedStyle(node).animationName),'shockwave-spread');
 const bulb=page.locator('[data-scene-interactive=bulb]');await bulb.dispatchEvent('click');assert(Number(await page.locator('svg.scene-bulb').evaluate(n=>n.closest('svg').dataset.heat))>0);
 const brightness=await page.locator('.bulb-glass').evaluate(node=>Number(getComputedStyle(node).fillOpacity));await bulb.dispatchEvent('click');assert((await page.locator('.bulb-glass').evaluate(node=>Number(getComputedStyle(node).fillOpacity)))>brightness,'Consecutive clicks visibly increase brightness');
 for(let i=0;i<6;i++)await bulb.dispatchEvent('click');await page.waitForFunction(()=>document.querySelector('.scene-bulb').closest('svg').dataset.sceneState==='broken');
 const fragments=page.locator('.bulb-glass-fragments');assert.equal(await fragments.count(),1);assert.equal(await fragments.evaluate(node=>getComputedStyle(node).overflow),'hidden','Fragments are clipped to their tile');const tile=await page.locator('.settings-tile[data-section=accounts]').boundingBox(),effect=await fragments.boundingBox();assert(Math.abs(tile.y+tile.height-effect.y-effect.height)<2);
 const coffee=page.locator('[data-scene-interactive=coffee]'),cup=coffee.locator('.coffee-cup');const c=await cup.boundingBox();await page.mouse.move(c.x+c.width/2,c.y+c.height/2);await page.mouse.down();await page.mouse.move(c.x+c.width/2+15,c.y+c.height/2-100,{steps:8});await page.mouse.up();await page.waitForFunction(()=>document.querySelector('.scene-coffee').dataset.sceneState==='broken');assert.equal(await page.locator('.coffee-shards').count(),1);
 await page.waitForFunction(()=>!document.querySelector('.scene-bulb').closest('svg').dataset.sceneState);await bulb.dispatchEvent('click');assert(Number(await page.locator('svg.scene-bulb').evaluate(n=>n.closest('svg').dataset.heat))>0,'A replacement bulb remains clickable');
 await page.locator('.settings-tile[data-section=guide]>button').click({position:{x:20,y:20}});assert.equal(await page.evaluate(()=>window.sceneEntered),'guide');
 assert.deepEqual(errors,[]);console.log('PASS compass acceleration/decay, cloud and dinosaur drag, balloon-head pop, graphic clicks stay on page and blank area opens its setting');
}finally{await browser.close();await vite.close();}
