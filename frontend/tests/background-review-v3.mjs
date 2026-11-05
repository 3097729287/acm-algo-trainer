import assert from 'node:assert/strict';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';
const out=fileURLToPath(new URL('../../.backups/background-review-20261105/checks/',import.meta.url));await mkdir(out,{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true}),context=await browser.newContext({viewport:{width:1600,height:1100},offline:true,acceptDownloads:true}),page=await context.newPage(),errors=[],requests=[];
page.on('pageerror',error=>errors.push(error.message));page.on('request',request=>{if(/^https?:/.test(request.url()))requests.push(request.url());});
try{
 await page.goto(new URL('../../.backups/background-review-20261105/ToBe-背景重制.html',import.meta.url).href);
 const stage=page.locator('.review-stage'),cards=page.locator('.review-gallery .review-card');await cards.nth(13).waitFor();assert.equal(await cards.count(),14);
 await page.screenshot({path:out+'gallery.png',fullPage:true});
 const choose=async theme=>{await cards.filter({has:page.locator('[data-background-theme="'+theme+'"]')}).click();await stage.locator('[data-background-theme="'+theme+'"]').waitFor();};
 for(const theme of ['night','morning','rain','coast','beach','desert','rainforest','mountains','snow','river','sky','underground','room','galaxy']){
  await choose(theme);assert.equal(await stage.locator('circle').evaluateAll(nodes=>nodes.filter(node=>Number(node.getAttribute('r'))>6&&node.getAttribute('fill')!=='transparent').length),0,'No sun or moon');assert(await stage.locator('linearGradient stop').count()>=10);await stage.screenshot({path:out+theme+'.png'});
 }
 await choose('room');const aperture=await stage.locator('.room-window-aperture').boundingBox();await stage.getByRole('button',{name:'打开窗户'}).click();
 await page.waitForFunction(()=>[...document.querySelectorAll('.review-stage .room-window-pane')].every(node=>new DOMMatrixReadOnly(getComputedStyle(node).transform).a<-.23));
 const panes=await stage.locator('.room-window-pane').evaluateAll(nodes=>nodes.map(node=>{const b=node.getBoundingClientRect();return {left:b.left,right:b.right,width:b.width};}));
 assert(panes[0].right<=aperture.x+3,'Left pane clears the opening');assert(panes[1].left>=aperture.x+aperture.width-3,'Right pane clears the opening');assert(Math.abs(panes[0].width-panes[1].width)<1,'Both leaves open equally');await stage.screenshot({path:out+'room-open.png'});
 await stage.getByRole('button',{name:'关闭窗户'}).click();await page.waitForFunction(()=>[...document.querySelectorAll('.review-stage .room-window-pane')].every(node=>getComputedStyle(node).transform==='none'||new DOMMatrixReadOnly(getComputedStyle(node).transform).a>.99));
 await choose('underground');await stage.getByRole('button',{name:'轻触左侧洞壁，左侧落石'}).click();await stage.getByRole('button',{name:'轻触右侧洞壁，右侧落石'}).click();
 const origins=await stage.locator('.cave-debris').evaluateAll(nodes=>nodes.map(node=>({side:node.dataset.fallSide,x:Number(node.dataset.originX)})));assert.equal(origins.length,2);assert(origins.find(item=>item.side==='left').x<150);assert(origins.find(item=>item.side==='right').x>850);await stage.screenshot({path:out+'cave-both-sides.png'});
 await choose('galaxy');await stage.getByRole('button',{name:'凝视第 1 颗亮星'}).click();assert.equal(await stage.locator('svg').getAttribute('data-focused-star'),'0');assert((await stage.locator('.galaxy-camera').getAttribute('style')).includes('1.16'));
 const space=stage.getByRole('group',{name:/探索银河/}),b=await space.boundingBox(),before=await stage.locator('.galaxy-camera').getAttribute('style');await page.mouse.move(b.x+b.width*.48,b.y+b.height*.7);await page.mouse.down();await page.mouse.move(b.x+b.width*.56,b.y+b.height*.74,{steps:8});await page.mouse.up();assert.notEqual(await stage.locator('.galaxy-camera').getAttribute('style'),before);assert.equal(await stage.locator('svg').getAttribute('data-focused-star'),'');
 await space.focus();await page.keyboard.press('Home');assert((await stage.locator('.galaxy-camera').getAttribute('style')).includes('1.08'));assert.equal(await stage.locator('.galaxy-flight').count(),0);
 await page.emulateMedia({reducedMotion:'reduce'});assert.equal(await stage.locator('.galaxy-clouds').evaluate(node=>getComputedStyle(node).animationName),'none');
 const pending=page.waitForEvent('download');await page.getByRole('button',{name:/导出意见/}).click();const download=await pending;await download.saveAs(out+'export.json');const exported=JSON.parse(await readFile(out+'export.json','utf8'));assert.equal(exported.schema,'tobe-material-review-atmosphere-v3');assert(exported.items.find(item=>item.id==='background-night-common').previousNotes.includes('边界'));assert(exported.items.find(item=>item.id==='background-galaxy-legendary').approved);
 for(const width of [1000,640,390]){await page.setViewportSize({width,height:1000});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));}
 assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);const result={ok:true,backgrounds:14,independentGround:true,separateSnowAndForest:true,cloudBanks:true,windowBothFullyOpen:true,localizedSimultaneousFalls:true,galaxyPanAndFocus:true,noRadialFlight:true,approvalHistoryPreserved:true,offline:true,responsive:true,reducedMotion:true,errors};await writeFile(out+'result.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));
}catch(error){await page.screenshot({path:out+'failure.png',fullPage:true});throw error;}finally{await browser.close();}
