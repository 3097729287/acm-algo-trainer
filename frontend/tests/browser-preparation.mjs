import assert from 'node:assert/strict';
import {readFile, mkdir} from 'node:fs/promises';
import vm from 'node:vm';
import {chromium} from 'playwright';
import {createServer} from 'vite';

const detector = {};
vm.runInNewContext(await readFile('../desktop/browser_extension/login_state.js','utf8'), detector);
assert.equal(detector.tbCookieLoginState('Codeforces',[]), 'logged_out');
assert.equal(detector.tbCookieLoginState('Codeforces',[{name:'JSESSIONID',value:'anonymous'}]), 'unknown');
assert.equal(detector.tbPageLoginState('Codeforces','<div id="header"><a href="/enter">Enter</a></div>'), 'logged_out');
assert.equal(detector.tbPageLoginState('Codeforces','<div id="header"><a href="/profile/fixture">Fixture</a></div>'), 'logged_in');
assert.equal(detector.tbPageLoginState('Codeforces','<title>Just a moment</title>'), 'unknown');
assert.equal(detector.tbPageLoginState('AtCoder','var userScreenName = "fixture";'), 'logged_in');
assert.equal(detector.tbPageLoginState('AtCoder','var userScreenName = "";'), 'logged_out');
assert.equal(detector.tbPageLoginState('牛客','window.globalInfo={"ownerId":123};'), 'logged_in');
assert.equal(detector.tbPageLoginState('洛谷','<script id="lentille-context">{"user":null}</script>'), 'logged_out');
assert.equal(detector.tbPageLoginState('洛谷','<script id="lentille-context">{"user":{"uid":123}}</script>'), 'logged_in');

const vite = await createServer({server:{host:'127.0.0.1',port:0}});
await vite.listen();
const browser = await chromium.launch({channel:process.env.CI ? undefined : 'msedge',headless:true});
const page = await browser.newPage({viewport:{width:1050,height:760}});
page.setDefaultTimeout(10000);
const errors=[], actions=[];
page.on('pageerror',error=>errors.push(error.message));
let state = {available:true, extensionPath:'C:\\TB\\browser-extension', extension:{installed:false,connected:false,versions:[]},
  browsers:[{id:'edge',name:'Edge',available:true},{id:'chrome',name:'Chrome',available:true}],
  platforms:[['Codeforces','https://codeforces.com/enter'],['AtCoder','https://atcoder.jp/login'],['牛客','https://ac.nowcoder.com/login'],['洛谷','https://www.luogu.com.cn/auth/login']].map(([platform,loginUrl])=>({platform,loginUrl,state:'not_synced'})),ready:false};
await page.route('**/api/browser-preparation',async route=>{
  if (route.request().method()==='POST') {
    assert.equal(route.request().headers()['x-tb-token'],'preparation-fixture');
    const body=route.request().postDataJSON(); actions.push(body);
    if(body.action==='refresh') {state.extension={installed:true,connected:true,versions:['0.10.8']};state.platforms=state.platforms.map(p=>({...p,state:p.platform==='AtCoder'?'logged_out':'logged_in'}));}
    return route.fulfill({json:body.action==='refresh'?{...state,checking:true}:{opened:true}});
  }
  return route.fulfill({json:state});
});
try {
  await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/browser-preparation-fixture.html`);
  await page.getByText('原站提交前，请先安装浏览器连接扩展，再登录原站账号。').waitFor();
  await page.getByRole('button',{name:'查看准备说明'}).click();
  const guide=page.getByRole('dialog',{name:'浏览器提交准备'});
  await guide.waitFor();
  assert.equal(await guide.locator('.browser-guide-steps > li').count(),3);
  assert.equal(await guide.getByLabel('扩展文件夹路径').inputValue(),state.extensionPath);
  await guide.getByLabel('准备使用的浏览器').selectOption('chrome');
  await guide.getByRole('button',{name:'打开扩展管理',exact:true}).click();
  await guide.getByRole('button',{name:'打开扩展文件夹',exact:true}).click();
  for(const platform of ['牛客','洛谷','AtCoder','Codeforces']) await guide.getByRole('button',{name:'打开'+platform+'登录',exact:true}).click();
  assert.deepEqual(actions.filter(a=>a.action==='open-login').map(a=>a.platform),['牛客','洛谷','AtCoder','Codeforces']);
  assert.ok(actions.every(a=>a.browser==='chrome'));
  await guide.getByRole('button',{name:'重新检测浏览器准备'}).click();
  await guide.getByText('TB 浏览器连接扩展已连接',{exact:true}).waitFor();
  assert.equal(await guide.getByText('未登录或登录已失效',{exact:true}).count(),1);
  for (const [width,theme] of [[1050,'dark'],[375,'light']]) {
    await page.setViewportSize({width,height:760});
    await page.evaluate(theme=>{document.documentElement.dataset.theme=theme;document.documentElement.style.setProperty('--ui-font-size','18px');},theme);
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
    assert.ok(await guide.evaluate(node=>node.scrollWidth<=node.clientWidth+1));
    await mkdir('tests/screenshots',{recursive:true});
    await page.screenshot({path:`tests/screenshots/browser-preparation-${theme}-${width}.png`});
  }
  await page.keyboard.press('Escape');
  await guide.waitFor({state:'hidden'});
  await page.evaluate(()=>window.dispatchEvent(new CustomEvent('tb:browser-preparation',{detail:{platform:'AtCoder',status:'needs_login',message:'AtCoder 登录已失效，请先登录。'}})));
  await guide.getByText('AtCoder 登录已失效，请先登录。').waitFor();
  assert.ok((await guide.locator('.browser-guide-selected').innerText()).includes('AtCoder'));
  state={...state,ready:true,extension:{installed:true,connected:false},platforms:state.platforms.map(p=>({...p,state:'logged_in'}))};
  await page.evaluate(()=>window.dispatchEvent(new Event('focus')));
  await guide.getByText('扩展已安装，浏览器当前未连接',{exact:true}).waitFor();
  await page.getByText('四个平台的浏览器登录已同步',{exact:true}).waitFor();
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({ok:true,missingExtensionGuide:true,fourLoginActions:true,knownLogout:true,unknownIsNotLogout:true,verificationGuide:true,cachedLoginWithBrowserClosed:true,mobile:true,realAccountSubmission:false}));
} finally {await browser.close();await vite.close();}
