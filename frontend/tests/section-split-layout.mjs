import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {chromium} from 'playwright';
import {createServer} from 'vite';
import {emptyStudyBrowser,openStudyTab,splitStudyTab,studyGroups,studySnapshot,restoreStudyBrowser} from '../src/lib/learningBrowser.js';
import {resizeSectionSplit,sectionSplitLayout,SECTION_DIVIDER_WIDTH} from '../src/lib/sectionSplitLayout.js';

const out='../.backups/split-bounds-20261105';await mkdir(out,{recursive:true});
let state=['mine','library','training-lists'].reduce((value,id)=>openStudyTab(value,{kind:'panel',id,title:id}),emptyStudyBrowser());state=splitStudyTab(state,'panel:library');
for(const position of [-10000,10000,750]){
 const next=resizeSectionSplit(state,0,position,1500,[680,680],{snap:0}),layout=sectionSplitLayout(studyGroups(next),1500,[680,680]);
 assert(layout.widths.every(width=>width>=680-.001));assert(Math.abs(layout.widths.reduce((sum,width)=>sum+width,0)+SECTION_DIVIDER_WIDTH-1500)<.001);assert.deepEqual(restoreStudyBrowser(studySnapshot(next)),next);
}
const skew=studyGroups(state).map((group,index)=>({...group,weight:index?1:99}));assert.equal(sectionSplitLayout(skew,1500,[680,680]).widths[1],680);
assert(sectionSplitLayout(skew,1200,[680,680]).stacked);assert.equal(resizeSectionSplit(state,0,900,1200,[680,680]),state);
const triple=splitStudyTab(state,'panel:training-lists',{targetGroupId:state.groups[0].id});
const triples=studyGroups(triple),mins=triples.map(group=>group.tabs.includes('panel:training-lists')?420:680);
for(const index of [0,1]){const next=resizeSectionSplit(triple,index,10000,2000,mins,{snap:0}),layout=sectionSplitLayout(studyGroups(next),2000,mins);assert(layout.widths.every((width,at)=>width>=mins[at]-.001));assert(Math.abs(layout.widths.reduce((sum,width)=>sum+width,0)+2*SECTION_DIVIDER_WIDTH-2000)<.001);}
assert.deepEqual(sectionSplitLayout([triples[0]],300,[680]).widths,[300]);

const vite=await createServer({cacheDir:out+'/vite',optimizeDeps:{entries:['tests/section-split-fixture.html']},server:{host:'127.0.0.1',port:0,watch:null}});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1640,height:920}}),errors=[];page.on('pageerror',error=>errors.push(error.message));page.setDefaultTimeout(12000);
const fixture=vite.resolvedUrls.local[0]+'tests/section-split-fixture.html',workspace=page.locator('[data-section=training]'),panes=workspace.locator(':scope>.section-pane');
const contained=async()=>page.evaluate(()=>{
 const root=document.querySelector('[data-section=training]'),box=root.getBoundingClientRect(),panes=[...root.querySelectorAll(':scope>.section-pane')];
 const violations=[];
 for(const pane of panes){const bounds=pane.getBoundingClientRect();if(bounds.left<box.left-.75||bounds.right>box.right+.75||bounds.top<box.top-.75||bounds.bottom>box.bottom+.75)violations.push('pane');
  for(const table of pane.querySelectorAll('.section-document:not([hidden]) .problem-table')){const rect=table.getBoundingClientRect(),parent=table.closest('.table-scroll').getBoundingClientRect();if(rect.right>parent.right+.75||table.scrollWidth>table.clientWidth+1)violations.push('table');const title=table.querySelector('tr[data-id] .title-cell');if(title&&title.getBoundingClientRect().width<Math.min(170,parent.width*.3))violations.push('title squeezed');}
  for(const footer of pane.querySelectorAll('.section-document:not([hidden]) [data-pagination]')){const rect=footer.getBoundingClientRect();for(const action of footer.querySelectorAll('.pagination-actions button,.pagination-position')){const b=action.getBoundingClientRect();if(b.left<rect.left-.75||b.right>rect.right+.75)violations.push('pagination');}}
  for(const action of pane.querySelectorAll('.section-document:not([hidden]) td.row-actions .row-icon')){const b=action.getBoundingClientRect(),cell=action.parentElement.getBoundingClientRect();if(b.width&&((b.right>cell.right+.75)||(b.left<cell.left-.75)))violations.push('row action');}
 }
 return {violations,documentOverflow:document.documentElement.scrollWidth>innerWidth+1,workspaceOverflow:root.scrollWidth>root.clientWidth+1,stacked:root.dataset.stacked==='true',widths:panes.map(pane=>pane.getBoundingClientRect().width)};
});
const verify=async()=>{const value=await contained();assert.deepEqual(value.violations,[],JSON.stringify(value));assert.equal(value.documentOverflow,false);assert.equal(value.workspaceOverflow,false);return value;};
const drag=async(x,index=0)=>{const separator=workspace.getByRole('separator').nth(index),box=await separator.boundingBox();await page.mouse.move(box.x+box.width/2,box.y+box.height/2);await page.mouse.down();await page.mouse.move(x,box.y+box.height/2,{steps:12});await page.mouse.up();};
try{
 await page.goto(fixture);await page.getByRole('tab',{name:'我的训练',exact:true}).click();await page.getByRole('tabpanel',{name:'我的训练',exact:true}).locator('tbody tr[data-id]').first().waitFor();
 await workspace.getByRole('tab',{name:'题库',exact:true}).click();let value=await verify();assert.equal(value.stacked,false);
 const first=await panes.first().boundingBox(),second=await panes.nth(1).boundingBox(),leftTable=await panes.first().locator('.list-page').boundingBox(),rightTable=await panes.nth(1).locator('.list-page').boundingBox();assert(second.x-first.x-first.width<=5.5);assert(rightTable.x-leftTable.x-leftTable.width<=5.5,'The seam includes no duplicate panel padding');
 await page.screenshot({path:out+'/equal-panes.png'});
 await drag(1638);value=await verify();assert(Math.abs(value.widths[1]-680)<1);const upper=value.widths[0];await drag(1638);assert(Math.abs((await verify()).widths[0]-upper)<1,'Dragging beyond the boundary stops');await page.screenshot({path:out+'/right-limit.png'});
 await drag(2);value=await verify();assert(Math.abs(value.widths[0]-680)<1);await page.screenshot({path:out+'/left-limit.png'});
 const separator=workspace.getByRole('separator');await separator.focus();for(let index=0;index<40;index++)await page.keyboard.press('ArrowRight');value=await verify();assert(Math.abs(value.widths[1]-680)<1);await page.keyboard.press('Home');value=await verify();assert(Math.abs(value.widths[0]-value.widths[1])<1);
 await drag(1638);await page.reload();await panes.nth(1).waitFor();await page.getByRole('tab',{name:'题库',exact:true}).click();value=await verify();assert(Math.abs(value.widths[1]-680)<1,'The saved maximum remains contained');
 for(const font of [18,22]){await page.evaluate(font=>window.splitFixture.setPrefs(previous=>({...previous,fontSize:font})),font);await page.waitForFunction(font=>window.splitFixture.prefs.fontSize===font,font);await verify();}
 await page.evaluate(()=>window.splitFixture.setPrefs(previous=>({...previous,fontSize:15})));await page.setViewportSize({width:1180,height:920});await page.waitForFunction(()=>document.querySelector('[data-section=training]').dataset.stacked==='true');value=await verify();assert(value.widths.every(width=>Math.abs(width-1180)<1));await page.screenshot({path:out+'/narrow-stacked.png'});
 for(const width of [900,640,390]){await page.setViewportSize({width,height:920});await verify();}await page.screenshot({path:out+'/phone-stacked.png'});
 await page.setViewportSize({width:1640,height:920});await page.waitForFunction(()=>document.querySelector('[data-section=training]').dataset.stacked==='false');await verify();
 await page.evaluate(()=>localStorage.removeItem('split-fixture'));await page.goto(fixture+'?skew');await page.getByRole('tab',{name:'题库',exact:true}).click();value=await verify();assert(Math.abs(value.widths[1]-680)<1,'Old oversqueezed layouts are clamped before display');
 await page.evaluate(()=>localStorage.removeItem('split-fixture'));await page.setViewportSize({width:2100,height:1000});await page.goto(fixture+'?three');await panes.nth(2).waitFor();await page.getByRole('tab',{name:'题库',exact:true}).click();assert.equal(await panes.count(),3);for(const index of [0,1]){await drag(2098,index);await verify();await drag(2,index);await verify();}await page.screenshot({path:out+'/three-panes.png'});
 await page.setViewportSize({width:1640,height:920});await page.waitForFunction(()=>document.querySelector('[data-section=training]').dataset.stacked==='true');await verify();assert.equal(await panes.count(),3,'Narrowing keeps every tab and pane');
 assert.deepEqual(errors,[]);const result={ok:true,seamPixels:5,contentMinimum:680,pointerClamped:true,keyboardClamped:true,oldRatiosClamped:true,tableFits:true,rowActionsContained:true,paginationContained:true,largeFonts:true,stackOnInsufficientWidth:true,restoreHorizontal:true,threePanes:true,errors};await writeFile(out+'/result.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));
}catch(error){await page.screenshot({path:out+'/failure.png'});console.error(await contained());throw error;}finally{await browser.close();await vite.close();}
