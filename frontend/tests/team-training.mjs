import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {spawn} from 'node:child_process';
import {mkdtemp,readFile,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {DatabaseSync} from 'node:sqlite';
import {join,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createServer} from 'vite';
import {chromium} from 'playwright';
import {startFixture} from '../../server/leaderboard/tests/local-server.mjs';
import {parseTeamReceipt} from '../../server/leaderboard/src/team-receipts.mjs';

const root=fileURLToPath(new URL('../..',import.meta.url)),state=await mkdtemp(join(tmpdir(),'tb-team-integration-'));
const shared=await startFixture();
const contest={id:'codeforces:contest:123',title:'Isolated partial contest',platform:'Codeforces',availableProblems:2,missingProblems:1,
 problems:['A','B','C'].map((letter,index)=>({id:'fixture::'+letter,letter,title:'Fixture '+letter,url:'https://codeforces.com/contest/123/problem/'+letter,
  problemKey:createHash('sha256').update('codeforces.com/contest/123/problem/'+letter).digest('hex'),available:index!==1,problemType:'standard'}))};
shared.STORE.teams.catalogue={schema:1,revision:'isolated-3-client-test',contests:[contest]};shared.STORE.teams.contests=new Map([[contest.id,contest]]);
shared.STORE.teams.verifyReceipt=async request=>parseTeamReceipt('codeforces',[{id:Number(request.submissionId),
 problem:{contestId:123,index:new URL(request.url).pathname.split('/').at(-1)},author:{members:[{handle:request.handle}]},
 verdict:'OK',creationTimeSeconds:Math.floor(request.issuedAt/1000)}],request);
let vite,browser,service,stderr='';const errors=[],checked=[];let contexts=[];
try{
 const accounts=[];
 for(let i=0;i<3;i++){
  const body={loginId:'team_ui_'+i,nickname:'队员'+(i+1),password:'isolated-team-password'};
  const headers={'Content-Type':'application/json'};
  const registered=await fetch(shared.endpoint+'/v1/accounts/register',{method:'POST',headers,body:JSON.stringify(body)});assert.equal(registered.status,201);
  const login=await fetch(shared.endpoint+'/v1/accounts/login',{method:'POST',headers,body:JSON.stringify({loginId:body.loginId,password:body.password})});assert.equal(login.status,200);
  const signed=await login.json();accounts.push({owner:signed.account.userId,token:signed.token});
 }
 shared.STORE.database.prepare('INSERT INTO official_ac_events(user_id,problem_key,event_id,accepted_at,accepted_day,difficulty,received_at) VALUES(?,?,?,?,?,?,?)')
  .run(accounts[0].owner,contest.problems[0].problemKey,createHash('sha256').update('isolated-old-first').digest('hex'),new Date(Date.now()-86400000).toISOString(),'2026-11-07',1200,new Date().toISOString());
 vite=await createServer({root:join(root,'frontend'),optimizeDeps:{entries:['tests/team-training-fixture.html']},server:{host:'127.0.0.1',port:0,hmr:false}});await vite.listen();
 const origin='http://127.0.0.1:'+vite.httpServer.address().port;
 service=spawn(process.env.TB_PYTHON||'python',[join(root,'frontend/tests/team-local-api.py')],{cwd:root,windowsHide:true,
  env:{...process.env,TB_OFFLINE:'1',TB_STATE_DIR:state,TB_TEAM_TEST_ACCOUNTS:JSON.stringify(accounts),TB_TEAM_TEST_ENDPOINT:shared.endpoint,TB_TEAM_TEST_ORIGIN:origin,PYTHONIOENCODING:'utf-8'}});
 service.stderr.on('data',part=>{stderr+=part;});
 const locals=await new Promise((done,fail)=>{
  let buffer='';const timer=setTimeout(()=>fail(new Error('native fixture startup timed out: '+stderr)),30000);
  service.stdout.on('data',part=>{buffer+=part;for(const line of buffer.split(/\r?\n/)){if(line.startsWith('[{"owner":')){clearTimeout(timer);done(JSON.parse(line));}}});
  service.once('exit',code=>{clearTimeout(timer);fail(new Error('native fixture exited '+code+': '+stderr));});
 });
 browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
 const pages=[];
 for(const config of locals){
  const context=await browser.newContext({viewport:{width:1440,height:900}});contexts.push(context);
  await context.addInitScript(value=>window.teamFixture=value,config);
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));await page.goto(origin+'/tests/team-training-fixture.html');pages.push(page);
  await page.getByRole('textbox',{name:'队名',exact:true}).waitFor();
 }
 const [a,b,c]=pages,refresh=async page=>{await page.getByRole('button',{name:'刷新团队训练',exact:true}).click();};
 await a.getByRole('textbox',{name:'队名',exact:true}).fill('三人真实链路');await a.getByRole('button',{name:'创建队伍',exact:true}).click();
 await a.locator('.team-invite code').waitFor();const invite=await a.locator('.team-invite code').innerText();
 for(const page of [b,c]){await page.getByRole('textbox',{name:'队伍邀请码'}).fill(invite);await page.getByRole('button',{name:'加入队伍',exact:true}).click();await page.locator('.team-members').waitFor();}
 await refresh(a);await a.waitForFunction(()=>window.team.state?.team?.members?.length===3);
 await a.getByLabel('团队训练比赛',{exact:true}).selectOption(contest.id);await a.getByLabel('团队训练时长').fill('5');await a.getByRole('button',{name:'保存比赛设置',exact:true}).click();
 for(const page of pages){await refresh(page);await page.waitForFunction(()=>window.team.state?.team?.contestId==='codeforces:contest:123');}
 // All three prepare against one configuration, including concurrent clicks.
 await Promise.all(pages.map(page=>page.getByRole('button',{name:'准备',exact:true}).click()));
 await refresh(a);await a.waitForFunction(()=>window.team.state?.team?.members.every(p=>p.ready));
 await a.getByRole('button',{name:'开始团队训练',exact:true}).click();await a.getByRole('button',{name:'进入团队比赛',exact:true}).waitFor();
 for(const page of pages){await refresh(page);await page.getByRole('button',{name:'进入团队比赛',exact:true}).click();await page.locator('.team-training-room .wb-statement-pane').waitFor();}
 await a.getByRole('button',{name:'接管编辑控制',exact:true}).waitFor();await a.getByRole('button',{name:'接管编辑控制',exact:true}).click();
 await a.waitForFunction(()=>window.team.canEdit);await b.waitForFunction(()=>window.team.state?.room?.lease?.owner===window.teamFixture.owner||window.team.state?.room?.lease?.owner!==undefined);
 assert.equal(await a.locator('.wb-code-pane .code-editor').getAttribute('data-readonly'),'false');
 for(const page of [b,c])assert.equal(await page.locator('.wb-code-pane .code-editor').getAttribute('data-readonly'),'true');
 checked.push('three independent authenticated accounts; concurrent readiness; unique editing lease');
 const source='#include <bits/stdc++.h>\nusing namespace std;\nint main() { cout << "中文🦆"; }\n';
 await a.getByRole('textbox',{name:'C++ 代码',exact:true}).fill(source);
 await a.waitForFunction(code=>window.team.state?.room?.document?.code===code,source);
 for(const page of [b,c])await page.waitForFunction(code=>document.querySelector('.wb-code-pane .cm-content')?.textContent.includes('中文🦆')&&window.team.state?.room?.document.code===code,source);
 const roomId=await a.evaluate(()=>window.team.state.room.id);
 const readPrivate=index=>{
  const db=new DatabaseSync(join(state,String(index),'personal.sqlite3'),{readOnly:true});
  try{return db.prepare("SELECT code FROM drafts WHERE context='' AND problem_id='fixture::A'").get().code;}finally{db.close();}
 };
 assert.equal(readPrivate(0),'private-0-untouched');assert.equal(readPrivate(1),'private-1-untouched');
 checked.push('Chinese/emoji shared CAS propagated to both observers; ordinary private drafts unchanged');
 const divider=a.getByRole('separator',{name:'调整运行区与代码高度',exact:true}),beforeHeight=Number(await divider.getAttribute('aria-valuenow')),point=await divider.boundingBox();
 await a.mouse.move(point.x+point.width/2,point.y+point.height/2);await a.mouse.down();await a.mouse.move(point.x+point.width/2,point.y-80,{steps:6});await a.mouse.up();
 const savedHeight=Number(await divider.getAttribute('aria-valuenow'));assert(savedHeight>beforeHeight+5,`height is a percentage: ${beforeHeight} → ${savedHeight}`);
 await a.reload();await a.locator('.team-training-room .wb-code-pane').waitFor();await a.waitForFunction(()=>window.team.canEdit);
 assert(Math.abs(Number(await a.getByRole('separator',{name:'调整运行区与代码高度',exact:true}).getAttribute('aria-valuenow'))-savedHeight)<2);
 checked.push('per-account room console height survives a full page reload');
 const missing=a.getByLabel('团队比赛题目').locator('option[value="fixture::B"]');assert(await missing.isDisabled());
 await a.getByRole('button',{name:'自测运行',exact:true}).click();await a.locator('.wb-result-summary').waitFor();
 assert.equal(await a.evaluate(()=>window.team.state.room.score.totalScore),0);checked.push('missing task disabled; actual local judge run gives no shared AC');
 await a.getByRole('button',{name:'提交',exact:true}).click();
 await a.waitForFunction(()=>window.team.state?.room?.score?.totalScore===1);
 assert.equal(shared.STORE.database.prepare('SELECT COUNT(*) AS n FROM team_native_receipts').get().n,1);
 await a.getByRole('button',{name:'提交',exact:true}).click();
 await a.waitForFunction(()=>!document.querySelector('.wb-run-toolbar button[aria-label="提交"]')?.disabled);
 await new Promise(done=>setTimeout(done,400));
 assert.equal(await a.evaluate(()=>window.team.state.room.score.totalScore),1);
 assert.equal(shared.STORE.database.prepare('SELECT COUNT(*) AS n FROM official_ac_events').get().n,1);
 const personalCount=index=>{const db=new DatabaseSync(join(state,String(index),'personal.sqlite3'),{readOnly:true});try{return db.prepare("SELECT COUNT(*) AS n FROM submissions WHERE scope='official' AND verdict='AC'").get().n;}finally{db.close();}};
 assert(personalCount(0)>=1);assert.equal(personalCount(1),0);assert.equal(personalCount(2),0);
 checked.push('deterministic native provider through the actual backend journal and shared verifier; repeated old-task AC counts once; peer progress untouched');
 // A temporary network interruption makes the observer read only, and expiry
 // permits another authenticated account to acquire a new lease.
 await contexts[0].setOffline(true);
 const offlineSource=source+'// offline-only private buffer\n';
 await a.getByRole('textbox',{name:'C++ 代码',exact:true}).fill(offlineSource);
 await a.waitForFunction(()=>Object.keys(localStorage).some(key=>{try{return key.includes('tb.draft.')&&JSON.parse(localStorage.getItem(key)).code?.includes('offline-only');}catch{return false;}}));
 shared.env.TEST_NOW=Date.now()+20000;
 await b.evaluate(()=>window.team.reload());await b.waitForFunction(()=>!window.team.state.room.lease||window.team.state.room.lease.until<=window.team.serverNow);
 await b.getByRole('button',{name:'接管编辑控制',exact:true}).click();await b.waitForFunction(()=>window.team.canEdit);
 await contexts[0].setOffline(false);await a.evaluate(()=>window.team.reload());await a.waitForFunction(()=>!window.team.canEdit);
 assert.equal(await a.locator('.wb-code-pane .code-editor').getAttribute('data-readonly'),'true');
 assert.equal(await b.evaluate(()=>window.team.state.room.document.code),source,'an offline private buffer must not replace the shared draft');
 await b.getByLabel('团队比赛题目').selectOption('fixture::C');
 await Promise.all(pages.map(page=>page.waitForFunction(()=>window.team.state?.room?.problemId==='fixture::C')));
 await b.getByRole('textbox',{name:'C++ 代码',exact:true}).fill('int main() { return 0; }\n');await b.waitForFunction(()=>window.team.state.room.document.code.includes('return 0'));
 await b.reload();await b.locator('.team-training-room .wb-code-pane').waitFor();await b.waitForFunction(()=>window.team.state?.room?.document?.code.includes('return 0'));
 checked.push('offline takeover preserves all shared drafts; task switch and reload resume server state');
 await a.setViewportSize({width:640,height:800});await a.screenshot({path:join(state,'team-room-narrow.png')});
 const overflow=await a.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth+1);assert.equal(overflow,false);
 await a.getByRole('button',{name:'结束团队比赛',exact:true}).click();await a.getByRole('button',{name:'结束并复盘',exact:true}).click();
 await a.waitForFunction(()=>window.team.state.room.status==='finished');await b.waitForFunction(()=>window.team.state.room.status==='finished');
 await a.evaluate(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async value=>{window.copiedLocalBuffer=value;}}}));
 await a.getByRole('button',{name:'返回列表',exact:true}).click();await a.getByRole('button',{name:'团队训练记录',exact:true}).click();await a.locator('.team-history button').first().click();await a.getByLabel('查看历史共享代码').selectOption('fixture::A');
 await a.getByRole('button',{name:'复制本机保留代码',exact:true}).click();assert.equal(await a.evaluate(()=>window.copiedLocalBuffer),offlineSource);
 await b.getByRole('button',{name:'返回列表',exact:true}).click();await b.getByRole('button',{name:'团队训练记录',exact:true}).click();
 await b.locator('.team-history button').first().click();await b.getByLabel('查看历史共享代码').selectOption('fixture::A');
 await b.waitForFunction(()=>document.querySelector('.team-record .cm-content')?.textContent.includes('中文🦆'));
 checked.push('narrow full-screen layout; leader finish; historical shared code retained across tasks');
 assert.deepEqual(errors,[]);
 const receipt={passed:true,accounts:3,localNativeApis:3,sharedHttpServer:true,actualProblemSiteSubmissions:0,
  checked,browserErrors:errors.length,sharedScore:1,roomId,privateDraftsPreserved:true,nativeProvider:'explicit deterministic fixture; no real OJ submissions'};
 const output=process.argv[2]||join(state,'result.json');await writeFile(output,JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));
}catch(e){
 console.error('FIXTURE ARTIFACTS',state);if(browser){for(let i=0;i<contexts.length;i++){const p=contexts[i].pages()[0];if(p)await p.screenshot({path:join(state,`failure-${i}.png`)}).catch(()=>{});}}
 console.error(stderr.slice(-4000));throw e;
}finally{
 await browser?.close();if(service){service.stdin.write('stop\n');service.stdin.end();await new Promise(done=>{const timer=setTimeout(()=>{service.kill();done();},10000);service.once('exit',()=>{clearTimeout(timer);done();});});}
 await vite?.close();await shared.close();
}
