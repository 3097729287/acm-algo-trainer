import assert from 'node:assert/strict';
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import {realpathSync} from 'node:fs';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const server=await createServer({server:{host:'127.0.0.1',port:0,fs:{allow:[process.cwd(),realpathSync('node_modules')]}}});await server.listen();
const base=server.resolvedUrls.local[0],browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1366,height:768}}),errors=[];
page.setDefaultTimeout(12000);page.on('pageerror',e=>errors.push(e.message));
const out='../.backups/local-1411/ui';await mkdir(out,{recursive:true});
const open=async view=>{await page.goto(base+'tests/release-1411-fixture.html?view='+view);await page.waitForTimeout(100);};
try{
 await open('range');const slider=page.getByRole('slider',{name:'最低难度滑块'}),box=await slider.boundingBox(),unit=(box.width-12)/40,start=box.x+6+unit*10,y=box.y+box.height/2;
 await page.mouse.move(start,y);await page.mouse.down();await page.mouse.move(start+unit*.3,y);assert.equal(await slider.inputValue(),'1000');
 await page.mouse.move(start+unit*.8,y);assert.equal(await slider.inputValue(),'1100');await page.mouse.move(start+unit*4,y);assert.equal(await slider.inputValue(),'1400');await page.mouse.up();assert.equal(await page.evaluate(()=>window.fixture.range.min),1400);
 await open('activity');assert.equal(await page.getByRole('gridcell').count(),365);
 for(const viewport of [{width:1366,height:768},{width:1024,height:640},{width:1920,height:1080}]){
  await page.setViewportSize(viewport);await page.waitForTimeout(100);
  const fit=await page.locator('.activity-continuous-grid').evaluate(g=>{const p=g.parentElement,a=g.getBoundingClientRect(),b=p.getBoundingClientRect(),c=g.children;return {coverage:a.width/b.width,right:a.right,bound:b.right,bottom:a.bottom,limit:b.bottom,a:c[0].getBoundingClientRect().x,b:c[1].getBoundingClientRect().x,rows:Number(g.getAttribute('aria-rowcount')),next:c[Number(g.getAttribute('aria-rowcount'))].getBoundingClientRect().x};});
  assert(fit.coverage>.85&&fit.right<=fit.bound+1&&fit.bottom<=fit.limit+1,JSON.stringify(fit));assert.equal(fit.a,fit.b);assert(fit.next>fit.a);
 }
 await page.locator('.activity-month-heading h2').click();await page.keyboard.press('d');assert.match(await page.locator('[aria-label="日期明细分页"]').innerText(),/第 2/);await page.keyboard.press('a');assert.match(await page.locator('[aria-label="日期明细分页"]').innerText(),/第 1/);
 await page.screenshot({path:out+'/calendar.png'});
 await open('settings');assert.equal(await page.locator('img.dino-model').count(),1);assert(await page.locator('img.dino-model').evaluate(x=>x.complete&&x.naturalWidth>0));await page.screenshot({path:out+'/settings.png'});
 await open('random');await page.getByRole('button',{name:'随机单题',exact:true}).click();await page.getByRole('button',{name:'取消',exact:true}).click();assert.equal(await page.evaluate(()=>window.chosen||0),0);
 await page.getByRole('button',{name:'随机单题',exact:true}).click();await page.getByRole('button',{name:'确认',exact:true}).click();await page.waitForTimeout(150);assert.equal(await page.evaluate(()=>window.chosen),1);assert.equal(await page.locator('[data-popconfirm]').count(),0);
 await open('lab');assert.equal(await page.locator('.lab-catalog>.lab-panel').count(),10);const cards=await page.locator('.lab-catalog>.lab-panel').evaluateAll(x=>x.slice(0,3).map(n=>n.getBoundingClientRect().x));assert(cards[1]>cards[0]);await page.screenshot({path:out+'/lab.png'});
 for(const id of ['sorting-basics','divide-sort','bucket-sort']){
  await page.evaluate(id=>window.fixture.seed({learningPaths:{activePath:id,[id]:{mode:'learn'}}}),id);await page.locator('.sorting-experiment').waitFor();
  await page.getByRole('button',{name:'查看结果',exact:true}).click();const values=await page.locator('.sorting-array b').allTextContents();assert.deepEqual(values.map(Number),values.map(Number).sort((a,b)=>a-b));
  await page.keyboard.press('d');assert.match(await page.locator('.lab-position').innerText(),/^2 /);await page.keyboard.press('a');assert.match(await page.locator('.lab-position').innerText(),/^1 /);
  await page.getByRole('textbox',{name:'预测下一步数组'}).fill('4 2');await page.keyboard.press('d');assert.match(await page.locator('.lab-position').innerText(),/^1 /);
  await page.evaluate(id=>window.fixture.seed({learningPaths:{activePath:id,[id]:{mode:'guided'}}}),id);await page.waitForTimeout(30);assert.match(await page.locator('.lab-position').innerText(),/跟做 1 \/ 5/);
 }
 await page.screenshot({path:out+'/guided.png'});
 await open('lists');await page.getByRole('button',{name:'题单目录方式',exact:true}).click();await page.locator('.catalog-folder-row').first().click();await page.locator('.catalog-folder-row').first().click();await page.locator('.training-list-table').waitFor();
 let cells=await page.locator('.training-list-table tbody tr td:nth-child(2)').allTextContents();assert(cells.length>2);
 const first=await page.locator('.training-list-table tbody tr').first().getAttribute('data-id');assert.equal(first,'list-0');
 await page.getByRole('button',{name:'切换题单难度排序方向'}).click();assert.equal(await page.locator('.training-list-table tbody tr').first().getAttribute('data-id'),'list-7');
 await page.locator('.training-list-table tbody tr').first().locator('td').last().click();assert.equal(await page.evaluate(()=>window.trained),'list-7');
 await page.keyboard.press('ArrowRight');assert.match(await page.locator('[aria-label="题单分页"]').innerText(),/第 2/);await page.keyboard.press('a');assert.match(await page.locator('[aria-label="题单分页"]').innerText(),/第 1/);
 await page.keyboard.press('Backspace');await page.locator('.catalog-folder-row').first().waitFor();assert.equal(await page.getByRole('button',{name:'切换题单难度排序方向'}).count(),0);assert((await page.locator('.catalog-folder-row strong').first().evaluate(x=>parseFloat(getComputedStyle(x).fontSize)))>=15);
 await page.screenshot({path:out+'/folders.png'});
 // Render the actual imported statements and translations in the shared reader.
 const statements=JSON.parse(await readFile('../data/library/statements.json','utf8')).filter(x=>/remote:(codeforces:726517|nowcoder:142622)::|lab:codeforces:(339A|405A|160A|977C|451B|1490D|768B|559B|448C|873D|43A|4C|1520D|1742D|1399C)$/.test(x.problem_id));
 assert.equal(statements.length,33);await open('content');let rendered=0;
 for(const {problem_id,content} of statements)for(const markdown of [content.markdown,content.translation?.markdown].filter(Boolean)){
  await page.evaluate(content=>window.fixture.render(content),{...content,markdown});await page.waitForTimeout(20);
  const bad=await page.locator('.katex-error').allTextContents();assert.deepEqual(bad,[],problem_id+': '+bad.join(' '));
  assert.equal(await page.locator('.reading-image-missing').count(),0,problem_id);rendered++;
 }
 assert.deepEqual(errors,[]);await writeFile(out+'/report.json',JSON.stringify({ok:true,rendered,courses:10,viewports:3,stepDrag:true,calendar:true,keys:true,folders:true,randomConfirmation:true,errors},null,2));console.log('1.4.11 UI checks passed: '+rendered+' statement renders');
}finally{await browser.close();await server.close();}
