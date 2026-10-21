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
const training=rows.map(row=>({id:row.id,activeAt:timestamp,lastActivityAt:timestamp,today:true,accepted:false,verdict:null,attempts:0}));
let preferences=null,likes={total:4,likedToday:false},failLike=true,boardDay=date,notifications=[{id:'33333333-3333-4333-8333-333333333333',kind:'comment',actor:other,recipient:self,text:'一起加油 <script>window.untrusted=true</script>',createdAt:timestamp,read:false}];
notifications.push(...Array.from({length:100},(_,index)=>({id:`55555555-5555-4555-8555-${String(index).padStart(12,'0')}`,kind:'like',actor:other,recipient:self,createdAt:timestamp,read:false})));
const workspace=()=>({training,sets:[],contests:[],activeContest:null,goals:{goals:[]},goalTasks:[],summary:{total:120,accepted:training.filter(row=>row.accepted).length,todayAccepted:2,beforeTodayAccepted:82,historicalAccepted:84,attempts:0,due:0,pending:0,streak:1},now:timestamp});
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
  else if(path==='/api/data')value={rows,categories:[{name:'数据结构',tags:['栈','单调栈'],children:[{name:'单调栈',tags:['单调栈']}]}],token:'fixture',today:date,revision:'ui-social'};
  else if(path==='/api/workspace')value=workspace();
  else if(path==='/api/hub')value=hub;
  else if(path==='/api/insights')value={summary:{officialSolved:0,submissions:0,activeDays:1,streak:1},growth:{...progress,totalXp:6265,currentLevelXp:665,nextLevelXp:1600,ranked},knowledge:[],achievements:[],activity:[],recommendations:[],assessment:{platforms:[]},dailyTasks:{tasks:[]}};
  else if(path==='/api/profile')value={profile:self,leaderboard:{configured:true,status:'ready'}};
  else if(path==='/api/goals')value={goals:[]};
  else if(path==='/api/contests/events')value={events:[]};
  else if(path==='/api/submissions')value={submissions:[],total:0,hasMore:false};
  else if(path==='/api/lectures')value={lectures:[{id:'lesson',title:'二分查找',category:'基础技巧',tags:['二分']} ]};
  else if(path==='/api/desktop/fullscreen')value={available:false,fullscreen:false};
  else if(path==='/api/training/start')value={workspace:workspace()};
  else if(path==='/api/problem')value={id:url.searchParams.get('id'),title:rows.find(row=>row.id===url.searchParams.get('id')).title,markdown:'## 题目描述\n\n测试题面。\n\n## 样例\n\n```text\n1 2\n```',samples:[{input:'1\n',output:'2\n'}],limits:{timeMs:2000,memoryMb:256},judge:{scope:'samples',cases:1},statementAvailable:true,draft:'int main() { return 0; }',submissions:[]};
  else if(path==='/api/draft')value={savedAt:timestamp};
  else if(path==='/api/translation/settings')value={provider:'custom',providerName:'自定义',model:'fixture',configured:false,keyStored:false,providers:[]};
  else if(path==='/api/leaderboard')value={period:url.searchParams.get('period')||'daily',date:boardDay,configured:true,status:'ready',hasSnapshot:true,socialAvailable:true,socialProtocol:1,isAdmin:false,entries:[{...self,rank:1,count:2,likes:{total:9,likedToday:false},publicProgress:progress},{...other,rank:2,count:1,likes,publicProgress:progress}],self};
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
async function settings(name){await nav('设置').click();if(await page.locator('.settings-breadcrumb').count())await page.keyboard.press('Escape');if(name)await page.getByRole('tab',{name,exact:true}).click();}
async function header(){const value=await page.locator('.topbar').evaluate(node=>{const s=node.querySelector('#tb-page-search'),a=node.querySelector('.topbar-actions');return {search:s.getBoundingClientRect().right,actions:a.getBoundingClientRect().left,inputs:s.querySelectorAll('input').length,placeholder:s.querySelector('input')?.getAttribute('placeholder'),height:node.getBoundingClientRect().height};});assert(value.search<=value.actions);assert(value.inputs<=1);assert(!value.placeholder);await checkOverflow();}
try{
 await mkdir('tests/screenshots',{recursive:true});
 await page.goto('http://127.0.0.1:18831');await page.locator('.problem-table tr[data-id]').first().waitFor();
 assert.equal(await page.locator('.topbar-daily-ac').innerText(),'AC:82+2');
 assert.equal(await page.locator('.footer-hint').count(),0);
 await header();
 await page.getByRole('button',{name:'筛选题目',exact:true}).click();
 const sort=page.getByRole('combobox',{name:'排序方式',exact:true});assert.equal(await sort.inputValue(),'contestDate');
 await sort.click();await page.getByRole('listbox',{name:'排序方式'}).getByRole('option',{name:'难度',exact:true}).click();
 assert.equal(await sort.inputValue(),'difficulty');assert.equal(await page.locator('.filter-popover').count(),1);
 await page.keyboard.press('Escape');await page.locator('.filter-popover').waitFor({state:'hidden'});
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
 assert.equal(await page.getByLabel('比赛文件夹浏览',{exact:true}).count(),0);
 await page.getByRole('button',{name:'筛选比赛',exact:true}).click();await page.getByLabel('比赛文件夹浏览',{exact:true}).check();await page.keyboard.press('Escape');await page.locator('.catalog-explorer').waitFor();
 await nav('成长与能力').click();await page.getByLabel('一级知识雷达',{exact:true}).waitFor();await header();
 await page.getByLabel('账号成长统计',{exact:true}).waitFor();assert.equal(await page.getByText('下一步练什么',{exact:true}).count(),0);assert.equal(await page.getByText('今日同行',{exact:true}).count(),0);
 await page.getByRole('button',{name:'数学，掌握 0%，进入二级雷达',exact:true}).click();await page.getByRole('button',{name:'素数筛，掌握 0%，筛选题目',exact:true}).waitFor();await page.getByRole('button',{name:'取模与同余，掌握 0%，筛选题目',exact:true}).waitFor();
 await shot('growth');
 await nav('排行榜').click();await page.locator('.ranking-self').waitFor();
 const own=page.locator('.ranking-self');assert.equal(await own.locator('.like-burst').getAttribute('data-liked'),'true');assert.equal(await own.locator('.ranking-message').count(),0);assert.equal(await own.locator('.avatar-rank-frame').count(),1);
 await page.locator('.social-activity').waitFor();assert.equal(await page.locator('.social-activity>div').count(),1);assert.equal(await page.locator('.social-activity').getByText('昨日用户').count(),0);
 await shot('rankings');await nav('题库').click();await nav('排行榜').click();assert.equal(await page.locator('.social-activity').count(),1);
 await settings();for(const width of [1280,1600,2048]){await page.setViewportSize({width,height:1000});await checkOverflow();const grid=await page.locator('.settings-home-grid').boundingBox();assert(grid.width>width*.7);assert(grid.height>700);}
 await shot('settings');await page.getByRole('tab',{name:'鸣谢',exact:true}).click();assert.equal(await page.locator('.acknowledgements p').count(),5);await shot('thanks');await page.keyboard.press('Escape');
 await page.getByRole('tab',{name:'交互与导航',exact:true}).click();assert.equal(await page.locator('.navigation-editor-row').count(),10);assert.equal(await page.getByText('自定义顺序',{exact:true}).count(),0);await page.keyboard.press('Escape');
 await nav('从零讲').click();await page.locator('.lectures-layout').waitFor();await header();assert.equal(await page.locator('.workspace-area h2').filter({hasText:'从零讲'}).count(),0);
 await nav('题单').click();assert.equal(await page.getByText('算法题单',{exact:true}).count(),0);await nav('题库').click();
 await page.locator('.problem-table tr[data-id] .problem-title').first().click();await page.locator('.cm-editor').waitFor();
 assert.equal(await page.locator('.sidebar').isVisible(),false);assert.equal(await page.locator('.topbar').isVisible(),false);
 const box=await page.locator('.tb-workbench').boundingBox();assert.deepEqual({x:box.x,y:box.y,width:box.width,height:box.height},{x:0,y:0,width:2048,height:1000});
 assert.equal(await page.locator('.wb-editor-actions .wb-solution-button').count(),1);await shot('workbench');
 await page.locator('.cm-content').click();await page.keyboard.press('Escape');await page.locator('.problem-table').waitFor();assert.equal(await page.locator('.sidebar').isVisible(),true);
 await page.getByRole('button',{name:'消息通知',exact:true}).click();assert.equal(await page.getByText('题库与版本更新',{exact:true}).count(),0);await page.keyboard.press('Escape');
 assert.deepEqual(errors,[]);console.log('PASS: v1.3.1 header search, filter popup selection, AC baseline, editable shortcuts, opacity 0/50/100, radar, rankings daily feed, settings, full-screen practice and Escape');
}catch(error){await shot('failure').catch(()=>{});throw error;}finally{await browser.close();await vite.close();}
