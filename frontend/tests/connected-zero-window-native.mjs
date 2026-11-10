// One real Edge instance with a fresh owned profile. All site bodies are
// synthetic CDP routes; normal browser profiles and account DBs are untouched.
import assert from 'node:assert/strict';
import {spawn,execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {dirname,join,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash,randomUUID} from 'node:crypto';
import {chromium} from 'playwright';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const out=join('D:/Temp/T13HFix-20261110','native-connected-'+randomUUID());await mkdir(out,{recursive:false});
const python=process.env.TB_PYTHON||'C:/Users/lenovo/AppData/Local/Programs/Python/Python313/python.exe';
const edge=process.env.TB_TEST_EDGE||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const run=promisify(execFile),hash=b=>createHash('sha256').update(b).digest('hex');
const profile=join(out,'profile'),extension=join(out,'extension');
const extensionId='blgkmkjbdekeoenepgnajpeafofccbjm';
const env={...process.env,TB_OFFLINE:'1',PYTHONDONTWRITEBYTECODE:'1',PYTHONIOENCODING:'utf-8'};
const fixture=spawn(python,['-B','-u','desktop/tests/connected_zero_window_server.py'],{cwd:root,env,windowsHide:true,stdio:['pipe','pipe','pipe']});
let serverError='',edgeError='';fixture.stderr.on('data',b=>serverError=(serverError+b).slice(-16384));
const {port}=await new Promise((ok,no)=>{let text='';fixture.stdout.on('data',b=>{text+=b;if(text.includes('\n'))ok(JSON.parse(text.split('\n')[0]))});fixture.once('exit',code=>no(Error('FIXTURE_START_FAILED_'+code)))});
const base='http://127.0.0.1:'+port;
let child,browser,monitor,monitorResult,worker,browserPid,foregroundPromise;
const checks=[],blocked=[],pageErrors=[],focusAttempts=[];let posts=0;
const clientWindowOverrides=[];
const result={ok:false,out,realOriginalSiteRequests:0,realProviderRequests:0,ordinaryProfilesUsed:false,personalDatabasesOpened:false,
  cleanup:{removed:[],reason:'Current production sources, prior tests and recovery proofs remain referenced.'}};
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function until(read,accept,milliseconds=25000){let value;const end=Date.now()+milliseconds;while(Date.now()<end){value=await read();if(accept(value))return value;await pause(100)}throw Error('FIXTURE_STATE_TIMEOUT_'+JSON.stringify(value))}
async function get(path){const r=await fetch(base+path);assert.equal(r.status,200);return r.json()}
try{
  await run(python,['-B','scripts/build_browser_extension.py',extension,'--base-url',base],{cwd:root,env,windowsHide:true});
  result.workerSha256=hash(await readFile(resolve(root,'desktop/browser_extension/worker.js')));
  assert.equal(hash(await readFile(join(extension,'worker.js'))),result.workerSha256);
  result.manifestSha256=hash(await readFile(join(extension,'manifest.json')));
  await mkdir(profile,{recursive:false});
  monitor=spawn(python,['-B','-u','-c',String.raw`
import ctypes,ctypes.wintypes as w,json,sys,threading,time
u=ctypes.WinDLL('user32');u.GetForegroundWindow.restype=w.HWND
u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
stop=threading.Event();target=[None];samples=[]
def reader():
 for line in sys.stdin:
  if line.strip()=='stop':stop.set();break
  target[0]=int(line.strip())
threading.Thread(target=reader,daemon=True).start()
print('ready',flush=True)
while not stop.is_set():
 p=w.DWORD();u.GetWindowThreadProcessId(u.GetForegroundWindow(),ctypes.byref(p));samples.append(p.value);time.sleep(.02)
print(json.dumps({'samples':len(samples),'ownedForegroundSamples':sum(p==target[0] for p in samples),'otherProcessIdsExported':False}),flush=True)
`],{env,windowsHide:true,stdio:['pipe','pipe','pipe']});
  let monitorText='';foregroundPromise=new Promise((ok,no)=>{monitor.stdout.on('data',b=>monitorText+=b);monitor.once('exit',code=>{try{assert.equal(code,0);ok(JSON.parse(monitorText.trim().split('\n').at(-1)))}catch(e){no(e)}})});
  await until(async()=>monitorText,text=>text.includes('ready'),5000);
  child=spawn(edge,[`--user-data-dir=${profile}`,'--profile-directory=Default','--no-startup-window','--no-first-run','--no-default-browser-check',
    '--remote-debugging-address=127.0.0.1','--remote-debugging-port=0','--disable-background-networking','--disable-component-update','--disable-sync',
    '--proxy-server=direct://','--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1',`--disable-extensions-except=${extension}`,`--load-extension=${extension}`],
    {env,windowsHide:true,stdio:['ignore','ignore','pipe']});
  child.stderr.on('data',b=>edgeError=(edgeError+b).slice(-16384));
  let address;
  await until(async()=>{try{const lines=(await readFile(join(profile,'DevToolsActivePort'),'utf8')).trim().split('\n');address='http://127.0.0.1:'+Number(lines[0]);return (await fetch(address+'/json/version')).json()}catch{return null}},value=>value?.webSocketDebuggerUrl,15000);
  const version=await (await fetch(address+'/json/version')).json();
  const socket=new WebSocket(version.webSocketDebuggerUrl);
  await new Promise((ok,no)=>{socket.addEventListener('open',ok,{once:true});socket.addEventListener('error',no,{once:true})});
  const transport={send(message){
    if(['Browser.setWindowBounds','Emulation.setFocusEmulationEnabled','Emulation.setDeviceMetricsOverride'].includes(message.method))clientWindowOverrides.push({method:message.method,params:message.params});
    socket.send(JSON.stringify(message));
  },close(){socket.close()}};
  socket.addEventListener('message',event=>transport.onmessage?.(JSON.parse(event.data)));
  socket.addEventListener('close',()=>transport.onclose?.());
  browser=await chromium.connectOverCDP(transport,{noDefaults:true});const context=browser.contexts()[0],cdp=await browser.newBrowserCDPSession();
  result.connectNoDefaults=true;
  result.browserVersion=(await cdp.send('Browser.getVersion')).product;
  browserPid=(await cdp.send('SystemInfo.getProcessInfo')).processInfo.find(p=>p.type==='browser').id;result.ownedBrowserPid=browserPid;monitor.stdin.write(String(browserPid)+'\n');
  context.on('page',page=>page.on('pageerror',e=>pageErrors.push(e.message)));
  await context.route('**/*',async route=>{
    const request=route.request(),url=new URL(request.url());
    if(url.hostname==='127.0.0.1'||url.protocol==='chrome-extension:'&&url.hostname===extensionId)return route.continue();
    if(url.origin!=='https://ac.nowcoder.com'){blocked.push(url.hostname);return route.abort('blockedbyclient')}
    const json=value=>route.fulfill({contentType:'application/json',body:JSON.stringify(value)});
    if(url.pathname==='/favicon.ico')return route.fulfill({status:204,body:''});
    if(request.method()==='POST'){
      assert.equal(url.pathname,'/nccommon/submit_cd');const form=new URLSearchParams(request.postData()||'');
      assert.equal(form.get('content'),'int main(){}');assert.equal(form.get('doneQuestionId'),'21992');assert.equal(form.get('tagId'),'4');assert.equal(form.get('subTagId'),'0');
      posts++;return json({code:0,submissionId:85470571});
    }
    if(url.pathname==='/nccommon/status'){assert.equal(url.searchParams.get('submissionId'),'85470571');return json({code:0,data:{submissionId:85470571,status:12}})}
    assert.equal(url.pathname,'/acm/problem/21992');
    return route.fulfill({contentType:'text/html; charset=utf-8',body:`<!doctype html><title>Isolated native form</title><script>window.globalInfo={ownerId:12345};window.isLogin=true;window.pageInfo={problemId:'21992',doneQuestionId:'21992',questionId:'308955',tagId:'4',subTagId:'0',codeJudgeType:'0'};</script><select name="language"><option value="2">C++（clang++18）</option></select><div class="CodeMirror">Synthetic native editor</div><button class="btn-submit">保存并提交</button><script>let code='';document.querySelector('.CodeMirror').CodeMirror={setValue(value){code=value},getValue(){return code}};document.querySelector('.btn-submit').onclick=()=>fetch('/nccommon/submit_cd',{method:'POST',body:new URLSearchParams({questionId:'308955',doneQuestionId:'21992',content:code,language:'2',tagId:'4',subTagId:'0'})});</script>`});
  });
  try{worker=context.serviceWorkers().find(w=>w.url().includes(extensionId))||await context.waitForEvent('serviceworker',{predicate:w=>w.url().includes(extensionId),timeout:15000})}
  catch{result.status='blocked';result.failureCode='EDGE_DID_NOT_LOAD_UNPACKED_EXTENSION_FROM_FLAGS';throw Error(result.failureCode)}
  assert.equal(await worker.evaluate(()=>TB_CONNECTION_BASE),base);
  assert.equal((await worker.evaluate(()=>chrome.windows.getAll({windowTypes:['normal']}))).length,0,'This must exercise the zero-normal-window branch');
  await worker.evaluate(()=>{
    globalThis.nativeFocusAttempts=[];globalThis.nativeWindowEvents=[];
    const update=chrome.windows.update.bind(chrome.windows),create=chrome.windows.create.bind(chrome.windows),tabUpdate=chrome.tabs.update.bind(chrome.tabs);
    chrome.windows.update=(id,value,...rest)=>{if(value.focused||value.state==='normal'){nativeFocusAttempts.push({operation:'update',id,focused:value.focused,state:value.state});throw Error('OWNED_TEST_FOCUS_GUARD')}return update(id,value,...rest)};
    chrome.windows.create=async(value,...rest)=>{if(value.focused!==false||value.state!=='minimized'){nativeFocusAttempts.push({operation:'create',focused:value.focused,state:value.state});throw Error('OWNED_TEST_FOCUS_GUARD')}const answer=await create(value,...rest);nativeWindowEvents.push({phase:'create-return',state:answer.state,focused:answer.focused});return answer};
    chrome.tabs.update=async(id,value,...rest)=>{const answer=await tabUpdate(id,value,...rest);if(value.url){const window=await chrome.windows.get(answer.windowId);nativeWindowEvents.push({phase:'navigation-return',state:window.state,focused:window.focused})}return answer};
  });
  const before=await until(()=>get('/fixture/proof'),v=>v.register.length>0&&v.queueWithoutWindow>0);
  assert(before.register.every(v=>v.protocol===4&&v.backgroundWindows));checks.push('Actual extension registers backgroundWindows while no normal window exists');
  const created=await get('/fixture/create');
  const finished=await until(()=>get('/fixture/status'),v=>v.status==='finished');
  assert.equal(finished.verdict,'CE');assert.equal(finished.submissionId,'85470571');assert.equal(posts,1);
  const job=await worker.evaluate(async sid=>Object.values((await chrome.storage.session.get('jobs')).jobs||{}).find(j=>j.sessionId===sid),created.sessionId);
  assert(job?.ownedWindowId);const window=await worker.evaluate(id=>chrome.windows.get(id,{populate:true}),job.ownedWindowId);
  result.chromeJobWindow={state:window.state,focused:window.focused,type:window.type};
  assert.equal(window.state,'minimized');assert.equal(window.focused,false);
  assert.equal((await worker.evaluate(id=>chrome.tabs.get(id),job.tabId)).mutedInfo.muted,true);
  const page=context.pages().find(p=>p.url().startsWith('https://ac.nowcoder.com/'));assert(page);
  result.clientViewport=page.viewportSize();assert.equal(result.clientViewport,null);
  const target=await context.newCDPSession(page),info=await target.send('Target.getTargetInfo');
  result.nativeWindowBounds=(await cdp.send('Browser.getWindowForTarget',{targetId:info.targetInfo.targetId})).bounds;
  assert.equal(result.nativeWindowBounds.windowState,'minimized');checks.push('Actual minimized unfocused window, muted tab and synthetic native POST persist one CE');
  const keep=await worker.evaluate(async windowId=>chrome.tabs.create({windowId,url:'about:blank#fixture-preserve',active:false}),job.ownedWindowId);
  await get('/fixture/ack');await until(()=>get('/fixture/status'),v=>v.windowClosed===true);
  assert(page.isClosed());assert.equal((await worker.evaluate(id=>chrome.tabs.get(id),keep.id)).id,keep.id);
  assert.equal((await worker.evaluate(id=>chrome.windows.get(id),job.ownedWindowId)).state,'minimized');
  focusAttempts.push(...await worker.evaluate(()=>nativeFocusAttempts));assert.deepEqual(focusAttempts,[]);
  assert.equal(posts,1);assert.equal((await get('/fixture/proof')).savedReceipts,1);assert.deepEqual(pageErrors,[]);
  checks.push('ACK closes only its owned submission tab; the extra owned-fixture tab remains minimized');
  result.ok=true;result.status='passed';result.checks=checks;result.syntheticNativePosts=posts;result.loginCaptchaForegroundBranch='VM-covered; not triggered on user desktop';
}catch(error){
  result.status??='failed';result.failureCode??=error.message;result.checks=checks;
}finally{
  result.syntheticNativePosts=posts;
  try{result.bridgeProof=await get('/fixture/proof')}catch{}
  if(worker)try{const observed=await worker.evaluate(()=>({focus:globalThis.nativeFocusAttempts||[],windows:globalThis.nativeWindowEvents||[]}));focusAttempts.splice(0,focusAttempts.length,...observed.focus);result.windowEvents=observed.windows}catch{}
  if(browser){try{const cdp=await browser.newBrowserCDPSession();await cdp.send('Browser.close')}catch{}await browser.close().catch(()=>{})}
  if(child){if(child.exitCode===null)try{await Promise.race([new Promise(r=>child.once('exit',r)),pause(8000)])}catch{}if(child.exitCode===null){child.kill();result.ownBrowserLauncherTerminated=true}}
  if(monitor){monitor.stdin.end('stop\n');try{monitorResult=await foregroundPromise;result.foreground=monitorResult;if(monitorResult.ownedForegroundSamples!==0){result.ok=false;result.failureCode='OWNED_BROWSER_WAS_FOREGROUND'}}catch(e){result.ok=false;result.foregroundError=e.message}}
  fixture.stdin.end('stop\n');await Promise.race([new Promise(r=>fixture.once('exit',r)),pause(5000)]);if(fixture.exitCode===null)fixture.kill();
  result.ownedBrowserExitCode=child?.exitCode;result.ownedFixtureExitCode=fixture.exitCode;
  result.pageErrors=pageErrors;result.blockedUnexpectedHosts=[...new Set(blocked)];result.focusAttempts=focusAttempts;
  result.clientWindowOverrides=clientWindowOverrides;
  result.onlyOwnBrowserAndFixtureClosed=true;result.workerSourceUnchanged=hash(await readFile(resolve(root,'desktop/browser_extension/worker.js')))===result.workerSha256;
  await writeFile(join(out,'result.json'),JSON.stringify(result,null,2)+'\n');
  await writeFile(join(out,'edge-stderr.log'),edgeError);await writeFile(join(out,'fixture-stderr.log'),serverError);
  console.log(JSON.stringify(result));
}
if(!result.ok)process.exitCode=1;
