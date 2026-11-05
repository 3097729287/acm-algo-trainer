import assert from 'node:assert/strict';
import { mkdir,writeFile } from 'node:fs/promises';
import { createServer,preview } from 'vite';
import { chromium } from 'playwright';
import {emptyStudyBrowser,openStudyTab,studySnapshot} from '../src/lib/learningBrowser.js';

const built=process.env.TB_TEST_BUILT==='1';
const vite=built?await preview({preview:{host:'127.0.0.1',port:0}}):await createServer({cacheDir:'../.backups/training-split-quiz-20261105/vite-workspace',optimizeDeps:{entries:['index.html']},server:{host:'127.0.0.1',port:0,watch:null}});
if(built)vite.close=()=>new Promise((resolve,reject)=>vite.httpServer.close(error=>error?reject(error):resolve()));else await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[],writes=[];
page.on('pageerror',error=>errors.push(error.message));
page.setDefaultTimeout(12000);
const timestamp=new Date().toISOString(),date=new Date().toLocaleDateString('sv-SE',{timeZone:'Asia/Shanghai'});
const self={userId:'11111111-1111-4111-8111-111111111111',nickname:'训练者甲'},other={userId:'22222222-2222-4222-8222-222222222222',nickname:'训练者乙'};
const rows=Array.from({length:120},(_,index)=>({id:`fixture::${index}`,contest:'周赛 166',problem:String(index+1),title:`列表定位测试 ${String(index+1).padStart(3,'0')}`,tags:['模拟'],knowledge:'模拟',platform:'牛客',series:'周赛',difficulty:800+index*10,url:`https://ac.nowcoder.com/acm/contest/142622/${index+1}`,contestDate:'2026-10-20T00:00:00Z',solutionAvailable:true}));
for(const row of rows){row.contestProblemCount=rows.filter(item=>item.contest===row.contest&&item.platform===row.platform).length;row.catalogContentReady=true;}
const training=rows.map(row=>({id:row.id,activeAt:timestamp,lastActivityAt:timestamp,today:true,accepted:false,verdict:null,attempts:0}));
let preferences=null,likes={total:4,likedToday:false},failLike=true,failAutomaticRead=true,boardDay=date,notifications=[{id:'33333333-3333-4333-8333-333333333333',kind:'comment',actor:other,recipient:self,text:'一起加油 <script>window.untrusted=true</script>',createdAt:timestamp,read:false}];
notifications.push(...Array.from({length:100},(_,index)=>({id:`55555555-5555-4555-8555-${String(index).padStart(12,'0')}`,kind:index<3?'like':'comment',text:index<3?'':`分页留言 ${index}`,actor:other,recipient:self,createdAt:timestamp,read:false})));
const workspace=()=>({training,sets:[],contests:[],activeContest:null,goals:{goals:[]},goalTasks:[],summary:{total:120,accepted:training.filter(row=>row.accepted).length,todayAccepted:0,attempts:0,due:0,pending:0,streak:1},now:timestamp});
const progress={badge:'tier-7',level:8,tier:'大师',rankTier:'大师',rankScore:2000,titles:[]};
const ranked={badge:'tier-7',tier:'大师',qualified:true,abilityScore:2000,nextAbilityScore:2100,evidenceCount:8,minimumEvidence:5,levelGate:5};
ranked.tierRequirements=['黑铁','青铜','白银','黄金','翡翠','钻石','大师','宗师','王者'].map((tier,index)=>({tier,badge:`tier-${index}`,minAbilityScore:[0,800,1000,1200,1600,1800,2000,2100,2200][index]}));
const hub={settings:{githubRepo:'3097729287/acm-algo-trainer',accounts:{},autoSync:false,intervalHours:6,minDifficulty:0,maxDifficulty:2199},sync:{busy:false},updates:{currentVersion:'1.1.5'},accounts:[],notifications:[]};
const legacyTasks=studySnapshot([['overview','学习概览'],['week','本周计划'],['progress','专题进度'],['history','历史记录'],['today','今日任务']].reduce((state,[id,title])=>openStudyTab(state,{kind:'panel',id,title}),emptyStudyBrowser()));
await page.addInitScript(legacy=>localStorage.setItem('tb.preferences',JSON.stringify({onboardingGuideVersion:2,theme:'dark',accent:'teal',backdrop:'aurora',panelOpacity:35,widgets:true,fontSize:16,navOrder:['mine','library','training-lists','competitions','mock','duel','tasks','lectures','wiki','templates','paths','growth','records','activity','rankings'],learningPaths:{sectionWorkspaces:{tasks:legacy}},views:[]})),legacyTasks);

let summaryRevision=1;
let summary={version:1,revision:'1',config:{goal:{kind:'xcpc',title:'区域赛铜牌',deadline:''},weekdayMinutes:60,weekendMinutes:60,restDays:[],team:false,role:''},plan:{id:'plan-fixture',week:date,tasks:[{key:'lecture-one',kind:'lecture',id:'fixture-lecture',title:'滑动窗口：边界处理',date,status:'pending',minutes:20,order:1,topicId:'window'},{key:'problem-one',kind:'problem',id:rows[0].id,title:'最长不重复子串',date,status:'pending',minutes:25,order:2,topicId:'window'},{key:'review-one',kind:'review',id:rows[1].id,title:'前缀和间隔复习',date,status:'pending',minutes:15,order:3,topicId:'prefix'}],days:Array.from({length:7},(_,i)=>({date:new Date(Date.now()+i*86400000).toLocaleDateString('sv-SE',{timeZone:'Asia/Shanghai'}),minutes:60})),tracks:['window','prefix'],waiting:[],gaps:[]},proposal:null,article:[],topics:[{id:'window',title:'双指针与滑动窗口',independent:2,retained:1,level:6,mixed:false,label:'隔一段时间仍能完成'}],availableTopics:[{id:'window',title:'双指针与滑动窗口'},{id:'prefix',title:'前缀和与差分'}],history:[{id:'empty-history',at:timestamp,reason:'首次规划'},{id:'plan-history',week:date,at:timestamp,reason:'调整时间安排'}],view:{mode:'float',pinned:true},seen:{},recommendation:{title:'双指针与滑动窗口',reason:'先检查窗口边界。'},effectiveSeconds:5400};

await page.route('**/api/**',async route=>{
  const request=route.request(),url=new URL(request.url()),path=url.pathname;
  if(!path.startsWith('/api/'))return route.continue();
  const body=request.method()==='POST'?request.postDataJSON():null;
  if(body)writes.push({path,body});
  let value;
  if(path==='/api/account')value={required:false,authenticated:true,usesOriginalWorkspace:true,token:'fixture',account:self};
  else if(path==='/api/learning-summary/history')value={id:url.searchParams.get('id'),article:[{id:'archive',title:'当时的重点',text:'历史内容保留'}],plan:url.searchParams.get('id')==='empty-history'?{}:summary.plan};
  else if(path==='/api/learning-summary/quiz')value={topicId:'window',question:'读取两个整数 a、b 并输出它们的和，需要输出什么？',options:['a+b 的值','字符 a+b','两个变量的地址']};
  else if(path==='/api/training-lists')value={lists:[]};
  else if(path.startsWith('/api/learning-summary')){
 if(path.endsWith('/update')){if(body.action==='configure'){summary={...summary,config:body.config,proposal:{...summary.plan,id:'proposed-'+summaryRevision,tracks:body.tracks||summary.plan.tracks,reason:'更新可用时间'}};}else if(body.action==='accept'){summary={...summary,plan:summary.proposal||summary.plan,proposal:null};}else if(body.action==='view'){summary={...summary,view:body.view};}summary={...summary,revision:String(++summaryRevision)};}value=summary;
 }
 else if(path==='/api/wiki')value={articles:[]};
 else if(path==='/api/templates')value={templates:[]};
 else if(path==='/api/training-list-likes')value={likes:[]};
  else if(path==='/api/preferences'){if(body)preferences=body.preferences;value={preferences,updatedAt:timestamp};}
  else if(path==='/api/contest-calendar')value={contests:[],refreshing:false,importing:false};
  else if(path==='/api/content-update')value={revision:0,status:'current',error:''};
  else if(path==='/api/software-update')value={currentVersion:'1.1.5',status:'current',autoCheck:false,canInstall:false};
  else if(path==='/api/browser-preparation')value={available:false};
  else if(path==='/api/data')value={rows,categories:[],token:'fixture',today:date,revision:'ui-social'};
  else if(path==='/api/workspace')value=workspace();
  else if(path==='/api/hub')value=hub;
  else if(path==='/api/hub/dismiss-all')value=hub;
  else if(path==='/api/insights')value={summary:{officialSolved:0,submissions:0,activeDays:1,streak:1},growth:{confirmed:true,authority:{owner:self.userId,epoch:'legacy-fixture',revision:1},...progress,totalXp:6265,currentLevelXp:665,nextLevelXp:1600,ranked},knowledge:[],achievements:[],activity:[],recommendations:[],assessment:{platforms:[]},dailyTasks:{date,tasks:[{id:'solve',title:'AC',description:'AC 1 道不同题目',kind:'solve',progress:1,target:1,completed:true,claimed:false,xp:25},{id:'review',title:'复习',description:'复习 1 道题',kind:'review',progress:0,target:1,completed:false,claimed:false,xp:10},{id:'learning',title:'使用时长',description:'学习 5 分钟',kind:'learning',progress:5,target:5,completed:true,claimed:true,xp:10}]}};
  else if(path==='/api/profile')value={profile:self,leaderboard:{configured:true,status:'ready'}};
  else if(path==='/api/duel/board')value={owner:self.userId,mode:'ranked',date,entries:[{...self,rank:1,rating:1245,online:true},{...other,rank:2,rating:1100,online:false}],records:[]};
  else if(path==='/api/goals')value={goals:[]};
  else if(path==='/api/contests/events')value={events:[]};
  else if(path==='/api/submissions')value={submissions:[],total:0,hasMore:false};
  else if(path==='/api/lectures')value={lectures:[]};
  else if(path==='/api/desktop/fullscreen')value={available:false,fullscreen:false};
  else if(path==='/api/training/start')value={workspace:workspace()};
  else if(path==='/api/problem')value={id:url.searchParams.get('id'),title:rows.find(row=>row.id===url.searchParams.get('id')).title,markdown:'## 题目描述\n\n测试题面。\n\n## 样例\n\n```text\n1 2\n```',samples:[{input:'1\n',output:'2\n'}],limits:{timeMs:2000,memoryMb:256},judge:{scope:'samples',cases:1},statementAvailable:true,draft:'int main() { return 0; }',submissions:[]};
  else if(path==='/api/draft')value={savedAt:timestamp};
  else if(path==='/api/translation/settings')value={provider:'custom',providerName:'自定义',model:'fixture',configured:false,keyStored:false,providers:[]};
  else if(path==='/api/leaderboard')value={period:url.searchParams.get('period')||'daily',date:boardDay,configured:true,status:'ready',hasSnapshot:true,socialAvailable:true,socialProtocol:1,isAdmin:false,entries:[{...self,rank:1,count:2,likes:{total:9,likedToday:false},publicProgress:progress},{...other,rank:2,count:1,likes,publicProgress:progress}],self};
  else if(path==='/api/leaderboard/sync')value={queued:true};
  else if(path==='/api/social')value={available:true,protocol:1,totalLikes:9,todayLikes:3,unreadCount:notifications.filter(row=>!row.read).length,notifications:notifications.slice(0,100),activity:likes.likedToday?[{id:'44444444-4444-4444-8444-444444444444',kind:'like',actor:self,recipient:other,createdAt:timestamp}]:[]};
  else if(path==='/api/social/likes'){
    await new Promise(resolve=>setTimeout(resolve,120));
    if(failLike){failLike=false;await route.fulfill({status:503,json:{error:'测试连接中断'}});return;}
    likes={total:likes.total+(likes.likedToday?0:1),likedToday:true};value={created:true,targetId:other.userId,likes};
  }
  else if(path==='/api/social/comments'){
    const reply={id:body.requestId,text:body.text,createdAt:timestamp};
    if(body.replyTo){const original=notifications.find(item=>item.id===body.replyTo);assert(original);original.myReplies=[...(original.myReplies||[]).filter(item=>item.id!==reply.id),reply];}
    value={created:true,id:body.requestId,createdAt:timestamp};
  }
  else if(path==='/api/social/read'){
    if(failAutomaticRead&&body.ids){failAutomaticRead=false;await route.fulfill({status:503,json:{error:'自动已读暂未完成，请重试'}});return;}
    notifications=notifications.map(row=>body.all===true||body.ids?.includes(row.id)?{...row,read:true}:row);value={ok:true};
  }
  else {await route.fulfill({status:404,json:{error:'fixture missing '+path}});return;}
  await route.fulfill({json:value});
});
const nav=name=>page.locator('.sidebar').getByRole('button',{name,exact:true});
const out='../.backups/training-split-quiz-20261105/app-checks';await mkdir(out,{recursive:true});
try{
 await page.goto(vite.resolvedUrls.local[0]);await page.locator('.problem-table tr[data-id]').first().waitFor();await nav('任务').waitFor();
 if(process.argv.includes('--appearance'))await (await import('./surface-appearance.mjs')).checkSurfaceAppearance({page,nav,out});
 for(const name of ['我的训练','任务','学习','竞赛','成长','排行榜'])assert.equal(await nav(name).count(),1,name);
 assert.deepEqual(await page.locator('.sidebar [data-navigation-id]').allTextContents(),['我的训练','任务','学习','竞赛','成长','排行榜']);
 assert.deepEqual(await page.getByRole('tablist',{name:'组合页面 我的训练'}).getByRole('tab').allTextContents(),['我的训练','题库','题单']);
 const train=page.locator('[data-section=training]'),minePane=train.getByRole('tabpanel',{name:'我的训练',exact:true}),libraryPane=train.getByRole('tabpanel',{name:'题库',exact:true});
 await page.locator('#tb-page-search input').fill('测试 005');await page.waitForFunction(()=>document.querySelectorAll('#section-panel-mine tr[data-id]').length===1);assert.equal(await minePane.locator('tr[data-id]').count(),1);
 await page.locator('#tb-page-bookmarks').getByRole('tab',{name:'题库',exact:true}).click();await page.locator('#tb-page-search input').fill('测试 010');await libraryPane.locator('tr[data-id]').first().waitFor();
 await page.locator('#tb-page-bookmarks').getByRole('tab',{name:'我的训练',exact:true}).click();assert.equal(await page.locator('#tb-page-search input').inputValue(),'测试 005');
 await page.locator('#tb-page-bookmarks').getByRole('tab',{name:'题库',exact:true}).click();assert.equal(await page.locator('#tb-page-search input').inputValue(),'测试 010');
 await page.locator('#tb-page-bookmarks').getByRole('tab',{name:'我的训练',exact:true}).click();assert(await minePane.isVisible());assert(!(await libraryPane.isVisible()));assert.equal(await minePane.locator('tr[data-id]').count(),1);
 await minePane.locator('tr[data-id]').first().click({position:{x:2,y:2},button:'right'});await minePane.getByRole('region',{name:'题目列表'}).focus();await page.keyboard.press('/');assert.equal(await page.locator('#tb-page-search input').inputValue(),'测试 005');
 await page.locator('#tb-page-bookmarks').getByRole('tab',{name:'题库',exact:true}).click();await page.locator('#tb-page-search input').fill('');await libraryPane.locator('tr[data-id]').nth(1).waitFor();await libraryPane.getByRole('button',{name:'题库下一页',exact:true}).click();const libraryFirst=await libraryPane.locator('tr[data-id]').first().getAttribute('data-id');
 await page.locator('#tb-page-bookmarks').getByRole('tab',{name:'我的训练',exact:true}).click();assert.equal(await minePane.locator('tr[data-id]').count(),1);await page.locator('#tb-page-bookmarks').getByRole('tab',{name:'题库',exact:true}).click();assert.equal(await libraryPane.locator('tr[data-id]').first().getAttribute('data-id'),libraryFirst,'Returning preserves the library page');
 await page.locator('#tb-page-bookmarks').getByRole('tab',{name:'题单',exact:true}).dragTo(page.locator('#tb-page-bookmarks').getByRole('tab',{name:'题库',exact:true}));assert.equal(await train.locator('.section-pane').count(),1);assert.equal(await train.getByRole('separator').count(),0);assert.equal(await train.locator('.section-split-button').count(),0);
 await nav('竞赛').click();assert.deepEqual(await page.getByRole('tablist',{name:'组合页面 竞赛'}).getByRole('tab').allTextContents(),['比赛','模拟赛','对战']);
 await page.getByRole('tab',{name:'模拟赛',exact:true}).dragTo(page.getByRole('tab',{name:'比赛',exact:true}));assert.deepEqual(await page.getByRole('tablist',{name:'组合页面 竞赛'}).getByRole('tab').allTextContents(),['模拟赛','比赛','对战']);
 const sourceLink=page.getByRole('link',{name:'前往原站 周赛 166',exact:true});await sourceLink.waitFor();assert.equal(await sourceLink.getAttribute('href'),'https://ac.nowcoder.com/acm/contest/142622');assert.equal(await sourceLink.getAttribute('target'),'_blank');
 await page.context().route('https://ac.nowcoder.com/acm/contest/142622',route=>route.fulfill({contentType:'text/html',body:'<h1>Isolated original contest</h1>'}));const [original]=await Promise.all([page.waitForEvent('popup'),sourceLink.click()]);await original.waitForLoadState();assert.equal(original.url(),'https://ac.nowcoder.com/acm/contest/142622');await original.close();assert.equal(await page.locator('.competition-detail').count(),0,'Opening the original contest does not enter or start a local match');
 assert.equal(await page.locator('.sidebar').getByRole('button',{name:'题库',exact:true}).count(),0);
 await nav('学习').click();const workspace=page.locator('.section-workspace[data-section=learning]');await workspace.waitFor();
 for(const name of ['从零讲','维基百科','模板','实验室'])assert.equal(await page.getByRole('tab',{name,exact:true}).count(),1);
 for(const [name,label,text] of [['从零讲','搜索从零讲知识','lecture-query'],['维基百科','搜索维基百科','wiki-query'],['模板','搜索模板','template-query'],['实验室','搜索算法','lab-query']]){
  if(name==='从零讲'){await page.getByRole('tab',{name,exact:true}).click();assert.equal(await workspace.locator('.lecture-catalogue').count(),1);assert.equal(await workspace.locator('.lectures-intro,.lectures-detail').count(),0);}
  await page.getByRole('tab',{name,exact:true}).click();const search=page.locator('#tb-page-search').getByRole('textbox',{name:label,exact:true});await search.waitFor();assert.equal(await page.locator('#tb-page-search input').count(),1);assert.equal(await workspace.locator('.section-document-tools input').count(),0);const box=await search.boundingBox();assert(box.x>(await page.locator('#tb-page-bookmarks').boundingBox()).x&&box.y<100,'Search follows the topbar bookmarks');await search.fill(text);
 }
 await page.locator('#tb-page-bookmarks').getByRole('tab',{name:'维基百科',exact:true}).click();assert.equal(await page.locator('#tb-page-search').getByRole('textbox',{name:'搜索维基百科',exact:true}).inputValue(),'wiki-query');
 await page.locator('#tb-page-bookmarks').getByRole('tab',{name:'模板',exact:true}).dragTo(page.locator('#tb-page-bookmarks').getByRole('tab',{name:'从零讲',exact:true}));assert.equal(await workspace.locator('.section-pane').count(),1);assert.equal(await workspace.locator('.section-split-button').count(),0);await page.locator('#tb-page-bookmarks').getByRole('tab',{name:'维基百科',exact:true}).click();assert.equal(await page.locator('#tb-page-search').getByRole('textbox',{name:'搜索维基百科',exact:true}).inputValue(),'wiki-query');
 await nav('任务').click();const board=page.locator('[data-section=tasks]');await board.locator('.task-now').waitFor();
 const oldStyle=await page.locator('html').getAttribute('style'),oldTheme=await page.locator('html').getAttribute('data-theme'),opacityOverride=await page.addStyleTag({content:':root{}'});
 for(const theme of ['dark','light'])for(const opacity of [0,35,76,100]){
  await opacityOverride.evaluate((node,opacity)=>node.textContent=':root{--panel-opacity:'+opacity+'%!important}',opacity);await page.locator('html').evaluate((node,theme)=>node.dataset.theme=theme,theme);
  for(const title of ['学习概览','本周计划','专题进度','历史记录']){await page.locator('#tb-page-bookmarks').getByRole('tab',{name:title,exact:true}).click();const paint=await board.locator('.section-document:not([hidden]) .task-card').first().evaluate(el=>{const alpha=color=>{const canvas=document.createElement('canvas');canvas.width=canvas.height=1;const c=canvas.getContext('2d');c.fillStyle=color;c.fillRect(0,0,1,1);return c.getImageData(0,0,1,1).data[3]/255;};return {card:alpha(getComputedStyle(el).backgroundColor),pane:alpha(getComputedStyle(el.closest('.task-board-pane')).backgroundColor),text:alpha(getComputedStyle(el).color)};});assert(Math.abs(paint.card-opacity/100)<.006,JSON.stringify(paint));assert.equal(paint.pane,0);assert.equal(paint.text,1);}
 }
 await opacityOverride.evaluate(node=>node.remove());await page.evaluate(({oldStyle,oldTheme})=>{document.documentElement.setAttribute('style',oldStyle);document.documentElement.dataset.theme=oldTheme;},{oldStyle,oldTheme});await page.locator('#tb-page-bookmarks').getByRole('tab',{name:'学习概览',exact:true}).click();
 const boardBox=await board.boundingBox(),areaBox=await page.locator('.workspace-area').boundingBox();assert(boardBox.width>=areaBox.width-1,'Workspace fills the available width');
 const main=board.locator('.task-now'),mainBox=await main.boundingBox(),nextBox=await board.locator('.task-next').boundingBox();assert(mainBox.width>nextBox.width*1.5,'The mainline gets the main area');await main.getByText('当前主线',{exact:true}).waitFor();await main.getByRole('heading',{name:'双指针与滑动窗口、前缀和与差分',exact:true}).waitFor();await main.getByText('完成条件：读完讲解后确认完成',{exact:true}).waitFor();
 assert.equal(await page.getByRole('tab').count(),4);assert.equal(await board.locator('.task-daily-summary,.task-inline-time,.task-inline-feedback').count(),0);assert.equal(await board.getByRole('spinbutton').count(),0,'Settings stay behind a button');assert.equal(await board.getByRole('textbox',{name:'待办名称',exact:true}).count(),0);
 for(const tab of await page.getByRole('tab').all())assert.equal(await tab.locator(':scope>svg').count(),1,'Every bookmark has one corresponding icon');
 const overviewSearch=page.locator('#tb-page-search input');await overviewSearch.fill('最长');assert.equal(await board.locator('.task-search-results .task-board-row').count(),1);
 await page.getByRole('tab',{name:'本周计划',exact:true}).click();assert.equal(await overviewSearch.inputValue(),'');await overviewSearch.fill('前缀');assert.equal(await board.locator('.task-page-heading h1').count(),0);
 await page.getByRole('tab',{name:'学习概览',exact:true}).click();assert.equal(await overviewSearch.inputValue(),'最长');await overviewSearch.fill('');
 await page.getByRole('tab',{name:'本周计划',exact:true}).click();assert.equal(await overviewSearch.inputValue(),'前缀');await overviewSearch.fill('');await page.getByRole('tab',{name:'学习概览',exact:true}).click();
 const dailyButton=page.locator('.app-statusbar').getByRole('button',{name:'每日任务',exact:true});await dailyButton.click();const dailyDialog=page.getByRole('dialog',{name:'每日任务',exact:true});await dailyDialog.locator('.daily-task').first().waitFor();assert.equal(await dailyDialog.locator('.daily-task').count(),3);await page.keyboard.press('Escape');
 await board.getByRole('button',{name:'可用时间',exact:true}).click();const settings=page.getByRole('dialog',{name:'可用时间',exact:true});
 const time=settings.getByRole('spinbutton',{name:'平日可用时间',exact:true});assert.equal(await time.inputValue(),'60');assert.equal(await time.getAttribute('min'),'60');
 await time.fill('15');await time.press('Tab');assert.equal(await time.inputValue(),'60');
 const group=settings.getByRole('group',{name:'平日可用时间',exact:true});await group.getByRole('button',{name:'平日可用时间增加30分钟',exact:true}).click();await page.waitForFunction(()=>document.querySelector('[aria-label="平日可用时间"] input')?.value==='90');assert.equal(await time.inputValue(),'90');await group.getByRole('button',{name:'平日可用时间增加60分钟',exact:true}).click();await page.waitForFunction(()=>document.querySelector('[aria-label="平日可用时间"] input')?.value==='150');assert.equal(await time.inputValue(),'150');
 await settings.getByRole('spinbutton',{name:'周末可用时间',exact:true}).fill('120');await settings.getByRole('button',{name:'更新安排',exact:true}).click();await settings.waitFor({state:'detached'});
 assert.deepEqual(summary.plan.tracks,['window','prefix'],'Changing time preserves the current mainline');assert(writes.some(item=>item.path==='/api/learning-summary/update'&&item.body.action==='configure'&&item.body.config.weekdayMinutes===150&&item.body.config.weekendMinutes===120));
 await board.getByRole('button',{name:'自建待办',exact:true}).click();const todoDialog=page.getByRole('dialog',{name:'自建待办',exact:true});await todoDialog.getByRole('textbox',{name:'待办名称',exact:true}).fill('整理今天的错题');await todoDialog.getByRole('button',{name:'添加',exact:true}).click();await todoDialog.getByRole('checkbox',{name:'完成 整理今天的错题',exact:true}).check();
 await page.waitForFunction(()=>Array.from(document.querySelectorAll('.task-todo-row')).some(node=>node.dataset.done==='true'));
 await page.waitForTimeout(600);assert(preferences.learningPaths.taskBoard.items.some(item=>item.title==='整理今天的错题'&&item.done));
 await page.keyboard.press('Escape');await todoDialog.waitFor({state:'detached'});await main.getByRole('button',{name:'调整推荐',exact:true}).click();await main.getByRole('button',{name:'太难',exact:true}).waitFor();assert.equal(await board.locator('.task-inline-feedback').count(),0);
 await main.getByRole('button',{name:'更换主线',exact:true}).click();const change=page.getByRole('dialog',{name:'更换主线',exact:true});await change.getByRole('checkbox',{name:'前缀和与差分',exact:true}).uncheck();await change.getByRole('button',{name:'更换并更新安排',exact:true}).click();await change.waitFor({state:'detached'});assert.deepEqual(summary.plan.tracks,['window']);await main.getByRole('heading',{name:'双指针与滑动窗口',exact:true}).waitFor();
 await page.getByRole('tab',{name:'专题进度',exact:true}).click();const topic=board.locator('.task-topic-card').first();assert.equal(await topic.getByRole('progressbar').getAttribute('aria-valuenow'),'6');assert.equal(await topic.locator('.topic-mastery-bar>i').count(),7);assert.equal(await topic.locator('.topic-mastery-bar>i[data-complete=true]').count(),6);assert.equal(await topic.getByText(/独立应用|延迟检验|尚未验证|能独立/).count(),0);
 for(const stage of [0,1,3,6,7]){summary={...summary,topics:[{...summary.topics[0],level:Math.min(stage,6),mixed:stage===7}]};await page.evaluate(()=>window.dispatchEvent(new Event('tb:learning-progress')));await page.waitForFunction(value=>document.querySelector('.task-topic-card [role=progressbar]')?.getAttribute('aria-valuenow')===String(value),stage);assert.equal(await topic.locator('.topic-mastery-bar>i[data-complete=true]').count(),stage);}
 await topic.click();const details=page.getByRole('dialog',{name:'双指针与滑动窗口',exact:true});await details.locator('.topic-stage-list li').last().waitFor();assert.equal(await details.locator('.topic-stage-list li[data-complete=true]').count(),7);await details.getByRole('button',{name:'检查判断',exact:true}).click();const quiz=page.getByRole('dialog',{name:'原理检查',exact:true});await quiz.locator('.summary-quiz-options button').first().waitFor();const boxes=await quiz.locator('.summary-quiz-options button').evaluateAll(nodes=>nodes.map(node=>{const box=node.getBoundingClientRect();return {x:box.x,y:box.y,width:box.width,height:box.height};}));assert(boxes.every(box=>Math.abs(box.y-boxes[0].y)<1&&Math.abs(box.height-boxes[0].height)<1));assert(boxes[2].x>boxes[1].x&&boxes[1].x>boxes[0].x);await page.screenshot({path:out+'/quiz-horizontal.png'});await page.keyboard.press('Escape');
 await page.locator('#tb-page-bookmarks').getByRole('tab',{name:'历史记录',exact:true}).click();await board.getByRole('button',{name:/首次规划/}).click();await board.getByText('这份记录没有周计划任务。',{exact:true}).waitFor();await board.getByText('历史内容保留',{exact:true}).waitFor();assert.equal(await page.getByRole('heading',{name:'界面暂时无法显示',exact:true}).count(),0);await board.getByRole('button',{name:/调整时间安排/}).click();await board.locator('.task-history-article tbody tr').first().waitFor();assert.equal(await board.locator('.task-history-article .summary-link').count(),0,'Archived tasks are read-only');
 await page.locator('#tb-page-bookmarks').getByRole('tab',{name:'学习概览',exact:true}).click();await page.screenshot({path:out+'/tasks-overview.png'});assert(await board.locator('.task-now').getByText('当前主线已完成',{exact:true}).isVisible());
 await page.locator('#tb-page-bookmarks').getByRole('tab',{name:'本周计划',exact:true}).dragTo(page.locator('#tb-page-bookmarks').getByRole('tab',{name:'学习概览',exact:true}));assert.equal(await board.locator('.section-pane').count(),1);await page.waitForTimeout(600);assert.equal(preferences.learningPaths.sectionWorkspaces.learning.groups.length,1);assert.equal(preferences.learningPaths.sectionWorkspaces.tasks.groups.length,1);await page.reload();await nav('任务').waitFor();await nav('任务').click();await page.getByRole('tab',{name:'学习概览',exact:true}).click();await board.getByRole('button',{name:'自建待办',exact:true}).click();await page.getByRole('checkbox',{name:'完成 整理今天的错题',exact:true}).waitFor();assert(await page.getByRole('checkbox',{name:'完成 整理今天的错题',exact:true}).isChecked());
 await page.getByRole('button',{name:'删除待办 整理今天的错题',exact:true}).click();assert.equal(await page.getByRole('checkbox',{name:'完成 整理今天的错题',exact:true}).count(),0);await page.waitForTimeout(600);assert(preferences.learningPaths.taskBoard.items[0].deletedAt);await page.keyboard.press('Escape');
 await nav('排行榜').click();const rankings=page.locator('[data-section=rankings]');await page.getByRole('tab',{name:'排位分排行榜',exact:true}).waitFor();for(const name of ['排位分排行榜','过题数排行榜','团队训练排行榜'])assert.equal(await page.getByRole('tab',{name,exact:true}).count(),1);
 assert.equal(await page.getByRole('tab',{name:'过题数排行榜',exact:true}).getAttribute('aria-selected'),'true');await rankings.locator('.ranking-table tbody tr').first().waitFor();
 const rankSearch=page.locator('#tb-page-search').getByRole('textbox',{name:'搜索排行榜用户昵称',exact:true});await rankSearch.waitFor();assert.equal(await rankings.locator('.section-document-tools input').count(),0);const rankBox=await rankSearch.boundingBox();assert(rankBox.y<100);await rankSearch.fill('训练者乙');assert.equal(await rankings.locator('.ranking-table tbody tr').count(),1);await rankSearch.fill('');
 await page.getByRole('tab',{name:'排位分排行榜',exact:true}).click();await rankings.getByRole('cell',{name:'1245',exact:true}).waitFor();assert.equal(await rankings.locator('.duel-public-records').count(),0);
 await page.getByRole('tab',{name:'过题数排行榜',exact:true}).click();await rankings.locator('.ranking-table tbody tr').first().waitFor();assert((await rankings.locator('.ranking-table tbody tr').first().boundingBox()).height<=110);await page.screenshot({path:out+'/three-rankings-compact.png'});
 await page.getByRole('tab',{name:'团队训练排行榜',exact:true}).click();await rankings.getByText('尚未接入团队训练成绩。',{exact:true}).waitFor();assert.equal(await rankings.locator('.team-standings tbody tr').count(),0,'Missing team records never become invented standings');
 await nav('成长').click();await rankings.waitFor({state:'detached'});await nav('排行榜').click();await page.getByRole('tab',{name:'过题数排行榜',exact:true}).waitFor();assert.equal(await page.getByRole('tab',{name:'过题数排行榜',exact:true}).getAttribute('aria-selected'),'true','Returning to the rankings starts with the accepted-problem board');
 await nav('任务').click();assert.equal(await page.locator('.summary-floating').count(),0);
 const headers=[];
 for(const width of [2048,1280,900,640,390]){
  await page.setViewportSize({width,height:1000});
  for(const name of ['我的训练','任务','学习','竞赛','成长','排行榜']){
   await nav(name).click();await page.waitForTimeout(40);
   assert.equal(await page.locator('.topbar-actions [aria-label="任务概览"]').count(),0,'The redundant task overview button is removed');
   const slot=await page.locator('#tb-page-bookmarks').evaluate(node=>{const css=getComputedStyle(node);return {overflowY:css.overflowY,scrollbarWidth:css.scrollbarWidth,webkitDisplay:getComputedStyle(node,'::-webkit-scrollbar').display};});
   assert.equal(slot.overflowY,'hidden');assert.equal(slot.scrollbarWidth,'none');assert.equal(slot.webkitDisplay,'none');
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),`Document overflow at ${width}/${name}`);
   if(width===2048){const recommendation=await page.locator('.next-actions').boundingBox(),actions=await page.locator('.topbar-actions').boundingBox();assert(recommendation&&actions);assert(Math.abs(recommendation.y-actions.y)<30);assert(actions.x-recommendation.x-recommendation.width<=18,'Recommendation sits beside the right status area');}
   headers.push({width,page:name,bookmarkScrollbarsHidden:true});
  }
 }
 await page.setViewportSize({width:2048,height:1000});await nav('任务').click();await page.locator('.next-actions-primary').hover();await page.locator('.next-actions-flyout').waitFor();assert((await page.locator('.next-actions-item').count())<=4);await page.mouse.move(80,500);
 await page.screenshot({path:out+'/updated-header.png'});await writeFile(out+'/header-catalogue.json',JSON.stringify({ok:true,headers,taskOverviewRemoved:true,recommendationBesideStatus:true,dropdownMaximum:4,introductionRemoved:true},null,2));
 assert.deepEqual(errors,[]);const result={ok:true,groupedNavigation:true,defaultGroups:6,independentCompetition:true,trainingTabs:3,competitionTabs:3,learningBookmarks:4,learningSearchInTopbar:true,focusedSearchAndQueryPreserved:true,rankingBookmarks:3,defaultRanking:'accepted',taskBookmarks:4,todayPageRemoved:true,dailySummaryRemoved:true,existingDailyDialog:true,timeSettingsDialog:true,mainlineVisibleAndSwitchable:true,phaseMastery:true,topicDetailsOnDemand:true,horizontalQuiz:true,emptyHistoryFixed:true,archivedTasksReadOnly:true,topLevelSplitRemoved:true,trainingPageStateIndependent:true,legacySplitMerged:true,legacyTodayLayoutMigrated:true,dragReorder:true,topLevelSinglePane:true,taskSurfaceOpacity:true,compactOverview:true,minimumMinutes:60,customTodoPersisted:true,completionAndDelete:true,layoutRestored:true,responsive:true,errors};await writeFile(out+'/result.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));
}catch(error){await page.screenshot({path:out+'/failure.png',fullPage:true});throw error;}finally{await browser.close();await vite.close();}
