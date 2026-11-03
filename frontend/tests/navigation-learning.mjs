import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
import {chromium} from 'playwright';
import {createServer} from 'vite';
import {openSettings} from './settings-navigation.mjs';
import {availablePages} from '../src/lib/navigationVisibility.js';

const vite=await createServer({server:{host:'127.0.0.1',port:0,watch:null},plugins:[{name:'isolated-navigation-api',configureServer(server){server.middlewares.use((request,response,next)=>{if(!request.url?.startsWith('/api/'))return next();response.writeHead(410,{'Content-Type':'application/json'});response.end(JSON.stringify({error:'Isolated navigation fixture; live API disabled'}));});}}]});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:960}});page.setDefaultTimeout(12000);
const errors=[],unknown=[];page.on('pageerror',error=>errors.push(error.message));
await page.addInitScript(()=>{window.__tbNewAccount=new URL(location.href).searchParams.get('newAccount')==='1';});
const owner='c3e5d799-502a-4b4f-a864-a342f7db419e',now=new Date().toISOString();
let level=1,revision=0,draft='',sampleRequested=false,officialRequested=false,preferences={theme:'dark',accent:'teal',fontSize:15,onboardingGuideVersion:2,onboardingCompleted:true,onboardingUnlockedPages:availablePages(11),learningPaths:{navigationAccess:{version:3,retained:[]}},levelNoticeVersion:1,levelNoticeSeen:100,levelNoticePending:0};
let preferenceSaveFailures=0,preferenceSaveAttempts=0;
const rows=['A','B','C'].map((letter,index)=>({id:'fixture::'+letter,title:index?'基础练习 '+letter:'实际基础练习',contest:'测试题单',problem:letter,platform:'Codeforces',url:'https://codeforces.com/contest/1/problem/'+letter,difficulty:1000,difficultySource:'Codeforces 官方评分（隔离夹具）',difficultyConfidence:'HIGH',difficultyEstimated:false,tags:['输入输出','排序'],knowledge:'输入输出',catalogContentReady:true,solutionAvailable:true}));
const lists=[{id:'fixture-basic',title:'顺序结构',sourcePlatform:'洛谷',available:true,categories:[],problems:rows.map(row=>({problemId:row.id,url:row.url}))}];
const workspace={training:[],sets:[],contests:[],activeContest:null,summary:{total:0,accepted:0,attempts:0,due:0,pending:0,todayAccepted:0},now};
await page.route('**/api/**',async route=>{
 const url=new URL(route.request().url());if(!url.pathname.startsWith('/api/'))return route.continue();const path=url.pathname.replace('/api/','');let value;
 if(path==='account')value={required:true,authenticated:true,token:'fixture',account:{userId:owner,loginId:'fixture',nickname:'测试学习者'}};
 else if(path==='preferences'){if(route.request().method()==='POST'){preferenceSaveAttempts++;if(preferenceSaveFailures>0){preferenceSaveFailures--;await route.fulfill({status:503,json:{error:'隔离偏好保存失败'}});return;}preferences=route.request().postDataJSON().preferences;}value={preferences,updatedAt:now};}
 else if(path==='data')value={rows,categories:[],token:'fixture',today:now.slice(0,10)};
 else if(path==='workspace')value=workspace;
 else if(path==='insights')value={summary:{totalSolved:0},growth:{level,confirmed:true,authority:{owner,epoch:'navigation-fixture',revision:++revision},tier:'黑铁',currentLevelXp:0,nextLevelXp:200,totalXp:0},knowledge:[],recommendations:[],activity:[],assessment:{},dailyTasks:{tasks:[]}};
 else if(path==='software-update')value={currentVersion:'1.4.29',status:'current',autoCheck:false,canInstall:false};
 else if(path==='content-update')value={revision:0,status:'current'};
 else if(path==='contest-calendar')value={contests:[],providers:[],refreshing:false};
 else if(path==='browser-preparation')value={available:false};
 else if(path==='social')value={notifications:[],likes:[],unread:0};
 else if(path==='goals')value={goals:[],contestPlan:{contests:[]}};
 else if(path==='inbox')value={pending:0,errors:[]};
 else if(path==='hub')value=null;
 else if(path==='desktop/fullscreen')value={available:false,fullscreen:false};
 else if(path==='usage')value={days:[],totalSeconds:0};
 else if(path==='training-lists')value={lists};
 else if(path==='training-list-likes')value={likes:[]};
 else if(path==='templates')value={templates:[]};
 else if(path==='training/start')value={workspace};
 else if(path==='problem')value={...rows[0],id:url.searchParams.get('id'),markdown:'# 基础练习\n\n输入两个整数，输出它们的和。',samples:[{name:'样例 1',input:'1 2\n',output:'3\n'}],limits:{timeMs:2000,memoryMb:256},judge:{scope:'samples',cases:1},locked:false,statementAvailable:true,draft,submissions:[]};
 else if(path==='draft'){draft=route.request().postDataJSON().code;value={savedAt:now};}
 else if(path==='submissions'&&route.request().method()==='POST'){sampleRequested=route.request().postDataJSON().sampleRun;value={submission:{id:'sample-1',problemId:rows[0].id,mode:'run',verdict:'QUEUED',scope:'samples',finishedAt:null,submittedAt:now}};}
 else if(path==='submission')value={submission:{id:'sample-1',problemId:rows[0].id,mode:'run',sampleRun:true,verdict:'SAMPLE_PASS',scope:'samples',finishedAt:now,submittedAt:now,passed:1,total:1,caseResults:[{name:'样例 1',input:'1 2\n',expected:'3\n',actual:'3\n',verdict:'SAMPLE_PASS',timeMs:2,exitCode:0}]},workspace};
 else if(path==='official/submit'){officialRequested=true;value={sessionId:'official-fixture',status:'loading',platform:'Codeforces'};}
 else if(path==='official/status')value={sessionId:'official-fixture',status:'finished',verdict:'AC',submissionId:'isolated-fixture',message:'原站确认 fixture',workspace};
 else if(path==='official/ack'||path==='official/close')value={closed:true};
 else if(path==='submissions')value={submissions:[],groups:[],total:0,page:1,pages:1};
 else {unknown.push(path);value={};}
 await route.fulfill({json:value});
});
const load=async (next,newAccount=false)=>{level=next;await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}${newAccount?'?newAccount=1':''}`);await page.locator('.sidebar nav').waitFor();await page.waitForFunction(value=>document.querySelector('.profile-level-number')?.textContent===String(value),next);await page.getByRole('navigation',{name:'主导航'}).getByRole('button',{name:next>=6?'对战':next>=5?'排行榜':next>=4?'模拟赛':next>=3?'题库':next>=2?'实验室':'成长',exact:true}).waitFor();await page.locator(newAccount?'.training-list-content':'.next-actions').waitFor();};
const nav=()=>page.getByRole('navigation',{name:'主导航'});
try{
 const originalPreferences={...preferences};
 const defaultNames=['我的训练','题库','题单','从零讲','维基百科','模板','实验室','比赛','模拟赛','对战','成长','提交记录','活动记录','排行榜'];
 const shippedOrders=[
  ['mine','library','training-lists','competitions','mock','paths','rankings','growth','records','activity','lectures'],
  ['mine','library','training-lists','competitions','mock','paths','rankings','growth','records','activity','lectures','templates'],
  ['mine','library','training-lists','competitions','mock','records','growth','activity','lectures','templates','paths','rankings'],
  ['mine','library','training-lists','competitions','mock','rankings','growth','records','paths','templates','lectures','activity'],
 ];
 for(const navOrder of shippedOrders){
  preferences={...originalPreferences,navOrder,navSchema:1};await load(11);
  assert.deepEqual(await nav().getByRole('button').allTextContents(),defaultNames,'A previously shipped default order migrates to the current visible order');
 }
 const customOrder=['mine','paths','templates','library','training-lists','activity','competitions','mock','rankings','growth','records','lectures'];
 const customNames=['我的训练','实验室','模板','题库','题单','活动记录','比赛','模拟赛','排行榜','成长','提交记录','从零讲','对战','维基百科'];
 for(const withSchema of [true,false]){
  preferences={...originalPreferences,navOrder:customOrder,...(withSchema?{navSchema:1}:{})};await load(11);
  assert.deepEqual(await nav().getByRole('button').allTextContents(),customNames,'A genuine custom order survives account restoration, including preferences without an old schema');
 }
 await openSettings(page,'交互与导航');
 preferences={...originalPreferences,navOrder:[]};await load(11);
 assert.deepEqual(await nav().getByRole('button').allTextContents(),defaultNames,'Reset keeps the new default order after restoring persisted preferences');
 for(const width of [2048,1440,800,430]){
  preferences={...originalPreferences,fontSize:22};await page.setViewportSize({width,height:960});await load(11);await openSettings(page,'交互与导航');
  const rows=await page.locator('.navigation-visibility-item').evaluateAll(nodes=>nodes.map(row=>{
   const bounds=node=>{const r=node.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height};};
   return {row:bounds(row),icon:bounds(row.querySelector('svg')),label:bounds(row.querySelector('span')),toggle:bounds(row.querySelector('input'))};
  }));
  assert.equal(rows.length,14);
  for(const row of rows){
   assert(row.row.left>=0&&row.row.right<=width+.5&&row.row.height>=47.5,'Visibility row remains a usable target');
   assert(row.label.right<=row.toggle.left-5&&row.icon.right<=row.label.left-5,'Icon, page name and visibility switch do not overlap');
  }
  await mkdir('tests/screenshots/navigation-learning',{recursive:true});
  await page.screenshot({path:`tests/screenshots/navigation-learning/navigation-settings-${width}-22.png`,animations:'disabled'});
 }
 await page.setViewportSize({width:1440,height:960});
 for(const theme of ['dark','light']){
  preferences={...originalPreferences,theme};await load(11);await nav().getByRole('button',{name:'成长',exact:true}).click();
  await page.locator('.sticker-canvas').waitFor();
  assert.equal(await page.locator('.sticker-canvas .growth-footer-actions').count(),0,'Growth controls stay outside the clean canvas in '+theme);
  assert.equal(await page.locator('.app-statusbar .growth-footer-actions').count(),1);
 }
 preferences={...originalPreferences};
 await load(1);
 assert.equal(await page.locator('.topbar > .next-actions').count(),1,'the next task occupies the shared top bar');
 assert.equal(await page.locator('.workspace-area .next-actions').count(),0,'recommendations do not consume training list space');
 await page.locator('.next-actions').hover();await page.locator('.next-actions-popover').waitFor();
 const firstAdvice=page.locator('.next-actions-popover .next-actions-item').first();
 const reasonId=await firstAdvice.getAttribute('aria-describedby');assert(reasonId);
 assert.match(await page.locator('[id="'+reasonId+'"]').textContent(),/证据|独立|基础/);
 assert.equal(await page.locator('.next-actions-reason,.next-actions-primary small').count(),0);
 assert(await firstAdvice.getAttribute('aria-describedby'),'The recommendation evidence remains available to assistive technology');
 await page.keyboard.press('Escape');assert.equal(await page.locator('.next-actions-popover').count(),0);
 assert.deepEqual(await nav().getByRole('button').allTextContents(),['我的训练','题单','从零讲','成长','提交记录','活动记录']);
 assert.equal(await page.getByRole('button',{name:'比赛日历',exact:true}).count(),0);
 assert.equal(await page.locator('[data-recommendation="course"]').count(),0);
 await page.keyboard.press('Control+2');assert.equal(await page.locator('.workspace-area').getAttribute('data-page'),'mine','locked page shortcuts use the shared level rule');
 await page.keyboard.press('Control+k');const commands=page.getByRole('dialog',{name:'快捷操作',exact:true});await commands.waitFor();
 assert.equal(await commands.getByRole('button',{name:/打开题库/}).count(),0);assert.equal(await commands.getByRole('button',{name:/打开实验室/}).count(),0);await page.keyboard.press('Escape');
 await load(1,true);assert.equal(await page.locator('.workspace-area').getAttribute('data-page'),'training-lists');
 await page.locator('.training-list-path').getByRole('button',{name:'01 编程基础',exact:true}).waitFor();
 await load(1);
 await nav().getByRole('button',{name:'题单',exact:true}).click();await page.locator('.training-list-path').getByRole('button',{name:'01 编程基础',exact:true}).waitFor();
 await page.locator('.training-list-content').getByText('输入输出与顺序结构',{exact:true}).click();
 await page.locator('.training-list-table .problem-title').first().click();await page.locator('.cm-content').waitFor();
 assert.equal(await page.getByRole('button',{name:'打开模板',exact:true}).count(),1,'in-problem help stays available at Lv1');
 await page.locator('.cm-content').fill('#include <iostream>\nint main(){std::cout<<3;}');
 await page.getByRole('button',{name:'自测运行',exact:true}).click();await page.locator('.wb-result-summary').getByText('样例通过',{exact:false}).waitFor();assert(sampleRequested);
 const officialReceipt=page.waitForResponse(response=>new URL(response.url()).pathname==='/api/official/status');
 await page.getByRole('button',{name:'提交',exact:true}).click();await officialReceipt;await page.waitForTimeout(400);assert(officialRequested,'formal original-site submission entry works at Lv1; requests are fixture-only');
 await page.getByRole('button',{name:'返回主界面',exact:true}).click();
 await page.locator('.study-browser').waitFor({state:'hidden'});
 await page.evaluate(async()=>{const pending=[];window.dispatchEvent(new CustomEvent('tb-before-update',{detail:{waitUntil:value=>pending.push(Promise.resolve(value))}}));await Promise.all(pending);});
 await load(1);
 await openSettings(page,'新手指引');
 await page.locator('.tour-guide-grid').waitFor();
 assert.equal(await page.locator('.tour-guide-grid').getByRole('button',{name:'模拟赛',exact:true}).count(),0);
 assert.equal(await page.locator('.tour-guide-grid').getByRole('button',{name:'题单',exact:true}).count(),1);
 await load(3);assert.equal(await nav().getByRole('button',{name:'模板',exact:true}).count(),1);assert.equal(await nav().getByRole('button',{name:'模拟赛',exact:true}).count(),0);
 await load(4);await nav().getByRole('button',{name:'实验室',exact:true}).click();await page.getByRole('button',{name:'打开算法 排序基础',exact:true}).click();assert.match(await page.locator('.lab-course-header h1').textContent(),/排序基础/);await page.getByRole('button',{name:'返回主界面',exact:true}).click();
 await load(11);assert.equal(await nav().getByRole('button').count(),14);
 await openSettings(page,'交互与导航');
 assert(await page.getByRole('checkbox',{name:'显示 我的训练',exact:true}).isDisabled());
 await page.getByRole('checkbox',{name:'显示 题单',exact:true}).uncheck();
 await page.getByRole('checkbox',{name:'显示 模板',exact:true}).uncheck();
 assert.equal(await nav().getByRole('button',{name:'题单',exact:true}).count(),0);
 assert.equal(await nav().getByRole('button',{name:'模板',exact:true}).count(),0);
 await nav().getByRole('button',{name:'题库',exact:true}).click();await page.locator('.problem-table').waitFor();
 assert.equal(await page.getByRole('button',{name:'将筛选结果加入题单',exact:true}).count(),0);
 assert.equal(await page.getByRole('button',{name:'加入题单 实际基础练习',exact:true}).count(),0);
 await openSettings(page,'新手指引');
 await page.locator('.tour-guide-grid').waitFor();
 assert.equal(await page.locator('.tour-guide-grid').getByRole('button',{name:'题单',exact:true}).count(),0);
 assert.equal(await page.locator('.tour-guide-grid').getByRole('button',{name:'模板',exact:true}).count(),0);
 await openSettings(page,'交互与导航');await page.getByRole('checkbox',{name:'显示 题单',exact:true}).check();
 assert.equal(await nav().getByRole('button',{name:'题单',exact:true}).count(),1);
 // Existing custom group and hide changes survive account-owned persistence.
 preferences={...preferences,navGroups:{library:'学习','training-lists':'学习'}};await load(11);await openSettings(page,'交互与导航');
 assert.equal(await nav().getByRole('button',{name:'学习',exact:true}).count(),1);
 await page.getByRole('checkbox',{name:'显示 题单',exact:true}).uncheck();
 assert.equal(await nav().getByRole('button',{name:'学习',exact:true}).count(),1);
 await nav().getByRole('button',{name:'学习',exact:true}).click();
 assert.equal(await page.getByRole('tab',{name:'题单',exact:true}).count(),0);
 await openSettings(page);await mkdir('tests/screenshots/navigation-learning',{recursive:true});
 for(const [width,font] of [[960,15],[1294,15],[1440,22]]){
  await page.setViewportSize({width,height:850});
  if(font===22){await openSettings(page,'外观');await page.getByRole('spinbutton',{name:'界面字号',exact:true}).fill('22');await page.getByRole('spinbutton',{name:'界面字号',exact:true}).press('Enter');await openSettings(page);}
  await page.locator('.settings-home-grid').waitFor();
  const geometry=await page.locator('.settings-home-grid').evaluate(grid=>{const parent=grid.getBoundingClientRect(),rects=[...grid.querySelectorAll('.settings-tile')].map(node=>node.getBoundingClientRect());return {width:parent.width,rects:rects.map(r=>({left:r.left-parent.left,top:r.top-parent.top,right:r.right-parent.left,bottom:r.bottom-parent.top})),overflow:document.documentElement.scrollWidth>innerWidth};});
  assert.equal(geometry.rects.length,9);assert(!geometry.overflow);
  for(const rect of geometry.rects)assert(rect.left>=-1&&rect.right<=geometry.width+1);
  for(let i=0;i<geometry.rects.length;i++)for(let j=i+1;j<geometry.rects.length;j++){const a=geometry.rects[i],b=geometry.rects[j];assert(a.right<=b.left+1||b.right<=a.left+1||a.bottom<=b.top+1||b.bottom<=a.top+1,'settings tiles must not overlap');}
  await page.screenshot({path:`tests/screenshots/navigation-learning/settings-${width}-${font}.png`,animations:'disabled'});
 }
 await page.emulateMedia({reducedMotion:'reduce'});await page.waitForTimeout(100);
 const animation=await page.locator('.settings-home-grid').evaluate(node=>node.getAnimations({subtree:true}).filter(animation=>animation.playState==='running').length);
 assert.equal(animation,0,'OS reduced motion disables home animations');
 // The preceding hide/group scenario deliberately removes the only source
 // foundation list. Restore its real entrypoint before testing recommendation
 // geometry: without that list these fixture rows also require an unsupported
 // sorting technique, so the strict model is right to offer no task.
 await openSettings(page,'交互与导航');
 const restoredPreferences=page.waitForResponse(response=>{
  if(new URL(response.url()).pathname!=='/api/preferences'||response.request().method()!=='POST')return false;
  const hidden=response.request().postDataJSON().preferences?.hiddenNavPages;
  return Array.isArray(hidden)&&!hidden.includes('training-lists')&&!hidden.includes('templates');
 });
 await page.getByRole('checkbox',{name:'显示 题单',exact:true}).check();
 await page.getByRole('button',{name:'显示 模板',exact:true}).click();
 assert.equal((await restoredPreferences).status(),200,'Geometry starts only after restored account preferences are saved');
 assert(!preferences.hiddenNavPages.includes('training-lists')&&!preferences.hiddenNavPages.includes('templates'));
 for(const theme of ['dark','light'])for(const fontSize of [15,22])for(const width of [2048,1294,960,430]){
  preferences={...preferences,theme,fontSize};await page.setViewportSize({width,height:850});await load(11);
  const recommendation=page.locator('.topbar > .next-actions');await recommendation.hover();await page.locator('.next-actions-popover').waitFor();
  const geometry=await page.locator('.next-actions-popover').evaluate(node=>{const r=node.getBoundingClientRect(),header=document.querySelector('.topbar');return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:innerWidth,height:innerHeight,headerOverflow:header.scrollWidth>header.clientWidth+1};});
  const trigger=await recommendation.boundingBox();
  const spacing=await recommendation.evaluate(node=>{const control=node.getBoundingClientRect(),button=node.querySelector('.next-actions-primary'),title=button.querySelector('strong'),range=document.createRange();range.selectNodeContents(title);const css=getComputedStyle(button),icon=button.querySelector('svg').getBoundingClientRect();return {width:control.width,natural:range.getBoundingClientRect().width+icon.width+parseFloat(css.columnGap)+parseFloat(css.paddingLeft)+parseFloat(css.paddingRight),gap:document.querySelector('.topbar-actions').getBoundingClientRect().left-control.right};});
  assert(spacing.width<=spacing.natural+1,'No reserved blank width after the recommendation: '+JSON.stringify(spacing));
  if(width>=960)assert(spacing.gap>=0&&spacing.gap<=13,'Recommendation sits next to the right-side statistics: '+JSON.stringify(spacing));
  const popupWidth=geometry.right-geometry.left,alignedLeft=Math.max(10,Math.min(trigger.x,width-popupWidth-10));
  assert(Math.abs(geometry.left-alignedLeft)<.75&&popupWidth>0&&popupWidth<=width-16,'Real App compact popup aligns with the control and fits the viewport: '+JSON.stringify({theme,fontSize,width,geometry,trigger}));
  const primaryName=await recommendation.locator('.next-actions-primary').getAttribute('aria-label');
  assert.equal(await page.locator('.next-actions-popover').getByRole('button',{name:primaryName,exact:true}).count(),0);
  assert.equal(await recommendation.locator('.next-actions-primary .lucide-arrow-right').count(),0);
  assert.equal(await page.locator('.next-actions-popover .lucide-arrow-right').count(),0);
  assert.equal(await recommendation.locator('.next-actions-toggle,.lucide-chevron-down').count(),0,'Actual App recommendation has no separate expansion arrow');
  assert(await recommendation.locator('.next-actions-primary').evaluate(node=>{const style=getComputedStyle(node);return style.backgroundColor==='rgba(0, 0, 0, 0)'&&parseFloat(style.borderWidth)===0&&style.boxShadow==='none';}),'Actual App primary recommendation stays transparent and borderless');
  assert(await page.locator('.next-actions-popover .next-actions-item').count()<=5);
  assert(geometry.left>=0&&geometry.right<=geometry.width+1&&geometry.top>=0&&geometry.bottom<=geometry.height+1,JSON.stringify(geometry));
  assert.equal(geometry.headerOverflow,false,`topbar remains usable at ${width}px / ${fontSize}px / ${theme}`);
  if(width===2048&&fontSize===15&&theme==='dark')await page.screenshot({path:'../.backups/interaction-1434/right-alignment/topbar-right-dark.png'});
  await page.screenshot({path:`tests/screenshots/navigation-learning/next-${theme}-${width}-${fontSize}.png`,animations:'disabled'});await page.keyboard.press('Escape');
 }
 // Newly unlocked guides become available without interrupting with a tour.
 await page.waitForTimeout(800);
 preferences={theme:'dark',onboardingGuideVersion:2,onboardingCompleted:true,onboardingUnlockedPages:availablePages(1),levelNoticeVersion:1,levelNoticeSeen:2,levelNoticePending:0};
 await page.evaluate(()=>localStorage.clear());await load(2);
 const unlockedGuide=page.getByRole('dialog',{name:'新手指引',exact:true});
 assert.equal(await unlockedGuide.count(),0);
 await openSettings(page,'新手指引');assert.equal(await page.locator('.tour-guide-grid').getByRole('button',{name:'排行榜',exact:true}).count(),1);assert.equal(await page.locator('.tour-guide-grid').getByRole('button',{name:'模板',exact:true}).count(),0);
 await load(2);assert.equal(await unlockedGuide.count(),0,'acknowledged unlock guides do not repeat on restart');
 // Exercise the actual App persistence queue rather than only the observer model.
 preferences={theme:'dark',onboardingGuideVersion:2,onboardingCompleted:true,onboardingUnlockedPages:availablePages(1),levelNoticeVersion:1,levelNoticeSeen:1,levelNoticePending:0};
 await page.evaluate(()=>{localStorage.clear();sessionStorage.clear();});await load(1);
 preferenceSaveFailures=2;const savesBefore=preferenceSaveAttempts;await load(2);
 const promotion=page.getByRole('dialog',{name:'等级提升',exact:true});await promotion.waitFor();await page.keyboard.press('Escape');
 for(let i=0;i<100&&preferences.levelNoticeSeen!==2;i++){await page.waitForTimeout(100);assert.equal(await promotion.count(),0,'save failure cannot repeat an acknowledged celebration');}
 assert.equal(preferences.levelNoticeSeen,2,'failed account preference writes retry and eventually persist');assert(preferenceSaveAttempts-savesBefore>=3);
 await page.evaluate(()=>{localStorage.clear();sessionStorage.clear();});await load(2);assert.equal(await promotion.count(),0,'durable acknowledgement survives clearing browser mirrors and restarting');
 assert.deepEqual(errors,[]);assert.deepEqual(unknown,[]);
 console.log('PASS real App level gates, course handoff, hidden-dependent actions, protected essential pages, guide visibility, groups, settings responsive/reducedmotion');
}catch(error){console.error(JSON.stringify({errors,unknown,body:(await page.locator('body').innerText()).slice(0,1600)}));throw error;}finally{await browser.close();await vite.close();}
