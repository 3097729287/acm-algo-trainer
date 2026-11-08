// Real Workbench review of explicit public originals; no account or network writes.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createServer} from 'vite';
import {chromium} from 'playwright';

if(!process.argv[2]||!process.argv[3])throw new Error('Supply isolated public original data and result path');
const rows=JSON.parse(await fs.readFile(process.argv[2],'utf8'));
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const server=await createServer({root,optimizeDeps:{entries:['tests/statement-pdf-fixture.html']},server:{host:'127.0.0.1',port:18796,strictPort:true,hmr:false}});
await server.listen();let browser;const checked=[],errors=[],external=[];let images=0;
try{
 browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
 const context=await browser.newContext({viewport:{width:1280,height:800}});
 await context.route('**/*',route=>{
  const url=new URL(route.request().url());
  if(url.origin==='http://127.0.0.1:18796'||['blob:','data:'].includes(url.protocol))return route.continue();
  external.push(url.href);return route.abort();
 });
 for(const row of rows){
  const page=await context.newPage();page.on('pageerror',error=>errors.push(error.message));
  await page.addInitScript(value=>window.pdfFixtureData=value,row);
  await page.goto('http://127.0.0.1:18796/tests/statement-pdf-fixture.html');
  const statement=page.locator('.wb-statement');await statement.waitFor();
  const text=await statement.textContent();assert.match(text,/输入格式/);assert.match(text,/输出格式/);
  assert.equal(await statement.locator('.katex-error').count(),0,row.originalId);
  const blocks=await statement.locator('pre').allTextContents();
  for(const sample of row.samples){
   assert(blocks.some(value=>value.trimEnd()===sample.input.trimEnd()),row.originalId+' sample input');
   assert(blocks.some(value=>value.trimEnd()===sample.output.trimEnd()),row.originalId+' sample output');
  }
  const pictures=statement.locator('img');
  const referenced=Object.keys(row.images||{}).filter(url=>row.markdown.includes(url)).length;
  assert.equal(await pictures.count(),referenced,row.originalId+' original illustrations');
  for(const picture of await pictures.all()){
   await picture.scrollIntoViewIfNeeded();
   await picture.evaluate(image=>image.decode());
   assert(await picture.evaluate(image=>image.complete&&image.naturalWidth>0));images++;
  }
  checked.push(row.originalId);await page.close();
 }
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 const result={checked,originalImagesLoaded:images,browserErrors:0,formulaErrors:0,samplesPreserved:true,externalRequests:0};
 await fs.writeFile(process.argv[3],JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
}finally{await browser?.close();await server.close();}
