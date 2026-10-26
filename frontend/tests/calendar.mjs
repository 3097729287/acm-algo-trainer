import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const vite=await createServer({server:{host:'127.0.0.1',port:0,fs:{allow:[process.cwd(),fs.realpathSync('node_modules')]}}});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage(),errors=[];page.on('pageerror',error=>errors.push(error.message));
try{
  await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/calendar-fixture.html`);
  const toggle=page.getByRole('button',{name:'比赛日历',exact:true});
  await page.locator('.notification-dot').waitFor();await toggle.click();
  assert.deepEqual(await page.locator('.contest-calendar-day h3').allTextContents(),['今天','明天','后天','4天后']);
  const today=page.getByRole('group',{name:'今天',exact:true});
  assert.equal(await today.locator('.contest-calendar-row').count(),2);
  assert(await today.evaluate(el=>el.classList.contains('calendar-unread-today')));
  const colors=await today.locator('.contest-calendar-row').evaluateAll(rows=>rows.map(row=>getComputedStyle(row).backgroundColor));
  assert.equal(colors[0],colors[1]);
  await toggle.click();await toggle.click();assert.equal(await page.locator('.calendar-unread-today').count(),1,'opening alone does not mark read');
  await today.hover();await page.locator('.calendar-unread-today').waitFor({state:'detached'});await toggle.click();assert.equal(await page.locator('.notification-dot').count(),0);
  await page.reload();await toggle.click();assert.equal(await page.locator('.calendar-unread-today').count(),0,'read state survives reload');
  await page.evaluate(()=>{calendarFixture.events.push({...calendarFixture.events[0],id:'new'});calendarFixture.refresh();});
  await page.locator('.notification-dot').waitFor();await today.focus();await page.locator('.calendar-unread-today').waitFor({state:'detached'});
  await page.evaluate(()=>calendarFixture.account('another'));await page.locator('.notification-dot').waitFor();
  await page.evaluate(()=>calendarFixture.setNow(Date.parse('2026-10-27T10:00:00+08:00')));
  await page.waitForFunction(()=>document.querySelector('.contest-calendar-day h3')?.textContent==='今天'&&document.querySelectorAll('.calendar-unread-today .contest-calendar-row').length===1);
  assert.deepEqual(errors,[]);console.log('Calendar: relative dates, shared day surface, unread/hover/focus, persistence, new events, account/day rollover passed.');
}finally{await browser.close();await vite.close();}
