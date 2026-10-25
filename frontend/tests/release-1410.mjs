import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {realpathSync} from 'node:fs';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const server=await createServer({server:{host:'127.0.0.1',port:0,fs:{allow:[process.cwd(),realpathSync('node_modules')]}}});await server.listen();
const base=server.resolvedUrls.local[0];
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1366,height:768}}),errors=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('response',r=>{if(r.status()>=400)errors.push(r.status()+' '+r.url());});
const out='../.backups/local-1410/ui';await mkdir(out,{recursive:true});
const open=async view=>{await page.goto(base+'tests/release-1410-fixture.html?view='+view);await page.waitForTimeout(180);};
try{
 await open('records');
 for(const viewport of [{width:1366,height:768},{width:1024,height:640},{width:1920,height:1080}]){
  await page.setViewportSize(viewport);await page.waitForTimeout(120);
  const fit=await page.evaluate(()=>{const panel=document.querySelector('.submission-log'),box=panel.getBoundingClientRect(),rows=[...panel.querySelectorAll('.submission-log-row')],shown=rows.filter(r=>!r.hasAttribute('aria-hidden'));return {count:shown.length,last:shown.at(-1)?.getBoundingClientRect().bottom,bottom:box.bottom,next:rows[shown.length]?.getBoundingClientRect().bottom,left:shown[0].querySelector('strong').getBoundingClientRect().left,panelLeft:box.left,scroll:getComputedStyle(panel).overflowY};});
  assert(fit.count>0&&fit.last<=fit.bottom+1,JSON.stringify(fit));assert(fit.next>fit.bottom,JSON.stringify(fit));assert(fit.left-fit.panelLeft<40);assert.equal(fit.scroll,'hidden');
 }
 const first=page.locator('.submission-log-row:not([aria-hidden])').first();await first.locator('.submission-problem-link').click();assert.equal(await page.evaluate(()=>window.problemOpened),'20C');
 await first.getByRole('button',{name:'查看提交代码'}).click();assert(await page.evaluate(()=>window.codeOpened));
 const firstId=await first.locator('strong').innerText();assert(!firstId.startsWith('remote:'));
 await page.getByRole('button',{name:'下一页提交',exact:true}).click();await page.waitForTimeout(120);assert(Number(await page.locator('.submission-log').getAttribute('data-offset'))>0);
 await page.screenshot({path:out+'/records.png'});
 await open('range');const slider=page.getByRole('slider',{name:'最低难度滑块'}),box=await slider.boundingBox();const start=box.x+6+(box.width-12)*.25;
 await page.mouse.move(start,box.y+box.height/2);await page.mouse.down();await page.mouse.move(start+47,box.y+box.height/2,{steps:10});
 const visual=Number(await slider.inputValue());assert(Math.abs(box.x+6+(box.width-12)*visual/4000-(start+47))<1.5);await page.mouse.up();assert.equal((await page.evaluate(()=>window.fixture.range.min))%100,0);
 await open('activity');const cells=page.getByRole('gridcell');const a=await cells.nth(0).boundingBox(),b=await cells.nth(1).boundingBox(),c=await cells.nth(5).boundingBox();assert(a.width<=24&&a.width>0);assert.equal(a.x,b.x);assert(b.y>a.y);assert(c.x>a.x);await cells.nth(0).focus();await page.keyboard.press('ArrowDown');assert.equal(await cells.nth(1).getAttribute('aria-selected'),'true');await page.screenshot({path:out+'/activity.png'});
 await open('settings');await page.screenshot({path:out+'/settings.png'});assert.equal(await page.locator('.dino-model').count(),1);assert.equal(await page.locator('.orbit-system').count(),1);
 await open('lab');assert.equal(await page.locator('.lab-catalog>.lab-panel').count(),7);
 for(const id of ['dijkstra','dsu','dfs','bfs']){
  await page.evaluate(id=>window.fixture.seed({learningPaths:{activePath:id,[id]:{mode:'learn'}}}),id);await page.waitForTimeout(50);
  assert.equal(await page.locator('.graph-experiment').count(),1);
  await page.getByRole('button',{name:'下一页',exact:true}).click();assert.match(await page.locator('.lab-position').innerText(),/2 \/ 7/);
  await page.evaluate(id=>window.fixture.seed({learningPaths:{activePath:id,[id]:{mode:'guided'}}}),id);await page.waitForTimeout(30);assert.match(await page.locator('.lab-position').innerText(),/跟做 1 \/ 5/);
 }
 await page.screenshot({path:out+'/graph-guided.png'});
 await page.setViewportSize({width:1024,height:640});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
 await open('radar');await page.getByRole('button',{name:/数学与计数，掌握/}).click();
 const labels=await page.locator('text[data-knowledge-name]').evaluateAll(nodes=>nodes.map(n=>({name:n.textContent,...(()=>{const r=n.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom}})()})));
 assert.equal(labels.length,24);
 for(let i=0;i<labels.length;i++)for(let j=i+1;j<labels.length;j++){const a=labels[i],b=labels[j];assert(!(a.left<b.right&&b.left<a.right&&a.top<b.bottom&&b.top<a.bottom),a.name+' overlaps '+b.name);}
 await page.screenshot({path:out+'/radar.png'});
 await open('format');assert(await page.locator('blockquote .katex').count()>=4);assert.equal((await page.locator('pre').innerText()).trim(),'A_1 \\ldots');
 assert.deepEqual(errors,[]);await writeFile(out+'/report.json',JSON.stringify({ok:true,viewports:3,courses:7,graphGuided:4,submissionPagination:true,pointerAligned:true,columnCalendar:true,errors},null,2));console.log('1.4.10 UI regressions passed');
}finally{await browser.close();await server.close();}
