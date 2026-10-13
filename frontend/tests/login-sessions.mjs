// Real Chromium cookie API and connector, disposable profile and local TB.
// All website responses are fixtures. No real account/network submission.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdtemp,readFile,writeFile,rm} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';
import {fixtureExtension} from './extension-fixture.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const platforms=['Codeforces','AtCoder','牛客','洛谷'];
const server=spawn(process.env.TB_PYTHON||'C:/Users/lenovo/AppData/Local/Programs/Python/Python313/python.exe',['desktop/tests/browser_server.py'],{
  cwd:root,env:{...process.env,TB_OFFLINE:'1',TB_TEST_SILENT:'1',TB_TEST_PREPARATION:'1',TB_TEST_INSTALLED:'1',PYTHONIOENCODING:'utf-8'},windowsHide:true});
let stderr='';server.stderr.on('data',b=>stderr+=b);
const {port}=await new Promise((resolve,reject)=>{
  let data='';server.stdout.on('data',b=>{data+=b;if(data.includes('\n'))resolve(JSON.parse(data.split('\n')[0]));});
  server.on('exit',code=>reject(new Error('Fixture server '+code+' '+stderr)));
});
const base=`http://127.0.0.1:${port}`,profile=await mkdtemp(path.join(os.tmpdir(),'tb-login-sessions-'));
const extension=await fixtureExtension(process.env.TB_BROWSER_EXTENSION||path.join(root,'build/browser-extension'),profile,base);
const workerPath=path.join(extension,'worker.js');
await writeFile(workerPath,`
const fixtureFetch=globalThis.fetch.bind(globalThis);
globalThis.fetch=async (url,options)=>{
  const host=new URL(url).hostname;
  if(host==='127.0.0.1')return fixtureFetch(url,options);
  if(options?.method && options.method!=='GET')throw new Error('Fixture forbids site writes');
  const domain=host.replace(/^www\\./,'');
  const cookies=[...await chrome.cookies.getAll({domain}),...await chrome.cookies.getAll({domain,partitionKey:{topLevelSite:'https://'+domain,hasCrossSiteAncestor:false}})];
  const signed=cookies.some(c=>c.name==='JSESSIONID'&&c.value==='fixture-only');
  if(domain==='codeforces.com')return new Response('<div id="header"><a href="/'+(signed?'profile/fixture':'enter')+'">Account</a></div>',{status:200});
  // Blocked/background-negative responses must not erase signed Revel claims.
  if(domain==='atcoder.jp')return new Response('var userScreenName="";', {status:200});
  return new Response('Fixture unavailable',{status:503});
};
`+await readFile(workerPath,'utf8'));
let browser,child;
const get=async suffix=>(await fetch(base+'/fixture/'+suffix)).json();
async function waitState(predicate){
  let value;
  for(let i=0;i<160;i++){
    value=await get('preparation');if(predicate(value))return value;
    await new Promise(r=>setTimeout(r,100));
  }
  assert.fail(JSON.stringify({value,stderr}));
}
try{
  browser=await chromium.launchPersistentContext(profile,{channel:'msedge',headless:true,args:[`--disable-extensions-except=${extension}`,`--load-extension=${extension}`]});
  let worker=browser.serviceWorkers()[0]||await browser.waitForEvent('serviceworker');
  await worker.evaluate(async()=>{
    const expires=Date.now()/1000+3600;
    await chrome.cookies.set({url:'https://codeforces.com/',name:'cf_clearance',value:'fixture-only',secure:true,httpOnly:true,sameSite:'no_restriction',expirationDate:expires,partitionKey:{topLevelSite:'https://codeforces.com',hasCrossSiteAncestor:false}});
    // A real CF JSESSIONID can lack Secure even on HTTPS. HTTPS-only host
    // permission hides it from getAll; use browser-owned cookies in this test.
    await chrome.cookies.set({url:'https://atcoder.jp/',name:'REVEL_SESSION',value:encodeURIComponent('signed-\x00UserScreenName:fixture\x00\x00csrf_token:fixture\x00'),secure:true,httpOnly:true,expirationDate:expires});
    await chrome.cookies.set({url:'https://ac.nowcoder.com/',domain:'.nowcoder.com',name:'t',value:'fixture-only',secure:true,httpOnly:true,expirationDate:expires});
    await chrome.cookies.set({url:'https://www.luogu.com.cn/',domain:'.luogu.com.cn',name:'_uid',value:'123',secure:true,expirationDate:expires});
    await chrome.cookies.set({url:'https://www.luogu.com.cn/',domain:'.luogu.com.cn',name:'__client_id',value:'fixture-only',secure:true,httpOnly:true,expirationDate:expires});
  });
  await browser.addCookies([{name:'JSESSIONID',value:'fixture-only',domain:'codeforces.com',path:'/',secure:false,httpOnly:true,sameSite:'Lax',expires:Date.now()/1000+3600}]);
  assert.equal(await worker.evaluate(async()=>(await chrome.cookies.getAll({domain:'codeforces.com'})).some(c=>c.name==='JSESSIONID'&&!c.secure)),true,'CF non-Secure login cookie must be visible to the connector');
  for(const domain of ['atcoder.jp','nowcoder.com','luogu.com.cn']) {
    await browser.addCookies([{name:'nonsecure_fixture',value:'fixture-only',domain,path:'/',secure:false,httpOnly:true,sameSite:'Lax',expires:Date.now()/1000+3600}]);
    assert.equal(await worker.evaluate(async domain=>(await chrome.cookies.getAll({domain})).some(c=>c.name==='nonsecure_fixture'&&!c.secure),domain),true);
  }
  await waitState(value=>value.ready);
  assert.ok(browser.pages().every(p=>!p.url().startsWith('https://')),'No OJ tab opened for login detection');
  const cookies=await get('sync');
  assert.deepEqual(Object.fromEntries(platforms.map(p=>[p,cookies[p].count])),{Codeforces:2,AtCoder:2,'牛客':2,'洛谷':3});
  await browser.close();browser=null;
  await get('restart-sessions');
  const restored=await get('preparation');
  assert.equal(restored.extension.connected,false);
  assert.equal(restored.ready,true,'All four confirmed states survive TB restart without a browser');
  child=spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',['--no-startup-window',`--user-data-dir=${profile}`,'--profile-directory=Default','--remote-debugging-port=0',`--disable-extensions-except=${extension}`,`--load-extension=${extension}`],{windowsHide:true,stdio:'ignore'});
  let debugPort;
  for(let i=0;i<120;i++){
    try {debugPort=Number((await readFile(path.join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0]);await fetch(`http://127.0.0.1:${debugPort}/json/version`);break;}catch{}
    await new Promise(r=>setTimeout(r,100));
  }
  browser=await chromium.connectOverCDP(`http://127.0.0.1:${debugPort}`);
  const context=browser.contexts()[0];worker=context.serviceWorkers()[0]||await context.waitForEvent('serviceworker');
  await waitState(value=>value.extension.connected&&value.ready);
  assert.equal((await worker.evaluate(()=>chrome.windows.getAll())).length,0);
  // A real logout/anonymous Revel session must replace the prior login proof.
  await worker.evaluate(async()=>{
    await chrome.cookies.set({url:'https://atcoder.jp/',name:'REVEL_SESSION',value:encodeURIComponent('signed-\x00csrf_token:guest\x00'),secure:true,httpOnly:true,expirationDate:Date.now()/1000+3600});
    await chrome.cookies.remove({url:'https://codeforces.com/',name:'JSESSIONID'});
    await chrome.cookies.remove({url:'https://codeforces.com/',name:'cf_clearance',partitionKey:{topLevelSite:'https://codeforces.com',hasCrossSiteAncestor:false}});
    await chrome.cookies.remove({url:'https://ac.nowcoder.com/',name:'t'});
    await chrome.cookies.remove({url:'https://www.luogu.com.cn/',name:'_uid'});
    await chrome.cookies.remove({url:'https://www.luogu.com.cn/',name:'__client_id'});
    for(const domain of ['atcoder.jp','nowcoder.com','luogu.com.cn'])await chrome.cookies.remove({url:'https://'+domain+'/',name:'nonsecure_fixture'});
  });
  await waitState(value=>value.platforms.every(p=>p.state==='logged_out'));
  assert.equal((await worker.evaluate(()=>chrome.windows.getAll())).length,0);
  const cdp=await browser.newBrowserCDPSession();await cdp.send('Browser.close');browser=null;
  console.log(JSON.stringify({ok:true,allFourWithoutSiteTabs:true,allFourNonSecureCookiesExported:true,firstPartyPartitionExported:true,atcoderExistingSessionDetected:true,desktopRestartKeepsLogin:true,closedBrowserColdStartHasZeroWindows:true,allFourLogoutUpdates:true,sitePosts:0,realAccountUsed:false}));
}finally{
  if(browser)await browser.close();if(child&&!child.killed)child.kill();server.kill();
  assert.ok(path.resolve(profile).startsWith(path.resolve(os.tmpdir())+path.sep));
  await rm(profile,{recursive:true,force:true,maxRetries:10,retryDelay:200});
}
