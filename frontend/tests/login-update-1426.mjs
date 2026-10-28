import assert from 'node:assert/strict';
import {preview} from 'vite';
import {chromium} from 'playwright';
import fs from 'node:fs';
const original=process.argv.includes('--original');
const directory=process.env.TB_UI_DIST||'dist';
const server=await preview({build:{outDir:directory},preview:{host:'127.0.0.1',port:0}});
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const report={original,restoringUpdate:false,legacyRestoreRecovery:false,loginRejectedUpdate:false};
try {
 for(const scenario of ['restoring','legacy','login-rejected']) {
  const page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[],calls=[];
  let restoring=scenario!=='login-rejected',ready=scenario!=='login-rejected',allowInstall=false,installed=false;
  page.on('pageerror',issue=>errors.push(issue.message));
  await page.route('**/api/**',async route=>{
   const request=route.request(),path=new URL(request.url()).pathname;
   calls.push({path,method:request.method()});
   if(path==='/api/account')return route.fulfill({json:{required:true,authenticated:false,restoring,token:'isolated-login-update-token',error:restoring?'':'此版本需要更新'}});
   if(path==='/api/account/login')return route.fulfill({status:426,json:{error:'此版本需要更新'}});
   if(path==='/api/software-update')return route.fulfill({json:{currentVersion:'1.4.25',latestVersion:'1.4.26',status:installed?'installing':ready?'ready':'downloading',canInstall:true,automatic:true,autoCheck:true,releaseUrl:'https://47.82.84.74/updates/stable/index.html',notes:'',downloadedBytes:0,totalBytes:10}});
   if(path==='/api/software-update/install') {
    assert.equal(request.headers()['x-tb-token'],'isolated-login-update-token');
    if(!allowInstall)return route.fulfill({status:409,json:{error:'请等待当前评测完成后再安装更新'}});
    installed=true;return route.fulfill({json:{status:'installing',currentVersion:'1.4.25',latestVersion:'1.4.26',automatic:true,canInstall:true}});
   }
   throw new Error('Unexpected authenticated API during pre-login update: '+path);
  });
  await page.goto(server.resolvedUrls.local[0]);
  if(scenario==='restoring'&&!original) {
   await page.getByLabel('ToBe 启动',{exact:true}).waitFor();
   await page.getByLabel('软件更新提示',{exact:true}).waitFor();
   await page.waitForFunction(()=>document.body.innerText.includes('请等待当前评测'));
   allowInstall=true;
   await page.waitForFunction(()=>document.body.innerText.includes('正在关闭 ToBe'),null,{timeout:15000});
   assert(restoring,'the install must finish while the login restore remains pending');report.restoringUpdate=true;
  } else if(scenario==='legacy'||original&&scenario==='restoring') {
   await page.getByLabel('ToBe 启动',{exact:true}).waitFor();
   if(original) {
    await page.waitForTimeout(1300);
    assert.equal(calls.filter(c=>c.path==='/api/software-update/install').length,0,'original gate defers updates during restore');
   }
   // A 401 on the legacy private-state restore clears only its saved session;
   // /api/account then exposes the login screen and its existing updater.
   restoring=false;allowInstall=true;
   await page.waitForFunction(()=>document.body.innerText.includes('正在关闭 ToBe'),null,{timeout:15000});
   report.legacyRestoreRecovery=true;
  } else {
   await page.getByRole('heading',{name:'登录 ToBe',exact:true}).waitFor();
   await page.getByLabel('登录号',{exact:true}).fill('isolated_user');
   await page.getByLabel('密码',{exact:true}).fill('fixture-password');
   await page.getByRole('button',{name:'登录',exact:true}).click();
   await page.getByRole('alert').filter({hasText:'此版本需要更新'}).waitFor();
   ready=true;allowInstall=true;
   await page.waitForFunction(()=>document.body.innerText.includes('正在关闭 ToBe'),null,{timeout:15000});
   report.loginRejectedUpdate=true;
  }
  assert(installed);assert.equal(await page.locator('.workspace-area').count(),0);assert.deepEqual(errors,[]);
  await page.close();
 }
 fs.mkdirSync('../.backups/local-1426',{recursive:true});
 fs.writeFileSync(`../.backups/local-1426/login-update-${original?'original':'fixed'}-ui.json`,JSON.stringify({...report,ok:true},null,2));
 console.log(JSON.stringify({...report,ok:true}));
} finally {await browser.close();await new Promise(resolve=>server.httpServer.close(resolve));}
