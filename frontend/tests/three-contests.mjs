import assert from 'node:assert/strict';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {resolve,join} from 'node:path';
import {createServer} from 'vite';
import {chromium} from 'playwright';

const root=resolve(fileURLToPath(new URL('../..',import.meta.url)));
const output=join(root,'.backups/three-contests/render');
await mkdir(output,{recursive:true});
const data=JSON.parse(await readFile(join(root,'.backups/three-contests/readers.json'),'utf8'));
function mainFigureCount(markdown){
 let lessonLevel=0,fence=false,count=0;
 for(const line of markdown.split('\n')){
  if(/^```/.test(line)){fence=!fence;continue;}
  if(fence)continue;
  const heading=/^(#{1,6})\s+(.+)$/.exec(line);
  if(heading&&lessonLevel&&heading[1].length<=lessonLevel)lessonLevel=0;
  if(heading&&/从零讲[：:]/.test(heading[2]))lessonLevel=heading[1].length;
  if(!lessonLevel)count+=(line.match(/!\[[^\]]*\]\((assets\/[^)]+)\)/g)||[]).length;
 }
 return count;
}
const api={name:'three-contests-fixture-data',configureServer(server){server.middlewares.use((req,res,next)=>{
 if(req.url!=='/__three_contests_data')return next();
 res.setHeader('Content-Type','application/json; charset=utf-8');res.end(JSON.stringify(data));
})}};
const server=await createServer({root:join(root,'frontend'),plugins:[api],server:{host:'127.0.0.1',port:0}});
let browser;
const report={passed:false,articles:[],statements:[],foundationFlows:0,imageZoomFlows:0,errors:[]};
try{
 await server.listen();
 browser=await chromium.launch({channel:'msedge',headless:true});
 const page=await browser.newPage({viewport:{width:1180,height:900}});
 page.on('pageerror',error=>report.errors.push(error.message));
 await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/tests/three-contests-fixture.html`);
 await page.waitForFunction(()=>window.fixtureData&&window.openContestEditorial);
 const metrics=()=>page.evaluate(()=>({mathErrors:document.querySelectorAll('.katex-error').length,
  brokenImages:[...document.images].filter(i=>!i.complete||!i.naturalWidth).length,
  images:document.images.length,overflow:document.documentElement.scrollWidth>innerWidth+2,
  cpp:[...document.querySelectorAll('code.language-cpp')].map(c=>c.textContent),
  replacements:document.body.innerText.includes('\ufffd'),
  invisibleFigures:[...document.querySelectorAll('.reader-content .reading-image-open img')].filter(i=>i.getBoundingClientRect().width<20||i.getBoundingClientRect().height<20).length}));
 for(let i=0;i<data.readers.length;i++){
  await page.evaluate(i=>window.openContestEditorial(i),i);
  await page.getByRole('button',{name:'切换为详细题解',exact:true}).waitFor();
  for(const variant of ['default','detailed']){
   if(variant==='detailed')await page.getByRole('button',{name:'切换为详细题解',exact:true}).click();
   await page.locator('code.language-cpp').waitFor();
   for(const mode of [{name:'wide-light',width:1180,height:900,theme:'light'}, {name:'wide-dark',width:1180,height:900,theme:'dark'}, {name:'narrow-dark',width:390,height:844,theme:'dark'}]){
    await page.setViewportSize({width:mode.width,height:mode.height});
    await page.evaluate(theme=>{document.documentElement.dataset.theme=theme;document.documentElement.classList.toggle('dark',theme==='dark');},mode.theme);
    await page.emulateMedia({colorScheme:mode.theme});
    await page.evaluate(()=>document.fonts.ready);
    await page.waitForFunction(()=>[...document.images].every(i=>i.complete));
    const m=await metrics();
    assert.equal(m.mathErrors,0,`${i} ${variant} ${mode.name}: math`);
    assert.equal(m.brokenImages,0,`${i} ${variant} ${mode.name}: images`);
    assert.equal(m.overflow,false,`${i} ${variant} ${mode.name}: body overflow`);
    assert.equal(m.replacements,false,`${i}: encoding`);
    assert.equal(m.invisibleFigures,0,`${i} ${variant} ${mode.name}: figure must have visible dimensions`);
    const expectedFigures=mainFigureCount(variant==='detailed'?data.readers[i].detailedSolution.markdown:data.readers[i].markdown);
    assert.equal(await page.locator('.reader-content .reading-image-open img').count(),expectedFigures,`${i}: every main figure must be shown`);
    assert.equal(m.cpp.length,1,`${i}: exactly one reference program`);
    const reference=/^```cpp\s*\n([\s\S]*?)^```/m.exec(data.readers[i].markdown)[1];
    assert.equal(m.cpp[0].trim(),reference.trim());
    report.articles.push({id:data.readers[i].id||i,variant,mode:mode.name,images:m.images,mathErrors:0});
    if(variant==='detailed'&&[3,4,5,8,9,10,15].includes(i)){
     const image=page.locator('.reader-content img').first();
     if(await image.count())await image.scrollIntoViewIfNeeded();
     await page.screenshot({path:join(output,`${i}-${variant}-${mode.name}.png`)});
     const enlarge=page.locator('.reader-content .reading-image-open').first();
     if(await enlarge.count()){
      await enlarge.click();await page.locator('dialog[open]').waitFor();
      const full=await page.locator('dialog[open] .reading-image-full img').boundingBox();assert(full&&full.width>=700);
      await page.screenshot({path:join(output,`${i}-zoom-${mode.name}.png`)});
      await page.locator('dialog[open]').getByRole('button',{name:'关闭',exact:true}).click();report.imageZoomFlows++;
     }
    }
   }
   const foundation=page.locator('.lesson-reader-link>button:first-child').first();
   if(await foundation.count()){
    await foundation.click();
    await page.getByRole('button',{name:'返回上一级',exact:true}).waitFor();
    await page.waitForFunction(()=>[...document.images].every(i=>i.complete));
    const m=await metrics();assert.equal(m.mathErrors,0);assert.equal(m.brokenImages,0);
    await page.getByRole('button',{name:'返回上一级',exact:true}).click();report.foundationFlows++;
   }
  }
 }
 for(let i=0;i<data.statements.length;i++){
  for(const chinese of [false,...(data.statements[i].translation?[true]:[])]){
   await page.evaluate(({i,chinese})=>window.openContestStatement(i,chinese),{i,chinese});
   await page.waitForTimeout(40);await page.waitForFunction(()=>[...document.images].every(i=>i.complete));
   const m=await metrics();assert.equal(m.mathErrors,0,`statement ${i}`);assert.equal(m.brokenImages,0);
   report.statements.push({index:i,chinese,images:m.images,mathErrors:0});
  }
 }
 assert.deepEqual(report.errors,[]);report.passed=true;
 await writeFile(join(output,'report.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({passed:true,articleFrames:report.articles.length,statements:report.statements.length,foundationFlows:report.foundationFlows,imageZoomFlows:report.imageZoomFlows}));
}finally{
 if(!report.passed)await writeFile(join(output,'report.json'),JSON.stringify(report,null,2)+'\n');
 await browser?.close();await server.close();
}
