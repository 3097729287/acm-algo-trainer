import assert from 'node:assert/strict';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {resolve,join} from 'node:path';
import {createServer} from 'vite';
import {chromium} from 'playwright';

const root=resolve(fileURLToPath(new URL('../..',import.meta.url)));
const out=join(root,'.backups/div3-1131-a/final');
const data=JSON.parse(await readFile(join(out,'readers.json'),'utf8'));
const index=data.readers.findIndex(x=>x.title==='Fraction and Six');
assert(index>=0);assert.equal(data.readers[index].detailedSolution,null);
const server=await createServer({root:join(root,'frontend'),plugins:[{name:'cf2278-a-data',configureServer(server){
 server.middlewares.use((req,res,next)=>{if(req.url!=='/__three_contests_data')return next();res.setHeader('Content-Type','application/json; charset=utf-8');res.end(JSON.stringify(data));});
}}],server:{host:'127.0.0.1',port:0}});
const report={passed:false,articleFrames:[],statementFrames:[],errors:[]};let browser;
await mkdir(join(out,'render'),{recursive:true});
try{
 await server.listen();browser=await chromium.launch({channel:'msedge',headless:true});
 const page=await browser.newPage({viewport:{width:1180,height:900}});
 page.on('pageerror',x=>report.errors.push(x.message));
 await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/tests/three-contests-fixture.html`);
 await page.waitForFunction(()=>window.openContestEditorial);await page.evaluate(i=>window.openContestEditorial(i),index);
 const metrics=()=>page.evaluate(()=>({mathErrors:document.querySelectorAll('.katex-error').length,
  brokenImages:[...document.images].filter(i=>!i.complete||!i.naturalWidth).length,
  overflow:document.documentElement.scrollWidth>innerWidth+2,
  code:[...document.querySelectorAll('code.language-cpp')].map(x=>x.textContent)}));
 for(const mode of [{name:'wide-light',width:1180,height:900,theme:'light'},{name:'wide-dark',width:1180,height:900,theme:'dark'},{name:'narrow-dark',width:390,height:844,theme:'dark'}]){
  await page.setViewportSize(mode);await page.evaluate(theme=>{document.documentElement.dataset.theme=theme;document.documentElement.classList.toggle('dark',theme==='dark');},mode.theme);
  await page.locator('code.language-cpp').waitFor();const m=await metrics();assert.equal(m.mathErrors,0);assert.equal(m.overflow,false);
  assert.equal(m.code.length,1);assert.equal(m.code[0].trim(),/^```cpp\s*\n([\s\S]*?)^```/m.exec(data.readers[index].markdown)[1].trim());
  await page.screenshot({path:join(out,'render',mode.name+'.png')});report.articleFrames.push(mode.name);
 }
 const statement=data.statements.findIndex(x=>x.title==='Fraction and Six'||x.markdown.startsWith('# Fraction and Six'));
 assert(statement>=0);
 for(const chinese of [false,true]){
  await page.evaluate(({i,chinese})=>window.openContestStatement(i,chinese),{i:statement,chinese});
  await page.waitForFunction(()=>[...document.images].every(i=>i.complete));const m=await metrics();assert.equal(m.mathErrors,0);assert.equal(m.brokenImages,0);
  assert.equal(await page.locator('.reader-content .reading-image-open img').count(),1);report.statementFrames.push({chinese,images:1});
 }
 assert.deepEqual(report.errors,[]);report.passed=true;
 console.log(JSON.stringify(report));
}finally{await writeFile(join(out,'render/report.json'),JSON.stringify(report,null,2)+'\n');await browser?.close();await server.close();}
