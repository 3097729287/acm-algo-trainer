import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {realpathSync} from 'node:fs';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const vite=await createServer({server:{host:'127.0.0.1',port:0,fs:{allow:[process.cwd(),realpathSync('node_modules')]}}});await vite.listen();
const {filterRows}=await vite.ssrLoadModule('/src/models/workspaceModel.js');
const browser=await chromium.launch({channel:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1366,height:768}}),errors=[];
page.setDefaultTimeout(12000);page.on('pageerror',e=>errors.push(e.message));
const base=vite.resolvedUrls.local[0],out='../.backups/local-1412/ui';await mkdir(out,{recursive:true});
const open=async mode=>{await page.goto(base+'tests/release-1412-fixture.html?view='+mode);await page.waitForTimeout(150);};
const rect=locator=>locator.evaluate(x=>{const r=x.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom,cx:r.x+r.width/2,cy:r.y+r.height/2};});
try{
 await page.clock.install({time:new Date('2026-10-26T04:00:00Z')});
 for(const viewport of [{width:1366,height:768},{width:1024,height:640},{width:1920,height:1080}]){
  await page.setViewportSize(viewport);const footers=[];
  for(const mode of ['library','records','activity','lists','competitions']){
   await open(mode);await page.locator('[data-pagination]').waitFor();
   const footer=page.locator('[data-pagination]'),f=await rect(footer),main=await rect(page.locator('main'));
   assert(Math.abs(f.right-(main.right-12))<2,mode+' right '+JSON.stringify({f,main}));
   assert(Math.abs(f.bottom-(main.bottom-12))<2,mode+' bottom '+JSON.stringify({f,main}));
   for(const button of await footer.locator('button').all()){
    const icon=await rect(button.locator('svg')),text=await rect(button.locator('span'));
    assert(Math.abs(icon.cy-text.cy)<.6,mode+' icon/text alignment');
   }
   footers.push({mode,...f});
  }
  assert.equal(new Set(footers.map(f=>f.height)).size,1);
  await open('activity');assert.equal(await page.getByRole('gridcell').count(),365);
  const first=await rect(page.getByRole('gridcell').first()),last=await rect(page.getByRole('gridcell').last()),grid=await rect(page.locator('.activity-continuous-grid'));
  assert.match(await page.getByRole('gridcell').first().getAttribute('aria-label'),/^2026-01-01/);
  assert.match(await page.getByRole('gridcell').last().getAttribute('aria-label'),/^2026-12-31/);
  assert(Math.abs(first.x-grid.x)<1&&Math.abs(first.y-grid.y)<1);
  assert(Math.abs(last.right-grid.right)<1);const finalColumn=page.getByRole('gridcell').filter({hasNot:page.locator('span.never')});const tops=await finalColumn.evaluateAll(nodes=>nodes.map(node=>node.getBoundingClientRect()).filter(r=>Math.abs(r.right-nodes.at(-1).getBoundingClientRect().right)<1).map(r=>r.y));assert(Math.abs(Math.min(...tops)-grid.y)<1);
  assert.equal(await page.locator('.activity-month-marker').count(),12);
  assert.deepEqual(await page.locator('.activity-month-marker').allTextContents(),Array.from({length:12},(_,i)=>String(i+1)));
  for(const theme of ['dark','light']){
   await page.evaluate(theme=>document.documentElement.dataset.theme=theme,theme);
   const colors=[];
   for(let n=1;n<=25;n++){const cell=page.getByRole('gridcell',{name:`2026-10-${String(n).padStart(2,'0')}，${n} 题通过`,exact:true});colors.push(await cell.evaluate(x=>getComputedStyle(x).backgroundColor));}
   assert.equal(new Set(colors).size,25,'five distinct shades in each palette');
  }
  await page.evaluate(()=>document.documentElement.dataset.theme='dark');await page.clock.runFor(250);
  await page.screenshot({path:`${out}/activity-${viewport.width}.png`});
 }
 await page.getByRole('combobox',{name:'活动年份'}).selectOption('2024');assert.equal(await page.getByRole('gridcell').count(),366);await page.getByRole('gridcell',{name:'2024-02-29，0 题通过',exact:true}).click();
 await page.getByRole('textbox',{name:'搜索活动日期'}).fill('2026/10/08');await page.getByRole('gridcell',{name:'2026-10-08，8 题通过',exact:true}).waitFor();await page.waitForFunction(()=>document.querySelector('.activity-selected-count b')?.textContent==='8');
 await open('random');await page.getByRole('button',{name:'随机单题',exact:true}).click();await page.clock.runFor(100);
 const popup=await rect(page.getByRole('alertdialog')),anchor=await rect(page.getByRole('button',{name:'随机单题',exact:true}));assert(popup.width<=290&&popup.height<=115);assert(Math.abs(popup.x-Math.max(12,Math.min(anchor.cx-popup.width/2,page.viewportSize().width-popup.width-12)))<1,JSON.stringify({popup,anchor}));await page.screenshot({path:out+'/confirm.png'});await page.getByRole('button',{name:'取消',exact:true}).click();assert.equal(await page.evaluate(()=>Boolean(window.fixture.chosen)),false);
 await open('lab');assert.deepEqual(await page.locator('.lab-catalog h3').allTextContents(),['排序基础','前缀和与差分','双指针算法','分治与随机化','桶与按位处理','BFS 广度优先搜索','DFS 深度优先搜索','并查集','Dijkstra 最短路','背包 DP']);
 await page.screenshot({path:out+'/lab.png'});
 for(const viewport of [{width:1366,height:768},{width:1024,height:640},{width:1920,height:1080}]){
  await page.setViewportSize(viewport);await open('mock');
  const geometries=[];
  for(const mode of ['综合训练','专项训练']){
   await page.getByRole('button',{name:mode,exact:true}).click();const slider=page.getByRole('slider',{name:'训练最低难度滑块'}),rail=await rect(slider),values=await rect(page.locator('.difficulty-range-values'));
   assert.equal(await slider.getAttribute('min'),'800');assert(rail.width<=480&&rail.width>=220);assert(values.bottom<=rail.y+1);assert(Math.abs(values.cx-rail.cx)<1);geometries.push(rail);
   if(mode==='专项训练'){const topic=await rect(page.getByRole('combobox',{name:'专项训练知识点'}));assert(topic.bottom<rail.y);assert.equal(await page.locator('.mock-config .folder-icon-control').count(),0);}
   const button=await rect(page.getByRole('button',{name:'生成试卷',exact:true})),duration=await rect(page.locator('.training-duration-summary'));assert(duration.y>=button.bottom);assert(Math.abs(button.cx-duration.cx)<1);assert(duration.bottom<viewport.height,'generate controls stay visible');
   await page.screenshot({path:`${out}/mock-${mode}-${viewport.width}.png`});
  }
  assert(Math.abs(geometries[0].width-geometries[1].width)<1&&Math.abs(geometries[0].x-geometries[1].x)<1);
  const slider=page.getByRole('slider',{name:'训练最高难度滑块'}),box=await slider.boundingBox(),unit=(box.width-12)/32;
  await page.mouse.move(box.x+6+unit*6,box.y+box.height/2);await page.mouse.down();await page.mouse.move(box.x+6+unit*13,box.y+box.height/2);await page.mouse.up();assert.equal(await page.getByRole('spinbutton',{name:'训练最高难度',exact:true}).inputValue(),'2100');
  await page.getByRole('button',{name:'重现赛',exact:true}).click();assert.equal(await page.getByRole('slider').count(),0);
 }
 await open('rankings');await page.locator('.ranking-identity .profile-avatar-face img').nth(1).waitFor();assert.equal(await page.locator('.ranking-identity .profile-avatar-face img').count(),2);
 assert.deepEqual(await page.locator('.ranking-identity [role=meter]').evaluateAll(xs=>xs.map(x=>Number(x.getAttribute('aria-valuenow')))),[40,75]);await page.screenshot({path:out+'/rankings.png'});
 for(const style of ['minimal','outlined','aurora','blueprint']){
  await open('competitions');await page.evaluate(value=>document.documentElement.dataset.panelStyle=value,style);
  const cards=page.locator('.competition-card');await cards.first().waitFor();
  const boxes=await cards.evaluateAll(xs=>xs.slice(0,2).map(x=>{const r=x.getBoundingClientRect(),s=getComputedStyle(x);return {y:r.y,bottom:r.bottom,radius:s.borderRadius,top:s.borderTopWidth,margin:s.marginBottom,image:s.backgroundImage};}));
  assert(Math.abs(boxes[1].y-boxes[0].bottom)<1,style+' contiguous competition rows');
  assert.equal(boxes[0].radius,'0px');assert.equal(boxes[0].top,'0px');assert.equal(boxes[0].margin,'0px');assert.equal(boxes[0].image,'none');
  await cards.first().hover();await page.clock.runFor(200);assert.match(await cards.first().evaluate(x=>getComputedStyle(x).boxShadow),/inset/);
 }
 await open('list-problems');const question=page.locator('.training-problem-row').first();await question.waitFor();
 await question.locator('td').last().click();await question.focus();await page.keyboard.press('Enter');await question.locator('button').click();
 assert.equal(await page.evaluate(()=>window.fixture.calls.filter(call=>call.train).length),3,'row blank space, keyboard and title each enter once');
 assert.deepEqual(filterRows([{id:'a',title:'基础',difficulty:800}],{min:0,max:700}).map(r=>r.id),['a']);
 assert.equal(filterRows([{id:'unknown',title:'未知',difficulty:null}],{min:800,max:10000}).length,1);
 assert.deepEqual(errors,[]);await writeFile(out+'/report.json',JSON.stringify({ok:true,viewports:3,paginationSurfaces:5,yearBoundaries:true,leapYear:true,monthMarkers:12,heatColors:25,firstAcRegression:true,compactConfirm:true,courseOrder:true,mockLayout:true,publicAvatarAndXp:true},null,2));
 console.log('1.4.12 UI passed: aligned pagination, full years, 25 colors, compact confirmation, learning order, mock controls, shared avatars and XP.');
}finally{await browser.close();await vite.close();}
