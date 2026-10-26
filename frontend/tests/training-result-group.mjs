import fs from 'node:fs';
import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { createServer } from 'vite';
import { chromium } from 'playwright';

const vite=await createServer({server:{host:'127.0.0.1',port:0,fs:{allow:[process.cwd(),fs.realpathSync('node_modules')]}}});
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
const workspace=()=>({training,sets:[],contests:[],activeContest:null,goals:{goals:[]},goalTasks:[],summary:{total:120,accepted:training.filter(row=>row.accepted).length,todayAccepted:0,attempts:0,due:0,pending:0,streak:1},now:timestamp});
const progress={badge:'tier-7',level:8,tier:'大师',rankTier:'大师',rankScore:2000,titles:[]};
const ranked={badge:'tier-7',tier:'大师',qualified:true,abilityScore:2000,nextAbilityScore:2100,evidenceCount:8,minimumEvidence:5,levelGate:5};
ranked.tierRequirements=['黑铁','青铜','白银','黄金','翡翠','钻石','大师','宗师','王者'].map((tier,index)=>({tier,badge:`tier-${index}`,minAbilityScore:[0,800,1000,1200,1600,1800,2000,2100,2200][index]}));
const hub={settings:{githubRepo:'3097729287/acm-algo-trainer',accounts:{},autoSync:false,intervalHours:6,minDifficulty:0,maxDifficulty:2199},sync:{busy:false},updates:{currentVersion:'1.1.5'},accounts:[],notifications:[]};
await page.addInitScript(()=>localStorage.setItem('tb.preferences',JSON.stringify({theme:'dark',accent:'teal',backdrop:'aurora',panelOpacity:35,widgets:true,fontSize:16,navOrder:['mine','library','competitions','mock','rankings','growth','records','activity','lectures'],views:[],onboardingCompleted:true})));
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
  else if(path==='/api/data')value={rows,categories:[],token:'fixture',today:date,revision:'ui-social'};
  else if(path==='/api/workspace')value=workspace();
  else if(path==='/api/hub')value=hub;
  else if(path==='/api/insights')value={summary:{officialSolved:0,submissions:0,activeDays:1,streak:1},growth:{...progress,totalXp:6265,currentLevelXp:665,nextLevelXp:1600,ranked},knowledge:[],achievements:[],activity:[],recommendations:[],assessment:{platforms:[]},dailyTasks:{tasks:[]}};
  else if(path==='/api/profile')value={profile:self,leaderboard:{configured:true,status:'ready'}};
  else if(path==='/api/goals')value={goals:[]};
  else if(path==='/api/contest-calendar')value={contests:[],providers:[]};
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
  else if(path==='/api/social/comments')value={created:true,id:body.requestId};
  else if(path==='/api/social/read'){notifications=notifications.map(row=>body.all===true||body.ids?.includes(row.id)?{...row,read:true}:row);value={ok:true};}
  else {await route.fulfill({status:404,json:{error:'fixture missing '+path}});return;}
  await route.fulfill({json:value});
});
try {
  training[0].queue='fill';training[0].verdict='WA';
  await page.goto(vite.resolvedUrls.local[0]);
  const row=page.locator('tr[data-id="fixture::0"]');await row.waitFor();
  const group=()=>row.evaluate(node=>{while(node=node.previousElementSibling){if(node.classList.contains('queue-heading'))return node.textContent;}return '';});
  assert.match(await group(),/待攻克/);
  assert.equal(await page.locator('.topbar-love-count b').textContent(),'6+3');
  await row.locator('.problem-title').click();await page.locator('.cm-editor').waitFor();
  training[0].accepted=true;training[0].verdict='AC';training[0].queue=null;
  await page.getByRole('button',{name:'返回列表',exact:true}).click();
  await row.waitFor();
  await page.waitForFunction(()=>{let node=document.querySelector('tr[data-id="fixture::0"]');while(node=node?.previousElementSibling){if(node.classList.contains('queue-heading'))return node.textContent.includes('已 AC');}return false;});
  assert.match(await group(),/已 AC/);
  assert.equal(await page.locator('.queue-heading').filter({hasText:'待攻克'}).count(),0);
  assert.deepEqual(errors,[]);
  console.log('PASS actual App: official AC replaces the frozen failure group; topbar hearts show history + today.');
} finally {await browser.close();await vite.close();}
