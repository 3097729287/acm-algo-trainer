import assert from 'node:assert/strict';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';

const catalog=JSON.parse(await readFile('../data/editorial-motions.json','utf8'));
const cases=await Promise.all(catalog.cases.map(async row=>({...row,source:'data:image/svg+xml;base64,'+Buffer.from(await readFile('../'+row.asset)).toString('base64')})));
const model=JSON.parse(await readFile('../.backups/editorial-motion-20261108/models.json','utf8'));
const output='../.backups/editorial-motion-20261108/ui';await mkdir(output,{recursive:true});
const server=await createServer({optimizeDeps:{entries:['tests/editorial-motion-fixture.html']},server:{host:'127.0.0.1',port:0}});await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1260,height:1000}}),errors=[],external=[];
page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url())&&!r.url().startsWith(base))external.push(r.url());});
await page.route('**/tests/editorial-motion-data.json',route=>route.fulfill({contentType:'application/json',body:JSON.stringify(cases)}));
const base=`http://127.0.0.1:${server.httpServer.address().port}`;
const go=(index,options='&static')=>page.goto(`${base}/tests/editorial-motion-fixture.html?case=${index}${options}`);
const root=()=>page.locator('.reading-motion');
async function loaded(){await page.waitForFunction(()=>{const image=document.querySelector('.reading-motion>.reading-image img');return image?.complete&&image.naturalWidth>0;});}
let visited=0;
try{
 for(let index=0;index<cases.length;index++){
  await go(index);await loaded();assert.equal(await root().count(),1);
  assert.equal(await page.evaluate(()=>motionFixture.parse(motionFixture.sample.source).steps.length),cases[index].steps);
  for(let step=0;step<cases[index].steps;step++){
   assert.equal(await root().getAttribute('data-step'),String(step));await loaded();
   assert.equal(await root().locator('>.reading-motion-caption').textContent(),model[index].steps[step].caption);
   if(step<cases[index].steps-1)await root().getByRole('button',{name:'下一步演示',exact:true}).click();
   visited++;
  }
  const escaped=await page.evaluate(()=>motionFixture.parse('data:image/svg+xml;base64,'+btoa('<svg xmlns="http://www.w3.org/2000/svg"><metadata id="tb-editorial-motion">{"version":1,"title":"x","steps":[{"image":"javascript:alert(1)","caption":"x"},{"image":"https://example.com","caption":"x"}]}</metadata></svg>')));
  assert.equal(escaped,null);
 }
 // Check the bounds of every authored frame using the actual Chinese font.
 const bounds=await page.evaluate(async models=>{
  await document.fonts.ready;const failures=[];const host=document.createElement('div');host.style.cssText='position:absolute;left:-10000px;top:0;visibility:hidden';document.body.append(host);
  for(const clip of models)for(let i=0;i<clip.steps.length;i++){
   const xml=new TextDecoder().decode(Uint8Array.from(atob(clip.steps[i].image.split(',')[1]),c=>c.charCodeAt(0))),doc=new DOMParser().parseFromString(xml,'image/svg+xml'),svg=document.importNode(doc.documentElement,true);host.replaceChildren(svg);
   const box=svg.viewBox.baseVal;
   for(const text of svg.querySelectorAll('text')){const b=text.getBBox();if(b.x<-.5||b.y<-.5||b.x+b.width>box.width+.5||b.y+b.height>box.height+.5)failures.push({id:clip.id,step:i,text:text.textContent,box:{x:b.x,y:b.y,width:b.width,height:b.height},view:{width:box.width,height:box.height}});}
  }
  host.remove();return failures;
 },model);
 await writeFile(output+'/bounds.json',JSON.stringify(bounds,null,2));assert.deepEqual(bounds,[],JSON.stringify(bounds.slice(0,8)));
 for(const id of ['window-deques','fleet-root-and-head','bracket-prefix-affine','grid-delete-closure','mex-threshold-assign'])for(const width of [1260,430])for(const theme of ['dark','light']){
  const index=cases.findIndex(row=>row.id===id);await page.setViewportSize({width,height:950});await go(index,`&static&theme=${theme}`);await loaded();
  await root().getByRole('slider',{name:'演示步骤'}).press('End');await loaded();
  assert((await page.evaluate(()=>document.documentElement.scrollWidth))<=width+1);
  await page.screenshot({path:`${output}/${id}-${width}-${theme}.png`});
  if(width===430&&theme==='dark'){
   await root().getByRole('button',{name:'演示回到开头'}).click();await root().getByRole('button',{name:/放大图片/}).click();
   const dialog=page.getByRole('dialog');await dialog.waitFor();await dialog.getByRole('button',{name:'下一步演示',exact:true}).click();
   assert.equal(await root().getAttribute('data-step'),'1');await page.keyboard.press('Escape');assert(await root().getByRole('button',{name:/放大图片/}).evaluate(n=>n===document.activeElement));
  }
 }
 await page.setViewportSize({width:1260,height:950});await go(0,'&below');await loaded();
 await page.waitForTimeout(2300);assert.equal(await root().getAttribute('data-step'),'0','Offscreen image must not start');
 await root().scrollIntoViewIfNeeded();await page.waitForFunction(()=>document.querySelector('.reading-motion').dataset.step==='1');
 await root().getByRole('button',{name:'暂停演示',exact:true}).click();const paused=await root().getAttribute('data-step');await page.waitForTimeout(2300);assert.equal(await root().getAttribute('data-step'),paused);
 await root().getByRole('button',{name:'播放演示',exact:true}).click();await page.evaluate(()=>{Object.defineProperty(document,'hidden',{get:()=>true,configurable:true});document.dispatchEvent(new Event('visibilitychange'));});
 await page.waitForTimeout(2300);assert.equal(await root().getAttribute('data-step'),paused,'Hidden window must pause');
 await page.evaluate(()=>{Object.defineProperty(document,'hidden',{get:()=>false,configurable:true});document.dispatchEvent(new Event('visibilitychange'));document.documentElement.dataset.motion='off';});await page.waitForTimeout(2300);
 assert.equal(await root().getAttribute('data-step'),paused);assert(await root().getByRole('button',{name:'播放演示',exact:true}).isDisabled());
 await root().getByRole('button',{name:'下一步演示',exact:true}).click();assert.equal(await root().getAttribute('data-step'),String(Number(paused)+1));
 const short=cases.findIndex(row=>row.id==='stable-letter-swaps');
 await page.emulateMedia({reducedMotion:'reduce'});await go(short,'');await loaded();await page.waitForTimeout(2300);assert.equal(await root().getAttribute('data-step'),'0');assert(await root().getByRole('button',{name:'播放演示',exact:true}).isDisabled());await root().getByRole('button',{name:'下一步演示',exact:true}).click();assert.equal(await root().getAttribute('data-step'),'1');
 await page.route('**/standalone-motion.svg',route=>route.fulfill({contentType:'image/svg+xml',body:Buffer.from(cases[short].source.split(',')[1],'base64')}));
 await page.goto(base+'/standalone-motion.svg');await page.evaluate(()=>document.fonts.ready);const still=await page.locator('svg').screenshot();await page.waitForTimeout(2500);assert.equal(Buffer.compare(still,await page.locator('svg').screenshot()),0,'Standalone SVG document respects OS reduced motion');
 await page.emulateMedia({reducedMotion:'no-preference'});await go(short,'');await loaded();await page.waitForFunction(()=>document.querySelector('.reading-motion').dataset.playing==='false'&&document.querySelector('.reading-motion').dataset.step==='3',{},{timeout:14000});
 await root().getByRole('button',{name:'重播演示',exact:true}).click();assert.equal(await root().getAttribute('data-step'),'0');
 await go(short,'&raw');await page.locator('#standalone').waitFor();const before=await page.locator('#standalone').screenshot();await page.waitForTimeout(2500);const after=await page.locator('#standalone').screenshot();assert.notEqual(Buffer.compare(before,after),0,'Exported SVG must actually animate');
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 const report={ok:true,cases:cases.length,framesViewed:visited,frameBounds:true,visualScenarios:20,zoomControls:true,pause:true,stepAndReplay:true,offscreen:true,hidden:true,reducedMotion:true,osReducedMotion:true,standaloneAnimation:true,errors,external};
 await writeFile(output+'/checks.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}finally{await browser.close();await server.close();}
