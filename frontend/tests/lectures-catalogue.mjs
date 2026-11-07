import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';
import {FOUNDATION_LESSONS} from '../src/lib/learningCurriculum.js';
import {foundationLectures} from '../src/lib/algorithmLearning.js';
const out='../.backups/header-catalogue-audio-20261106/catalogue';await mkdir(out,{recursive:true});
const vite=await createServer({cacheDir:out+'/vite',optimizeDeps:{entries:['tests/lectures-lifecycle-fixture.html']},server:{host:'127.0.0.1',port:0,watch:null}});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage(),errors=[];page.on('pageerror',error=>errors.push(error.message));
try{
 await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/lectures-lifecycle-fixture.html?catalogue=1`);
 const catalogue=page.locator('.lecture-catalogue');await catalogue.locator('.learning-catalogue-entry').last().waitFor();
 assert.equal(await catalogue.locator('.learning-catalogue-entry').count(),foundationLectures(FOUNDATION_LESSONS).length+2,'Every lesson in the existing From Zero queue remains in the shared catalogue');
 assert.equal(await page.locator('.lectures-intro,.lectures-detail,.lecture-curriculum-info,.lecture-role,.lecture-prerequisite-preview').count(),0,'No introduction or redundant item details');
 assert.equal(await page.getByRole('button',{name:'阅读第一篇',exact:true}).count(),0);
 const groups=await catalogue.locator('.learning-catalogue-group>h3').allTextContents();assert.equal(new Set(groups).size,groups.length,'Each section occurs once');
 const shapes=await catalogue.locator('.learning-catalogue-entry').evaluateAll(nodes=>nodes.map(node=>({icons:node.querySelectorAll(':scope>svg').length,title:node.getAttribute('aria-label'),text:node.textContent})));assert(shapes.every(entry=>entry.icons===2&&entry.title&&entry.text),'All entries share the existing book/title/arrow row');
 const layouts=[];
 for(const width of [2048,1280,900,640,390])for(const font of [16,20,24]){
  await page.setViewportSize({width,height:1000});await page.evaluate(font=>document.documentElement.style.fontSize=font+'px',font);
  const layout=await catalogue.evaluate(node=>({catalogueOverflow:node.scrollWidth>node.clientWidth+1,documentOverflow:document.documentElement.scrollWidth>innerWidth+1,items:[...node.querySelectorAll('.learning-catalogue-entry')].map(entry=>{const box=entry.getBoundingClientRect(),title=entry.querySelector(':scope>span').getBoundingClientRect();return {x:box.x,y:box.y,width:box.width,height:box.height,titleBottom:title.bottom,bottom:box.bottom,overflow:entry.scrollWidth>entry.clientWidth+1};})}));
  assert(!layout.catalogueOverflow&&!layout.documentOverflow,`No horizontal overflow at ${width}/${font}`);assert(layout.items.every(item=>!item.overflow&&item.titleBottom<=item.bottom+.5),`Titles wrap inside their rows at ${width}/${font}`);
  layouts.push({width,font,items:layout.items.length});
  if(font===16&&[2048,640].includes(width))await page.screenshot({path:out+`/catalogue-${width}.png`});
 }
 await page.setViewportSize({width:1280,height:900});await page.evaluate(()=>document.documentElement.style.fontSize='16px');
 const search=page.getByRole('textbox',{name:'搜索从零讲知识',exact:true});await search.fill('用下标定位');assert.equal(await catalogue.locator('.learning-catalogue-entry').count(),1);assert.equal(await catalogue.locator('.learning-catalogue-entry').textContent(),'数组');
 await catalogue.getByRole('button',{name:'数组',exact:true}).click();await page.locator('.lecture-markdown').waitFor();assert((await page.locator('.lecture-markdown').textContent()).includes('用下标定位'),'The original full lecture is retained');
 await page.getByRole('button',{name:'从零讲全屏',exact:true}).click();await page.locator('.lecture-reading-full').waitFor();await page.keyboard.press('Escape');assert.equal(await page.locator('.lecture-reading-full').count(),0);
 await page.addInitScript(()=>window.__tbAdmin=true);await page.setViewportSize({width:2048,height:1152});await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/lectures-lifecycle-fixture.html?catalogue=1&fresh=1`);await catalogue.locator('.learning-catalogue-entry').last().waitFor();assert.equal(await catalogue.locator('.learning-catalogue-entry').count(),foundationLectures(FOUNDATION_LESSONS).length+2,'Administrator sees the real full catalogue even without any encountered problems');for(const title of ['基础学习','通用算法','题目中的应用'])await catalogue.getByRole('heading',{name:title,exact:true}).waitFor();await page.screenshot({path:out+'/admin-full-catalogue.png'});
 assert.deepEqual(errors,[]);const result={ok:true,sharedCatalogueRows:true,introductionRemoved:true,allLessonsPreserved:true,groups,layouts,originalTitleSearch:true,fullLectureAndFullscreen:true,errors};await writeFile(out+'/result.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));
}catch(error){await page.screenshot({path:out+'/failure.png'});throw error;}finally{await browser.close();await vite.close();}
