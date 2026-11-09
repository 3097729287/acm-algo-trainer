// Page-reviewed public contest documents through the real Workbench, with no account.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {createServer} from 'vite';
import {chromium} from 'playwright';

if(!process.argv[2]||!process.argv[3])throw new Error('Supply reviewed public fixtures and an isolated receipt path');
const rows=JSON.parse(await fs.readFile(process.argv[2],'utf8'));
const output=path.resolve(process.argv[3]);await fs.mkdir(path.dirname(output),{recursive:true});
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const port=Number(process.env.TB_REVIEW_PORT||18835);
assert(Number.isInteger(port)&&port>=1024&&port<=65535);
const lines=value=>value.replace(/\r\n?/g,'\n').trimEnd();
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const server=await createServer({root,cacheDir:path.join(path.dirname(output),'vite-review'),optimizeDeps:{entries:['tests/statement-pdf-fixture.html']},server:{host:'127.0.0.1',port,strictPort:true,hmr:false}});
await server.listen();let browser;const checked=[],errors=[],external=[];
try{
 browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
 const context=await browser.newContext({viewport:{width:1440,height:950},acceptDownloads:true});
 await context.route('**/*',route=>{
  const url=new URL(route.request().url());
  if(url.origin===`http://127.0.0.1:${port}`||['data:','blob:'].includes(url.protocol))return route.continue();
  external.push(url.href);return route.abort();
 });
 for(const row of rows){
  const page=await context.newPage();page.on('pageerror',error=>errors.push(error.message));
  await page.addInitScript(value=>window.pdfFixtureData=value,row);
  await page.goto(`http://127.0.0.1:${port}/tests/statement-pdf-fixture.html`);
  await page.locator('.wb-code-pane').waitFor();
  const samples=page.locator('.wb-sample-list > details');
  await page.waitForFunction(count=>document.querySelectorAll('.wb-sample-list > details').length===count,row.samples.length);
  for(let i=0;i<row.samples.length;i++){
   const blocks=await samples.nth(i).locator('pre').allTextContents();
   assert.equal(lines(blocks[0]),lines(row.samples[i].input),row.originalId+' console input');
   assert.equal(lines(blocks[1]),lines(row.samples[i].output),row.originalId+' console output');
  }
  const viewer=page.locator('.wb-statement-pdf');await viewer.waitFor();
  await viewer.locator('.wb-pdf-page[data-ready="true"]').first().waitFor();
  assert.equal(await viewer.locator('.wb-pdf-page').count(),row.statementPdf.pageCount,row.originalId+' complete page inventory');
  let pages=0;
  for(const item of await viewer.locator('.wb-pdf-page').all()){
   await item.scrollIntoViewIfNeeded();
   await page.waitForFunction(element=>element.dataset.ready==='true',await item.elementHandle());
   assert((await item.locator('.wb-pdf-text-layer').textContent()).trim(),row.originalId+' selectable original text');pages++;
  }
  const originalBytes=await viewer.getByRole('link',{name:'下载 PDF',exact:true}).evaluate(async node=>Array.from(new Uint8Array(await(await fetch(node.href)).arrayBuffer())));
  assert.equal(sha(Buffer.from(originalBytes)),row.statementPdf.sha256,row.originalId+' exact selected original pages');
  await page.getByRole('button',{name:'原文',exact:true}).click();
  await page.getByRole('button',{name:'中文',exact:true}).waitFor();
  assert.equal(await viewer.count(),0,row.originalId+' Chinese text replaces native PDF');
  const statement=page.locator('.wb-statement');
  assert((await statement.textContent()).includes(row.reviewChineseFragment),row.originalId+' full Chinese prose');
  assert.equal(await statement.locator('.katex-error').count(),0,row.originalId+' Chinese formulas');
  assert.equal(await page.locator('.wb-translation-error').count(),0,row.originalId+' prepared translation');
  const blocks=await statement.locator('pre').allTextContents();
  for(const sample of row.samples){
   assert(blocks.some(value=>lines(value)===lines(sample.input)),row.originalId+' Chinese sample input');
   assert(blocks.some(value=>lines(value)===lines(sample.output)),row.originalId+' Chinese sample output');
  }
  const pictures=statement.locator('img');assert.equal(await pictures.count(),row.reviewImageCount,row.originalId+' all original diagrams');
  for(const picture of await pictures.all()){
   await picture.scrollIntoViewIfNeeded();await picture.evaluate(image=>image.decode());
   assert(await picture.evaluate(image=>image.complete&&image.naturalWidth>0),row.originalId+' offline original image');
  }
  const attachments=statement.locator('a[download]');assert.equal(await attachments.count(),1,row.originalId+' original complete contest download');
  const bookletUrl=row.sourcePdfUrl||row.statementPdf.sourceUrl;
  const bookletSha=row.sourcePdfSha256||row.statementPdf.sourceSha256;
  const anchor=attachments.first(),original=row.attachments[bookletUrl];
  assert(original&&/^[a-f0-9]{64}$/.test(bookletSha),row.originalId+' exact complete-booklet source descriptor');
  const pending=page.waitForEvent('download');await anchor.scrollIntoViewIfNeeded();await anchor.click();
  const download=await pending;assert.equal(download.suggestedFilename(),original.fileName,row.originalId+' original filename');
  const stream=await download.createReadStream(),chunks=[];for await(const chunk of stream)chunks.push(chunk);
  assert.equal(sha(Buffer.concat(chunks)),bookletSha,row.originalId+' complete original booklet exact bytes');
  assert.equal(await download.failure(),null);
  if(['C','F','G'].includes(row.originalId.split('::').at(-1))){
   await statement.evaluate(element=>element.scrollTop=0);
   await page.screenshot({path:path.join(path.dirname(output),row.originalId.replaceAll(':','_')+'-Chinese.png')});
  }
  await page.getByRole('button',{name:'中文',exact:true}).click();
  await page.locator('.wb-pdf-page[data-ready="true"]').first().waitFor();
  assert.equal(await viewer.locator('.wb-pdf-page').count(),row.statementPdf.pageCount);
  assert((await page.locator('.cm-content').innerText()).includes('isolated public review'),row.originalId+' editor draft unchanged');
  checked.push({id:row.originalId,pages,samples:row.samples.length,images:row.reviewImageCount,subsetSha256:row.statementPdf.sha256,originalBookletSha256:bookletSha,bilingualVerified:true,downloadVerified:true});
  await page.close();
 }
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 const result={checked,browserErrors:0,formulaErrors:0,externalRequests:0,allOriginalPagesRendered:true,consoleAndChineseSamplesPreserved:true,originalBookletByteIdentity:true,originalSubsetByteIdentity:true,allOriginalImagesLoaded:true,editorDraftsPreserved:true,realJudgeSubmissions:0};
 await fs.writeFile(output,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
}finally{await browser?.close();await server.close();}
