import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const out=path.join(root,'.backups/core7-editorials-20261030/reader');fs.mkdirSync(out,{recursive:true});
const authored=JSON.parse(fs.readFileSync(path.join(root,'.backups/core7-editorials-20261030/authored.json'),'utf8'));
const solutions=JSON.parse(fs.readFileSync(path.join(root,'.backups/core7-editorials-20261030/runtime-solutions.json'),'utf8'));
const lectures=JSON.parse(fs.readFileSync(path.join(root,'data/library/lectures.json'),'utf8')).map(r=>r.content);
const selections=[['P1425','io-basics'],['P5705','strings'],['P1553','string-tools'],['P5741','structures'],['P5737','functions'],['CF2135A','arrays'],['CF2136A','basic-control'],['B2029','basic-arithmetic'],['P1923','random-selection'],['P1059','sort'],['P1177','recursion']];
selections.push(['P1088','lex-permutation'],['P1303','big-integers']);
selections.push(['P6155','unsigned64'],['P2949','heap'],['P12041','dsu'],['AT_arc161_c','trees']);
const server=await createServer({root:path.join(root,'frontend'),server:{host:'127.0.0.1',port:0}});await server.listen();
const browser=await chromium.launch({channel:'msedge',headless:true});const errors=[],frames=[];
try{
for(const [width,dark] of [[1440,false],[1050,true],[390,false]])for(const [pid,name] of selections){
  const content=solutions.find(row=>row.problem_id==='luogu-training-'+pid).content;
  const reader={...content,title:pid};const page=await browser.newPage({viewport:{width,height:1000}});
  page.on('pageerror',error=>errors.push(error.message));
  await page.addInitScript(data=>{window.core7Reader=data;},{reader,lectures,dark});
  await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/tests/core7-reader-fixture.html`);
  await page.getByRole('button',{name:'切换为详细题解',exact:true}).waitFor();
  for(const method of content.methods){
    await page.locator(`[data-method="${method.id}"]`).click();
    await page.getByRole('button',{name:'切换为详细题解',exact:true}).waitFor();
    const first=await page.locator('.reader-content').innerText();
    await page.getByRole('button',{name:'切换为详细题解',exact:true}).click();
    await page.getByRole('button',{name:'切换为默认题解',exact:true}).waitFor();
    const second=await page.locator('.reader-content').innerText();
    assert.notEqual(first,second,pid+' '+method.id+' has two distinct variants');
    assert.equal(await page.locator('.katex-error,.reading-image-missing').count(),0);
    await page.getByRole('button',{name:'切换为默认题解',exact:true}).click();
  }
  const lessonMethod=authored.find(entry=>entry.pid===pid&&entry.lessons.includes(name));assert.ok(lessonMethod,name);
  await page.locator(`[data-method="${lessonMethod.method}"]`).click();
  const lesson=lectures.find(l=>l.id==='lecture:foundation-'+name);assert.ok(lesson,name);
  const open=page.locator('.lesson-reader-link button').filter({hasText:lesson.displayTitle});
  assert.equal(await open.count(),1,pid+' has one precisely matched '+name+' lesson');
  await open.click();await page.getByRole('button',{name:'返回题解',exact:true}).waitFor();
  await page.waitForFunction(()=>[...document.querySelectorAll('.reader-content img')].every(i=>i.complete&&i.naturalWidth>0));
  assert.ok((await page.locator('.reader-content').innerText()).length>120);
  assert.equal(await page.locator('.katex-error,.reading-image-missing').count(),0);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
  const capture=pid+'-'+name+'-'+width+'.png';await page.screenshot({path:path.join(out,capture)});
  await page.getByRole('button',{name:'返回题解',exact:true}).click();
  await page.getByRole('button',{name:'切换为详细题解',exact:true}).waitFor();
  frames.push({pid,name,width,dark,capture});await page.close();
}
const amended=JSON.parse(fs.readFileSync(path.join(root,'.backups/core7-editorials-20261030/private-amendment-reader.json'),'utf8'));
for(const width of [1440,390]){
  const page=await browser.newPage({viewport:{width,height:1000}});
  page.on('pageerror',error=>errors.push(error.message));
  await page.addInitScript(data=>{window.core7Reader=data;},{reader:amended,lectures:[],dark:false});
  await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/tests/core7-reader-fixture.html`);
  await page.getByRole('button',{name:'切换为详细题解',exact:true}).waitFor();
  assert.ok((await page.locator('.reader-content').innerText()).includes('Private annotation remains intact after a public editorial update.'));
  await page.getByRole('button',{name:'切换为详细题解',exact:true}).click();
  await page.getByRole('button',{name:'切换为默认题解',exact:true}).waitFor();
  assert.ok((await page.locator('.reader-content').innerText()).includes('update. detailed'));
  assert.equal(await page.locator('.katex-error,.reading-image-missing').count(),0);
  const capture=`private-primary-variants-${width}.png`;await page.screenshot({path:path.join(out,capture)});
  frames.push({pid:'private-amendment-fixture',width,capture});await page.close();
}
assert.deepEqual(errors,[]);fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({frames,errors},null,2)+'\n');console.log(JSON.stringify({frames:frames.length,errors}));
}finally{await browser.close();await server.close();}
