import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {openMockSelection} from './mock-mode-selection.mjs';
import {realpathSync} from 'node:fs';
import {createServer} from 'vite';
import {chromium} from 'playwright';
import {problemTitle} from '../src/lib/problemTitle.js';
const vite=await createServer({server:{host:'127.0.0.1',port:0,fs:{allow:[process.cwd(),realpathSync('node_modules')]}}});await vite.listen();
const browser=await chromium.launch({channel:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1366,height:768}}),errors=[];
page.setDefaultTimeout(10000);page.on('pageerror',error=>errors.push(error.message));
const base=vite.resolvedUrls.local[0],out='../.backups/local-1413/ui';await mkdir(out,{recursive:true});
const open=async mode=>{await page.goto(base+'tests/release-1413-fixture.html?view='+mode);await page.waitForTimeout(120);};
const rect=locator=>locator.evaluate(node=>{const r=node.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom,cx:r.x+r.width/2,cy:r.y+r.height/2};});
const surface=mode=>page.locator(mode==='lab'?'.lab-page-surface':'.list-page').first();
try {
 assert.equal(problemTitle('[入门赛 #53] 买牛奶'),'买牛奶');assert.equal(problemTitle('[模板]【NOI2026】最短路'),'最短路');assert.equal(problemTitle('[a,b] 区间求和'),'[a,b] 区间求和');
 if(!process.env.TB_UI_FOCUS)for(const theme of ['dark','light'])for(const style of ['minimal','outlined','aurora','blueprint'])for(const opacity of [0,25,100]){
  const results=[];
  for(const mode of ['library','lists','list-problems','competitions','lab']){
   await open(mode);await page.evaluate(({theme,style,opacity})=>{const root=document.documentElement;root.dataset.theme=theme;root.dataset.panelStyle=style;document.querySelector('main').style.setProperty('--page-opacity',opacity+'%');},{theme,style,opacity});await page.waitForTimeout(80);
   const result=await surface(mode).evaluate(node=>{const css=getComputedStyle(node),canvas=document.createElement('canvas'),ctx=canvas.getContext('2d');ctx.fillStyle=css.backgroundColor;ctx.fillRect(0,0,1,1);return {background:css.backgroundColor,alpha:ctx.getImageData(0,0,1,1).data[3]/255,image:css.backgroundImage,radius:css.borderRadius};});
   assert(Math.abs(result.alpha-opacity/100)<.015,`${mode} ${theme}/${style}/${opacity}: ${JSON.stringify(result)}`);results.push(result);
  }
  for(const result of results.slice(1))assert.deepEqual(result,results[0],`${theme}/${style}/${opacity}: shared catalog surface`);
 }
 for(const viewport of [{width:1024,height:640},{width:1366,height:768},{width:1920,height:1080}]){
  await page.setViewportSize(viewport);await open('activity');const cells=page.getByRole('gridcell'),grid=await rect(page.locator('.activity-continuous-grid')),last=await rect(cells.last());
  const finalColumnTop=await cells.evaluateAll(nodes=>Math.min(...nodes.map(node=>node.getBoundingClientRect()).filter(r=>Math.abs(r.x-nodes.at(-1).getBoundingClientRect().x)<1).map(r=>r.y)));
  assert(Math.abs(grid.y-finalColumnTop)<1);assert(Math.abs(last.right-grid.right)<1);
  assert.deepEqual(await page.locator('.activity-month-marker').allTextContents(),Array.from({length:12},(_,i)=>String(i+1)));
  for(const marker of await page.locator('.activity-month-marker').all()){const text=await rect(marker),cell=await rect(marker.locator('..'));assert(Math.abs(text.cx-cell.cx)<1&&Math.abs(text.cy-cell.cy)<1);}
  await page.screenshot({path:`${out}/calendar-${viewport.width}.png`});
  await open('lists');const heading=await rect(page.locator('.training-list-directory'));
  for(const source of [false,true]){if(source)await page.getByRole('button',{name:'题单目录方式'}).click();await page.waitForTimeout(100);for(const row of await page.locator('.catalog-folder-row').all())assert(Math.abs((await rect(row)).height-heading.height)<1);}
  await open('mock');const heights=[];
  for(const mode of ['综合训练','专项训练','重现赛']){await page.getByRole('button',{name:mode,exact:true}).click();heights.push((await rect(page.locator('.mock-config'))).height);assert.equal(await page.locator('#tb-page-search .folder-icon-control').count(),0);assert.equal(await page.locator('#tb-page-search .sort-direction').count(),0);const button=await rect(page.getByRole('button',{name:'生成试卷',exact:true}));assert(button.bottom<viewport.height);await page.keyboard.press('Escape');}
  assert(Math.max(...heights)-Math.min(...heights)<1);
  await openMockSelection(page,'专项训练');await page.getByRole('listbox').getByRole('option',{name:'基础技巧',exact:true}).click();await page.getByRole('listbox').getByRole('option',{name:'前缀和',exact:true}).click();await page.getByRole('button',{name:'生成试卷',exact:true}).click();assert.deepEqual(await page.evaluate(()=>window.fixture.calls.find(call=>call.path==='contests/preview').body.tags),['前缀和']);
  await openMockSelection(page,'重现赛');
  for(let depth=0;depth<5;depth++){const options=page.getByRole('listbox').getByRole('option'),labels=await options.allTextContents();if(labels.some(text=>/^周赛 167/.test(text)))break;const folder=options.filter({hasText:/^(牛客|周赛)$/}).first();await folder.click();}
  const before=(await page.getByRole('listbox').getByRole('option').allTextContents()).filter(text=>/^周赛 \d/.test(text));assert(before.length===3);await page.getByRole('button',{name:'切换重现赛排序方向'}).click();const after=(await page.getByRole('listbox').getByRole('option').allTextContents()).filter(text=>/^周赛 \d/.test(text));assert.deepEqual(after,[...before].reverse());await page.keyboard.press('Escape');
  await open('settings');assert.equal(await page.getByRole('tab').count(),10);const tiles=await page.locator('.settings-tile').evaluateAll(nodes=>nodes.map(node=>{const r=node.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom};}));for(let i=0;i<tiles.length;i++)for(let j=i+1;j<tiles.length;j++)assert(!(Math.min(tiles[i].right,tiles[j].right)-Math.max(tiles[i].left,tiles[j].left)>1&&Math.min(tiles[i].bottom,tiles[j].bottom)-Math.max(tiles[i].top,tiles[j].top)>1),'settings tiles overlap');
  await page.screenshot({path:`${out}/settings-${viewport.width}.png`});await page.getByRole('tab',{name:'新手指引',exact:true}).click();await page.getByRole('button',{name:'打开指引'}).click();assert(await page.evaluate(()=>window.fixture.guideOpened));await page.getByRole('button',{name:'返回设置首页',exact:true}).click();await page.getByRole('tab',{name:'动画',exact:true}).click();await page.getByRole('checkbox',{name:'界面动效'}).uncheck();assert.equal(await page.locator('html').getAttribute('data-motion'),'off');
  await open('growth');const columns=page.locator('.progress-growth-columns');await columns.waitFor();const sizes=await columns.evaluate(node=>[...node.children].map(child=>child.getBoundingClientRect().width));assert(Math.abs(sizes[0]-sizes[1])<1);assert.equal(await columns.evaluate(node=>getComputedStyle(node).columnGap),'8px');
 }
 assert.deepEqual(errors,[]);await writeFile(out+'/report.json',JSON.stringify({ok:true,themes:2,styles:4,opacities:3,surfaces:5,viewports:3,calendarTopAligned:true,monthNumbersCentered:true,directoryRowsEqual:true,mockAreasEqual:true,topicToolbar:true,replayMenuSorting:true,settingsMenus:true,growthColumnsEqual:true},null,2));console.log('RELEASE 1.4.13 UI OK');
}finally{await browser.close();await vite.close();}

