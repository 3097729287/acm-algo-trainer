import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createServer} from 'vite';
import {chromium} from 'playwright';

if(!process.argv[2]||!process.argv[3])throw new Error('Supply isolated reviewed translation data and result path');
const rows=JSON.parse(await fs.readFile(process.argv[2],'utf8'));
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const server=await createServer({root,optimizeDeps:{entries:['tests/statement-pdf-fixture.html']},server:{host:'127.0.0.1',port:18795,strictPort:true,hmr:false}});
await server.listen();let browser;const checked=[],errors=[],external=[];let originalImagesLoaded=0;
try{
 browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
 for(const row of rows){
  const page=await browser.newPage({viewport:{width:1280,height:800}});
  page.on('request',request=>{if(/^https?:/.test(request.url())&&!request.url().startsWith('http://127.0.0.1:18795/'))external.push(request.url());});
  page.on('pageerror',error=>errors.push(error.message));await page.addInitScript(value=>window.pdfFixtureData=value,row);
  await page.goto('http://127.0.0.1:18795/tests/statement-pdf-fixture.html');
  await page.locator('.wb-pdf-page[data-page="1"][data-ready="true"]').waitFor();
  await page.getByRole('button',{name:'原文',exact:true}).click();
  await page.getByRole('button',{name:'中文',exact:true}).waitFor();
  const statement=page.locator('.wb-statement');await statement.waitFor();
  assert.equal(await statement.locator('.katex-error').count(),0,row.originalId);
  assert.match(await statement.textContent(),/输入格式|题目描述/);
  assert.equal(await page.locator('.wb-statement-pdf').count(),0,'Chinese text replaces the original PDF view');
  assert.equal(await page.locator('.wb-translation-error').count(),0);
  const expectedImages=[...(row.translation?.markdown||'').matchAll(/!\[[^\]]*\]\([^)]+\)/g)].length;
  const pictures=statement.locator('img');assert.equal(await pictures.count(),expectedImages,row.originalId+' original diagrams');
  for(let index=0;index<expectedImages;index++){
   const picture=pictures.nth(index);await picture.scrollIntoViewIfNeeded();
   await picture.evaluate(img=>new Promise((resolve,reject)=>{
    if(img.complete){img.naturalWidth?resolve():reject(new Error('Original diagram failed to load'));return;}
    img.addEventListener('load',resolve,{once:true});img.addEventListener('error',()=>reject(new Error('Original diagram failed to load')),{once:true});
   }));originalImagesLoaded++;
  }
  const code=await statement.locator('pre').allTextContents();
  for(const sample of row.samples){
   assert(code.some(value=>value.trimEnd()===sample.input.trimEnd()),row.originalId+' input');
   assert(code.some(value=>value.trimEnd()===sample.output.trimEnd()),row.originalId+' output');
  }
  await page.getByRole('button',{name:'中文',exact:true}).click();
  await page.locator('.wb-pdf-page[data-page="1"][data-ready="true"]').waitFor();
  checked.push(row.originalId);await page.close();
 }
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 const result={checked,originalImagesLoaded,browserErrors:0,formulaErrors:0,samplesPreserved:true,originalPdfRestored:true,externalRequests:0};
 await fs.writeFile(process.argv[3],JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
}finally{await browser?.close();await server.close();}
