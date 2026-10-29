import assert from 'node:assert/strict';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {chromium} from 'playwright';import {createServer} from 'vite';
import {availablePages} from '../src/lib/navigationVisibility.js';
const templates=JSON.parse(await readFile('../backend/resources/code-templates.json','utf8'));
const vite=await createServer({server:{host:'127.0.0.1',port:0},plugins:[{name:'root-ui-isolation',configureServer(server){server.middlewares.use((request,response,next)=>{if(!request.url?.startsWith('/api/'))return next();response.writeHead(410,{'Content-Type':'application/json'});response.end('{"error":"Isolated UI fixture; live API disabled"}');});}}]});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1440,height:960}});
page.setDefaultTimeout(10000);const errors=[],unknown=[],external=[];page.on('pageerror',error=>errors.push(error.message));
const owner='c3e5d799-502a-4b4f-a864-a342f7db419e',now='2026-10-29T04:00:00.000Z';await page.clock.setFixedTime(new Date(now));
let completed=0,revision=0,preferences={theme:'dark',accent:'teal',fontSize:22,onboardingGuideVersion:2,onboardingCompleted:true,onboardingUnlockedPages:availablePages(11),levelNoticeVersion:1,levelNoticeSeen:100,levelNoticePending:0};
const rows=[400,401,402].flatMap((round,index)=>['A','B'].map(letter=>({id:`fixture::${round}${letter}`,title:`练习 ${round}${letter}`,contest:`ABC ${round}`,problem:letter,platform:'AtCoder',series:'ABC',contestDate:`2026-10-${10+index}T12:00:00Z`,contestProblemCount:2,catalogContentReady:true,statementAvailable:true,solutionAvailable:true,url:`https://atcoder.jp/contests/abc${round}/tasks/abc${round}_${letter.toLowerCase()}`,difficulty:1000,difficultySource:'Codeforces 官方评分（隔离夹具）',difficultyConfidence:'HIGH',tags:['输入输出']})));
const workspace={training:[],sets:[],contests:[],activeContest:null,summary:{total:0,accepted:0,attempts:0,pending:0,due:0},now};
let notifications=Array.from({length:32},(_,i)=>({id:'today-'+i,kind:i%2?'comment':'like',actor:{nickname:'今日用户'+i},text:'今日留言内容 '.repeat(8),createdAt:i===0?'2026-10-28T16:00:00.000Z':now,read:true}));
notifications.push(...[{id:'old',kind:'comment',actor:{nickname:'昨日用户'},text:'昨日内容不可出现',createdAt:'2026-10-28T15:59:59.999Z',read:false},{id:'future',kind:'comment',actor:{nickname:'未来用户'},text:'未来内容不可出现',createdAt:'2026-10-29T16:00:00.000Z',read:false},{id:'invalid',kind:'comment',actor:{nickname:'无效日期'},text:'无效日期不可出现',createdAt:'invalid',read:false}]);
let hub={settings:{autoSync:false},accounts:[],updates:{configured:true},sync:{busy:false,providers:[]},notifications:Array.from({length:32},(_,i)=>({id:'update-'+i,type:'content',title:`公共内容更新 ${i}`,createdAt:now,read:true,count:i+1}))};
const daily=()=>({policyVersion:3,date:'2026-10-29',tasks:[],displayCompletedCount:completed,displayTarget:Math.min(10,Math.max(3,completed+1)),displayComplete:completed>=10});
let holdAutomaticReads=false,failSocialAll=false;const held=[],calls={social:0,updates:0};
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
 else if(name==='social')value={available:true,notifications,totalLikes:999,todayLikes:notifications.filter(n=>n.kind==='like').length,unreadCount:notifications.filter(n=>!n.read).length,likes:[]};
 else if(name==='social/read'){
 const body=request.postDataJSON();if(!body.all&&holdAutomaticReads)await new Promise(resolve=>held.push(resolve));
 if(body.all){calls.social++;if(failSocialAll){failSocialAll=false;await route.fulfill({status:503,json:{error:'测试社交标读失败'}});return;}}
 const ids=new Set(body.ids||[]);notifications=notifications.map(item=>body.all||ids.has(item.id)?{...item,read:true}:item);value={ok:true};
 }
 else if(name==='hub/dismiss-all'){calls.updates++;hub={...hub,notifications:hub.notifications.map(item=>({...item,read:true}))};value=hub;}
 else if(name==='hub/dismiss'){if(holdAutomaticReads)await new Promise(resolve=>held.push(resolve));const id=request.postDataJSON().id;hub={...hub,notifications:hub.notifications.map(item=>item.id===id?{...item,read:true}:item)};value=hub;}
 else if(name==='goals')value={goals:[],contestPlan:{contests:[]}};
 else if(name==='inbox')value={pending:0,errors:[]};
 else if(name==='hub')value=hub;
 else if(name==='desktop/fullscreen')value={available:false,fullscreen:false};
 else if(name==='usage')value={days:[],totalSeconds:0};
 else if(name==='training-lists')value={lists:[]};
 else if(name==='training-list-likes')value={likes:[]};
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

const output='tests/screenshots/messages-modal';await mkdir(output,{recursive:true});const report={geometry:[],bulk:[],external};
const socialRows=count=>Array.from({length:count},(_,i)=>({id:'social-'+i,kind:i%2?'like':'comment',actor:{nickname:'测试用户'+i},text:'当天留言，保留原文。'.repeat(20),createdAt:now,read:true}));
const updates=()=>Array.from({length:32},(_,i)=>({id:'update-'+i,type:'content',title:'更新通知 '+i,createdAt:now,read:true,count:i+1}));
async function open(){
 await load();await page.evaluate(()=>{window.__tbAccountSync={status:'offline',offline:true,recoverable:true,error:'离线学习：本机记录已保存，联网后自动同步'};window.dispatchEvent(new CustomEvent('tb:sync-status',{detail:window.__tbAccountSync}));window.dispatchEvent(new CustomEvent('tb:account-sync-attention',{detail:{owner:'c3e5d799-502a-4b4f-a864-a342f7db419e',kind:'recovery',id:'legacy-offline',message:'离线学习：本机记录已保存，联网后自动同步'}}));});
 await page.getByRole('button',{name:'消息通知',exact:true}).click();const dialog=page.getByRole('dialog',{name:'消息与更新',exact:true});await dialog.waitFor();await dialog.locator('.social-notifications-summary').waitFor();return dialog;
}
try{
 for(const width of [1440,960,430])for(const count of [0,1,32]){
  notifications=socialRows(count);hub={...hub,notifications:updates()};preferences={...preferences,fontSize:22,theme:width===430?'light':'dark'};await page.setViewportSize({width,height:900});const modal=await open();
  assert.equal(await modal.getByRole('button',{name:'全部已读',exact:true}).count(),1);assert.equal(await modal.getByRole('button',{name:'一键已读',exact:true}).count(),0);assert.equal(await modal.getByRole('region',{name:'账号同步消息'}).count(),0);assert.doesNotMatch(await modal.innerText(),/离线学习|账号同步|收到的爱心和留言会出现在这里/);
  const geometry=await modal.evaluate(n=>{const box=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {x:r.x,y:r.y,right:r.right,bottom:r.bottom,w:r.width,h:r.height,client:e.clientHeight,scroll:e.scrollHeight,overflow:s.overflowY};};return {modal:box(n),body:box(n.querySelector('.modal-body')),social:box(n.querySelector('.messages-social-pane')),updates:box(n.querySelector('.update-panel')),title:box(n.querySelector('.social-notifications-title')),summary:box(n.querySelector('.social-notifications-summary')),read:box(n.querySelector('header button[aria-label="全部已读"]')),close:box(n.querySelector('header button[aria-label="关闭"]'))};});
  assert(geometry.social.h<=geometry.updates.h+2,JSON.stringify({count,width,geometry}));assert.equal(geometry.modal.scroll,geometry.modal.client);assert.equal(geometry.body.scroll,geometry.body.client);assert(geometry.read.right<=geometry.close.x+1);assert(Math.abs(geometry.title.y+geometry.title.h/2-geometry.summary.y-geometry.summary.h/2)<2);assert(geometry.summary.x>=geometry.title.right-1);assert(geometry.summary.right<=width);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
  if(count===0){assert(geometry.social.h<90,JSON.stringify(geometry));assert(geometry.updates.h>geometry.social.h*2);}
  if(count===32){assert(Math.abs(geometry.social.h-geometry.updates.h)<2,JSON.stringify(geometry));const top=modal.locator('.messages-social-pane'),bottom=modal.locator('.update-panel');await top.hover();await page.mouse.wheel(0,260);await page.waitForFunction(()=>document.querySelector('.messages-social-pane').scrollTop>0);assert.equal(await bottom.evaluate(n=>n.scrollTop),0);const before=await top.evaluate(n=>n.scrollTop);await bottom.hover();await page.mouse.wheel(0,260);await page.waitForFunction(()=>document.querySelector('.messages-modal .update-panel').scrollTop>0);assert.equal(await top.evaluate(n=>n.scrollTop),before);}
  await page.screenshot({path:output+'/'+width+'-'+count+'.png'});report.geometry.push({width,count,...geometry});await page.keyboard.press('Escape');await modal.waitFor({state:'hidden'});
 }
 for(const partialFailure of [false,true]){
  holdAutomaticReads=true;failSocialAll=partialFailure;notifications=socialRows(2).map(item=>({...item,read:false}));hub={...hub,notifications:updates().map(item=>({...item,read:false}))};calls.social=0;calls.updates=0;
  await page.setViewportSize({width:1050,height:800});const modal=await open();const all=modal.getByRole('button',{name:'全部已读',exact:true});await all.click();await page.waitForTimeout(150);assert.equal(calls.social,1);assert.equal(calls.updates,1);assert(hub.notifications.every(item=>item.read));
  if(partialFailure){await page.getByText('测试社交标读失败',{exact:true}).waitFor();assert(notifications.some(item=>!item.read));await all.click();await page.waitForTimeout(150);assert.equal(calls.social,2);assert.equal(calls.updates,2);}
  await page.waitForFunction(()=>document.querySelector('.social-notifications-summary')?.textContent.includes('0 条未读消息'));assert(notifications.every(item=>item.read));assert.equal(await all.isDisabled(),true);holdAutomaticReads=false;held.splice(0).forEach(release=>release());report.bulk.push({partialFailure,...calls,updatesRetainedOnSocialFailure:true});await page.keyboard.press('Escape');
 }
 assert.deepEqual(errors,[]);assert.deepEqual(unknown,[]);assert.deepEqual(external,[]);console.log(JSON.stringify({ok:true,geometryCases:report.geometry.length,bulkCases:report.bulk.length,report:output+'/report.json'}));
}catch(error){report.error=error.stack||error.message;await page.screenshot({path:output+'/failure.png'}).catch(()=>{});throw error;}
finally{holdAutomaticReads=false;held.splice(0).forEach(release=>release());await writeFile(output+'/report.json',JSON.stringify({...report,errors,unknown},null,2));await page.unrouteAll({behavior:'ignoreErrors'});await browser.close();await vite.close();}
