import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
import {createServer} from 'vite';
import {chromium} from 'playwright';
import {availablePages} from '../src/lib/navigationVisibility.js';

// Actual App, LearningBrowser and Workbench. All API records are synthetic;
// neither the original site nor a normal ToBe account is contacted.
const frontend=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const out=resolve(frontend,'../.backups/review-completion-app',String(Date.now()));
await mkdir(out,{recursive:true});
const vite=await createServer({root:frontend,cacheDir:resolve(frontend,'../.backups/review-completion-vite'),optimizeDeps:{entries:['index.html']},server:{host:'127.0.0.1',port:0,watch:null},plugins:[{name:'review-offline-fixture',configureServer(server){server.middlewares.use((request,response,next)=>{if(!request.url?.startsWith('/api/'))return next();response.writeHead(410,{'Content-Type':'application/json'});response.end(JSON.stringify({error:'Fixture API must be intercepted'}));});}}]});
await vite.listen();
const origin=`http://127.0.0.1:${vite.httpServer.address().port}`;
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:960}});
page.setDefaultTimeout(12000);
const errors=[],unknown=[],writes=[],requests=[];
page.on('pageerror',error=>errors.push(error.message));
const owner='c3e5d799-502a-4b4f-a864-a342f7db419e',reviewId='a'.repeat(32),now=()=>new Date().toISOString();
const day=new Date().toLocaleDateString('sv-SE',{timeZone:'Asia/Shanghai'});
const row={id:'fixture::A',title:'Good times Good times',contest:'Isolated regression',problem:'A',platform:'Codeforces',url:'https://codeforces.com/contest/1016/problem/A',difficulty:1000,difficultySource:'Synthetic test rating',difficultyConfidence:'HIGH',difficultyEstimated:false,tags:['输入输出'],catalogContentReady:true,solutionAvailable:true};
let settled=false,raceOnStart=false,draft='',refreshes=0,settledAt=0;
let preferences={theme:'dark',accent:'teal',fontSize:15,onboardingGuideVersion:2,onboardingCompleted:true,onboardingUnlockedPages:availablePages(11),levelNoticeVersion:1,levelNoticeSeen:100,levelNoticePending:0,learningPaths:{navigationAccess:{version:3,retained:[]}}};
const reviewTask={id:reviewId,problemId:row.id,due:day,openedAt:null,stage:0,minutes:15};
const workspace=()=>({training:[{...row,active:true,accepted:true,verdict:'AC',lastSubmittedAt:now(),queue:settled?null:'review',...(!settled?{reviewTask}:{})}],sets:[],contests:[],activeContest:null,reviews:{tasks:settled?[]:[reviewTask],dueCount:settled?0:1,reviewOnly:false,newMinutes:60},summary:{total:1,accepted:1,attempts:settled?3:2,due:settled?0:1,pending:0,todayAccepted:settled?1:0},now:now()});
const summary=()=>({version:1,revision:settled?'settled':'pending',config:{goal:{kind:'xcpc',title:'Synthetic plan'},weekdayMinutes:60,weekendMinutes:60,restDays:[],team:false,role:''},plan:{id:'review-regression-plan',week:day,tasks:[{key:'review:A',kind:'review',id:row.id,title:row.title,date:day,status:settled?'done':'pending',reviewId,minutes:15,order:1},{key:'lecture:next',kind:'lecture',id:'fixture-next',title:'下一项：边界检查',date:day,status:'pending',minutes:15,order:2}],tracks:[],days:[],waiting:[],gaps:[]},proposal:null,article:[],topics:[],availableTopics:[],history:[],view:{},recommendation:{tracks:[]},effectiveSeconds:0});
const receipt=()=>({id:'synthetic-official-receipt',problemId:row.id,contestId:null,mode:'submit',scope:'official',verdict:'AC',code:draft,submittedAt:now(),finishedAt:now(),message:'Synthetic offline fixture',passed:0,total:0});
await page.route('**/*',async route=>{
 const url=new URL(route.request().url());
 if(url.origin!==origin&&!['data:','blob:'].includes(url.protocol))return route.abort('blockedbyclient');
 if(!url.pathname.startsWith('/api/'))return route.continue();
 const request=route.request(),path=url.pathname.slice(5),body=request.method()==='POST'?request.postDataJSON():null;
 requests.push({path,at:Date.now()});if(body)writes.push({path,body});
 let value;
 if(path==='account')value={required:true,authenticated:true,token:'fixture',account:{userId:owner,loginId:'fixture',nickname:'隔离回归'}};
 else if(path==='preferences'){if(body)preferences=body.preferences;value={preferences,updatedAt:now()};}
 else if(path==='data')value={rows:[row],categories:[],token:'fixture',today:day};
 else if(path==='workspace')value=workspace();
 else if(path==='workspace/ready')value={ready:true};
 else if(path==='navigation')value={level:11,confirmed:true,authority:{owner,epoch:'review-fixture',revision:1}};
 else if(path==='learning-summary')value=summary();
 else if(path==='learning-summary/refresh'){refreshes++;value=summary();}
 else if(path==='learning-summary/time')value={saved:true};
 else if(path==='duel')value={owner,status:'idle',match:null,ticket:null,serverNow:Date.now()};
 else if(path==='duel/board')value={owner,entries:[],records:[]};
 else if(path==='thought')value={owner,status:'idle',match:null};
 else if(path==='pk/v1/state')value={owner,enabled:false,status:'idle',lobby:null};
 else if(path==='team-training')value={owner,teams:[],invites:[]};
 else if(path==='team-training/state')value={owner,available:true,teams:[],invites:[],activeTeam:null,activeSession:null};
 else if(path==='stickers')value={owner,catalogue:[],units:[],boxes:[],grants:{},revision:0};
 else if(path==='insights')value={summary:{totalSolved:1},growth:{level:11,confirmed:true,authority:{owner,epoch:'review-fixture',revision:1},tier:'黑铁',currentLevelXp:0,nextLevelXp:200,totalXp:0},knowledge:[],recommendations:[],activity:[],assessment:{},dailyTasks:{tasks:[]}};
 else if(path==='software-update')value={currentVersion:'1.6.12',status:'current',autoCheck:false,canInstall:false};
 else if(path==='content-update')value={revision:0,status:'current'};
 else if(path==='contest-calendar')value={contests:[],providers:[],refreshing:false};
 else if(path==='browser-preparation')value={available:false};
 else if(path==='social')value={notifications:[],likes:[],unread:0};
 else if(path==='presence')value={owner,available:true,count:1,users:[]};
 else if(path==='goals')value={goals:[],contestPlan:{contests:[]}};
 else if(path==='daily-tasks')value={tasks:[]};
 else if(path==='inbox')value={pending:0,errors:[]};
 else if(path==='hub')value=null;
 else if(path==='desktop/fullscreen')value={available:false,fullscreen:false};
 else if(path==='usage')value={days:[],totalSeconds:0};
 else if(path==='training-lists')value={lists:[]};
 else if(path==='training-list-likes')value={likes:[]};
 else if(path==='templates')value={templates:[]};
 else if(path==='training/start'){
  if(raceOnStart){settled=true;settledAt=Date.now();}
  value=settled&&body.restoreReviewId?{reviewTask:null,reviewAlreadyCompleted:true}:{reviewTask,workspace:workspace()};
 }
 else if(path==='problem')value={...row,markdown:'# Isolated exercise\n\nRead two integers and output their sum.',samples:[{name:'Sample',input:'1 2\n',output:'3\n'}],limits:{timeMs:2000,memoryMb:256},judge:{scope:'samples',cases:1},locked:false,statementAvailable:true,draft,submissions:settled?[receipt()]:[]};
 else if(path==='draft'){draft=body.code;value={savedAt:now()};}
 else if(path==='official/submit')value={sessionId:'review-regression',status:'loading',platform:'Codeforces'};
 else if(path==='official/status'){settled=true;settledAt=Date.now();value={sessionId:'review-regression',status:'finished',platform:'Codeforces',verdict:'AC',submissionId:'100000001',submission:receipt(),workspace:workspace()};}
 else if(path==='official/ack'||path==='official/close')value={closed:true};
 else if(path==='submissions')value={submissions:settled?[receipt()]:[],groups:[],total:settled?1:0,hasMore:false};
 else if(path==='lecture')value={id:'fixture-next',title:'边界检查',concept:'边界检查',markdown:'## 边界检查\n\n保留既有阅读入口。',images:{}};
 else if(path==='lectures')value={lectures:[{id:'fixture-next',title:'边界检查',concept:'边界检查'}]};
 else if(path==='wiki')value={articles:[]};
 else {unknown.push(path);value={};}
 await route.fulfill({json:value});
});
await page.addInitScript(()=>localStorage.setItem('tb.preferences',JSON.stringify({onboardingGuideVersion:2,onboardingCompleted:true,theme:'dark'})));
const top=()=>page.locator('.topbar .next-actions-primary');
let result={ok:false,fullApp:true,syntheticApiFixture:true,liveOfficialSubmission:false,normalStateReadOrWritten:false};
try{
 await page.goto(origin);await top().getByText(row.title,{exact:true}).waitFor();
 assert(await page.locator('.app-statusbar').getByRole('button',{name:'卡包',exact:true}).isVisible());
 const initialRefreshes=refreshes;
 await top().click();await page.locator('.study-browser .cm-content[contenteditable=true]').waitFor();
 assert.equal(await page.locator('.study-browser .study-pack-button').count(),0,'The coding surface must not render a global pack dock');
 await page.locator('.study-browser .cm-content[contenteditable=true]').fill('int main(){return 0;}');
 await page.getByRole('button',{name:'提交',exact:true}).click();
 await top().getByText('下一项：边界检查',{exact:true}).waitFor({state:'attached',timeout:5000});
 const refreshLatency=Date.now()-settledAt;
 assert(settledAt&&refreshLatency<5000&&refreshes>initialRefreshes,'The official result must refresh the adopted plan immediately');
 await page.getByRole('button',{name:'返回主界面',exact:true}).click();
 await page.locator('.study-browser').waitFor({state:'hidden'});
 assert(await page.locator('.app-statusbar').getByRole('button',{name:'卡包',exact:true}).isVisible());
 await top().click();await page.locator('.study-browser .lectures-detail').waitFor();
 assert(await page.locator('.study-browser .study-pack-button').isVisible(),'Reading keeps its existing pack entrance');
 await page.getByRole('button',{name:'返回主界面',exact:true}).click();
 await page.locator('.study-browser').waitFor({state:'hidden'});
 // The AC arrives after the pending recommendation was painted but before
 // training/start receives its old reviewId. The API explicitly acknowledges
 // completion; App must refresh instead of entering the settled rewrite.
 await page.evaluate(async()=>{const pending=[];window.dispatchEvent(new CustomEvent('tb-before-update',{detail:{waitUntil:value=>pending.push(Promise.resolve(value))}}));await Promise.all(pending);});
 // The second scenario starts at the main page; browser restoration was
 // exercised above and is not the race under test here.
 preferences={...preferences,learningPaths:{...preferences.learningPaths,browserV1:{version:1,tabs:[],open:false}}};
 await page.evaluate(()=>localStorage.clear());
 settled=false;raceOnStart=true;draft='';await page.reload();
 await top().getByText(row.title,{exact:true}).waitFor();
 await top().click();await top().getByText('下一项：边界检查',{exact:true}).waitFor({timeout:5000});
 assert.equal(await page.locator('.study-browser:visible .cm-content').count(),0);
 assert.equal(await page.getByText('这次复习已经完成',{exact:true}).count(),0);
 assert(!writes.some(item=>item.path==='learning-summary/update'&&['complete','quiz','reflect'].includes(item.body.action)),'Refreshing or navigating must not settle learning records');
 assert.deepEqual(errors,[]);
 result={...result,ok:true,immediateSummaryRefreshMs:refreshLatency,completedReviewRaceAcknowledged:true,noDuplicateCompletionWrites:true,mainPackPresent:true,singleCodingPackAbsent:true,readingPackPreserved:true,errors,unknownApiPaths:[...new Set(unknown)]};
 await page.screenshot({path:resolve(out,'completed-race.png'),animations:'disabled'});
}catch(error){result={...result,errorClass:error.name,error:error.message,errors,unknownApiPaths:[...new Set(unknown)]};await page.screenshot({path:resolve(out,'failure.png'),animations:'disabled'});throw error;}
finally{await writeFile(resolve(out,'result.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({...result,receipt:resolve(out,'result.json')}));await browser.close();await vite.close();}
