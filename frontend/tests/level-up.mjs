import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
import {chromium} from 'playwright';
import {createServer} from 'vite';
const vite=await createServer({server:{host:'127.0.0.1',port:0,watch:null}});await vite.listen();
const realFocus=process.env.TB_REAL_FOCUS==='1';
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:!realFocus,args:realFocus&&process.platform==='win32'?['--window-position=-20000,-20000']:[]});
const context=await browser.newContext({viewport:{width:1100,height:850}}),page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(8000);
const open=()=>page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/level-up-fixture.html`);
const snapshot=()=>page.evaluate(()=>levelFixture.snapshot()),emit=(level,revision,options={})=>page.evaluate(([l,r,o])=>levelFixture.emit(l,r,o),[level,revision,options]);
const dialog=()=>page.getByRole('dialog',{name:'等级提升',exact:true});
try{
 await open();await page.getByRole('navigation').waitFor();await page.waitForTimeout(80);console.log('baseline');assert.equal(await dialog().count(),0);assert.equal((await snapshot()).preferences.levelNoticeSeen,1);
 await page.getByRole('textbox',{name:'练习草稿'}).focus();await emit(3,2);await page.waitForTimeout(50);
 assert.equal(await dialog().count(),0);assert.equal((await snapshot()).preferences.levelNoticePending,3);
 assert.equal(await page.getByRole('navigation').getByRole('button',{name:'模拟赛',exact:true}).count(),1,'gates unlock immediately even while notices queue');
 console.log('queued');await page.getByRole('button',{name:'离开编辑器'}).click();await dialog().waitFor();console.log('visible');assert.match(await dialog().textContent(),/Lv\.1.*Lv\.3/s);
 await emit(4,3);await page.waitForTimeout(50);assert.match(await dialog().textContent(),/Lv\.4/);assert.equal(await dialog().getByRole('button',{name:'打开新解锁板块 实验室',exact:true}).count(),1);
 await page.keyboard.press('Tab');await page.keyboard.press('Shift+Tab');assert(await page.evaluate(()=>!!document.activeElement.closest('[data-level-up]')));
 await page.keyboard.press('Escape');await page.waitForTimeout(50);assert.equal(await dialog().count(),0);assert.equal((await snapshot()).preferences.levelNoticeSeen,4);
 assert(await page.locator('.level-new-entry').count()>0);await page.waitForTimeout(1500);assert.equal(await page.locator('.level-new-entry').count(),0);
 await emit(4,4);await page.waitForTimeout(50);assert.equal(await dialog().count(),0);await emit(2,1);assert.equal((await snapshot()).growth.level,4,'older authority cannot roll back features');
 await page.evaluate(()=>levelFixture.block(true));await emit(5,5);await page.waitForTimeout(50);assert.equal(await dialog().count(),0);await page.reload();await page.getByRole('navigation').waitFor();assert.equal((await snapshot()).preferences.levelNoticePending,5);
 await page.evaluate(()=>levelFixture.block(false));await dialog().waitFor();assert.match(await dialog().textContent(),/成长/);await page.keyboard.press('Escape');
 await page.evaluate(()=>levelFixture.other(true));await emit(6,6);await page.waitForTimeout(80);assert.equal(await dialog().count(),0);await page.getByRole('button',{name:'关闭',exact:true}).click();await dialog().waitFor();assert.equal(await dialog().locator('.level-up-next').count(),0,'no invented feature unlocks after Lv5');await page.keyboard.press('Escape');
 await page.evaluate(()=>levelFixture.switchOwner('second-account',11));await page.waitForTimeout(100);assert.equal(await dialog().count(),0);assert.equal((await snapshot()).preferences.levelNoticeSeen,11);
 await emit(20,40,{owner:'first-account'});await page.waitForTimeout(50);assert.equal((await snapshot()).growth.level,11);assert.equal(await dialog().count(),0);
 await emit(12,2,{epoch:'new-account'});await dialog().waitFor();await page.evaluate(()=>levelFixture.collapsed(true));
 await mkdir('tests/screenshots/level-up',{recursive:true});
 for(const theme of ['dark','light']){await page.evaluate(t=>levelFixture.theme(t),theme);await page.setViewportSize({width:430,height:700});await page.evaluate(()=>levelFixture.font(22));await page.waitForTimeout(1050);const box=await dialog().boundingBox();assert(box.width<=406&&box.height<=700*.85+1);assert.equal(await dialog().getByRole('button',{name:'继续学习',exact:true}).isVisible(),true);assert.equal(await dialog().locator('.level-up-current').evaluate(node=>getComputedStyle(node).opacity),'1');await page.screenshot({path:`tests/screenshots/level-up/${theme}-430-22.png`,animations:'disabled'});}
 await page.emulateMedia({reducedMotion:'reduce'});await page.waitForTimeout(80);assert.equal(await dialog().evaluate(node=>node.getAnimations({subtree:true}).filter(item=>item.playState==='running').length),0);
 await page.keyboard.press('Escape');assert.equal(await page.getByRole('navigation').getAttribute('data-collapsed'),'true');
 await emit(100,3,{epoch:'new-account'});await dialog().waitFor();assert.match(await dialog().textContent(),/已达等级上限/);assert.doesNotMatch(await dialog().innerHTML(),/NaN|Infinity/);await page.keyboard.press('Escape');
 if(realFocus){
  // Playwright forces page focus by default. Disable that browser override on
  // both real tabs so this checks native focus, without stubbing hasFocus().
  const otherPage=await context.newPage();await otherPage.setContent('<title>Foreground focus fixture</title><button>Other window</button>');
  const firstCdp=await context.newCDPSession(page),otherCdp=await context.newCDPSession(otherPage);
  await firstCdp.send('Emulation.setFocusEmulationEnabled',{enabled:false});await otherCdp.send('Emulation.setFocusEmulationEnabled',{enabled:false});
  await page.bringToFront();await page.waitForFunction(()=>document.hasFocus());
  await page.evaluate(()=>levelFixture.switchOwner('foreground-account',1));await page.waitForFunction(()=>levelFixture.snapshot().preferences.levelNoticeSeen===1);
  const draft=page.getByRole('textbox',{name:'练习草稿'}),draftText='retained draft during a real background upgrade';await draft.fill(draftText);await page.getByRole('button',{name:'离开编辑器'}).click();
  await otherPage.bringToFront();await page.waitForFunction(()=>!document.hasFocus());
  assert.equal(await page.evaluate(()=>document.hidden),false,'a visible but unfocused window must also defer notices');
  assert.equal(await page.evaluate(()=>document.activeElement.tagName),'BUTTON','typing must not be the reason this background notice queues');
  await emit(2,2,{epoch:'new-account'});await emit(4,3,{epoch:'new-account'});await page.waitForTimeout(600);
  assert.equal(await dialog().count(),0);assert.equal((await snapshot()).preferences.levelNoticePending,4);assert.equal((await snapshot()).preferences.levelNoticeSeen,1);assert.equal(await draft.inputValue(),draftText);
  assert.equal(await page.evaluate(()=>document.hasFocus()),false,'pending notices must not steal native focus');
  await page.bringToFront();await dialog().waitFor();assert.match(await dialog().textContent(),/Lv\.1.*Lv\.4/s);
  await otherPage.bringToFront();await page.waitForFunction(()=>!document.hasFocus());await emit(5,4,{epoch:'new-account'});await page.waitForTimeout(80);
  assert.match(await dialog().textContent(),/Lv\.5/);assert.equal(await page.evaluate(()=>document.hasFocus()),false);
  await dialog().getByRole('button',{name:'关闭等级提升',exact:true}).evaluate(button=>button.click());await page.waitForTimeout(80);
  assert.equal((await snapshot()).preferences.levelNoticeSeen,4,'an update rendered behind another window was not presented');assert.equal((await snapshot()).preferences.levelNoticePending,5);assert.equal(await dialog().count(),0);
  await page.bringToFront();await dialog().waitFor();assert.match(await dialog().textContent(),/Lv\.4.*Lv\.5/s);await page.keyboard.press('Escape');assert.equal((await snapshot()).preferences.levelNoticeSeen,5);
  await emit(6,5,{epoch:'new-account'});await dialog().waitFor();await otherPage.bringToFront();await page.waitForFunction(()=>!document.hasFocus());await emit(7,6,{epoch:'new-account'});await page.waitForTimeout(80);
  await page.bringToFront();await page.waitForFunction(()=>document.hasFocus());await page.keyboard.press('Escape');assert.equal((await snapshot()).preferences.levelNoticeSeen,7,'returning to the foreground presents the current merged level');assert.equal((await snapshot()).preferences.levelNoticePending,0);assert.equal(await draft.inputValue(),draftText);
  await otherPage.close();console.log('PASS real foreground/background focus, merged pending levels, retained draft, no native focus theft, unseen background update acknowledgment, focus-return presentation');
 }
 assert.deepEqual(errors,[]);console.log('PASS baseline/nohistoricalnotice, editingqueue, immediateunlock, combinedvisibleupdate, focus/Esc, nonrepeatedfeedback, pendingrestart, othermodal, accountstale, dark/light narrow/font22/reducedmotion, level100');
}finally{await browser.close();await vite.close();}
