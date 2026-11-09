// Real v4 service worker, background tabs and native forms. Every original
// site request is intercepted; only a disposable loopback server is reached.
import assert from 'node:assert/strict';
import {spawn,execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {mkdir,readFile,writeFile,readdir,lstat,copyFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..'),run=promisify(execFile);
const out=path.join(root,'.backups/review-latest-ac-20261109/connected-browser',String(Date.now()));await mkdir(out,{recursive:true});
const python=process.env.TB_PYTHON||'python';
const server=spawn(python,['-B','-u','desktop/tests/connected_server.py'],{cwd:root,windowsHide:true,env:{...process.env,TB_OFFLINE:'1',PYTHONDONTWRITEBYTECODE:'1',PYTHONIOENCODING:'utf-8'},stdio:['ignore','pipe','pipe']});
let stderr='';server.stderr.on('data',chunk=>stderr+=chunk);
const {port}=await new Promise((resolve,reject)=>{let text='';server.stdout.on('data',chunk=>{text+=chunk;if(text.includes('\n'))resolve(JSON.parse(text.split('\n')[0]))});server.once('exit',code=>reject(Error('Fixture exited '+code+' '+stderr)))});
const base='http://127.0.0.1:'+port,extension=path.join(out,'extension');
await run(python,['-B','scripts/build_browser_extension.py',extension,'--base-url',base],{cwd:root,windowsHide:true,env:{...process.env,PYTHONDONTWRITEBYTECODE:'1'}});
const manifest=JSON.parse(await readFile(path.join(extension,'manifest.json'),'utf8'));
assert.deepEqual(manifest.permissions.sort(),['alarms','storage']);
for(const name of ['worker.js','content.js','main.js'])assert(!/chrome\.cookies|cookies\/get|\/api\/browser\/session/.test(await readFile(path.join(extension,name),'utf8')));
assert(!JSON.stringify(manifest).includes('<all_urls>'));assert(!manifest.permissions.includes('debugger'));
const profile=process.env.TB_TEST_REUSE_PROFILE||path.join(out,'profile');
// Chromium remembers an unpacked extension's physical directory across reuse
// of this test-only profile. Preserve the previous PUBLIC bundle, then refresh
// its known fixture directory. No browser preferences or login store is read.
let runtimeExtension=extension;
if(process.env.TB_TEST_RUNTIME_EXTENSION){
 runtimeExtension=path.resolve(process.env.TB_TEST_RUNTIME_EXTENSION);
 assert(runtimeExtension.startsWith(path.join(root,'.backups/review-latest-ac-20261109/connected-browser')+path.sep)&&path.basename(runtimeExtension)==='extension');
 const previous=path.join(out,'runtime-previous');await mkdir(previous);let total=0;
 for(const name of await readdir(runtimeExtension)){const file=path.join(runtimeExtension,name),info=await lstat(file);assert(info.isFile()&&!info.isSymbolicLink());total+=info.size;assert(total<1048576);await copyFile(file,path.join(previous,name))}
 for(const name of await readdir(extension))await copyFile(path.join(extension,name),path.join(runtimeExtension,name));
}
let browser,worker;const errors=[],unexpected=[],posts=[],checks=[];let loginNeeded=false,ncCount=0,cfCount=0,acCount=0,lgCount=0,qojCount=0;
const source='int main(){}',knownHosts=new Set(['codeforces.com','atcoder.jp','ac.nowcoder.com','www.luogu.com.cn','qoj.ac']);
const account=platform=>platform==='Codeforces'?'<header id="header"><a href="/profile/fixture">fixture</a><a href="/logout">Logout</a></header>':platform==='AtCoder'?'<nav class="navbar"><a href="/users/fixture">fixture</a><a href="/logout">Logout</a></nav>':'<nav class="navbar"><a href="/user/profile/fixture">fixture</a><a href="/logout">Logout</a></nav>';
const cfRow=id=>`<tr><td><a href="/contest/123/submission/${id}">${id}</a><a href="/contest/123/problem/A">A</a><a href="/profile/fixture">fixture</a></td><td class="submissionVerdictWrapper">Accepted</td></tr>`;
const acRow=id=>`<tr><td><a href="/contests/abc100/submissions/${id}">${id}</a><a href="/contests/abc100/tasks/abc100_a">A</a><a href="/users/fixture">fixture</a></td><td class="label">AC</td></tr>`;
const table=rows=>'<table class="status-frame-datatable"><tr><th>Submission</th><th>Status</th></tr>'+rows+'</table>';
const qojList=()=>account('QOJ')+'<table><thead><tr><th>ID</th><th>Problem</th><th>Submitter</th><th>Score</th></tr></thead><tbody>'+(qojCount?'<tr><td><a href="/submission/5001">5001</a></td><td><a href="/problem/15032">A</a></td><td><a href="/user/profile/fixture">fixture</a></td><td>100</td></tr>':'')+'</tbody></table>';
const nativeForm=(platform,problem)=>`<form method="post"><input type="hidden" name="csrf_token" value="fixture-native-token"><select name="${platform==='AtCoder'?'data.TaskScreenName':'submittedProblemIndex'}"><option value="${problem}">${problem}</option></select><select name="${platform==='AtCoder'?'data.LanguageId':'programTypeId'}"><option value="54">GNU C++17</option><option value="4006">Python 3</option></select><textarea name="sourceCode"></textarea><button type="submit" ${platform==='Codeforces'?'disabled':''}>Submit</button></form>${platform==='Codeforces'?'<script>setTimeout(()=>document.querySelector("button").disabled=false,1200)</script>':''}`;
async function get(pathname){const r=await fetch(base+pathname);if(!r.ok)throw Error('Fixture HTTP '+r.status+' '+await r.text());return r.json()}
async function until(read,accept,timeout=25000){let value;const end=Date.now()+timeout;while(Date.now()<end){value=await read();if(accept(value))return value;await new Promise(r=>setTimeout(r,100))}throw Error('Timed out: '+JSON.stringify(value)+' '+stderr.slice(-1500))}
const state=(key,status)=>until(async()=>(await get('/fixture/status'))[key],value=>value?.status===status);
async function create(key,url,language='cpp17',code=source,manual=false){return get('/fixture/create?'+new URLSearchParams({key,url,language,code,...(manual?{manual:'1'}:{})}))}
try{
 browser=await chromium.launchPersistentContext(profile,{channel:process.env.CI?undefined:'msedge',headless:true,ignoreHTTPSErrors:true,args:[`--disable-extensions-except=${runtimeExtension}`,`--load-extension=${runtimeExtension}`,'--disable-background-networking']});
 browser.on('page',page=>page.on('pageerror',issue=>errors.push(issue.message)));
 await browser.route('**/*',async route=>{
  const request=route.request(),url=new URL(request.url());if(url.hostname==='127.0.0.1'||url.protocol==='chrome-extension:'&&url.hostname==='blgkmkjbdekeoenepgnajpeafofccbjm')return route.continue();
  if(!knownHosts.has(url.hostname)){unexpected.push(url.hostname);return route.abort('blockedbyclient')}
  const html=body=>route.fulfill({contentType:'text/html; charset=utf-8',headers:{'set-cookie':'fixture-session=synthetic-only; Secure; SameSite=Lax; Path=/'},body:'<!doctype html><meta charset="utf-8"><title>Original-site fixture</title>'+body});
  const json=value=>route.fulfill({contentType:'application/json',body:JSON.stringify(value)});
  if(request.method()==='POST'){
   const body=request.postData()||'';const cookie=(await request.allHeaders()).cookie||'';
   posts.push({host:url.hostname,path:url.pathname,cookiePresent:cookie.includes('fixture-session=synthetic-only')});
   if(url.hostname==='codeforces.com'){cfCount++;const form=new URLSearchParams(body);assert.equal(form.get('sourceCode'),source);assert.equal(form.get('programTypeId'),'54');return html(account('Codeforces')+table(cfRow(1000+cfCount)+cfRow(1000)))}
   if(url.hostname==='atcoder.jp'){acCount++;const form=new URLSearchParams(body);assert.equal(form.get('sourceCode'),'print(0)');assert.equal(form.get('data.LanguageId'),'4006');assert.equal(form.get('csrf_token'),'fixture-native-token');return html(account('AtCoder')+table(acRow(2000+acCount)))}
   if(url.hostname==='ac.nowcoder.com'){ncCount++;const form=new URLSearchParams(body);assert.equal(form.get('content'),source);assert.equal(form.get('doneQuestionId'),'21992');assert.equal(form.get('tagId'),'4');assert.equal(form.get('subTagId'),'0');return json({code:0,submissionId:85470510+ncCount})}
   if(url.hostname==='www.luogu.com.cn'){lgCount++;assert.equal(JSON.parse(body).code,source);return json({rid:4000+lgCount})}
   if(url.hostname==='qoj.ac'){qojCount++;const form=new URLSearchParams(body);assert.equal(form.get('answer_answer_editor'),source);assert.equal(form.get('_token'),'synthetic-native-token');return html(qojList())}
   throw Error('Unexpected POST')
  }
  if(url.hostname==='codeforces.com'){
   if(url.pathname.endsWith('/my'))return html(account('Codeforces')+table((cfCount?cfRow(1000+cfCount):'')+cfRow(1000)));
   if(url.pathname==='/api/user.status')return json({status:'OK',result:cfCount?[{id:1000+cfCount,verdict:'OK',problem:{contestId:123,index:'A'},author:{members:[{handle:'fixture'}]}}]:[]});
   return html(account('Codeforces')+nativeForm('Codeforces','A'));
  }
  if(url.hostname==='atcoder.jp'){
   if(url.pathname.endsWith('/submissions/me'))return html(account('AtCoder')+table(acCount?acRow(2000+acCount):''));
   return html(account('AtCoder')+nativeForm('AtCoder','abc100_a'));
  }
  if(url.hostname==='ac.nowcoder.com'){
   if(url.pathname==='/nccommon/status'){
    assert.equal(url.searchParams.get('tagId'),'4');assert.equal(url.searchParams.get('subTagId'),'0');
    const id=url.searchParams.get('submissionId');await new Promise(r=>setTimeout(r,180));return json({code:0,data:{submissionId:Number(id),status:id==='85470558'?4:12}});
   }
   if(url.pathname.startsWith('/acm/contest/'))return html('<script>window.globalInfo={ownerId:12345}</script><script>window.secret="private-token"</script><input type="password" value="private-token"><div class="subject-describe">'+('statement '.repeat(4000)+'😀').repeat(10)+'</div><div class="question-oi"><pre>1 2</pre></div>');
   const pid=url.pathname.split('/').pop();
   if(loginNeeded)return html('<script>window.globalInfo={ownerId:0};window.isLogin=false</script><input type="password">');
   return html(`<script>window.globalInfo={ownerId:12345};window.isLogin=true;window.pageInfo={problemId:'${pid}',doneQuestionId:'${pid}',questionId:'308955',tagId:'4',subTagId:'0',codeJudgeType:'0'};</script><select name="language"><option value="2">C++（clang++18）</option></select><div class="CodeMirror">Original native editor</div><button class="btn-submit">保存并提交</button><script>let code='';document.querySelector('.CodeMirror').CodeMirror={setValue(value){code=value},getValue(){return code}};const nativeFetch=fetch;document.querySelector('.btn-submit').onclick=()=>nativeFetch('/nccommon/submit_cd',{method:'POST',body:new URLSearchParams({questionId:'308955',doneQuestionId:'${pid}',content:code,language:'2',tagId:'4',subTagId:'0'})});</script>`);
  }
  if(url.hostname==='www.luogu.com.cn'){
   if(url.pathname.startsWith('/record/'))return json({data:{record:{id:4000+lgCount,problem:{pid:'P1001'},user:{uid:12345},status:12}}});
   return html('<script id="lentille-context" type="application/json">{"user":{"uid":12345},"data":{"problem":{"pid":"P1001","acceptLanguages":[12]},"contest":null}}</script><select name="language"><option value="12">C++17</option></select><textarea name="sourceCode"></textarea><button id="native-submit">提交评测</button><script>document.querySelector("button").onclick=()=>fetch("/fe/api/problem/submit/P1001",{method:"POST",body:JSON.stringify({code:document.querySelector("textarea").value,lang:12})})</script>');
  }
  if(url.hostname==='qoj.ac'){
   if(url.pathname==='/submissions')return html(qojList());
   return html(account('QOJ')+'<a href="#tab-submit">Submit</a><form id="form-answer" action="/problem/15032" method="post"><select name="answer_answer_language"><option>C++ 17</option></select><input type="radio" name="answer_answer_upload_type" value="editor" checked><textarea name="answer_answer_editor"></textarea><input type="hidden" name="_token" value="synthetic-native-token"><button id="button-submit-answer" type="submit">Submit</button></form>');
  }
 });
 worker=browser.serviceWorkers().find(w=>w.url().includes('blgkmkjbdekeoenepgnajpeafofccbjm'))||await browser.waitForEvent('serviceworker',{predicate:w=>w.url().includes('blgkmkjbdekeoenepgnajpeafofccbjm')});
 if(process.env.TB_TEST_RUNTIME_EXTENSION){
  const replaced=browser.waitForEvent('serviceworker',{predicate:w=>w!==worker&&w.url().includes('blgkmkjbdekeoenepgnajpeafofccbjm'),timeout:10000});
  await worker.evaluate(()=>chrome.runtime.reload()).catch(()=>{});worker=await replaced;
 }
 const configured=await worker.evaluate(async()=>({base:TB_CONNECTION_BASE,bases:(await chrome.storage.local.get('bases')).bases||null}));assert.equal(configured.base,base,'Owned fixture must load the new endpoint before any test');assert(!configured.bases||configured.bases.length===1&&configured.bases[0]===base,'Owned fixture retained an older endpoint');
 assert.equal(await worker.evaluate(()=>typeof chrome.cookies),'undefined');
 await worker.evaluate(()=>{globalThis.focusCalls=[];const update=chrome.windows.update.bind(chrome.windows);chrome.windows.update=(id,value,...rest)=>{focusCalls.push(value);return update(id,value,...rest)}});
 const foreground=browser.pages()[0]||await browser.newPage();await foreground.goto(base+'/');
 const foregroundId=await worker.evaluate(async()=> (await chrome.tabs.query({active:true,lastFocusedWindow:true}))[0].id);
 await until(()=>get('/fixture/preparation'),value=>value.extension.connected);
 for(const [key,url,verdict,language,code] of [
  ['cf','https://codeforces.com/contest/123/problem/A','AC'],
  ['ac','https://atcoder.jp/contests/abc100/tasks/abc100_a','AC','python3','print(0)'],
  ['nc','https://ac.nowcoder.com/acm/problem/21992','CE'],
  ['lg','https://www.luogu.com.cn/problem/P1001','AC'],
  ['qoj','https://qoj.ac/problem/15032','AC'],
 ]){
  const created=await create(key,url,language,code);const result=await state(key,'finished');assert.equal(result.verdict,verdict);
  assert.equal(await worker.evaluate(async()=> (await chrome.tabs.query({active:true,lastFocusedWindow:true}))[0].id),foregroundId);
  const job=await worker.evaluate(async sid=>Object.values((await chrome.storage.session.get('jobs')).jobs||{}).find(job=>job.sessionId===sid),created.sessionId);assert(job,'Final result waits for UI ACK');
  assert.equal((await worker.evaluate(id=>chrome.tabs.get(id),job.tabId)).mutedInfo.muted,true);
  const page=browser.pages().find(p=>p.url().startsWith(new URL(url).origin));assert(page);
  await get('/fixture/ack?key='+key);await until(()=>get('/fixture/status'),states=>states[key]?.windowClosed===true);
  assert(page.isClosed(),'Only the acknowledged owned page is closed');checks.push(key+' native form, existing session, background, saved receipt then ACK close');
 }
 assert.equal(posts.length,5);assert(posts.every(p=>p.cookiePresent));assert.equal((await worker.evaluate(()=>focusCalls)).length,0);
 const before=posts.length;await create('manual','https://codeforces.com/contest/123/problem/A','cpp17',source,true);await state('manual','ready');await new Promise(r=>setTimeout(r,1300));assert.equal(posts.length,before);
 checks.push('Manual page remains open without automatic POST');
 loginNeeded=true;await create('login','https://ac.nowcoder.com/acm/problem/21992');await state('login','needs_login');
 assert.equal((await worker.evaluate(()=>focusCalls)).filter(value=>value.focused).length,1);assert.equal(posts.length,before);
 loginNeeded=false;const loginPage=browser.pages().find(p=>p.url().startsWith('https://ac.nowcoder.com/acm/problem/21992'));await loginPage.reload();await state('login','finished');assert.equal(posts.length,before+1);
 await get('/fixture/ack?key=login');await until(()=>get('/fixture/status'),value=>value.login.windowClosed===true);checks.push('Only missing login focuses the owned tab; same unsent intent resumes once');
 const count=posts.length;const reading=await get('/fixture/read?'+new URLSearchParams({url:'https://ac.nowcoder.com/acm/contest/123/A'}));assert(reading.length>262144);assert.equal(reading.unsafe,false);assert.equal(posts.length,count);checks.push('Bounded multi-part statement DOM, no form/script/password export');
 await get('/fixture/restore');const restored=await state('restore','finished');assert.equal(restored.verdict,'WA');assert.equal(restored.submissionId,'85470558');assert.equal(posts.length,count);await get('/fixture/ack?key=restore');await until(()=>get('/fixture/status'),value=>value.restore.windowClosed===true);checks.push('Persisted exact NC SID recovers WA by GET only');
 const other=await worker.evaluate(id=>chrome.tabs.get(id),foregroundId);assert.equal(other.mutedInfo.muted,false);
 const connectionPage=await browser.newPage();await connectionPage.goto('chrome-extension://blgkmkjbdekeoenepgnajpeafofccbjm/connection.html');try{await connectionPage.getByText('已连接 ToBe',{exact:true}).waitFor({timeout:10000})}catch(issue){throw Error(issue.message+'; popup='+await connectionPage.locator('body').innerText())}await connectionPage.close();checks.push('Bundled manual connection page reports the actual local connection');
 assert.deepEqual(unexpected,[]);assert.deepEqual(errors,[]);
 const result={ok:true,checks,syntheticNativePosts:posts.length,originalSiteNetworkRequests:0,realLogins:0,realSubmissions:0,sourceVersions:manifest.version,out};
 await writeFile(path.join(out,'result.log'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
}finally{if(browser)await browser.close();server.kill();await writeFile(path.join(out,'server-stderr.log'),stderr)}
