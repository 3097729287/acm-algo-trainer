import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
import {realpathSync} from 'node:fs';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const server=await createServer({server:{host:'127.0.0.1',port:0,fs:{allow:[process.cwd(),realpathSync('node_modules')]}}});await server.listen();
const browser=await chromium.launch({channel:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1280,height:800}}),errors=[];
const output='../.backups/local-1415/ui';await mkdir(output,{recursive:true});page.on('pageerror',error=>errors.push(error.message));
await page.route(url=>url.pathname.startsWith('/api/'),route=>route.fulfill({contentType:'application/json',body:JSON.stringify(route.request().url().includes('/account')?{required:true,authenticated:false}:{status:'idle',currentVersion:'1.4.15'})}));
try {
 for(const theme of ['dark','light'])for(const view of ['brand','startup','login']){
  await page.goto(server.resolvedUrls.local[0]+'tests/release-1413-fixture.html?view='+view);await page.locator('.brand-wordmark').waitFor();
  await page.evaluate(theme=>document.documentElement.dataset.theme=theme,theme);
  const result=await page.locator('.brand-wordmark').evaluate(word=>{
   const to=word.querySelector('.brand-to'),be=word.querySelector('.brand-be'),a=getComputedStyle(to),b=getComputedStyle(be),x=to.getBoundingClientRect(),y=be.getBoundingClientRect(),w=word.getBoundingClientRect(),box=word.parentElement.getBoundingClientRect();
   return {to:a.color,be:b.color,toSize:a.fontSize,beSize:b.fontSize,toFont:a.fontFamily,beFont:b.fontFamily,toWeight:a.fontWeight,beWeight:b.fontWeight,gap:y.left-x.right,baseline:y.bottom-x.bottom,centerX:w.x+w.width/2-box.x-box.width/2,centerY:w.y+w.height/2-box.y-box.height/2,text:word.textContent,wordWidth:w.width,boxWidth:box.width};
  });
  assert.equal(result.text,'ToBe');assert.equal(result.to,'rgb(155, 138, 251)');assert.equal(result.be,'rgb(239, 237, 248)');
  assert.equal(result.toSize,result.beSize);assert.equal(result.toFont,result.beFont);assert.equal(result.toWeight,result.beWeight);
  assert(Math.abs(result.gap)<1&&Math.abs(result.baseline)<1,JSON.stringify(result));assert(Math.abs(result.centerX)<1&&Math.abs(result.centerY)<1,JSON.stringify(result));assert(result.wordWidth<result.boxWidth-2);
  await page.locator('.brand-wordmark').locator('..').screenshot({path:`${output}/${view}-${theme}.png`});
 }
 await page.goto(server.resolvedUrls.local[0]+'tobe.svg');await page.screenshot({path:output+'/svg.png'});
 assert.deepEqual(errors,[]);console.log('PASS horizontal two-color ToBe marks: equal font, shared baseline and centered in sidebar, startup and login under both themes');
} finally {await browser.close();await server.close();}
