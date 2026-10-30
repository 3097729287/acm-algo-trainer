import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {chromium} from 'playwright';
import {createServer} from 'vite';
import {availablePages} from '../src/lib/navigationVisibility.js';
import {chooseMockValue} from './mock-mode-selection.mjs';

const vite=await createServer({server:{host:'127.0.0.1',port:0,watch:null},plugins:[{name:'platform-api-isolation',configureServer(server){server.middlewares.use((req,res,next)=>{if(!req.url?.startsWith('/api/'))return next();res.writeHead(410);res.end('Isolated platforms fixture');});}}]});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1440,height:960}});page.setDefaultTimeout(12000);
const now=new Date().toISOString(),owner='4c63fe3d-4b42-4f0f-a310-5de700689d79',unknown=[],errors=[],external=[],requests=[];
const platforms=['Codeforces','AtCoder','牛客','洛谷','QOJ','FutureJudge'];
const urls=['https://codeforces.com/contest/1/problem/A','https://atcoder.jp/contests/abc001/tasks/abc001_1','https://ac.nowcoder.com/acm/contest/1/A','https://www.luogu.com.cn/problem/P1001','https://qoj.ac/problem/18307','https://future.invalid/problem/1'];
const rows=platforms.map((platform,index)=>({id:platform+'::fixture',platform,url:urls[index],title:platform+' 真实来源夹具',problem:'A',contest:platform==='QOJ'?'ICPC 2026 山东省赛':platform+' 隔离比赛',series:platform==='QOJ'?'XCPC':platform,eventYear:2026,contestDate:now,contestProblemCount:1,catalogContentReady:true,statementAvailable:true,solutionAvailable:true,difficulty:1100,difficultySource:'人工复核（隔离夹具）',difficultyConfidence:'HIGH',tags:['输入输出']}));
const training=rows.map(row=>({id:row.id,activeAt:now,queue:'fill',accepted:false}));
const receipts=rows.map((row,index)=>({id:'receipt-'+index,problemId:row.id,canonicalProblemId:row.id,title:row.title,platform:row.platform,url:row.url,problem:row.problem,contestName:row.contest,submittedAt:now,verdict:'AC',scope:'official',mode:'submit',codePending:true}));
let preferences={theme:'dark',accent:'teal',fontSize:15,onboardingCompleted:true,onboardingGuideVersion:2,onboardingUnlockedPages:availablePages(11),levelNoticeVersion:1,levelNoticeSeen:100,levelNoticePending:0};
const workspace={now,training,sets:[],contests:[],activeContest:null,summary:{total:6,accepted:0,attempts:0,due:0,pending:0,todayAccepted:0}};
page.on('pageerror',error=>errors.push(error.message));
await page.route('**/api/**',async route=>{
 const request=route.request(),url=new URL(request.url());if(!url.pathname.startsWith('/api/'))return route.continue();const name=url.pathname.replace('/api/',''),body=request.method()==='POST'?request.postDataJSON():null;requests.push({name,query:Object.fromEntries(url.searchParams),body});let value;
 if(name==='account')value={required:true,authenticated:true,token:'platform-fixture',account:{userId:owner,loginId:'platform-fixture',nickname:'平台隔离账号'}};
 else if(name==='data')value={rows,categories:[{name:'输入输出',children:[]}],token:'platform-fixture',today:now.slice(0,10)};
 else if(name==='workspace')value=workspace;
 else if(name==='insights')value={summary:{totalSolved:0},growth:{level:11,confirmed:true,authority:{owner,epoch:'platform-fixture',revision:1},currentLevelXp:0,nextLevelXp:2200,totalXp:0},knowledge:[],recommendations:[],activity:[],assessment:{},dailyTasks:{tasks:[]}};
 else if(name==='preferences'){if(body)preferences=body.preferences;value={preferences,updatedAt:now};}
 else if(name==='training-lists')value={lists:[]};
 else if(name==='training-list-likes')value={likes:[]};
 else if(name==='templates')value={templates:[]};
 else if(name==='contest')value={contest:null};
 else if(name==='software-update')value={currentVersion:'1.4.31',status:'current',autoCheck:false,canInstall:false};
 else if(name==='content-update')value={status:'current',revision:0};
 else if(name==='contest-calendar')value={contests:[],providers:[],refreshing:false};
 else if(name==='social')value={available:false,notifications:[],likes:[],unread:0};
 else if(name==='goals')value={goals:[],contestPlan:{contests:[]}};
 else if(name==='inbox')value={pending:0,errors:[]};
 else if(name==='hub')value={settings:{accounts:{codeforces:'',atcoder:'',nowcoder:'',luogu:''}},accounts:[]};
 else if(name==='browser-preparation')value=body?{opened:true}:{available:true,mode:'external',preferredBrowser:'edge',platforms:platforms.slice(0,5).map(platform=>({platform,state:'unknown'})),browsers:[{id:'edge',available:true}]};
 else if(name==='desktop/fullscreen')value={available:false,fullscreen:false};
 else if(name==='usage')value={days:[],totalSeconds:0};
 else if(name==='profile')value={profile:{userId:owner,nickname:'平台隔离账号'}};
 else if(name==='submissions'){
  const selected=receipts.filter(row=>!url.searchParams.get('platform')||row.platform===url.searchParams.get('platform'));
  value={submissions:selected,total:selected.length,offset:0,limit:100};
 }
 else if(name==='contests/events')value={events:rows.map(row=>({name:row.contest,displayName:row.contest,platform:row.platform,series:row.series,eventYear:2026,count:1,expectedCount:1,duration:300}))};
 else if(name==='contests/preview'){
  assert.equal(request.headers()['x-tb-token'],'platform-fixture');const selected=rows.filter(row=>row.platform===body.platform);
  assert(selected.length,'The fixture receives a real selected source platform');
  value={plan:{previewId:'qoj-preview',slots:selected.map(row=>({id:row.id,title:row.title})),difficultyRange:{min:1100,max:1100}}};
 }else{unknown.push(name);value={};}
 await route.fulfill({json:value});
});
await page.route(/^https?:\/\/(?!127\.0\.0\.1)(?!localhost)/,route=>{external.push(route.request().url());return route.abort();});
const base=`http://127.0.0.1:${vite.httpServer.address().port}`,output='tests/screenshots/platforms',report={ok:false,actualApp:true,platforms,realOfficialSubmissions:0,geometry:[]};await mkdir(output,{recursive:true});
const nav=()=>page.getByRole('navigation',{name:'主导航'});
const choose=async(label,value)=>{await page.getByLabel(label,{exact:true}).click();await page.getByRole('listbox',{name:label,exact:true}).getByRole('option',{name:value,exact:true}).click();};
try{
 await page.goto(base);await page.waitForFunction(()=>document.querySelector('.profile-level-number')?.textContent==='11');
 for(const pageName of ['我的训练','题库']){
  await nav().getByRole('button',{name:pageName,exact:true}).click();await page.getByRole('button',{name:'筛选题目',exact:true}).click();
  assert.deepEqual(await page.getByLabel('题目平台',{exact:true}).locator('option').allTextContents(),['全部平台',...platforms]);
  for(const platform of platforms){
   await choose('题目平台',platform);
   await page.waitForFunction(platform=>{const nodes=[...document.querySelectorAll('.problem-title')];return nodes.length===1&&nodes[0].textContent.startsWith(platform);},platform);
   assert.equal(await page.locator('.platform-symbol').getAttribute('title'),platform);
   assert.equal(await page.locator('.platform-symbol').textContent(),platform==='QOJ'?'QJ':platform==='FutureJudge'?'Fu':platform==='Codeforces'?'CF':platform==='AtCoder'?'At':platform==='牛客'?'牛':'洛');
  }
  await choose('题目平台','QOJ');
  await page.getByLabel('筛选比赛分类',{exact:true}).click();
  const menu=page.getByRole('listbox',{name:'筛选比赛分类',exact:true});
  assert.equal(await menu.getByRole('option',{name:'QOJ',exact:true}).count(),0,'XCPC events have no hosting-platform category mirror');
  await menu.getByRole('option',{name:'XCPC',exact:true}).click();
  await menu.getByRole('option',{name:'选择「XCPC」',exact:true}).click();
  await page.waitForFunction(()=>document.querySelectorAll('.problem-title').length===1);
  assert.equal(await page.getByLabel('题目平台',{exact:true}).inputValue(),'QOJ','Selecting the event taxonomy preserves the independent source filter');
  await page.keyboard.press('Escape');await page.screenshot({path:`${output}/${pageName}-qoj.png`,animations:'disabled'});
 }
 await nav().getByRole('button',{name:'比赛',exact:true}).click();await page.getByRole('button',{name:'筛选比赛',exact:true}).click();await choose('比赛平台','QOJ');await page.keyboard.press('Escape');
 await page.waitForFunction(()=>document.querySelectorAll('.competition-card').length===1);assert(await page.getByRole('button',{name:/查看 QOJ ICPC 2026 山东省赛/}).count());
 await page.getByRole('button',{name:'比赛文件夹浏览',exact:true}).click();const explorer=page.getByRole('region',{name:'比赛层级浏览'});
 const qojFolder=explorer.getByRole('button',{name:/QOJ/}),xcpcFolder=explorer.getByRole('button',{name:/XCPC/});
 // Fitted pagination measures its first row in the next animation frame.
 // Observe the event folder after that measurement before asserting.
 await xcpcFolder.waitFor({state:'visible'});
 assert.equal(await qojFolder.count(),0,'XCPC events appear only under their platform-independent category');assert.equal(await xcpcFolder.count(),1);
 await xcpcFolder.click();const catalogPath=page.getByRole('navigation',{name:'题目浏览路径'});
 assert.equal(await catalogPath.getByRole('button',{name:'XCPC',exact:true}).count(),1);assert.equal(await catalogPath.getByRole('button',{name:'QOJ',exact:true}).count(),0);
 await nav().getByRole('button',{name:'提交记录',exact:true}).click();await page.getByLabel('提交平台',{exact:true}).click();await page.getByRole('listbox',{name:'提交平台',exact:true}).getByRole('option',{name:'QOJ',exact:true}).click();
 await page.waitForFunction(()=>document.querySelectorAll('.submission-log-row').length===1&&document.querySelector('.submission-platform')?.textContent==='QOJ');
 assert(requests.some(request=>request.name==='submissions'&&request.query.platform==='QOJ'&&request.query.offset==='0'));
 assert.match(await page.locator('.submission-problem-link').textContent(),/QOJ 真实来源夹具/);
 await nav().getByRole('button',{name:'模拟赛',exact:true}).click();await page.getByRole('button',{name:'训练筛选',exact:true}).click();await page.getByRole('button',{name:'QOJ',exact:true}).click();await page.getByRole('button',{name:'关闭筛选',exact:true}).click();
 await page.getByRole('button',{name:'生成试卷',exact:true}).click();await page.getByLabel('训练试卷预览',{exact:true}).waitFor();
 assert.equal(requests.filter(request=>request.name==='contests/preview').at(-1).body.platform,'QOJ');
 await chooseMockValue(page,'重现赛','ICPC 2026 山东省赛');await page.getByRole('button',{name:'生成试卷',exact:true}).click();
 assert.equal(requests.filter(request=>request.name==='contests/preview').at(-1).body.platform,'QOJ','Replaying an XCPC event preserves its independently selected hosting source');
 assert.equal(requests.filter(request=>request.name==='contests/preview').at(-1).body.contest,'ICPC 2026 山东省赛');
 assert.equal(requests.filter(request=>request.name==='contests/start').length,0);
 // Account source fields remain the four actually implemented public providers.
 await page.getByRole('button',{name:'训练概览',exact:true}).click();await page.getByRole('button',{name:'登录QOJ',exact:true}).waitFor();
 assert.equal(await page.getByLabel('QOJ公开账号',{exact:true}).count(),0);assert.equal(await page.getByRole('button',{name:'登录FutureJudge',exact:true}).count(),0);
 await page.getByRole('button',{name:'登录QOJ',exact:true}).click();assert(requests.some(request=>request.name==='browser-preparation'&&request.body?.platform==='QOJ'));
 for(const width of [1440,430]){await page.setViewportSize({width,height:960});const button=page.getByRole('button',{name:'登录QOJ',exact:true}),box=await button.boundingBox();assert(box.x>=0&&box.x+box.width<=width);report.geometry.push({width,qojLogin:box});}
 // The real Workbench must guard both the button and CodeMirror shortcuts.
 await page.setViewportSize({width:1440,height:960});await page.goto(base+'/tests/workbench-fixture.html');
 const editor=page.getByRole('textbox',{name:'C++ 代码'});await editor.waitFor();
 await page.evaluate(()=>{
  workbenchFixture.problemOverrides.U={platform:'FutureJudge',url:'https://future.invalid/problem/1'};
  workbenchFixture.problemOverrides.Q={platform:'QOJ',url:'https://qoj.ac/problem/18307'};
  workbenchFixture.problemOverrides.T={platform:'FutureJudge',url:'https://future.invalid/problem/template',templatePractice:true};
  workbenchFixture.changeProblem('U');
 });
 await page.waitForFunction(()=>document.querySelector('.wb-primary')?.disabled&&document.querySelector('.wb-primary')?.title==='暂不支持此平台原站提交');
 assert(await page.getByRole('button',{name:'提交',exact:true}).isDisabled());assert(await page.locator('.wb-statement').isVisible());
 await page.waitForFunction(()=>document.querySelector('.cm-content')?.getAttribute('contenteditable')==='true');
 await editor.press('Control+Enter');await page.waitForTimeout(150);
 assert.equal(await page.evaluate(()=>workbenchFixture.calls.filter(call=>call.path==='official/submit').length),0,'Unknown platform shortcuts never send an original-site request');
 await page.getByRole('button',{name:'运行样例',exact:true}).click();await page.waitForFunction(()=>workbenchFixture.calls.some(call=>call.path==='submissions'&&call.body.mode==='run'));
 await page.evaluate(()=>workbenchFixture.changeProblem('Q'));await page.waitForFunction(()=>document.querySelector('.wb-primary')?.disabled===false&&document.querySelector('.wb-primary')?.title==='原站提交 · Ctrl+Enter');
 await editor.press('Control+Enter');await page.waitForFunction(()=>workbenchFixture.calls.some(call=>call.path==='official/submit'&&call.body.id==='Q'));
 await page.getByRole('button',{name:'在浏览器查看',exact:true}).waitFor();await page.getByRole('button',{name:'在浏览器查看',exact:true}).click();
 await page.waitForFunction(()=>workbenchFixture.calls.some(call=>call.path==='official/open'&&call.body.id==='Q'));
 await page.evaluate(()=>workbenchFixture.changeProblem('T'));await page.waitForFunction(()=>document.querySelector('.wb-primary')?.disabled===false&&document.querySelector('.wb-primary')?.title==='模板评测 · Ctrl+Enter');
 await editor.press('Control+Enter');await page.waitForFunction(()=>workbenchFixture.calls.some(call=>call.path==='submissions'&&call.body.mode==='submit'&&call.body.id==='T'));
 assert.equal(await page.evaluate(()=>workbenchFixture.calls.filter(call=>call.path==='official/submit').length),1,'Template practice uses its local submit even for an unknown source');
 report.submitGuard={unknownButtonBlocked:true,unknownShortcutBlocked:true,unknownRunAvailable:true,qojShortcutAllowed:true,existingSessionOpenPreserved:true,templateLocalSubmitPreserved:true};
 assert.deepEqual(errors,[]);assert.deepEqual(unknown,[]);assert.deepEqual(external,[]);report.ok=true;
 console.log('PASS actual App: five supported + future display-only source filters/badges, QOJ and XCPC catalog axes, exact mock source/event, SQL-query parameter/record source, native-login-only account control; zero real OJ traffic');
}finally{await writeFile(output+'/report.json',JSON.stringify({...report,errors,unknown,external,requests},null,2));await browser.close();await vite.close();}
