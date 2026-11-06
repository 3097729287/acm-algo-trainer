import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const out='../.backups/frame-toolbar-20261107/checks';await mkdir(out,{recursive:true});
const server=await createServer({server:{host:'127.0.0.1',port:0,hmr:false},optimizeDeps:{entries:['tests/learned-lectures-fixture.html']}});await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
const colour=async locator=>{await page.mouse.move(0,0);await page.waitForTimeout(250);return locator.evaluate(n=>{const c=document.createElement('canvas');c.width=c.height=1;const ctx=c.getContext('2d');ctx.fillStyle=getComputedStyle(n).backgroundColor;ctx.fillRect(0,0,1,1);return [...ctx.getImageData(0,0,1,1).data];});};
const success=rgba=>assert(rgba[1]>rgba[0]+20&&rgba[1]>rgba[2]+10&&rgba[3]>25,'A learned row uses success green: '+JSON.stringify(rgba));
try{
 await page.goto(server.resolvedUrls.local[0]+'tests/learned-lectures-fixture.html');const entries=page.locator('.lecture-entry');await entries.first().waitFor();assert.equal(await page.locator('.lecture-learned').count(),0);
 await entries.first().click();await page.getByRole('button',{name:'标记已学会',exact:true}).click();const side=page.locator('.lectures-list>button.lecture-learned');await side.waitFor();const sideColour=await colour(side);success(sideColour);
 await page.evaluate(()=>learnedLectureFixture.reset());await page.locator('.lecture-entry.lecture-learned').waitFor();let mainColour=await colour(page.locator('.lecture-entry.lecture-learned'));success(mainColour);assert.equal(await page.locator('.lecture-entry.lecture-learned').count(),1);await page.screenshot({path:out+'/learned-catalogue-dark.png'});
 await page.reload();await page.locator('.lecture-entry.lecture-learned').waitFor();await page.evaluate(()=>document.documentElement.dataset.theme='light');mainColour=await colour(page.locator('.lecture-entry.lecture-learned'));success(mainColour);
 await page.locator('.lecture-entry.lecture-learned').click();await page.getByRole('button',{name:'取消已学会',exact:true}).click();await page.evaluate(()=>learnedLectureFixture.reset());await page.locator('.lecture-entry').first().waitFor();assert.equal(await page.locator('.lecture-entry.lecture-learned').count(),0);
 assert.deepEqual(errors,[]);const result={ok:true,realLearnedState:true,mainAndSidebar:true,darkAndLight:true,persistsReload:true,cancelRestores:true,sideColour,errors};await writeFile(out+'/learned-result.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));
}catch(error){await page.screenshot({path:out+'/failure.png'});throw error;}finally{await browser.close();await server.close();}
