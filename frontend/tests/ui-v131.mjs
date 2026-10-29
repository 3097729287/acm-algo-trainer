import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { createServer } from 'vite';
import { chromium } from 'playwright';

const vite=await createServer({server:{host:'127.0.0.1',port:18831,strictPort:true}});
await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[],writes=[];
page.on('pageerror',error=>errors.push(error.message));
page.on('console',message=>{if(message.type()==='error'&&/ReferenceError|TypeError|TB render failure/.test(message.text()))errors.push(message.text());});
page.setDefaultTimeout(12000);
const timestamp=new Date().toISOString(),date=new Date().toLocaleDateString('sv-SE',{timeZone:'Asia/Shanghai'});
const calendarDate=new Date(Date.now()+86400000).toISOString().slice(0,10);
const self={userId:'11111111-1111-4111-8111-111111111111',nickname:'训练者甲'},other={userId:'22222222-2222-4222-8222-222222222222',nickname:'训练者乙'};
const rows=Array.from({length:120},(_,index)=>({id:`fixture::${index}`,contest:'周赛 166',problem:String(index+1),title:`列表定位测试 ${String(index+1).padStart(3,'0')}`,tags:['模拟'],knowledge:'模拟',platform:'牛客',series:'周赛',difficulty:800+index*10,url:`https://example.com/${index}`,contestDate:'2026-10-20T00:00:00Z',solutionAvailable:true}));
for(const index of [20,21,22])rows[index]={...rows[index],tags:['KMP'],knowledge:'KMP'};
for(let i=0;i<6;i++)rows[i]={...rows[i],tags:[i<3?'素数':'取模与同余'],knowledge:i<3?'素数':'取模与同余'};
rows[117]={...rows[117],id:'lab:luogu:P1048',title:'采药',tags:['背包 DP'],knowledge:'背包 DP',url:'https://www.luogu.com.cn/problem/P1048'};
rows[118]={...rows[118],contest:'CCPC 2025 郑州区域赛（热身赛）',series:'XCPC'};
rows[119]={...rows[119],contest:'CCPC 2025 郑州区域赛',series:'XCPC'};
let mockRecords=[1,3,2].map(day=>({id:`mock-${day}`,name:`训练记录 ${day}`,status:'finished',startedAt:`2026-10-${String(day).padStart(2,'0')}T10:00:00Z`,duration:120,total:4,accepted:day,slots:rows.slice(0,4).map((row,index)=>({...row,letter:String.fromCharCode(65+index),accepted:index<day,attempts:1}))}));
for(const row of rows){row.contestProblemCount=rows.filter(item=>item.contest===row.contest&&item.platform===row.platform).length;row.catalogContentReady=true;}
const training=rows.filter(row=>row.id!==rows[119].id).map(row=>({id:row.id,activeAt:timestamp,lastActivityAt:timestamp,today:true,accepted:false,verdict:null,attempts:0}));
let adminMode=false,calendarReads=0,trainingDelay=0,failDraft=false,reviewId=null,mockActive=null,todayCount=2,rankingOnlySelf=false,richFixture=false;
let preferences=null,likes={total:4,likedToday:false},failLike=true,boardDay=date,notifications=[{id:'33333333-3333-4333-8333-333333333333',kind:'comment',actor:other,recipient:self,text:'一起加油 <script>window.untrusted=true</script>',createdAt:timestamp,read:false}];
notifications.push(...Array.from({length:100},(_,index)=>({id:`55555555-5555-4555-8555-${String(index).padStart(12,'0')}`,kind:'like',actor:other,recipient:self,createdAt:timestamp,read:false})));
const workspace=()=>({training,sets:[],contests:mockRecords,activeContest:mockActive,goals:{goals:[]},goalTasks:[...rows.slice(0,2),{...rows[119],accepted:true}],summary:{total:120,accepted:training.filter(row=>row.accepted).length,todayAccepted:todayCount,beforeTodayAccepted:82,historicalAccepted:82+todayCount,attempts:0,due:0,pending:0,streak:12},now:timestamp});
const progress={badge:'tier-7',level:8,tier:'大师',rankTier:'大师',rankScore:2000,titles:[]};
const ranked={badge:'tier-7',tier:'大师',qualified:true,abilityScore:2000,nextAbilityScore:2100,evidenceCount:8,minimumEvidence:5,levelGate:5};
ranked.tierRequirements=['黑铁','青铜','白银','黄金','铂金','翡翠','钻石','大师','宗师','王者'].map((tier,index)=>({tier,badge:`tier-${index}`,minAbilityScore:[0,800,1000,1200,1400,1600,1800,2000,2100,2200][index]}));
const hub={settings:{githubRepo:'3097729287/acm-algo-trainer',accounts:{},autoSync:false,intervalHours:6,minDifficulty:0,maxDifficulty:2199},sync:{busy:false},updates:{currentVersion:'1.1.5'},accounts:[],notifications:[]};
await page.addInitScript(()=>localStorage.setItem('tb.preferences',JSON.stringify({onboardingGuideVersion:2,theme:'dark',accent:'teal',backdrop:'aurora',panelOpacity:35,widgets:true,fontSize:16,navOrder:['mine','library','competitions','mock','rankings','growth','records','activity','lectures'],views:[]})));
await page.route('**/api/**',async route=>{
  const request=route.request(),url=new URL(request.url()),path=url.pathname;
  if(!path.startsWith('/api/'))return route.continue();
  const body=request.method()==='POST'?request.postDataJSON():null;
  if(body)writes.push({path,body});
  let value;
  if(path==='/api/account')value={required:false,authenticated:true,usesOriginalWorkspace:true,token:'fixture',account:{...self,createdAt:'2026-10-01T00:00:00Z'},admin:adminMode};
  else if(path==='/api/training-list-likes')value={likes:[]};
  else if(path==='/api/preferences'){if(body)preferences=body.preferences;value={preferences,updatedAt:timestamp};}
  else if(path==='/api/usage')value={days:[],totalSeconds:0,maxDailySeconds:0,maxDailyDate:null};
  else if(path==='/api/content-update')value={revision:0,status:'current',error:''};
  else if(path==='/api/software-update')value={currentVersion:'1.1.5',status:'current',autoCheck:false,canInstall:false};
  else if(path==='/api/browser-preparation')value={available:false};
  else if(path==='/api/data')value={rows,categories:richFixture?[{name:'基础技巧',tags:['二分查找','线性 DP'],children:[{name:'二分查找',tags:['二分查找']}]},{name:'动态规划',tags:['线性 DP','背包 DP'],children:[{name:'线性 DP',tags:['线性 DP']},{name:'背包 DP',tags:['背包 DP']}]},{name:'数学',tags:Array.from({length:40},(_,i)=>'专题'+i),children:Array.from({length:40},(_,i)=>({name:'专题'+i,tags:['专题'+i]}))}]:[{name:'数据结构',tags:['栈','单调栈'],children:[{name:'单调栈',tags:['单调栈']}]},{name:'数学',tags:['素数','取模与同余'],children:[{name:'素数',tags:['素数']},{name:'取模与同余',tags:['取模与同余']}]},{name:'字符串',tags:['KMP','字典树'],children:[{name:'KMP',tags:['KMP']},{name:'字典树',tags:['字典树']}]}],token:'fixture',today:date,revision:'ui-social'};
  else if(path==='/api/workspace')value=workspace();
  else if(path==='/api/hub')value=hub;
  else if(path==='/api/insights')value={summary:{officialSolved:0,submissions:0,activeDays:1,streak:1},growth:{confirmed:true,authority:{owner:self.userId,epoch:'legacy-fixture',revision:1},...progress,totalXp:6265,currentLevelXp:665,nextLevelXp:1600,ranked},knowledge:[],achievements:[],personalStatistics:{longestAcStreak:7,maxDailyAc:8,maxDailyAcDate:date,hardestSolved:{...rows[20]}},activity:richFixture?Array.from({length:Number(date.slice(-2))},(_,i)=>({date:date.slice(0,8)+String(i+1).padStart(2,'0'),officialAccepted:i%8,submissions:1})):[],recommendations:[],assessment:{platforms:[]},dailyTasks:{tasks:[]}};
  else if(path==='/api/profile')value={profile:self,leaderboard:{configured:true,status:'ready'}};
  else if(path==='/api/goals')value={goals:[]};
  else if(path==='/api/usage')value=body?{saved:true}:{days:[],totalSeconds:7200,maxDailySeconds:3600,maxDailyDate:date};
  else if(path==='/api/contest-calendar'){calendarReads++;value={refreshing:false,providers:['Codeforces','AtCoder','牛客','洛谷'].map(label=>({platform:label,label,status:'ready'})),contests:[{id:'abc-fixture',title:'ABC 481',platform:'atcoder',startAt:`${calendarDate}T12:00:00Z`,endAt:`${calendarDate}T13:40:00Z`,url:'https://atcoder.jp/contests/abc481'},{id:'cf-fixture',title:'Codeforces Round (Div. 2)',platform:'codeforces',startAt:`${calendarDate}T14:35:00Z`,endAt:`${calendarDate}T16:35:00Z`,url:'https://codeforces.com/contest/2100'}]};}
  else if(path==='/api/solution')value={id:url.searchParams.get('id'),title:'Fixture editorial',markdown:'## 思路\n\n先分析边界，再计算答案。\n\n$$a^2+b^2=c^2$$',images:{},lectures:[]};
  else if(path==='/api/contests/events')value={events:[]};
  else if(path==='/api/contest')value={contest:mockRecords.find(item=>item.id===url.searchParams.get('id'))};
  else if(path==='/api/contests/delete'){mockRecords=body.all?[]:mockRecords.filter(item=>item.id!==body.id);value={workspace:workspace(),deleted:1};}
  else if(path==='/api/submissions')value={submissions:rows.slice(0,3).map((row,index)=>({id:`submission-${index}`,problemId:row.id,submittedAt:timestamp,mode:'submit',verdict:'AC',timeMs:index===2?15:null})),total:3,hasMore:false};
  else if(path==='/api/lectures')value={lectures:[{id:'lesson',title:'二分查找',category:'基础技巧',tags:richFixture?['二分','线性 DP']:['二分']},{id:'linear',title:'线性状态',category:'动态规划 / 线性 DP',tags:['线性 DP']},{id:'bag',title:'背包选择',category:'动态规划 / 背包 DP',tags:['背包 DP']} ]};
  else if(path==='/api/lecture')value={id:url.searchParams.get('id'),title:'知识正文',tags:['二分','线性 DP'],markdown:'## 先说明状态\n\n独立复用基础知识。'};
  else if(path==='/api/desktop/fullscreen')value={available:false,fullscreen:false};
  else if(path==='/api/training/start'){if(trainingDelay)await new Promise(resolve=>setTimeout(resolve,trainingDelay));value={workspace:workspace(),reviewTask:reviewId?{id:reviewId}:null};}
  else if(path==='/api/problem')value={id:url.searchParams.get('id'),title:rows.find(row=>row.id===url.searchParams.get('id')).title,markdown:'## 题目描述\n\n测试题面。\n\n## 样例\n\n```text\n1 2\n```',samples:[{input:'1\n',output:'2\n'}],limits:{timeMs:2000,memoryMb:256},judge:{scope:'samples',cases:1},statementAvailable:true,draft:'int main() { return 0; }',submissions:[]};
  else if(path==='/api/draft'){if(failDraft){await route.fulfill({status:503,json:{error:'fixture draft unavailable'}});return;}value={savedAt:timestamp};}
  else if(path==='/api/translation/settings')value={provider:'custom',providerName:'自定义',model:'fixture',configured:false,keyStored:false,providers:[]};
  else if(path==='/api/leaderboard')value={period:url.searchParams.get('period')||'daily',date:boardDay,configured:true,status:'ready',hasSnapshot:true,socialAvailable:true,socialProtocol:1,isAdmin:true,entries:[{...self,rank:1,count:2,likes:{total:9,likedToday:false},publicProgress:progress},...rankingOnlySelf?[]:[{...other,rank:2,count:1,likes,publicProgress:progress}]],self};
  else if(path==='/api/leaderboard/sync')value={queued:true};
  else if(path==='/api/social')value={available:true,protocol:1,totalLikes:9,todayLikes:3,unreadCount:notifications.filter(row=>!row.read).length,notifications:notifications.slice(0,100),activity:[{id:'today',kind:'like',actor:self,recipient:other,createdAt:timestamp},{id:'yesterday',kind:'like',actor:{nickname:'昨日用户'},recipient:other,createdAt:new Date(Date.now()-86400000).toISOString()}]};
  else if(path==='/api/social/likes'){
    await new Promise(resolve=>setTimeout(resolve,120));
    if(failLike){failLike=false;await route.fulfill({status:503,json:{error:'测试连接中断'}});return;}
    likes={total:likes.total+(likes.likedToday?0:1),likedToday:true};value={created:true,targetId:other.userId,likes};
  }
  else if(path==='/api/social/comments')value={created:true,id:body.requestId};
  else if(path==='/api/social/read'){notifications=notifications.map(row=>body.all===true||body.ids?.includes(row.id)?{...row,read:true}:row);value={ok:true};}
  else {await route.fulfill({status:404,json:{error:'fixture missing '+path}});return;}
  await route.fulfill({json:value});
});
const nav=name=>page.locator('.sidebar').getByRole('button',{name,exact:true});
async function openPage(name){if(await nav(name).isVisible())await nav(name).click();else if(name==='题库')await page.keyboard.press('Control+2');else{await page.keyboard.press('Control+k');await page.getByRole('button',{name:'打开'+name,exact:true}).click();}}
const checkOverflow=async()=>assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
async function shot(name){await page.screenshot({path:`tests/screenshots/v131-${name}.png`,animations:'disabled'});}
async function settings(name){await nav('设置').click();await page.locator('.settings-page').waitFor();if(!(await page.locator('.settings-home-grid').count()))await page.keyboard.press('Escape');if(name)await page.getByRole('tab',{name,exact:true}).click();}
async function header(){const value=await page.locator('.topbar').evaluate(node=>{const s=node.querySelector('#tb-page-search'),a=node.querySelector('.topbar-actions');return {search:s.getBoundingClientRect().right,actions:a.getBoundingClientRect().left,inputs:s.querySelectorAll('input').length,placeholder:s.querySelector('input')?.getAttribute('placeholder'),height:node.getBoundingClientRect().height};});assert(value.search<=value.actions);assert(value.inputs<=1);assert(!value.placeholder);await checkOverflow();}
async function chrome(){
 assert.equal(await page.locator('.page-identity,.breadcrumb,.settings-breadcrumb').count(),0);
 const result=await page.evaluate(()=>{const rect=selector=>document.querySelector(selector).getBoundingClientRect(),footer=rect('.app-statusbar'),settings=rect('.sidebar-bottom .nav-item'),workspace=rect('.workspace-area'),bar=rect('.topbar');return {center:Math.abs(settings.y+settings.height/2-footer.y-footer.height/2),bar:bar.height,bottom:workspace.bottom-footer.top};});
 assert(result.center<=1,JSON.stringify(result));assert(result.bar>=64&&result.bar<=70,JSON.stringify(result));assert.equal(result.bottom,0);await header();
}
async function radarNames(){
 const result=await page.locator('.knowledge-radar').evaluate(section=>{const labels=[...section.querySelectorAll('svg text')],nodes=[...section.querySelectorAll('.radar-node')],rows=[...section.querySelectorAll('.radar-detail-row>button')];return {names:labels.map(label=>label.textContent),rows:rows.map(row=>row.childNodes[0].textContent),overlaps:labels.map((label,index)=>{const a=label.getBoundingClientRect(),b=nodes[index].getBoundingClientRect();return a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top;})};});
 assert.deepEqual(result.names,result.rows);assert(result.overlaps.every(value=>!value),JSON.stringify(result));
}
try{
 await mkdir('tests/screenshots',{recursive:true});
 await page.goto('http://127.0.0.1:18831');await page.locator('.problem-table tr[data-id]').first().waitFor();
 assert.equal((await page.locator('.topbar-daily-ac').innerText()).replace(/\s/g,''),'AC:82+2');
 assert.equal(await page.locator('.practice-streak').getAttribute('data-lit'),'true');
 const flameBefore=await page.locator('.practice-streak').boundingBox();
 todayCount=0;await page.evaluate(()=>window.dispatchEvent(new Event('focus')));
 await page.waitForFunction(()=>document.querySelector('.practice-streak')?.dataset.lit==='false');
 assert.equal(await page.locator('.practice-streak .flame-shell').evaluate(node=>getComputedStyle(node).fill),'none');
 assert.equal(await page.locator('.practice-streak .flame-body').count(),0);
 todayCount=2;await page.evaluate(()=>window.dispatchEvent(new Event('focus')));
 await page.waitForFunction(()=>document.querySelector('.practice-streak')?.dataset.lit==='true');
 assert.equal(await page.locator('.practice-streak .flame-shell').evaluate(node=>getComputedStyle(node).fill),'rgb(236, 81, 44)');
 assert.deepEqual(await page.locator('.practice-streak').boundingBox(),flameBefore,'today completion fills the flame without shifting header status');
 assert.equal(await page.locator('.topbar-love-count svg').getAttribute('fill'),'currentColor');
 const settingsGeometry=()=>page.locator('.sidebar-bottom .nav-item').evaluate(node=>{const box=node.getBoundingClientRect(),label=node.querySelector('span').getBoundingClientRect();return {x:box.x,y:box.y,width:box.width,height:box.height,labelX:label.x,labelY:label.y};});
 const fixedSettings=await settingsGeometry();
 for(const sync of [{status:'syncing',pending:true},{status:'ready',pending:false},{status:'error',pending:true,error:'fixture'},{status:'ready',pending:false}]){await page.evaluate(value=>window.dispatchEvent(new CustomEvent('tb:sync-status',{detail:value})),sync);await page.waitForTimeout(20);assert.deepEqual(await settingsGeometry(),fixedSettings);}
 assert.equal((await page.locator('.brand-mark').innerText()).replace(/\s/g,''),'ToBe');
 await page.getByRole('button',{name:'收起侧边栏',exact:true}).click();await page.waitForFunction(()=>document.querySelector('.sidebar').getBoundingClientRect().width<70);
 await page.getByRole('button',{name:'展开侧边栏',exact:true}).click();await chrome();
 assert.equal(await page.locator('.queue-heading').first().evaluate(node=>getComputedStyle(node.querySelector('td')).textAlign),'left');
 await page.evaluate(()=>document.documentElement.dataset.panelStyle='outlined');
 const edges=await page.locator('.list-page').evaluate(node=>[getComputedStyle(node).borderTopWidth,getComputedStyle(node).borderLeftWidth,getComputedStyle(node).borderRightWidth]);assert.deepEqual(edges,['1px','1px','1px'],'outlined style bounds the shared list surface');
 const archivedGoal=page.locator(`.problem-table tr[data-id="${rows[119].id}"]`);assert.equal(await archivedGoal.locator('.verdict').innerText(),'AC');assert.equal(await archivedGoal.locator('.remove-training').count(),0);
 await page.getByRole('button',{name:'每日任务',exact:true}).click();await page.getByRole('dialog',{name:'每日任务',exact:true}).waitFor();assert.equal(await page.locator('.daily-goal-tasks').count(),0);await page.keyboard.press('Escape');
 assert(calendarReads>=1,'calendar refreshes in background while training remains usable');
 await page.getByRole('button',{name:'比赛日历',exact:true}).click();await page.getByRole('dialog',{name:'比赛日历',exact:true}).waitFor();await page.getByRole('link',{name:/ABC 481/}).waitFor();assert.equal((await page.locator('.contest-calendar-row time').allTextContents()).join(','),'20:00,22:35');assert.equal(await page.locator('.contest-calendar-provider-error').count(),0);await checkOverflow();await shot('calendar');await page.keyboard.press('Escape');
 const status=await page.locator('.topbar').evaluate(node=>{const ac=node.querySelector('.topbar-daily-ac'),heart=node.querySelector('.topbar-love-count b'),flame=node.querySelector('.streak-flame');return {ac:getComputedStyle(ac).color,muted:getComputedStyle(node).getPropertyValue('--muted').trim(),size:parseFloat(getComputedStyle(heart).fontSize),flame:flame.getBoundingClientRect().height,animation:getComputedStyle(flame).animationName};});
 assert(status.size>=16);assert(status.flame>=18&&status.flame<=24,'flame remains readable within compact header');assert.equal(status.animation,'none');
 assert.equal(await page.locator('.footer-hint').count(),0);
 await header();
 await page.getByRole('button',{name:'筛选题目',exact:true}).click();
 const sort=page.getByRole('combobox',{name:'排序方式',exact:true});assert.equal(await sort.inputValue(),'contestDate');
 await sort.click();await page.getByRole('listbox',{name:'排序方式'}).getByRole('option',{name:'难度',exact:true}).click();
 assert.equal(await sort.inputValue(),'difficulty');assert.equal(await page.locator('.filter-popover').count(),1);
 await page.keyboard.press('Escape');await page.locator('.filter-popover').waitFor({state:'hidden'});
 const beforeDirection=await page.locator('.problem-table tr[data-id]').first().getAttribute('data-id');await page.getByRole('button',{name:'切换题目排序方向',exact:true}).click();
 assert.equal(await page.getByRole('button',{name:'切换题目排序方向',exact:true}).getAttribute('aria-pressed'),'true');assert.notEqual(await page.locator('.problem-table tr[data-id]').first().getAttribute('data-id'),beforeDirection);
 await page.getByRole('button',{name:'切换题目排序方向',exact:true}).click();
 await shot('list');
 await settings('快捷键');
 const searchKey=page.getByLabel('快捷键 搜索',{exact:true});assert.equal(await searchKey.inputValue(),'Ctrl+F');
 await searchKey.focus();await page.keyboard.press('Control+G');assert.equal(await searchKey.inputValue(),'Ctrl+G');
 const saveKey=page.getByLabel('快捷键 保存草稿',{exact:true});await saveKey.focus();await page.keyboard.press('Control+G');
 await page.getByRole('alert').filter({hasText:'已用于'}).waitFor();assert.equal(await saveKey.inputValue(),'按下新快捷键');await page.keyboard.press('Escape');
 await page.keyboard.press('Escape');await page.getByRole('tab',{name:'外观',exact:true}).waitFor();
 await page.getByRole('tab',{name:'外观',exact:true}).click();
 await page.getByLabel('我的训练不透明度',{exact:true}).fill('100');await page.getByLabel('我的训练不透明度',{exact:true}).blur();
 await nav('我的训练').click();await page.locator('.problem-table').waitFor();
 const alpha=()=>page.locator('.list-page').evaluate(node=>{const c=getComputedStyle(node).backgroundColor;const canvas=document.createElement('canvas');canvas.width=canvas.height=1;const context=canvas.getContext('2d');context.fillStyle=c;context.fillRect(0,0,1,1);return context.getImageData(0,0,1,1).data[3];});
 assert.equal(await alpha(),255);
 await page.keyboard.press('Control+G');assert.equal(await page.getByLabel('搜索题目',{exact:true}).evaluate(node=>document.activeElement===node),true);
 await settings('外观');await page.getByLabel('我的训练不透明度',{exact:true}).fill('0');await page.getByLabel('我的训练不透明度',{exact:true}).blur();await nav('我的训练').click();assert.equal(await alpha(),0);
 await settings('外观');await page.getByLabel('我的训练不透明度',{exact:true}).fill('50');await page.getByLabel('我的训练不透明度',{exact:true}).blur();await nav('我的训练').click();assert(Math.abs(await alpha()-128)<=1);
 await nav('比赛').click();await page.locator('.competition-card').first().waitFor();await header();
 assert.match(await page.locator('.competition-page').evaluate(node=>getComputedStyle(node).backgroundColor),/0\.35/,'competition surface follows configured opacity');
 await shot('competitions');
 await page.getByRole('button',{name:'筛选比赛',exact:true}).click();assert.equal(await page.getByRole('combobox',{name:'筛选比赛分类'}).count(),0,'classification uses the adjacent folder browser');await page.getByRole('combobox',{name:'比赛年份',exact:true}).waitFor();await page.getByRole('button',{name:'关闭筛选',exact:true}).click();
 await page.getByRole('button',{name:'比赛文件夹浏览',exact:true}).click();await page.locator('.catalog-explorer').waitFor();
 await page.locator('.catalog-folder-row').filter({hasText:'XCPC'}).click();await page.locator('.catalog-folder-row').filter({hasText:'CCPC 区域赛'}).click();await page.locator('.catalog-folder-row').filter({hasText:'2025年'}).click();
 await page.locator('.competition-card').first().waitFor();assert.equal(await page.locator('.competition-card').count(),2);
 await page.getByRole('button',{name:/查看 牛客 CCPC 2025 郑州区域赛（热身赛）/}).click();await page.getByLabel(/CCPC 2025 郑州区域赛（热身赛）比赛详情/).waitFor();
 await page.getByRole('button',{name:'全部比赛',exact:true}).click();await page.getByRole('button',{name:'全部平台',exact:true}).click();assert(await page.locator('.catalog-folder-row').count()>=2);
 await nav('模拟赛').click();await page.locator('.mock-history').waitFor();
 assert.equal(await page.getByRole('tab',{name:/模拟赛记录|创建训练/}).count(),0);
 assert.deepEqual(await page.locator('.mock-history .record-row strong').allTextContents(),['训练记录 3','训练记录 2','训练记录 1']);
 const mock=await page.evaluate(()=>{const setup=document.querySelector('.mock-config').getBoundingClientRect(),history=document.querySelector('.mock-history').getBoundingClientRect();return {bottom:setup.bottom,history:history.top,borders:[...document.querySelectorAll('.mock-mode-options>button')].map(node=>parseFloat(getComputedStyle(node).borderTopWidth))};});
 assert(mock.history>=mock.bottom&&mock.history-mock.bottom<=20);assert(mock.borders.every(width=>width>=1));await shot('mock');
 await page.locator('.mock-history .record-row').first().click();await page.locator('.record-detail').waitFor();await page.keyboard.press('Escape');await page.locator('.mock-history').waitFor();
 console.log('STAGE radar');
 await nav('成长与能力').click();await page.getByLabel('一级知识雷达',{exact:true}).waitFor();await header();
 await radarNames();assert.equal(await page.getByRole('button',{name:'成就与称号',exact:true}).count(),0);assert.equal(await page.locator('.growth-account-hero #growth-goals').count(),1);
 await page.getByRole('button',{name:'新建目标',exact:true}).click();await page.getByRole('dialog',{name:'新建目标',exact:true}).waitFor();await page.getByRole('button',{name:'关闭目标设置',exact:true}).click();
 await page.getByLabel('账号成长统计',{exact:true}).waitFor();assert.equal(await page.getByText('下一步练什么',{exact:true}).count(),0);assert.equal(await page.getByText('今日同行',{exact:true}).count(),0);
 assert.equal(await page.locator('.radar-data-dot').count(),0);assert.equal(await page.locator('.radar-value').count(),0);
 await page.getByRole('button',{name:'数学与计数，掌握 ?%，进入二级雷达',exact:true}).click();await page.getByRole('button',{name:'素数，掌握 ?%，筛选题目',exact:true}).waitFor();await page.getByRole('button',{name:'取模与同余，掌握 ?%，筛选题目',exact:true}).waitFor();
 const backAlignment=await page.locator('.knowledge-radar>.progress-section-heading').evaluate(node=>{const h=node.querySelector('h2').getBoundingClientRect(),b=node.querySelector('.radar-back').getBoundingClientRect(),r=node.getBoundingClientRect();return {right:r.right-b.right,centers:Math.abs(h.y+h.height/2-b.y-b.height/2),gap:b.left-h.right};});
 assert(backAlignment.right<1&&backAlignment.centers<1&&backAlignment.gap>0,JSON.stringify(backAlignment));
 await page.getByRole('button',{name:'返回一级雷达',exact:true}).click();await page.getByRole('group',{name:'一级知识雷达',exact:true}).waitFor();
 await page.getByRole('button',{name:'数学与计数，掌握 ?%，进入二级雷达',exact:true}).click();
 await radarNames();await page.keyboard.press('Escape');await page.getByRole('group',{name:'一级知识雷达',exact:true}).waitFor();await page.getByRole('button',{name:'字符串，掌握 ?%，进入二级雷达',exact:true}).click();await radarNames();
 await shot('growth');
 await page.getByRole('button',{name:'KMP，掌握 ?%，筛选题目',exact:true}).click();await page.getByRole('group',{name:'当前知识点筛选',exact:true}).waitFor();
 assert.equal(await page.locator('.problem-table tr[data-id]').count(),3);await page.getByLabel('搜索题目',{exact:true}).fill('列表定位');
 await page.getByRole('button',{name:'清除知识点筛选 KMP',exact:true}).click();assert.equal(await page.locator('.active-knowledge-filter').count(),0);assert.equal(await page.getByLabel('搜索题目',{exact:true}).inputValue(),'列表定位');assert(await page.locator('.problem-table tr[data-id]').count()>1);await shot('knowledge-filter-cleared');
 await nav('排行榜').click();await page.locator('.ranking-self').waitFor();
 const own=page.locator('.ranking-self');assert.equal(await own.locator('.like-burst').getAttribute('data-liked'),'true');assert.equal(await own.locator('.ranking-message').count(),0);assert.equal(await own.locator('.avatar-rank-frame').count(),1);
 const ownHeart=await own.locator('.like-burst').boundingBox(),otherLast=await page.locator('.ranking-table tbody tr').nth(1).locator('.like-burst').boundingBox();
 assert(Math.abs(ownHeart.x+ownHeart.width-otherLast.x-otherLast.width)<1,'the last available action aligns with the right edge without a missing-message gap');
 assert.equal(await page.getByRole('button',{name:'清空当前榜单',exact:true}).count(),0,'user edition hides management even when an old service returns isAdmin');assert.equal(await page.locator('.ranking-admin-cell').count(),0);
 const ranking=await own.evaluate(row=>{const bounds=selector=>row.querySelector(selector).getBoundingClientRect(),self=row.getBoundingClientRect(),identity=bounds('.ranking-identity'),place=bounds('.ranking-place'),count=bounds('.ranking-count'),social=bounds('.ranking-social-cell');return {left:identity.left-self.left,place:place.width,right:self.right-count.right,gap:count.left-social.right,social:social.width};});
 assert(ranking.left<=ranking.place+10,JSON.stringify(ranking));assert.equal(ranking.gap,0);assert(ranking.social<=135);assert(ranking.right<=1);
 assert.equal((await own.locator('.profile-avatar-button').boundingBox()).width,76);assert.equal((await own.locator('.ranking-medal').boundingBox()).height,52);
 await page.locator('.social-activity').waitFor();assert.equal(await page.locator('.social-activity>div').count(),1);assert.equal(await page.locator('.social-activity').getByText('昨日用户').count(),0);
 await shot('rankings');await nav('题库').click();await nav('排行榜').click();assert.equal(await page.locator('.social-activity').count(),1);
 adminMode=true;await page.reload();await nav('排行榜').click();await page.getByRole('button',{name:'清空当前榜单',exact:true}).waitFor();assert.equal(await page.locator('.ranking-admin-cell').count(),2);adminMode=false;await page.reload();await page.locator('.problem-table').waitFor();
 console.log('STAGE scenes');
 await settings();for(const width of [1280,1600,2048]){await page.setViewportSize({width,height:1000});await chrome();const grid=await page.locator('.settings-home-grid').boundingBox();assert(grid.width>width*.7);assert(grid.height>700);}
 const sceneChecks=await page.locator('.settings-home-grid').evaluate(grid=>{
  const sample=(selector,time)=>{const node=grid.querySelector(selector),animation=node.getAnimations()[0];animation.pause();animation.currentTime=time;const box=node.getBoundingClientRect(),css=getComputedStyle(node);return {x:box.x,right:box.right,fill:Number(css.fillOpacity),opacity:Number(css.opacity),transform:css.transform};};
  const dino=grid.querySelector('.dino-traveler'),area=dino.closest('button').getBoundingClientRect(),start=sample('.dino-traveler',0),end=sample('.dino-traveler',9000),back=sample('.dino-traveler',18000);
  return {unique:new Set([...grid.querySelectorAll('.settings-scene')].map(node=>node.className.baseVal||node.className)).size,travel:end.x-start.x,returns:Math.abs(start.x-back.x),inside:start.x>=area.left&&end.right<=area.right,bulbDim:sample('.bulb-glass',0).fill,bulbLit:sample('.bulb-glass',3000).fill,balloon:sample('.balloon-flight',10000).opacity,buildings:new Set([...grid.querySelectorAll('.globe-building>path')].map(node=>node.getAttribute('d'))).size};
 });assert.equal(sceneChecks.unique,9);assert(sceneChecks.travel>100&&sceneChecks.returns<2&&sceneChecks.inside,JSON.stringify(sceneChecks));assert(sceneChecks.bulbLit>sceneChecks.bulbDim*3&&sceneChecks.bulbLit<.4);assert(sceneChecks.balloon>.8);assert.equal(sceneChecks.buildings,8);
 await shot('settings');await page.getByRole('tab',{name:'鸣谢',exact:true}).click();assert.equal(await page.locator('.acknowledgements p').count(),7);assert.equal(await page.locator('.acknowledgements').evaluate(node=>new Set([...node.querySelectorAll('p')].map(p=>getComputedStyle(p).color)).size),6);await shot('thanks');await page.getByRole('button',{name:'返回设置首页',exact:true}).click();await page.locator('.settings-home-grid').waitFor();
 await page.getByRole('tab',{name:'更新',exact:true}).click();assert.equal(await page.getByRole('button',{name:'查看更新通知',exact:true}).count(),0);await page.getByRole('button',{name:'返回设置首页',exact:true}).click();
 await page.getByRole('tab',{name:'翻译 API',exact:true}).click();await page.getByLabel('题面翻译配置',{exact:true}).waitFor();assert.notEqual(await page.locator('.settings-translation-panel').evaluate(node=>getComputedStyle(node).backgroundColor),'rgba(0, 0, 0, 0)');assert.equal(await page.locator('.translation-settings .progress-small').count(),0);await page.getByRole('button',{name:'题面翻译说明',exact:true}).focus();await page.getByRole('tooltip').filter({hasText:'只翻译公开题面'}).waitFor();await page.keyboard.press('Escape');await shot('translation');await page.getByRole('button',{name:'返回设置首页',exact:true}).click();
 await page.getByRole('tab',{name:'交互与导航',exact:true}).click();assert.equal(await page.locator('.navigation-editor-row').count(),12);assert.equal(await page.getByText('自定义顺序',{exact:true}).count(),0);await page.keyboard.press('Escape');
 console.log('STAGE lectures');
 await nav('从零讲').click();await page.locator('.lectures-layout').waitFor();await header();assert.equal(await page.locator('.workspace-area h2').filter({hasText:'从零讲'}).count(),0);
 assert.equal(await page.locator('.lectures-layout').evaluate(node=>getComputedStyle(node).backgroundColor),'rgba(0, 0, 0, 0)');assert.equal((await page.locator('.lecture-difficulty').first().innerText()).includes('≈'),false);await shot('lectures');
 await page.getByRole('combobox',{name:'从零讲知识分类'}).press('Space');
 const knowledgeFolders=page.getByRole('listbox',{name:'从零讲知识分类'});
 await knowledgeFolders.getByRole('option',{name:'动态规划',exact:true}).click();await shot('lecture-folders');
 await knowledgeFolders.getByRole('option',{name:'选择「动态规划」',exact:true}).click();assert.equal(await page.locator('.lectures-list>button').count(),2);
 await page.getByRole('combobox',{name:'从零讲知识分类'}).press('Space');await knowledgeFolders.getByRole('option',{name:'动态规划',exact:true}).click();await knowledgeFolders.getByRole('option',{name:'线性 DP',exact:true}).click();assert.equal(await page.locator('.lectures-list>button').count(),1);
 await page.getByRole('combobox',{name:'从零讲知识分类'}).press('Space');await knowledgeFolders.getByRole('button',{name:'返回上一级',exact:true}).click();await knowledgeFolders.getByRole('option',{name:'全部知识分类',exact:true}).click();assert.equal(await page.locator('.lectures-list>button').count(),3);
 await nav('提交记录').click();await page.locator('.submission-log-row').first().waitFor();assert.equal(await page.locator('.submission-log-row>svg').count(),0);assert.equal(await page.locator('.submission-runtime').count(),1);assert.equal(await page.locator('.submission-runtime').innerText(),'15 ms');
 await nav('算法实验室').click();assert.equal(await page.getByText('算法题单',{exact:true}).count(),0);
 await page.locator('.lab-multi-catalog').waitFor();assert.equal(await page.locator('.lab-multi-catalog .catalog-card').count(),10);
 await page.getByRole('button',{name:'打开算法 背包 DP',exact:true}).click();await page.locator('.algorithm-lab .lab-course-header').waitFor();assert.equal(await page.locator('.lab-lesson-footer').count(),0);
 await page.getByRole('button',{name:'下一页',exact:true}).click();await page.getByRole('heading',{name:/把大问题拆小/}).waitFor();
 await page.locator('.learning-paths-page').evaluate(node=>{node.scrollTop=node.scrollHeight;});
 const labNext=await page.getByRole('button',{name:'下一页',exact:true}).boundingBox(), lessonBox=await page.locator('.lab-lesson').boundingBox();assert(labNext.y>=0&&labNext.y<90,'navigation stays in the compact immersive header while scrolling');assert.equal(await page.locator('.sidebar').isVisible(),false);assert.equal(await page.locator('.topbar').isVisible(),false);
 assert.equal(await page.locator('.lab-course-header').getByRole('button',{name:'进入跟着做题',exact:true}).count(),0);
 for(const width of [2048,1280]){await page.setViewportSize({width,height:1000});await page.locator('.learning-paths-page').evaluate(node=>node.scrollTop=0);const body=await page.locator('.lab-lesson').boundingBox(),area=await page.locator('.learning-paths-page').boundingBox();assert(body.width>area.width*.9,'immersive course uses the available page width');await shot('algorithm-lab-wide-'+width);}
 await page.locator('.learning-paths-page').evaluate(node=>{node.style.setProperty('--page-opacity','30%');node.style.backgroundImage='linear-gradient(135deg,#24566a,#31354d)';});
 const railColors=await page.locator('.lab-course-tools button').evaluateAll(buttons=>buttons.map(button=>({background:getComputedStyle(button).backgroundColor,opacity:getComputedStyle(button).opacity})));
 const lessonColor=await page.locator('.lab-panel').first().evaluate(node=>getComputedStyle(node).backgroundColor);
 assert(railColors.every(item=>item.background===lessonColor&&item.opacity==='1'),JSON.stringify({railColors,lessonColor}));await shot('algorithm-lab-translucent-controls');
 await page.locator('.learning-paths-page').evaluate(node=>{node.style.removeProperty('--page-opacity');node.style.removeProperty('background-image');});
 await page.setViewportSize({width:2048,height:1000});await page.getByRole('button',{name:'目录',exact:true}).click();await page.getByRole('navigation',{name:'课程章节'}).getByRole('button',{name:/独立练习/}).click();
 await page.getByRole('button',{name:'进入跟着做题',exact:true}).click();await page.getByRole('heading',{name:'采药',exact:true}).waitFor();
 const guidanceSaved=page.waitForResponse(response=>response.url().endsWith('/api/preferences')&&response.request().method()==='POST'&&response.request().postData().includes('"assisted":true'));
 await page.getByRole('button',{name:'3 推到代码',exact:true}).click();await page.getByRole('form',{name:'补出关键转移'}).waitFor();await guidanceSaved;
 mockActive={id:'lab-lock',name:'隔离考场',status:'running',startedAt:timestamp,endsAt:new Date(Date.now()+3600000).toISOString(),duration:60,total:1,remainingSeconds:3600,slots:[{...rows[117],id:'fixture:alias:P1048',letter:'A'}]};
 await page.reload();await nav('算法实验室').click();await page.getByRole('button',{name:'打开算法 背包 DP',exact:true}).click();await page.getByRole('region',{name:'跟做指导已锁定',exact:true}).waitFor();
 assert.equal(await page.getByRole('form',{name:'补出关键转移'}).count(),0,'guided source obeys the active original-task lock, including aliases');
 assert.equal(await page.getByRole('navigation',{name:'解题过程'}).count(),0);await shot('algorithm-lab-locked');
 mockActive=null;await page.reload();await nav('算法实验室').click();await page.getByRole('button',{name:'打开算法 背包 DP',exact:true}).click();await page.getByRole('form',{name:'补出关键转移'}).waitFor();
 await page.getByRole('button',{name:'5 自行实现',exact:true}).click();
 const labCheck=await page.locator('.lab-implementation input[type=checkbox]').first().boundingBox();assert(labCheck.width<=20&&labCheck.height<=20);await shot('algorithm-lab-guided');
 await page.getByRole('button',{name:'进入工作台实现',exact:true}).click();await page.locator('.cm-editor').waitFor();
 assert.equal(writes.some(row=>row.path==='/api/training/start'&&row.body?.id==='lab:luogu:P1048'&&row.body.assisted===true),true,'guided problem opens the real practice flow with assistance evidence');
 await page.reload();await nav('题库').click();
 await page.locator('.problem-table tr[data-id] .problem-title').first().click();await page.locator('.cm-editor').waitFor();
 assert.equal(await page.locator('.sidebar').isVisible(),false);assert.equal(await page.locator('.topbar').isVisible(),false);
 const box=await page.locator('.tb-workbench').boundingBox();assert.deepEqual({x:box.x,y:box.y,width:box.width,height:box.height},{x:0,y:0,width:2048,height:1000});
 assert.equal(await page.locator('.wb-editor-actions .wb-solution-button').count(),1);await shot('workbench');
 await page.route('**/src/components/SolutionMarkdown.jsx*',async route=>{await new Promise(resolve=>setTimeout(resolve,600));await route.continue();});
 await page.evaluate(()=>{window.readerWidths=[];window.readerWatch=true;function sample(){const panel=document.querySelector('.reader-panel');if(panel)window.readerWidths.push(panel.getBoundingClientRect().width);if(window.readerWatch)requestAnimationFrame(sample);}sample();});
 await page.locator('.wb-solution-button').click();await page.locator('.reader-panel .markdown').waitFor();await page.waitForTimeout(150);const widths=await page.evaluate(()=>{window.readerWatch=false;return window.readerWidths;});assert(widths.length>2);assert(Math.max(...widths)-Math.min(...widths)<2,JSON.stringify(widths));await page.getByRole('button',{name:'收起题解',exact:true}).click();await page.locator('.reader-panel').waitFor({state:'hidden'});
 const oldTitle=await page.locator('.wb-heading strong').innerText();trainingDelay=450;
 await page.evaluate(()=>{window.chromeFlash=false;window.nextWatch=true;function sample(){if(!document.querySelector('.practice-focus')||!document.querySelector('.tb-workbench'))window.chromeFlash=true;if(window.nextWatch)requestAnimationFrame(sample);}sample();});
 await page.getByRole('button',{name:'下一题',exact:true}).click();await page.waitForFunction(title=>{const node=document.querySelector('.wb-heading strong');return node&&node.textContent!==title&&!node.textContent.includes('载入');},oldTitle);assert.equal(await page.evaluate(()=>{window.nextWatch=false;return window.chromeFlash;}),false);trainingDelay=0;
 const heldTitle=await page.locator('.wb-heading strong').innerText();failDraft=true;await page.locator('.cm-content').click();await page.keyboard.type('// unsaved review code');await page.getByRole('button',{name:'下一题',exact:true}).click();await page.waitForTimeout(150);assert.equal(await page.locator('.wb-heading strong').innerText(),heldTitle,'save failure keeps current editor');failDraft=false;await page.locator('.cm-content').click();await page.keyboard.press('Control+S');
 await page.locator('.cm-content').click();await page.keyboard.press('Escape');await page.locator('.problem-table').waitFor();assert.equal(await page.locator('.sidebar').isVisible(),true);
 await page.getByRole('button',{name:'消息通知',exact:true}).click();assert.equal(await page.getByText('题库与版本更新',{exact:true}).count(),0);
 const messageTitle=page.locator('.social-notifications-title');assert.equal(await messageTitle.innerText(),'和');
 const titleParts=await messageTitle.locator(':scope > span').evaluateAll(nodes=>nodes.map(node=>{const r=node.getBoundingClientRect();return {x:r.x,right:r.right,center:r.y+r.height/2};}));
 assert(titleParts.every(part=>Math.abs(part.center-titleParts[0].center)<1));assert(titleParts.slice(1).every((part,index)=>part.x>titleParts[index].right));await shot('social-title-aligned');await page.keyboard.press('Escape');
 await page.evaluate(()=>window.dispatchEvent(new CustomEvent('tb:browser-preparation',{detail:{status:'needs_login'}})));assert.equal(await page.getByRole('dialog',{name:'浏览器原站提交'}).count(),0);
 for(const width of [1280,2048])for(const name of ['我的训练','题库','比赛','模拟赛','算法实验室','排行榜','成长与能力','提交记录','活动记录','从零讲']){
  await page.setViewportSize({width,height:1000});await nav(name).click();await page.waitForTimeout(75);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'page overflow: '+name+' '+width);
  const area=await page.locator('.workspace-area').boundingBox();assert(area.x>=0&&area.x+area.width<=width+1,name);await shot('audit-'+name+'-'+width);
 }

 console.log('STAGE rich-fixture');
 // The new layout uses real filtered pools, bounded month grids and all surface presets.
 richFixture=true;rows.forEach((row,index)=>row.tags=[...row.tags,'专题'+Math.floor(index/3)]);await page.reload();await nav('题库').click();await page.locator('.problem-table').waitFor();
 const firstPageIds=await page.locator('.problem-table tr[data-id]').evaluateAll(nodes=>nodes.map(node=>node.dataset.id));
 await page.evaluate(()=>{window.savedRandom=crypto.getRandomValues.bind(crypto);crypto.getRandomValues=array=>{array[0]=119;return array;};});
 await page.getByRole('button',{name:'随机单题',exact:true}).click();await page.getByRole('button',{name:'确认',exact:true}).click();await page.locator('.cm-editor').waitFor();
 const randomId=writes.filter(item=>item.path==='/api/training/start').at(-1).body.id;
 assert(!firstPageIds.includes(randomId),'random selection spans all pages');
 await page.keyboard.press('Escape');await page.getByRole('button',{name:'随机单题',exact:true}).click();await page.getByRole('button',{name:'确认',exact:true}).click();await page.locator('.cm-editor').waitFor();
 assert.equal(writes.filter(item=>item.path==='/api/training/start').at(-1).body.id,randomId,'pure random permits repeat draws');await page.keyboard.press('Escape');
 await page.getByLabel('搜索题目',{exact:true}).fill('KMP');await page.waitForFunction(()=>document.querySelectorAll('.problem-table tr[data-id]').length===3);
 await page.getByRole('button',{name:'随机单题',exact:true}).click();await page.getByRole('button',{name:'确认',exact:true}).click();await page.locator('.cm-editor').waitFor();
 assert(rows.slice(20,23).some(row=>row.id===writes.filter(item=>item.path==='/api/training/start').at(-1).body.id),'random draw honors the current search filter');await page.keyboard.press('Escape');
 await page.evaluate(()=>{crypto.getRandomValues=window.savedRandom;});
 await page.getByRole('button',{name:'筛选题目',exact:true}).click();
 const minimum=page.getByLabel('最低难度滑块',{exact:true}),minInput=page.getByLabel('最低难度',{exact:true});const oldMinimum=Number(await minInput.inputValue());await minimum.focus();await page.keyboard.press('ArrowRight');await page.waitForFunction(expected=>Number(document.querySelector('input[aria-label="最低难度"]')?.value)===expected,oldMinimum+100);assert.equal(Number(await minInput.inputValue()),oldMinimum+100);
 const track=await page.locator('.filter-popover .difficulty-range-track').boundingBox(),limits=await minimum.evaluate(node=>({min:Number(node.min),max:Number(node.max),value:Number(node.value)})),startFraction=(limits.value-limits.min)/(limits.max-limits.min);await page.mouse.move(track.x+6+(track.width-12)*startFraction,track.y+14);await page.mouse.down();await page.mouse.move(track.x+6+(track.width-12)*.65,track.y+14,{steps:6});await page.mouse.up();
 assert(Number(await minInput.inputValue())>oldMinimum+100,'the actual lower thumb can be dragged within the current catalog difficulty bounds');await page.keyboard.press('Escape');
 await nav('活动记录').click();await page.locator('.activity-month-grid').waitFor();
 assert.equal(await page.locator('.activity-month-grid [role=gridcell]').count(),Math.round((new Date(Number(date.slice(0,4))+1,0,1)-new Date(Number(date.slice(0,4)),0,1))/86400000));
 const beforeDay=await page.locator('.activity-selected-summary time').getAttribute('dateTime');await page.keyboard.press('ArrowLeft');
 assert.notEqual(await page.locator('.activity-selected-summary time').getAttribute('dateTime'),beforeDay,'arrow keys select immediately without Enter');
 for(const height of [1000,720,600]){
  await page.setViewportSize({width:1600,height});await page.waitForTimeout(80);
  const geometry=await page.locator('.activity-month-page').evaluate(node=>({height:node.clientHeight,scroll:node.scrollHeight,rows:node.querySelectorAll('tbody tr').length,overflow:node.querySelector('.activity-detail-table').scrollHeight>node.querySelector('.activity-detail-table').clientHeight+1}));
  assert(geometry.scroll<=geometry.height+1&&!geometry.overflow,JSON.stringify(geometry));
  assert(geometry.rows>0,'remaining viewport gets visible detail rows');await shot('monthly-activity-'+height);
 }
 if(await page.getByRole('button',{name:'下一页日期明细',exact:true}).isEnabled()){
  const first=await page.locator('.activity-detail-table tbody tr[data-date]').evaluateAll(nodes=>nodes.map(node=>node.dataset.date));await page.getByRole('button',{name:'下一页日期明细',exact:true}).click();await page.waitForFunction(previous=>JSON.stringify([...document.querySelectorAll('.activity-detail-table tbody tr[data-date]')].map(node=>node.dataset.date))!==JSON.stringify(previous),first);
 }
 const previousYear=String(Number(date.slice(0,4))-1);await page.getByLabel('活动年份',{exact:true}).selectOption(previousYear);await page.waitForFunction(y=>[...document.querySelectorAll('.activity-month-grid [role=gridcell]')].every(node=>node.dataset.date.startsWith(y)),previousYear);assert.equal(await page.locator('.activity-month-grid [role=gridcell]').count(),Math.round((new Date(Number(previousYear)+1,0,1)-new Date(Number(previousYear),0,1))/86400000));
 await page.getByLabel('活动年份',{exact:true}).selectOption(date.slice(0,4));await page.setViewportSize({width:1600,height:1000});
 await nav('成长与能力').click();await page.getByRole('button',{name:'数学与计数，掌握 ?%，进入二级雷达',exact:true}).click();
 const panels=await page.locator('.progress-growth-columns').evaluate(node=>{const [left,right]=[...node.children].map(item=>item.getBoundingClientRect());return {top:Math.abs(left.top-right.top),bottom:Math.abs(left.bottom-right.bottom)};});assert(panels.top<1&&panels.bottom<1,JSON.stringify(panels));
 const topicPages=page.getByRole('navigation',{name:'知识点分页',exact:true}),seenTopics=new Set();
 for(let index=0;index<4;index++){const names=await page.locator('.radar-detail-row>button').evaluateAll(nodes=>nodes.map(node=>node.childNodes[0].textContent));assert(names.length>0&&names.length<=12,'each radar page has at most12 actual topics');names.forEach(name=>seenTopics.add(name));if(index<3){await topicPages.getByRole('button',{name:'下一页',exact:true}).click();await page.waitForFunction(first=>document.querySelector('.radar-detail-row>button')?.childNodes[0].textContent!==first,names[0]);}}
 assert.equal(seenTopics.size,40,'all40 backed-by-three-problem topics remain reachable');await shot('bounded-radar');
 await nav('从零讲').click();const ratings=(await page.locator('.lecture-difficulty').allTextContents()).map(Number);assert.deepEqual(ratings,[...ratings].sort((a,b)=>a-b));assert.equal(await page.getByRole('button',{name:'筛选讲解',exact:true}).count(),0);
 await page.locator('.lectures-list>button').filter({hasText:'二分查找'}).click();await page.getByRole('navigation',{name:'相关知识从零讲'}).waitFor();await page.getByRole('button',{name:'从零讲：线性 DP',exact:false}).click();await page.getByRole('article',{name:'知识讲解正文'}).getByText('独立复用基础知识。').waitFor();
 await nav('算法实验室').click();await page.waitForFunction(()=>document.querySelector('.lab-catalog,.lab-course-header'));if(await page.getByRole('button',{name:'打开算法 背包 DP',exact:true}).count())await page.getByRole('button',{name:'打开算法 背包 DP',exact:true}).click();if(await page.getByRole('button',{name:'返回学算法',exact:true}).count())await page.getByRole('button',{name:'返回学算法',exact:true}).click();await page.getByRole('button',{name:'目录',exact:true}).click();await page.getByRole('navigation',{name:'课程章节'}).getByRole('button').first().click();await page.getByRole('button',{name:'下一页',exact:true}).click();
 await page.clock.install({time:Date.now()});await openPage('题库');await page.locator('.problem-table').waitFor();await page.clock.fastForward(179000);await openPage('算法实验室');await page.getByRole('heading',{name:/把大问题拆小/}).waitFor();
 await openPage('题库');await page.clock.fastForward(180000);await openPage('算法实验室');await page.getByRole('button',{name:'打开算法 背包 DP',exact:true}).waitFor();await page.clock.resume();
 await settings('数据统计');await page.getByRole('region',{name:'个人数据统计',exact:true}).waitFor();assert.equal(await page.locator('.personal-stat').count(),8);await shot('personal-statistics');
 await page.getByRole('button',{name:'返回设置首页',exact:true}).click();await page.getByRole('tab',{name:'更新',exact:true}).click();
 assert.equal(await page.getByLabel('自动检查间隔',{exact:true}).count(),0);assert.equal(await page.getByLabel('自动收录最低难度',{exact:true}).count(),0);assert.equal(await page.locator('.update-status').count(),0);
 const clickable=await page.getByRole('button',{name:'检查软件更新',exact:true}).evaluate(node=>{const s=getComputedStyle(node);return {background:s.backgroundColor,border:s.borderTopWidth};});assert.notEqual(clickable.background,'rgba(0, 0, 0, 0)');assert.equal(clickable.border,'1px');await shot('settings-updates');
 for(const theme of ['dark','light'])for(const style of ['minimal','outlined','aurora','blueprint'])for(const name of ['题库','比赛','模拟赛','成长与能力','提交记录','活动记录','从零讲']){
  await nav(name).click();await page.waitForTimeout(30);await page.evaluate(({theme,style})=>{document.documentElement.dataset.theme=theme;document.documentElement.dataset.panelStyle=style;},{theme,style});
  const appearance=await page.locator('.workspace-area').evaluate(node=>{const panels=[...node.querySelectorAll('.list-page,.records-page,.mock-config,.progress-section,.lectures-list,.lectures-detail')];return panels.map(panel=>({image:getComputedStyle(panel).backgroundImage,radius:getComputedStyle(panel).borderTopLeftRadius,rect:panel.getBoundingClientRect().width}));});
  assert(appearance.length>0,name);assert(appearance.every(panel=>style==='minimal'||style==='outlined'?panel.image==='none':style==='blueprint'?panel.image.includes('linear-gradient'):panel.image.includes('radial-gradient')),JSON.stringify({name,style,appearance}));
  await checkOverflow();if(theme==='dark'&&style==='blueprint'&&['提交记录','活动记录','成长与能力'].includes(name))await shot('blueprint-'+name);
 }
 await page.evaluate(()=>{document.documentElement.dataset.theme='dark';document.documentElement.dataset.panelStyle='outlined';});

 console.log('STAGE artwork');
 rankingOnlySelf=true;await page.reload();await nav('排行榜').click();await page.locator('.ranking-self').waitFor();
 for(const width of [2048,1280,800]){
  await page.setViewportSize({width,height:1000});
  const aligned=await page.locator('.ranking-self').evaluate(row=>{const a=row.querySelector('.profile-avatar-button').getBoundingClientRect(),m=row.querySelector('.ranking-medal').getBoundingClientRect(),c=row.querySelector('.ranking-count b').getBoundingClientRect(),l=row.querySelector('.like-burst').getBoundingClientRect(),r=row.getBoundingClientRect();return {right:r.right-row.querySelector('.ranking-count').getBoundingClientRect().right,countGap:row.querySelector('.ranking-count').getBoundingClientRect().left-l.right,centerGap:Math.abs(a.y+a.height/2-m.y-m.height/2),avatar:a.width,medal:m.height};});
  assert(aligned.right<=10&&aligned.right>=0,JSON.stringify(aligned));assert(aligned.countGap<=35&&aligned.countGap>=0,JSON.stringify(aligned));assert(aligned.centerGap<1,JSON.stringify(aligned));assert(aligned.avatar>=(width>800?76:58)&&aligned.medal>=(width>800?52:42));
  await shot('ranking-self-right-'+width);
 }
 await page.goto('http://127.0.0.1:18831/tests/ui-feedback-fixture.html?view=streak');await page.locator('.streak-preview .practice-streak').last().waitFor();
 const flameShapes=await page.locator('.streak-preview .flame-lit .flame-shell').evaluateAll(nodes=>nodes.map(node=>node.getAttribute('d')));assert.equal(new Set(flameShapes).size,7);
 for(const theme of ['dark','light']){
  await page.evaluate(theme=>document.documentElement.dataset.theme=theme,theme);await shot('streak-shapes-'+theme);
  const dims=await page.locator('.streak-preview .streak-flame').evaluateAll(nodes=>nodes.map(node=>{const r=node.getBoundingClientRect();return [r.width,r.height];}));assert(dims.every(([w,h])=>w===h&&w>=20&&w<=24));
 }
 await page.goto('http://127.0.0.1:18831/tests/ui-feedback-fixture.html');await page.locator('.tier-preview').last().waitFor();
 assert.equal(await page.locator('.profile-xp-ring').first().evaluate(node=>getComputedStyle(node).transform),'matrix(0, 1, -1, 0, 0, 0)');
 const symmetry=await page.locator('.tier-preview>.medal-rank').evaluateAll(async medals=>{
  const results=[];
  for(const medal of medals){
   const svg=medal.cloneNode(true),style=getComputedStyle(medal),canvas=document.createElement('canvas');canvas.width=240;canvas.height=276;
   svg.setAttribute('xmlns','http://www.w3.org/2000/svg');svg.setAttribute('width','240');svg.setAttribute('height','276');svg.style.color=style.color;svg.style.setProperty('--panel-base',style.getPropertyValue('--panel-base'));
   const picture=new Image();picture.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(new XMLSerializer().serializeToString(svg));await picture.decode();
   const context=canvas.getContext('2d');context.drawImage(picture,0,0);const data=context.getImageData(0,0,240,276).data;let difference=0;
   for(let y=0;y<276;y++)for(let x=0;x<120;x++)for(let channel=0;channel<4;channel++)difference+=Math.abs(data[(y*240+x)*4+channel]-data[(y*240+239-x)*4+channel]);
   results.push(difference/(120*276*4));
  }
  return results;
 });
 assert(symmetry.every(difference=>difference<1),JSON.stringify(symmetry));await shot('rank-artwork');
 await page.goto('http://127.0.0.1:18831/tests/ui-feedback-fixture.html?view=achievements');await page.locator('.achievement-icon').first().waitFor();
 const meanings=await page.locator('.progress-achievement').evaluateAll(cards=>Object.fromEntries(cards.map(card=>[card.dataset.achievementId,card.querySelector('.achievement-icon').dataset.achievementSymbol])));
 assert.equal(meanings['difficulty-1500'],'footprints');assert.equal(meanings['difficulty-2400'],'gem');assert.equal(meanings['streak-365'],'orbit');assert.equal(meanings['missions-1'],'gift');assert.equal(meanings['platforms-2'],'network');
 assert.equal(await page.locator('.progress-achievement>.medal-emblem').count(),0);await shot('achievement-symbols');
 await page.goto('http://127.0.0.1:18831/tests/ui-feedback-fixture.html?view=radar');await page.getByRole('button',{name:'字符串，掌握 ?%，进入二级雷达',exact:true}).waitFor();assert.equal(await page.locator('.radar-data-dot').count(),0);assert.equal(await page.locator('.radar-value').count(),0);await page.getByRole('button',{name:'字符串，掌握 ?%，进入二级雷达',exact:true}).click();await page.getByRole('button',{name:/^KMP，掌握 [0-9]+%，筛选题目$/}).waitFor();await page.getByRole('button',{name:'字典树，掌握 ?%，筛选题目',exact:true}).waitFor();await shot('mastery');
 assert.deepEqual(errors,[]);console.log('PASS: compact chrome, logo toggle, left queue headings, AC colors and sizes, deep contest folders, inline sorted mock history, canonical radar labels, removable knowledge filters, compact rankings, goals in account panel, rounded lecture surfaces, clean submission rows, symmetric rank artwork and semantic achievement symbols; existing search, shortcuts, opacity, settings, practice and Escape checks passed.');
}catch(error){await shot('failure').catch(()=>{});throw error;}finally{await browser.close();await vite.close();}
