import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createServer} from 'vite';
import {chromium} from 'playwright';
import {solutionBlocks} from '../src/lib/practiceMetadata.js';

const front=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const repo=path.dirname(front),out=path.join(repo,'.backups','editorial-teaching-20261022','render');
fs.mkdirSync(out,{recursive:true});
const load=name=>JSON.parse(fs.readFileSync(path.join(repo,'data','library',name+'.json'),'utf8'));
const defaults=load('solutions'),details=load('detailed_solutions'),lectures=load('lectures').map(row=>row.content);
const target='remote:nowcoder:141877::C';
let articleCount=0,inlineCount=0;
for (const article of [...defaults,...details]) {
  const blocks=solutionBlocks(article.markdown,lectures);
  const lessons=blocks.filter(block=>block.type==='lecture');
  if(article.problem_id===target)assert.ok(lessons.length>=5,article.problem_id+' exposes its dedicated foundation lessons');
  assert.ok(article.markdown.trim(),article.problem_id+' has readable editorial content');
  assert.ok(blocks.some(block=>block.type==='markdown'&&block.markdown.includes('```cpp')),article.problem_id+' keeps its reference program outside disclosures');
  for (const block of lessons.filter(block=>block.markdown.includes('assets/foundations/')||block.markdown.includes('保存对象'))) {
    assert.ok(block.markdown.length>300,article.problem_id+' must contain the complete lesson');
  }
  articleCount++;inlineCount+=lessons.length;
}
const server=await createServer({root:front,server:{host:'127.0.0.1',port:0}});
await server.listen();
const port=server.httpServer.address().port;
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const errors=[];let screenshots=0;
try {
  for (const [variant,collection] of [['default',defaults],['detailed',details]]) {
    const solution=collection.find(row=>row.problem_id===target);
    for (const [width,dark,narrow] of [[1440,false,false],[1050,true,true],[390,false,false]]) {
      const page=await browser.newPage({viewport:{width,height:1000}});
      page.on('pageerror',error=>errors.push(error.message));
      await page.addInitScript(data=>{window.editorialTeaching=data;},{solution,lectures:lectures.filter(row=>row.conceptSource==='independent-foundation'),dark,narrow});
      await page.goto(`http://127.0.0.1:${port}/tests/editorial-teaching-fixture.html`);
      await page.locator('main h2').waitFor();
      const disclosures=page.locator('details');
      assert.ok(await disclosures.count()>=5);
      assert.equal(await page.locator('details[open]').count(),0,'Lessons begin collapsed');
      const coverage=page.locator('.reading-image-open').filter({has:page.locator('img[alt*="八个闭区间"]')});
      await coverage.scrollIntoViewIfNeeded();
      await page.waitForFunction(()=>[...document.querySelectorAll('.reading-image-open img')].some(img=>img.alt.includes('八个闭区间')&&img.complete&&img.naturalWidth>0));
      await coverage.screenshot({path:path.join(out,`${variant}-${width}-${dark?'dark':'light'}-intervals.png`)});screenshots++;
      await coverage.click();
      await page.getByRole('dialog').waitFor();
      await page.keyboard.press('Escape');
      assert.equal(await page.getByRole('dialog').count(),0,'The figure can be enlarged and closed');
      for (const name of ['lower_bound 与 upper_bound','lambda：定义']) {
        const disclosure=disclosures.filter({has:page.locator('summary',{hasText:name})});
        assert.equal(await disclosure.count(),1,name+' is uniquely matched');
        await disclosure.locator('summary').click();
        await disclosure.locator('.lecture-disclosure-body').waitFor();
        assert.ok((await disclosure.innerText()).length>1000,name+' has the complete guide');
        const image=disclosure.locator('.reading-image-open').first();
        await image.scrollIntoViewIfNeeded();
        await page.waitForFunction(()=>[...document.querySelectorAll('details[open] img')].every(img=>img.complete&&img.naturalWidth>0));
        await image.screenshot({path:path.join(out,`${variant}-${width}-${name.startsWith('lambda')?'lambda':'bounds'}.png`)});screenshots++;
        await disclosure.locator('summary').click();
      }
      assert.deepEqual(await page.locator('.katex-error,.reading-image-missing').evaluateAll(nodes=>nodes.map(n=>n.outerHTML)),[]);
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
      assert.equal(overflow,false,'The reading page fits '+width+' px');
      await page.close();
    }
  }
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({articleCount,inlineCount,screenshots,errors},null,2));
} finally {await browser.close();await server.close();}
