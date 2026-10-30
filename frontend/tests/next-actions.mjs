import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';
import {createServer} from 'vite';

const frontend=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const output=path.join(frontend,'tests/screenshots/next-actions');
await mkdir(output,{recursive:true});
const verified={platform:'Codeforces',difficultySource:'Codeforces 官方',difficultyConfidence:'HIGH',solutionAvailable:true,solutionState:'available'};
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
:root{font-size:15px;--panel:#191d25;--panel-base:#191d25;--text:#e3e8ed;--muted:#a8b2c1;--line:#35414e;--accent:#72d3be;--accent-soft:#263e3e}
:root[data-theme=light]{--panel-base:#f7f9fc;--text:#172431;--muted:#526170;--line:#cad4de;--accent:#267a6c;--accent-soft:#dfefe9}
*{box-sizing:border-box}body{margin:0;background:#11151b;color:var(--text)}
button,input{font:inherit;color:inherit;border:0;background:none;cursor:pointer}
header{display:flex;gap:12px;align-items:center;padding:10px}
header>input{flex:1 1 250px;min-width:30px;background:#232730;height:40px}
.fixture-metrics{flex:0 0 160px}
.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}
.fixture-underlay{display:none;position:fixed;inset:90px 0 0;z-index:110;background:repeating-linear-gradient(0deg,#365b5b 0 1px,#191d25 1px 24px);color:white;font-size:22px}
body[data-underlay=true] .fixture-underlay{display:block}
#outside{position:relative;z-index:111}
@media(max-width:600px){.fixture-metrics{flex-basis:65px}}
</style></head><body><div id="root"></div><button id="outside">外部按钮</button><div class="fixture-underlay">Underlying page content / 下层题单内容</div>
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
  const primary=()=>page.locator('.next-actions-primary');
  const hover=async()=>{await page.mouse.move(20,700);await root.hover();await popup().waitFor();};
  const lastAction=()=>page.evaluate(()=>window.fixtureEvents.at(-1));

  phase='default-and-hover';
  await root.waitFor();
  assert.equal(await page.locator('[data-recommendation]').count(),1,'Default chrome shows a single actionable recommendation');
  assert.equal(await page.locator('.next-actions-toggle,.next-actions .lucide-chevron-down').count(),0,'The recommendation itself handles expansion; no separate arrow button remains');
  await hover();
  assert.equal(await page.locator('.next-actions-primary small').count(),0,'The top task has no next-step/category label');
  assert.equal(await page.locator('.next-actions-primary .lucide-arrow-right').count(),0,'The top task has no trailing right arrow');
  assert.equal(await root.evaluate(node=>getComputedStyle(node).borderWidth),'0px','The complete recommendation control has no outer frame');
  assert.equal(await page.locator('.next-actions-reason').count(),0,'Reasons are tooltips, not a second information panel');
  assert(!/优先推荐的原因|根据当前学习记录|接下来还可以/.test(await popup().innerText()));
  const allTasks=popup().locator('.next-actions-item');
  assert.equal(await allTasks.count(),3,'The menu contains the current foundation list and two alternatives, without repeating the primary review');
  assert.equal(await popup().getByRole('button',{name:'开始间隔复习 待复习的前缀和练习',exact:true}).count(),0);
  assert(await allTasks.count()<=5,'The limit of six includes the primary task');
  const motion=await popup().locator('li').evaluateAll(nodes=>nodes.map(node=>{
    const style=getComputedStyle(node);return {duration:parseFloat(style.animationDuration),delay:parseFloat(style.animationDelay),iterations:style.animationIterationCount};
  }));
  assert(motion.every((item,index)=>item.iterations==='1'&&item.duration>0&&item.duration+item.delay<=.3&&(index===0||item.delay>motion[index-1].delay)),'Rows enter with finite short staggered animation, completing within 300ms');
  for(const task of await allTasks.all()){
    const description=await task.getAttribute('aria-describedby');
    assert(description&&await page.locator(`[id="${description}"]`).count()===1);
    const reason=await page.locator(`[id="${description}"]`).innerText();
    assert(reason.length>20);assert((await task.getAttribute('title')).includes(reason));
    assert.equal(await task.locator('small').count(),0);
    assert(!(await task.innerText()).includes(reason),'A long recommendation reason is not visibly rendered');
  }
  assert.match(await page.locator('.next-actions-primary').getAttribute('title'),/1 道.*到期/);
  const listAction=popup().getByRole('button',{name:'开始基础题单 输入输出与顺序结构',exact:true});
  await listAction.waitFor();
  const bounds=await root.boundingBox();
  await page.mouse.move(bounds.x+20,bounds.y+bounds.height+4);
  await page.waitForTimeout(250);
  assert.equal(await popup().count(),1,'Moving through the visible gap does not dismiss the advice');
  await listAction.hover();await page.waitForTimeout(200);
  assert.equal(await popup().count(),1,'Hovering a real expanded task keeps the list open beyond the leave delay');
  await page.mouse.move(20,700);
  await popup().waitFor({state:'detached',timeout:180});
  await hover();
  await listAction.click();
  assert.equal((await lastAction()).navigate,'list');
  assert.equal(await popup().count(),0);
  await page.getByRole('button',{name:'开始间隔复习 待复习的前缀和练习',exact:true}).click();
  assert.deepEqual(await lastAction(),{train:'B'});

  phase='keyboard-and-outside';
  await page.mouse.move(800,500);await page.locator('#outside').focus();await primary().focus();await popup().waitFor();
  await page.keyboard.press('ArrowDown');
  await page.waitForFunction(()=>document.activeElement?.dataset.recommendation==='list');
  await page.waitForTimeout(200);
  assert.equal(await popup().count(),1,'Keyboard focus moving within the component keeps the menu open while the pointer is elsewhere');
  assert(await allTasks.first().evaluate(node=>getComputedStyle(node).color===getComputedStyle(node.querySelector('svg')).color),'The focused task uses the accent color while keeping its borderless appearance');
  await page.keyboard.press('ArrowDown');assert.equal(await allTasks.nth(1).evaluate(node=>node===document.activeElement),true);
  await page.keyboard.press('End');assert.equal(await allTasks.last().evaluate(node=>node===document.activeElement),true);
  await page.keyboard.press('Home');assert.equal(await allTasks.first().evaluate(node=>node===document.activeElement),true);
  await page.keyboard.press('ArrowUp');assert.equal(await allTasks.last().evaluate(node=>node===document.activeElement),true);
  await page.keyboard.press('ArrowDown');assert.equal(await allTasks.first().evaluate(node=>node===document.activeElement),true);
  await page.keyboard.press('Escape');
  assert.equal(await popup().count(),0);assert.equal(await primary().evaluate(node=>node===document.activeElement),true);
  const beforeEnter=await page.evaluate(()=>window.fixtureEvents.length);
  await page.keyboard.press('Enter');assert.deepEqual(await lastAction(),{train:'B'});
  assert.equal(await page.evaluate(()=>window.fixtureEvents.length),beforeEnter+1,'Enter on the primary recommendation enters that task directly');
  assert.equal(await popup().count(),0);
  await primary().press('ArrowUp');await popup().waitFor();
  await page.waitForFunction(()=>{const tasks=[...document.querySelectorAll('.next-actions-flyout .next-actions-item')];return tasks.length>0&&tasks.at(-1)===document.activeElement;});
  assert.equal(await allTasks.last().evaluate(node=>node===document.activeElement),true,'ArrowUp on the primary opens the final menu task');
  await page.locator('#outside').click();assert.equal(await popup().count(),0);
  await hover();await primary().focus();await popup().waitFor();
  await page.mouse.move(20,700);await popup().waitFor({state:'detached',timeout:180});
  assert.equal(await primary().evaluate(node=>node===document.activeElement),true,'Mouse leave dismisses the menu even when the primary task retains focus');
  await hover();await primary().click();assert.deepEqual(await lastAction(),{train:'B'});assert.equal(await popup().count(),0);

  phase='evidence-based-course';
  await page.evaluate(()=>window.fixtureUpdate({proved:true,pages:['mine','library','paths','templates','mock']}));
  await hover();
  await page.getByRole('button',{name:'开始实验室 排序基础',exact:true}).click();
  assert.deepEqual(await lastAction(),{navigate:'course',id:'sorting-basics'});
  await page.evaluate(()=>window.fixtureUpdate({}));

  phase='viewport-and-motion';
  await page.evaluate(()=>document.body.dataset.underlay='true');
  for(const theme of ['dark','light'])for(const font of [15,22])for(const width of [2048,1440,1294,960,430]){
    await page.setViewportSize({width,height:800});
    await page.evaluate(theme=>document.documentElement.dataset.theme=theme,theme);
    await page.evaluate(size=>document.documentElement.style.fontSize=size+'px',font);
    await hover();
    const box=await popup().boundingBox();
    const trigger=await root.boundingBox();
    assert(Math.abs(box.x-trigger.x)<.75&&Math.abs(box.width-trigger.width)<.75,'The flyout aligns with the whole recommendation control: '+JSON.stringify({font,width,box,trigger}));
    assert(box.x>=0&&box.x+box.width<=width+.5&&box.y+box.height<=800+.5,JSON.stringify({font,width,box}));
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    const alignment=await page.evaluate(()=>{
      const first=document.querySelector('.next-actions-primary'),others=[...document.querySelectorAll('.next-actions-item')];
      return [first,...others].map(node=>{
        const icon=node.querySelector(':scope>svg'),text=node.querySelector('strong'),arrow=node.classList.contains('next-actions-item')?node.querySelector(':scope>svg:last-child'):null,style=getComputedStyle(node);
        return {iconX:icon&&getComputedStyle(icon).display!=='none'?icon.getBoundingClientRect().x:null,textX:text.getBoundingClientRect().x,
          arrowRight:arrow?.getBoundingClientRect().right??null,
          background:style.backgroundColor,borders:[style.borderTopWidth,style.borderRightWidth,style.borderBottomWidth,style.borderLeftWidth],shadow:style.boxShadow};
      });
    });
    for(const item of alignment){
      assert(item.borders.every(value=>parseFloat(value)===0)&&item.shadow==='none','Rows share the popup border and shadow: '+JSON.stringify({width,font,item}));
      assert(Math.abs(item.textX-alignment[0].textX)<.75,'Primary and expanded task text share the same horizontal start: '+JSON.stringify({width,font,alignment}));
      if(item.iconX!==null&&alignment[0].iconX!==null)assert(Math.abs(item.iconX-alignment[0].iconX)<.75,'Recommendation icons share the same horizontal start');
    }
    const arrows=alignment.filter(item=>item.arrowRight!==null);assert(arrows.every(item=>Math.abs(item.arrowRight-arrows[0].arrowRight)<.75),'Trailing arrows align');
    assert(await root.evaluate(node=>{
      const style=getComputedStyle(node);return style.backgroundColor==='rgba(0, 0, 0, 0)'&&parseFloat(style.borderWidth)===0&&style.boxShadow==='none';
    }),'The closed primary control retains its compact styling');
    const readability=await popup().evaluate(node=>{
      const style=getComputedStyle(node),item=node.querySelector('button'),r=item.getBoundingClientRect(),hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);
      return {background:style.backgroundColor,opacity:style.opacity,border:parseFloat(style.borderWidth),shadow:style.boxShadow,hit:node.contains(hit)};
    });
    assert.equal(readability.background,theme==='dark'?'rgb(25, 29, 37)':'rgb(247, 249, 252)','The menu has an opaque theme background');
    assert.equal(readability.opacity,'1');assert.equal(readability.border,1);assert.notEqual(readability.shadow,'none');assert(readability.hit,'The actual menu stays above the underlying page');
    report.geometry.push({width,font,theme,bounds:box,alignment,readability});
    await popup().locator('li').evaluateAll(nodes=>Promise.all(nodes.flatMap(node=>node.getAnimations().map(animation=>animation.finished))));
    await page.screenshot({path:path.join(output,`${width}-${font}-${theme}.png`)});
    await page.keyboard.press('Escape');
  }
  await page.evaluate(()=>{delete document.body.dataset.underlay;document.documentElement.dataset.theme='dark';});
  await page.emulateMedia({reducedMotion:'reduce'});await hover();
  assert(await popup().locator('li').evaluateAll(nodes=>nodes.every(node=>getComputedStyle(node).animationName==='none')));

  phase='active-contest-and-suspended';
  await page.evaluate(()=>window.fixtureUpdate({contest:{id:'current',name:'正在进行的试卷'}}));
  const contest=page.locator('.next-actions-primary');await contest.waitFor();
  await page.waitForFunction(()=>document.querySelector('.next-actions-primary')?.dataset.recommendation==='contest');
  await page.mouse.move(20,700);await root.hover();assert.equal(await popup().count(),0);
  assert.equal(await contest.getAttribute('aria-expanded'),null,'A single primary task has no empty dropdown');
  assert.match(await contest.getAttribute('title'),/已有正在进行的模拟赛/);
  await contest.click();
  assert.deepEqual(await lastAction(),{navigate:'contest',id:'current'});
  await page.evaluate(()=>{
    window.fixtureUpdate({suspended:true});window.fixtureEscapes=0;
    document.addEventListener('keydown',event=>{if(event.key==='Escape')window.fixtureEscapes++;});
  });
  await page.waitForFunction(()=>document.querySelector('.next-actions-primary')?.disabled===true);
  assert.equal(await popup().count(),0);assert.equal(await page.evaluate(()=>window.fixtureAdviceOpen),false);
  await page.mouse.move(20,700);await root.hover();assert.equal(await popup().count(),0);
  await page.keyboard.press('Escape');
  assert.equal(await page.evaluate(()=>window.fixtureEscapes),1,'Suspended advice must leave another dialog in control of Escape');

  phase='touch';
  const touchContext=await browser.newContext({hasTouch:true,viewport:{width:430,height:800}});
  try{
    const touch=await touchContext.newPage();await preparePage(touch);
    const touchPrimary=touch.locator('.next-actions-primary');
    await touchPrimary.tap();
    const touchPopup=touch.locator('.next-actions-popover');await touchPopup.waitFor();
    assert.deepEqual(await touch.evaluate(()=>window.fixtureEvents),[],'The first primary tap opens choices without entering a task');
    // A non-mouse pointer clears Chromium's sticky compatibility hover without
    // clicking outside. The following native mouseout models a touchscreen's
    // compatibility event; it must not acquire real-mouse dismissal semantics.
    const touchInput=await touch.context().newCDPSession(touch);
    await touchInput.send('Input.dispatchMouseEvent',{type:'mouseMoved',x:425,y:790,pointerType:'pen'});
    await touchInput.detach();
    const touchCompatibility=await touchPrimary.evaluate(node=>{
      const root=node.closest('.next-actions');
      const remaining=Math.max(0,...document.getAnimations().map(animation=>Number(animation.effect.getComputedTiming().endTime)-Number(animation.currentTime||0)).filter(Number.isFinite));
      const detail={rootHovered:root.matches(':hover'),primaryHovered:node.matches(':hover'),flyoutHovered:document.querySelector('.next-actions-flyout')?.matches(':hover'),at:performance.now(),settledAfter:performance.now()+remaining+80+16};
      node.dispatchEvent(new MouseEvent('mouseout',{bubbles:true,relatedTarget:document.body}));
      return detail;
    });
    console.log('TOUCH COMPATIBILITY',JSON.stringify(touchCompatibility));
    await touch.waitForFunction(settledAfter=>performance.now()>=settledAfter&&document.getAnimations().every(animation=>animation.playState==='finished'),touchCompatibility.settledAfter);
    assert.equal(await touchPopup.count(),1,'A compatibility mouseout after a touch tap must not close the menu during its entrance animation');
    await touchPopup.getByRole('button',{name:'开始基础题单 输入输出与顺序结构',exact:true}).tap();
    assert.equal((await touch.evaluate(()=>window.fixtureEvents.at(-1))).navigate,'list');
    await touchPrimary.tap();await touchPopup.waitFor();
    assert.equal(await touch.evaluate(()=>window.fixtureEvents.length),1);
    await touchPrimary.tap();
    assert.deepEqual(await touch.evaluate(()=>window.fixtureEvents.at(-1)),{train:'B'});
    assert.equal(await touchPopup.count(),0);
    await touchPrimary.tap();await touchPopup.waitFor();
    await touch.touchscreen.tap(425,790);assert.equal(await touch.locator('.next-actions-popover').count(),0);
    const pen=await touch.context().newCDPSession(touch),penBox=await touchPrimary.boundingBox(),penPoint={x:penBox.x+penBox.width/2,y:penBox.y+penBox.height/2,pointerType:'pen'};
    await touch.evaluate(()=>{window.penEvents=[];for(const type of ['pointerover','pointerenter','pointerdown','pointerup','click','focusin','focusout'])document.addEventListener(type,event=>{window.penEvents.push({type,pointer:event.pointerType,target:event.target.className,expanded:document.querySelector('.next-actions')?.dataset.open});},true);});
    await pen.send('Input.dispatchMouseEvent',{type:'mouseMoved',...penPoint});
    const beforePen=await touch.evaluate(()=>window.fixtureEvents.length);
    await pen.send('Input.dispatchMouseEvent',{type:'mousePressed',...penPoint,button:'left',buttons:1,clickCount:1});
    await pen.send('Input.dispatchMouseEvent',{type:'mouseReleased',...penPoint,button:'left',buttons:0,clickCount:1});await pen.detach();
    assert.equal(await touch.evaluate(()=>window.fixtureEvents.length),beforePen+1,'Pen click enters the primary task directly');
    assert.deepEqual(await touch.evaluate(()=>window.fixtureEvents.at(-1)),{train:'B'});
    await touchPopup.waitFor({state:'detached',timeout:1000}).catch(async error=>{console.log('PEN TRACE',JSON.stringify(await touch.evaluate(()=>window.penEvents)));throw error;});
    assert.equal(await touchPopup.count(),0);
    report.touchCompatibility={...touchCompatibility,menuSurvivedAnimationAndCloseBudget:true,secondaryTapNavigated:true,penClickNavigated:true};
  }finally{await touchContext.close();}

  phase='open-change-and-unmount';
  await page.evaluate(()=>window.fixtureUpdate({}));
  await page.waitForFunction(()=>document.querySelector('.next-actions-primary')?.disabled===false);await primary().waitFor();
  await hover();await page.waitForFunction(()=>window.fixtureAdviceOpen===true);
  await page.evaluate(()=>window.fixtureUnmount());
  assert.equal(await page.evaluate(()=>window.fixtureAdviceOpen),false);
  assert.equal(await page.locator('.next-actions-popover').count(),0);
  assert.deepEqual(errors,[]);assert.deepEqual(unknown,[]);
  assert(requests.includes('/api/training-lists')&&requests.includes('/api/templates'));
  Object.assign(report,{ok:true,hoverBridge:true,realTaskHover:true,mouseLeaveWithin180ms:true,mouseLeaveWithRetainedFocus:true,keyboardInternalFocusKeepsOpen:true,independentNavigation:true,keyboard:true,outsideClose:true,
    touch:true,suspended:true,openChange:true,unmountCloses:true,reducedMotion:true,reasonTooltips:true,allTasksDirect:true,primaryNotRepeated:true,alignedToWholeControl:true,alignedIconsTextAndArrows:true,opaqueThemedPopup:true,subtleBorderAndShadow:true,aboveUnderlyingContent:true,noSeparateChevron:true,noPrimaryArrow:true,realOfficialSubmissionsSent:0});
  console.log(JSON.stringify({ok:true,geometryCases:report.geometry.length,report:path.join(output,'report.json')}));
}catch(error){
  report.failure={phase,message:error.message};
  await page.screenshot({path:path.join(output,'failure.png')}).catch(()=>{});throw error;
}finally{
  await writeFile(path.join(output,'report.json'),JSON.stringify({...report,errors,unknown,requests},null,2)+'\n');
  await browser.close();await vite.close();
}
