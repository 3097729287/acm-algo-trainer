import {openSettings,setTheme} from './settings-navigation.mjs';
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


const output='tests/screenshots/chrome-theme';await mkdir(output,{recursive:true});const report={cases:[]};
const geometry=()=>page.evaluate(()=>{
 const box=n=>{const r=n.getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom,w:r.width,h:r.height,cx:r.x+r.width/2,cy:r.y+r.height/2};};
 const shown=n=>n&&n.getClientRects().length&&getComputedStyle(n).display!=='none';
 const top=document.querySelector('.topbar'),footer=document.querySelector('.app-statusbar'),settings=document.querySelector('.sidebar-bottom .nav-item'),brand=document.querySelector('.brand-mark'),nav=[...document.querySelectorAll('.sidebar nav .nav-item')].find(shown);
 const controls=[...document.querySelectorAll('.topbar-actions>.practice-streak,.topbar-actions>.topbar-status-chip,.topbar-actions>.profile-badge,.topbar-actions>.icon-button')].filter(shown).map(box);
 const footerControls=[...footer.children].filter(shown).map(box),ts=getComputedStyle(top),fs=getComputedStyle(footer);
 const first=[...top.children].filter(shown).map(box).sort((a,b)=>a.y-b.y)[0];
 return {width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth+1,top:box(top),first,controls,footer:box(footer),footerControls,brand:box(brand),navIcon:box(nav.querySelector('svg')),navText:shown(nav.querySelector('span'))?box(nav.querySelector('span')):null,settingsIcon:box(settings.querySelector('svg')),settings:box(settings),padding:[ts.paddingLeft,ts.paddingRight,fs.paddingLeft,fs.paddingRight],theme:box(document.querySelector('.theme-toggle')),bell:box(document.querySelector('.topbar-actions>.icon-button[aria-label="消息通知"]'))};
});
try{
 for(const width of [2048,1294,960,810,650,430])for(const font of [13,22])for(const collapsed of (width===1294?[false,true]:[false])){
  preferences={...preferences,theme:'dark',fontSize:font,collapsed};await page.setViewportSize({width,height:960});await load();await page.locator('.next-actions-primary').waitFor();await page.waitForTimeout(220);
  await setTheme(page,'light');let g=await geometry();
  assert.equal(g.overflow,false,JSON.stringify({width,font,collapsed,g}));assert(g.theme.w>0&&g.bell.w>0&&g.theme.right<=width&&g.bell.right<=width,JSON.stringify(g));assert(Math.abs(g.theme.cy-g.bell.cy)<1.5);
  assert(g.controls.every(c=>c.right<=width+1),JSON.stringify(g));assert(g.controls.every(c=>Math.abs(c.cy-g.controls[0].cy)<1.5),JSON.stringify(g));
  assert(Math.abs(g.brand.cx-g.navIcon.cx)<1.5&&Math.abs(g.brand.cx-g.settingsIcon.cx)<1.5,JSON.stringify(g));
  if(g.navText)assert(Math.abs(g.navText.cy-g.navIcon.cy)<1.5,JSON.stringify(g));
  assert(Math.abs(g.settings.cy-g.footer.cy)<1.5&&g.footerControls.every(c=>Math.abs(c.cy-g.footer.cy)<1.5),JSON.stringify(g));assert(g.padding.every(p=>p===g.padding[0]),JSON.stringify(g));
  if(width>650)assert(Math.abs(g.brand.cy-g.top.cy)<1.5,JSON.stringify(g));else assert(Math.abs(g.brand.cy-g.first.cy)<1.5,JSON.stringify(g));
  await page.screenshot({path:output+'/'+width+'-'+font+'-'+collapsed+'.png'});report.cases.push({width,font,collapsed,...g});
 }
 await openSettings(page,'外观');assert.equal(await page.getByRole('button',{name:'石墨深色',exact:true}).count(),0);assert.equal(await page.getByRole('button',{name:'云白浅色',exact:true}).count(),0);assert.equal(await page.locator('.visual-preferences .setting-label strong').filter({hasText:/^主题$/}).count(),0);
 const darkSaved=page.waitForResponse(response=>{const request=response.request(),url=new URL(response.url());return url.origin===new URL(base).origin&&url.pathname==='/api/preferences'&&request.method()==='POST'&&request.postDataJSON()?.preferences?.theme==='dark'&&response.ok();});
 await setTheme(page,'dark');await darkSaved;assert.equal(preferences.theme,'dark');await page.reload();await page.waitForFunction(()=>document.documentElement.dataset.theme==='dark');
 await page.waitForFunction(()=>document.querySelector('.profile-level-number')?.textContent==='11');await page.locator('.next-actions-primary').waitFor();await page.keyboard.press('Control+k');const commands=page.getByRole('dialog',{name:'快捷操作',exact:true});await commands.waitFor();await commands.getByRole('button',{name:'切换深浅主题',exact:true}).click();await page.waitForFunction(()=>document.documentElement.dataset.theme==='light');
 assert.deepEqual(errors,[]);assert.deepEqual(unknown,[]);assert.deepEqual(external,[]);report.ok=true;console.log(JSON.stringify({ok:true,geometryCases:report.cases.length,singleThemeButton:true,settingsRowRemoved:true,savedPreferenceReload:true,keyboardCommandPreserved:true}));
}catch(error){report.error=error.stack||error.message;await page.screenshot({path:output+'/failure.png'}).catch(()=>{});throw error;}
finally{await writeFile(output+'/report.json',JSON.stringify({...report,errors,unknown,external},null,2));await page.unrouteAll({behavior:'ignoreErrors'});await browser.close();await vite.close();}
