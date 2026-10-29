import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const out='../.backups/local-1419/ui';fs.mkdirSync(out,{recursive:true});
const vite=await createServer({server:{host:'127.0.0.1',port:0,fs:{allow:[process.cwd(),fs.realpathSync('node_modules')]}}});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1440,height:900}});
page.setDefaultTimeout(12000);
const errors=[],writes=[],now=new Date().toISOString(),self={userId:'11111111-1111-4111-8111-111111111111',nickname:'测试用户'};
const rows=Array.from({length:60},(_,i)=>({id:'task-'+i,title:'练习 '+String(i+1).padStart(2,'0'),contest:'ABC 400',problem:'P'+(1000+i),platform:'洛谷',url:'https://www.luogu.com.cn/problem/P'+(1000+i),tags:i%2?['图论']:['前缀和'],difficulty:1000,contestDate:'2026-01-01T00:00:00Z',solutionAvailable:false}));
const ids=['custom:11111111-1111-4111-8111-111111111111','custom:22222222-2222-4222-8222-222222222222'];
let lists=ids.map((id,i)=>({id,title:['周末练习','考前复习'][i],custom:true,available:true,children:[],aggregateChildren:false,problems:[],categories:[{id:'personal',name:'我的题单',position:i,order:-1}]}));
let notifications=[{id:'33333333-3333-4333-8333-333333333333',kind:'like',actor:{nickname:'朋友'},createdAt:now,read:false}];
let hub={settings:{accounts:{},autoSync:false},sync:{},updates:{},accounts:[],notifications:[{id:'content-1',title:'题库更新',type:'content',createdAt:now,read:false}]};
let preferences={theme:'dark',fontSize:15,onboardingCompleted:true,motion:false},failAdd=false,holdNext=false,releaseOld=null;
const workspace=()=>({training:[{id:'task-0',accepted:true,verdict:'AC',activeAt:now}],sets:[],contests:[],activeContest:null,goals:{goals:[]},goalTasks:[],summary:{total:1,accepted:1,pending:0,historicalAccepted:1,streak:1},now});
await page.addInitScript(()=>{localStorage.setItem('tb.preferences',JSON.stringify({theme:'dark',motion:false,onboardingCompleted:true}));sessionStorage.setItem('tb.settings.location.11111111-1111-4111-8111-111111111111',JSON.stringify({tab:'animation'}));});
page.on('pageerror',error=>errors.push(error.message));
await page.route('**/api/**',async route=>{
  const request=route.request(),url=new URL(request.url()),path=url.pathname,body=request.method()==='POST'?request.postDataJSON():null;
  if(!path.startsWith('/api/'))return route.continue();
  if(body){assert.equal(request.headers()['x-tb-token'],'fixture');writes.push({path,body});}
  let value;
  if(path==='/api/account')value={required:false,authenticated:true,usesOriginalWorkspace:true,token:'fixture',account:self};
  else if(path==='/api/preferences'){if(body)preferences=body.preferences;value={preferences};}
  else if(path==='/api/data')value={rows,categories:[{name:'前缀和',tags:['前缀和'],children:[]}],token:'fixture',today:now.slice(0,10),revision:'list-workflows'};
  else if(path==='/api/workspace')value=workspace();
  else if(path==='/api/hub')value=hub;
  else if(path==='/api/hub/dismiss'){hub={...hub,notifications:hub.notifications.map(item=>item.id===body.id?{...item,read:true}:item)};value=hub;}
  else if(path==='/api/insights')value={summary:{officialSolved:1,submissions:1,activeDays:1,streak:1,completedContests:0,longestStreak:1},growth:{level:1,totalXp:10,currentLevelXp:10,nextLevelXp:100,ranked:{}},knowledge:[],achievements:[],activity:[],assessment:{platforms:[]},dailyTasks:{tasks:[]}};
  else if(path==='/api/contest-calendar')value={contests:[],refreshing:false,importing:false};
  else if(path==='/api/content-update')value={revision:0,status:'current',error:''};
  else if(path==='/api/software-update')value={currentVersion:'1.4.19',status:'current',autoCheck:false,canInstall:false};
  else if(path==='/api/desktop/fullscreen')value={available:false,fullscreen:false};
  else if(path==='/api/profile')value={profile:self,leaderboard:{configured:true,status:'ready'}};
  else if(path==='/api/goals')value={goals:[]};
  else if(path==='/api/submissions')value={submissions:[],total:0};
  else if(path==='/api/contests/calendar')value={events:[]};
  else if(path==='/api/contests/events')value={events:[{name:'ABC 481',displayName:'ABC 481',platform:'AtCoder',series:'ABC',count:8,duration:120}]};
  else if(path==='/api/contests/preview')value={plan:{previewId:'fixture-'+writes.length,slots:rows.slice(0,body.mode==='replay'?8:body.count).map((row,i)=>({id:row.id,title:row.title,letter:'P'+(16000+i)})),difficultyRange:{min:1100,max:2000},event:{displayName:'ABC 481'}}};
  else if(path==='/api/contests/start')return route.fulfill({status:503,json:{error:'测试已收到重命名后的开赛请求'}});
  else if(path==='/api/social'){
    value={available:true,totalLikes:1,todayLikes:0,notifications:structuredClone(notifications),unreadCount:notifications.filter(item=>!item.read).length};
    if(holdNext){holdNext=false;await new Promise(resolve=>{releaseOld=resolve;});}
  }
  else if(path==='/api/social/read'){notifications=notifications.map(item=>body.all||body.ids.includes(item.id)?{...item,read:true}:item);value={ok:true};}
  else if(path==='/api/training-lists')value={lists};
  else if(path==='/api/training-lists/add'){
    if(failAdd){failAdd=false;return route.fulfill({status:503,json:{error:'测试添加失败'}});}
    assert(body.listIds.every(id=>ids.includes(id)));
    lists=lists.map(list=>body.listIds.includes(list.id)?{...list,problems:[...new Set([...list.problems.map(item=>item.problemId),...body.problemIds])].map(id=>({problemId:id,pid:rows.find(row=>row.id===id).problem,sections:[]}))}:list);
    value={customLists:lists};
  }
  else if(path==='/api/usage')value={ok:true};
  else return route.fulfill({status:404,json:{error:'fixture missing '+path}});
  await route.fulfill({json:value});
});
const nav=name=>page.locator('.sidebar').getByRole('button',{name,exact:true});
const bell=()=>page.getByRole('button',{name:'消息通知',exact:true});
const dialog=()=>page.getByRole('dialog',{name:'加入题单',exact:true});
try{
  await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}`);await nav('题库').click();await page.locator('tr[data-id]').first().waitFor();
  const headers=await page.locator('.problem-table th').allTextContents();
  await page.getByRole('button',{name:'加入题单 练习 01',exact:true}).click();await dialog().getByLabel('周末练习',{exact:false}).check();await dialog().getByLabel('考前复习',{exact:false}).check();
  assert.equal(await dialog().locator('button').evaluateAll(nodes=>nodes.map(node=>node.textContent).join('')),'');
  await dialog().getByRole('button',{name:'添加',exact:true}).click();await dialog().waitFor({state:'detached'});assert(lists.every(list=>list.problems.length===1));
  await page.getByRole('textbox',{name:'搜索题目',exact:true}).fill('前缀和');await page.getByRole('region',{name:'题目列表'}).getByRole('button',{name:'加入题单 练习 01',exact:true}).waitFor();
  await page.waitForFunction(()=>document.querySelector('[aria-label="题库分页"]')?.textContent.includes('共 30 题'));
  assert(await page.locator('tr[data-id]').count()<30);
  await page.getByRole('button',{name:'将筛选结果加入题单',exact:true}).click();await dialog().getByLabel('周末练习',{exact:false}).check();await dialog().getByLabel('考前复习',{exact:false}).check();
  assert.match(await dialog().innerText(),/30 道题/);failAdd=true;
  await dialog().getByRole('button',{name:'添加',exact:true}).click();await dialog().getByRole('alert').waitFor();assert(lists.every(list=>list.problems.length===1));
  await dialog().getByRole('button',{name:'添加',exact:true}).click();await dialog().waitFor({state:'detached'});
  assert(lists.every(list=>list.problems.length===30));const batch=writes.filter(item=>item.path==='/api/training-lists/add').at(-1).body;assert.equal(batch.problemIds.length,30);assert(batch.problemIds.includes('task-58'));
  await page.screenshot({path:out+'/filtered-library.png'});
  await nav('题单').click();const progress=page.getByRole('progressbar',{name:'我的题单 已 AC / 总题数'});await progress.waitFor();assert.equal(await progress.getAttribute('aria-valuetext'),'1 / 30');
  await page.screenshot({path:out+'/directory-progress.png'});
  await page.locator('.catalog-folder-row').filter({has:page.locator('strong',{hasText:'我的题单'})}).click();await page.getByRole('button',{name:'打开题单：周末练习',exact:true}).click();
  assert.deepEqual(await page.locator('.problem-table th').allTextContents(),headers);
  assert.equal(await page.locator('.training-list-table .row-actions').first().locator('button').count(),4);
  await page.screenshot({path:out+'/unified-list.png'});
  await nav('比赛').click();await page.getByRole('button',{name:'筛选比赛',exact:true}).click();const filter=page.locator('.filter-popover');await filter.waitFor();assert.equal(await filter.locator('.filter-field').count(),2);assert.match(await filter.innerText(),/年份/);assert.match(await filter.innerText(),/训练情况/);assert.doesNotMatch(await filter.innerText(),/比赛分类|排序/);await page.keyboard.press('Escape');
  await nav('模拟赛').click();await page.getByRole('button',{name:'训练筛选',exact:true}).click();
  assert.equal(await page.locator('.filter-popover details').count(),0);assert.equal(await page.locator('.mock-filter-categories button').count(),7);
  assert.equal(await page.locator('.filter-popover .difficulty-presets').count(),1);assert.equal(await page.locator('.mock-config .difficulty-presets').count(),0);
  assert.equal(await page.locator('.filter-popover input[aria-label="模拟赛名称"]').count(),0);assert.equal(await page.locator('.filter-popover select').count(),0);
  const switchOrder=await page.locator('.mock-filter-switches').evaluate(node=>node.compareDocumentPosition(document.querySelector('[aria-label="模拟赛时长"]')));assert(switchOrder&2);
  await page.getByRole('radio',{name:/普通/}).click();await page.getByRole('button',{name:'关闭筛选',exact:true}).click();
  assert.equal(await page.locator('.training-difficulty-summary').innerText(),'难度 1300–1700');
  assert.equal(await page.getByRole('button',{name:'删除全部模拟赛记录'}).count(),0);
  await page.getByRole('button',{name:'生成试卷',exact:true}).click();await page.locator('.paper-slot').first().waitFor();
  assert.deepEqual(await page.locator('.paper-slot strong').allTextContents(),['A','B','C','D']);
  assert.deepEqual(await page.locator('.paper-slot > span').allTextContents(),rows.slice(0,4).map(row=>row.title));
  assert.equal(await page.getByText('模拟赛记录',{exact:true}).count(),0);assert.doesNotMatch(await page.locator('.mock-create').innerText(),/官方样例/);
  assert.equal(await page.locator('.create-buttons button').evaluateAll(nodes=>nodes.map(node=>node.textContent).join('')),'');
  const rename=page.getByRole('textbox',{name:'模拟赛名称',exact:true});
  await page.locator('.paper-preview-title > span').click();await rename.fill('周末模拟赛');await rename.press('Enter');assert.equal(await page.getByRole('button',{name:'重命名模拟赛'}).innerText(),'周末模拟赛');
  await page.getByRole('button',{name:'重命名模拟赛'}).click();await rename.fill('不保存');await rename.press('Escape');assert.equal(await page.getByRole('button',{name:'重命名模拟赛'}).innerText(),'周末模拟赛');
  await page.getByRole('button',{name:'开始训练',exact:true}).click();await page.getByText('测试已收到重命名后的开赛请求',{exact:true}).first().waitFor();assert.equal(writes.filter(item=>item.path==='/api/contests/start').at(-1).body.name,'周末模拟赛');
  await page.getByRole('button',{name:'重现赛',exact:true}).click();await page.getByRole('combobox',{name:'重现赛比赛'}).selectOption('ABC 481');
  assert.equal(await page.locator('.create-main select').count(),0);await page.getByRole('button',{name:'生成试卷',exact:true}).click();await page.locator('.paper-slot').first().waitFor();
  assert.deepEqual(await page.locator('.paper-slot strong').allTextContents(),['A','B','C','D','E','F','G','H']);assert.equal(await page.locator('.training-difficulty-summary').innerText(),'难度 1100–2000');
  for(const width of [1440,720,390]){await page.setViewportSize({width,height:900});await page.screenshot({path:out+`/mock-${width}.png`});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);}
  await page.setViewportSize({width:1440,height:900});
  await nav('设置').click();await page.locator('.settings-home-grid').waitFor();assert.equal(await page.locator('[data-section="animation"]').count(),0);assert.equal(await page.locator('.settings-home-grid .settings-tile').count(),9);
  await page.emulateMedia({reducedMotion:'reduce'});assert.equal(await page.evaluate(()=>document.documentElement.dataset.motion),'on');
  assert.notEqual(await page.locator('.globe-turn').evaluate(el=>getComputedStyle(el).animationName),'none');
  for(const width of [1440,1100,720]){await page.setViewportSize({width,height:900});await page.screenshot({path:out+`/settings-${width}.png`});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);}
  await page.setViewportSize({width:1440,height:900});await nav('成长与能力').click();await page.locator('.account-hero-statistics').waitFor();
  for(const label of ['连续练习','完成比赛'])assert.equal(await page.locator(`.account-stat-icon[aria-label="${label}"] svg`).getAttribute('fill'),'currentColor');
  await bell().locator('.notification-dot').waitFor();holdNext=true;await page.evaluate(()=>window.dispatchEvent(new Event('tb:social-change')));
  for(let i=0;!releaseOld&&i<40;i++)await page.waitForTimeout(25);assert(releaseOld);
  await bell().click();await page.getByRole('dialog',{name:'消息与更新'}).waitFor();
  await page.waitForFunction(()=>!document.querySelector('[aria-label="消息通知"] .notification-dot'));
  assert(notifications.every(item=>item.read)&&hub.notifications.every(item=>item.read));releaseOld();releaseOld=null;await page.waitForTimeout(200);assert.equal(await bell().locator('.notification-dot').count(),0);
  await page.keyboard.press('Escape');notifications.push({id:'44444444-4444-4444-8444-444444444444',kind:'like',actor:{nickname:'新朋友'},createdAt:now,read:false});await page.evaluate(()=>window.dispatchEvent(new Event('tb:social-change')));await bell().locator('.notification-dot').waitFor();
  assert.deepEqual(errors,[]);fs.writeFileSync(out+'/workflow-report.json',JSON.stringify({ok:true,filteredAllPages:30,multipleDestinations:2,duplicatesSkipped:true,atomicRetry:true,folderProgress:'1 / 30',sharedColumns:true,alwaysAnimated:true,settingsTiles:9,contestFilters:2,solidGrowthIcons:true,staleNotificationGuard:true,newNotificationDot:true},null,2));
  console.log('PASS: full app single/batch add, all pages, multi-list retry/dedupe, folder progress, shared columns, icon-only actions, settings animation, contest filters, solid icons and notification read/race/new arrival.');
}catch(error){await page.screenshot({path:out+'/workflow-failure.png'});console.error(errors);throw error;}finally{releaseOld?.();await browser.close();await vite.close();}
