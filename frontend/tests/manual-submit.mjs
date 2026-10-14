import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdtemp,rm} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';
import {fixtureExtension} from './extension-fixture.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const server=spawn(process.env.TB_PYTHON||(process.platform==='win32'?'python':'python3'),['desktop/tests/browser_server.py'],{cwd:root,env:{...process.env,TB_OFFLINE:'1',TB_TEST_HYBRID:'1',PYTHONIOENCODING:'utf-8'},windowsHide:true});
let serverErrors='';server.stderr.on('data',b=>serverErrors+=b);
const {port}=await new Promise((resolve,reject)=>{let output='';server.stdout.on('data',b=>{output+=b;if(output.includes('\n'))resolve(JSON.parse(output.split('\n')[0]))});server.on('exit',code=>reject(new Error('fixture exited '+code+' '+serverErrors)))});
const base=`http://127.0.0.1:${port}`,profile=await mkdtemp(path.join(os.tmpdir(),'tb-manual-submit-'));
let browser,available=false,accepted=false,posts=0;
const header='<header id="header"><a href="/profile/fixture">fixture</a></header>';
const receipt='<table class="status-frame-datatable"><tr><th>Submission</th><th>Status</th></tr><tr><td><a href="/contest/123/submission/1002">1002</a><a href="/contest/123/problem/A">A</a><a href="/profile/fixture">fixture</a><span class="submissionVerdictWrapper">Accepted</span></td></tr></table>';
async function until(read,accept){for(let i=0;i<120;i++){const value=await read();if(accept(value))return value;await new Promise(r=>setTimeout(r,100));}throw new Error('Condition timed out: '+serverErrors)}
try{
 const extension=await fixtureExtension(path.join(root,'build/browser-extension'),profile,base);
 browser=await chromium.launchPersistentContext(profile,{channel:'msedge',headless:true,args:[`--disable-extensions-except=${extension}`,`--load-extension=${extension}`]});
 await browser.route('**/*',async route=>{
  const request=route.request(),u=new URL(request.url());
  if(u.hostname==='127.0.0.1')return route.continue();
  if(u.hostname!=='codeforces.com')return route.fulfill({status:503,body:'isolated'});
  if(request.method()==='POST'){posts++;assert.equal(new URLSearchParams(request.postData()).get('source'),'int main(){}');accepted=true;return route.fulfill({contentType:'text/html',body:header+receipt});}
  if(u.pathname.endsWith('/my'))return route.fulfill({contentType:'text/html',body:header+(accepted?receipt:'<table class="status-frame-datatable"><tr><th>Submission</th></tr></table>')});
  if(u.pathname==='/api/user.status')return route.fulfill({contentType:'application/json',body:'{"status":"OK","result":[]}'});
  const form='<form method="post"><input type="hidden" name="csrf_token" value="site-token"><select name="submittedProblemIndex"><option value="A">A</option></select><select name="programTypeId"><option value="54">GNU C++17</option></select><textarea name="source"></textarea><input type="submit" value="Submit"></form>';
  return route.fulfill({contentType:'text/html',body:header+(available?form:'<p>Submission editor unavailable</p>')});
 });
 const worker=browser.serviceWorkers()[0]||await browser.waitForEvent('serviceworker');
 await worker.evaluate(async base=>chrome.storage.local.set({bases:[base]}),base);
 await browser.pages()[0].goto(base+'/browser-connect.html');
 await until(async()=>(await(await fetch(base+'/fixture/browser')).json()),v=>v.connected&&v.hasWindow);
 await fetch(base+'/fixture/create?'+new URLSearchParams({key:'cf',url:'https://codeforces.com/contest/123/problem/A'}));
 const page=await until(async()=>browser.pages().find(p=>p.url().includes('/contest/123/submit')),Boolean);
 await until(async()=>page.evaluate(()=>!!window.__tbSubmissionWork),Boolean);
 const fallback=await(await fetch(base+'/fixture/manual')).json();
 assert.equal(fallback.cf.status,'awaiting_submit');
 assert.equal(posts,0);
 available=true;await page.reload();
 await until(async()=>page.locator('textarea').inputValue(),v=>v==='int main(){}');
 assert.equal(posts,0,'Prefilling never submits');
 await page.locator('input[type=submit]').click();
 const saved=await until(async()=>(await(await fetch(base+'/fixture/saved')).json()),v=>v.length===1);
 assert.equal(saved[0].verdict,'AC');assert.equal(posts,1);
 assert.ok(!page.isClosed(),'User-controlled submission tab remains open');
 console.log(JSON.stringify({ok:true,timeoutHandoff:true,prefilledWithoutPost:true,userSubmitCount:posts,officialReceiptSaved:true,realAccountSubmission:false}));
}finally{await browser?.close();server.kill();assert.equal(path.dirname(path.resolve(profile)),path.resolve(os.tmpdir()));assert.ok(path.basename(profile).startsWith('tb-manual-submit-'));await rm(profile,{recursive:true,force:true});}
