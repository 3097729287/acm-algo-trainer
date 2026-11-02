import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';
import {createServer} from 'vite';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const output=path.resolve(root,'../.backups/learning-1437/ui');await mkdir(output,{recursive:true});
const fixture=`
import React,{useState} from 'react';import {createRoot} from 'react-dom/client';
import {Heart} from 'lucide-react';import NextActions from '/src/components/NextActions.jsx';
import {useSocial} from '/src/components/Social.jsx';import LearningPathsPage from '/src/pages/LearningPathsPage.jsx';
import MockSetup from '/src/app/MockSetup.jsx';import {FOUNDATION_LESSONS} from '/src/lib/learningCurriculum.js';
import {knowledgeCandidates} from '/src/lib/knowledgeJourney.js';import {availablePages} from '/src/lib/featureUnlocks.js';
import '/src/styles/workspace.css';import '/src/styles/refinements.css';import '/src/styles/polish.css';import '/src/styles/unified.css';import '/src/styles/revision.css';import '/src/styles/interaction.css';
const api=async endpoint=>{const response=await fetch('/fixture-api/'+endpoint);if(!response.ok)throw new Error('isolated unavailable');return response.json();};
const rows=['A','B','C','D'].map(id=>({id,title:'并查集陌生应用 '+id,url:'https://codeforces.com/contest/900/problem/'+id,tags:['并查集'],platform:'Codeforces',difficulty:1000,difficultySource:'Codeforces 官方',difficultyConfidence:'HIGH',catalogContentReady:true,solutionAvailable:true,solutionState:'available'}));
const initial={learnedLectures:FOUNDATION_LESSONS.map(item=>item.id),learningPaths:{}};
initial.learningPaths.knowledgeLearning={version:1,selection:knowledgeCandidates({prefs:initial,rows}).findIndex(item=>item.id==='dsu'),activeTopicId:null,journeys:{}};
window.events=[];
function Fixture(){const [prefs,setPrefs]=useState(initial),[state,setState]=useState({owner:'one',screen:'mine',facts:[]});const social=useSocial(api,true,state.owner);window.fixture={prefs,state,setPrefs,setState,social};
 const navigate=item=>{window.events.push(item);if(item.kind==='course')setPrefs(previous=>({...previous,learningPaths:{...previous.learningPaths,activePath:item.id,resumePath:item.id,[item.id]:previous.learningPaths[item.id]||{mode:'learn',labV1:{chapter:'0'}}}}));setState(previous=>({...previous,screen:item.page,recommendation:item.kind==='specialized'?{mode:'topic',tags:item.tags,requestId:Date.now()}:item.kind==='replay'?{mode:'replay',requestId:Date.now()}:null}));};
 return <div className="app-shell"><main className="main-area"><header className="topbar"><div id="tb-page-search" className="topbar-search-slot"/><NextActions rows={rows} prefs={prefs} setPrefs={setPrefs} api={api} insights={{learningEvidence:{version:1,method:'verified-official-learning-v1',records:state.facts}}} availablePages={availablePages(8)} onNavigate={navigate} onTrain={id=>window.events.push({train:id})}/><div className="topbar-actions"><button aria-label="爱心" className="topbar-love-count"><Heart/><b>{social.snapshot?.totalLikes??'—'}</b></button></div></header>
 <button id="return-home" onClick={()=>setState(previous=>({...previous,screen:'mine'}))}>返回推荐</button>
 {state.screen==='paths'&&<LearningPathsPage rows={rows} prefs={prefs} setPrefs={setPrefs} onTrain={id=>window.events.push({train:id})}/>}
 {state.screen==='mock'&&<MockSetup api={api} recommendation={state.recommendation} categories={[]} platforms={[]}/>}
 </main></div>;
}(window.fixtureRoot||=createRoot(document.getElementById('root'))).render(<Fixture/>);`;
const html='<!doctype html><html><head><meta charset="utf-8"></head><body><div id="root"></div><script type="module" src="/@id/virtual:learning.jsx"></script></body></html>';
await writeFile(path.join(output,'fixture.jsx'),fixture);
const vite=await createServer({root,cacheDir:'../.backups/next-150/vite-knowledge-final',configFile:path.join(root,'vite.config.js'),server:{host:'127.0.0.1',port:0,watch:null},plugins:[{name:'isolated-learning',configureServer(server){server.middlewares.use(async(req,res,next)=>{if(req.url!=='/learning')return next();res.setHeader('Content-Type','text/html');res.end(await server.transformIndexHtml('/learning',html));});},resolveId(id){if(id==='virtual:learning.jsx')return path.join(output,'fixture.jsx');},load(id){if(id===path.join(output,'fixture.jsx'))return fixture;}}]});
await vite.listen();const base='http://127.0.0.1:'+vite.httpServer.address().port;
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});const page=await browser.newPage({viewport:{width:1440,height:960}});
page.setDefaultTimeout(10000);
let slow=true,unavailable=false;const errors=[],calls=[];page.on('pageerror',error=>errors.push(error.message));
await page.route('**/fixture-api/**',async route=>{const name=new URL(route.request().url()).pathname.slice('/fixture-api/'.length);calls.push(name);if(slow)await new Promise(resolve=>setTimeout(resolve,1200));const values={'training-lists':{lists:[]},templates:{templates:[{id:'builtin:dsu',title:'并查集',practicePassed:[false,false]}]},social:{available:true,totalLikes:12,todayLikes:2,notifications:[],unreadCount:0},'contests/events':{events:[]}};if(!Object.hasOwn(values,name))return route.fulfill({status:501,json:{error:'unexpected isolated route'}});return route.fulfill(unavailable&&name==='social'?{status:503,json:{error:'offline'}}:{json:values[name]});});
const report={ok:false,checks:[],actualComponents:['NextActions','useSocial','LearningPathsPage','GraphCourse','MockSetup']};
try{
 await page.goto(base+'/learning');await page.locator('.next-actions-primary').waitFor();assert.equal(await page.getByRole('button',{name:'爱心',exact:true}).locator('svg').count(),1);report.checks.push('recommendation and heart present while API delayed');
 await page.waitForFunction(()=>window.fixture?.social.snapshot?.totalLikes===12);slow=false;
 const popup=()=>page.getByRole('region',{name:'推荐任务与依据'});const open=async()=>{await page.mouse.move(20,900);await page.locator('.next-actions').hover();await popup().waitFor();};
 await open();
 await page.getByRole('button',{name:'开始知识点学习 并查集',exact:true}).hover();
 await page.waitForFunction(()=>{const row=document.querySelector('.next-actions-popover li:hover');return row&&[...row.querySelectorAll(':scope>button')].every(button=>getComputedStyle(button).color===getComputedStyle(row).color);});
 const rowPaint=await page.getByRole('button',{name:'开始知识点学习 并查集',exact:true}).evaluate(button=>{const row=button.closest('li'),style=getComputedStyle(row);return {background:style.backgroundColor,color:style.color,controls:[...row.querySelectorAll(':scope>button')].map(node=>getComputedStyle(node).color)};});
 assert.notEqual(rowPaint.background,'rgba(0, 0, 0, 0)');assert(rowPaint.controls.every(color=>color===rowPaint.color),'Hover highlights the complete row including refresh/info: '+JSON.stringify(rowPaint));
 await page.getByRole('button',{name:'开始知识点学习 并查集',exact:true}).click();await page.getByRole('dialog',{name:'学习并查集',exact:true}).waitFor();assert.equal(await page.evaluate(()=>fixture.prefs.learningPaths.knowledgeLearning.activeTopicId),null);
 await page.getByRole('button',{name:'进入学习',exact:true}).click();await page.waitForFunction(()=>fixture.prefs.learningPaths.knowledgeLearning.activeTopicId==='dsu');
 assert.equal(await page.locator('.next-actions-primary').getAttribute('data-recommendation'),'course');report.checks.push('explicit learning confirmation and active-topic recommendation');
 await page.locator('.next-actions-primary').click();await page.getByRole('heading',{name:'并查集',exact:true}).waitFor();await page.getByRole('button',{name:'下一页',exact:true}).click();
 const chapter=await page.evaluate(()=>fixture.prefs.learningPaths.dsu.labV1.chapter);assert.notEqual(String(chapter),'0');await page.locator('#return-home').click();await page.locator('.next-actions-primary').click();assert.equal(String(await page.evaluate(()=>fixture.prefs.learningPaths.dsu.labV1.chapter)),String(chapter));report.checks.push('actual Lab navigation resumes without resetting chapter');
 await page.locator('#return-home').click();await page.getByRole('button',{name:'取消并查集学习',exact:true}).click();await page.getByRole('alertdialog',{name:'取消知识点学习确认'}).waitFor();await page.getByRole('button',{name:'继续学习',exact:true}).click();assert.equal(await page.evaluate(()=>fixture.prefs.learningPaths.knowledgeLearning.activeTopicId),'dsu');
 await page.getByRole('button',{name:'取消并查集学习',exact:true}).click();await page.getByRole('button',{name:'取消学习',exact:true}).click();await page.waitForFunction(()=>fixture.prefs.learningPaths.knowledgeLearning.activeTopicId===null);assert.equal(await page.evaluate(()=>fixture.prefs.learningPaths.knowledgeLearning.journeys.dsu.status),'paused');report.checks.push('cancel PopConfirm retains progress');
 await open();const before=await popup().locator('[data-recommendation=knowledge] strong').first().textContent();await page.getByRole('button',{name:'更换推荐知识点',exact:true}).click();assert.notEqual(await popup().locator('[data-recommendation=knowledge] strong').first().textContent(),before);report.checks.push('refresh changes candidate without entering it');
 await popup().locator('[data-recommendation=specialized]').click();await page.getByRole('button',{name:'专项训练',exact:true}).waitFor();assert.equal(await page.getByRole('button',{name:'专项训练',exact:true}).getAttribute('aria-pressed'),'true');await page.locator('#return-home').click();await open();await popup().locator('[data-recommendation=replay]').click();assert.equal(await page.getByRole('button',{name:'重现赛',exact:true}).getAttribute('aria-pressed'),'true');report.checks.push('specialized and replay recommendations select actual setup mode');
 unavailable=true;await page.evaluate(()=>fixture.social.refresh());assert.equal(await page.getByRole('button',{name:'爱心',exact:true}).innerText(),'12');await page.evaluate(()=>fixture.setState(previous=>({...previous,owner:'two'})));await page.waitForFunction(()=>fixture.social.snapshot?.totalLikes!==12);assert.equal(await page.getByRole('button',{name:'爱心',exact:true}).locator('svg').count(),1);report.checks.push('heart persists across failed fetch and never leaks prior owner count');
 for(const width of [2048,1440,1280,960,430]){await page.setViewportSize({width,height:960});await page.locator('#return-home').click();await open();const box=await popup().boundingBox();assert(box.x>=0&&box.x+box.width<=width+1);const anchor=await page.locator('.next-actions').boundingBox(),main=await page.locator('.main-area').boundingBox();assert(Math.abs(anchor.x+anchor.width/2-(main.x+main.width/2))<2,'Recommendation must be centered on workspace');assert(Math.abs(box.x+box.width/2-(anchor.x+anchor.width/2))<2,'Popup must share its anchor center');assert(await page.locator('.next-actions-primary').isVisible());await page.screenshot({path:path.join(output,'knowledge-'+width+'.png'),animations:'disabled'});await page.mouse.move(10,900);}
 assert.deepEqual(errors,[]);assert(!calls.some(name=>/start|submit|save/.test(name)));report.ok=true;console.log('PASS '+report.checks.join('; '));
}catch(error){report.error=error.stack;await page.screenshot({path:path.join(output,'failed.png')});throw error;}finally{await writeFile(path.join(output,'result.json'),JSON.stringify(report,null,2));await browser.close();await vite.close();}
