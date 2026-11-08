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
const port=Number(process.env.TB_REVIEW_PORT||18826);
assert(Number.isInteger(port)&&port>=1024&&port<=65535,'Valid isolated review port');
const normalizedLines=value=>value.replace(/\r\n?/g,'\n').trimEnd();
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
  const examples=page.locator('.wb-sample-list > details');
  await page.waitForFunction(expected=>document.querySelectorAll('.wb-sample-list > details').length===expected,row.samples.length);
  for(let i=0;i<row.samples.length;i++){
   const blocks=await examples.nth(i).locator('pre').allTextContents();
   assert.equal(normalizedLines(blocks[0]),normalizedLines(row.samples[i].input||'（空输入）'),row.originalId+' console input');
   assert.equal(normalizedLines(blocks[1]),normalizedLines(row.samples[i].output||'（空输出）'),row.originalId+' console output');
  }
  let pages=0,images=0,attachments=0;
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
    assert(blocks.some(value=>normalizedLines(value)===normalizedLines(sample.input)),row.originalId+' sample input');
    assert(blocks.some(value=>normalizedLines(value)===normalizedLines(sample.output)),row.originalId+' sample output');
   }
   for(const picture of await statement.locator('img[src]:not([src=""])').all()){
    await picture.scrollIntoViewIfNeeded();await picture.evaluate(image=>image.decode());
    assert(await picture.evaluate(image=>image.complete&&image.naturalWidth>0),row.originalId+' original image');images++;
    await picture.screenshot({path:path.join(path.dirname(output),row.originalId.replaceAll(':','_')+'-image-'+images+'.png')});
   }
   for(const anchor of await statement.locator('a[download]').all()){
    const href=await anchor.getAttribute('href'),variants=[href];
    try{variants.push(decodeURI(href),decodeURIComponent(href));}catch{/* Keep original spelling. */}
    const key=variants.find(value=>Object.hasOwn(row.attachments||{},value));
    assert(key,row.originalId+' known original attachment');
    const original=row.attachments[key],expected=Buffer.from(original.data.split(',',2)[1],'base64');
    const promised=page.waitForEvent('download');await anchor.scrollIntoViewIfNeeded();await anchor.click();
    const download=await promised,stream=await download.createReadStream(),chunks=[];
    if(original.fileName)assert.equal(download.suggestedFilename(),original.fileName,row.originalId+' original attachment filename');
    for await(const chunk of stream)chunks.push(chunk);
    assert.equal(createHash('sha256').update(Buffer.concat(chunks)).digest('hex'),createHash('sha256').update(expected).digest('hex'),row.originalId+' original attachment byte identity');
    assert.equal(await download.failure(),null,row.originalId+' original download');attachments++;
   }
  }
  let bilingualVerified=false;
  if(row.reviewBilingual){
   const toggle=page.locator('.wb-language-toggle button');await toggle.waitFor();
   if(await toggle.getAttribute('aria-label')==='中文')await toggle.click();
   await page.getByRole('button',{name:'原文',exact:true}).waitFor();
   const statement=page.locator('.wb-statement');assert((await statement.textContent()).includes(row.reviewEnglishFragment),row.originalId+' original English text');
   await page.screenshot({path:path.join(path.dirname(output),row.originalId.replaceAll(':','_')+'-original.png')});
   await toggle.click();await page.getByRole('button',{name:'中文',exact:true}).waitFor();
   assert((await statement.textContent()).includes(row.reviewChineseFragment),row.originalId+' reviewed Chinese text');
   assert.equal(await statement.locator('.katex-error').count(),0,row.originalId+' Chinese formula');
   assert.equal(await page.locator('.wb-translation-error').count(),0,row.originalId+' language switch');
   for(const picture of await statement.locator('img').all())await picture.evaluate(image=>image.decode());
   bilingualVerified=true;
  }
  await page.screenshot({path:path.join(path.dirname(output),row.originalId.replaceAll(':','_')+'.png')});
  checked.push({id:row.originalId,pages,images,attachments,samples:row.samples.length,bilingualVerified});await page.close();
 }
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 const result={checked,browserErrors:0,formulaErrors:0,externalRequests:0,samplesPreserved:true,allPdfPagesRendered:true,originalPdfByteIdentity:true,originalAttachmentByteIdentity:true};
 await fs.writeFile(output,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
}finally{await browser?.close();await server.close();}
