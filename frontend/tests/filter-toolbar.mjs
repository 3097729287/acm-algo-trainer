import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {chromium} from 'playwright';
import {createServer} from 'vite';
import {availablePages} from '../src/lib/navigationVisibility.js';

// Actual App, controls and filter models; every API/write belongs to this fixture.
const vite=await createServer({server:{host:'127.0.0.1',port:0,watch:null},plugins:[{name:'filter-api-isolation',configureServer(server){server.middlewares.use((request,response,next)=>{if(!request.url?.startsWith('/api/'))return next();response.writeHead(410);response.end('Isolated filter fixture');});}}]});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:960}});page.setDefaultTimeout(10000);
const now=new Date().toISOString(),owner='87a702f8-66fd-4ae0-b4b2-ed50d6277279',errors=[],unknown=[],external=[],writes=[];
page.on('pageerror',error=>errors.push(error.message));
const rows=['A','B','C'].map((letter,index)=>({id:'filter::'+letter,title:'筛选练习 '+letter,contest:'ABC '+(400+index),problem:'A',platform:'AtCoder',contestDate:now,contestProblemCount:1,catalogContentReady:true,statementAvailable:true,solutionAvailable:true,difficulty:1000+index*100,difficultySource:'原站评分（隔离夹具）',difficultyConfidence:'HIGH',tags:['输入输出'],url:'https://example.invalid/'+letter}));
const originals=rows.slice(0,2).map(row=>({id:row.id,activeAt:now,queue:'fill',accepted:false,attempts:1,verdict:'WA'}));
let training=structuredClone(originals),pending=0,activeContest=null,revision=0;
let preferences={theme:'dark',accent:'teal',fontSize:15,onboardingCompleted:true,onboardingGuideVersion:2,onboardingUnlockedPages:availablePages(11),levelNoticeVersion:1,levelNoticeSeen:100,levelNoticePending:0};
const preserved={draft:'int main(){return 0;}',history:['historical-official-receipt']};
const workspace=()=>({now,training,sets:[],contests:activeContest?[activeContest]:[],activeContest,summary:{total:training.length,accepted:0,attempts:2,due:0,pending,todayAccepted:0}});
await page.route('**/api/**',async route=>{
 const request=route.request(),url=new URL(request.url());if(!url.pathname.startsWith('/api/'))return route.continue();const name=url.pathname.replace('/api/','');let value;
 if(name==='account')value={required:true,authenticated:true,token:'filter-fixture',account:{userId:owner,loginId:'filter-fixture',nickname:'隔离筛选账号'}};
 else if(name==='data')value={rows,categories:[{name:'输入输出',count:3,children:[]}],token:'filter-fixture',today:now.slice(0,10)};
 else if(name==='workspace')value=workspace();
 else if(name==='insights')value={summary:{totalSolved:0},growth:{level:11,confirmed:true,authority:{owner,epoch:'filter-fixture',revision:++revision},currentLevelXp:0,nextLevelXp:2200,totalXp:0},knowledge:[],recommendations:[],activity:[],assessment:{},dailyTasks:{tasks:[]}};
 else if(name==='preferences'){if(request.method()==='POST')preferences=request.postDataJSON().preferences;value={preferences,updatedAt:now};}
 else if(name==='training/clear'){
  assert.equal(request.method(),'POST');assert.equal(request.headers()['x-tb-token'],'filter-fixture');assert.deepEqual(request.postDataJSON(),{});
  assert(!pending&&!activeContest);writes.push({path:name,body:request.postDataJSON()});const cleared=training.length;training=[];value={cleared,workspace:workspace()};
 }
 else if(name==='training-lists')value={lists:[]};
 else if(name==='templates')value={templates:[]};
 else if(name==='training-list-likes')value={likes:[]};
 else if(name==='contest')value={contest:activeContest};
 else if(name==='software-update')value={currentVersion:'1.4.31',status:'current',autoCheck:false,canInstall:false};
 else if(name==='content-update')value={status:'current',revision:0};
 else if(name==='contest-calendar')value={contests:[],providers:[],refreshing:false};
 else if(name==='browser-preparation')value={available:false};
 else if(name==='social')value={available:false,notifications:[],likes:[],unread:0};
 else if(name==='goals')value={goals:[],contestPlan:{contests:[]}};
 else if(name==='inbox')value={pending:0,errors:[]};
 else if(name==='hub')value=null;
 else if(name==='desktop/fullscreen')value={available:false,fullscreen:false};
 else if(name==='usage')value={days:[],totalSeconds:0};
 else if(name==='submissions')value={submissions:[],groups:[],total:0,page:1,pages:1};
 else{unknown.push(name);value={};}
 await route.fulfill({json:value});
});
await page.route(/^https?:\/\/(?!127\.0\.0\.1)(?!localhost)/,route=>{external.push(route.request().url());return route.abort();});
const base=`http://127.0.0.1:${vite.httpServer.address().port}`,nav=()=>page.getByRole('navigation',{name:'主导航'});
const load=async()=>{await page.goto(base);await page.waitForFunction(()=>document.querySelector('.profile-level-number')?.textContent==='11');await page.getByRole('button',{name:'筛选题目',exact:true}).waitFor();};
const output='tests/screenshots/filter-toolbar';await mkdir(output,{recursive:true});
const report={ok:false,actualApp:true,geometry:[],realAccountsUsed:false,realOfficialSubmissions:0};
try{
 await load();
 const clear=()=>page.getByRole('button',{name:'清空我的训练',exact:true});
 const confirm=()=>page.getByRole('alertdialog',{name:'清空我的训练确认',exact:true});
 assert.equal(await clear().innerText(),'','The clear action is an icon in the shared toolbar');
 const placement=await clear().evaluate(button=>{const a=document.querySelector('.filter-trigger').getBoundingClientRect(),b=button.getBoundingClientRect();return {gap:b.left-a.right,sameLine:Math.abs(a.top+a.height/2-b.top-b.height/2)<1};});
 assert(placement.sameLine&&placement.gap>=0&&placement.gap<=16,'Clear is immediately to the right of the filter trigger');
 for(const [pageName,label] of [['我的训练','筛选题目'],['题库','筛选题目'],['比赛','筛选比赛']]){
  await nav().getByRole('button',{name:pageName,exact:true}).click();
  if(pageName!=='我的训练')assert.equal(await clear().count(),0,'Only the personal training workspace exposes its clear action');
  const trigger=page.getByRole('button',{name:label,exact:true});await trigger.click();
  const popup=page.getByRole('dialog',{name:label,exact:true});await popup.waitFor();
  assert.equal(await popup.getByRole('button',{name:'清空我的训练',exact:true}).count(),0,'The filter menu has no destructive action');
  for(const theme of ['dark','light'])for(const font of [15,22])for(const width of [2048,1440,800,430]){
   await page.setViewportSize({width,height:960});
   await page.evaluate(({theme,font})=>{document.documentElement.dataset.theme=theme;document.documentElement.style.setProperty('--ui-font-size',font+'px');document.documentElement.style.fontSize=font+'px';window.dispatchEvent(new Event('resize'));},{theme,font});
   await page.waitForFunction(()=>{const popup=document.querySelector('.filter-popover'),trigger=document.querySelector('.filter-trigger');if(!popup||!trigger)return false;const p=popup.getBoundingClientRect(),a=trigger.getBoundingClientRect();return Math.abs(p.left-Math.max(12,Math.min(a.left,innerWidth-p.width-12)))<1&&Math.abs(p.top-a.bottom-8)<1;});
   const geometry=await popup.evaluate(node=>{
    const rect=n=>{const r=n.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height};};
    const selects=[...node.querySelectorAll('select')].map(select=>{const style=getComputedStyle(select),canvas=document.createElement('canvas'),context=canvas.getContext('2d');context.font=style.font;return {...rect(select),text:select.selectedOptions[0].textContent,textWidth:context.measureText(select.selectedOptions[0].textContent).width,padding:parseFloat(style.paddingLeft)+parseFloat(style.paddingRight),font:style.font};});
    const range=node.querySelector('.difficulty-filter'),difficulty=range?{label:rect(range.querySelector(':scope>span')),values:rect(range.querySelector('.difficulty-range-values')),track:rect(range.querySelector('.difficulty-range-track'))}:null;
    return {popup:rect(node),selects,difficulty,overflow:node.scrollWidth>node.clientWidth};
   });
   assert(geometry.popup.left>=0&&geometry.popup.right<=width+.5&&geometry.popup.bottom<=960+.5&&!geometry.overflow,JSON.stringify({pageName,width,font,geometry}));
   for(const select of geometry.selects){
    assert(Math.abs(select.height-36)<1&&select.left>=geometry.popup.left&&select.right<=geometry.popup.right+.5);
    const space=select.width-select.padding-select.textWidth;
    assert(space>=-1&&space<=20,'Selected text fits without a large empty arrow area: '+JSON.stringify({pageName,width,font,select,space}));
   }
   if(geometry.difficulty){const d=geometry.difficulty;assert(Math.abs((d.label.top+d.label.bottom)/2-(d.values.top+d.values.bottom)/2)<1,'Difficulty label and both numeric endpoints share one row');assert(d.track.top>=d.values.bottom-.5&&d.track.top-d.values.bottom<=4,'The slider directly follows the compact numeric row');}
   report.geometry.push({pageName,width,font,theme,...geometry});
   if(font===22&&(width===1440||width===430))await page.screenshot({path:`${output}/${pageName}-${theme}-${width}.png`,animations:'disabled'});
  }
  if(pageName==='比赛'){
   await popup.getByLabel('比赛训练情况',{exact:true}).click();
   await page.getByRole('listbox',{name:'比赛训练情况',exact:true}).getByRole('option',{name:'尚未全部通过',exact:true}).click();
   assert.equal(await popup.getByLabel('比赛训练情况',{exact:true}).inputValue(),'unfinished','The shared presentation keeps all existing filter choices and native change behavior');
  }
  await page.keyboard.press('Escape');await popup.waitFor({state:'detached'});
 }
 await page.setViewportSize({width:1440,height:960});await nav().getByRole('button',{name:'我的训练',exact:true}).click();
 await clear().click();await confirm().waitFor();assert.equal(writes.length,0,'Opening confirmation never clears training');
 await confirm().getByRole('button',{name:'取消',exact:true}).click();assert.equal(writes.length,0);assert.equal(training.length,2);
 await clear().click();await confirm().waitFor();await page.keyboard.press('Escape');assert.equal(await confirm().count(),0);assert.equal(writes.length,0);
 await clear().click();await confirm().waitFor();await confirm().getByRole('button',{name:'确认清空 2 道训练题',exact:true}).click();await confirm().waitFor({state:'detached'});
 assert.equal(writes.length,1);assert.equal(training.length,0);assert.equal(await clear().count(),0,'The empty training page has no further clear action');assert.deepEqual(preserved,{draft:'int main(){return 0;}',history:['historical-official-receipt']});
 training=structuredClone(originals);pending=1;await load();assert(await clear().isDisabled(),'Pending judging keeps clear disabled');
 pending=0;activeContest={id:'filter-contest',name:'隔离中的比赛',status:'running',slots:[],duration:120,deadline:new Date(Date.now()+3600000).toISOString()};await load();assert(await clear().isDisabled(),'A running contest keeps clear disabled');
 assert.equal(writes.length,1);assert.deepEqual(unknown,[]);assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 Object.assign(report,{ok:true,anchorResize:true,compactSelectedText:true,oneRowDifficulty:true,iconBesideFilter:true,clearOnlyPersonalTraining:true,cancelAndEscapeSafe:true,confirmedClearOnce:true,pendingAndContestProtected:true,preservedDraftAndHistory:true});
 console.log(JSON.stringify({ok:true,geometryCases:report.geometry.length,clearWrites:writes.length}));
}catch(error){report.failure=error.message;await page.screenshot({path:output+'/failure.png'}).catch(()=>{});throw error;}
finally{await writeFile(output+'/report.json',JSON.stringify({...report,errors,unknown,external,writes},null,2)+'\n');await browser.close();await vite.close();}
