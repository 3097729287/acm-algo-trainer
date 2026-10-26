import assert from 'node:assert/strict';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {realpathSync} from 'node:fs';
import {createServer} from 'vite';
import {chromium} from 'playwright';

const {categories}=JSON.parse(await readFile(new URL('./interface-polish-categories.json',import.meta.url),'utf8'));
const out='../.backups/local-1416/ui';await mkdir(out,{recursive:true});
const server=process.env.TB_POLISH_BASE?null:await createServer({server:{host:'127.0.0.1',port:0,fs:{allow:[process.cwd(),realpathSync('node_modules')]}}});
if(server)await server.listen();
const base=process.env.TB_POLISH_BASE||server.resolvedUrls.local[0];
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1920,height:1080}}),errors=[];
page.setDefaultTimeout(15000);page.on('pageerror',error=>errors.push(error.message));
const now=new Date().toISOString(),self={userId:'11111111-1111-4111-8111-111111111111',nickname:'练习者'};
const verdicts=['AC','WA','CE','TLE','MLE','RE','OLE','SAMPLE_PASS',null];
const rows=verdicts.map((verdict,i)=>({id:'polish-'+i,title:'练习 '+String.fromCharCode(65+i),contest:'ABC 481',problem:String.fromCharCode(65+i),url:`https://atcoder.jp/contests/abc481/tasks/abc481_${String.fromCharCode(97+i)}`,platform:'AtCoder',series:'ABC',difficulty:800+i*100,tags:['模拟']}));
const training=rows.slice(0,-1).map((row,i)=>({id:row.id,verdict:verdicts[i],accepted:i===0,scope:i===0?'official':'local',attempts:1,activeAt:now}));
let preferences={theme:'dark',accent:'teal',fontSize:18,panelStyle:'blueprint',panelOpacity:100,widgets:true};
await page.addInitScript(value=>localStorage.setItem('tb.preferences',JSON.stringify(value)),preferences);
await page.route('**/api/**',async route=>{
 const request=route.request(),path=new URL(request.url()).pathname,body=request.method()==='POST'?request.postDataJSON():null;
 if(!path.startsWith('/api/'))return route.continue();
 let value={};
 if(path==='/api/account')value={required:false,authenticated:true,usesOriginalWorkspace:true,token:'fixture',account:self};
 else if(path==='/api/preferences'){if(body)preferences=body.preferences;value={preferences,updatedAt:now};}
 else if(path==='/api/software-update')value={currentVersion:'1.4.16',status:'current',autoCheck:false,canInstall:false};
 else if(path==='/api/data')value={rows,categories,token:'fixture',today:now.slice(0,10),revision:'polish'};
 else if(path==='/api/workspace')value={training,sets:[],contests:[],activeContest:null,summary:{total:training.length,accepted:1,attempts:8,todayAccepted:0,due:0,pending:0,streak:16},now};
 else if(path==='/api/insights')value={summary:{totalSolved:72,officialSolved:72,submissions:94,activeDays:25,streak:16},growth:{level:9,currentLevelXp:680,nextLevelXp:1800,titles:[]},knowledge:[],knowledgeEvidence:[],achievements:[],activity:[],assessment:{rating:1000,evidenceCount:5,platforms:[]},dailyTasks:{tasks:[]}};
 else if(path==='/api/hub')value={settings:{accounts:{},autoSync:false},sync:{busy:false},accounts:[],notifications:[]};
 else if(path==='/api/profile')value={profile:self,leaderboard:{configured:true,status:'ready'}};
 else if(path==='/api/social')value={available:true,todayLikes:0,unreadCount:0,notifications:[]};
 else if(path==='/api/goals')value={goals:[],contestPlan:{contests:[]}};
 else if(path==='/api/contests/events')value={events:[]};
 else if(path==='/api/submissions')value={submissions:[],total:0};
 else if(path==='/api/lectures')value={lectures:[]};
 else if(path==='/api/browser-preparation')value={available:false};
 else if(path==='/api/desktop/fullscreen')value={available:false,fullscreen:false};
 await route.fulfill({json:value});
});
const nav=name=>page.locator('.sidebar').getByRole('button',{name,exact:true});
let charts=0,maxLabelGap=0;
async function checkRadar(){
 const result=await page.locator('.knowledge-radar>svg').evaluate(svg=>{
  const rect=node=>{const r=node.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom};};
  const labels=[...svg.querySelectorAll('text[data-knowledge-name]')].map(node=>({name:node.dataset.knowledgeName,...rect(node)}));
  const nodes=[...svg.querySelectorAll('.radar-node')].map(rect);
  return {labels,nodes,bounds:rect(svg),guides:svg.querySelectorAll('.radar-label-guide').length,scale:svg.getScreenCTM().a};
 });
 assert.equal(result.guides,0);
 for(let i=0;i<result.labels.length;i++){
  const a=result.labels[i],vertex=result.nodes[i];
  assert(a.left>=result.bounds.left-1&&a.right<=result.bounds.right+1&&a.top>=result.bounds.top-1&&a.bottom<=result.bounds.bottom+1,'clipped '+a.name);
  const gap=Math.hypot(Math.max(0,a.left-vertex.right,vertex.left-a.right),Math.max(0,a.top-vertex.bottom,vertex.top-a.bottom))/result.scale;
  maxLabelGap=Math.max(maxLabelGap,gap);assert(gap<45,`${a.name} too far from its vertex: ${gap}`);
  for(let j=i+1;j<result.labels.length;j++){const b=result.labels[j];assert(!(Math.min(a.right,b.right)-Math.max(a.left,b.left)>.5&&Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>.5),a.name+' overlaps '+b.name);}
 }
 charts++;
}
try{
 await page.goto(base);await nav('成长与能力').click();await page.locator('.knowledge-radar').waitFor();
 assert.equal(await page.getByRole('button',{name:'切换主题',exact:true}).count(),0);
 for(const viewport of [{width:1920,height:1080},{width:1366,height:768},{width:1024,height:640}]){
  await page.setViewportSize(viewport);
  for(const font of [14,18,22]){
   await page.evaluate(font=>document.documentElement.style.setProperty('--ui-font-size',font+'px'),font);
   const centers=await page.locator('.topbar-actions').evaluate(node=>[node.querySelector('.practice-streak'),node.querySelector('.topbar-daily-ac'),node.querySelector('.topbar-love-count'),node.querySelector('[aria-label="消息通知"]')].map(element=>{const r=element.getBoundingClientRect();return r.y+r.height/2;}));
   assert(Math.max(...centers)-Math.min(...centers)<.6,JSON.stringify(centers));
   const textCenters=await page.locator('.topbar-actions').evaluate(node=>[...node.querySelectorAll('.metric-label,.metric-separator,.topbar-status-chip b,.practice-streak b')].map(element=>{const r=element.getBoundingClientRect();return r.y+r.height/2;}));
   assert(Math.max(...textCenters)-Math.min(...textCenters)<.6,JSON.stringify(textCenters));
   await checkRadar();
   const names=await page.locator('.radar-node').evaluateAll(nodes=>nodes.map(node=>node.getAttribute('aria-label')));
   for(const name of names){await page.getByRole('button',{name,exact:true}).click();await checkRadar();await page.getByRole('button',{name:'返回一级雷达',exact:true}).click();}
  }
 }
 await page.setViewportSize({width:1920,height:1080});
 await page.getByRole('button',{name:/思维与策略，掌握/}).click();await page.screenshot({path:out+'/radar-strategy.png'});
 await page.getByRole('button',{name:'返回一级雷达',exact:true}).click();await page.getByRole('button',{name:/数学与计数，掌握/}).click();await page.screenshot({path:out+'/radar-math.png'});
 await nav('比赛').click();await page.getByRole('button',{name:/查看 .*ABC 481/}).click();
 assert.deepEqual(await page.locator('.competition-result').allTextContents(),['AC','WA','CE','TLE','MLE','RE','OLE','样例通过','未加入']);
 await page.screenshot({path:out+'/contest-verdicts.png'});
 await nav('设置').click();await page.getByRole('tab',{name:'外观',exact:true}).click();await page.getByRole('button',{name:'云白浅色',exact:true}).click();
 await page.waitForFunction(()=>document.documentElement.dataset.theme==='light');
 assert.equal(await page.getByRole('button',{name:'切换主题',exact:true}).count(),0);
 await page.screenshot({path:out+'/header-settings.png'});
 assert.deepEqual(errors,[]);
 const report={ok:true,charts,viewports:3,fontSizes:[14,18,22],maxLabelGap:Math.round(maxLabelGap*100)/100,noLeaderLines:true,noLabelOverlaps:true,headerAligned:true,themeOnlyInSettings:true,verdicts:true,compiledUi:!!process.env.TB_POLISH_BASE};
 await writeFile(out+(process.env.TB_POLISH_BASE?'/compiled-report.json':'/report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}catch(error){await page.screenshot({path:out+'/failure.png'});console.error(JSON.stringify({errors,body:(await page.locator('body').innerText()).slice(0,2500)}));throw error;}finally{await browser.close();if(server)await server.close();}
