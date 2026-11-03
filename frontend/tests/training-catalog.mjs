import assert from 'node:assert/strict';
import fs from 'node:fs';
import {chromium} from 'playwright';
import {createServer} from 'vite';
import {availablePages} from '../src/lib/navigationVisibility.js';

const lists=JSON.parse(fs.readFileSync('../data/library/training_lists.json','utf8'));
const rows=JSON.parse(fs.readFileSync('../data/library/problems.json','utf8')).map(row=>row.encoded);
const output='../.backups/interaction-1433/catalog-visuals';fs.mkdirSync(output,{recursive:true});
const vite=await createServer({server:{host:'127.0.0.1',port:0}});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:900}});page.setDefaultTimeout(15000);
const errors=[],writes=[],now=new Date().toISOString(),owner='b4cce6cd-0452-48aa-a8c1-2c90cc02be4a';
page.on('pageerror',error=>errors.push(error.message));
let requests=0,preferences={theme:'light',fontSize:15,onboardingGuideVersion:2,onboardingCompleted:true,onboardingUnlockedPages:availablePages(50),levelNoticeVersion:1,levelNoticeSeen:100};
let savedResolve;const saved=new Promise(resolve=>{savedResolve=resolve;});
await page.route('**/api/**',async route=>{
 const request=route.request(),url=new URL(request.url()),name=url.pathname.replace('/api/','');let value;
 if(!url.pathname.startsWith('/api/'))return route.continue();
 if(request.method()==='POST'&&name==='workspace/ready')return route.fulfill({json:{ready:true}});
 if(request.method()==='POST'){
  writes.push(name);assert.equal(name,'preferences','Browsing only saves interface location');
  preferences=request.postDataJSON().preferences;
  if(preferences.trainingListLocation?.state?.trail?.includes('curriculum:0'))savedResolve();
 }
 if(name==='account')value={required:true,authenticated:true,token:'fixture',account:{userId:owner,loginId:'catalog_fixture',nickname:'目录测试'}};
 else if(name==='preferences')value={preferences,updatedAt:now};
 else if(name==='data')value={rows,categories:[],token:'fixture',revision:'full-catalog-1433',today:now.slice(0,10)};
 else if(name==='workspace')value={training:[],sets:[],contests:[],activeContest:null,goalTasks:[],summary:{},now};
 else if(name==='hub')value={settings:{accounts:{}},accounts:[],sync:{},updates:{},notifications:[]};
 else if(name==='duel'||name==='pk/v1/state')value={owner,available:false,enabled:false,status:'idle',match:null};
 else if(name==='social')value={available:false,notifications:[],totalLikes:0,unreadCount:0,likes:[]};
 else if(name==='profile')value={profile:{userId:owner,nickname:'目录测试'}};
 else if(name==='insights'||name==='navigation')value={summary:{},growth:{level:11,confirmed:true,authority:{owner,epoch:'full-catalog-fixture',revision:1},currentLevelXp:745,nextLevelXp:2200,totalXp:11745},knowledge:[],achievements:[],activity:[],assessment:{platforms:[]},dailyTasks:{tasks:[]}};
 else if(name==='training-lists'){requests++;value={lists};}
 else if(name==='contest-calendar')value={contests:[],refreshing:false,importing:false};
 else if(name==='content-update')value={revision:0,status:'current',error:''};
 else if(name==='software-update')value={currentVersion:'1.4.33',status:'current',autoCheck:false,canInstall:false};
 else if(name==='desktop/fullscreen')value={available:false,fullscreen:false};
 else if(name==='browser-preparation')value={available:false};
 else if(name==='daily-tasks')value={tasks:[]};
 else if(name==='usage')value={days:[],totalSeconds:0};
 else if(name==='inbox')value={pending:0,errors:[]};
 else if(name==='goals')value={goals:[],contestPlan:{contests:[]}};
 else if(name==='leaderboard')value={configured:false,entries:[]};
 else if(name==='templates')value=JSON.parse(fs.readFileSync('../backend/resources/code-templates.json','utf8'));
 else if(name==='lectures')value={lectures:[]};
 else throw Error('Unrecognized isolated fixture request: '+name);
 await route.fulfill({json:value});
});
const base=`http://127.0.0.1:${vite.httpServer.address().port}`;
const folder=name=>page.locator('.training-list-content').getByRole('button').filter({has:page.locator('strong').getByText(name,{exact:true})}).first();
const navigation=()=>page.locator('.sidebar').getByRole('button',{name:'题单',exact:true});
const report={lists:lists.length,problems:rows.length,layouts:[]};
try {
 await page.goto(base);await navigation().waitFor();
 const start=performance.now();await navigation().click();await folder('洛谷').waitFor();report.firstOpenMs=Math.round(performance.now()-start);
 await folder('洛谷').click();
 for(const name of ['01 编程基础','02 基础解题方法','03 搜索与图','04 动态规划','05 数据结构进阶','06 数学与字符串','07 CF 2300 综合训练','08 专题加练','09 高阶拓展'])await folder(name).waitFor();
 await folder('01 编程基础').click();
 await page.getByRole('button',{name:/输入输出与顺序结构/}).first().click();
 await page.locator('.training-list-table tbody tr').first().waitFor();
 const firstIds=await page.locator('.training-list-table tbody tr').evaluateAll(nodes=>nodes.map(node=>node.dataset.problemId||node.innerText));
 assert(firstIds.length>0);report.firstPageProblems=firstIds.length;
 for(const width of [1440,1024,420]){
  await page.setViewportSize({width,height:900});
  for(const theme of ['light','dark']){
   await page.evaluate(value=>document.documentElement.dataset.theme=value,theme);await page.waitForTimeout(150);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
   assert(await page.locator('.training-list-content').evaluate(node=>node.scrollWidth<=node.clientWidth+1));
   report.layouts.push({width,theme});
  }
 }
 await page.setViewportSize({width:1440,height:900});
 await Promise.race([saved,new Promise((_,reject)=>setTimeout(()=>reject(Error('Account location was not saved')),12000))]);
 const prior=requests;await page.locator('.sidebar').getByRole('button',{name:'题库',exact:true}).click();
 const revisit=performance.now();await navigation().click();await page.locator('.training-list-table tbody tr').first().waitFor();report.revisitMs=Math.round(performance.now()-revisit);
 assert.equal(requests,prior,'A fresh account-scoped catalogue is reused on return');
 await page.reload();await navigation().click();await page.locator('.training-list-table tbody tr').first().waitFor();
 assert.match(await page.locator('.training-list-path').innerText(),/输入输出与顺序结构/);
 assert.deepEqual(await page.locator('.training-list-table tbody tr').evaluateAll(nodes=>nodes.map(node=>node.dataset.problemId||node.innerText)),firstIds);
 assert(writes.every(name=>name==='preferences'));assert.deepEqual(errors,[]);
 await page.screenshot({path:output+'/restored.png'});report.ok=true;console.log(JSON.stringify(report));
} catch(error){report.error=error.stack;await page.screenshot({path:output+'/failure.png'}).catch(()=>{});throw error;}
finally{fs.writeFileSync(output+'/report.json',JSON.stringify({...report,errors,writes,requests},null,2));await page.unrouteAll({behavior:'ignoreErrors'});await browser.close();await vite.close();}
