import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { createServer } from 'vite';
import { chromium } from 'playwright';

const vite=await createServer({server:{host:'127.0.0.1',port:18831,strictPort:true}});
await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[],writes=[];
page.on('pageerror',error=>errors.push(error.message));
page.setDefaultTimeout(12000);
const timestamp=new Date().toISOString(),date=new Date().toLocaleDateString('sv-SE',{timeZone:'Asia/Shanghai'});
const self={userId:'11111111-1111-4111-8111-111111111111',nickname:'训练者甲'},other={userId:'22222222-2222-4222-8222-222222222222',nickname:'训练者乙'};
const rows=Array.from({length:120},(_,index)=>({id:`fixture::${index}`,contest:'周赛 166',problem:String(index+1),title:`列表定位测试 ${String(index+1).padStart(3,'0')}`,tags:['模拟'],knowledge:'模拟',platform:'牛客',series:'周赛',difficulty:800+index*10,url:`https://example.com/${index}`,contestDate:'2026-10-20T00:00:00Z',solutionAvailable:true}));
rows[20]={...rows[20],tags:['KMP'],knowledge:'KMP'};
rows[118]={...rows[118],contest:'CCPC 2025 郑州区域赛（热身赛）',series:'XCPC'};
rows[119]={...rows[119],contest:'CCPC 2025 郑州区域赛',series:'XCPC'};
let mockRecords=[1,3,2].map(day=>({id:`mock-${day}`,name:`训练记录 ${day}`,status:'finished',startedAt:`2026-10-${String(day).padStart(2,'0')}T10:00:00Z`,duration:120,total:4,accepted:day,slots:rows.slice(0,4).map((row,index)=>({...row,letter:String.fromCharCode(65+index),accepted:index<day,attempts:1}))}));
const training=rows.filter(row=>row.id!==rows[119].id).map(row=>({id:row.id,activeAt:timestamp,lastActivityAt:timestamp,today:true,accepted:false,verdict:null,attempts:0}));
let preferences=null,likes={total:4,likedToday:false},failLike=true,boardDay=date,notifications=[{id:'33333333-3333-4333-8333-333333333333',kind:'comment',actor:other,recipient:self,text:'一起加油 <script>window.untrusted=true</script>',createdAt:timestamp,read:false}];
notifications.push(...Array.from({length:100},(_,index)=>({id:`55555555-5555-4555-8555-${String(index).padStart(12,'0')}`,kind:'like',actor:other,recipient:self,createdAt:timestamp,read:false})));
const workspace=()=>({training,sets:[],contests:mockRecords,activeContest:null,goals:{goals:[]},goalTasks:[...rows.slice(0,2),{...rows[119],accepted:true}],summary:{total:120,accepted:training.filter(row=>row.accepted).length,todayAccepted:2,beforeTodayAccepted:82,historicalAccepted:84,attempts:0,due:0,pending:0,streak:12},now:timestamp});
const progress={badge:'tier-7',level:8,tier:'大师',rankTier:'大师',rankScore:2000,titles:[]};
const ranked={badge:'tier-7',tier:'大师',qualified:true,abilityScore:2000,nextAbilityScore:2100,evidenceCount:8,minimumEvidence:5,levelGate:5};
ranked.tierRequirements=['黑铁','青铜','白银','黄金','铂金','翡翠','钻石','大师','宗师','王者'].map((tier,index)=>({tier,badge:`tier-${index}`,minAbilityScore:[0,800,1000,1200,1400,1600,1800,2000,2100,2200][index]}));
const hub={settings:{githubRepo:'3097729287/acm-algo-trainer',accounts:{},autoSync:false,intervalHours:6,minDifficulty:0,maxDifficulty:2199},sync:{busy:false},updates:{currentVersion:'1.1.5'},accounts:[],notifications:[]};
await page.addInitScript(()=>localStorage.setItem('tb.preferences',JSON.stringify({theme:'dark',accent:'teal',backdrop:'aurora',panelOpacity:35,widgets:true,fontSize:16,navOrder:['mine','library','competitions','mock','rankings','growth','records','activity','lectures'],views:[]})));
await page.route('**/api/**',async route=>{
  const request=route.request(),url=new URL(request.url()),path=url.pathname;
  if(!path.startsWith('/api/'))return route.continue();
  const body=request.method()==='POST'?request.postDataJSON():null;
  if(body)writes.push({path,body});
  let value;
  if(path==='/api/account')value={required:false,authenticated:true,usesOriginalWorkspace:true,token:'fixture',account:self};
  else if(path==='/api/preferences'){if(body)preferences=body.preferences;value={preferences,updatedAt:timestamp};}
  else if(path==='/api/software-update')value={currentVersion:'1.1.5',status:'current',autoCheck:false,canInstall:false};
  else if(path==='/api/browser-preparation')value={available:false};
  else if(path==='/api/data')value={rows,categories:[{name:'数据结构',tags:['栈','单调栈'],children:[{name:'单调栈',tags:['单调栈']}]},{name:'数学',tags:['素数','取模与同余'],children:[{name:'素数',tags:['素数']},{name:'取模与同余',tags:['取模与同余']}]},{name:'字符串',tags:['KMP','字典树'],children:[{name:'KMP',tags:['KMP']},{name:'字典树',tags:['字典树']}]}],token:'fixture',today:date,revision:'ui-social'};
  else if(path==='/api/workspace')value=workspace();
  else if(path==='/api/hub')value=hub;
  else if(path==='/api/insights')value={summary:{officialSolved:0,submissions:0,activeDays:1,streak:1},growth:{...progress,totalXp:6265,currentLevelXp:665,nextLevelXp:1600,ranked},knowledge:[],achievements:[],activity:[],recommendations:[],assessment:{platforms:[]},dailyTasks:{tasks:[]}};
  else if(path==='/api/profile')value={profile:self,leaderboard:{configured:true,status:'ready'}};
  else if(path==='/api/goals')value={goals:[]};
  else if(path==='/api/contests/events')value={events:[]};
  else if(path==='/api/contest')value={contest:mockRecords.find(item=>item.id===url.searchParams.get('id'))};
  else if(path==='/api/contests/delete'){mockRecords=body.all?[]:mockRecords.filter(item=>item.id!==body.id);value={workspace:workspace(),deleted:1};}
  else if(path==='/api/submissions')value={submissions:rows.slice(0,3).map((row,index)=>({id:`submission-${index}`,problemId:row.id,submittedAt:timestamp,mode:'submit',verdict:'AC',timeMs:index===2?15:null})),total:3,hasMore:false};
  else if(path==='/api/lectures')value={lectures:[{id:'lesson',title:'二分查找',category:'基础技巧',tags:['二分']} ]};
  else if(path==='/api/desktop/fullscreen')value={available:false,fullscreen:false};
  else if(path==='/api/training/start')value={workspace:workspace()};
  else if(path==='/api/problem')value={id:url.searchParams.get('id'),title:rows.find(row=>row.id===url.searchParams.get('id')).title,markdown:'## 题目描述\n\n测试题面。\n\n## 样例\n\n```text\n1 2\n```',samples:[{input:'1\n',output:'2\n'}],limits:{timeMs:2000,memoryMb:256},judge:{scope:'samples',cases:1},statementAvailable:true,draft:'int main() { return 0; }',submissions:[]};
  else if(path==='/api/draft')value={savedAt:timestamp};
  else if(path==='/api/translation/settings')value={provider:'custom',providerName:'自定义',model:'fixture',configured:false,keyStored:false,providers:[]};
  else if(path==='/api/leaderboard')value={period:url.searchParams.get('period')||'daily',date:boardDay,configured:true,status:'ready',hasSnapshot:true,socialAvailable:true,socialProtocol:1,isAdmin:true,entries:[{...self,rank:1,count:2,likes:{total:9,likedToday:false},publicProgress:progress},{...other,rank:2,count:1,likes,publicProgress:progress}],self};
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
const checkOverflow=async()=>assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
async function shot(name){await page.screenshot({path:`tests/screenshots/v131-${name}.png`,animations:'disabled'});}
async function settings(name){await nav('设置').click();await page.locator('.settings-page').waitFor();if(!(await page.locator('.settings-home-grid').count()))await page.keyboard.press('Escape');if(name)await page.getByRole('tab',{name,exact:true}).click();}
async function header(){const value=await page.locator('.topbar').evaluate(node=>{const s=node.querySelector('#tb-page-search'),a=node.querySelector('.topbar-actions');return {search:s.getBoundingClientRect().right,actions:a.getBoundingClientRect().left,inputs:s.querySelectorAll('input').length,placeholder:s.querySelector('input')?.getAttribute('placeholder'),height:node.getBoundingClientRect().height};});assert(value.search<=value.actions);assert(value.inputs<=1);assert(!value.placeholder);await checkOverflow();}
async function chrome(){
 assert.equal(await page.locator('.page-identity,.breadcrumb,.settings-breadcrumb').count(),0);
 const result=await page.evaluate(()=>{const rect=selector=>document.querySelector(selector).getBoundingClientRect(),footer=rect('.app-statusbar'),settings=rect('.sidebar-bottom .nav-item'),workspace=rect('.workspace-area'),bar=rect('.topbar');return {center:Math.abs(settings.y+settings.height/2-footer.y-footer.height/2),bar:bar.height,bottom:workspace.bottom-footer.top};});
 assert(result.center<=1,JSON.stringify(result));assert(result.bar<=58);assert.equal(result.bottom,0);await header();
}
async function radarNames(){
 const result=await page.locator('.knowledge-radar').evaluate(section=>{const labels=[...section.querySelectorAll('svg text')],nodes=[...section.querySelectorAll('.radar-node')],rows=[...section.querySelectorAll('.radar-detail-row>button')];return {names:labels.map(label=>label.textContent),rows:rows.map(row=>row.childNodes[0].textContent),overlaps:labels.map((label,index)=>{const a=label.getBoundingClientRect(),b=nodes[index].getBoundingClientRect();return a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top;})};});
 assert.deepEqual(result.names,result.rows);assert(result.overlaps.every(value=>!value),JSON.stringify(result));
}
try{
 await mkdir('tests/screenshots',{recursive:true});
 await page.goto('http://127.0.0.1:18831');await page.locator('.problem-table tr[data-id]').first().waitFor();
 assert.equal(await page.locator('.topbar-daily-ac').innerText(),'AC:82+2');
 assert.equal(await page.locator('.topbar-love-count svg').getAttribute('fill'),'currentColor');
 const settingsGeometry=()=>page.locator('.sidebar-bottom .nav-item').evaluate(node=>{const box=node.getBoundingClientRect(),label=node.querySelector('span').getBoundingClientRect();return {x:box.x,y:box.y,width:box.width,height:box.height,labelX:label.x,labelY:label.y};});
 const fixedSettings=await settingsGeometry();
 for(const sync of [{status:'syncing',pending:true},{status:'ready',pending:false},{status:'error',pending:true,error:'fixture'},{status:'ready',pending:false}]){await page.evaluate(value=>window.dispatchEvent(new CustomEvent('tb:sync-status',{detail:value})),sync);await page.waitForTimeout(20);assert.deepEqual(await settingsGeometry(),fixedSettings);}
 assert.equal((await page.locator('.brand-mark').innerText()).trim(),'TB');
 await page.getByRole('button',{name:'收起侧边栏',exact:true}).click();await page.waitForFunction(()=>document.querySelector('.sidebar').getBoundingClientRect().width<70);
 await page.getByRole('button',{name:'展开侧边栏',exact:true}).click();await chrome();
 assert.equal(await page.locator('.queue-heading').first().evaluate(node=>getComputedStyle(node.querySelector('td')).textAlign),'left');
 await page.evaluate(()=>document.documentElement.dataset.panelStyle='outlined');
 const edges=await page.locator('.problem-table tr[data-id]').first().evaluate(row=>[getComputedStyle(row.firstElementChild).borderTopWidth,getComputedStyle(row.firstElementChild).borderLeftWidth,getComputedStyle(row.lastElementChild).borderRightWidth]);assert.deepEqual(edges,['1px','1px','1px']);
 const archivedGoal=page.locator(`.problem-table tr[data-id="${rows[119].id}"]`);assert.equal(await archivedGoal.locator('.verdict').innerText(),'AC');assert.equal(await archivedGoal.locator('.remove-training').count(),0);
 await page.getByRole('button',{name:'每日任务',exact:true}).click();await page.getByRole('dialog',{name:'每日任务',exact:true}).waitFor();assert.equal(await page.locator('.daily-goal-tasks').count(),0);await page.keyboard.press('Escape');
 const status=await page.locator('.topbar').evaluate(node=>{const ac=node.querySelector('.topbar-daily-ac'),heart=node.querySelector('.topbar-love-count b'),flame=node.querySelector('.streak-flame');return {ac:getComputedStyle(ac).color,muted:getComputedStyle(node).getPropertyValue('--muted').trim(),size:parseFloat(getComputedStyle(heart).fontSize),flame:flame.getBoundingClientRect().height,animation:getComputedStyle(flame).animationName};});
 assert(status.size>=16);assert.equal(status.flame,20);assert.equal(status.animation,'none');
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
 assert.equal(await page.locator('.competition-page').evaluate(node=>getComputedStyle(node).backgroundColor),'rgba(0, 0, 0, 0)');
 await shot('competitions');
 await page.getByRole('button',{name:'比赛文件夹浏览',exact:true}).click();await page.locator('.catalog-explorer').waitFor();
 await page.locator('.catalog-folder-row').filter({hasText:'ACM'}).click();await page.locator('.catalog-folder-row').filter({hasText:'CCPC'}).click();await page.locator('.catalog-folder-row').filter({hasText:'2025年'}).click();
 await page.locator('.catalog-folder-row').filter({hasText:'CCPC 2025 郑州区域赛'}).click();
 assert.equal(await page.locator('.catalog-contest-entry').count(),2);
 await page.getByRole('button',{name:/查看 牛客 CCPC 2025 郑州区域赛（热身赛）/}).click();await page.getByLabel(/CCPC 2025 郑州区域赛（热身赛）比赛详情/).waitFor();
 await page.getByRole('button',{name:'全部比赛',exact:true}).click();await page.getByRole('button',{name:'全部平台',exact:true}).click();assert(await page.locator('.catalog-folder-row').count()>=2);
 await nav('模拟赛').click();await page.locator('.mock-history').waitFor();
 assert.equal(await page.getByRole('tab',{name:/模拟赛记录|创建训练/}).count(),0);
 assert.deepEqual(await page.locator('.mock-history .record-row strong').allTextContents(),['训练记录 3','训练记录 2','训练记录 1']);
 const mock=await page.evaluate(()=>{const setup=document.querySelector('.mock-config').getBoundingClientRect(),history=document.querySelector('.mock-history').getBoundingClientRect();return {bottom:setup.bottom,history:history.top,borders:[...document.querySelectorAll('.mock-mode-options>button')].map(node=>parseFloat(getComputedStyle(node).borderTopWidth))};});
 assert(mock.history>=mock.bottom&&mock.history-mock.bottom<=20);assert(mock.borders.every(width=>width>=1));await shot('mock');
 await page.locator('.mock-history .record-row').first().click();await page.locator('.record-detail').waitFor();await page.keyboard.press('Escape');await page.locator('.mock-history').waitFor();
 await nav('成长与能力').click();await page.getByLabel('一级知识雷达',{exact:true}).waitFor();await header();
 await radarNames();assert.equal(await page.getByRole('button',{name:'成就与称号',exact:true}).count(),0);assert.equal(await page.locator('.growth-account-hero #growth-goals').count(),1);
 await page.getByRole('button',{name:'新建目标',exact:true}).click();await page.getByRole('dialog',{name:'新建目标',exact:true}).waitFor();await page.getByRole('button',{name:'关闭目标设置',exact:true}).click();
 await page.getByLabel('账号成长统计',{exact:true}).waitFor();assert.equal(await page.getByText('下一步练什么',{exact:true}).count(),0);assert.equal(await page.getByText('今日同行',{exact:true}).count(),0);
 assert.equal(await page.locator('.radar-data-dot').count(),0);assert.equal(await page.locator('.radar-value').count(),0);
 await page.getByRole('button',{name:'数学与计数，掌握 ?%，进入二级雷达',exact:true}).click();await page.getByRole('button',{name:'素数，掌握 ?%，筛选题目',exact:true}).waitFor();await page.getByRole('button',{name:'取模与同余，掌握 ?%，筛选题目',exact:true}).waitFor();
 await radarNames();await page.keyboard.press('Escape');await page.getByRole('group',{name:'一级知识雷达',exact:true}).waitFor();await page.getByRole('button',{name:'字符串，掌握 ?%，进入二级雷达',exact:true}).click();await radarNames();
 await shot('growth');
 await page.getByRole('button',{name:'KMP，掌握 ?%，筛选题目',exact:true}).click();await page.getByRole('group',{name:'当前知识点筛选',exact:true}).waitFor();
 assert.equal(await page.locator('.problem-table tr[data-id]').count(),1);await page.getByLabel('搜索题目',{exact:true}).fill('列表定位');
 await page.getByRole('button',{name:'清除知识点筛选 KMP',exact:true}).click();assert.equal(await page.locator('.active-knowledge-filter').count(),0);assert.equal(await page.getByLabel('搜索题目',{exact:true}).inputValue(),'列表定位');assert(await page.locator('.problem-table tr[data-id]').count()>1);await shot('knowledge-filter-cleared');
 await nav('排行榜').click();await page.locator('.ranking-self').waitFor();
 const own=page.locator('.ranking-self');assert.equal(await own.locator('.like-burst').getAttribute('data-liked'),'true');assert.equal(await own.locator('.ranking-message').count(),0);assert.equal(await own.locator('.avatar-rank-frame').count(),1);
 assert(Math.abs((await own.locator('.like-burst').boundingBox()).x-(await page.locator('.ranking-table tbody tr').nth(1).locator('.like-burst').boundingBox()).x)<1,'own and other hearts align vertically');
 assert.equal(await page.getByRole('button',{name:'清空当前榜单',exact:true}).count(),0,'user edition hides management even when an old service returns isAdmin');assert.equal(await page.locator('.ranking-admin-cell').count(),0);
 const ranking=await own.evaluate(row=>{const bounds=selector=>row.querySelector(selector).getBoundingClientRect(),self=row.getBoundingClientRect(),identity=bounds('.ranking-identity'),place=bounds('.ranking-place'),count=bounds('.ranking-count'),social=bounds('.ranking-social-cell');return {left:identity.left-self.left,place:place.width,right:self.right-social.right,gap:social.left-count.right,social:social.width};});
 assert(ranking.left<65,JSON.stringify(ranking));assert.equal(ranking.gap,0);assert(ranking.social<=135);assert(ranking.right<=1);
 await page.locator('.social-activity').waitFor();assert.equal(await page.locator('.social-activity>div').count(),1);assert.equal(await page.locator('.social-activity').getByText('昨日用户').count(),0);
 await shot('rankings');await nav('题库').click();await nav('排行榜').click();assert.equal(await page.locator('.social-activity').count(),1);
 await page.evaluate(()=>window.__tbAdmin=true);await nav('题库').click();await nav('排行榜').click();await page.getByRole('button',{name:'清空当前榜单',exact:true}).waitFor();assert.equal(await page.locator('.ranking-admin-cell').count(),2);await page.evaluate(()=>window.__tbAdmin=false);
 await settings();for(const width of [1280,1600,2048]){await page.setViewportSize({width,height:1000});await chrome();const grid=await page.locator('.settings-home-grid').boundingBox();assert(grid.width>width*.7);assert(grid.height>700);}
 const sceneChecks=await page.locator('.settings-home-grid').evaluate(grid=>{
  const sample=(selector,time)=>{const node=grid.querySelector(selector),animation=node.getAnimations()[0];animation.pause();animation.currentTime=time;const box=node.getBoundingClientRect(),css=getComputedStyle(node);return {x:box.x,right:box.right,fill:Number(css.fillOpacity),opacity:Number(css.opacity),transform:css.transform};};
  const dino=grid.querySelector('.dino-traveler'),area=dino.closest('button').getBoundingClientRect(),start=sample('.dino-traveler',0),end=sample('.dino-traveler',9000),back=sample('.dino-traveler',18000);
  return {unique:new Set([...grid.querySelectorAll('.settings-scene')].map(node=>node.className.baseVal||node.className)).size,travel:end.x-start.x,returns:Math.abs(start.x-back.x),inside:start.x>=area.left&&end.right<=area.right,bulbDim:sample('.bulb-glass',0).fill,bulbLit:sample('.bulb-glass',3000).fill,balloon:sample('.balloon-flight',10000).opacity,buildings:new Set([...grid.querySelectorAll('.globe-building>path')].map(node=>node.getAttribute('d'))).size};
 });assert.equal(sceneChecks.unique,8);assert(sceneChecks.travel>400&&sceneChecks.returns<2&&sceneChecks.inside,JSON.stringify(sceneChecks));assert(sceneChecks.bulbLit>sceneChecks.bulbDim*3&&sceneChecks.bulbLit<.4);assert(sceneChecks.balloon>.8);assert.equal(sceneChecks.buildings,8);
 await shot('settings');await page.getByRole('tab',{name:'鸣谢',exact:true}).click();assert.equal(await page.locator('.acknowledgements p').count(),6);assert.equal(await page.locator('.acknowledgements').evaluate(node=>new Set([...node.querySelectorAll('p')].map(p=>getComputedStyle(p).color)).size),6);await shot('thanks');await page.getByRole('button',{name:'返回设置首页',exact:true}).click();await page.locator('.settings-home-grid').waitFor();
 await page.getByRole('tab',{name:'更新',exact:true}).click();assert.equal(await page.getByRole('button',{name:'查看更新通知',exact:true}).count(),0);await page.getByRole('button',{name:'返回设置首页',exact:true}).click();
 await page.getByRole('tab',{name:'翻译 API',exact:true}).click();await page.getByLabel('题面翻译配置',{exact:true}).waitFor();assert.notEqual(await page.locator('.settings-translation-panel').evaluate(node=>getComputedStyle(node).backgroundColor),'rgba(0, 0, 0, 0)');assert.equal(await page.locator('.translation-settings .progress-small').count(),0);await page.getByRole('button',{name:'题面翻译说明',exact:true}).focus();await page.getByRole('tooltip').filter({hasText:'只翻译公开题面'}).waitFor();await page.keyboard.press('Escape');await shot('translation');await page.getByRole('button',{name:'返回设置首页',exact:true}).click();
 await page.getByRole('tab',{name:'交互与导航',exact:true}).click();assert.equal(await page.locator('.navigation-editor-row').count(),10);assert.equal(await page.getByText('自定义顺序',{exact:true}).count(),0);await page.keyboard.press('Escape');
 await nav('从零讲').click();await page.locator('.lectures-layout').waitFor();await header();assert.equal(await page.locator('.workspace-area h2').filter({hasText:'从零讲'}).count(),0);
 assert.equal(await page.locator('.lectures-layout').evaluate(node=>getComputedStyle(node).backgroundColor),'rgba(0, 0, 0, 0)');assert.equal((await page.locator('.lecture-difficulty').first().innerText()).includes('≈'),false);await shot('lectures');
 await nav('提交记录').click();await page.locator('.submission-log-row').first().waitFor();assert.equal(await page.locator('.submission-log-row>svg').count(),0);assert.equal(await page.locator('.submission-runtime').count(),1);assert.equal(await page.locator('.submission-runtime').innerText(),'15 ms');
 await nav('题单').click();assert.equal(await page.getByText('算法题单',{exact:true}).count(),0);await nav('题库').click();
 await page.locator('.problem-table tr[data-id] .problem-title').first().click();await page.locator('.cm-editor').waitFor();
 assert.equal(await page.locator('.sidebar').isVisible(),false);assert.equal(await page.locator('.topbar').isVisible(),false);
 const box=await page.locator('.tb-workbench').boundingBox();assert.deepEqual({x:box.x,y:box.y,width:box.width,height:box.height},{x:0,y:0,width:2048,height:1000});
 assert.equal(await page.locator('.wb-editor-actions .wb-solution-button').count(),1);await shot('workbench');
 await page.locator('.cm-content').click();await page.keyboard.press('Escape');await page.locator('.problem-table').waitFor();assert.equal(await page.locator('.sidebar').isVisible(),true);
 await page.getByRole('button',{name:'消息通知',exact:true}).click();assert.equal(await page.getByText('题库与版本更新',{exact:true}).count(),0);await page.keyboard.press('Escape');
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
 await page.goto('http://127.0.0.1:18831/tests/ui-feedback-fixture.html?view=radar');await page.getByRole('button',{name:'字符串，掌握 ?%，进入二级雷达',exact:true}).waitFor();assert.equal(await page.locator('.radar-data-dot').count(),0);assert.equal(await page.locator('.radar-value').count(),0);await page.getByRole('button',{name:'字符串，掌握 ?%，进入二级雷达',exact:true}).click();await page.getByRole('button',{name:'KMP，掌握 54%，筛选题目',exact:true}).waitFor();await page.getByRole('button',{name:'字典树，掌握 ?%，筛选题目',exact:true}).waitFor();await shot('mastery');
 assert.deepEqual(errors,[]);console.log('PASS: compact chrome, logo toggle, left queue headings, AC colors and sizes, deep contest folders, inline sorted mock history, canonical radar labels, removable knowledge filters, compact rankings, goals in account panel, rounded lecture surfaces, clean submission rows, symmetric rank artwork and semantic achievement symbols; existing search, shortcuts, opacity, settings, practice and Escape checks passed.');
}catch(error){await shot('failure').catch(()=>{});throw error;}finally{await browser.close();await vite.close();}
