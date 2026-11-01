import assert from 'node:assert/strict';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const vite=await createServer({server:{host:'127.0.0.1',port:0}});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage(),errors=[];page.on('pageerror',error=>errors.push(error.message));
try{
 await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/workbench-fixture.html`);
 const editor=page.getByRole('textbox',{name:'C++ 代码'}),submit=page.getByRole('button',{name:'提交',exact:true});
 await editor.fill('// A original submission');
 await page.evaluate(()=>{workbenchFixture.officialOpenDelay=650;workbenchFixture.officialStatus='judging';});
 await submit.click();
 await page.waitForFunction(()=>workbenchFixture.calls.some(call=>call.path==='official/submit'));
 await page.evaluate(()=>workbenchFixture.changeProblem('B'));
 await editor.fill('// B private draft');assert(await submit.isDisabled());
 await page.waitForFunction(()=>workbenchFixture.calls.some(call=>call.path.startsWith('official/status')));
 assert(await submit.isDisabled(),'Submit stays locked after the original open request returns on B');
 assert.equal(await page.evaluate(()=>workbenchFixture.calls.filter(call=>call.path==='official/close').length),0);
 await editor.press('Control+Enter');
 assert.equal(await page.evaluate(()=>workbenchFixture.calls.filter(call=>call.path==='official/submit').length),1);
 await page.evaluate(()=>{
   const fixture=workbenchFixture,id=Object.keys(fixture.officialSessions)[0],original=fixture.officialSessions[id];
   const receipt={id:'A-receipt',problemId:original.id,contestId:null,scope:'official',mode:'submit',verdict:'AC',code:original.code,submittedAt:new Date().toISOString(),finishedAt:new Date().toISOString(),message:'原站确认提交 #88'};
   fixture.submissions.push(receipt);original.saved=true;
   window.dispatchEvent(new CustomEvent('tb:official-status',{detail:{sessionId:id,status:'finished',verdict:'AC',submissionId:'88',submission:receipt}}));
 });
 await page.waitForFunction(()=>!document.querySelector('.wb-primary')?.disabled);
 assert.equal(await page.evaluate(()=>workbenchFixture.readCode()),'// B private draft');
 assert.equal(await page.locator('.wb-result-summary').count(),0,'A receipt never becomes B result');
 await page.waitForFunction(()=>workbenchFixture.progress.length===1);
 await page.evaluate(()=>workbenchFixture.changeProblem('A'));
 await page.waitForFunction(()=>workbenchFixture.readCode()==='// A original submission');
 await page.getByRole('button',{name:/记录/}).click();
 assert.match(await page.locator('.wb-history').innerText(),/AC/);
 assert.equal(await page.evaluate(()=>workbenchFixture.calls.filter(call=>call.path==='official/submit')[0].body.code),'// A original submission');
 assert.deepEqual(errors,[]);console.log('PASS changing A to B during opening and judging; B remains editable, global submit lock, original source and A receipt preserved, B draft isolated.');
}finally{await browser.close();await vite.close();}
