import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const seed=process.env.TB_CORPUS_SOURCE||path.join(root,'../data/library');
const solutions=JSON.parse(fs.readFileSync(path.join(seed,'solutions.json'),'utf8'));
const lectures=JSON.parse(fs.readFileSync(path.join(seed,'lectures.json'),'utf8'));
const records=[...solutions.map(r=>({id:r.problem_id,markdown:r.markdown,images:r.images})),...lectures.map(r=>({id:r.id,...r.content}))];
const out=process.env.TB_CORPUS_REPORT||path.join(root,'tests/screenshots/corpus');
fs.mkdirSync(out,{recursive:true});
const server=await createServer({root,server:{host:'127.0.0.1',port:18776,strictPort:true}});await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
try{
 const page=await browser.newPage({viewport:{width:1080,height:900}});
 const pageErrors=[];page.on('pageerror',e=>pageErrors.push(e.message));
 await page.route(/^https?:/,r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():r.abort());
 await page.goto('http://127.0.0.1:18776/tests/corpus-reading.html');await page.waitForFunction(()=>window.renderDocument);
 let images=0,math=0;const errors=[];
 for(const [i,record] of records.entries()){
  try{
   const r=await page.evaluate(record=>window.renderDocument(record),record);
   images+=r.images;math+=r.math;
   if(r.mathErrors.length||r.missing.length)errors.push({id:record.id,...r});
   if(['周赛 164::C','周赛 149::F','月赛 310::D'].includes(record.id)){
    await page.evaluate(()=>document.fonts.ready);
    await page.screenshot({path:path.join(out,record.id.replaceAll('::','-')+'.png')});
    const image=page.locator('.reading-image-open').first();
    if(await image.count()){await image.click();await page.locator('dialog[open]').waitFor();await page.keyboard.press('Escape');assert.equal(await page.locator('dialog[open]').count(),0);}
   }
  }catch(error){errors.push({id:record.id,error:String(error)});}
  if((i+1)%100===0)console.log(`Reviewed ${i+1}/${records.length} documents`);
 }
 const report={solutions:solutions.length,lectures:lectures.length,documents:records.length,images,math,errors,pageErrors};
 fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify(report));assert.deepEqual(errors,[]);assert.deepEqual(pageErrors,[]);
}finally{await browser.close();await server.close();}
