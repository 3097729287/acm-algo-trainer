import assert from 'node:assert/strict';
import path from 'node:path';
import fs from 'node:fs';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {chromium} from 'playwright';

const frontend=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const directory=path.resolve(process.argv[2]);
const output=path.join(frontend,'../.backups/editorial-teaching-20261022/render');
fs.mkdirSync(output,{recursive:true});
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
let checks=0;
try{
  for(const variant of ['默认题解','详细题解']){
    const file=path.join(directory,'小月的长廊-'+variant+'.html');
    assert.ok(fs.existsSync(file));
    const context=await browser.newContext({viewport:{width:390,height:900},offline:true});
    const page=await context.newPage(),network=[],errors=[];
    page.on('request',request=>{if(/^https?:/.test(request.url()))network.push(request.url())});
    page.on('pageerror',error=>errors.push(error.message));
    await page.goto(pathToFileURL(file).href);
    await page.locator('h2').first().waitFor();
    assert.equal(await page.locator('details[open]').count(),0);
    assert.ok(await page.locator('.katex').count()>8);
    await page.locator('summary').filter({hasText:'lower_bound 与 upper_bound'}).click();
    assert.ok((await page.locator('details[open]').innerText()).includes('底层怎样二分'));
    await page.evaluate(()=>document.querySelectorAll('details').forEach(node=>{node.open=true}));
    await page.evaluate(async()=>{
      for(const img of document.images)img.loading='eager';
      await Promise.race([
        Promise.all([...document.images].map(img=>img.decode())),
        new Promise((_,reject)=>setTimeout(()=>reject(new Error('Offline figures did not finish decoding')),10000)),
      ]);
    });
    assert.equal(await page.locator('.katex-error').count(),0);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
    assert.deepEqual(network,[]);assert.deepEqual(errors,[]);
    const figure=page.locator('img[alt*="八个闭区间"]');
    await figure.screenshot({path:path.join(output,'offline-'+variant+'-390.png')});
    checks++;await context.close();
  }
  console.log(JSON.stringify({offlineFiles:checks,httpRequests:0,mathErrors:0,imagesDecoded:true},null,2));
}finally{await browser.close()}
