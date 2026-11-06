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
  else if(path==='/api/stickers')value={owner:self.userId,revision:1,catalogue:[{id:'background-night-common',kind:'background',theme:'night',title:'安静夜晚',shape:'background-night',rarity:'common'},{id:'background-galaxy-legendary',kind:'background',theme:'galaxy',title:'银河漫游',shape:'background-galaxy',rarity:'legendary'},{id:'fixture-star',title:'星星',shape:'star',rarity:'common'}],units:[{id:'owned-night',stickerId:'background-night-common',revision:0,placement:null},{id:'owned-star',stickerId:'fixture-star',revision:0,placement:null}],capabilities:{backgrounds:true,scenes:true},scenePresets:[]};
  else if(path==='/api/training-lists')value={lists:[]};
  else if(path.startsWith('/api/learning-summary')){
 if(path.endsWith('/update')){if(body.action==='configure'){summary={...summary,config:body.config,proposal:{...summary.plan,id:'proposed-'+summaryRevision,tracks:body.tracks||summary.plan.tracks,reason:'更新可用时间'}};}else if(body.action==='accept'){summary={...summary,plan:summary.proposal||summary.plan,proposal:null};}else if(body.action==='view'){summary={...summary,view:body.view};}summary={...summary,revision:String(++summaryRevision)};}value=summary;
 }
 else if(path==='/api/wiki')value={articles:[{id:'basic/binary',title:'二分',category:'基础算法'}]};
 else if(path==='/api/templates')value={templates:[{id:'fixture-template',title:'二分',tags:['二分']}]};
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
  else if(path==='/api/lectures')value={lectures:[{id:'fixture-lecture',title:'二分',concept:'二分',tags:['二分']}]};
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

const out='../.backups/library-backgrounds/app-checks';await mkdir(out,{recursive:true});
try{
 rows[0].title='二分';rows[1].title='二分';
 await page.goto(vite.resolvedUrls.local[0]);await page.locator('.problem-table tr[data-id]').first().waitFor();const search=page.getByRole('searchbox',{name:'统一搜索',exact:true}),bookmarks=page.locator('#tb-page-bookmarks');await search.waitFor();
 // These two same-name problem results are independent records too.
 rows[0].title='二分';rows[1].title='二分';
 if(process.argv.includes('--appearance')){await (await import('./surface-appearance.mjs')).checkSurfaceAppearance({page,nav});await nav('任务').click();await bookmarks.getByRole('tab',{name:'概况',exact:true}).click();}
 const coordinates=[];
 for(const name of ['我的训练','任务','学习','竞赛','成长','排行榜','设置']){await nav(name).click();await search.waitFor();const box=await search.boundingBox();coordinates.push({name,x:box.x,width:box.width,y:box.y});assert.equal(await page.locator('.app-statusbar').getByRole('button',{name:'卡包',exact:true}).count(),1);assert.equal(await page.locator('.app-statusbar').getByRole('button',{name:'目标',exact:true}).count(),0);}
 assert(coordinates.every(box=>Math.abs(box.x-coordinates[0].x)<1&&Math.abs(box.width-coordinates[0].width)<1),'Search coordinates do not depend on bookmark labels');
 await search.fill('二分');const results=page.getByRole('region',{name:'全局搜索结果'});await results.getByRole('listitem',{name:'从零讲 二分',exact:true}).waitFor();for(const source of ['从零讲','模板','维基百科'])assert.equal(await results.getByRole('listitem',{name:source+' 二分',exact:true}).count(),1);assert.equal(await results.getByRole('listitem',{name:'单题 二分',exact:true}).count(),2);await page.screenshot({path:out+'/unified-search.png'});
 await page.getByRole('button',{name:'清空搜索',exact:true}).click();await nav('任务').click();assert.deepEqual(await bookmarks.getByRole('tab').allTextContents(),['概况','计划','进度','历史记录']);await page.getByRole('button',{name:'目标',exact:true}).click();await page.getByRole('dialog',{name:'更换主线',exact:true}).waitFor();await page.getByRole('button',{name:'关闭更换主线',exact:true}).click();await bookmarks.getByRole('tab',{name:'进度',exact:true}).click();await nav('我的训练').click();await nav('任务').click();assert.equal(await bookmarks.getByRole('tab',{name:'进度',exact:true}).getAttribute('aria-selected'),'true');
 await nav('学习').click();await bookmarks.getByRole('tab',{name:'实验室',exact:true}).click();await page.waitForFunction(()=>document.querySelector('#tb-page-bookmarks [aria-controls=section-panel-paths]')?.getAttribute('aria-selected')==='true');await nav('我的训练').click();await nav('学习').click();assert.equal(await bookmarks.getByRole('tab',{name:'实验室',exact:true}).getAttribute('aria-selected'),'true');
 await nav('排行榜').click();assert.deepEqual((await bookmarks.getByRole('tab').allTextContents()).sort(),['过题数','排位分','团队训练'].sort());await bookmarks.getByRole('tab',{name:'团队训练',exact:true}).click();await nav('任务').click();await nav('排行榜').click();assert.equal(await bookmarks.getByRole('tab',{name:'团队训练',exact:true}).getAttribute('aria-selected'),'true');
 // Source tabs and per-account persisted state both survive refresh.
 await page.reload();await search.waitFor();await nav('排行榜').click();assert.equal(await bookmarks.getByRole('tab',{name:'团队训练',exact:true}).getAttribute('aria-selected'),'true');await nav('任务').click();assert.equal(await bookmarks.getByRole('tab',{name:'进度',exact:true}).getAttribute('aria-selected'),'true');
 await page.setViewportSize({width:2048,height:1152});await nav('设置').click();await search.fill('二分');await results.getByRole('listitem',{name:'实验室 整数二分',exact:true}).click();await page.locator('.study-lab .algorithm-lab').waitFor();assert((await page.locator('.study-lab .lab-position').innerText()).includes('1 /'));assert.equal(await page.locator('.study-browser').getByRole('searchbox',{name:'统一搜索',exact:true}).count(),1);await page.locator('.study-browser').getByRole('button',{name:'卡包',exact:true}).click();await page.getByRole('dialog',{name:'卡包',exact:true}).waitFor();await page.getByRole('button',{name:'关闭卡包',exact:true}).click();await page.locator('.study-browser').getByRole('searchbox',{name:'统一搜索',exact:true}).fill('二分');await page.locator('.study-browser .workspace-search-results').getByRole('listitem',{name:'从零讲 二分',exact:true}).waitFor();await page.locator('.study-browser').getByRole('button',{name:'清空搜索',exact:true}).click();await page.getByRole('button',{name:'返回主界面',exact:true}).click();
 for(const width of [2048,1280,900,640,390]){await page.setViewportSize({width,height:1000});await nav('设置').click();await search.waitFor();assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);}
 assert.deepEqual(errors,[]);const result={ok:true,globalSearch:true,sameNameRowsPreserved:true,searchCoordinates:coordinates,settingsSearch:true,packEverywhere:true,goalInTasks:true,shortLabels:true,bookmarkResume:true,refreshResume:true,labOpenFromSearch:true,responsive:true,errors};await writeFile(out+'/result.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));
}catch(error){await page.screenshot({path:out+'/failure.png'});throw error;}finally{await browser.close();await vite.close();}
