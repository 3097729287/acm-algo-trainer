import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createServer} from 'vite';
import {chromium} from 'playwright';
import {trainingListModel} from '../src/lib/trainingListModel.js';
import {availablePages} from '../src/lib/featureUnlocks.js';
import {readingQueue,nextReading} from '../src/lib/lectureQueue.js';
import {FOUNDATION_LESSONS} from '../src/lib/learningCurriculum.js';
const lists=JSON.parse(fs.readFileSync('../data/library/training_lists.json','utf8')),rows=JSON.parse(fs.readFileSync('../data/library/problems.json','utf8')).map(row=>row.encoded);
const models=Array.from({length:6},(_,i)=>trainingListModel(lists,rows,'source',[],i+1));
const basic=models[0].organized.filter(item=>item.id.startsWith('curriculum:'));
assert.equal(basic.length,4);assert.deepEqual([...new Set(basic.map(item=>item.topicPath.at(-1)))],['01 编程基础']);
assert.equal(models[0].index.stats(basic.map(item=>item.id)).total,69);
assert(models[1].organized.some(item=>item.topicPath.includes('02 基础解题方法')));
assert(!models[1].organized.some(item=>item.topicPath.includes('03 搜索与图')));
assert(!availablePages(1).includes('library'));assert(!availablePages(2).includes('library'));assert(availablePages(3).includes('library'));
assert(availablePages(3).includes('competitions'));assert(!availablePages(3).includes('mock'));assert(availablePages(4).includes('mock'));assert(availablePages(5).includes('rankings'));assert(!availablePages(5).includes('duel'));assert(availablePages(6).includes('duel'));
const language=FOUNDATION_LESSONS.filter(item=>item.kind==='language');
assert.equal(readingQueue({lectures:[...language,{id:'unseen',sourceProblemIds:['future']}]}).length,23);
assert.equal(nextReading(readingQueue({lectures:language}),language.at(-1).id),null);
const vite=await createServer({cacheDir:'../.backups/next-150/vite-learning-guidance',server:{host:'127.0.0.1',port:0,watch:null}});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(12000);
try{
 await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/learning-guidance-fixture.html`);
 const catalog=page.locator('main:not([hidden]) .lectures-list');await catalog.locator('button').first().waitFor();
 assert.equal(await catalog.locator('button').count(),25);assert.equal(await catalog.getByText('尚未练习题的讲解').count(),0);assert.equal(await catalog.locator('button').filter({hasText:'以前读过的讲解'}).count(),1);
 assert.match(await catalog.locator('button').first().textContent(),/01.*C\+\+/);await page.screenshot({path:'../.backups/next-150/learning-route-dark.png'});
 await catalog.locator('button').first().click();await page.locator('.study-pane:not([hidden]) .lecture-markdown').waitFor();
 await page.getByRole('button',{name:'标记已学会',exact:true}).click();await page.waitForFunction(()=>guidanceFixture.prefs().learnedLectures.includes('lecture:foundation-io-basics'));
 await page.getByRole('button',{name:'下一篇',exact:true}).click();await page.waitForFunction(()=>guidanceFixture.state().tabs[0].id==='lecture:foundation-basic-arithmetic');
 assert.equal((await page.evaluate(()=>guidanceFixture.state())).tabs.length,1,'Next article replaces the current lecture tab');
 await page.locator('.study-pane:not([hidden]) .lecture-markdown').waitFor();await page.getByRole('button',{name:'下一篇',exact:true}).click();await page.waitForFunction(()=>guidanceFixture.state().tabs[0].id==='lecture:foundation-integer');
 assert((await page.evaluate(()=>guidanceFixture.prefs())).learnedLectures.includes('lecture:foundation-io-basics'));
 await page.evaluate(()=>guidanceFixture.home());await catalog.locator('button').first().waitFor();assert.equal(await catalog.locator('.lecture-learned').count(),2);
 await page.evaluate(()=>guidanceFixture.gallery());await page.getByRole('button',{name:'待达成',exact:true}).click();
 const medals=await page.locator('.achievement-badge svg').evaluateAll(nodes=>nodes.map(node=>({stage:node.getAttribute('data-medal-stage'),body:node.innerHTML.replace(/medal-[^ ]+/g,'id')})));
 assert.equal(new Set(medals.slice(5).map(item=>item.stage)).size,8,'Each difficulty tier advances the badge design');
 for(const width of [1440,760,390])for(const theme of ['dark','light']){
  await page.setViewportSize({width,height:900});await page.evaluate(t=>document.documentElement.dataset.theme=t,theme);
  const overflow=await page.locator('.achievement-reward-row').evaluateAll(nodes=>nodes.filter(node=>node.scrollWidth>node.clientWidth+1||[...node.children].some(child=>child.getBoundingClientRect().right>node.getBoundingClientRect().right+1)).length);
  assert.equal(overflow,0,`Reward text fits at ${width} ${theme}`);
  if(width===1440||width===390)await page.screenshot({path:`../.backups/next-150/medal-rewards-${width}-${theme}.png`});
 }
 assert.deepEqual(errors,[]);console.log('PASS ordered 23-part foundation route; reached-only applications and retained read progress; next replaces lecture; 69 beginner problems; level 1–6 entries; eight advancing medals; reward containment at three widths and both themes');
}finally{await browser.close();await vite.close();}
