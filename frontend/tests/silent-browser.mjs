// Disposable browser profile only: prove zero-window startup and login sync.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { chromium } from 'playwright';
import { fileURLToPath } from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const server=spawn(process.env.TB_PYTHON||'C:/Users/lenovo/AppData/Local/Programs/Python/Python313/python.exe',['desktop/tests/browser_server.py'],{cwd:root,env:{...process.env,TB_OFFLINE:'1',TB_TEST_SILENT:'1'},windowsHide:true});
const port=await new Promise(resolve=>server.stdout.once('data',b=>resolve(JSON.parse(b.toString().trim()).port)));
const base=`http://127.0.0.1:${port}`;
const profile=await mkdtemp(path.join(os.tmpdir(),'tb-silent-start-'));
const extension=process.env.TB_BROWSER_EXTENSION||path.join(root,'build/browser-extension');
let browser, child;
try{
 browser=await chromium.launchPersistentContext(profile,{channel:'msedge',headless:true,args:[`--disable-extensions-except=${extension}`,`--load-extension=${extension}`]});
 const worker=browser.serviceWorkers()[0]||await browser.waitForEvent('serviceworker');
 await worker.evaluate(async base=>chrome.storage.local.set({bases:[base]}),base);
 for(const domain of ['codeforces.com','atcoder.jp','nowcoder.com','luogu.com.cn'])await browser.addCookies([{name:'fixture_login',value:'fixture-only',domain,path:'/',secure:true,httpOnly:true,sameSite:'Lax',expires:Math.floor(Date.now()/1000)+3600}]);
 await browser.close();browser=null;
 child=spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',['--no-startup-window',`--user-data-dir=${profile}`,'--profile-directory=Default','--remote-debugging-port=0',`--disable-extensions-except=${extension}`,`--load-extension=${extension}`],{windowsHide:true,stdio:'ignore'});
 let debugPort;
 for(let i=0;i<100;i++){
  try{debugPort=Number((await readFile(path.join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0]);await fetch(`http://127.0.0.1:${debugPort}/json/version`);break}catch{}
  await new Promise(r=>setTimeout(r,100));
 }
 browser=await chromium.connectOverCDP(`http://127.0.0.1:${debugPort}`);
 const context=browser.contexts()[0];
 const awake=context.serviceWorkers()[0]||await context.waitForEvent('serviceworker',{timeout:10000});
 assert.equal((await awake.evaluate(()=>chrome.windows.getAll())).length,0,'silent startup must not create any browser window');
 for(const platform of ['Codeforces','AtCoder','牛客','洛谷'])await fetch(base+'/fixture/sync?'+new URLSearchParams({platform}));
 let result;
 for(let i=0;i<100;i++){
  result=await(await fetch(base+'/fixture/sync')).json();
  if(Object.keys(result).length===4)break;
  await new Promise(r=>setTimeout(r,100));
 }
 assert.equal(Object.keys(result).length,4,JSON.stringify(result));
 assert.ok(Object.values(result).every(v=>v.count===1&&v.fixture));
 assert.equal((await awake.evaluate(()=>chrome.windows.getAll())).length,0);
 const cdp=await browser.newBrowserCDPSession();await cdp.send('Browser.close');browser=null;
 console.log(JSON.stringify({ok:true,coldStartWithoutWindow:true,allFourLoginSessionsSynced:true,realAccountUsed:false}));
}finally{
 if(browser)await browser.close();
 if(child&&!child.killed)child.kill();
 server.kill();
 await rm(profile,{recursive:true,force:true,maxRetries:10,retryDelay:200});
}
