import assert from 'node:assert/strict';
import {createServer} from 'vite';
import {chromium} from 'playwright';
import {mkdir} from 'node:fs/promises';
import path from 'node:path';
import {startFixture} from '../../server/leaderboard/tests/local-server.mjs';
import {emptyScore} from '../../server/leaderboard/src/pk-judge.mjs';
const output=path.resolve('../.backups/thought-duel-20261109/ui-'+Date.now());await mkdir(output,{recursive:true});
const fixture=await startFixture({now:Date.parse('2026-11-04T00:00:00Z')}),auth={};
for(const name of ['A','B']){
 const body={loginId:'ui_thought_'+name,nickname:'选手 '+name,password:'isolated-ui-password'};
 await fetch(fixture.endpoint+'/v1/accounts/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 auth[name]=await (await fetch(fixture.endpoint+'/v1/accounts/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({loginId:body.loginId,password:body.password})})).json();assert(auth[name].token);
}
let judgeRelease,holdDraft=false,releaseDraft,holdHistory=false,releaseHistory;const judgeWait=new Promise(resolve=>{judgeRelease=resolve;});
const perfect=()=>({correct_algorithm:true,time_feasible:true,scores:{correctness:40,complexity:20,edge_case:15,constant:10,clarity:10,innovation:5},final_score:100,fatal_flaws:[],feedback:'隔离测试裁判：正确思路'});
fixture.STORE.pk.configure({enabled:true,now:()=>fixture.env.TEST_NOW,judge:async(problem,answers)=>{await judgeWait;const a=answers[0].includes('正确思路');return {problem_analysis:{optimal_algorithm:'隔离测试标准思路',optimal_time_complexity:'O(n)',optimal_space_complexity:'O(1)',key_edges:['最小边界']},player_a:a?perfect():emptyScore(),player_b:a?emptyScore():perfect(),winner:a?'A':'B',reason:'隔离测试模型回执'};}});
const bridge={name:'isolated-pk-bridge',configureServer(server){server.middlewares.use(async(req,res,next)=>{
 const match=/^\/__pk_proxy\/([AB])\/(.+)$/.exec(req.url||'');if(!match)return next();
 const [_,who,route]=match,identity=auth[who];
 try{
  if(route.startsWith('duel')){res.setHeader('Content-Type','application/json');res.end(JSON.stringify({owner:identity.account.userId,status:'idle',serverNow:fixture.env.TEST_NOW}));return;}
  const chunks=[];for await(const chunk of req)chunks.push(chunk);
  const response=await fetch(fixture.endpoint+'/api/'+route,{method:req.method,headers:{'Content-Type':'application/json','X-TB-User':identity.account.userId,Authorization:'Bearer '+identity.token},...(['GET','HEAD'].includes(req.method)?{}:{body:Buffer.concat(chunks)})});
  const body=await response.text();
  if(holdDraft&&who==='A'&&route.endsWith('/game/draft')){holdDraft=false;await new Promise(resolve=>{releaseDraft=resolve;});}
  if(holdHistory&&who==='A'&&route.endsWith('/history')){holdHistory=false;await new Promise(resolve=>{releaseHistory=resolve;});}
  res.statusCode=response.status;res.setHeader('Content-Type','application/json');res.end(body);
 }catch{res.statusCode=503;res.end(JSON.stringify({error:'隔离连接中断'}));}
});}};
const vite=await createServer({cacheDir:path.join(output,'vite'),plugins:[bridge],server:{host:'127.0.0.1',port:0,watch:null}});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});const contexts=[],pages=[],errors=[];
try{
 for(const who of ['A','B']){
  const context=await browser.newContext({viewport:{width:1600,height:960}});contexts.push(context);const page=await context.newPage();pages.push(page);page.setDefaultTimeout(10000);page.on('pageerror',e=>errors.push(e.message));
  await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/thought-duel-fixture.html?owner=${who}`);
  await page.waitForFunction(()=>typeof window.pkFixtureIdentity==='function');await page.evaluate(ids=>pkFixtureIdentity(ids),Object.fromEntries(Object.entries(auth).map(([key,a])=>[key,a.account.userId])));
  await page.getByRole('tab',{name:'思维对决',exact:true}).click();await page.getByRole('button',{name:'开始思维匹配'}).waitFor();assert(await page.getByRole('button',{name:'开始思维匹配'}).isEnabled());
 }
 const [a,b]=pages;
 await a.screenshot({path:path.join(output,'lobby.png')});
 await a.getByRole('button',{name:'开始思维匹配'}).click();await a.getByRole('button',{name:'取消匹配'}).waitFor();assert(await a.getByRole('tab',{name:'排位',exact:true}).isDisabled());
 await b.getByRole('button',{name:'开始思维匹配'}).click();await Promise.all(pages.map(p=>p.getByRole('alert',{name:'已找到对手'}).waitFor()));
 const room=JSON.parse(fixture.STORE.database.prepare('SELECT payload FROM pk_matches').get().payload);fixture.env.TEST_NOW=room.startedAt;
 await Promise.all(pages.map(p=>p.getByRole('textbox',{name:'思维对决答卷'}).waitFor()));
 assert(await a.getByRole('timer',{name:'思维对决剩余时间'}).textContent().then(v=>v.includes('15:00')||v.includes('14:59')));
 const answerA=a.getByRole('textbox',{name:'思维对决答卷'}),answerB=b.getByRole('textbox',{name:'思维对决答卷'});
 await answerA.fill('正确思路：先定义状态并证明转移，检查最小与极端输入，时间 O(n)，空间 O(1)。');
 await a.waitForFunction(()=>document.querySelector('.thought-answer header span')?.textContent==='已保存');
 await answerB.fill('错误思路');await b.waitForFunction(()=>document.querySelector('.thought-answer header span')?.textContent==='已保存');
 // A late draft acknowledgement cannot overwrite the next account's answer.
 holdDraft=true;await answerA.fill('正确思路：完整证明与边界，时间 O(n)，空间 O(1)。');
 for(let i=0;i<100&&!releaseDraft;i++)await new Promise(resolve=>setTimeout(resolve,20));assert(releaseDraft);
 await a.evaluate(()=>selectPkOwner('B'));await a.waitForFunction(()=>document.querySelector('textarea')?.value==='错误思路');releaseDraft();releaseDraft=null;
 await a.waitForTimeout(100);assert.equal(await a.getByRole('textbox',{name:'思维对决答卷'}).inputValue(),'错误思路');
 await a.evaluate(()=>selectPkOwner('A'));await a.waitForFunction(()=>document.querySelector('textarea')?.value.startsWith('正确思路'));
 await a.screenshot({path:path.join(output,'active.png')});
 fixture.STORE.pk.dailyCallLimit=1;await fixture.STORE.pk.transaction(db=>fixture.STORE.pk.reserveCall(db,fixture.env.TEST_NOW));
 await a.getByRole('button',{name:'提交思路',exact:true}).click();await a.getByText('已交卷，等待对手作答或时间结束',{exact:true}).waitFor();assert(await answerA.isDisabled());assert(await answerB.isEnabled());
 await b.getByRole('button',{name:'提交思路',exact:true}).click();await a.getByText('答卷已保留，等待裁判恢复',{exact:true}).waitFor();assert.equal(fixture.STORE.database.prepare('SELECT COUNT(*) n FROM pk_records').get().n,0);assert(await answerA.isDisabled());assert(await answerB.isDisabled());await a.screenshot({path:path.join(output,'budget-wait.png')});
 fixture.STORE.pk.dailyCallLimit=2;fixture.env.TEST_NOW+=60000;await fixture.STORE.pk.maintain();await a.getByText('AI 裁判中',{exact:true}).waitFor();judgeRelease();
 await a.getByRole('heading',{name:'本局获胜',exact:true}).waitFor();await b.getByRole('heading',{name:'本局结束',exact:true}).waitFor();assert.equal(await a.locator('.thought-dimensions progress').count(),12);
 await a.screenshot({path:path.join(output,'result.png')});
 await a.getByRole('button',{name:'返回匹配',exact:true}).click();await a.getByRole('button',{name:'对局记录',exact:true}).click();await a.getByRole('heading',{name:'对局记录'}).waitFor();await a.locator('.thought-history-row').click();await a.getByRole('heading',{name:'本局获胜'}).waitFor();
 await a.setViewportSize({width:540,height:900});await a.screenshot({path:path.join(output,'mobile-result.png')});assert.equal(await a.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 await a.getByRole('button',{name:'返回匹配',exact:true}).click();await a.getByRole('button',{name:'返回思维对决',exact:true}).click();await a.getByRole('button',{name:'开始思维匹配'}).waitFor();
 holdHistory=true;await a.getByRole('button',{name:'对局记录',exact:true}).click();
 for(let i=0;i<100&&!releaseHistory;i++)await new Promise(resolve=>setTimeout(resolve,20));assert(releaseHistory);
 await a.evaluate(()=>selectPkOwner('B'));await a.waitForFunction(()=>document.getElementById('duel-ranked-tab')?.getAttribute('aria-selected')==='true');await a.getByRole('tab',{name:'思维对决',exact:true}).click();await a.getByRole('heading',{name:'本局结束',exact:true}).waitFor();await a.getByRole('button',{name:'返回匹配',exact:true}).click();await a.getByRole('button',{name:'开始思维匹配'}).waitFor();
 releaseHistory();releaseHistory=null;await a.waitForTimeout(100);assert.equal(await a.getByRole('heading',{name:'对局记录',exact:true}).count(),0);assert.equal(await a.locator('.thought-history-row').count(),0);
 assert.deepEqual(errors,[]);console.log('PASS real React + shared HTTP service: mode tabs, queue, server countdown, autosave, draft/history owner-race isolation, early-submit lock, recoverable budget wait, AI wait, six-dimension result, private history and narrow layout. Fixture judge only. Evidence: '+output);
}finally{judgeRelease();releaseDraft?.();releaseHistory?.();for(const c of contexts)await c.close();await browser.close();await vite.close();await fixture.close();}
