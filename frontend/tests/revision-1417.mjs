import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {realpathSync} from 'node:fs';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const server=await createServer({server:{host:'127.0.0.1',port:0,fs:{allow:[process.cwd(),realpathSync('node_modules')]}}});await server.listen();
const browser=await chromium.launch({channel:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1920,height:1080}}),errors=[];
page.setDefaultTimeout(15000);page.on('pageerror',e=>errors.push(e.message));
const base=server.resolvedUrls.local[0],out='../.backups/local-1417/ui';await mkdir(out,{recursive:true});
const open=async view=>page.goto(base+'tests/revision-1417-fixture.html?view='+view);
try{
 await page.clock.install({time:new Date('2026-10-26T09:00:00Z')});
 await open('activity');await page.locator('.activity-week-summary').first().waitFor();
 assert.match(await page.locator('.activity-week-summary').first().innerText(),/第43周/);
 assert.equal(await page.locator('[data-week="2026-10-26"] b').innerText(),'2');
 const previous=page.locator('[data-week="2026-10-19"]');assert.equal(await previous.locator('b').innerText(),'35');
 assert.match(await previous.getByRole('meter').getAttribute('aria-valuetext'),/每段 35 题/);
 assert.equal(await previous.locator('.activity-progress-segment i').first().evaluate(x=>x.style.width),'100%');
 await page.screenshot({path:out+'/weekly-activity.png'});
 await open('lists');await page.getByRole('button',{name:'题单目录方式',exact:true}).click();
 await page.getByRole('textbox',{name:'搜索题单或题目'}).fill('排序专项');
 await page.locator('.training-card-open').filter({hasText:'排序专项'}).click();
 assert.equal(await page.locator('.training-tag-browser,.training-active-tags,.training-list-tags').count(),0);
 await open('rankings');await page.locator('.ranking-identity').first().waitFor();await page.clock.runFor(3100);
 const other=page.locator('.ranking-identity').filter({hasText:'有头像的用户'});await other.locator('.profile-avatar-face img').waitFor();
 assert.equal(await other.locator('.profile-xp-ring').getAttribute('aria-valuenow'),'25');
 assert.match(await other.locator('.profile-xp-ring').getAttribute('aria-valuetext'),/100\/400/);assert.equal(await page.evaluate(()=>window.avatarCalls),2);
 const old=page.locator('.ranking-identity').filter({hasText:'旧版用户'});assert.doesNotMatch(await old.innerText(),/XP|经验待同步/);assert.equal(await old.locator('.profile-xp-ring').count(),0);
 await page.screenshot({path:out+'/public-appearance.png'});
 await page.goto(base+'tests/release-1411-fixture.html?view=lab');
 for(const viewport of [{width:1024,height:640},{width:1366,height:768},{width:1920,height:1080}]){
  await page.setViewportSize(viewport);
  for(const id of ['sorting-basics','prefix-difference','bfs','knapsack']){
   await page.evaluate(id=>window.fixture.seed({learningPaths:{activePath:id,[id]:{mode:'learn'}}}),id);
   await page.locator('.lab-course-header').waitFor();
   const box=await page.locator('.lab-course-header').evaluate(header=>{
    const h=header.closest('.algorithm-lab').getBoundingClientRect(),left=header.querySelector('.lab-header-actions').getBoundingClientRect(),right=header.querySelector('.lab-course-tools').getBoundingClientRect();
    return {leftGap:left.left-h.left,rightGap:h.right-right.right,borders:[...header.querySelectorAll('.lab-icon-button,.lab-menu-toggle')].map(b=>getComputedStyle(b).borderTopWidth)};
   });
   assert(box.leftGap<1&&box.rightGap<1,JSON.stringify({id,...box}));assert(box.borders.every(x=>x==='0px'));
  }
 }
 await page.screenshot({path:out+'/course-header.png'});
 assert.deepEqual(errors,[]);await writeFile(out+'/report.json',JSON.stringify({ok:true,weeklyTotals:true,listTagsRemoved:true,publicAvatarRetry:true,publicXp:true,headerEdges:true,viewports:3},null,2));
 console.log('PASS: weekly totals, removed list tags, avatar retry, XP and course header');
}catch(error){await page.screenshot({path:out+'/failure.png'});console.error(errors);throw error;}finally{await browser.close();await server.close();}
