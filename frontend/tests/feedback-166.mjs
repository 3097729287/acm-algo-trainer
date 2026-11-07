import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';

const server=await createServer({optimizeDeps:{entries:['tests/learning-browser-fixture.html','tests/editorial-code-fixture.html']},server:{host:'127.0.0.1',port:0}});await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1536,height:900}}),errors=[];
page.on('pageerror',error=>errors.push(error.message));
const base=`http://127.0.0.1:${server.httpServer.address().port}`,output='../.backups/feedback-20261108/ui';await mkdir(output,{recursive:true});
const metrics=()=>page.locator('.study-pane:not([hidden]) .wb-code-pane').evaluate(pane=>{
 const box=s=>pane.querySelector(s).getBoundingClientRect();
 const p=pane.getBoundingClientRect(),c=box('.wb-console'),e=box('.wb-editor'),h=box('.wb-console-splitter');
 return {pane:p.height,console:c.height,editor:e.height,line:h.y,resized:pane.dataset.consoleResized==='true',overflow:pane.scrollHeight>pane.clientHeight+1};
});
const separator=()=>page.getByRole('separator',{name:'调整运行区与代码高度',exact:true});
const drag=async y=>{const box=await separator().boundingBox();await page.mouse.move(box.x+box.width/2,box.y+.5);await page.mouse.down();await page.mouse.move(box.x+box.width/2,y,{steps:8});await page.mouse.up();};
async function noZoomOverlap(){
 const result=await page.locator('.reading-zoom-toast').evaluate(toast=>{
  const a=toast.getBoundingClientRect(),intersects=b=>a.left<b.right-.5&&a.right>b.left+.5&&a.top<b.bottom-.5&&a.bottom>b.top+.5;
  const toolbar=toast.parentElement;
  const conflicts=[...toolbar.querySelectorAll('button,a,select,input')].filter(node=>getComputedStyle(node).visibility!=='hidden'&&intersects(node.getBoundingClientRect())).map(node=>node.getAttribute('aria-label')||node.textContent);
  const title=toolbar.querySelector('.wiki-reader-title,.wb-editor-title,.wb-title,.template-heading h2,.solution-reader-title');
  if(title){const range=document.createRange();range.selectNodeContents(title);for(const b of range.getClientRects())if(intersects(b)){conflicts.push('title');break;}}
  return {inline:toast.classList.contains('is-inline'),conflicts,within:a.left>=toolbar.getBoundingClientRect().left-.5&&a.right<=toolbar.getBoundingClientRect().right+.5};
 });
 assert(result.inline&&result.within&&result.conflicts.length===0,JSON.stringify(result));
}
try{
 await page.goto(base+'/tests/learning-browser-fixture.html');
 await page.getByRole('button',{name:'题目入口',exact:true}).click();
 await page.locator('.cm-content[contenteditable=true]').waitFor();await separator().waitFor();
 const initial=await metrics();
 await drag(initial.line-160);const expanded=await metrics();
 assert(expanded.console>initial.console+145&&expanded.editor<initial.editor-145,JSON.stringify({initial,expanded}));
 assert(!expanded.overflow&&expanded.editor>=119);
 await page.screenshot({path:output+'/console-expanded.png'});
 await separator().focus();await separator().press('End');
 assert((await metrics()).editor>=119,'Maximum lower pane retains useful code height');
 await separator().press('Home');const reset=await metrics();assert.equal(reset.resized,false);assert(Math.abs(reset.console-initial.console)<2);
 await drag(initial.line-140);await drag(initial.line+8);const snapped=await metrics();
 assert.equal(snapped.resized,false,'Dragging near the normal divider snaps to the default');
 await separator().press('ArrowUp');assert((await metrics()).console>initial.console+10);
 await separator().dblclick();assert.equal((await metrics()).resized,false);
 await drag(initial.line-120);const saved=await metrics();
 await page.evaluate(()=>studyFixture.open({kind:'wiki',id:'ds/stack',title:'栈',newTab:true}));
 const wiki=page.frameLocator('.study-pane:not([hidden]) .wiki-reader').locator('body');await wiki.waitFor();
 await wiki.click({position:{x:200,y:160}});
 for(const width of [1536,430]){
  await page.setViewportSize({width,height:900});
  await page.keyboard.down('Control');await page.mouse.wheel(0,-100);await page.keyboard.up('Control');
  await page.getByRole('status',{name:'缩放比例'}).waitFor();await noZoomOverlap();
  await page.screenshot({path:output+`/wiki-zoom-${width}.png`});
 }
 await page.setViewportSize({width:1536,height:900});await page.getByRole('tab',{name:'小月的数组',exact:true}).click();
 await page.waitForTimeout(100);
 const returned=await metrics();
 assert(Math.abs(returned.console/returned.pane-saved.console/saved.pane)<.003,'Each tab retains its lower pane ratio '+JSON.stringify({saved,returned}));
 await page.reload();await page.locator('.cm-content[contenteditable=true]').waitFor();
 assert(Math.abs((await metrics()).console-returned.console)<2,'Console height survives persisted study workspace restoration');
 await separator().press('Home');
 await page.locator('.cm-content').click();await page.keyboard.down('Control');await page.mouse.wheel(0,-100);await page.keyboard.up('Control');
 await page.getByRole('status',{name:'缩放比例'}).waitFor();await noZoomOverlap();
 for(const width of [1000,430]){
  await page.setViewportSize({width,height:700});
  if(width<996)await page.keyboard.press('Alt+2');
  await separator().waitFor();const before=await metrics();await drag(before.line-80);const after=await metrics();
  assert(after.console>before.console+60&&!after.overflow&&after.editor>=119,JSON.stringify({width,before,after}));
  await separator().focus();await separator().press('Home');assert.equal((await metrics()).resized,false);
 }
 await page.setViewportSize({width:1000,height:800});
 await page.goto(base+'/tests/editorial-code-fixture.html');
 await page.waitForFunction(()=>document.querySelector('.editorial-code code')?.textContent===referenceFixture.expected);
 assert.equal(await page.evaluate(()=>referenceFixture.calls.length),1);
 assert(await page.locator('.editorial-code .tok-keyword').count()>0);
 assert(await page.locator('.editorial-code .tok-string,.editorial-code .tok-meta').count()>0);
 await page.getByRole('button',{name:'复制',exact:true}).click();
 assert.equal(await page.evaluate(()=>referenceFixture.copied),await page.evaluate(()=>referenceFixture.expected));
 assert.equal(await page.evaluate(()=>referenceFixture.calls[0].body.code.includes('++i')),false);
 const dark=await page.locator('.tok-keyword').first().evaluate(node=>getComputedStyle(node).color);
 await page.screenshot({path:output+'/reference-dark.png'});
 await page.evaluate(()=>document.documentElement.dataset.theme='light');
 const light=await page.locator('.tok-keyword').first().evaluate(node=>getComputedStyle(node).color);assert.notEqual(light,dark);
 await page.screenshot({path:output+'/reference-light.png'});
 assert.deepEqual(errors,[]);
 await writeFile(output+'/checks.json',JSON.stringify({consoleDrag:true,limits:true,snap:true,doubleClickReset:true,keyboardReset:true,tabPersistence:true,restartPersistence:true,narrow:true,zoomNoOverlap:true,referenceHighlight:true,copyMatchesFormatted:true,errors},null,2));
 console.log('PASS lower console drag/limits/snap/reset/persistence, wide/narrow zoom avoidance, formatted and highlighted reference code with exact copying.');
}finally{await browser.close();await server.close();}
