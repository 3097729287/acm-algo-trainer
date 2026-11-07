import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const out='../.backups/direct-fixes-20261105';await mkdir(out,{recursive:true});
const vite=await createServer({cacheDir:out+'/tasks-vite',optimizeDeps:{entries:['tests/calendar-tasks-fixture.html']},server:{host:'127.0.0.1',port:0,watch:null}});await vite.listen();
const browser=await chromium.launch({channel:'msedge',headless:true}),page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));const proof=[];let ok=false;
try{
 for(const width of[2048,1294,800,430])for(const theme of['dark','light']){
  await page.setViewportSize({width,height:1152});await page.goto(vite.resolvedUrls.local[0]+'tests/calendar-tasks-fixture.html');await page.locator('.task-now').waitFor();await page.evaluate(theme=>document.documentElement.dataset.theme=theme,theme);
  assert.equal(await page.locator('.task-week-strip,.task-week-days').count(),0,'The redundant overview week/date strip is removed');
  assert.equal(await page.locator('.task-current-step h3').textContent(),'原有学习任务','Future contests do not replace the current study task');
  const upcoming=page.locator('.task-next').getByRole('button',{name:/日历里的正式比赛/});await upcoming.click();assert.equal(await page.evaluate(()=>calendarCalls.at(-1).kind),'calendar-contest');
  await page.getByRole('tab',{name:'计划',exact:true}).click();const rows=page.locator('.summary-week tbody tr');assert.equal(await rows.count(),3);assert.equal(await page.getByRole('button',{name:'推迟 日历里的正式比赛'}).count(),0,'An official start time cannot be postponed');
  assert((await rows.allTextContents()).some(row=>row.includes('原有复习任务')));assert((await rows.allTextContents()).some(row=>row.includes('尚未开始')));
  await page.evaluate(()=>calendarFixture.live());await page.getByRole('tab',{name:'概况',exact:true}).click();
  assert.equal(await page.locator('.task-current-step h3').textContent(),'日历里的正式比赛');await page.getByRole('button',{name:'开始比赛',exact:true}).click();
  await page.evaluate(()=>calendarFixture.running());const resume=page.getByRole('button',{name:'回到比赛',exact:true});assert(await resume.isEnabled());await resume.click();
  await page.getByRole('tab',{name:'计划',exact:true}).click();
  await page.evaluate(()=>calendarFixture.complete());await page.locator('.summary-week tbody tr[data-done=true]').waitFor();
  await page.getByRole('tab',{name:'概况',exact:true}).click();assert((await page.locator('.task-recent').textContent()).includes('日历里的正式比赛'));assert((await page.locator('.task-recent').textContent()).includes('1 / 3'));
  await page.evaluate(()=>calendarFixture.switchOwner());assert(!(await page.locator('.task-recent').textContent()).includes('日历里的正式比赛'),'Another account cannot inherit participation');
  if(width===2048||width===430)await page.screenshot({path:`${out}/tasks-${width}-${theme}.png`});proof.push({width,theme,weekStripRemoved:true,studyPreserved:true,calendarEntryWorks:true,liveStartAndResume:true,participationCompletion:true,accountIsolation:true});
 }
 await page.evaluate(()=>calendarFixture.mode('unplanned'));await page.locator('.task-current-step h3').filter({hasText:'阅读：输入输出'}).waitFor();assert.match(await page.locator('.task-current-step').innerText(),/建议任务/);assert.equal(await page.getByRole('button',{name:'完成并继续',exact:true}).count(),0);await page.getByRole('button',{name:'开始学习',exact:true}).click();assert.deepEqual(await page.evaluate(()=>calendarCalls.at(-1)),{kind:'lecture',id:'lecture:foundation-io-basics',key:undefined});assert(await page.locator('.task-next').getByRole('button',{name:/日历里的正式比赛/}).isVisible());
 await page.evaluate(()=>calendarFixture.mode('empty'));await page.getByRole('button',{name:'安排学习',exact:true}).waitFor();assert.doesNotMatch(await page.locator('.task-now').innerText(),/等待比赛|查看比赛/);
 await page.evaluate(()=>calendarFixture.mode('finished'));await page.getByRole('button',{name:'选择下一条主线',exact:true}).waitFor();assert.doesNotMatch(await page.locator('.task-now').innerText(),/等待比赛|查看比赛/);
 assert.deepEqual(errors,[]);ok=true;console.log(JSON.stringify({ok,proof,errors}));
}finally{await writeFile(out+'/calendar-ui.json',JSON.stringify({ok,proof,errors},null,2));await browser.close();await vite.close();}
