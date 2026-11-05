import assert from 'node:assert/strict';
import {createServer} from 'vite';
import {chromium} from 'playwright';
import {mkdir,writeFile} from 'node:fs/promises';
const out='../.backups/contact-navigation-20261105';await mkdir(out,{recursive:true});
const vite=await createServer({cacheDir:out+'/vite',optimizeDeps:{entries:['tests/contact-navigation-fixture.html','tests/settings-interactions-fixture.html']},server:{host:'127.0.0.1',port:0,watch:null}});await vite.listen();
const browser=await chromium.launch({channel:'msedge',headless:true}),page=await browser.newPage({viewport:{width:2048,height:1152}}),errors=[],proof=[];page.on('pageerror',e=>errors.push(e.message));
const base=()=>vite.resolvedUrls.local[0];let ok=false;
try{
 await page.goto(base()+'tests/contact-navigation-fixture.html?mode=mock');
 await page.getByRole('button',{name:'重现赛',exact:true}).click();
 await page.getByRole('option',{name:'校队训练',exact:true}).click();
 for(const name of ['数学专场','团队模拟1','图论专场'])await page.getByRole('option',{name:new RegExp(name)}).waitFor();
 await page.getByRole('option',{name:/数学专场/}).click();
 await page.locator('.mock-create').getByRole('button',{name:/生成|刷新|组卷/}).first().click().catch(async()=>{await page.locator('.mock-create .paper-generate,.mock-create .mock-generate').click();});
 await page.waitForFunction(()=>window.navigationFixture.calls.some(call=>call.path==='contests/preview'));
 assert.equal(await page.evaluate(()=>window.navigationFixture.calls.find(call=>call.path==='contests/preview').body.contest),'1024数学专场考核');
 proof.push({schoolPicker:3,canonicalIdentityPreserved:true});
 await page.goto(base()+'tests/contact-navigation-fixture.html?mode=mock&unready=1');await page.getByRole('button',{name:'重现赛',exact:true}).click();await page.getByRole('option',{name:'校队训练',exact:true}).click();
 assert(await page.getByRole('option',{name:/数学专场.*题面待核验/}).isDisabled());proof.push({unverifiedSchoolVisible:true,unverifiedSchoolDisabled:true});
 await page.goto(base()+'tests/contact-navigation-fixture.html');
 await page.getByRole('button',{name:'比赛文件夹浏览',exact:true}).click();await page.getByRole('button',{name:/校队训练/}).click();
 assert.equal(await page.locator('.competition-card').count(),3);
 for(const name of ['数学专场','团队模拟1','图论专场'])assert(await page.locator('.competition-card-title').getByText(name,{exact:true}).isVisible());
 await page.screenshot({path:out+'/school-contests.png'});proof.push({schoolDirectory:3,conciseNames:true});
 await page.goto(base()+'tests/contact-navigation-fixture.html?mode=rankings');await page.locator('.ranking-identity').nth(2).waitFor();
 for(const width of [2048,1294,800]){
  await page.setViewportSize({width,height:1152});
  const positions=await page.locator('.ranking-identity>.user-presence').evaluateAll(nodes=>nodes.map(n=>{const r=n.getBoundingClientRect(),p=n.parentElement.getBoundingClientRect();return {x:r.x,center:r.y+r.height/2,expected:p.y+p.height/2};}));
  assert.equal(positions.length,3);assert(Math.max(...positions.map(p=>p.x))-Math.min(...positions.map(p=>p.x))<1);assert(positions.every(p=>Math.abs(p.center-p.expected)<1));
 }await page.screenshot({path:out+'/presence-alignment.png'});proof.push({presenceAligned:true});
 await page.goto(base()+'tests/settings-interactions-fixture.html');await page.locator('[data-scene-interactive=globe]').waitFor();
 for(const width of [2048,1294,800,430]){
  await page.setViewportSize({width,height:1152});await page.waitForTimeout(60);
  const groundError=await page.locator('.scene-dino-stage').evaluate(root=>{const a=new DOMPoint(0,289).matrixTransform(root.querySelector('.dino-landscape').getScreenCTM()),b=new DOMPoint(0,317.5).matrixTransform(root.querySelector('.dino-model').getScreenCTM());return Math.abs(a.y-b.y);});
  assert(groundError<2,'Feet remain on the real landscape ground after resize: '+groundError);
 }
 await page.setViewportSize({width:2048,height:1152});
 const dino=page.locator('.dino-traveler');await dino.scrollIntoViewIfNeeded();await page.waitForTimeout(60);
 const eyes=await dino.locator('.dino-eyes circle').first().boundingBox();await page.mouse.move(eyes.x+eyes.width/2,eyes.y+eyes.height/2);await page.mouse.down();await page.mouse.move(eyes.x+eyes.width/2,eyes.y+eyes.height/2-90,{steps:5});
 assert.equal(await dino.getAttribute('data-scene-state'),'held');assert.equal(await dino.locator('.dino-foot').first().evaluate(n=>n.getAnimations().length),0);
 await page.evaluate(()=>window.dispatchEvent(new Event('blur')));await page.mouse.up();assert.notEqual(await dino.getAttribute('data-scene-state'),'held');await page.waitForFunction(()=>document.querySelector('.dino-traveler').dataset.sceneState==='walking');
 proof.push({groundedAcrossWidths:true,lostWindowRelease:true,airborneWalkingStopped:true});
 // Recreate CSS animations by toggling the app preference. Click the actual
 // surface with a real pointer; no cached Animation objects or phase mocks.
 await page.evaluate(()=>document.documentElement.dataset.motion='off');await page.waitForTimeout(20);await page.evaluate(()=>document.documentElement.dataset.motion='on');await page.waitForTimeout(40);
 const globe=page.locator('[data-scene-interactive=globe]');await globe.scrollIntoViewIfNeeded();const box=await globe.boundingBox();
 for(let i=0;i<6;i++)await page.mouse.click(box.x+box.width/2,box.y+box.height/2,{delay:5});
 assert.equal(await page.locator('svg.scene-globe').getAttribute('data-scene-state'),'exploded');
 assert(await page.locator('.globe-burst').evaluate(node=>Number(getComputedStyle(node).opacity)>.4),'A real burst is visible immediately');
 await page.screenshot({path:out+'/globe-burst.png'});proof.push({rapidClickVisibleBurst:true,preferenceResetSupported:true});
 assert.deepEqual(errors,[]);ok=true;
}finally{await writeFile(out+'/verification.json',JSON.stringify({ok,proof,errors},null,2));await browser.close();await vite.close();}
console.log(JSON.stringify({ok,proof,errors}));
