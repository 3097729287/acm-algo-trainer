import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {createServer} from 'vite';
import {chromium} from 'playwright';

const save=path.resolve('../.backups/contest-ui-20261024/reader');
fs.mkdirSync(save,{recursive:true});
const vite=await createServer({server:{host:'127.0.0.1',port:0},cacheDir:path.join(save,'vite-cache')});
await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const errors=[],frames=[],name='CCPC 2026 福建邀请赛';
try {
  for(const width of [1440,1050,390])for(const theme of ['light','dark']){
    const page=await browser.newPage({viewport:{width,height:850}});
    page.on('pageerror',error=>errors.push(error.message));
    await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/contest-reading-fixture.html`);
    await page.locator('.competition-card').first().waitFor();
    await page.evaluate(theme=>document.documentElement.dataset.theme=theme,theme);
    const cards=page.locator('.competition-card');
    assert.equal(await cards.count(),7);
    for(const event of ['福建邀请赛','秦皇岛邀请赛','广西邀请赛','武汉邀请赛']){
      assert.equal(await cards.filter({hasText:event}).locator('.competition-difficulty').count(),0);
    }
    assert.equal(await cards.filter({hasText:'周赛 166'}).locator('.competition-difficulty').count(),3);
    assert.equal(await cards.filter({hasText:'蓝桥杯'}).locator('.competition-difficulty').count(),3);
    await page.getByRole('button',{name:'比赛文件夹浏览',exact:true}).click();
    for(const folder of ['ACM','邀请赛','2026年'])await page.locator('.catalog-folder-row').filter({has:page.getByText(folder,{exact:true})}).click();
    assert.equal(await cards.count(),5,'year level shows every actual contest, including the separate warmup');
    assert.equal(await page.locator('.catalog-folder-row').count(),0,'no event wrapper folder remains');
    assert.equal(await page.locator('.competition-start').count(),5);
    await page.getByRole('button',{name:'开始比赛 ICPC 2026 广西邀请赛（热身赛）',exact:true}).click();
    assert.deepEqual(await page.evaluate(()=>window.contestActions.at(-1)),['replay','ICPC 2026 广西邀请赛（热身赛）']);
    await page.screenshot({path:path.join(save,`${width}-${theme}-cards.png`)});
    await page.getByRole('button',{name:`查看 Codeforces ${name}，13 道题`,exact:true}).click();
    const detail=page.locator('.competition-detail'),questions=page.locator('.competition-question');
    assert.equal(await questions.count(),13);
    assert.equal(await detail.locator('.competition-difficulty').count(),0);
    assert.equal(await page.locator('.competition-detail-heading > div > span,.contest-grade').count(),0);
    assert.equal(await page.locator('.competition-notice').count(),0);
    assert.doesNotMatch(await detail.innerText(),/公开题单核对|日期待核实|整场 4\/5|题解逐步补充/);
    const box=await detail.boundingBox();
    await page.mouse.move(box.x+box.width/2,box.y+box.height*.65);
    await page.mouse.wheel(0,6000);
    await page.waitForFunction(()=>{
      const panel=document.querySelector('.competition-detail'),last=document.querySelector('.competition-question:last-child');
      return panel.scrollTop>0&&last.getBoundingClientRect().bottom<=panel.getBoundingClientRect().bottom+1;
    });
    const wheelScroll=await detail.evaluate(node=>node.scrollTop);
    await questions.last().click();
    assert.deepEqual(await page.evaluate(()=>window.contestActions.at(-1)),['practice','event-0-12']);
    await detail.evaluate(node=>node.scrollTop=0);
    await detail.focus();await page.keyboard.press('End');
    await page.waitForFunction(()=>{
      const panel=document.querySelector('.competition-detail'),last=document.querySelector('.competition-question:last-child');
      return panel.scrollTop>0&&last.getBoundingClientRect().bottom<=panel.getBoundingClientRect().bottom+1;
    });
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,'no horizontal overflow');
    await page.screenshot({path:path.join(save,`${width}-${theme}-last-problem.png`)});
    frames.push({width,theme,wheelScroll,questions:13,lastProblemClickable:true,keyboardScroll:true});

    const state=async value=>{await page.evaluate(value=>window.setContestWorkspace(value),value);await page.waitForTimeout(40);};
    const record=(status,strategy,contest=name)=>({id:'test-replay',status,strategy,constraints:{contest},slots:[]});
    for(const contest of [record('running','replay'),record('cancelled','replay'),record('finished','comprehensive'),record('finished','replay','ICPC 2026 广西邀请赛（热身赛）')]){
      await state({training:[],contests:[contest]});
      assert.equal(await detail.locator('.competition-difficulty').count(),0);
    }
    await state({training:[],contests:[record('finished','replay')]});
    assert.equal(await detail.locator('.competition-difficulty').count(),13);
    assert.equal(await detail.locator('.competition-difficulty').first().innerText(),'1400');
    await state({training:[],contests:[],completedReplayContests:[name]});
    assert.equal(await detail.locator('.competition-difficulty').count(),13,'hiding history does not erase completion');
    await state({training:[],contests:[],completedReplayContests:[name],activeContest:{status:'running',slots:Array.from({length:13},(_,i)=>({id:`event-0-${i}`}))}});
    assert.equal(await detail.locator('.competition-difficulty').count(),0,'active contest lock still applies');
    assert.equal(await page.evaluate(()=>window.contestProgressRows.filter(row=>row.id.startsWith('event-0-')).every(row=>row.locked&&row.difficultyHidden)),true,'all other displays inherit the active lock even after a previous replay was completed');
    await page.close();
  }
  assert.deepEqual(errors,[]);
  const report={ok:true,frames,errors,officialSubmissionsSent:0};
  fs.writeFileSync(path.join(save,'report.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report));
} finally {await browser.close();await vite.close();}
