import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {chromium} from 'playwright';
import {createServer} from 'vite';
import {availablePages} from '../src/lib/navigationVisibility.js';

const vite=await createServer({server:{host:'127.0.0.1',port:0,watch:null},plugins:[{name:'isolated-navigation-api',configureServer(server){server.middlewares.use((request,response,next)=>{if(!request.url?.startsWith('/api/'))return next();response.writeHead(410,{'Content-Type':'application/json'});response.end(JSON.stringify({error:'Isolated navigation fixture; live API disabled'}));});}}]});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:960}});page.setDefaultTimeout(12000);
const errors=[],unknown=[];page.on('pageerror',error=>errors.push(error.message));
await page.addInitScript(()=>{window.__tbNewAccount=new URL(location.href).searchParams.get('newAccount')==='1';});
let owner='c3e5d799-502a-4b4f-a864-a342f7db419e';const now=new Date().toISOString();
let held=false,resume=[];let level=12,revision=0,draft='',sampleRequested=false,officialRequested=false,preferences={theme:'dark',accent:'teal',fontSize:15,onboardingGuideVersion:2,onboardingCompleted:true,onboardingUnlockedPages:availablePages(11),levelNoticeVersion:1,levelNoticeSeen:100,levelNoticePending:0};
preferences.navOrder=['training-lists'];
let events=[],calendarReads=0,catalogReads=0,holdCatalog=false,releaseCatalog;
const calendarState=()=>({contests:structuredClone(events),imports:events.map(e=>e.import).filter(Boolean),providers:[],refreshing:false,importing:false});
let preferenceSaveFailures=0,preferenceSaveAttempts=0;
const rows=Array.from({length:20},(_,i)=>({id:'fixture::'+i,title:'完整练习 '+i,contest:'1024数学专场考核',problem:String.fromCharCode(65+i),platform:'牛客',series:'牛客',url:'https://ac.nowcoder.com/acm/contest/142622/'+String.fromCharCode(65+i),difficulty:1000,difficultySource:'fixture',difficultyConfidence:'HIGH',tags:[i<10?'枚举':'素数'],contestProblemCount:20,catalogContentReady:true,solutionAvailable:true}));
for(const prefix of ['ICPC','CCPC'])rows.push({id:prefix,contest:prefix+' 2026 中国区域赛',title:prefix+'练习',problem:'A',platform:'Codeforces',series:'XCPC',url:'https://codeforces.com/gym/'+(prefix==='ICPC'?'101':'102')+'/problem/A',difficulty:2000,tags:['树'],contestProblemCount:1,catalogContentReady:true});
const lists=[{id:'fixture-basic',title:'顺序结构',available:true,categories:[],problems:rows.map(row=>({problemId:row.id,url:row.url}))}];
const workspace={training:[],sets:[],contests:[],activeContest:null,summary:{total:0,accepted:0,attempts:0,due:0,pending:0,todayAccepted:0},now};
await page.route('**/api/**',async route=>{
 const url=new URL(route.request().url());if(!url.pathname.startsWith('/api/'))return route.continue();const path=url.pathname.replace('/api/','');let value;
 if(path==='account')value={required:true,authenticated:true,token:'fixture',account:{userId:owner,loginId:'fixture',nickname:'测试学习者'}};
 else if(path==='preferences'){if(route.request().method()==='POST'){preferenceSaveAttempts++;if(preferenceSaveFailures>0){preferenceSaveFailures--;await route.fulfill({status:503,json:{error:'隔离偏好保存失败'}});return;}preferences=route.request().postDataJSON().preferences;}value={preferences,updatedAt:now};}
 else if(path==='data'){catalogReads++;const payload={rows:structuredClone(rows),categories:[],token:'fixture',today:now.slice(0,10)};if(url.searchParams.has('calendar')&&holdCatalog){holdCatalog=false;await new Promise(resolve=>{releaseCatalog=resolve;});}value=payload;}
 else if(path==='workspace')value={...workspace,now:new Date().toISOString()};
 else if(path==='insights'){if(held)await new Promise(resolve=>resume.push(resolve));value={summary:{totalSolved:0},growth:{level,confirmed:true,authority:{owner,epoch:'navigation-fixture',revision:++revision},tier:'黑铁',currentLevelXp:0,nextLevelXp:200,totalXp:0},equippedTitles:[{id:'ac-2000',name:'双千传奇',category:'ac',target:2000},{id:'streak-730',name:'双年不辍',category:'streak',target:730}],knowledge:[],recommendations:[],activity:[],assessment:{},dailyTasks:{tasks:[]}};}
 else if(path==='software-update')value={currentVersion:'1.4.29',status:'current',autoCheck:false,canInstall:false};
 else if(path==='content-update')value={revision:0,status:'current'};
 else if(path==='contest-calendar'){calendarReads++;value=calendarState();}
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
 else if(path==='problem')value={...rows.find(row=>row.id===url.searchParams.get('id')),id:url.searchParams.get('id'),markdown:'# Maximize the Score\n\nRead two integers and print their sum.',samples:[{name:'样例 1',input:'1 2\n',output:'3\n'}],limits:{timeMs:2000,memoryMb:256},judge:{scope:'samples',cases:1},locked:false,statementAvailable:true,draft,submissions:[]};
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

const base=`http://127.0.0.1:${vite.httpServer.address().port}`;
const nav=()=>page.getByRole('navigation',{name:'主导航'});
const modal=()=>page.getByRole('dialog',{name:'比赛日历',exact:true});
const detail=()=>page.locator('.competition-detail');
const calendarButton=()=>page.getByRole('button',{name:'比赛日历',exact:true});
async function openCalendar(){await calendarButton().click();await modal().waitFor();}
async function closeCalendar(){await modal().getByRole('button',{name:'关闭',exact:true}).click();await modal().waitFor({state:'detached'});}
const event=(id,title,start)=>({id:'nowcoder:'+id,title,platform:'nowcoder',url:'https://ac.nowcoder.com/acm/contest/'+id,startAt:new Date(start).toISOString(),endAt:new Date(start+7200000).toISOString()});
function publish(e){
 for(let i=0;i<6;i++)rows.push({id:`remote:${e.id}::${String.fromCharCode(65+i)}`,title:e.title+'题'+i,contest:e.title,problem:String.fromCharCode(65+i),platform:'牛客',series:'牛客',url:e.url+'/'+String.fromCharCode(65+i),difficulty:1000,tags:['前缀和'],contestProblemCount:6,catalogContentReady:true});
 e.import={id:e.id,status:'ready',ready:6,total:6,catalogRevision:e.id+'-complete'};
}
try{
 const future=event('141882','小白月赛 139',Date.now()+180000);events=[future];
 await page.goto(base);await nav().getByRole('button',{name:'比赛',exact:true}).waitFor();
 const reminder=page.getByRole('dialog',{name:'比赛即将开始',exact:true});await reminder.waitFor();assert.match(await reminder.innerText(),/小白月赛 139/);await reminder.getByRole('button',{name:'关闭',exact:true}).click();
 await nav().getByRole('button',{name:'比赛',exact:true}).click();
 await page.getByRole('button',{name:'查看 牛客 1024数学专场考核，20 道题',exact:true}).click();
 await page.getByRole('button',{name:'练习 A 完整练习 0',exact:true}).click();await page.locator('.cm-content').waitFor();
 const code='// calendar import must keep this draft\nint main() { return 0; }';await page.locator('.cm-content').fill(code);
 // A publication arrives from the background calendar poll while the editor is open.
 const oldReads=catalogReads;future.startAt=new Date(Date.parse(now)-60000).toISOString();publish(future);
 await page.evaluate(()=>window.dispatchEvent(new Event('focus')));
 await page.waitForFunction(()=>document.querySelector('.cm-content')?.textContent.includes('calendar import'));
 for(let n=0;n<80&&catalogReads===oldReads;n++)await page.waitForTimeout(25);
 assert(catalogReads>oldReads,'ready imports invalidate the already loaded public catalogue');
 assert.equal(await page.locator('.cm-content').innerText(),code);assert.equal(await detail().count(),0,'automatic publication does not leave the active editor');
 const back=page.getByRole('button',{name:'返回列表',exact:true});await back.click();await detail().waitFor();assert.equal(draft,code);assert.equal(await detail().locator('h2').innerText(),'1024数学专场考核');
 await openCalendar();await modal().getByRole('button',{name:'在TB打开比赛 小白月赛 139',exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('.competition-detail h2')?.textContent==='小白月赛 139');
 assert.equal(await detail().locator('.competition-question').count(),6,'same-page calendar entry selects newly imported contest');
 await page.getByRole('button',{name:'练习 A 小白月赛 139题0',exact:true}).click();await page.locator('.cm-content').waitFor();assert.equal(await page.locator('.wb-pane-title').count()>0||await page.locator('.tb-workbench').count()>0,true);await page.getByRole('button',{name:'返回列表',exact:true}).click();
 // A slow read for event A cannot win after a later explicit event B.
 const another=event('141883','晚场比赛 B',Date.parse(now)-120000);publish(another);events.push(another);
 await openCalendar();await modal().getByRole('button',{name:'刷新赛程',exact:true}).click();await modal().getByRole('button',{name:'在TB打开比赛 晚场比赛 B',exact:true}).waitFor();
 await page.waitForTimeout(100);holdCatalog=true;
 await modal().getByRole('button',{name:'在TB打开比赛 小白月赛 139',exact:true}).click();
 for(let n=0;n<80&&!releaseCatalog;n++)await page.waitForTimeout(25);assert(releaseCatalog);
 await modal().getByRole('button',{name:'在TB打开比赛 晚场比赛 B',exact:true}).click();await page.waitForFunction(()=>document.querySelector('.competition-detail h2')?.textContent==='晚场比赛 B');releaseCatalog();releaseCatalog=null;await page.waitForTimeout(100);
 assert.equal(await detail().locator('h2').innerText(),'晚场比赛 B','late A cannot override B navigation');
 // Closing the calendar invalidates a pending open before its data response arrives.
 await openCalendar();holdCatalog=true;await modal().getByRole('button',{name:'在TB打开比赛 小白月赛 139',exact:true}).click();
 for(let n=0;n<80&&!releaseCatalog;n++)await page.waitForTimeout(25);assert(releaseCatalog);await closeCalendar();await nav().getByRole('button',{name:'题库',exact:true}).click();releaseCatalog();releaseCatalog=null;await page.waitForTimeout(100);
 await page.locator('.workspace-area[data-page="library"]').waitFor();assert.equal(await detail().count(),0,'closed calendar does not navigate after a late response');
 assert.deepEqual(errors,[]);assert.deepEqual(unknown,[]);assert.equal(officialRequested,false);assert.equal(sampleRequested,false);
 console.log('Calendar full App: reminder, loaded-catalogue update, active editor/draft preserved, same-page contest and problem open, B over late A, close cancellation passed.');
}catch(error){console.error(JSON.stringify({errors,unknown,body:(await page.locator('body').innerText()).slice(0,2400)}));throw error;}finally{releaseCatalog?.();for(const done of resume)done();await browser.close();await vite.close();}
