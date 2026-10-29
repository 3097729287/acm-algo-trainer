import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createServer} from 'vite';
import {chromium} from 'playwright';
import {createHash} from 'node:crypto';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const out=path.join(root,'.backups/core7-editorials-20261030/render');
fs.mkdirSync(out,{recursive:true});
const authored=JSON.parse(fs.readFileSync(path.join(root,'.backups/core7-editorials-20261030/authored.json'),'utf8'));
const lectures=JSON.parse(fs.readFileSync(path.join(root,'data/library/lectures.json'),'utf8')).map(r=>r.content);
const server=await createServer({root:path.join(root,'frontend'),server:{host:'127.0.0.1',port:0}});
await server.listen();
const browser=await chromium.launch({channel:'msedge',headless:true});
const frames=[],errors=[];
const previous=process.argv.includes('--only-changed')&&fs.existsSync(path.join(out,'report.json'))
  ?JSON.parse(fs.readFileSync(path.join(out,'report.json'),'utf8')).frames:[];
try {
  for(const [width,dark] of [[1440,false],[1050,true],[390,false]]) {
    for(const entry of authored) for(const [variant,solution] of Object.entries(entry.variants)) {
      const digest=createHash('sha256').update(solution.markdown).digest('hex');
      const imagesDigest=createHash('sha256').update(JSON.stringify(solution.images)).digest('hex');
      const expectedFigures=Object.keys(solution.images).filter(name=>name.startsWith('assets/core7/')).length;
      const old=previous.find(f=>f.pid===entry.pid&&f.method===entry.method&&f.variant===variant&&f.width===width&&f.dark===dark&&f.markdownSha256===digest&&f.imagesSha256===imagesDigest);
      if(old&&old.captures.every(name=>fs.existsSync(path.join(out,name)))){frames.push(old);continue;}
      const page=await browser.newPage({viewport:{width,height:1000}});
      page.on('pageerror',e=>errors.push(e.message));
      await page.addInitScript(fixture=>{window.editorialTeaching=fixture;},{solution,lectures,dark,narrow:false});
      await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/tests/editorial-teaching-fixture.html`);
      await page.locator('main h2').waitFor();
      assert.equal(await page.locator('details[open]').count(),0);
      assert.ok(await page.locator('details').count()>0);
      assert.equal(await page.locator('.katex-error,.reading-image-missing').count(),0,entry.pid);
      await page.waitForFunction(()=>[...document.querySelectorAll('main img')].every(img=>img.complete&&img.naturalWidth>0));
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,entry.pid+' overflow '+width);
      const key=`${entry.pid}-${entry.method}-${variant}-${width}`;
      const images=page.locator('main .reading-image-open');
      assert.ok(await images.count()>=expectedFigures,entry.pid+' did not render its problem diagram');
      const captures=[];
      for(let i=0;i<await images.count();i++) {
        const img=images.nth(i);await img.scrollIntoViewIfNeeded();
        const target=key+`-figure-${i}.png`;
        await img.screenshot({path:path.join(out,target)});captures.push(target);
      }
      // Also exercise the complete inline lesson, using the actual reader.
      const disclosure=page.locator('details').first();
      await disclosure.locator('summary').click();
      await disclosure.locator('.lecture-disclosure-body').waitFor();
      assert.ok((await disclosure.innerText()).length>120);
      await disclosure.locator('summary').click();
      await page.screenshot({path:path.join(out,key+'.png'),fullPage:true});
      frames.push({pid:entry.pid,method:entry.method,variant,width,dark,markdownSha256:digest,imagesSha256:imagesDigest,captures:[key+'.png',...captures]});
      await page.close();
      if(frames.length%24===0)console.log(JSON.stringify({rendered:frames.length,total:authored.length*6}));
    }
  }
  assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({frames,errors},null,2)+'\n');
  console.log(JSON.stringify({frames:frames.length,errors}));
} finally {await browser.close();await server.close();}
