import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';
import {createServer} from 'vite';
const frontend=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),output=path.join(frontend,'tests/screenshots/template-first-frame');await mkdir(output,{recursive:true});
const replayOld=process.env.TB_TEMPLATE_REPLAY_OLD==='1';
const vite=await createServer({root:frontend,configFile:path.join(frontend,'vite.config.js'),server:{host:'127.0.0.1',port:0,watch:null},plugins:[{name:'isolated-template-first-frame',enforce:'pre',
 configureServer(server){server.middlewares.use((request,response,next)=>{if(!request.url?.startsWith('/api/'))return next();response.writeHead(410,{'Content-Type':'application/json'});response.end(JSON.stringify({error:'Isolated template fixture; live API disabled'}));});},
 transform(source,id){if(!replayOld||!id.replaceAll('\\','/').endsWith('/src/pages/TemplatesPage.jsx'))return;return source.replace('useLayoutEffect(()=>{onActiveChange?.(Boolean(selected))','useEffect(()=>{onActiveChange?.(Boolean(selected))').replace('const open=item=>{onActiveChange?.(true);','const open=item=>{').replace('const back=()=>{onActiveChange?.(false);','const back=()=>{').replace('const create=source=>{onActiveChange?.(true);','const create=source=>{');},
}]});await vite.listen();const base=`http://127.0.0.1:${vite.httpServer.address().port}`;
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),errors=[],unknown=[],external=[],measurements=[];
const owner='c3e5d799-502a-4b4f-a864-a342f7db419e',now=new Date().toISOString();let revision=0;
const template={id:'builtin:window-extrema',title:'单调队列：滑动窗口最值',category:'数据结构',language:'cpp17',builtin:true,
 code:'#include <bits/stdc++.h>\nusing namespace std;\nusing ll = long long;\nvector<ll> minimums(const vector<ll>& a,int width) {\n    deque<int> pending;\n    return {};\n}\n',contestCode:'#include <bits/stdc++.h>\nusing namespace std;\nusing ll = long long;\n',notes:'记录有效窗口中的候选下标。',example:'int main() { return 0; }',practiceIds:[]};
const workspace={training:[],sets:[],contests:[],activeContest:null,summary:{total:0,accepted:0,attempts:0,due:0,pending:0,todayAccepted:0},now};
const report={ok:false,actualApp:true,replayOld,readOnlyFixtures:true,cases:measurements};
try{
 for(const [index,viewport] of [{width:2048,height:1152},{width:1294,height:826},{width:960,height:720},{width:430,height:850}].entries()){
  const context=await browser.newContext({viewport,reducedMotion:index===3?'reduce':'no-preference'}),page=await context.newPage();page.setDefaultTimeout(12000);
  let preferences={theme:index%2?'light':'dark',accent:'teal',fontSize:index===3?22:15,onboardingGuideVersion:999,onboardingCompleted:true,onboardingUnlockedPages:['mine','training-lists','library','rankings','competitions','mock','paths','templates','lectures','growth','activity','records','settings'],levelNoticeVersion:1,levelNoticeSeen:100,levelNoticePending:0,navSchema:2};
  page.on('pageerror',error=>errors.push(error.message));
  await page.addInitScript(()=>{
   const native=Element.prototype.getBoundingClientRect;window.templateMeasurements=[];window.templateFrames=[];window.templateWatching=false;
   const snapshot=()=>{const root=document.querySelector('.templates-page.template-detail-open'),shell=document.querySelector('.app-shell');if(!root)return null;const r=native.call(root),visible=selector=>{const n=document.querySelector(selector);return Boolean(n&&getComputedStyle(n).display!=='none'&&native.call(n).height>0);};return {left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height,focused:Boolean(shell?.classList.contains('template-focus')),sidebar:visible('.sidebar'),topbar:visible('.topbar'),status:visible('.app-statusbar')};};
   Element.prototype.getBoundingClientRect=function(...args){const result=native.apply(this,args);if(window.templateWatching&&this.closest?.('.template-code')&&window.templateMeasurements.length<200){const value=snapshot();if(value)window.templateMeasurements.push(value);}return result;};
   window.startTemplateWatch=()=>{window.templateMeasurements=[];window.templateFrames=[];window.templateWatching=true;const frame=()=>{if(!window.templateWatching)return;const value=snapshot();if(value&&window.templateFrames.length<30)window.templateFrames.push(value);requestAnimationFrame(frame);};requestAnimationFrame(frame);};
   window.finishTemplateWatch=()=>{window.templateWatching=false;return {measurements:window.templateMeasurements,frames:window.templateFrames};};
  });
  await page.route('**/api/**',async route=>{
   const name=new URL(route.request().url()).pathname.slice('/api/'.length);let value;
   if(name==='account')value={required:true,authenticated:true,token:'isolated',account:{userId:owner,loginId:'isolated',nickname:'模板测试'}};
   else if(name==='preferences'){if(route.request().method()==='POST')preferences=route.request().postDataJSON().preferences;value={preferences,updatedAt:now};}
   else if(name==='data')value={rows:[],categories:[],token:'isolated',today:now.slice(0,10)};
   else if(name==='workspace')value=workspace;
   else if(name==='insights')value={summary:{totalSolved:0},growth:{level:12,confirmed:true,authority:{owner,epoch:'template-first-frame',revision:++revision},tier:'黑铁',currentLevelXp:0,nextLevelXp:2400,totalXp:8000},knowledge:[],recommendations:[],activity:[],assessment:{},dailyTasks:{tasks:[]}};
   else {const fixed={templates:{templates:[template]},'training-lists':{lists:[]},'training-list-likes':{likes:[]},'software-update':{currentVersion:'1.4.31',status:'current',autoCheck:false,canInstall:false},'content-update':{revision:0,status:'current'},'contest-calendar':{contests:[],providers:[],refreshing:false},'browser-preparation':{available:false},social:{notifications:[],likes:[],unread:0},goals:{goals:[],contestPlan:{contests:[]}},inbox:{pending:0,errors:[]},hub:null,'desktop/fullscreen':{available:false,fullscreen:false},usage:{days:[],totalSeconds:0}};if(!Object.hasOwn(fixed,name)){unknown.push(name);return route.fulfill({status:410,json:{error:'Unknown isolated template route'}});}value=fixed[name];}
   await route.fulfill({json:value});
  });
  await page.route('**/*',route=>{const url=new URL(route.request().url());if(url.pathname.startsWith('/api/'))return route.fallback();if(url.origin===base||['data:','blob:'].includes(url.protocol))return route.continue();external.push(url.origin+url.pathname);return route.abort();});
  const assertOpening=async(action,kind)=>{await page.evaluate(()=>window.startTemplateWatch());await action();await page.locator('.template-detail .cm-editor').waitFor();await page.waitForFunction(()=>window.templateMeasurements.length>0&&window.templateFrames.length>=3);const captured=await page.evaluate(()=>window.finishTemplateWatch());assert(captured.measurements.length>0,'The real editor measured its first layout');for(const [source,values] of Object.entries(captured))for(const value of values){assert(value.focused&&!value.sidebar&&!value.topbar&&!value.status,`${kind} ${source}: detail preceded final shell state ${JSON.stringify(value)}`);assert(Math.abs(value.left)<=1&&Math.abs(value.top)<=1&&Math.abs(value.right-viewport.width)<=1&&Math.abs(value.bottom-viewport.height)<=1,`${kind} ${source}: intermediate size ${JSON.stringify(value)}`);}measurements.push({viewport,theme:preferences.theme,fontSize:preferences.fontSize,kind,editorMeasurements:captured.measurements.length,paintedFrames:captured.frames.length,firstMeasurement:captured.measurements[0],firstFrame:captured.frames[0]});};
  const nav=()=>page.getByRole('navigation',{name:'主导航'}),back=()=>page.getByRole('button',{name:'返回模板',exact:true}).click();
  const leave=async()=>{await page.keyboard.press('Control+k');await page.getByRole('dialog',{name:'快捷操作'}).getByRole('button',{name:/^打开题库(?:\s|$)/}).click();await nav().waitFor();};
  await page.goto(base);await page.waitForFunction(()=>document.querySelector('.profile-level-number')?.textContent==='12');await nav().getByRole('button',{name:'模板',exact:true}).click();await page.getByRole('button',{name:'打开模板 '+template.title,exact:true}).waitFor();
  await assertOpening(()=>page.getByRole('button',{name:'打开模板 '+template.title,exact:true}).click(),'open');
  await page.getByRole('button',{name:'讲解版',exact:true}).click();assert.equal(await page.getByRole('button',{name:'竞赛版',exact:true}).count(),1);await back();await nav().waitFor();assert.equal(await page.locator('.app-shell.template-focus').count(),0);
  await assertOpening(()=>page.getByRole('button',{name:'打开模板 '+template.title,exact:true}).click(),'reopen');assert.equal(await page.getByRole('button',{name:'讲解版',exact:true}).count(),1);
  await leave();await assertOpening(()=>nav().getByRole('button',{name:'模板',exact:true}).click(),'restore');
  await page.keyboard.press('Escape');await page.getByRole('button',{name:'新建模板',exact:true}).waitFor();await assertOpening(()=>page.getByRole('button',{name:'新建模板',exact:true}).click(),'new');
  await page.getByRole('textbox',{name:'模板名称',exact:true}).fill('隔离草稿保留');await leave();await assertOpening(()=>nav().getByRole('button',{name:'模板',exact:true}).click(),'restore-draft');assert.equal(await page.getByRole('textbox',{name:'模板名称',exact:true}).inputValue(),'隔离草稿保留');
  await page.screenshot({path:path.join(output,`${viewport.width}-${preferences.theme}.png`)});await back();assert.equal(await page.locator('.app-shell.template-focus').count(),0);await context.close();
 }
 assert.deepEqual(errors,[]);assert.deepEqual(unknown,[]);assert.deepEqual(external,[]);report.ok=true;
 console.log(`PASS real App template first editor measurement and painted frame; ${measurements.length} openings, four widths, return/reopen/saved detail/new/draft restore; no external requests`);
}finally{report.errors=errors;report.unknown=unknown;report.external=external;await writeFile(path.join(output,replayOld?'old-layout-proof.json':'report.json'),JSON.stringify(report,null,2));await browser.close();await vite.close();}
