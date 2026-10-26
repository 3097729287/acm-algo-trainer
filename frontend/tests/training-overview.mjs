import { openSettings } from './settings-navigation.mjs';
// All API calls use public fixture data; no user state or original-site access.
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {createServer} from 'vite';
import {mkdir} from 'node:fs/promises';

const server = await createServer({server:{host:'127.0.0.1',port:0}});
await server.listen();
const browser = await chromium.launch({channel:process.env.CI ? undefined : 'msedge',headless:true});
const page = await browser.newPage({viewport:{width:1480,height:1000}});
page.setDefaultTimeout(10000);
const errors = [], loadedModules = [];
page.on('pageerror', error => errors.push(error.message));
page.on('request', request => { if (/Workbench\.jsx|CodeEditor\.jsx|codemirror/i.test(request.url())) loadedModules.push(request.url()); });
await page.addInitScript(() => localStorage.setItem('tb.preferences', JSON.stringify({theme:'dark',accent:'teal',navGroups:{mine:'练习中心',library:'练习中心'}})));
const now = new Date().toISOString();
const rows = ['A','B'].map((letter,index) => ({id:`fixture::${letter}`,title:`训练概览题 ${letter}`,contest:'测试比赛',problem:letter,
  url:`https://example.com/${letter}`,platform:'Codeforces',difficulty:1200,tags:['模拟'],knowledge:'模拟',solutionAvailable:true}));
const workspace = {training:[{id:rows[0].id,accepted:true,verdict:'AC',attempts:3,activeAt:now},
  {id:rows[1].id,accepted:false,verdict:'WA',attempts:2,activeAt:now,queue:'fill'}],sets:[],contests:[],activeContest:null,
  summary:{total:2,accepted:1,attempts:5,due:1,pending:0,todayAccepted:1},now};
const steps = [[1,25],[10,40],[25,60],[50,80],[100,120],[200,160],[300,200],[500,0],[750,0],[1000,0],[1500,0],[2000,0]];
const achievements = steps.map(([target,rewardXp]) => ({id:`official-${target}`,name:`AC ${target}题`,description:`官方 AC ${target} 道不同题目`,
  target,progress:Math.min(27,target),unlocked:target<=27,unlockedAt:target<=27?now:null,rewardXp,rewardClaimed:target<=27}));
achievements.push({id:'contest-1',name:'完成模拟赛',description:'完成一场模拟赛',target:1,progress:0,unlocked:false,rewardXp:40,rewardClaimed:false});
const insights = {summary:{totalSolved:27,officialSolved:27,submissions:5},growth:{level:7,tier:'钻石',badge:'tier-6',currentLevelXp:125,nextLevelXp:1400,totalXp:5000},
  achievements,knowledge:[],recommendations:[],activity:[],assessment:{},dailyTasks:{tasks:[]}};
let releaseInsights;
const waitInsights = new Promise(resolve => { releaseInsights=resolve; });
await page.route('**/api/**', async route => {
  const path = new URL(route.request().url()).pathname;
  if (!path.startsWith('/api/')) return route.continue();
  let value;
  if (path==='/api/account') value={required:false,authenticated:true,token:'fixture',account:null};
  else if (path==='/api/software-update') value={currentVersion:'1.0.19',status:'current',autoCheck:false,canInstall:false};
  else if (path==='/api/browser-preparation') value={available:false};
  else if (path==='/api/data') value={rows,categories:[],token:'fixture',today:now.slice(0,10)};
  else if (path==='/api/workspace') value=workspace;
  else if (path==='/api/goals') value={goals:[],contestPlan:{contests:[]}};
  else if (path==='/api/inbox') value={pending:0,errors:[]};
  else if (path==='/api/hub') value=null;
  else if (path==='/api/insights') { await waitInsights; value=insights; }
  else if (path==='/api/desktop/fullscreen') value={available:false,fullscreen:false};
  else if(path==='/api/usage'||path==='usage') value={days:[],totalSeconds:0,maxDailySeconds:0,maxDailyDate:null};
  else throw new Error(`Unexpected fixture request: ${path}`);
  await route.fulfill({json:value});
});
try {
  await mkdir('tests/screenshots/training-overview',{recursive:true});
  await page.goto(`http://127.0.0.1:${server.httpServer.address().port}`);
  await page.getByRole('navigation',{name:'主导航'}).waitFor();
  const overview = page.getByRole('button',{name:'训练概览',exact:true});
  assert.equal(await overview.getAttribute('aria-busy'),'true');
  assert.doesNotMatch(await overview.textContent(),/黑铁|Lv\.1\b/);
  await overview.click();
  const dialog = page.getByRole('dialog',{name:'你的训练概览',exact:true});
  await dialog.waitFor();
  assert.equal(await page.locator('.overview-popover').count(),0);
  await dialog.getByText('成长与成就数据读取中',{exact:true}).waitFor();
  await page.keyboard.press('Escape');
  assert.deepEqual(loadedModules,[],'the library/home page does not load the practice editor or CodeMirror');
  releaseInsights();
  await page.waitForFunction(()=>document.querySelector('.profile-level-number')?.textContent==='7');
  await overview.click();
  await dialog.getByText('AC 25题',{exact:true}).waitFor();
  assert.equal(await dialog.locator('.summary-grid > div').count(),2);
  assert.equal(await dialog.getByText('仅样例通过',{exact:true}).count(),0);
  assert.equal(await dialog.getByText('今日待办',{exact:true}).count(),0);
  assert.equal(await dialog.locator('.milestones > div').count(),1);
  assert.match(await dialog.locator('.milestones').textContent(),/下个成就 · AC 50题27 \/ 50\+80 XP/);
  await page.screenshot({path:'tests/screenshots/training-overview/overview-dark.png',animations:'disabled'});
  await page.keyboard.press('Escape');
  const groupedNav = page.getByRole('navigation',{name:'主导航'}).getByRole('button',{name:'练习中心',exact:true});
  assert.match(await groupedNav.getAttribute('aria-describedby'),/training-pending/);
  assert.ok(await groupedNav.locator('.training-pending-dot').isVisible());
  assert.ok(await page.getByRole('tab',{name:/我的训练/}).locator('.training-tab-dot').isVisible());
  await page.keyboard.press('Control+b');
  assert.ok(await groupedNav.locator('.training-pending-dot').isVisible(),'pending hint survives an icon-only grouped navigation');
  assert.ok(await groupedNav.evaluate(node => {
    const dot=node.querySelector('.training-pending-dot').getBoundingClientRect(),nav=node.getBoundingClientRect();
    return dot.left>=nav.left && dot.right<=nav.right;
  }),'pending dot stays inside its collapsed navigation button');
  await page.getByRole('button',{name:'成就',exact:true}).click();
  const achievementDialog = page.getByRole('dialog',{name:/成就 ·/});
  await achievementDialog.getByText('AC 2000题',{exact:true}).waitFor();
  assert.equal(await achievementDialog.getByText('AC 10000题',{exact:true}).count(),0);
  assert.equal(await achievementDialog.locator('.progress-achievement-new').count(),3,'opening keeps unseen achievements highlighted');
  await achievementDialog.locator('[data-achievement-id="official-10"]').hover();
  assert.equal(await achievementDialog.locator('.progress-achievement-new').count(),2,'hover reads only this achievement');
  await achievementDialog.getByText('完成模拟赛',{exact:true}).waitFor();
  assert.equal(await achievementDialog.getByText('+25 XP · 已发放',{exact:true}).count(),1);
  assert.equal(await achievementDialog.getByText('+80 XP · 达成后发放',{exact:true}).count(),1);
  await page.screenshot({path:'tests/screenshots/training-overview/achievements-dark.png',animations:'disabled'});
  await page.keyboard.press('Escape');
  await page.getByRole('button',{name:'成就',exact:true}).click();
  assert.equal(await achievementDialog.locator('.progress-achievement-new').count(),2,'read status survives reopening');
  await page.keyboard.press('Escape');
  await openSettings(page);await page.locator('.settings-home-grid').waitFor();
  assert.equal(await page.getByRole('tab',{name:'翻译 API',exact:true}).count(),1);
  assert.equal(await page.getByRole('tab',{name:'账号与身份',exact:true}).count(),1);
  await openSettings(page, '快捷键');
  assert.equal(await page.locator('.settings-commands').count(),0);
  await openSettings(page, '外观');await page.getByRole('button',{name:'云白浅色',exact:true}).click();
  await overview.click();
  await page.screenshot({path:'tests/screenshots/training-overview/overview-light.png',animations:'disabled'});
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({ok:true,directOverview:true,loadingGrowthIsExplicit:true,serverAchievementProgress:true,rewardStatus:true,groupedCollapsedPendingHint:true,practiceEditorDeferred:true,realAccountSubmission:false}));
} finally {
  releaseInsights();
  await browser.close();
  await server.close();
}
