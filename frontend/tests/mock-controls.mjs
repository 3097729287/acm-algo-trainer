import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {chromium} from 'playwright';
import {createServer} from 'vite';
import {chooseMockValue,openMockSelection} from './mock-mode-selection.mjs';
const vite=await createServer({server:{host:'127.0.0.1',port:0,watch:null},plugins:[{name:'isolated-mock-controls',configureServer(server){server.middlewares.use((request,response,next)=>{if(!request.url?.startsWith('/api/'))return next();response.writeHead(410);response.end('No live API for mock-controls fixture');});}}]});await vite.listen();
const base=`http://127.0.0.1:${vite.httpServer.address().port}`,browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage(),errors=[],unexpected=[],cases=[];page.setDefaultTimeout(12000);page.on('pageerror',e=>errors.push(e.message));
await page.route('**/*',route=>{const url=new URL(route.request().url());if(url.pathname.startsWith('/api/')||url.origin!==base&&!['data:','blob:'].includes(url.protocol)){unexpected.push(url.origin+url.pathname);return route.abort();}return route.continue();});
const output='tests/screenshots/mock-controls';await mkdir(output,{recursive:true});let passed=false;const modeAnchors=[];
try{
 await page.goto(base+'/tests/revision-fixture.html');await page.getByRole('button',{name:'生成试卷',exact:true}).click();await page.getByRole('button',{name:'开始训练',exact:true}).waitFor();
 for(const width of [2048,1294,960,430,320])for(const theme of ['dark','light']){await page.setViewportSize({width,height:850});await page.evaluate(theme=>{document.documentElement.dataset.theme=theme;document.documentElement.style.fontSize='22px';},theme);
  const geometry=await page.locator('.mock-config .create-buttons').evaluate(node=>{const rect=n=>{const r=n.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height,cx:r.x+r.width/2,cy:r.y+r.height/2};};return {buttons:[...node.querySelectorAll(':scope>button')].map(n=>({box:rect(n),icon:rect(n.querySelector('svg'))})),duration:rect(node.querySelector('.training-duration-summary')),difficulty:rect(node.querySelector('.training-difficulty-summary')),preview:rect(document.querySelector('.paper-preview')),viewport:innerWidth};});
  assert.equal(geometry.buttons.length,2);const[a,b]=geometry.buttons;for(const{box,icon}of geometry.buttons){assert.equal(box.width,64);assert.equal(box.height,42);assert(Math.abs(box.cx-icon.cx)<.6&&Math.abs(box.cy-icon.cy)<.6);assert(box.left>=0&&box.right<=width);}assert.equal(a.box.top,b.box.top);assert.equal(b.box.left-a.box.right,10);const center=(a.box.left+b.box.right)/2;assert(Math.abs(center-geometry.duration.cx)<1&&Math.abs(center-geometry.difficulty.cx)<1&&Math.abs(center-geometry.preview.cx)<1);cases.push({width,theme,fontSize:22,geometry});if(theme==='dark'&&[2048,430].includes(width))await page.screenshot({path:output+`/${width}.png`});
  const modes=await page.getByRole('group',{name:'组题方式',exact:true}).getByRole('button').evaluateAll(nodes=>nodes.map(node=>{const r=node.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,width:r.width,height:r.height};}));
  assert.equal(modes.length,3);assert(modes.every(mode=>mode.left>=0&&mode.right<=width&&mode.width<=180.5&&Math.abs(mode.width-modes[0].width)<1&&Math.abs(mode.height-modes[0].height)<1&&Math.abs(mode.top-modes[0].top)<1),'The three training modes are compact, equal and aligned: '+JSON.stringify({width,modes}));
  assert(Math.abs((modes[0].left+modes[2].right)/2-geometry.preview.cx)<1,'Mode tabs share the paper preview center');
  cases.at(-1).modeTabs=modes;
 }
 await page.setViewportSize({width:1440,height:960});
 const topic=page.getByRole('button',{name:'专项训练',exact:true}),replay=page.getByRole('button',{name:'重现赛',exact:true});
 const previewCount=()=>page.evaluate(()=>revisionFixture.calls.filter(item=>item.path==='contests/preview').length);
 const beforeMode=await previewCount();await topic.click();
 const topicMenu=page.getByRole('listbox',{name:'专项训练知识点',exact:true});await topicMenu.waitFor();
 assert.equal(await page.locator('#tb-page-search .folder-icon-control').count(),0,'Mode selectors no longer live in the top search toolbar');
 assert.equal(await previewCount(),beforeMode);assert.equal(await page.evaluate(()=>revisionFixture.started.length),0,'Changing a mode never generates or starts a contest');
 assert(await topicMenu.evaluate(node=>node===document.activeElement),'The anchored mode menu receives keyboard focus');
 await page.keyboard.press('Escape');assert.equal(await topicMenu.count(),0);assert(await topic.evaluate(node=>node===document.activeElement));
 await topic.press('ArrowDown');await topicMenu.waitFor();await page.keyboard.press('End');await page.keyboard.press('Enter');
 await topicMenu.getByRole('option',{name:'前缀和',exact:true}).waitFor();await topicMenu.getByRole('option',{name:'前缀和',exact:true}).click();
 assert.equal(await page.locator('select[aria-label="专项训练知识点"]').inputValue(),'前缀和');
 await page.getByRole('button',{name:'生成试卷',exact:true}).click();
 assert.deepEqual(await page.evaluate(()=>revisionFixture.calls.filter(item=>item.path==='contests/preview').at(-1).body.tags),['前缀和']);
 await topic.click();await topicMenu.waitFor();assert.equal(await page.locator('.paper-preview').count(),1,'Reopening the same mode preserves the generated preview');
 await page.mouse.click(10,800);assert.equal(await topicMenu.count(),0,'An outside click dismisses the anchored selector');
 for(const width of [1440,430,320])for(const mode of ['专项训练','重现赛']){
  await page.setViewportSize({width,height:850});const menu=await openMockSelection(page,mode),trigger=page.getByRole('button',{name:mode,exact:true});
  await page.waitForFunction(({label,mode})=>{const popup=[...document.querySelectorAll('[role=listbox]')].find(node=>node.getAttribute('aria-label')===label),anchor=[...document.querySelectorAll('.mock-config button')].find(node=>node.textContent===mode);if(!popup||!anchor)return false;const r=popup.getBoundingClientRect(),a=anchor.getBoundingClientRect();return Math.abs(r.y-a.bottom-8)<1&&Math.abs(r.x-Math.max(8,Math.min(a.x,innerWidth-r.width-8)))<1;},{label:mode==='专项训练'?'专项训练知识点':'重现赛比赛',mode});
  const box=await menu.boundingBox(),anchor=await trigger.boundingBox();assert(box.x>=0&&box.x+box.width<=width+.5&&box.y+box.height<=850+.5);
  assert(Math.abs(box.x-Math.max(8,Math.min(anchor.x,width-box.width-8)))<1&&Math.abs(box.y-anchor.y-anchor.height-8)<1,'Mode selector stays anchored below its actual tab: '+JSON.stringify({width,mode,box,anchor}));
  modeAnchors.push({width,mode,box,anchor});if(width!==320)await page.screenshot({path:`${output}/mode-${mode}-${width}.png`,animations:'disabled'});
  await page.keyboard.press('Escape');assert(await trigger.evaluate(node=>node===document.activeElement));
 }
 await page.setViewportSize({width:1440,height:960});await chooseMockValue(page,'重现赛','CCPC 2025 郑州区域赛');
 await page.getByRole('button',{name:'生成试卷',exact:true}).click();
 const replayBody=await page.evaluate(()=>revisionFixture.calls.filter(item=>item.path==='contests/preview').at(-1).body);assert.equal(replayBody.contest,'CCPC 2025 郑州区域赛');assert.equal(replayBody.duration,300);assert.equal(await page.evaluate(()=>revisionFixture.started.length),0);
 await openMockSelection(page,'重现赛');await page.getByRole('button',{name:'综合训练',exact:true}).click();assert.equal(await page.getByRole('listbox').count(),0,'Switching away closes the previous mode selector');
 await page.getByRole('button',{name:'生成试卷',exact:true}).click();
 const before=await page.evaluate(()=>revisionFixture.calls.filter(item=>item.path==='contests/preview').length);await page.getByRole('button',{name:'生成试卷',exact:true}).click();assert.equal(await page.evaluate(()=>revisionFixture.calls.filter(item=>item.path==='contests/preview').length),before+1);await page.getByRole('button',{name:'开始训练',exact:true}).click();assert.equal(await page.evaluate(()=>revisionFixture.started.at(-1).previewId),'preview-comprehensive');assert.deepEqual(errors,[]);assert.deepEqual(unexpected,[]);passed=true;console.log('PASS compact aligned mode tabs; tab-anchored knowledge/replay selectors, keyboard/Esc/outside, exact original IDs, no accidental start, preserved preview and 64x42 generator/start controls at five widths/two themes');
}finally{await writeFile(output+'/report.json',JSON.stringify({ok:passed&&errors.length===0&&unexpected.length===0,cases,modeAnchors,errors,unexpected},null,2));await browser.close();await vite.close();}
