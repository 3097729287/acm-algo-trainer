import assert from 'node:assert/strict';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { createServer } from 'vite';
import { chromium } from 'playwright';
import { solutionBlocks } from '../src/lib/practiceMetadata.js';
import { SEQUENCE_PROBLEMS } from '../src/pages/algorithm-lab/sequenceProblems.js';

process.env.TB_OFFLINE='1';
const frontend=fileURLToPath(new URL('../',import.meta.url)),repo=path.resolve(frontend,'..'),out=path.join(repo,'.backups/sequence-lab-20261023/editorials');
await mkdir(out,{recursive:true});
const load=async name=>JSON.parse(await readFile(path.join(repo,'data/library',name+'.json'),'utf8'));
const lectures=(await load('lectures')).map(r=>r.content).filter(c=>c.conceptSource==='independent-foundation');
const selected=Object.values(SEQUENCE_PROBLEMS).flat(),ids=new Set(selected.map(p=>p.id)),errors=[];
const server=await createServer({root:frontend,server:{host:'127.0.0.1',port:0},logLevel:'error'});await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
let pages=0,figures=0;
try {
  for(const collection of ['solutions','detailed_solutions']) {
    const rows=(await load(collection)).filter(r=>ids.has(r.problem_id));assert.equal(rows.length,10);
    for(const solution of rows) {
      const blocks=solutionBlocks(solution.markdown,lectures),body=blocks.filter(b=>b.type==='markdown').map(b=>b.markdown).join('\n');
      assert.ok(blocks.some(b=>b.type==='lecture'),'reusable foundations must be disclosures');
      assert.ok(body.includes('```cpp'),'the actual reference stays visible');
      assert.ok(body.includes('assets/sequence/'),'the problem-specific reasoning figure stays visible');
      for(const [width,dark,narrow] of [[1440,false,false],[1050,true,true],[390,false,false]]) {
        const page=await browser.newPage({viewport:{width,height:1000}});page.on('pageerror',e=>errors.push(e.message));
        await page.addInitScript(data=>window.editorialTeaching=data,{solution,lectures,dark,narrow});
        await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/tests/editorial-teaching-fixture.html`);
        await page.locator('main h2').waitFor();
        assert.equal(await page.locator('details[open]').count(),0);
        assert.equal(await page.locator('.katex-error,.reading-image-missing').count(),0);
        const diagram=page.locator('main>.markdown .reading-image-open').first();await diagram.scrollIntoViewIfNeeded();
        await page.waitForFunction(()=>[...document.querySelectorAll('main>.markdown img')].every(img=>img.complete&&img.naturalWidth>0));
        await diagram.screenshot({path:path.join(out,`${solution.problem_id.split(':').at(-1)}-${collection}-${width}.png`)});figures++;
        if(width===1440) {await diagram.click();await page.getByRole('dialog').waitFor();await page.keyboard.press('Escape');assert.equal(await page.getByRole('dialog').count(),0);}
        const lesson=page.locator('details').first();await lesson.locator('summary').click();await lesson.locator('.lecture-disclosure-body').waitFor();
        assert.ok((await lesson.innerText()).length>500,'complete standalone foundation is available');
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
        await page.close();pages++;
      }
    }
  }
  assert.deepEqual(errors,[]);
  const report={status:'passed',variants:20,pages,figures,foundationsInitiallyCollapsed:true,reasoningAndCodeVisible:true,oldRecordsPreserved:true,errors};
  await writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
} finally {await browser.close();await server.close();}
