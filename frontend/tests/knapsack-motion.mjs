import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { pathToFileURL,fileURLToPath } from 'node:url';
import path from 'node:path';
import { chromium } from 'playwright';
import { choiceFrames } from '../src/pages/algorithm-lab/knapsackMotion.js';
import { EXPEDITION, enumerate01 } from '../src/pages/algorithm-lab/knapsackModel.js';

let assertions=0;
for(let c=0;c<=12;c++)for(let n=1;n<=EXPEDITION.length;n++) {
  const items=EXPEDITION.slice(0,n),frames=choiceFrames(items,c);
  assert.equal(frames.length,n*4);assertions++;
  for(const f of frames) {
    assert.equal(f.result,enumerate01(items.slice(0,f.i),c));
    assert.equal(f.skip,enumerate01(items.slice(0,f.i-1),c));
    assert.equal(f.take,f.remaining<0?null:enumerate01(items.slice(0,f.i-1),f.remaining)+f.item.value);
    for(const plan of [f.skipPlan,f.takePlan,f.resultPlan]) {
      assert.ok(plan.reduce((s,p)=>s+p.weight,0)<=c);
      assert.equal(new Set(plan.map(p=>p.id)).size,plan.length);
    }
    assertions+=9;
  }
}
const repo=fileURLToPath(new URL('../../',import.meta.url)),out=path.join(repo,'.backups/sequence-lab-20261023/knapsack-motion');await mkdir(out,{recursive:true});
const entry=path.resolve(repo,'../../版本/算法实验室体验版/开始体验.html');
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),context=await browser.newContext({offline:true,viewport:{width:1440,height:1050}}),page=await context.newPage(),errors=[];
page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(10000);
const chapter=async title=>{await page.getByRole('button',{name:'目录',exact:true}).click();await page.getByRole('navigation',{name:'课程章节'}).getByRole('button').filter({hasText:title}).click();};
try {
  await page.goto(pathToFileURL(entry).href);await page.getByRole('region',{name:'背包 DP',exact:true}).getByRole('button',{name:'学算法',exact:true}).click();
  const film=page.getByRole('region',{name:'拿与不拿动态演示'});await film.scrollIntoViewIfNeeded();
  assert.equal(await film.getAttribute('data-playing'),'false');
  await page.getByLabel('选择动画速度',{exact:true}).selectOption('1250');await page.getByRole('button',{name:'播放选择动画',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('.knapsack-motion').dataset.frame!=='0');
  await page.getByRole('button',{name:'暂停选择动画',exact:true}).click();const paused=await film.getAttribute('data-frame');await page.waitForTimeout(350);assert.equal(await film.getAttribute('data-frame'),paused);
  await page.getByRole('button',{name:'跳到A、B：如果拿新物品',exact:true}).click();assert.match(await film.locator('.kn-motion-narration').innerText(),/余下 2 格/);
  await page.getByRole('button',{name:'跳到A、B、C：比较后，重新选方案',exact:true}).click();assert.match(await film.locator('.kn-motion-result').innerText(),/B \+ C[\s\S]*最大价值 8/);
  const state=await page.evaluate(()=>JSON.parse(localStorage.getItem('tb.knapsack.standalone.v1')));assert.deepEqual(state.learningPaths.knapsack.labV1?.passed||{},{});
  await film.screenshot({path:path.join(out,'choice-final-wide.png')});
  await page.emulateMedia({reducedMotion:'reduce'});await page.waitForFunction(()=>document.querySelector('[aria-label="播放选择动画"]')?.disabled);assert.equal(await page.getByRole('button',{name:'播放选择动画'}).isDisabled(),true);await page.getByRole('button',{name:'选择动画上一帧'}).click();assert.equal(await film.getAttribute('data-frame'),'10');
  await page.emulateMedia({reducedMotion:'no-preference'});
  await chapter('读懂表格');await page.getByRole('group',{name:'逐步增加可选物品'}).getByRole('button',{name:/^2\s*只允许 A、B$/}).click();
  await film.scrollIntoViewIfNeeded();await page.getByRole('button',{name:'跳到A、B：如果拿新物品',exact:true}).click();assert.match(await film.locator('.kn-motion-narration').innerText(),/来源价值 0/);
  await page.getByRole('group',{name:'逐步增加可选物品'}).getByRole('button',{name:/^3\s*只允许 A、B、C$/}).click();
  await film.scrollIntoViewIfNeeded();await page.getByRole('button',{name:'跳到A、B、C：比较后，重新选方案',exact:true}).click();
  assert.match(await film.locator('.kn-motion-result').innerText(),/最大价值 \?/);assert.equal(await film.locator('.kn-motion-branches>[data-focus=true]').count(),0);
  await page.getByText('把这些答案记成表格',{exact:true}).click();await page.getByRole('button',{name:/可选A、B、C，容量 0 格/}).click();
  await film.getByRole('img',{name:'这件物品装不下，本分支不合法',exact:true}).waitFor();
  await chapter('理解倒序');await page.getByRole('button',{name:'正序 · w → W',exact:true}).click();
  for(let i=0;i<3;i++)await page.getByRole('button',{name:'下一步',exact:true}).click();
  await page.locator('.kn-flow[data-repeated=true]').waitFor();assert.match(await page.locator('.kn-flow').innerText(),/来源已经含有 X/);
  assert.match(await page.locator('.kn-flow svg').getAttribute('aria-label'),/dp\[2\]=3[\s\S]*写回 6/);
  assert.equal(await page.locator('.kn-flow animateMotion').count(),2);await page.locator('.kn-flow').screenshot({path:path.join(out,'repeated-read-wide.png')});
  await page.emulateMedia({reducedMotion:'reduce'});await page.waitForFunction(()=>document.querySelectorAll('.kn-flow animateMotion').length===0);assert.equal(await page.locator('.kn-flow animateMotion').count(),0);await page.emulateMedia({reducedMotion:'no-preference'});
  let variants=0;
  for(const theme of ['light','dark'])for(const width of [1440,390]) {
    await page.setViewportSize({width,height:1000});await page.evaluate(t=>document.documentElement.dataset.theme=t,theme);
    await chapter('先装一次背包');await film.scrollIntoViewIfNeeded();await page.getByRole('button',{name:'跳到A、B、C：比较后，重新选方案',exact:true}).click();await film.screenshot({path:path.join(out,`choice-${theme}-${width}.png`)});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);variants++;
  }
  assert.deepEqual(errors,[]);const report={status:'passed',modelAssertions:assertions,animatedChoice:true,synchronizedReadWrite:true,pauseAndStep:true,reducedMotion:true,doesNotAwardProgress:true,visualVariants:variants,errors};await writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}finally{await browser.close();}
