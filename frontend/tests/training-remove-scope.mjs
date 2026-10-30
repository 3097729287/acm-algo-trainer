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
const notifications=Array.from({length:32},(_,i)=>({id:'today-'+i,kind:i%2?'comment':'like',actor:{nickname:'今日用户'+i},text:'今日留言内容 '.repeat(8),createdAt:i===0?'2026-10-28T16:00:00.000Z':now,read:true}));
notifications.push(...[{id:'old',kind:'comment',actor:{nickname:'昨日用户'},text:'昨日内容不可出现',createdAt:'2026-10-28T15:59:59.999Z',read:false},{id:'future',kind:'comment',actor:{nickname:'未来用户'},text:'未来内容不可出现',createdAt:'2026-10-29T16:00:00.000Z',read:false},{id:'invalid',kind:'comment',actor:{nickname:'无效日期'},text:'无效日期不可出现',createdAt:'invalid',read:false}]);
const hub={settings:{autoSync:false},accounts:[],updates:{configured:true},sync:{busy:false,providers:[]},notifications:Array.from({length:32},(_,i)=>({id:'update-'+i,type:'content',title:`公共内容更新 ${i}`,createdAt:now,read:true,count:i+1}))};
const daily=()=>({policyVersion:3,date:'2026-10-29',tasks:[],displayCompletedCount:completed,displayTarget:Math.min(10,Math.max(3,completed+1)),displayComplete:completed>=10});
const activeIds=new Set([rows[0].id]),writes=[];
function trainingWorkspace(){workspace.training=rows.filter(row=>activeIds.has(row.id)).map(row=>({id:row.id,activeAt:now,lastActivityAt:now,today:true,accepted:false,verdict:null,attempts:0}));workspace.summary={...workspace.summary,total:activeIds.size};return workspace;}
await page.route('**/api/**',async route=>{
 const request=route.request(),url=new URL(request.url());if(!url.pathname.startsWith('/api/'))return route.continue();const name=url.pathname.replace('/api/','');let value;
 if(name==='account')value={required:true,authenticated:true,token:'fixture',account:{userId:owner,loginId:'fixture',nickname:'测试学习者'}};
 else if(name==='preferences'){if(request.method()==='POST')preferences=request.postDataJSON().preferences;value={preferences,updatedAt:now};}
 else if(name==='data')value={rows,categories:[],token:'fixture',today:'2026-10-29'};
 else if(name==='workspace')value=trainingWorkspace();
 else if(name==='training/remove'){const id=request.postDataJSON().id;writes.push({name,id});activeIds.delete(id);value={workspace:trainingWorkspace()};}
 else if(name==='training/start'){const id=request.postDataJSON().id;writes.push({name,id});activeIds.add(id);value={workspace:trainingWorkspace()};}
 else if(name==='training/contest'){const contest=request.postDataJSON().contest;const ids=rows.filter(row=>row.contest===contest).map(row=>row.id);writes.push({name,contest});ids.forEach(id=>activeIds.add(id));const set={id:'synthetic-set',name:contest,ids};workspace.sets=[set];value={workspace:trainingWorkspace(),set};}
 else if(name==='problem'){const id=url.searchParams.get('id');value={...rows.find(r=>r.id===id),id,markdown:'# 隔离题面\n\n输入两个整数，输出它们的和。',samples:[{input:'1 2\n',output:'3\n'}],limits:{timeMs:2000,memoryMb:256},judge:{scope:'samples',cases:1},statementAvailable:true,locked:false,draft:'int main(){return 0;}',submissions:[]};}
 else if(name==='draft')value={savedAt:now};
 else if(name==='translation/settings')value={provider:'custom',configured:false,providers:[]};
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
 else if(name==='training-lists')value={lists:[{id:'synthetic-list',title:'入口范围测试',available:true,custom:true,categories:[],problems:rows.map(row=>({problemId:row.id,url:row.url}))}]};
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

const output='tests/screenshots/training-remove-scope';await mkdir(output,{recursive:true});const checked=[];
const removeWrites=()=>writes.filter(item=>item.name==='training/remove').length;
async function noRemove(name,focus){assert.equal(await page.getByRole('button',{name:/^取消训练 /}).count(),0,name+' has no remove control');const before=removeWrites();if(focus)await focus.focus();await page.keyboard.press('Delete');await page.waitForTimeout(60);assert.equal(removeWrites(),before,name+' Delete cannot remove training');checked.push(name);}
async function openTitle(button){const before=writes.filter(item=>item.name==='training/start').length;await button.click();await page.getByRole('button',{name:'返回列表',exact:true}).waitFor();assert.equal(writes.filter(item=>item.name==='training/start').length,before+1);await page.getByRole('button',{name:'返回列表',exact:true}).click();}
try{
 await load();await nav().getByRole('button',{name:'我的训练',exact:true}).click();const remove=page.getByRole('button',{name:'取消训练 '+rows[0].title,exact:true});await remove.waitFor();await remove.click();await page.getByText('已取消训练，代码与历史记录保留。',{exact:true}).waitFor();assert.equal(removeWrites(),1);assert(!activeIds.has(rows[0].id));await page.getByRole('button',{name:'恢复',exact:true}).click();await remove.waitFor();assert(activeIds.has(rows[0].id));
 await nav().getByRole('button',{name:'题库',exact:true}).click();await page.locator('.problem-table tbody tr[data-id]').first().waitFor();await noRemove('library',page.getByRole('region',{name:'题目列表',exact:true}));await openTitle(page.getByRole('button',{name:rows[1].title,exact:true}));assert(activeIds.has(rows[1].id));await noRemove('library-after-add');
 await nav().getByRole('button',{name:'题单',exact:true}).click();await page.getByRole('textbox',{name:'搜索题单或题目',exact:true}).fill('入口范围测试');await page.getByRole('button',{name:'打开题单：入口范围测试',exact:true}).click();await page.locator('.training-list-table tr[data-id]').first().waitFor();await noRemove('training-list',page.locator('.training-problem-row').first());await openTitle(page.getByRole('button',{name:rows[2].title,exact:true}));assert(activeIds.has(rows[2].id));await noRemove('training-list-after-add');
 await nav().getByRole('button',{name:'比赛',exact:true}).click();await page.locator('.competition-card-open').first().click();const detail=page.locator('.competition-detail');await detail.waitFor();await noRemove('competition',detail);
 await openTitle(detail.getByRole('button',{name:/^练习 /}).first());await detail.waitFor();await noRemove('competition-after-add',detail);
 const join=page.getByRole('button',{name:/^(加入我的训练|加入剩余题目)$/,exact:true});await join.click();await page.waitForTimeout(100);assert.equal(writes.filter(item=>item.name==='training/contest').length,1);
 assert.equal(removeWrites(),1);assert.deepEqual(errors,[]);assert.deepEqual(unknown,[]);assert.deepEqual(external,[]);await page.screenshot({path:output+'/final.png'});console.log(JSON.stringify({ok:true,mineRemoveAndUndo:true,outsideMine:checked,starts:writes.filter(item=>item.name==='training/start').length,contestJoin:true,realWrites:0}));
}catch(error){await page.screenshot({path:output+'/failure.png'}).catch(()=>{});throw error;}
finally{await writeFile(output+'/report.json',JSON.stringify({checked,writes,errors,unknown,external},null,2));await page.unrouteAll({behavior:'ignoreErrors'});await browser.close();await vite.close();}
