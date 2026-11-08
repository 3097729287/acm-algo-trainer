import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const payload=await readFile('../.backups/editorial-playback-20261108/content/reader-cases.json','utf8'),cases=JSON.parse(payload);
const server=await createServer({optimizeDeps:{entries:['tests/editorial-motion-fixture.html']},server:{host:'127.0.0.1',port:0}});await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1050,height:950}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.route('**/tests/editorial-motion-articles.json',route=>route.fulfill({contentType:'application/json',body:payload}));let checked=0;
try{
 for(let i=0;i<cases.length;i++){
  await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/tests/editorial-motion-fixture.html?article&static&case=${i}`);
  for(const detailed of [false,true]){
   if(detailed)await page.getByRole('button',{name:'切换为详细题解',exact:true}).click();
   const root=page.locator('.reading-motion');assert.equal(await root.count(),1,cases[i].id);await root.scrollIntoViewIfNeeded();
   await page.waitForFunction(()=>{const image=document.querySelector('.reading-motion img');return document.querySelector('.reading-motion svg.reading-motion-scene')||image?.complete&&image.naturalWidth>0;});
   await root.getByRole('button',{name:'下一步演示',exact:true}).click();assert.equal(await root.getAttribute('data-step'),'1');
   assert.equal(await page.getByRole('status').filter({hasText:'图片未能加载'}).count(),0);
   assert(await page.locator('.editorial-code').count()>0,'Reference still exists');checked++;
  }
 }
 assert.deepEqual(errors,[]);const report={ok:true,problemCases:cases.length,defaultAndDetailed:checked,figuresReachableThroughReader:true,referencesPreserved:true,errors};
 await writeFile('../.backups/editorial-playback-20261108/ui/articles.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}finally{await browser.close();await server.close();}
