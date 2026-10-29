import assert from 'node:assert/strict';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {chromium} from 'playwright';import {createServer} from 'vite';
import {availablePages} from '../src/lib/navigationVisibility.js';
const templates=JSON.parse(await readFile('../backend/resources/code-templates.json','utf8'));
const vite=await createServer({server:{host:'127.0.0.1',port:0},plugins:[{name:'root-ui-isolation',configureServer(server){server.middlewares.use((request,response,next)=>{if(!request.url?.startsWith('/api/'))return next();response.writeHead(410,{'Content-Type':'application/json'});response.end('{"error":"Isolated UI fixture; live API disabled"}');});}}]});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1440,height:960}});
page.setDefaultTimeout(10000);const errors=[],unknown=[],external=[];page.on('pageerror',error=>errors.push(error.message));
const owner='c3e5d799-502a-4b4f-a864-a342f7db419e',now='2026-10-29T04:00:00.000Z';await page.clock.setFixedTime(new Date(now));
let completed=0,revision=0,preferences={theme:'dark',accent:'teal',fontSize:22,onboardingGuideVersion:2,onboardingCompleted:true,onboardingUnlockedPages:availablePages(11),favorites:['fixture::400A'],levelNoticeVersion:1,levelNoticeSeen:100,levelNoticePending:0};
const rows=[400,401,402].flatMap((round,index)=>['A','B'].map(letter=>({id:`fixture::${round}${letter}`,title:`练习 ${round}${letter}`,contest:`ABC ${round}`,problem:letter,platform:'AtCoder',series:'ABC',contestDate:`2026-10-${10+index}T12:00:00Z`,contestProblemCount:2,catalogContentReady:true,statementAvailable:true,solutionAvailable:true,url:`https://atcoder.jp/contests/abc${round}/tasks/abc${round}_${letter.toLowerCase()}`,difficulty:1000,difficultySource:'Codeforces 官方评分（隔离夹具）',difficultyConfidence:'HIGH',tags:['输入输出']})));
const workspace={training:[],sets:[],contests:[],activeContest:null,summary:{total:0,accepted:0,attempts:0,pending:0,due:0},now};
const notifications=Array.from({length:32},(_,i)=>({id:'today-'+i,kind:i%2?'comment':'like',actor:{nickname:'今日用户'+i},text:'今日留言内容 '.repeat(8),createdAt:i===0?'2026-10-28T16:00:00.000Z':now,read:true}));
notifications.push(...[{id:'old',kind:'comment',actor:{nickname:'昨日用户'},text:'昨日内容不可出现',createdAt:'2026-10-28T15:59:59.999Z',read:false},{id:'future',kind:'comment',actor:{nickname:'未来用户'},text:'未来内容不可出现',createdAt:'2026-10-29T16:00:00.000Z',read:false},{id:'invalid',kind:'comment',actor:{nickname:'无效日期'},text:'无效日期不可出现',createdAt:'invalid',read:false}]);
const hub={settings:{autoSync:false},accounts:[],updates:{configured:true},sync:{busy:false,providers:[]},notifications:Array.from({length:32},(_,i)=>({id:'update-'+i,type:'content',title:`公共内容更新 ${i}`,createdAt:now,read:true,count:i+1}))};
const daily=()=>({policyVersion:3,date:'2026-10-29',tasks:[],displayCompletedCount:completed,displayTarget:Math.min(10,Math.max(3,completed+1)),displayComplete:completed>=10});

for(const row of rows){row.platform='Codeforces';row.url='https://codeforces.com/contest/'+row.contest.replace(/\D/g,'')+'/problem/'+row.problem;row.difficultySource='Codeforces 官方评分（隔离夹具）';row.difficultyConfidence='HIGH';row.difficultyEstimated=false;}
rows.push(...['A','B'].map(letter=>({id:'nc-fixture::'+letter,title:'牛客练习 '+letter,contest:'隔离牛客题单',problem:letter,platform:'牛客',url:'https://ac.nowcoder.com/acm/problem/'+(letter==='A'?'221592':'221593'),tags:['输入输出'],knowledge:'输入输出',difficulty:null,catalogContentReady:true,statementAvailable:true})));
const refs=items=>items.map(row=>({problemId:row.id,url:row.url}));
const collections=[
 {id:'luogu-100',title:'【入门1】顺序结构',url:'https://www.luogu.com.cn/training/100',available:true,aggregateChildren:false,children:[],categories:[{id:'basic',name:'洛谷基础',order:0}],problems:refs(rows.slice(0,2))},
 {id:'luogu-101',title:'【入门2】分支结构',url:'https://www.luogu.com.cn/training/101',available:true,aggregateChildren:false,children:[],categories:[{id:'basic',name:'洛谷基础',order:0}],problems:refs(rows.slice(2,4))},
 {id:'nowcoder-selected',title:'牛客基础选编',url:'https://ac.nowcoder.com/discuss/817596',available:true,aggregateChildren:false,children:[],categories:[{id:'nc',name:'牛客公开题单',order:1}],problems:refs(rows.slice(-2))},
 {id:'custom-kept',title:'自建保留',custom:true,available:true,aggregateChildren:false,children:[],categories:[],problems:refs(rows.slice(0,1))}
];let likeRequests=0;
await page.addInitScript(()=>{if(new URLSearchParams(location.search).has('newAccount'))window.__tbNewAccount=true;});

await page.route('**/api/**',async route=>{
 const request=route.request(),url=new URL(request.url());if(!url.pathname.startsWith('/api/'))return route.continue();const name=url.pathname.replace('/api/','');let value;
 if(name==='account')value={required:true,authenticated:true,token:'fixture',account:{userId:owner,loginId:'fixture',nickname:'测试学习者'}};
 else if(name==='preferences'){if(request.method()==='POST')preferences=request.postDataJSON().preferences;value={preferences,updatedAt:now};}
 else if(name==='data')value={rows,categories:[],token:'fixture',today:'2026-10-29'};
 else if(name==='workspace')value=workspace;
 else if(name==='insights')value={summary:{totalSolved:98,submissions:171,activeDays:29,streak:19,longestStreak:21,completedContests:2},growth:{level:11,confirmed:true,authority:{owner,epoch:'root-ui-fixture',revision:++revision},currentLevelXp:745,nextLevelXp:2200,totalXp:11745,ranked:{qualified:true,tier:'青铜',badge:'tier-1',abilityScore:900}},knowledge:[],recommendations:[],activity:[],assessment:{},achievements:[],dailyTasks:daily()};
 else if(name==='daily-tasks')value=daily();
 else if(name==='software-update')value={currentVersion:'1.4.31',status:'current',autoCheck:false,canInstall:false};
 else if(name==='content-update')value={revision:0,status:'current'};
 else if(name==='contest-calendar')value={contests:[],providers:[],refreshing:false};
 else if(name==='browser-preparation')value={available:false};
 else if(name==='social')value={available:true,notifications,totalLikes:999,unreadCount:3,likes:[]};
 else if(name==='social/read')value={ok:true};
 else if(name==='goals')value={goals:[],contestPlan:{contests:[]}};
 else if(name==='inbox')value={pending:0,errors:[]};
 else if(name==='hub')value=hub;
 else if(name==='desktop/fullscreen')value={available:false,fullscreen:false};
 else if(name==='usage')value={days:[],totalSeconds:0};
 else if(name==='training-lists')value={lists:collections};
 else if(name==='training-list-likes'){likeRequests++;value={likes:[]};}
 else if(name==='templates')value=templates;
 else if(name==='lectures')value={lectures:[]};
 else if(name==='profile')value={profile:{userId:owner,nickname:'测试学习者'}};
 else if(name==='leaderboard')value={configured:false,entries:[]};
 else {unknown.push(name);value={};}
 await route.fulfill({json:value});
});
await page.route(/^https?:\/\/(?!127\.0\.0\.1)(?!localhost)/,route=>{external.push(route.request().url());return route.abort();});
const base=`http://127.0.0.1:${vite.httpServer.address().port}`,nav=()=>page.getByRole('navigation',{name:'主导航'});
async function load(){await page.goto(base);await page.waitForFunction(()=>document.querySelector('.profile-level-number')?.textContent==='11');await nav().getByRole('button',{name:'成长',exact:true}).waitFor();}
const openPage=async label=>{await page.keyboard.press('Control+k');const modal=page.getByRole('dialog',{name:'快捷操作',exact:true});await modal.waitFor();await modal.getByRole('button',{name:new RegExp('^打开'+label+'(?:\\s|$)')}).click();};

const output='tests/screenshots/training-platforms';await mkdir(output,{recursive:true});const report={samePage:[],geometry:[]};
const listPage=()=>page.getByRole('region',{name:'题单训练',exact:true}),home=()=>page.getByRole('button',{name:'全部题单',exact:true}).click();
const folder=name=>listPage().locator('.catalog-folder-row').filter({has:page.getByRole('strong')}).filter({hasText:name});
async function openFolder(name){await listPage().locator('.catalog-folder-row').filter({hasText:name}).first().click();}
async function waitIds(ids){await page.waitForFunction(ids=>JSON.stringify([...document.querySelectorAll('.training-list-table tr[data-id]')].map(n=>n.dataset.id))===JSON.stringify(ids),ids);}
async function recommended(from){await page.locator('.next-actions-primary[data-recommendation="list"]').click();await waitIds(rows.slice(0,2).map(r=>r.id));await page.locator('.training-list-path').getByRole('button',{name:'洛谷',exact:true}).waitFor();await page.locator('.training-list-path').getByRole('button',{name:'01 编程基础',exact:true}).waitFor();assert.equal(await page.getByRole('textbox',{name:'搜索题单或题目'}).inputValue(),'');report.samePage.push(from);}
try{
 await load();await nav().getByRole('button',{name:'题单',exact:true}).click();await listPage().waitFor();await listPage().locator('.catalog-folder-row').filter({hasText:'牛客'}).waitFor();
 for(const text of ['洛谷','牛客','我的题单','我的收藏'])assert.equal(await listPage().locator('.catalog-folder-row').filter({hasText:text}).count(),1,text);
 assert.equal(await listPage().locator('.like-burst').count(),0);await recommended('platform-root');
 await home();await openFolder('牛客');await page.getByRole('button',{name:'打开题单：牛客基础选编',exact:true}).click();await waitIds(rows.slice(-2).map(r=>r.id));assert.equal(await listPage().locator('.remove-training').count(),0);await recommended('nowcoder-list');
 await home();await openFolder('洛谷');await openFolder('01 编程基础');await page.getByRole('button',{name:'打开题单：分支与循环',exact:true}).click();await waitIds(rows.slice(2,4).map(r=>r.id));await recommended('different-luogu-list');
 await home();await page.getByRole('textbox',{name:'搜索题单或题目',exact:true}).fill('牛客');await page.getByRole('button',{name:'打开题单：牛客基础选编',exact:true}).waitFor();await page.getByRole('button',{name:'清空题单搜索',exact:true}).click();
 await page.getByRole('button',{name:'题单目录方式',exact:true}).click();await openFolder('牛客公开题单');await page.getByRole('button',{name:'打开题单：牛客基础选编',exact:true}).click();await waitIds(rows.slice(-2).map(r=>r.id));assert.equal(await page.getByRole('link',{name:'牛客原题单',exact:true}).getAttribute('href'),'https://ac.nowcoder.com/discuss/817596');await recommended('source-mode-nowcoder');
 await home();await page.getByRole('button',{name:'新建题单',exact:true}).click();await page.getByRole('textbox',{name:'题单名称',exact:true}).fill('未保存的自建题单草稿');
 await page.locator('.next-actions-primary[data-recommendation="list"]').dispatchEvent('click');assert.equal(await page.getByRole('textbox',{name:'题单名称',exact:true}).inputValue(),'未保存的自建题单草稿');await page.getByRole('button',{name:'关闭题单编辑',exact:true}).click();await waitIds(rows.slice(0,2).map(r=>r.id));report.samePage.push('editor-draft-kept');
 for(const width of [1440,960,430])for(const theme of ['dark','light']){
  preferences={...preferences,theme,fontSize:22};await page.setViewportSize({width,height:900});await load();await nav().getByRole('button',{name:'题单',exact:true}).click();await home();await openFolder('洛谷');await openFolder('01 编程基础');await page.locator('.training-list-card').first().waitFor();
  assert.equal(await listPage().locator('.training-card-actions').count(),0);assert.equal(await listPage().locator('.like-burst').count(),0);
  const cards=await page.locator('.training-list-card').evaluateAll(nodes=>nodes.map(n=>{const r=n.getBoundingClientRect(),title=n.querySelector('strong').getBoundingClientRect(),ring=n.querySelector('.training-card-progress').getBoundingClientRect();return {height:r.height,titleY:title.y+title.height/2,ringY:ring.y+ring.height/2,right:r.right,width:innerWidth};}));assert(cards.every(c=>Math.abs(c.titleY-c.ringY)<1.5&&c.right<=c.width),JSON.stringify(cards));assert(Math.max(...cards.map(c=>c.height))-Math.min(...cards.map(c=>c.height))<2,JSON.stringify(cards));await page.screenshot({path:output+'/'+width+'-'+theme+'.png'});report.geometry.push({width,theme,cards});
 }
 await home();await openFolder('我的收藏');await waitIds([rows[0].id]);await home();await openFolder('我的题单');await page.getByRole('button',{name:'删除题单：自建保留',exact:true}).waitFor();assert.equal(await page.locator('.like-burst').count(),0);
 await page.goto(base+'?newAccount=1');await page.locator('.training-list-path').getByRole('button',{name:'01 编程基础',exact:true}).waitFor();await page.locator('.training-list-path').getByRole('button',{name:'洛谷',exact:true}).waitFor();
 assert.equal(likeRequests,0);assert.deepEqual(errors,[]);assert.deepEqual(unknown,[]);assert.deepEqual(external,[]);report.ok=true;console.log(JSON.stringify({ok:true,samePageRequests:report.samePage,geometryCases:report.geometry.length,likeRequests,legacyFoundation:true,customAndFavoritesPreserved:true}));
}catch(error){report.error=error.stack||error.message;await page.screenshot({path:output+'/failure.png'}).catch(()=>{});throw error;}
finally{await writeFile(output+'/report.json',JSON.stringify({...report,errors,unknown,external},null,2));await page.unrouteAll({behavior:'ignoreErrors'});await browser.close();await vite.close();}
