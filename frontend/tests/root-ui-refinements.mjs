import assert from 'node:assert/strict';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {chromium} from 'playwright';import {createServer} from 'vite';
import {availablePages} from '../src/lib/navigationVisibility.js';
const templates=JSON.parse(await readFile('../backend/resources/code-templates.json','utf8'));
const vite=await createServer({server:{host:'127.0.0.1',port:0},plugins:[{name:'root-ui-isolation',configureServer(server){server.middlewares.use((request,response,next)=>{if(!request.url?.startsWith('/api/'))return next();response.writeHead(410,{'Content-Type':'application/json'});response.end('{"error":"Isolated UI fixture; live API disabled"}');});}}]});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1440,height:960}});
page.setDefaultTimeout(10000);const errors=[],unknown=[],external=[];page.on('pageerror',error=>errors.push(error.message));
const owner='c3e5d799-502a-4b4f-a864-a342f7db419e',now='2026-10-29T04:00:00.000Z';await page.clock.setFixedTime(new Date(now));
let completed=0,revision=0,preferences={theme:'dark',accent:'teal',fontSize:22,onboardingGuideVersion:2,onboardingCompleted:true,onboardingUnlockedPages:availablePages(11),levelNoticeVersion:1,levelNoticeSeen:100,levelNoticePending:0};
const rows=[400,401,402].flatMap((round,index)=>['A','B'].map(letter=>({id:`fixture::${round}${letter}`,title:`练习 ${round}${letter}`,contest:`ABC ${round}`,problem:letter,platform:'AtCoder',series:'ABC',contestDate:`2026-10-${10+index}T12:00:00Z`,contestProblemCount:2,catalogContentReady:true,statementAvailable:true,solutionAvailable:true,url:`https://atcoder.jp/contests/abc${round}/tasks/abc${round}_${letter.toLowerCase()}`,difficulty:1000,difficultySource:'Codeforces 官方评分（隔离夹具）',difficultyConfidence:'HIGH',tags:['输入输出']})));
const workspace={training:[],sets:[],contests:[],activeContest:null,summary:{total:0,accepted:0,attempts:0,pending:0,due:0},now};
const notifications=Array.from({length:32},(_,i)=>({id:'today-'+i,kind:i%2?'comment':'like',actor:{nickname:'今日用户'+i},text:'今日留言内容 '.repeat(8),createdAt:i===0?'2026-10-28T16:00:00.000Z':now,read:true}));
notifications.push(...[{id:'old',kind:'comment',actor:{nickname:'昨日用户'},text:'昨日内容不可出现',createdAt:'2026-10-28T15:59:59.999Z',read:false},{id:'future',kind:'comment',actor:{nickname:'未来用户'},text:'未来内容不可出现',createdAt:'2026-10-29T16:00:00.000Z',read:false},{id:'invalid',kind:'comment',actor:{nickname:'无效日期'},text:'无效日期不可出现',createdAt:'invalid',read:false}]);
const hub={settings:{autoSync:false},accounts:[],updates:{configured:true},sync:{busy:false,providers:[]},notifications:Array.from({length:32},(_,i)=>({id:'update-'+i,type:'content',title:`公共内容更新 ${i}`,createdAt:now,read:true,count:i+1}))};
const daily=()=>({policyVersion:3,date:'2026-10-29',tasks:[],displayCompletedCount:completed,displayTarget:Math.min(10,Math.max(3,completed+1)),displayComplete:completed>=10});
await page.route('**/api/**',async route=>{
 const request=route.request(),url=new URL(request.url());if(!url.pathname.startsWith('/api/'))return route.continue();const name=url.pathname.replace('/api/','');let value;
 if(name==='account')value={required:true,authenticated:true,token:'fixture',account:{userId:owner,loginId:'fixture',nickname:'测试学习者'}};
 else if(name==='preferences'){if(request.method()==='POST')preferences=request.postDataJSON().preferences;value={preferences,updatedAt:now};}
 else if(name==='data')value={rows,categories:[],token:'fixture',today:'2026-10-29'};
 else if(name==='workspace')value=workspace;
 else if(name==='insights')value={summary:{totalSolved:98,submissions:171,activeDays:29,streak:19,longestStreak:21,completedContests:2},growth:{level:11,confirmed:true,authority:{owner,epoch:'root-ui-fixture',revision:++revision},currentLevelXp:745,nextLevelXp:2200,totalXp:11745,ranked:{qualified:true,tier:'青铜',badge:'tier-1',abilityScore:900}},knowledge:[],recommendations:[],activity:[],assessment:{},achievements:[],dailyTasks:daily()};
 else if(name==='daily-tasks')value=daily();
 else if(name==='software-update')value={currentVersion:'1.4.30',status:'current',autoCheck:false,canInstall:false};
 else if(name==='content-update')value={revision:0,status:'current'};
 else if(name==='contest-calendar')value={contests:[],providers:[],refreshing:false};
 else if(name==='browser-preparation')value={available:false};
 else if(name==='social')value={available:true,notifications,totalLikes:999,unreadCount:3,likes:[]};
 else if(name==='social/read')value={ok:true};
 else if(name==='goals')value={goals:[],contestPlan:{contests:[]}};
 else if(name==='inbox')value={pending:0,errors:[]};
 else if(name==='hub')value=hub;
 else if(name==='desktop/fullscreen')value={available:false,fullscreen:false};
 else if(name==='usage')value={days:[],totalSeconds:0};
 else if(name==='training-lists')value={lists:[]};
 else if(name==='training-list-likes')value={likes:[]};
 else if(name==='templates')value=templates;
 else if(name==='lectures')value={lectures:[]};
 else if(name==='profile')value={profile:{userId:owner,nickname:'测试学习者'}};
 else if(name==='leaderboard')value={configured:false,entries:[]};
 else {unknown.push(name);value={};}
 await route.fulfill({json:value});
});
await page.route(/^https?:\/\/(?!127\.0\.0\.1)(?!localhost)/,route=>{external.push(route.request().url());return route.abort();});
const base=`http://127.0.0.1:${vite.httpServer.address().port}`,nav=()=>page.getByRole('navigation',{name:'主导航'});
async function load(){await page.goto(base);await page.waitForFunction(()=>document.querySelector('.profile-level-number')?.textContent==='11');await nav().getByRole('button',{name:'成长与能力',exact:true}).waitFor();}
const openPage=async label=>{await page.keyboard.press('Control+k');const modal=page.getByRole('dialog',{name:'快捷操作',exact:true});await modal.waitFor();await modal.getByRole('button',{name:new RegExp('^打开'+label+'(?:\\s|$)')}).click();};
const checkOverflow=async()=>assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
await mkdir('tests/screenshots/root-ui-refinements',{recursive:true});const proof={geometry:[],footer:[],lab:{},sort:[]};
try{
 for(const count of [0,3,4,9,10]){completed=count;await load();const counter=page.locator('.daily-task-top-button small');if(count===10){assert.equal(await counter.getAttribute('aria-label'),'今日已完成十项任务');assert.equal(await counter.locator('.lucide-check').count(),1);assert.equal(await counter.innerText(),'');}else assert.equal(await counter.innerText(),`${count}/${Math.max(3,count+1)}`);proof.footer.push({count,text:await counter.innerText(),label:await counter.getAttribute('aria-label')});}
 await page.setViewportSize({width:1440,height:960});await nav().getByRole('button',{name:'算法实验室',exact:true}).click();await page.getByRole('button',{name:'打开算法 排序基础',exact:true}).click();await page.locator('.lab-course-header h1').waitFor();
 await page.waitForFunction(()=>document.querySelector('.lab-course-header h1')?.textContent.includes('排序基础'));await page.waitForFunction(()=>!document.querySelector('.lab-catalog'));
 await openPage('题库');await page.clock.setFixedTime(new Date('2026-10-30T04:00:00.000Z'));await nav().getByRole('button',{name:'算法实验室',exact:true}).click();await page.locator('.lab-course-header h1').waitFor();assert.match(await page.locator('.lab-course-header h1').innerText(),/排序基础/);
 await page.waitForTimeout(400);assert.equal(preferences.learningPaths?.activePath,'sorting-basics');await page.evaluate(()=>localStorage.clear());await load();await nav().getByRole('button',{name:'算法实验室',exact:true}).click();await page.locator('.lab-course-header h1').waitFor();assert.match(await page.locator('.lab-course-header h1').innerText(),/排序基础/);proof.lab={afterDay:true,reloadFromAccountPrefs:true,browserMirrorCleared:true};
 await page.getByRole('button',{name:'返回算法实验室',exact:true}).click();await page.locator('.lab-catalog').waitFor();
 await nav().getByRole('button',{name:'比赛',exact:true}).click();await page.locator('.competition-card').first().waitFor();await page.getByRole('button',{name:'比赛文件夹浏览',exact:true}).click();
 for(let i=0;i<6&&await page.locator('.catalog-folder-row').count();i++){await page.locator('.catalog-folder-row').first().click();if(await page.locator('.competition-card').count())break;}
 const names=()=>page.locator('.competition-card .competition-card-title strong').allTextContents();assert.deepEqual(await names(),['ABC 402','ABC 401','ABC 400']);proof.sort.push(await names());await page.getByRole('button',{name:'切换比赛排序方向',exact:true}).click();await page.waitForFunction(()=>document.querySelector('.competition-card-title strong')?.textContent==='ABC 400');assert.deepEqual(await names(),['ABC 400','ABC 401','ABC 402']);proof.sort.push(await names());
 await page.clock.setFixedTime(new Date(now));
 for(const width of [2048,1294,960,430])for(const theme of ['dark','light']){
  preferences={...preferences,theme,fontSize:22,learningPaths:{}};await page.setViewportSize({width,height:960});await load();
  await page.waitForFunction(theme=>document.documentElement.dataset.theme===theme,theme);
  await page.getByRole('button',{name:'消息通知',exact:true}).click();const modal=page.getByRole('dialog',{name:'消息与更新',exact:true});await modal.waitFor();
  await modal.locator('.social-notification').first().waitFor();assert.equal(await modal.locator('.social-notification').count(),32);assert.doesNotMatch(await modal.innerText(),/昨日用户|未来用户|无效日期|999/);
  const geometry=await modal.evaluate(node=>{const panes=[node.querySelector('.messages-social-pane'),node.querySelector('.update-panel')],rect=n=>{const r=n.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height,client:n.clientHeight,scroll:n.scrollHeight,overflow:getComputedStyle(n).overflowY};};return {modal:rect(node),panes:panes.map(rect),viewport:{width:innerWidth,height:innerHeight}};});
  assert(Math.abs(geometry.panes[0].height-geometry.panes[1].height)<2,JSON.stringify({width,theme,...geometry}));
  assert(geometry.panes.every(p=>p.scroll>p.client&&p.overflow==='auto'&&p.left>=0&&p.right<=width&&p.bottom<=geometry.modal.bottom),JSON.stringify(geometry));
  const top=modal.locator('.messages-social-pane'),bottom=modal.locator('.update-panel');await top.hover();await page.mouse.wheel(0,300);await page.waitForFunction(()=>document.querySelector('.messages-social-pane')?.scrollTop>0);assert.equal(await bottom.evaluate(n=>n.scrollTop),0);const topScroll=await top.evaluate(n=>n.scrollTop);await bottom.hover();await page.mouse.wheel(0,300);await page.waitForFunction(()=>document.querySelector('.messages-modal .update-panel')?.scrollTop>0);assert.equal(await top.evaluate(n=>n.scrollTop),topScroll);
  await page.keyboard.press('Escape');await modal.waitFor({state:'hidden'});
  for(const label of ['算法实验室','模板']){
   await nav().getByRole('button',{name:label,exact:true}).click();await page.locator('.catalog-card').first().waitFor();
   const cards=await page.locator('.catalog-card').evaluateAll(nodes=>nodes.map(node=>{const r=node.getBoundingClientRect(),heading=node.querySelector('.catalog-card-heading').getBoundingClientRect(),icon=node.querySelector('.catalog-card-heading>svg').getBoundingClientRect(),text=node.querySelector('.catalog-card-heading>span').getBoundingClientRect();return {center:(r.left+r.right)/2,headingCenter:(heading.left+heading.right)/2,iconCenterY:(icon.top+icon.bottom)/2,textCenterY:(text.top+text.bottom)/2,left:r.left,right:r.right};}));
   assert(cards.every(c=>Math.abs(c.center-c.headingCenter)<1.5&&Math.abs(c.iconCenterY-c.textCenterY)<1.5&&c.left>=0&&c.right<=width),JSON.stringify({width,theme,label,cards}));await checkOverflow();
  }
  await nav().getByRole('button',{name:'成长与能力',exact:true}).click();const stats=page.locator('.account-hero-statistics>div');await stats.first().waitFor();assert.equal(await stats.count(),6);
  const icons=await stats.evaluateAll(nodes=>nodes.map(node=>{const svg=node.querySelector('svg').getBoundingClientRect(),number=node.querySelector('b').getBoundingClientRect();return {x:(svg.left+svg.right)/2,nx:(number.left+number.right)/2,width:svg.width,height:svg.height};}));assert(icons.every(i=>Math.abs(i.x-i.nx)<1.5&&i.width===30&&i.height===30),JSON.stringify({width,theme,icons}));
  assert.equal(await page.locator('.account-hero-statistics .lucide-flag').getAttribute('fill'),'none');assert.equal(await page.locator('.account-hero-statistics .streak-flame .flame-embers').count(),1);assert.equal(await page.locator('.account-hero-statistics .streak-flame .flame-core').count(),1);await checkOverflow();
  if(width===430)await page.locator('.account-hero-statistics').scrollIntoViewIfNeeded();
  await page.screenshot({path:`tests/screenshots/root-ui-refinements/growth-${width}-${theme}.png`});proof.geometry.push({width,theme,messagePanes:geometry.panes.length,catalogCentered:true,icons});
 }
 assert.deepEqual(errors,[]);assert.deepEqual(unknown,[]);assert.deepEqual(external,[]);await writeFile('tests/screenshots/root-ui-refinements/report.json',JSON.stringify({ok:true,...proof},null,2));console.log(JSON.stringify({ok:true,geometryCases:proof.geometry.length,footerCases:proof.footer.length,lab:proof.lab,sort:proof.sort}));
}catch(error){await page.screenshot({path:'tests/screenshots/root-ui-refinements/failure.png'});console.error(JSON.stringify({errors,unknown,external,body:(await page.locator('body').innerText()).slice(-3500)}));throw error;}finally{await browser.close();await vite.close();}
