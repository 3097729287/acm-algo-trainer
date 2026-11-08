// Explicit public-original fixtures through the real Workbench; no accounts.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {createServer} from 'vite';
import {chromium} from 'playwright';

if(!process.argv[2]||!process.argv[3])throw new Error('Supply public fixtures and an isolated review result path');
const rows=JSON.parse(await fs.readFile(process.argv[2],'utf8'));
const output=path.resolve(process.argv[3]);await fs.mkdir(path.dirname(output),{recursive:true});
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const port=18826;
const server=await createServer({root,cacheDir:path.join(path.dirname(output),'vite-review'),optimizeDeps:{entries:['tests/statement-pdf-fixture.html']},server:{host:'127.0.0.1',port,strictPort:true,hmr:false}});
await server.listen();let browser;const checked=[],errors=[],external=[];
try{
 browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
 const context=await browser.newContext({viewport:{width:1440,height:900}});
 await context.route('**/*',route=>{
  const url=new URL(route.request().url());
  if(url.origin===`http://127.0.0.1:${port}`||['blob:','data:'].includes(url.protocol))return route.continue();
  external.push(url.href);return route.abort();
 });
 for(const row of rows){
  const page=await context.newPage();page.on('pageerror',error=>errors.push(error.message));
  await page.addInitScript(value=>window.pdfFixtureData=value,row);
  await page.goto(`http://127.0.0.1:${port}/tests/statement-pdf-fixture.html`);
  await page.locator('.wb-code-pane').waitFor();
  let pages=0,images=0;
  if(row.statementPdf){
   const pdf=page.locator('.wb-statement-pdf');await pdf.waitFor();
   await pdf.locator('.wb-pdf-page[data-ready="true"]').first().waitFor();
   assert.equal(await pdf.locator('.wb-pdf-page').count(),row.statementPdf.pageCount,row.originalId);
   for(const item of await pdf.locator('.wb-pdf-page').all()){
    await item.scrollIntoViewIfNeeded();await page.waitForFunction(element=>element.dataset.ready==='true',await item.elementHandle());
    assert((await item.locator('.wb-pdf-text-layer').textContent()).trim().length>0,row.originalId+' every PDF page has text');pages++;
   }
   const bytes=await pdf.getByRole('link',{name:'下载 PDF',exact:true}).evaluate(async node=>Array.from(new Uint8Array(await(await fetch(node.href)).arrayBuffer())));
   assert.equal(createHash('sha256').update(Buffer.from(bytes)).digest('hex'),row.statementPdf.sha256,row.originalId+' original byte identity');
  }else{
   const statement=page.locator('.wb-statement');await statement.waitFor();
   assert.equal(await statement.locator('.katex-error').count(),0,row.originalId+' formula');
   const blocks=await statement.locator('pre').allTextContents();
   for(const sample of row.samples){
    assert(blocks.some(value=>value.trimEnd()===sample.input.trimEnd()),row.originalId+' sample input');
    assert(blocks.some(value=>value.trimEnd()===sample.output.trimEnd()),row.originalId+' sample output');
   }
   for(const picture of await statement.locator('img[src]:not([src=""])').all()){
    await picture.scrollIntoViewIfNeeded();await picture.evaluate(image=>image.decode());
    assert(await picture.evaluate(image=>image.complete&&image.naturalWidth>0),row.originalId+' original image');images++;
   }
  }
  await page.screenshot({path:path.join(path.dirname(output),row.originalId.replaceAll(':','_')+'.png')});
  checked.push({id:row.originalId,pages,images,samples:row.samples.length});await page.close();
 }
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 const result={checked,browserErrors:0,formulaErrors:0,externalRequests:0,samplesPreserved:true,allPdfPagesRendered:true,originalPdfByteIdentity:true};
 await fs.writeFile(output,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
}finally{await browser?.close();await server.close();}
