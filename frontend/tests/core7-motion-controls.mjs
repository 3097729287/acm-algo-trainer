import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..'),out=path.join(root,'.backups/core7-complete-20261108/reader-review');
const browser=await chromium.launch({channel:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1100,height:850}});
await page.goto('http://127.0.0.1:5278/tests/core7-completion-fixture.html');await page.waitForFunction(()=>window.reviewEntry);
const entries=fs.readdirSync(path.join(root,'data/core7-completion')).filter(name=>fs.existsSync(path.join(root,'data/core7-completion',name,'entry.json'))).map(pid=>({pid,...JSON.parse(fs.readFileSync(path.join(root,'data/core7-completion',pid,'entry.json'),'utf8'))})).filter(e=>Object.keys(e.images).length);
const clips=entries.flatMap(e=>Object.values(e.images));
const clipped=await page.evaluate(sources=>{
 const errors=[];
 for(const source of sources){
  const raw=new TextDecoder().decode(Uint8Array.from(atob(source.split(',')[1]),c=>c.charCodeAt(0))),documentSvg=new DOMParser().parseFromString(raw,'image/svg+xml');
  const model=JSON.parse(documentSvg.querySelector('metadata').textContent);
  for(let i=0;i<model.steps.length;i++){
   const frame=new TextDecoder().decode(Uint8Array.from(atob(model.steps[i].image.split(',')[1]),c=>c.charCodeAt(0))),host=document.createElement('div');host.style.cssText='position:fixed;left:-10000px;top:0';host.innerHTML=frame;document.body.append(host);
   for(const text of host.querySelectorAll('text')){const r=text.getBBox();if(r.x<0||r.y<0||r.x+r.width>760.5||r.y+r.height>310.5)errors.push({title:model.title,step:i,text:text.textContent,box:{x:r.x,y:r.y,w:r.width,h:r.height}});}
   host.remove();
  }
 }
 return errors;
},clips);assert.deepEqual(clipped,[]);
const entry=entries.find(e=>e.pid==='CF1909I');await page.evaluate(e=>window.reviewEntry({pid:e.pid,edition:'controls',markdown:e.variants.detailed,images:e.images}),entry);
const motion=page.locator('.reading-motion');await motion.scrollIntoViewIfNeeded();await page.waitForFunction(()=>document.querySelector('.reading-motion')?.dataset.playing==='true');
await motion.getByRole('button',{name:'暂停演示',exact:true}).click();const paused=await motion.getAttribute('data-step');await page.waitForTimeout(4300);assert.equal(await motion.getAttribute('data-step'),paused);
await motion.getByRole('button',{name:'下一步演示',exact:true}).click();assert.equal(Number(await motion.getAttribute('data-step')),Number(paused)+1);
await motion.getByRole('button',{name:'演示回到开头',exact:true}).click();assert.equal(await motion.getAttribute('data-step'),'0');
await motion.locator('.reading-image-open').click();const dialog=page.locator('.reading-image-dialog');await dialog.waitFor();await dialog.locator('input[type=range]').fill('2');assert.equal(await motion.getAttribute('data-step'),'2');await page.screenshot({path:path.join(out,'motion-zoom-controls.png')});await page.keyboard.press('Escape');
await page.evaluate(()=>document.documentElement.dataset.motion='off');await page.waitForFunction(()=>document.querySelector('.reading-motion-controls button').disabled);
const report={portableModels:clips.length,textClippingErrors:clipped.length,pause:true,step:true,reset:true,zoomStep:true,applicationReducedMotion:true};fs.writeFileSync(path.join(out,'controls.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));await browser.close();
