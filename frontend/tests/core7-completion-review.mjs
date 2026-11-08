import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const out=path.join(root,'.backups/core7-complete-20261108/reader-review');fs.mkdirSync(out,{recursive:true});
const selection=process.argv[2]?.split(',');
const folders=fs.readdirSync(path.join(root,'data/core7-completion')).filter(name=>(!selection||selection.includes(name))&&fs.existsSync(path.join(root,'data/core7-completion',name,'entry.json')));
const browser=await chromium.launch({channel:'msedge',headless:true});
const context=await browser.newContext({viewport:{width:1440,height:1100},reducedMotion:'reduce'}),page=await context.newPage(),errors=[];
page.on('pageerror',e=>errors.push(e.message));
await page.goto('http://127.0.0.1:5278/tests/core7-completion-fixture.html');
await page.waitForFunction(()=>typeof window.reviewEntry==='function');
let editions=0,steps=0;const motionNames=[];
for(const pid of folders){
 const entry=JSON.parse(fs.readFileSync(path.join(root,'data/core7-completion',pid,'entry.json'),'utf8'));
 const code=fs.readFileSync(path.join(root,'data/core7-completion',pid,'main.cpp'),'utf8').replaceAll('\r\n','\n').trim();
 for(const [edition,markdown]of Object.entries(entry.variants)){
  await page.evaluate(value=>window.reviewEntry(value),{pid,edition,markdown,images:entry.images});
  await page.waitForFunction(value=>document.querySelector('.markdown h2')?.textContent.includes(value),pid);
  const reference=page.locator('.editorial-code code.language-cpp');await reference.waitFor();
  const rendered=await reference.textContent();assert.equal(rendered.trim(),code,pid+' '+edition);
  assert.ok(await reference.locator('span').count(),pid+' syntax colors');
  await reference.locator('../..').locator('.copy-code').evaluate(button=>button.click());
  assert.equal((await page.evaluate(()=>window.copiedCode)).trim(),code,pid+' copy');
  assert.equal(await page.locator('.katex-error').count(),0,pid+' math parse');
  assert.equal(await page.locator('.reading-image-missing').count(),0,pid+' image source');
  editions++;
 }
 if(Object.keys(entry.images).length){
  motionNames.push(pid);const motions=page.locator('.reading-motion');assert.equal(await motions.count(),Object.keys(entry.images).length,pid+' motion metadata');
  for(let i=0;i<await motions.count();i++){
   const motion=motions.nth(i),range=motion.locator('input[type=range]');const maximum=Number(await range.getAttribute('max'));
   for(let step=0;step<=maximum;step++){
    await range.fill(String(step));await motion.scrollIntoViewIfNeeded();
    assert.equal(await motion.getAttribute('data-step'),String(step));
    const image=motion.locator('img').first();await image.evaluate(image=>image.decode());
    const bounds=await image.boundingBox();assert.ok(bounds.width>200&&bounds.height>80,pid+' frame size');
    await image.screenshot({path:path.join(out,`${pid}-${step}.png`)});steps++;
   }
  }
 }
}
await page.setViewportSize({width:390,height:900});
for(const pid of motionNames){
 const entry=JSON.parse(fs.readFileSync(path.join(root,'data/core7-completion',pid,'entry.json'),'utf8'));
 await page.evaluate(value=>window.reviewEntry(value),{pid,edition:'narrow',markdown:entry.variants.detailed,images:entry.images});
 await page.waitForFunction(value=>document.querySelector('.markdown h2')?.textContent.includes(value),pid);
 const motion=page.locator('.reading-motion').first();await motion.scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,pid+'-narrow.png')});
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+2),true,pid+' narrow page overflow');
}
assert.deepEqual(errors,[]);
fs.writeFileSync(path.join(out,selection?'selected-report.json':'report.json'),JSON.stringify({editions,motionArticles:motionNames.length,steps,errors},null,2));
console.log(JSON.stringify({editions,motionArticles:motionNames.length,steps,errors}));await browser.close();
