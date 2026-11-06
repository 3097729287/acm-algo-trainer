import assert from 'node:assert/strict';
import {mkdir,writeFile,copyFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const out=new URL('../../.backups/library-backgrounds/checks/',import.meta.url);await mkdir(out,{recursive:true});
const server=await createServer({server:{host:'127.0.0.1',port:0,hmr:false},optimizeDeps:{entries:['tests/library-backgrounds-fixture.html']}});await server.listen();
const browser=await chromium.launch({channel:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[],remote=[];
page.on('pageerror',error=>errors.push(error.message));page.on('request',request=>{if(/^https?:/.test(request.url())&&!['localhost','127.0.0.1'].includes(new URL(request.url()).hostname))remote.push(request.url());});
try{
 await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/tests/library-backgrounds-fixture.html`);await page.waitForFunction(()=>window.scenes?.length===11);
 const results=[];
 await page.evaluate(()=>{const host=document.createElement('div');host.id='capture';host.style.cssText='position:fixed;inset:0;z-index:99999';document.body.append(host);window.engine=new MotionScene(host,{id:'waves'});});
 await page.waitForFunction(()=>engine.host.dataset.ready==='true');
 const uninterrupted=await page.evaluate(async()=>{const effect=engine.effect,canvas=effect.renderer.domElement,frames=engine.frames;for(let i=0;i<3;i++){document.documentElement.dataset.theme=document.documentElement.dataset.theme||'dark';await new Promise(resolve=>setTimeout(resolve,40));}return{sameEffect:engine.effect===effect,sameCanvas:engine.effect?.renderer.domElement===canvas,moving:engine.frames>frames};});
 assert.deepEqual(uninterrupted,{sameEffect:true,sameCanvas:true,moving:true},'Saving unchanged appearance preferences must not restart the background');
 await page.evaluate(()=>{window.previousEffect=engine.effect;document.documentElement.dataset.theme='light';});await page.waitForFunction(()=>engine.effect&&engine.effect!==previousEffect&&engine.host.dataset.ready==='true');
 await page.evaluate(()=>{window.previousEffect=engine.effect;document.documentElement.dataset.theme='dark';});await page.waitForFunction(()=>engine.effect&&engine.effect!==previousEffect&&engine.host.dataset.ready==='true');
 for(const {id}of await page.evaluate(()=>window.scenes)){
  await page.evaluate(async id=>{if(engine.id!==id)await engine.setScene(id);else await engine.ready;},id);
  await page.waitForFunction(()=>document.getElementById('capture').dataset.ready==='true');await page.waitForTimeout(450);
  const before=await page.evaluate(()=>({frames:engine.frames,snapshot:engine.snapshot()}));await page.waitForTimeout(220);const after=await page.evaluate(()=>({frames:engine.frames,snapshot:engine.snapshot()}));
  if(id!=='meteors'){assert(after.frames>before.frames,`${id} animates`);assert.notEqual(after.snapshot,before.snapshot,`${id} changes the picture`);}
  await page.evaluate(()=>engine.setPaused(true));const paused=await page.evaluate(()=>engine.frames);await page.mouse.move(300,400);await page.waitForTimeout(100);assert.equal(await page.evaluate(()=>engine.frames),paused,`${id} stops when paused`);
  await page.locator('#capture').screenshot({path:fileURLToPath(new URL(id+'.jpg',out)),type:'jpeg',quality:85});
  results.push({id,frames:after.frames-before.frames,paused:true});await page.evaluate(()=>engine.setPaused(false));
 }
 await page.evaluate(()=>{engine.destroy();document.getElementById('capture').remove();});
 await page.getByRole('button',{name:'背景选择',exact:true}).first().click();const picker=page.getByRole('dialog',{name:'背景选择'});assert.equal(await picker.locator('.background-choice').count(),11);await picker.getByRole('button',{name:'我的背景'}).click();await picker.getByText('10 级解锁自选图片背景',{exact:true}).waitFor();assert.equal(await picker.locator('input[type=file]').count(),0);await picker.getByRole('button',{name:'关闭背景选择'}).click();
 await page.evaluate(()=>setLevel(10));await page.getByRole('button',{name:'背景选择',exact:true}).first().click();await picker.getByRole('button',{name:'我的背景'}).click();await picker.getByRole('button',{name:'添加背景图片或动图'}).waitFor();await picker.getByRole('button',{name:'奖励背景'}).click();await picker.getByRole('button',{name:'使用背景 立体海浪',exact:true}).click();await page.locator('.workspace-background-layer[data-background-id=waves]').waitFor();await page.waitForFunction(()=>document.querySelector('.workspace-background-layer .motion-background')?.dataset.ready==='true');
 assert.equal(await page.locator('[aria-label="页面背景"] .background-option').count(),2);assert.equal(await page.getByRole('button',{name:'夜空极光',exact:true}).count(),0);
 await page.emulateMedia({reducedMotion:'reduce'});await page.waitForFunction(()=>document.querySelector('.motion-background').dataset.paused==='true');await page.emulateMedia({reducedMotion:'no-preference'});await page.waitForFunction(()=>document.querySelector('.motion-background').dataset.paused==='false');
 await page.getByRole('button',{name:'火箭',exact:true}).click();await page.waitForTimeout(600);const displacement=await page.locator('.rocket-flight').evaluate(node=>{const m=new DOMMatrix(getComputedStyle(node).transform);return Math.hypot(m.m41,m.m42);});assert(displacement>2,'An edge placement must fly, rather than only showing flame');
 await page.waitForTimeout(3000);assert.equal(await page.locator('.rocket-flight').evaluate(node=>getComputedStyle(node).transform),'none');
 for(const width of [1440,900,640,390]){await page.setViewportSize({width,height:900});await page.getByRole('button',{name:'背景选择',exact:true}).first().click();await picker.waitFor();assert(await picker.evaluate(node=>node.scrollWidth<=node.clientWidth+1));await picker.getByRole('button',{name:'关闭背景选择'}).click();}
 assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);const result={ok:true,effects:results,unchangedThemeKeepsAnimation:true,themePaletteSwitch:true,customImageLevels:[9,10],onlySolidDefault:true,noBackgroundRarity:true,rocketEdgeFlight:true,noRemoteAssets:true,errors};await writeFile(new URL('result.json',out),JSON.stringify(result,null,2));
 if(process.env.TB_UPDATE_BACKGROUND_THUMBNAILS==='1'){const assets=new URL('../src/assets/backgrounds/',import.meta.url);await mkdir(assets,{recursive:true});for(const {id}of results)await copyFile(new URL(id+'.jpg',out),new URL(id+'.jpg',assets));}console.log(JSON.stringify(result));
}catch(error){await page.screenshot({path:fileURLToPath(new URL('failure.png',out))});throw error;}finally{await browser.close();await server.close();}
