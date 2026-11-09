// Actual Workbench/CodeMirror rendering. All APIs are isolated in-memory
// fixtures; no original-site login, request, verdict or account is created.
import assert from 'node:assert/strict';
import {mkdir,writeFile,readFile,realpath} from 'node:fs/promises';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createServer} from 'vite';
import react from '@vitejs/plugin-react';
import {chromium} from 'playwright';

const frontend=resolve(dirname(fileURLToPath(import.meta.url)),'..'),root=resolve(frontend,'..');
const out=resolve(root,'.backups/review-latest-ac-20261109/official-result-ack',String(Date.now()));
await mkdir(out,{recursive:true});
const server=await createServer({configFile:false,root:frontend,plugins:[react()],
 cacheDir:resolve(out,'vite'),optimizeDeps:{entries:['tests/workbench-fixture.html']},
 define:{__TB_VERSION__:JSON.stringify((await readFile(resolve(root,'VERSION'),'utf8')).trim())},
 resolve:{alias:{'@':resolve(frontend,'src')}},
 server:{host:'127.0.0.1',port:0,fs:{allow:[frontend,await realpath(resolve(frontend,'node_modules'))]}}});
await server.listen();
const origin='http://127.0.0.1:'+server.httpServer.address().port;
const browser=process.env.TB_TEST_REUSE_PROFILE
 ?await chromium.launchPersistentContext(process.env.TB_TEST_REUSE_PROFILE,{channel:'msedge',headless:true})
 :await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const errors=[],checks=[];
async function fixture(recovery=false){
 const page=await browser.newPage({viewport:{width:1280,height:850}});page.setDefaultTimeout(12000);
 page.on('pageerror',error=>errors.push(error.message));
 await page.route('**/*',route=>new URL(route.request().url()).origin===origin?route.continue():route.abort('blockedbyclient'));
 await page.addInitScript(()=>{localStorage.clear();window.ackFrameCounter=0;const frame=()=>{window.ackFrameCounter++;requestAnimationFrame(frame)};requestAnimationFrame(frame)});
 if(recovery)await page.addInitScript(()=>{
  window.officialRecoveryStatus='judging';
  window.officialRecoveryDrafts={'solo:A':'current unsent code after restart'};
  window.officialRecoverySessions={'recovered-old':{id:'A',code:'original sent code',submissionId:'900004',status:'loading',autoClose:true}};
  window.officialRecoveryFixture={A:{sessionId:'recovered-old',submissionId:'900004',platform:'AtCoder',status:'judging',readOnlyRestore:true,autoClose:true,message:'正在恢复查询原提交 #900004，不会重新发送代码。'}};
 });
 await page.goto(origin+'/tests/workbench-fixture.html');
 await page.locator('.cm-content[contenteditable=true]').waitFor();
 await page.evaluate(()=>{workbenchFixture.officialStatus='judging';workbenchFixture.officialIncludeSubmission=true});
 return page;
}
const ackCount=page=>page.evaluate(()=>workbenchFixture.calls.filter(c=>c.path==='official/ack').length);
try{
 const page=await fixture();
 await page.evaluate(()=>workbenchFixture.asyncBrowserAck=true);
 await page.getByRole('button',{name:'提交',exact:true}).click();
 await page.getByText('评测中',{exact:true}).waitFor();
 assert.equal(await ackCount(page),0,'Opening/clicking/judging is never an acknowledgement');
 await page.evaluate(()=>{document.querySelector('.fixture').style.display='none';workbenchFixture.officialVerdict='CE';workbenchFixture.officialStatus='finished'});
 await page.waitForFunction(()=>Object.values(workbenchFixture.officialSessions).some(s=>s.saved));
 await page.waitForTimeout(120);
 assert.equal(await ackCount(page),0,'A committed hidden result has not been shown');
 await page.evaluate(()=>{document.querySelector('.fixture').style.display=''});
 await page.waitForFunction(()=>workbenchFixture.ackFacts?.length===1);
 const proof=await page.evaluate(()=>({ack:workbenchFixture.ackFacts[0],session:Object.values(workbenchFixture.officialSessions)[0]}));
 assert.equal(proof.ack.displayId,proof.session.submission.id);assert.equal(proof.ack.verdict,'CE');
 assert.ok(proof.ack.visible&&proof.ack.documentVisible);assert.ok(proof.ack.frame>=proof.session.savedFrame+2);
 await page.waitForTimeout(850);assert.equal(await ackCount(page),1,'A real display ACK stops retries while the extension closes its tab asynchronously');
 await page.screenshot({path:resolve(out,'shown-ce.png')});await page.close();checks.push('hidden CE waits for exact visible persisted result and two paint frames');

 const history=await fixture();
 await history.evaluate(()=>{workbenchFixture.submissions.push({id:'old-official',problemId:'A',contestId:null,mode:'submit',scope:'official',verdict:'AC',finishedAt:'2026-10-01T00:00:00Z',submittedAt:'2026-10-01T00:00:00Z',message:'原站确认提交 #100'});workbenchFixture.changeProblem('B')});
 await history.waitForFunction(()=>document.querySelector('.tb-workbench')?.dataset.problemId==='B');
 await history.evaluate(()=>workbenchFixture.changeProblem('A'));
 await history.getByRole('button',{name:/^记录/}).click();await history.locator('.wb-history-main').first().click();
 await history.waitForFunction(()=>document.querySelector('.wb-result-summary')?.dataset.submissionId==='old-official');
 await history.getByRole('button',{name:'提交',exact:true}).click();
 await history.getByText('评测中',{exact:true}).waitFor();
 await history.evaluate(()=>{document.querySelector('.fixture').style.display='none';workbenchFixture.officialStatus='finished'});
 await history.waitForFunction(()=>document.querySelector('.wb-result-summary')?.dataset.submissionId==='official-1');
 await history.evaluate(()=>[...document.querySelectorAll('.wb-console-tabs button')].find(n=>n.textContent.startsWith('记录'))?.click());
 // Use the real React controls while their containing app is hidden, to model
 // a different history choice before the completed result is ever painted.
 await history.waitForFunction(()=>document.querySelectorAll('.wb-history-main').length===2);
 await history.evaluate(()=>document.querySelectorAll('.wb-history-main')[1].click());
 await history.waitForFunction(()=>document.querySelector('.wb-result-summary')?.dataset.submissionId==='old-official');
 await history.evaluate(()=>document.querySelector('.fixture').style.display='');
 await history.waitForTimeout(150);assert.equal(await ackCount(history),0,'A different historical AC cannot close this submission');
 await history.getByRole('button',{name:/^记录/}).click();await history.locator('.wb-history-main').first().click();
 await history.waitForFunction(()=>workbenchFixture.ackFacts?.length===1);
 assert.equal(await history.evaluate(()=>workbenchFixture.ackFacts[0].displayId),'official-1');
 await history.close();checks.push('same-verdict older history row cannot acknowledge the new SID');

 const other=await fixture();await other.getByRole('button',{name:'提交',exact:true}).click();
 await other.getByText('评测中',{exact:true}).waitFor();
 await other.evaluate(()=>workbenchFixture.changeProblem('B'));await other.waitForFunction(()=>document.querySelector('.tb-workbench')?.dataset.problemId==='B');
 await other.evaluate(()=>workbenchFixture.officialStatus='finished');await other.waitForFunction(()=>Object.values(workbenchFixture.officialSessions).some(s=>s.saved));
 await other.waitForTimeout(120);assert.equal(await ackCount(other),0,'A result arriving in another problem is not displayed');
 await other.evaluate(()=>workbenchFixture.changeProblem('A'));await other.getByRole('button',{name:'运行结果',exact:true}).click();await other.waitForFunction(()=>workbenchFixture.ackFacts?.length===1);
 await other.close();checks.push('background problem completion waits until its own result is visible');

 const manual=await fixture();await manual.evaluate(()=>workbenchFixture.officialStatus='needs_login');
 await manual.getByRole('button',{name:'提交',exact:true}).click();await manual.getByRole('button',{name:'在浏览器查看',exact:true}).click();
 await manual.evaluate(()=>workbenchFixture.officialStatus='finished');await manual.waitForFunction(()=>document.querySelector('.wb-result-summary')?.dataset.submissionId==='official-2');
 await manual.waitForTimeout(150);assert.equal(await ackCount(manual),0,'A manually opened page stays open after its real result');
 await manual.close();checks.push('manual browser inspection never auto-closes');
 const recovered=await fixture(true);await recovered.getByText('评测中',{exact:true}).waitFor();
 assert.equal(await recovered.evaluate(()=>workbenchFixture.readCode()),'current unsent code after restart');
 assert.equal(await recovered.evaluate(()=>workbenchFixture.calls.filter(c=>c.path==='official/submit').length),0);
 await recovered.evaluate(()=>{workbenchFixture.officialVerdict='WA';workbenchFixture.officialStatus='finished'});
 await recovered.waitForFunction(()=>workbenchFixture.ackFacts?.length===1);
 assert.equal(await recovered.evaluate(()=>workbenchFixture.ackFacts[0].displayId),'recovered-old');
 assert.equal(await recovered.evaluate(()=>workbenchFixture.submissions[0].code),'original sent code');
 assert.equal(await recovered.evaluate(()=>workbenchFixture.readCode()),'current unsent code after restart');
 assert.equal(await recovered.evaluate(()=>workbenchFixture.calls.filter(c=>c.path==='official/submit'||c.path==='official/open').length),0);
 await recovered.close();checks.push('restart attaches persisted SID, polls without submitting, displays exact WA and preserves current input');
 assert.deepEqual(errors,[]);await writeFile(resolve(out,'result.log'),JSON.stringify({ok:true,checks,pageErrors:errors,realSiteRequests:0},null,2));
 console.log(JSON.stringify({ok:true,checks,out,pageErrors:errors,realSiteRequests:0}));
}finally{await browser.close();await server.close()}
