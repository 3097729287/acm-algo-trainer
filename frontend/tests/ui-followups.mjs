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
let held=true,resume=[];let level=12,revision=0,draft='',sampleRequested=false,officialRequested=false,preferences={theme:'dark',accent:'teal',fontSize:15,onboardingGuideVersion:2,onboardingCompleted:true,onboardingUnlockedPages:availablePages(11),levelNoticeVersion:1,levelNoticeSeen:100,levelNoticePending:0};
preferences.navOrder=['training-lists'];
let preferenceSaveFailures=0,preferenceSaveAttempts=0;
const rows=Array.from({length:20},(_,i)=>({id:'fixture::'+i,title:'完整练习 '+i,contest:'1024数学专场考核',problem:String.fromCharCode(65+i),platform:'牛客',series:'牛客',url:'https://ac.nowcoder.com/acm/contest/142622/'+String.fromCharCode(65+i),difficulty:1000,difficultySource:'fixture',difficultyConfidence:'HIGH',tags:[i<10?'枚举':'素数'],contestProblemCount:20,catalogContentReady:true,solutionAvailable:true}));
for(const prefix of ['ICPC','CCPC'])rows.push({id:prefix,contest:prefix+' 2026 中国区域赛',title:prefix+'练习',problem:'A',platform:'Codeforces',series:'XCPC',url:'https://codeforces.com/gym/'+(prefix==='ICPC'?'101':'102')+'/problem/A',difficulty:2000,tags:['树'],contestProblemCount:1,catalogContentReady:true});
const lists=[{id:'fixture-basic',title:'顺序结构',available:true,categories:[],problems:rows.map(row=>({problemId:row.id,url:row.url}))}];
const workspace={training:[],sets:[],contests:[],activeContest:null,summary:{total:0,accepted:0,attempts:0,due:0,pending:0,todayAccepted:0},now};
await page.route('**/api/**',async route=>{
 const url=new URL(route.request().url());if(!url.pathname.startsWith('/api/'))return route.continue();const path=url.pathname.replace('/api/','');let value;
 if(path==='account')value={required:true,authenticated:true,token:'fixture',account:{userId:owner,loginId:'fixture',nickname:'测试学习者'}};
 else if(path==='preferences'){if(route.request().method()==='POST'){preferenceSaveAttempts++;if(preferenceSaveFailures>0){preferenceSaveFailures--;await route.fulfill({status:503,json:{error:'隔离偏好保存失败'}});return;}preferences=route.request().postDataJSON().preferences;}value={preferences,updatedAt:now};}
 else if(path==='data')value={rows,categories:[],token:'fixture',today:now.slice(0,10)};
 else if(path==='workspace')value=workspace;
 else if(path==='insights'){if(held)await new Promise(resolve=>resume.push(resolve));value={summary:{totalSolved:0},growth:{level,confirmed:true,authority:{owner,epoch:'navigation-fixture',revision:++revision},tier:'黑铁',currentLevelXp:0,nextLevelXp:200,totalXp:0},knowledge:[],recommendations:[],activity:[],assessment:{},dailyTasks:{tasks:[]}};}
 else if(path==='software-update')value={currentVersion:'1.4.29',status:'current',autoCheck:false,canInstall:false};
 else if(path==='content-update')value={revision:0,status:'current'};
 else if(path==='contest-calendar')value={contests:[],providers:[],refreshing:false};
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

const base=process.env.UI_FOLLOWUPS_BASE||`http://127.0.0.1:${vite.httpServer.address().port}`,save='../.backups/ui-followups-20261030/reader';await mkdir(save,{recursive:true});
const nav=()=>page.getByRole('navigation',{name:'主导航'});
const release=()=>{held=false;for(const done of resume)done();resume=[];};
const settled=async()=>{await nav().getByRole('button',{name:level>=5?'成长':'题单',exact:true}).waitFor();await page.waitForFunction(()=>!document.querySelector('.sidebar nav').getAttribute('aria-busy')||document.querySelector('.sidebar nav').getAttribute('aria-busy')==='false');};
try {
 await page.goto(base);await page.locator('.navigation-pending').waitFor();
 assert.equal(await nav().getByRole('button').count(),0,'Unknown level never masquerades as the three-page Lv1 menu');
 release();await settled();assert.equal(await nav().getByRole('button').count(),12);
 assert.equal(await page.evaluate(owner=>JSON.parse(localStorage.getItem('tb.navigation-level.v1.'+owner)).level,owner),12);
 held=true;await page.reload();await nav().getByRole('button',{name:'成长',exact:true}).waitFor();
 assert.equal(await nav().getByRole('button').count(),12,'Restart paints the last confirmed complete navigation before insights arrives');
 assert.equal(await page.locator('.navigation-pending').count(),0);release();await settled();
 assert.deepEqual((await nav().getByRole('button').allTextContents()).slice(0,4),['我的训练','题库','题单','比赛'],'The shipped singleton preference migrates to the requested default order');
 await page.setViewportSize({width:1440,height:600});
 await nav().getByRole('button',{name:'比赛',exact:true}).click();
 await page.getByRole('button',{name:'查看 牛客 1024数学专场考核，20 道题',exact:true}).click();
 const detail=()=>page.locator('.competition-detail');
 await page.screenshot({path:`${save}/contest-detail.png`});
 await detail().evaluate(node=>node.scrollTop=node.scrollHeight);const before=await detail().evaluate(node=>node.scrollTop);assert(before>0);
 await page.getByRole('button',{name:'练习 T 完整练习 19',exact:true}).click();await page.locator('.cm-content').waitFor();
 const fontSize=page.getByRole('spinbutton',{name:'题面字号',exact:true});
 await fontSize.fill('32');await fontSize.press('Tab');
 const toolbarGeometry=[];
 for(const font of [13,18,22])for(const width of [2048,1440,1280,1050,1000,960]){
  await page.setViewportSize({width,height:800});await page.evaluate(value=>document.documentElement.style.fontSize=value+'px',font);
  await page.waitForFunction(()=>!document.querySelector('.tb-workbench').classList.contains('wb-compact'));
  const geometry=await page.locator('.wb-body').evaluate(body=>{
   const rect=node=>{const r=node.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom};};
   return [...body.querySelectorAll(':scope>.wb-statement-pane>.wb-pane-header,:scope>.wb-code-pane>.wb-pane-header')].map(header=>({header:rect(header),controls:[...header.querySelectorAll('button,input,select,a')].filter(node=>node.getClientRects().length).map(node=>({label:node.getAttribute('aria-label')||node.textContent,rect:rect(node)}))}));
  });
  assert.equal(geometry.length,2);assert(Math.abs(geometry[0].header.y-geometry[1].header.y)<.5&&Math.abs(geometry[0].header.height-geometry[1].header.height)<.5,'Both full-App toolbars share one row: '+JSON.stringify({font,width,geometry}));
  for(const {header,controls} of geometry)for(const {label,rect} of controls)assert(rect.y>=header.y-.5&&rect.bottom<=header.bottom+.5&&rect.x>=header.x-.5&&rect.right<=header.right+.5,'Toolbar controls fit their actual pane: '+JSON.stringify({font,width,label,rect,header}));
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
  toolbarGeometry.push({font,width,panes:geometry.map(item=>item.header)});
 }
 await page.setViewportSize({width:1440,height:600});await page.evaluate(()=>document.documentElement.style.fontSize='15px');
 await page.screenshot({path:`${save}/workbench-aligned-32px.png`});
 await page.locator('.cm-content').fill('// corner-return draft\nint main() { return 0; }');
 for(const compact of [false,true]){
  if(compact){await page.getByRole('button',{name:'练习 T 完整练习 19',exact:true}).click();await page.locator('.cm-content').waitFor();await page.setViewportSize({width:430,height:800});await page.locator('.wb-compact-toolbar').waitFor();}
  const back=page.getByRole('button',{name:'返回列表',exact:true});
  const corner=await back.evaluate(button=>{const rect=button.getBoundingClientRect(),points=[{x:rect.left+1,y:rect.top+1},{x:rect.right-1,y:rect.bottom-1}];return {points,hits:points.map(p=>button.contains(document.elementFromPoint(p.x,p.y)))};});
  assert(corner.hits.every(Boolean),'Both corners of the actual full-App return button accept pointer clicks: '+JSON.stringify(corner));
  await page.mouse.click(corner.points[0].x,corner.points[0].y);await detail().waitFor();
  await page.waitForFunction(()=>!document.querySelector('.tb-workbench'));
  if(!compact){assert.equal(await detail().locator('h2').innerText(),'1024数学专场考核');assert(Math.abs(await detail().evaluate(node=>node.scrollTop)-before)<2,'The same contest and scroll position survive actual App workbench unmount');}
  assert.equal(draft,'// corner-return draft\nint main() { return 0; }','Returning retains the exact user draft');
 }
 await page.setViewportSize({width:1440,height:600});
 assert.equal(await detail().locator('h2').innerText(),'1024数学专场考核');
 assert.equal(await page.locator('.competition-question button button').count(),0,'Knowledge and practice controls are valid sibling buttons');
 await detail().evaluate(node=>node.scrollTop=0);
 await page.locator('.competition-tag').filter({hasText:'枚举'}).first().focus();await page.keyboard.press('Enter');
 await page.locator('.workspace-area[data-page="library"] .problem-table').waitFor();
 assert.equal(await page.locator('.active-knowledge-filter').innerText(),'枚举');
 await page.getByText('共 10 题',{exact:true}).waitFor();
 const filteredTitles=await page.locator('.problem-table .problem-title').allTextContents();
 await page.getByRole('button',{name:'题库下一页',exact:true}).click();
 filteredTitles.push(...await page.locator('.problem-table .problem-title').allTextContents());
 assert.equal(new Set(filteredTitles).size,10,'All ten matching library problems remain reachable across fitted pages');
 assert.equal(await page.locator('.cm-content').count(),0,'Clicking a knowledge chip does not open its problem');
 await page.getByRole('button',{name:'筛选题目',exact:true}).click();
 await page.getByRole('combobox',{name:'筛选比赛分类',exact:true}).click();
 await page.locator('.folder-select-menu [role="option"]').filter({hasText:/^XCPC$/}).click();
 const menuWidths=await page.locator('.folder-select-menu [role="option"] .catalog-latin-name').evaluateAll(nodes=>nodes.filter(node=>['ICPC','CCPC'].includes(node.textContent)).map(node=>node.getBoundingClientRect().width));
 assert.equal(menuWidths.length,2);assert(Math.abs(menuWidths[0]-menuWidths[1])<.1,'The shared folder selector uses the same aligned Latin names');
 await page.keyboard.press('Escape');if(await page.getByRole('button',{name:'关闭筛选',exact:true}).count())await page.getByRole('button',{name:'关闭筛选',exact:true}).click();
 await nav().getByRole('button',{name:'比赛',exact:true}).click();await detail().waitFor();
 await page.getByRole('button',{name:'全部比赛',exact:true}).click();
 await page.getByRole('button',{name:'比赛文件夹浏览',exact:true}).click();
 await page.locator('.catalog-folder-row').filter({has:page.getByText('XCPC',{exact:true})}).click();
 const geometry=[];
 for(const width of [1440,1050,430])for(const theme of ['dark','light']) {
  await page.setViewportSize({width,height:800});await page.evaluate(theme=>document.documentElement.dataset.theme=theme,theme);
  const values=await page.locator('.catalog-folder-row strong').evaluateAll(nodes=>nodes.filter(n=>/^(ICPC|CCPC) 区域赛$/.test(n.textContent)).map(n=>{const span=n.querySelector('.catalog-latin-name'),r=span.getBoundingClientRect();return {text:n.textContent,x:r.left,width:r.width,right:r.right,font:getComputedStyle(span).fontFamily};}));
  assert.equal(values.length,2);assert(Math.abs(values[0].width-values[1].width)<.1&&Math.abs(values[0].right-values[1].right)<.1,JSON.stringify(values));
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
  geometry.push({width,theme,values});await page.screenshot({path:`${save}/folders-${width}-${theme}.png`});
 }
 // A different account must not inherit the previous learner's navigation.
 owner='f4cf7c01-9c01-4cc1-a95b-a7412d3d0201';level=1;held=true;
 await page.goto(base);await page.locator('.navigation-pending').waitFor();assert.equal(await nav().getByRole('button').count(),0);
 release();await settled();assert.deepEqual(await nav().getByRole('button').allTextContents(),['我的训练','题单','提交记录']);
 await page.reload();await settled();assert.equal(await nav().getByRole('button').count(),3,'Real Lv1 gates remain intact');
 assert.deepEqual(errors,[]);assert.deepEqual(unknown,[]);
 const report={ok:true,unknownLevelDoesNotShowLv1:true,restartCompleteMenu:true,legacySidebarOrder:true,accountIsolation:true,actualAppContestReturn:true,fullAppReturnCorners:true,returnDraftPreserved:true,toolbarGeometry,detailScrollRestored:true,keyboardKnowledgeFilter:true,knowledgeCount:10,catalogGeometry:geometry,errors,unknown,officialSubmissionsSent:0};
 await writeFile(`${save}/report.json`,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
} catch(error){console.error(JSON.stringify({errors,unknown,body:(await page.locator('body').innerText()).slice(0,1800)}));throw error;}finally{release();await browser.close();await vite.close();}
