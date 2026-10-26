import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const vite=await createServer({server:{host:'127.0.0.1',port:0,fs:{allow:[process.cwd(),fs.realpathSync('node_modules')]}}});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});const page=await browser.newPage(),errors=[];
page.on('pageerror',error=>errors.push(error.message));
try{
  await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/workbench-fixture.html`);
  await page.getByRole('textbox',{name:'C++ 代码'}).fill('int main() { return 0; }');
  await page.evaluate(()=>{workbenchFixture.officialStatus='judging';workbenchFixture.officialPollDelay=1000;workbenchFixture.workspaceDelay=900;});
  await page.getByRole('button',{name:'提交',exact:true}).click();
  await page.waitForFunction(()=>workbenchFixture.calls.some(call=>call.path.startsWith('official/status')));
  const started=await page.evaluate(()=>{
    const fixture=workbenchFixture,sessionId=Object.keys(fixture.officialSessions).at(-1),session=fixture.officialSessions[sessionId];
    const submission={id:'native-official',problemId:session.id,contestId:null,mode:'submit',scope:'official',code:session.code,verdict:'AC',submittedAt:new Date().toISOString(),finishedAt:new Date().toISOString(),message:'原站确认提交 #456'};
    fixture.submissions.push(submission);fixture.nativeTime=performance.now();
    window.dispatchEvent(new CustomEvent('tb:official-status',{detail:{sessionId,status:'finished',submissionId:'456',verdict:'AC',receiptSaved:true,submission}}));
    return fixture.nativeTime;
  });
  await page.waitForFunction(()=>document.querySelector('.wb-result-summary')?.textContent.includes('AC'));
  const elapsed=await page.evaluate(start=>performance.now()-start,started);assert(elapsed<300,`native receipt display delayed ${elapsed}ms`);
  await page.waitForFunction(()=>workbenchFixture.ackVisible===true);
  await page.waitForTimeout(1100);assert.equal(await page.getByLabel('原站提交状态').count(),0,'late polling cannot overwrite the pushed terminal result');
  await page.getByRole('button',{name:'运行样例',exact:true}).click();
  await page.waitForFunction(()=>workbenchFixture.submissions.some(row=>row.mode==='run'));
  await page.evaluate(()=>{
    const row=workbenchFixture.submissions.find(row=>row.mode==='run');
    window.dispatchEvent(new CustomEvent('tb:submission-status',{detail:{submission:{...row,verdict:'TLE',finishedAt:new Date().toISOString(),message:'fixture timeout'}}}));
  });
  await page.waitForFunction(()=>document.querySelector('.wb-result-summary')?.textContent.includes('TLE'));
  assert.deepEqual(errors,[]);console.log(`Native result push displayed in ${Math.round(elapsed)} ms; visible-result acknowledgement and stale-poll guard passed.`);
}finally{await browser.close();await vite.close();}
