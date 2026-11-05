import assert from 'node:assert/strict';
import { mkdir,writeFile } from 'node:fs/promises';
import { createServer } from 'vite';
import { chromium } from 'playwright';
import {emptyStudyBrowser,openStudyTab,studySnapshot} from '../src/lib/learningBrowser.js';

const vite=await createServer({cacheDir:'../.backups/navigation-correction-20261105/vite-workspace',optimizeDeps:{entries:['index.html']},server:{host:'127.0.0.1',port:0,watch:null}});
await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[],writes=[];
page.on('pageerror',error=>errors.push(error.message));
page.setDefaultTimeout(12000);
const timestamp=new Date().toISOString(),date=new Date().toLocaleDateString('sv-SE',{timeZone:'Asia/Shanghai'});
const self={userId:'11111111-1111-4111-8111-111111111111',nickname:'训练者甲'},other={userId:'22222222-2222-4222-8222-222222222222',nickname:'训练者乙'};
const rows=Array.from({length:120},(_,index)=>({id:`fixture::${index}`,contest:'周赛 166',problem:String(index+1),title:`列表定位测试 ${String(index+1).padStart(3,'0')}`,tags:['模拟'],knowledge:'模拟',platform:'牛客',series:'周赛',difficulty:800+index*10,url:`https://example.com/${index}`,contestDate:'2026-10-20T00:00:00Z',solutionAvailable:true}));
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
let summary={version:1,revision:'1',config:{goal:{kind:'xcpc',title:'区域赛铜牌',deadline:''},weekdayMinutes:60,weekendMinutes:60,restDays:[],team:false,role:''},plan:{id:'plan-fixture',week:date,tasks:[{key:'lecture-one',kind:'lecture',id:'fixture-lecture',title:'滑动窗口：边界处理',date,status:'pending',minutes:20,order:1,topicId:'window'},{key:'problem-one',kind:'problem',id:rows[0].id,title:'最长不重复子串',date,status:'pending',minutes:25,order:2,topicId:'window'},{key:'review-one',kind:'review',id:rows[1].id,title:'前缀和间隔复习',date,status:'pending',minutes:15,order:3,topicId:'prefix'}],days:Array.from({length:7},(_,i)=>({date:new Date(Date.now()+i*86400000).toLocaleDateString('sv-SE',{timeZone:'Asia/Shanghai'}),minutes:60})),tracks:['window','prefix'],waiting:[],gaps:[]},proposal:null,article:[],topics:[{id:'window',title:'双指针与滑动窗口',independent:2,retained:1,label:'正在学'}],availableTopics:[{id:'window',title:'双指针与滑动窗口'},{id:'prefix',title:'前缀和与差分'}],history:[],view:{mode:'float',pinned:true},seen:{},recommendation:{title:'双指针与滑动窗口',reason:'先检查窗口边界。'},effectiveSeconds:5400};

await page.route('**/api/**',async route=>{
  const request=route.request(),url=new URL(request.url()),path=url.pathname;
  if(!path.startsWith('/api/'))return route.continue();
  const body=request.method()==='POST'?request.postDataJSON():null;
  if(body)writes.push({path,body});
  let value;
  if(path==='/api/account')value={required:false,authenticated:true,usesOriginalWorkspace:true,token:'fixture',account:self};
  else if(path.startsWith('/api/learning-summary')){
 if(path.endsWith('/update')){if(body.action==='configure'){summary={...summary,config:body.config,proposal:{id:'proposed',tasks:summary.plan.tasks,reason:'更新可用时间'}};}else if(body.action==='accept'){summary={...summary,proposal:null};}else if(body.action==='view'){summary={...summary,view:body.view};}summary={...summary,revision:String(++summaryRevision)};}value=summary;
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
const out='../.backups/navigation-correction-20261105/app-checks';await mkdir(out,{recursive:true});
try{
 await page.goto(vite.resolvedUrls.local[0]);await page.locator('.problem-table tr[data-id]').first().waitFor();await nav('任务').waitFor();
 for(const name of ['我的训练','任务','学习','竞赛','成长','排行榜'])assert.equal(await nav(name).count(),1,name);
 assert.deepEqual(await page.locator('.sidebar [data-navigation-id]').allTextContents(),['我的训练','任务','学习','竞赛','成长','排行榜']);
 assert.deepEqual(await page.getByRole('tablist',{name:'组合页面 我的训练'}).getByRole('tab').allTextContents(),['我的训练','题库','题单']);
 await nav('竞赛').click();assert.deepEqual(await page.getByRole('tablist',{name:'组合页面 竞赛'}).getByRole('tab').allTextContents(),['比赛','模拟赛','对战']);
 assert.equal(await page.locator('.sidebar').getByRole('button',{name:'题库',exact:true}).count(),0);
 await nav('学习').click();const workspace=page.locator('.section-workspace[data-section=learning]');await workspace.waitFor();
 for(const name of ['从零讲','维基百科','模板','实验室'])assert.equal(await workspace.getByRole('tab',{name,exact:true}).count(),1);
 for(const [name,label,text] of [['从零讲','搜索从零讲知识','lecture-query'],['维基百科','搜索维基百科','wiki-query'],['模板','搜索模板','template-query'],['实验室','搜索算法','lab-query']]){
  await workspace.getByRole('tab',{name,exact:true}).click();const search=page.locator('#tb-page-search').getByRole('textbox',{name:label,exact:true});await search.waitFor();assert.equal(await page.locator('#tb-page-search input').count(),1);assert.equal(await workspace.locator('.section-document-tools input').count(),0);const box=await search.boundingBox();assert(box.x<500&&box.y<80,'Learning search stays in the original upper-left header');await search.fill(text);
 }
 await workspace.getByRole('tab',{name:'维基百科',exact:true}).click();assert.equal(await page.locator('#tb-page-search').getByRole('textbox',{name:'搜索维基百科',exact:true}).inputValue(),'wiki-query');
 await workspace.getByRole('tab',{name:'模板',exact:true}).click();await workspace.getByRole('button',{name:'将当前书签向右分屏'}).click();
 await page.waitForFunction(()=>document.querySelectorAll('[data-section=learning]>.section-pane').length===2);
 const before=await workspace.locator('.section-pane').first().boundingBox(),divider=workspace.getByRole('separator').first();
 await divider.focus();await page.keyboard.press('ArrowRight');const after=await workspace.locator('.section-pane').first().boundingBox();assert(after.width>before.width);
 const first=workspace.locator('.section-pane').first(),target=await first.boundingBox();
 await workspace.getByRole('tab',{name:'维基百科',exact:true}).dragTo(first,{targetPosition:{x:target.width-4,y:120}});
 await page.waitForFunction(()=>document.querySelectorAll('[data-section=learning]>.section-pane').length===3);
 await workspace.getByRole('tab',{name:'模板',exact:true}).click();assert.equal(await page.locator('#tb-page-search').getByRole('textbox',{name:'搜索模板',exact:true}).inputValue(),'template-query');await workspace.getByRole('tab',{name:'维基百科',exact:true}).click();assert.equal(await page.locator('#tb-page-search').getByRole('textbox',{name:'搜索维基百科',exact:true}).inputValue(),'wiki-query');assert.equal(await page.locator('#tb-page-search input').count(),1,'Split panes share the header for the focused pane only');
 await page.screenshot({path:out+'/learning-three-panes.png'});
 await nav('任务').click();const board=page.locator('[data-section=tasks]');await board.getByRole('heading',{name:'学习概览',exact:true}).waitFor();
 const boardBox=await board.boundingBox(),areaBox=await page.locator('.workspace-area').boundingBox();assert(boardBox.width>=areaBox.width-1,'Workspace fills the available width');
 const nowBox=await board.locator('.task-now').first().boundingBox(),routeBox=await board.locator('.task-route').boundingBox();assert(Math.abs(nowBox.y-routeBox.y)<2,'Current route sits beside the recommendation');
 const top=await board.locator('.task-overview-head').boundingBox();assert(top.height<450,'Overview uses the upper screen efficiently');await page.screenshot({path:out+'/tasks-overview.png'});
 assert.equal(await board.getByRole('tab').count(),4);for(const name of ['今日任务','可用时间','自建待办','调整推荐','学习浮窗','顶部推荐'])assert.equal(await board.getByRole('tab',{name,exact:true}).count(),0);
 const daily=board.getByRole('region',{name:'每日任务进度',exact:true});await daily.getByText('已完成 2 / 3',{exact:true}).waitFor();assert.equal(await board.locator('.daily-task-grid').count(),0,'The overview contains a summary instead of another daily-task screen');await daily.getByRole('button',{name:'查看每日任务',exact:true}).click();const dailyDialog=page.getByRole('dialog',{name:'每日任务',exact:true});await dailyDialog.locator('.daily-task').first().waitFor();assert.equal(await dailyDialog.locator('.daily-task').count(),3);await page.keyboard.press('Escape');await dailyDialog.waitFor({state:'detached'});
 const time=board.getByRole('spinbutton',{name:'平日可用时间',exact:true});assert.equal(await time.inputValue(),'60');assert.equal(await time.getAttribute('min'),'60');
 await time.fill('15');await time.press('Tab');assert.equal(await time.inputValue(),'60');
 const group=board.getByRole('group',{name:'平日可用时间',exact:true});await group.getByRole('button',{name:'平日可用时间增加30分钟',exact:true}).click();assert.equal(await time.inputValue(),'90');await group.getByRole('button',{name:'平日可用时间增加60分钟',exact:true}).click();assert.equal(await time.inputValue(),'150');
 await board.getByRole('button',{name:'更新安排',exact:true}).click();await page.waitForFunction(()=>!document.querySelector('.task-inline-time>.task-primary')?.disabled);
 assert(writes.some(item=>item.path==='/api/learning-summary/update'&&item.body.action==='configure'&&item.body.config.weekdayMinutes===150&&item.body.config.weekendMinutes>=60));
 await board.getByRole('textbox',{name:'待办名称',exact:true}).fill('整理今天的错题');await board.getByRole('button',{name:'添加',exact:true}).click();await board.getByRole('checkbox',{name:'完成 整理今天的错题',exact:true}).check();
 await page.waitForFunction(()=>Array.from(document.querySelectorAll('.task-todo-row')).some(node=>node.dataset.done==='true'));
 await page.waitForTimeout(600);assert(preferences.learningPaths.taskBoard.items.some(item=>item.title==='整理今天的错题'&&item.done));
 await board.getByRole('tab',{name:'本周计划',exact:true}).click();await board.getByRole('button',{name:'将当前书签向右分屏'}).click();await page.waitForFunction(()=>document.querySelectorAll('[data-section=tasks]>.section-pane').length===2);
 await page.screenshot({path:out+'/tasks-plan-and-todos.png'});
 await page.waitForTimeout(600);assert.equal(preferences.learningPaths.sectionWorkspaces.learning.groups.length,3);assert.equal(preferences.learningPaths.sectionWorkspaces.tasks.groups.length,2);
 await page.reload();await nav('任务').waitFor();await nav('任务').click();await page.waitForFunction(()=>document.querySelectorAll('[data-section=tasks]>.section-pane').length===2);await page.getByRole('tab',{name:'学习概览',exact:true}).click();await page.getByRole('checkbox',{name:'完成 整理今天的错题',exact:true}).waitFor();assert(await page.getByRole('checkbox',{name:'完成 整理今天的错题',exact:true}).isChecked());
 await page.getByRole('button',{name:'删除待办 整理今天的错题',exact:true}).click();assert.equal(await page.getByRole('checkbox',{name:'完成 整理今天的错题',exact:true}).count(),0);await page.waitForTimeout(600);assert(preferences.learningPaths.taskBoard.items[0].deletedAt);
 await nav('排行榜').click();const rankings=page.locator('[data-section=rankings]');await rankings.getByRole('tab',{name:'排位分排行榜',exact:true}).waitFor();for(const name of ['排位分排行榜','过题数排行榜','团队训练排行榜'])assert.equal(await rankings.getByRole('tab',{name,exact:true}).count(),1);
 assert.equal(await rankings.getByRole('tab',{name:'过题数排行榜',exact:true}).getAttribute('aria-selected'),'true');await rankings.locator('.ranking-table tbody tr').first().waitFor();
 await rankings.getByRole('tab',{name:'排位分排行榜',exact:true}).click();await rankings.getByRole('cell',{name:'1245',exact:true}).waitFor();assert.equal(await rankings.locator('.duel-public-records').count(),0);
 await rankings.getByRole('tab',{name:'过题数排行榜',exact:true}).click();await rankings.locator('.ranking-table tbody tr').first().waitFor();assert((await rankings.locator('.ranking-table tbody tr').first().boundingBox()).height<=110);await page.screenshot({path:out+'/three-rankings-compact.png'});
 await rankings.getByRole('tab',{name:'团队训练排行榜',exact:true}).click();await rankings.getByText('尚未接入团队训练成绩。',{exact:true}).waitFor();assert.equal(await rankings.locator('.team-standings tbody tr').count(),0,'Missing team records never become invented standings');
 await nav('成长').click();await nav('排行榜').click();await rankings.getByRole('tab',{name:'过题数排行榜',exact:true}).waitFor();assert.equal(await rankings.getByRole('tab',{name:'过题数排行榜',exact:true}).getAttribute('aria-selected'),'true','Returning to the rankings starts with the accepted-problem board');
 await nav('任务').click();assert.equal(await page.locator('.summary-floating').count(),0);
 for(const width of [1280,900,640,390]){await page.setViewportSize({width,height:1000});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Document overflow at '+width);}
 assert.deepEqual(errors,[]);const result={ok:true,groupedNavigation:true,defaultGroups:6,independentCompetition:true,trainingTabs:3,competitionTabs:3,learningBookmarks:4,learningSearchInTopbar:true,focusedSearchAndQueryPreserved:true,rankingBookmarks:3,defaultRanking:'accepted',taskBookmarks:4,todayPageRemoved:true,dailySummaryAndExistingDialog:true,legacyTodayLayoutMigrated:true,dragSplit:true,keyboardResize:true,threeLearningPanes:true,compactOverview:true,minimumMinutes:60,customTodoPersisted:true,completionAndDelete:true,layoutRestored:true,responsive:true,errors};await writeFile(out+'/result.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));
}catch(error){await page.screenshot({path:out+'/failure.png',fullPage:true});throw error;}finally{await browser.close();await vite.close();}
