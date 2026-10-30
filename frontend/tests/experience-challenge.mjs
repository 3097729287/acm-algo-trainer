import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const vite=await createServer({cacheDir:'../.backups/experience-challenge/vite-cache',optimizeDeps:{entries:['tests/experience-challenge-fixture.html','tests/auth-recovery-fixture.html']},server:{host:'127.0.0.1',port:0,watch:null}});await vite.listen();
const base=`http://127.0.0.1:${vite.httpServer.address().port}`,browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),errors=[];
const fresh=async(policy=true,pending='')=>{const page=await browser.newPage({viewport:{width:1000,height:850}});page.setDefaultTimeout(10000);page.on('pageerror',e=>errors.push(e.message));await page.goto(base+'/tests/experience-challenge-fixture.html'+(!policy?'?noPolicy=1':pending?'?pending='+pending:''));return page;};
try{
 const page=await fresh(),prompt=page.getByRole('dialog',{name:'你有编程经验吗？'});await prompt.waitFor();
 await page.getByRole('button',{name:'我是新手',exact:false}).waitFor({state:'visible'});
 await page.waitForFunction(()=>challengeFixture.writes.some(v=>v.body.action==='seen'));
 assert.equal((await page.evaluate(()=>challengeFixture.prefs())).levelNoticeSeen,1,'The lower confirmed level was observed before assessment');
 await mkdir('tests/screenshots/experience-challenge',{recursive:true});
 for(const theme of ['dark','light']){await page.setViewportSize({width:430,height:740});await page.evaluate(t=>challengeFixture.theme(t),theme);const box=await prompt.boundingBox();assert(box.x>=0&&box.x+box.width<=430&&box.y>=0&&box.y+box.height<=740);await page.screenshot({path:`tests/screenshots/experience-challenge/${theme}.png`});}
 await prompt.getByRole('button',{name:'我是新手',exact:false}).click();await prompt.waitFor({state:'detached'});assert.equal(await page.locator('[data-level]').textContent(),'1');
 await page.evaluate(()=>challengeFixture.remount());await page.waitForTimeout(120);assert.equal(await prompt.count(),0,'A same-owner restored acknowledgement prevents a repeated prompt');await page.close();
 const veteran=await fresh();await veteran.getByRole('dialog',{name:'你有编程经验吗？'}).waitFor();
 await veteran.getByRole('button',{name:'我是老手',exact:false}).click();
 await veteran.waitForFunction(()=>challengeFixture.opened.length===1);assert.equal((await veteran.evaluate(()=>challengeFixture.opened[0])).id,'template-drill:binary-search:1');
 await veteran.evaluate(()=>challengeFixture.pass());await veteran.waitForFunction(()=>document.querySelector('[data-level]').textContent==='5');
 assert.equal(await veteran.getByRole('dialog',{name:'等级提升',exact:true}).count(),0,'Practice keeps the level animation queued');
 await veteran.getByRole('button',{name:'返回列表',exact:true}).click();
 await veteran.getByRole('dialog',{name:'等级提升',exact:true}).waitFor();assert.equal(await veteran.getByLabel('等级从 1 提升到 5').count(),1);
 assert((await veteran.locator('[data-navigation]').textContent()).includes('mock'));await veteran.getByRole('button',{name:'继续学习',exact:true}).click();
 await veteran.evaluate(()=>challengeFixture.remount());await veteran.waitForTimeout(100);assert.equal(await veteran.getByRole('dialog',{name:'等级提升',exact:true}).count(),0);await veteran.close();
 const race=await fresh();await race.getByRole('dialog',{name:'你有编程经验吗？'}).waitFor();await race.waitForFunction(()=>challengeFixture.writes.some(v=>v.body.action==='seen'));
 await race.waitForFunction(()=>!document.querySelector('.experience-challenge button').disabled);await race.evaluate(()=>{challengeFixture.hold=true;});
 await race.getByRole('button',{name:'我是老手',exact:false}).click();await race.waitForFunction(()=>challengeFixture.writes.some(v=>v.body.action==='choose'));
 await race.evaluate(()=>challengeFixture.switchOwner());await race.evaluate(()=>challengeFixture.release());await race.waitForTimeout(120);
 assert.equal(await race.locator('[data-level]').textContent(),'6');assert.deepEqual(await race.evaluate(()=>challengeFixture.opened),[],'A retired-owner response cannot open a challenge in the next account');await race.close();
 const legacy=await fresh(false);await legacy.waitForTimeout(100);await legacy.evaluate(()=>challengeFixture.remount());await legacy.waitForTimeout(100);assert.equal(await legacy.evaluate(()=>challengeFixture.writes.length),0,'Absent explicit backend policy never creates challenge requests');await legacy.close();
 for(const choice of ['beginner','experienced']){const registered=await fresh(true,choice);await registered.waitForFunction(()=>challengeFixture.writes.some(v=>v.body.action==='choose'));await registered.waitForFunction(()=>!window.__tbExperienceChoicePending);assert.equal(await registered.getByRole('dialog',{name:'你有编程经验吗？'}).count(),0,'Registration choices are not asked a second time');assert.equal(await registered.evaluate(()=>challengeFixture.opened.length),choice==='experienced'?1:0);assert.equal(await registered.locator('[data-level]').textContent(),'1','Only choosing experienced cannot award XP');await registered.close();}
 const gate=await browser.newPage();gate.setDefaultTimeout(10000);gate.on('pageerror',e=>errors.push(e.message));let authenticated=false;const posts=[];
 await gate.route('**/api/**',async route=>{const r=route.request(),path=new URL(r.url()).pathname;if(!path.startsWith('/api/'))return route.continue();const name=path.slice(5),body=r.method()==='POST'?r.postDataJSON():null;if(body)posts.push({name,body});let value;
  if(name==='account')value={required:true,authenticated,token:'test-token',account:authenticated?{userId:'registration-owner',loginId:'veteran_user',nickname:'老手'}:null};
  else if(name==='account/register')value={registered:true,loginId:'veteran_user'};
  else if(name==='account/login'){authenticated=true;value={required:true,authenticated:true,token:'next-token',account:{userId:'registration-owner',loginId:'veteran_user',nickname:'老手'}};}
  else if(name==='software-update')value={status:'idle',autoCheck:false,canInstall:false};else value={};await route.fulfill({json:value});});
 await gate.goto(base+'/tests/auth-recovery-fixture.html');await gate.getByRole('tab',{name:'注册',exact:true}).waitFor().catch(async e=>{console.error('Gate diagnostic',errors,await gate.locator('body').innerText());throw e;});await gate.getByRole('tab',{name:'注册',exact:true}).click();await gate.getByLabel('昵称',{exact:true}).fill('老手');await gate.getByLabel('登录号',{exact:true}).fill('veteran_user');await gate.getByLabel('密码',{exact:true}).fill('test-password-123');await gate.getByLabel('确认密码',{exact:true}).fill('test-password-123');await gate.getByRole('radio',{name:'我是老手',exact:true}).check();await gate.getByRole('button',{name:'注册账号',exact:true}).click();await gate.waitForFunction(()=>window.__tbAccountUserId==='registration-owner');
 assert.deepEqual(Object.keys(posts.find(v=>v.name==='account/register').body).sort(),['loginId','nickname','password']);assert.equal(await gate.evaluate(()=>window.__tbExperienceChoicePending.choice),'experienced');await gate.close();
 assert.deepEqual(errors,[]);console.log('PASS experience choice, owner-scoped once-only prompt, exact registration transport, lower-level baseline, guarded owner race, permanent navigation and existing 1→5 animation; no real account or OJ traffic');
}finally{await browser.close();await vite.close();}
