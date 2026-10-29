import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';
import {createServer} from 'vite';

const frontend=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const output=path.join(frontend,'tests/screenshots/next-actions');
await mkdir(output,{recursive:true});
const verified={platform:'Codeforces',difficultySource:'Codeforces 官方',difficultyConfidence:'HIGH'};
const rows=[
  ...['A','A2','A3'].map(id=>({...verified,id,title:'已独立通过 '+id,accepted:true,
    tags:['数组','输入输出'],difficulty:1000,catalogContentReady:true})),
  ...['B','C','D','E'].map(id=>({...verified,id,title:id==='B'?'待复习的前缀和练习':'基础练习 '+id,
    tags:['输入输出','排序'],knowledge:'输入输出',difficulty:1000,catalogContentReady:true})),
  {...verified,id:'F',title:'排序进阶挑战',tags:['排序'],difficulty:1500,catalogContentReady:true},
];
const lists=[{id:'basics',title:'顺序结构',available:true,categories:[],
  problems:['B','C','D'].map(problemId=>({problemId}))}];
const templates=[{id:'sort-template',title:'排序模板',builtin:true,tags:['排序'],practiceIds:['E']}];

// Render the production component and its real recommendation model. Only the
// small public catalog/account evidence inputs and navigation callbacks are fixtures.
const fixture=`
import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import NextActions from '/src/components/NextActions.jsx';
const rows=${JSON.stringify(rows)};
const api=async endpoint=>{
  const response=await fetch('/api/'+endpoint);
  if(!response.ok)throw new Error('Isolated fixture request failed: '+endpoint);
  const value=await response.json();window.fixtureApiReady=(window.fixtureApiReady||0)+1;return value;
};
window.fixtureEvents=[];
function App(){
  const [state,setState]=useState({});window.fixtureUpdate=setState;
  const evidence=state.proved?['A','A2','A3'].map((problemId,index)=>({problemId,
    date:new Date(Date.now()-(index+1)*86400000).toISOString(),solved:true,weight:1,failures:0,difficulty:1000})):[];
  return React.createElement('header',null,
    React.createElement('input',{'aria-label':'搜索'}),
    React.createElement(NextActions,{
      rows,training:[{...rows.find(row=>row.id==='B'),queue:'review',reviewDueAt:new Date(Date.now()-86400000).toISOString()}],
      insights:{assessment:{model:{method:'rasch-practice-evidence-v2'},qualified:true,abilityScore:1300,evidence}},
      prefs:{},api,availablePages:state.pages||['mine','library','training-lists','paths','templates','mock'],
      activeContest:state.contest,suspended:state.suspended,reviewPlan:state.reviewPlan,
      onOpenChange:value=>window.fixtureAdviceOpen=value,
      onTrain:id=>window.fixtureEvents.push({train:id}),
      onNavigate:item=>window.fixtureEvents.push({navigate:item.kind,id:item.id}),
    }),React.createElement('span',{className:'fixture-metrics'},'AC: 98'));
}
const root=createRoot(document.getElementById('root'));
window.fixtureUnmount=()=>root.unmount();root.render(React.createElement(App));
window.fixtureNextActions=true;
`;
const html=`<!doctype html><html><head><meta charset="utf-8"><style>
:root{font-size:15px;--panel:#191d25;--text:#e3e8ed;--muted:#a8b2c1;--line:#35414e;--accent:#72d3be;--accent-soft:#263e3e}
*{box-sizing:border-box}body{margin:0;background:#11151b;color:var(--text)}
button,input{font:inherit;color:inherit;border:0;background:none;cursor:pointer}
header{display:flex;gap:12px;align-items:center;padding:10px}
header>input{flex:1 1 250px;min-width:30px;background:#232730;height:40px}
.fixture-metrics{flex:0 0 160px}
.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}
@media(max-width:600px){.fixture-metrics{flex-basis:65px}}
</style></head><body><div id="root"></div><button id="outside">外部按钮</button>
<script type="module" src="/@id/virtual:next-actions.jsx"></script></body></html>`;
const vite=await createServer({
  root:frontend,configFile:path.join(frontend,'vite.config.js'),
  server:{host:'127.0.0.1',port:0,watch:null},
  plugins:[{
    name:'isolated-next-actions-fixture',
    configureServer(server){
      // Register before Vite's HTML fallback, so this never mounts the real App
      // or reaches its default API proxy.
      server.middlewares.use(async(request,response,next)=>{
        if(request.url!=='/fixture')return next();
        response.setHeader('Content-Type','text/html; charset=utf-8');
        response.end(await server.transformIndexHtml('/fixture',html));
      });
    },
    resolveId(id){if(id==='virtual:next-actions.jsx')return '\0virtual:next-actions.jsx';},
    load(id){if(id==='\0virtual:next-actions.jsx')return fixture;},
  }],
});
await vite.listen();
const base=`http://127.0.0.1:${vite.httpServer.address().port}`;
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const errors=[],unknown=[],requests=[];
const preparePage=async page=>{
  page.setDefaultTimeout(10000);
  page.on('pageerror',error=>errors.push(error.message));
  // Every API request is intercepted, including unknown paths. No request may
  // fall through to a live desktop, account service or original judge.
  await page.route('**/api/**',async route=>{
    const url=new URL(route.request().url());requests.push(url.pathname);
    const value=url.pathname==='/api/training-lists'?{lists}:url.pathname==='/api/templates'?{templates}:null;
    if(value)return route.fulfill({json:value});
    unknown.push(url.pathname);return route.fulfill({status:501,json:{error:'Unknown isolated fixture route'}});
  });
  await page.route('**/*',route=>{
    const url=new URL(route.request().url());
    if(url.pathname.startsWith('/api/'))return route.fallback();
    if(url.origin===base||['data:','blob:'].includes(url.protocol))return route.continue();
    unknown.push(url.origin+url.pathname);return route.abort();
  });
  await page.goto(base+'/fixture');
  await page.waitForFunction(()=>window.fixtureNextActions===true&&window.fixtureApiReady>=2);
};
const page=await browser.newPage({viewport:{width:1440,height:960}});
const report={ok:false,actualComponent:true,actualRecommendationModel:true,geometry:[]};
let phase='startup';
try{
  await preparePage(page);
  const root=page.locator('.next-actions');
  const popup=()=>page.getByRole('region',{name:'推荐任务与依据'});
  const toggle=()=>page.locator('.next-actions-toggle');
  const hover=async()=>{await page.mouse.move(20,700);await root.hover();await popup().waitFor();};
  const lastAction=()=>page.evaluate(()=>window.fixtureEvents.at(-1));

  phase='default-and-hover';
  await root.waitFor();
  assert.equal(await page.locator('[data-recommendation]').count(),1,'Default chrome shows a single actionable recommendation');
  await hover();
  assert.match(await page.locator('.next-actions-reason').innerText(),/1 道.*到期/);
  const listAction=page.getByRole('button',{name:'开始基础题单 输入输出与顺序结构',exact:true});
  await listAction.waitFor();
  const bounds=await root.boundingBox();
  await page.mouse.move(bounds.x+20,bounds.y+bounds.height+4);
  await page.waitForTimeout(250);
  assert.equal(await popup().count(),1,'Moving through the visible gap does not dismiss the advice');
  await listAction.click();
  assert.equal((await lastAction()).navigate,'list');
  assert.equal(await popup().count(),0);
  await page.getByRole('button',{name:'开始间隔复习 待复习的前缀和练习',exact:true}).click();
  assert.deepEqual(await lastAction(),{train:'B'});

  phase='keyboard-and-outside';
  await page.mouse.move(800,500);await toggle().focus();await popup().waitFor();
  await page.keyboard.press('ArrowDown');
  await page.waitForFunction(()=>document.activeElement?.dataset.recommendation==='list');
  for(const key of ['ArrowUp','Home','End']){
    await page.keyboard.press(key);assert.equal(await listAction.evaluate(node=>node===document.activeElement),true);
  }
  await page.keyboard.press('Escape');
  assert.equal(await popup().count(),0);assert.equal(await toggle().evaluate(node=>node===document.activeElement),true);
  await page.keyboard.press('Enter');await popup().waitFor();
  await page.locator('#outside').click();assert.equal(await popup().count(),0);
  await toggle().click();await popup().waitFor();await toggle().click();assert.equal(await popup().count(),0);

  phase='evidence-based-course';
  await page.evaluate(()=>window.fixtureUpdate({proved:true,pages:['mine','library','paths','templates','mock']}));
  await hover();
  await page.getByRole('button',{name:'开始算法实验室 排序基础',exact:true}).click();
  assert.deepEqual(await lastAction(),{navigate:'course',id:'sorting-basics'});
  await page.evaluate(()=>window.fixtureUpdate({}));

  phase='viewport-and-motion';
  for(const font of [15,22])for(const width of [1440,960,430]){
    await page.setViewportSize({width,height:800});
    await page.evaluate(size=>document.documentElement.style.fontSize=size+'px',font);
    await hover();
    const box=await popup().boundingBox();
    assert(box.x>=0&&box.x+box.width<=width+.5&&box.y+box.height<=800+.5,JSON.stringify({font,width,box}));
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    report.geometry.push({width,font,bounds:box});
    await page.screenshot({path:path.join(output,`${width}-${font}.png`)});
    await page.keyboard.press('Escape');
  }
  await page.emulateMedia({reducedMotion:'reduce'});await hover();
  assert.equal(await page.locator('.next-actions-toggle svg').evaluate(node=>getComputedStyle(node).transitionDuration),'0s');

  phase='active-contest-and-suspended';
  await page.evaluate(()=>window.fixtureUpdate({contest:{id:'current',name:'正在进行的试卷'}}));
  const contest=page.getByRole('button',{name:'开始继续比赛 正在进行的试卷',exact:true});await contest.waitFor();
  await hover();assert.equal(await page.locator('.next-actions-item').count(),0);
  assert.match(await page.locator('.next-actions-reason').innerText(),/已有正在进行的模拟赛/);
  await page.evaluate(()=>{
    window.fixtureUpdate({suspended:true});window.fixtureEscapes=0;
    document.addEventListener('keydown',event=>{if(event.key==='Escape')window.fixtureEscapes++;});
  });
  await page.waitForFunction(()=>document.querySelector('.next-actions-toggle').disabled);
  assert.equal(await popup().count(),0);assert.equal(await page.evaluate(()=>window.fixtureAdviceOpen),false);
  await page.mouse.move(20,700);await root.hover();assert.equal(await popup().count(),0);
  await page.keyboard.press('Escape');
  assert.equal(await page.evaluate(()=>window.fixtureEscapes),1,'Suspended advice must leave another dialog in control of Escape');

  phase='touch';
  const touchContext=await browser.newContext({hasTouch:true,viewport:{width:430,height:800}});
  try{
    const touch=await touchContext.newPage();await preparePage(touch);
    await touch.getByRole('button',{name:'展开下一步推荐任务',exact:true}).tap();
    await touch.locator('.next-actions-popover').waitFor();
    await touch.touchscreen.tap(425,790);assert.equal(await touch.locator('.next-actions-popover').count(),0);
  }finally{await touchContext.close();}

  phase='open-change-and-unmount';
  await page.evaluate(()=>window.fixtureUpdate({}));
  await page.waitForFunction(()=>!document.querySelector('.next-actions-toggle').disabled);
  await hover();await page.waitForFunction(()=>window.fixtureAdviceOpen===true);
  await page.evaluate(()=>window.fixtureUnmount());
  assert.equal(await page.evaluate(()=>window.fixtureAdviceOpen),false);
  assert.equal(await page.locator('.next-actions-popover').count(),0);
  assert.deepEqual(errors,[]);assert.deepEqual(unknown,[]);
  assert(requests.includes('/api/training-lists')&&requests.includes('/api/templates'));
  Object.assign(report,{ok:true,hoverBridge:true,independentNavigation:true,keyboard:true,outsideClose:true,
    touch:true,suspended:true,openChange:true,unmountCloses:true,reducedMotion:true,realOfficialSubmissionsSent:0});
  console.log(JSON.stringify({ok:true,geometryCases:report.geometry.length,report:path.join(output,'report.json')}));
}catch(error){
  report.failure={phase,message:error.message};
  await page.screenshot({path:path.join(output,'failure.png')}).catch(()=>{});throw error;
}finally{
  await writeFile(path.join(output,'report.json'),JSON.stringify({...report,errors,unknown,requests},null,2)+'\n');
  await browser.close();await vite.close();
}
