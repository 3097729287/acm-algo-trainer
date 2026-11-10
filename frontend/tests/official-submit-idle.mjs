// Real React/CodeMirror, synthetic receipts only. No site or existing profile.
import assert from 'node:assert/strict';
import {mkdir,readFile,realpath,writeFile} from 'node:fs/promises';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createServer} from 'vite';
import react from '@vitejs/plugin-react';
import {chromium} from 'playwright';

const frontend=resolve(dirname(fileURLToPath(import.meta.url)),'..'),root=resolve(frontend,'..');
const out=resolve(process.env.TB_SUBMIT_TEST_OUTPUT||resolve(root,'.backups/submission-idle-ui',String(Date.now())));
await mkdir(out,{recursive:true});
const vite=await createServer({configFile:false,root:frontend,plugins:[react()],cacheDir:resolve(out,'vite'),
  optimizeDeps:{entries:['tests/workbench-fixture.html']},resolve:{alias:{'@':resolve(frontend,'src')}},
  define:{__TB_VERSION__:JSON.stringify((await readFile(resolve(root,'VERSION'),'utf8')).trim())},
  server:{host:'127.0.0.1',port:0,fs:{allow:[root,frontend,await realpath(resolve(frontend,'node_modules'))]}}});
await vite.listen();const origin='http://127.0.0.1:'+vite.httpServer.address().port;
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const errors=[],checks=[];
async function fixture(){
  const page=await browser.newPage({viewport:{width:1280,height:850}});page.setDefaultTimeout(12000);
  page.on('pageerror',error=>errors.push(error.message));
  await page.route('**/*',route=>new URL(route.request().url()).origin===origin?route.continue():route.abort('blockedbyclient'));
  await page.goto(origin+'/tests/workbench-fixture.html',{waitUntil:'domcontentloaded',timeout:60000});
  await page.locator('.cm-content[contenteditable=true]').waitFor({timeout:60000});
  await page.evaluate(()=>{
    workbenchFixture.officialStatus='judging';
    workbenchFixture.officialSnapshot=(snapshot,session)=>({...snapshot,submissionId:session.submissionId||(session.submissionId=String(85470510+Number(snapshot.sessionId.split('-').at(-1))))});
  });return page;
}
async function emitReceipt(page,{sid,remote,code,verdict='CE',stored=true,official=false}){
  return page.evaluate(({sid,remote,code,verdict,stored,official})=>{
    const f=workbenchFixture,session=f.officialSessions[sid];
    const row={id:'receipt-'+remote,problemId:session.id,contestId:null,language:'cpp17',mode:'submit',scope:'official',code:code??session.code,
      verdict,finishedAt:new Date().toISOString(),submittedAt:new Date().toISOString(),message:'原站确认提交 #'+remote};
    if(stored)f.submissions.push(row);
    if(official)window.dispatchEvent(new CustomEvent('tb:official-status',{detail:{sessionId:sid,status:'finished',submissionId:remote,verdict,submission:row}}));
    else window.dispatchEvent(new CustomEvent('tb:submission-status',{detail:{submission:row}}));
    return performance.now();
  },{sid,remote,code,verdict,stored,official});
}
const submit=page=>page.getByRole('button',{name:'提交',exact:true});
try{
  const page=await fixture();
  await page.getByRole('textbox',{name:'C++ 代码'}).fill('// exact first submitted source');
  await page.evaluate(()=>{workbenchFixture.officialPollDelay=700;workbenchFixture.workspaceDelay=1500});
  await submit(page).click();await page.getByText('评测中',{exact:true}).waitFor();
  await page.waitForFunction(()=>workbenchFixture.calls.filter(c=>c.path.startsWith('official/status')).length>=2);
  await page.getByRole('textbox',{name:'C++ 代码'}).fill('// later unsent editor change');
  const start=await emitReceipt(page,{sid:'official-1',remote:'85470511'});
  await page.waitForFunction(()=>!document.querySelector('.wb-primary')?.disabled);
  const elapsed=await page.evaluate(start=>performance.now()-start,start);assert(elapsed<1000,'Persisted CE releases busy without waiting for workspace');
  assert.equal(await page.locator('.wb-result-summary').getAttribute('data-submission-id'),'receipt-85470511');
  assert.equal(await page.evaluate(()=>workbenchFixture.readCode()),'// later unsent editor change');
  await page.evaluate(()=>window.dispatchEvent(new CustomEvent('tb:official-status',{detail:{sessionId:'official-1',submissionId:'85470511',status:'judging'}})));
  await page.waitForTimeout(800);assert(await submit(page).isEnabled(),'Late judging push/poll cannot revive the spinner');
  checks.push({name:'persisted CE settles the exact frozen source immediately; late judging cannot regress',milliseconds:Math.round(elapsed)});

  await page.getByRole('textbox',{name:'C++ 代码'}).fill('// exact second submitted source');
  await submit(page).click();await page.getByText('评测中',{exact:true}).waitFor();
  assert.equal(await page.evaluate(()=>workbenchFixture.calls.filter(c=>c.path==='official/submit').length),2);
  await emitReceipt(page,{sid:'official-1',remote:'85470511',stored:false,official:true});
  await emitReceipt(page,{sid:'official-1',remote:'85470511',stored:false});
  await emitReceipt(page,{sid:'official-2',remote:'85470512',code:'// stale source',stored:false});
  await page.waitForTimeout(120);assert(await submit(page).isDisabled(),'Old CE and correct-ID/wrong-source cannot release the second attempt');
  await emitReceipt(page,{sid:'official-2',remote:'85470512',verdict:'WA'});
  await page.waitForFunction(()=>!document.querySelector('.wb-primary')?.disabled);
  assert.equal(await page.locator('.wb-result-summary').getAttribute('data-submission-id'),'receipt-85470512');
  assert.match(await page.locator('.wb-result-summary').innerText(),/WA/);
  assert.equal(await page.evaluate(()=>workbenchFixture.calls.filter(c=>c.path==='official/submit').length),2,'No automatic resubmit');
  await page.close();checks.push({name:'a second submission works; previous CE and mismatched source stay isolated'});

  const early=await fixture();await early.getByRole('textbox',{name:'C++ 代码'}).fill('// fast accepted source');
  await early.evaluate(()=>workbenchFixture.officialOpenDelay=350);
  await submit(early).click();await early.waitForFunction(()=>workbenchFixture.calls.some(c=>c.path==='official/submit'));
  await emitReceipt(early,{sid:'official-1',remote:'85470513',official:true});
  await early.waitForFunction(()=>document.querySelector('.wb-result-summary')?.dataset.submissionId==='receipt-85470513');
  assert(await submit(early).isEnabled());
  assert.equal(await early.evaluate(()=>workbenchFixture.calls.filter(c=>c.path==='official/submit').length),1);
  assert.equal(await early.evaluate(()=>workbenchFixture.calls.filter(c=>c.path.startsWith('official/status')).length),0,'A terminal event before open response is retained');
  await early.close();checks.push({name:'terminal receipt before opening response is attached only to its returned SID'});
  assert.deepEqual(errors,[]);
  const result={ok:true,checks,pageErrors:errors,realSiteRequests:0,realProviderRequests:0,existingBrowserProfilesUsed:false};
  await writeFile(resolve(out,'result.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({...result,out}));
}finally{await browser.close();await vite.close()}
