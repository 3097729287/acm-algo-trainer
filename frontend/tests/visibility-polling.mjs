// Real App + AccountGate, controlled browser time, isolated public API fixtures.
// This verifies UI polling only. The backend heartbeat is an independent Python
// thread covered by test_account_sync.py; no real backend or account is used here.
import assert from 'node:assert/strict';
import { createServer } from 'vite';
import { chromium } from 'playwright';
import { mkdir, writeFile } from 'node:fs/promises';

process.env.TB_OFFLINE='1';
const server=await createServer({server:{host:'127.0.0.1',port:0,hmr:false}});
await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1480,height:1000}});
page.setDefaultTimeout(10000);
const origin=`http://127.0.0.1:${server.httpServer.address().port}`;
const errors=[],unexpected=[],writes=[],requests=[];
let inFlight=0,completed=false,authenticated=true;
const date='2026-10-16',now=`${date}T05:00:00.000Z`;
const row={id:'visibility-fixture::A',title:'后台回执练习',contest:'测试比赛',problem:'A',url:'https://example.com/A',platform:'Codeforces',difficulty:1200,tags:['模拟'],solutionAvailable:true};
const observed=['/api/account','/api/workspace','/api/inbox','/api/hub','/api/insights'];
const hiddenObserved=[...observed,'/api/goals'];
const counts=()=>Object.fromEntries(observed.map(path=>[path,requests.filter(item=>item.path===path).length]));
const hiddenCounts=()=>Object.fromEntries(hiddenObserved.map(path=>[path,requests.filter(item=>item.path===path).length]));
const settle=async()=>{
  for(let i=0;i<100&&inFlight;i++)await new Promise(resolve=>setTimeout(resolve,10));
  await new Promise(resolve=>setTimeout(resolve,30));
  await page.evaluate(()=>Promise.resolve());
};
page.on('pageerror',issue=>errors.push(issue.message));
await page.addInitScript(()=>{
  window.fixtureHidden=false;
  Object.defineProperty(document,'hidden',{configurable:true,get:()=>window.fixtureHidden});
  Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>window.fixtureHidden?'hidden':'visible'});
  window.setFixtureVisibility=hidden=>{window.fixtureHidden=hidden;document.dispatchEvent(new Event('visibilitychange'));};
  localStorage.setItem('tb.preferences',JSON.stringify({theme:'dark',accent:'teal'}));
});
await page.route('**/*',async route=>{
  const request=route.request(),url=new URL(request.url()),path=url.pathname;
  if(url.origin===origin&&!path.startsWith('/api/'))return route.continue();
  if(url.origin!==origin){unexpected.push(url.href);return route.abort();}
  inFlight++;
  requests.push({path,method:request.method()});
  if(request.method()!=='GET')writes.push({path,body:request.postData()});
  let value;
  if(path==='/api/account')value={required:false,authenticated,token:'fixture',account:null,sync:{status:completed?'ready':'syncing',pending:!completed},...(authenticated?{}:{error:'账号已在另一台电脑登录，请重新登录'})};
  else if(path==='/api/data')value={rows:[row],categories:[],token:'fixture',today:date};
  else if(path==='/api/workspace')value={training:[{id:row.id,activeAt:now,accepted:completed,verdict:completed?'AC':'PENDING',attempts:1,today:true,queue:completed?null:'pending'}],sets:[],contests:[],activeContest:null,summary:{total:1,accepted:completed?1:0,attempts:1,due:0,pending:completed?0:1,todayAccepted:completed?1:0},now};
  else if(path==='/api/insights')value={summary:{totalSolved:completed?1:0,officialSolved:completed?1:0,submissions:1},growth:{level:1,currentLevelXp:completed?25:0,nextLevelXp:100,totalXp:completed?25:0},achievements:[],knowledge:[],recommendations:[],activity:[],assessment:{},dailyTasks:{tasks:[]}};
  else if(path==='/api/hub')value={settings:{accounts:{}},accounts:[],sync:{busy:true,message:'后台公开同步'},notifications:[]};
  else if(path==='/api/inbox')value={pending:0,errors:[]};
  else if(path==='/api/goals')value={goals:[],contestPlan:{contests:[]}};
  else if(path==='/api/software-update')value={currentVersion:'1.1.0',status:'current',automatic:false,canInstall:false};
  else if(path==='/api/browser-preparation')value={available:false};
  else if(path==='/api/desktop/fullscreen')value={available:false,fullscreen:false};
  else if(path==='/api/usage'||path==='usage') value={days:[],totalSeconds:0,maxDailySeconds:0,maxDailyDate:null};
  else {unexpected.push(path);value={error:'Unexpected fixture API'};}
  try{await route.fulfill({json:value});}finally{inFlight--;}
});

const result={};
try{
  await page.clock.install({time:new Date(now)});
  await page.goto(origin);
  await page.getByRole('navigation',{name:'主导航',exact:true}).waitFor();
  await page.getByRole('button',{name:'今日 AC 0 题',exact:true}).waitFor();
  await settle();
  const visibleBefore=counts();
  await page.clock.runFor(6500);
  await settle();
  const visibleAfter=counts();
  for(const path of observed)assert.ok(visibleAfter[path]>visibleBefore[path],`${path} refreshes while visible`);
  result.visiblePolling=true;

  await page.evaluate(()=>window.setFixtureVisibility(true));
  await settle();
  const hiddenBefore=hiddenCounts();
  await page.clock.runFor(125000);
  await settle();
  assert.deepEqual(hiddenCounts(),hiddenBefore,'App background data, goals and AccountGate polling pause while hidden');
  result.hiddenPollingPaused=true;
  result.hiddenGoalsPollingPaused=true;
  // The server receives an official receipt independently of frontend polling.
  completed=true;
  await page.clock.runFor(12000);
  await settle();
  assert.deepEqual(hiddenCounts(),hiddenBefore,'a background result does not require UI polling');
  await page.evaluate(()=>window.setFixtureVisibility(false));
  await page.getByRole('button',{name:'今日 AC 1 题',exact:true}).waitFor();
  await page.getByLabel('账号数据已同步',{exact:true}).waitFor();
  await settle();
  const restored=counts();
  for(const path of observed)assert.ok(restored[path]>hiddenBefore[path],`${path} refreshes immediately on visibility restoration`);
  assert.ok(hiddenCounts()['/api/goals']>hiddenBefore['/api/goals'],'goals refresh immediately when visible');
  result.visibilityRestoresAccountAndPendingResult=true;

  await page.evaluate(()=>window.setFixtureVisibility(true));
  await settle();
  const beforeTakeover=hiddenCounts();
  // Represents a revocation already detected by the backend's independent
  // heartbeat. No pause/resume/logout command is sent by the frontend.
  authenticated=false;
  await page.clock.runFor(10000);
  await settle();
  assert.deepEqual(hiddenCounts(),beforeTakeover);
  await page.evaluate(()=>window.setFixtureVisibility(false));
  await page.getByRole('heading',{name:'登录 TB',exact:true}).waitFor();
  await page.getByText('账号已在另一台电脑登录，请重新登录',{exact:true}).waitFor();
  assert.equal(await page.getByRole('navigation',{name:'主导航',exact:true}).count(),0,'revoked account cannot keep the training workspace mounted');
  assert.deepEqual(writes,[],'hiding the UI sends no session/heartbeat mutation');
  assert.deepEqual(errors,[]);
  assert.deepEqual(unexpected,[]);
  Object.assign(result,{ok:true,backendRevocationObservedOnRestore:true,noSessionOrHeartbeatMutation:true,backendHeartbeatRuntime:'covered separately by Python account-sync tests',controlledBrowserElapsedMs:153500,realAccountsUsed:false});
  await mkdir('../.backups/v110-root',{recursive:true});
  await writeFile('../.backups/v110-root/visibility-polling.json',JSON.stringify({...result,counts:counts(),requestCounts:Object.fromEntries([...new Set(requests.map(item=>item.path))].map(path=>[path,requests.filter(item=>item.path===path).length]))},null,2));
  console.log(JSON.stringify(result));
}finally{await browser.close();await server.close();}
