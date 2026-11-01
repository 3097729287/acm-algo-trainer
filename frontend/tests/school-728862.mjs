import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createServer} from 'vite';
import {chromium} from 'playwright';
import {catalogSegments,catalogEntries} from '../src/lib/contestCatalog.js';

const front=fileURLToPath(new URL('../',import.meta.url)),root=path.dirname(front.replace(/[\\/]$/,''));
const folder=path.join(root,'data/school-training/728862'),out=path.join(root,'.backups/school728862/render');
fs.mkdirSync(out,{recursive:true});
const rows=JSON.parse(fs.readFileSync(path.join(folder,'problems.json'),'utf8')).map(p=>p.encoded);
const statements=JSON.parse(fs.readFileSync(path.join(folder,'statements.json'),'utf8')).map(p=>p.content);
const methods=JSON.parse(fs.readFileSync(path.join(folder,'solution_methods.json'),'utf8'));
const lectures=JSON.parse(fs.readFileSync(path.join(root,'data/library/lectures.json'),'utf8')).map(p=>p.content);
for(const row of rows)assert.deepEqual(catalogSegments(row),['校队训练','1101 TTC(Team Training Contest)']);
assert.equal(catalogEntries(rows,['校队训练']).length,1);
const read=(letter,variant)=>{
 const markdown=fs.readFileSync(path.join(folder,variant,letter+'.md'),'utf8'),images={};
 for(const match of markdown.matchAll(/!\[[^\]]*\]\((assets\/[^)]+)\)/g))images[match[1]]='data:image/svg+xml;base64,'+fs.readFileSync(path.join(folder,match[1])).toString('base64');
 return {markdown,images};
};
const vite=await createServer({root:front,server:{host:'127.0.0.1',port:0},logLevel:'error'});await vite.listen();
const browser=await chromium.launch({channel:'msedge',headless:true});
const errors=[],report={readerFlows:0,articleFrames:0,statementFrames:0,diagrams:0,sourceImages:0,catalogProblems:12};
const base=`http://127.0.0.1:${vite.httpServer.address().port}/tests/school-728862-fixture.html`;
try{
 for(const row of rows){
  const body=read(row.problem,'default'),detailed=read(row.problem,'detailed');
  const method={...methods.find(m=>m.problem_id===row.id).content.methods[0],...body,detailedSolution:detailed};
  const reader={title:row.title,primaryMethod:'main',methods:[method]};
  for(const [width,dark] of [[1280,false],[820,true],[390,false]]){
   const page=await browser.newPage({viewport:{width,height:1000}});page.on('pageerror',e=>errors.push(e.message));
   await page.addInitScript(data=>window.gymFixture=data,{reader,lectures,dark});await page.goto(base);
   await page.locator('h2').first().waitFor();
   for(const variant of ['default','detailed']){
    if(variant==='detailed')await page.getByRole('button',{name:'切换为详细题解',exact:true}).click();
    await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));
    assert.equal(await page.locator('.katex-error,.reading-image-missing').count(),0,row.id);
    assert.equal(await page.locator('.reader-content .code-block').count(),1,'Verified reference must stay visible');
    assert(await page.locator('.reader-content').innerText().then(t=>t.includes('思路')&&t.includes('易错点')));
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,row.id+' '+width);
    const diagrams=page.locator('.reader-content .reading-image-open');
    report.diagrams+=await diagrams.count();
    if(width===1280&&variant==='detailed'&&await diagrams.count())await diagrams.first().screenshot({path:path.join(out,row.problem+'-diagram.png')});
    if(row.problem==='D'&&width===1280&&variant==='detailed')await page.screenshot({path:path.join(out,'D-derivation.png'),fullPage:true});
    if(row.problem==='J'&&width===390&&variant==='detailed')await page.screenshot({path:path.join(out,'J-mobile.png'),fullPage:true});
    report.articleFrames++;
   }
   const link=page.locator('.lesson-reader-link button').first();await link.click();
   await page.getByRole('button',{name:'返回题解',exact:true}).waitFor();
   assert((await page.locator('.reader-content').innerText()).length>60);
   await page.getByRole('button',{name:'返回题解',exact:true}).click();
   await page.getByRole('button',{name:'切换为默认题解',exact:true}).waitFor();
   report.readerFlows++;await page.close();
  }
 }
 for(const statement of statements){
  const page=await browser.newPage({viewport:{width:820,height:1000}});page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(data=>window.gymFixture=data,{mode:'statement',statement});await page.goto(base);
  await page.locator('main').waitFor();await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));
  assert.equal(await page.locator('.katex-error,.reading-image-missing').count(),0,statement.id);
  report.sourceImages+=await page.locator('img').count();report.statementFrames++;await page.close();
 }
 const page=await browser.newPage({viewport:{width:1280,height:900}});
 await page.addInitScript(data=>window.gymFixture=data,{mode:'catalog',rows});await page.goto(base);
 await page.getByRole('button',{name:/1101 TTC/}).waitFor();await page.getByRole('button',{name:/1101 TTC/}).click();
 await page.screenshot({path:path.join(out,'catalog.png')});await page.close();
 assert.deepEqual(errors,[]);report.passed=true;console.log(JSON.stringify(report));
}catch(error){report.error=error.stack;throw error;}
finally{fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({...report,errors},null,2));await browser.close();await vite.close();}
