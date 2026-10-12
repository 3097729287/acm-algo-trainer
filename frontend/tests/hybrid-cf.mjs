// Real extension + BrowserBridge with cookie sync enabled. Disposable profile;
// all official GET/POST requests intercepted and no foreground tab changes.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdtemp,rm} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const server=spawn(process.env.TB_PYTHON||'C:/Users/lenovo/AppData/Local/Programs/Python/Python313/python.exe',['desktop/tests/browser_server.py'],{cwd:root,env:{...process.env,TB_OFFLINE:'1',TB_TEST_HYBRID:'1',PYTHONIOENCODING:'utf-8'},windowsHide:true});
let serverErrors='';server.stderr.on('data',b=>{serverErrors+=b});
const {port}=await new Promise((resolve,reject)=>{let output='';server.stdout.on('data',b=>{output+=b;if(output.includes('\n'))resolve(JSON.parse(output.split('\n')[0]))});server.on('exit',code=>reject(new Error('Fixture server exited '+code)))});
const base=`http://127.0.0.1:${port}`,profile=await mkdtemp(path.join(os.tmpdir(),'tb-hybrid-cf-'));
const extension=process.env.TB_BROWSER_EXTENSION||path.join(root,'build/browser-extension');
let browser;const posts=[];let accepted=false;const errors=[],requests=[];
try{
 browser=await chromium.launchPersistentContext(profile,{channel:'msedge',headless:true,args:[`--disable-extensions-except=${extension}`,`--load-extension=${extension}`]});
 const worker=browser.serviceWorkers()[0]||await browser.waitForEvent('serviceworker');
 await worker.evaluate(async base=>chrome.storage.local.set({bases:[base]}),base);
 const foreground=browser.pages()[0];await foreground.goto(base+'/browser-connect.html');
 const active=await worker.evaluate(async()=>(await chrome.tabs.query({active:true,lastFocusedWindow:true}))[0].id);
 await browser.addCookies([{name:'fixture_login',value:'actual-browser-session',domain:'codeforces.com',path:'/',secure:true,httpOnly:true,sameSite:'Lax'}]);
 browser.on('page',p=>p.on('pageerror',e=>errors.push({url:p.url(),message:e.stack||e.message})));
 await browser.route('**/*',async route=>{
  const req=route.request(),url=new URL(req.url());if(url.hostname==='127.0.0.1')return route.continue();
  requests.push({url:req.url(),type:req.resourceType()});
  assert.equal(url.hostname,'codeforces.com');
  if(req.method()==='POST'){
   const form=new URLSearchParams(req.postData());
   assert.equal(form.get('source'),'int main(){}');assert.equal(form.get('csrf_token'),'fixture-csrf');
   assert.ok((await req.allHeaders()).cookie.includes('fixture_login=actual-browser-session'));
   posts.push(req.url());accepted=true;return route.fulfill({contentType:'text/html',body:'<table class="status-frame-datatable"><tr><td><a href="/contest/123/submission/1002">1002</a><a href="/contest/123/problem/A">A</a><a href="/profile/fixture">fixture</a><span class="submissionVerdictWrapper">Accepted</span></td></tr></table>'});
  }
  const account='<header id="header"><a href="/profile/fixture">fixture</a></header>';
  if(url.pathname.endsWith('/my'))return route.fulfill({contentType:'text/html',body:account+'<table class="status-frame-datatable"><tr><th>Submission</th><th>Status</th></tr>'+(accepted?'<tr><td><a href="/contest/123/submission/1002">1002</a><a href="/contest/123/problem/A">A</a><a href="/profile/fixture">fixture</a><span class="submissionVerdictWrapper">Accepted</span></td></tr>':'')+'</table>'});
  if(url.pathname==='/api/user.status')return route.fulfill({contentType:'application/json',body:JSON.stringify({status:'OK',result:[]})});
  return route.fulfill({contentType:'text/html',body:account+'<form method="post"><input name="csrf_token" value="fixture-csrf" type="hidden"><select name="submittedProblemIndex"><option value="A">A</option></select><select name="programTypeId"><option value="54">GNU C++17</option></select><textarea name="source"></textarea><input type="submit" value="Submit"></form>'});
 });
 for(let i=0;i<100;i++){const value=await(await fetch(base+'/fixture/browser')).json();if(value.connected&&value.hasWindow)break;await new Promise(r=>setTimeout(r,100))}
 const started=performance.now();
 const response=await fetch(base+'/fixture/create?'+new URLSearchParams({key:'cf',url:'https://codeforces.com/contest/123/problem/A'}));assert.equal(response.status,200);
 let status;
 for(let i=0;i<150;i++){status=(await(await fetch(base+'/fixture/status')).json()).cf;if(status.status==='finished')break;if(status.status==='error')throw new Error(JSON.stringify(status));await new Promise(r=>setTimeout(r,100))}
 if(status.verdict!=='AC')console.log(JSON.stringify({status,serverErrors,errors,pages:await Promise.all(browser.pages().map(async p=>({url:p.url(),dom:await p.evaluate(()=>({ready:document.readyState,text:document.body?.innerText?.slice(0,250),work:window.__tbSubmissionWork?.key,commandListener:String(window.tbOfficialPage).slice(0,50)}))}))),jobs:await worker.evaluate(async()=>Object.values((await chrome.storage.session.get('jobs')).jobs||{}).map(j=>({sessionId:j.sessionId,tabId:j.tabId,base:j.base})))}));
 assert.equal(status.verdict,'AC',JSON.stringify(status));assert.equal(status.submissionId,'1002');assert.equal(posts.length,1);
 assert.equal((await(await fetch(base+'/fixture/opened')).json()).length,0);
 assert.equal(await worker.evaluate(async()=>(await chrome.tabs.query({active:true,lastFocusedWindow:true}))[0].id),active);
 assert.deepEqual(errors,[],JSON.stringify({errors,requests}));
 console.log(JSON.stringify({ok:true,hybridMode:true,actualBrowserCookiesPreserved:true,nativeFormCsrf:true,exactReceipt:true,fixtureSeconds:Number(((performance.now()-started)/1000).toFixed(3)),posts:1,foregroundUnchanged:true,realAccountSubmission:false}));
}finally{
 if(browser)await browser.close();server.kill();
 assert.ok(path.resolve(profile).startsWith(path.resolve(os.tmpdir())+path.sep));
 await rm(profile,{recursive:true,force:true,maxRetries:10,retryDelay:200});
}
