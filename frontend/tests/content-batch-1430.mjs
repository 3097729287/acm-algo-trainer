import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createServer} from 'vite';
import {chromium} from 'playwright';
import {solutionBlocks} from '../src/lib/practiceMetadata.js';

const front=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),root=path.dirname(front);
const load=async name=>JSON.parse(await fs.readFile(path.join(root,'data/library',name+'.json'),'utf8'));
const ids=[1009,1065,1093,1096].map(number=>`remote:codeforces:${number}::A`);
const [defaults,details,statements]=await Promise.all(['solutions','detailed_solutions','statements'].map(load));
const docs=[];
for(const id of ids){
 const a=defaults.find(row=>row.problem_id===id),b=details.find(row=>row.problem_id===id),s=statements.find(row=>row.problem_id===id)?.content;
 assert(a&&b&&s?.translation?.markdown,id+' has both editorials and a full translation');
 assert.notEqual(a.markdown,b.markdown,id+' keeps meaningfully separate default and detailed explanations');
 for(const article of [a,b])assert(solutionBlocks(article.markdown).some(block=>block.type==='markdown'&&block.markdown.includes('```cpp')),id+' keeps the full program visible');
 docs.push({id:id+'-default',solution:a},{id:id+'-detailed',solution:b},{id:id+'-translation',solution:{markdown:s.translation.markdown,images:s.images||{}}});
}
const out=path.join(front,'tests/screenshots/content-1430');await fs.mkdir(out,{recursive:true});
const server=await createServer({root:front,server:{host:'127.0.0.1',port:0}});await server.listen();
const origin=`http://127.0.0.1:${server.httpServer.address().port}`;
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const errors=[],results=[];
try{
 for(const width of [1440,1050,390])for(const dark of [false,true]){
  for(const doc of docs){
   const page=await browser.newPage({viewport:{width,height:1000}});
   page.on('pageerror',error=>errors.push(error.message));
   await page.route('**/*',route=>route.request().url().startsWith(origin+'/')?route.continue():route.abort());
   await page.addInitScript(data=>{window.editorialTeaching=data;},{solution:doc.solution,lectures:[],dark,narrow:false});
   await page.goto(origin+'/tests/editorial-teaching-fixture.html');
   await page.locator('main h1').waitFor();
   await page.waitForFunction(()=>[...document.querySelectorAll('main img')].every(img=>img.complete&&img.naturalWidth>0));
   assert.equal(await page.locator('.katex-error,.reading-image-missing').count(),0,doc.id+' formulas/images');
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,doc.id+' fits '+width+' px');
   if(doc.id.endsWith('1009::A-detailed')&&width!==1050){
    await page.locator('.reading-image-open').screenshot({path:path.join(out,`simulation-${width}-${dark?'dark':'light'}.png`)});
   }
   results.push({id:doc.id,width,dark,images:await page.locator('main img').count()});
   await page.close();
  }
 }
 assert.deepEqual(errors,[]);
 await fs.writeFile(path.join(out,'report.json'),JSON.stringify({ok:true,documents:docs.length,renders:results.length,results,errors},null,2));
 console.log(JSON.stringify({ok:true,documents:docs.length,renders:results.length,errors}));
}finally{await browser.close();await server.close();}
