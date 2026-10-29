import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';
import {createServer} from 'vite';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),out=path.join(root,'tests/screenshots/admin-settings');
await mkdir(out,{recursive:true});
const fixture=`import React from 'react';import{createRoot}from'react-dom/client';import AdminSettings from '/src/pages/AdminSettings.jsx';import '/src/styles/workspace.css';
window.__tbAdmin=true;window.refreshed=0;
const api=async(path,body)=>{const response=await fetch('/api/'+path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json'},...(body===undefined?{}:{body:JSON.stringify(body)})});const value=await response.json();if(!response.ok)throw Error(value.error);return value;};
createRoot(document.getElementById('root')).render(React.createElement(AdminSettings,{api,onChanged:()=>{window.refreshed++;},onError:message=>{throw Error(message);}}));`;
const html=`<!doctype html><html data-theme="dark"><head><meta charset="utf-8"><style>html,body{height:auto;overflow:visible}body{margin:0;padding:16px}#root{max-width:100%;min-width:0}</style></head><body><div id="root"></div><script type="module" src="/@id/virtual:admin-settings.jsx"></script></body></html>`;
const vite=await createServer({root,server:{host:'127.0.0.1',port:0,watch:null},plugins:[{
 name:'admin-settings-fixture',configureServer(server){server.middlewares.use(async(req,res,next)=>{if(req.url!=='/admin-fixture')return next();res.setHeader('Content-Type','text/html;charset=utf-8');res.end(await server.transformIndexHtml('/admin-fixture',html));});},
 resolveId(id){if(id==='virtual:admin-settings.jsx')return '\0virtual:admin-settings.jsx';},load(id){if(id==='\0virtual:admin-settings.jsx')return fixture;},
}]});
await vite.listen();
const browser=await chromium.launch({headless:true}),page=await browser.newPage({viewport:{width:960,height:850}}),errors=[],unknown=[],requests=[],writes=[];
page.on('pageerror',error=>errors.push(error.message));
let logged=false,failSearch=false,config={level:100,tier:8,allAchievements:true};
const target={userId:'11111111-1111-4111-8111-111111111111',loginId:'target_user',nickname:'隔离账号',createdAt:'2026-10-29',protected:false};
const admin={...target,userId:'22222222-2222-4222-8222-222222222222',loginId:'admin',nickname:'管理员',protected:true};
const report={ok:false,realOfficialSubmissionsSent:0,productionAccountOperations:0,geometry:[]};
await page.route('**/api/**',async route=>{
 const request=route.request(),url=new URL(request.url()),method=request.method(),body=request.postDataJSON(),p=url.pathname;
 requests.push({path:p,method});let value,status=200;
 if(p==='/api/admin/session'&&method==='GET')value={authenticated:logged,configured:true,loginId:'admin'};
 else if(p==='/api/admin/session'&&method==='POST'){assert.deepEqual(body,{password:'fixture-admin-password'});logged=true;value={authenticated:true,configured:true,loginId:'admin'};}
 else if(p==='/api/admin/logout'){logged=false;value={authenticated:false,configured:true,loginId:'admin'};}
 else if(p==='/api/admin'){if(method==='POST'){assert.deepEqual(Object.keys(body).sort(),['allAchievements','level','tier']);config=body;}value=config;}
 else if(p==='/api/admin/accounts'&&method==='GET'){
  assert(logged,'An unauthenticated UI cannot search accounts');
  if(failSearch){status=503;value={error:'隔离服务暂不可用'};}else value={accounts:url.searchParams.get('q')==='admin'?[admin]:url.searchParams.get('q')===target.loginId?[target]:[]};
 }else if(['/api/admin/accounts/delete','/api/admin/accounts/reset-password'].includes(p)&&method==='POST'){
  assert(logged);assert.deepEqual(body,{userId:target.userId,loginId:target.loginId,confirmation:p.endsWith('/delete')?'delete-account':'reset-password'});writes.push({path:p,body});
  value={ok:true,userId:target.userId,loginId:target.loginId,[p.endsWith('/delete')?'deleted':'sessionsRevoked']:true};
 }else{unknown.push({path:p,method});return route.abort();}
 await route.fulfill({status,contentType:'application/json',body:JSON.stringify(value)});
});
async function lookup(value){await page.getByRole('textbox',{name:'查找账号',exact:true}).fill(value);await page.getByRole('button',{name:'查找账号',exact:true}).click();}
async function noOverflow(){return page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth);}
try {
 await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/admin-fixture`);
 await page.getByRole('spinbutton',{name:'管理员等级'}).waitFor();
 assert.equal(await page.getByRole('region',{name:'账号维护'}).count(),0);
 assert(await page.getByRole('checkbox',{name:'预览全部成就'}).isChecked());
 await page.getByRole('checkbox',{name:'预览全部成就'}).uncheck();await page.waitForFunction(()=>window.refreshed>=1);assert.equal(config.allAchievements,false);
 await page.getByRole('checkbox',{name:'预览全部成就'}).check();await page.waitForFunction(()=>window.refreshed>=2);assert.equal(config.allAchievements,true);
 await page.getByRole('spinbutton',{name:'管理员等级'}).fill('7');await page.waitForFunction(()=>window.refreshed>=3);assert.equal(config.level,7);
 await page.getByLabel('admin 密码',{exact:true}).fill('fixture-admin-password');await page.getByRole('button',{name:'登录管理账号'}).click();
 await page.getByRole('region',{name:'账号维护'}).waitFor();
 assert.equal(await page.getByLabel('admin 密码',{exact:true}).count(),0);
 await lookup(target.loginId);await page.getByRole('button',{name:'重置 target_user 的密码'}).click();
 await page.getByRole('dialog',{name:'重置密码',exact:true}).waitFor();assert(await page.getByRole('button',{name:'确认重置'}).isDisabled());
 await page.getByRole('button',{name:'取消',exact:true}).click();assert.equal(writes.length,0);
 await page.getByRole('button',{name:'重置 target_user 的密码'}).click();await page.getByRole('textbox',{name:'确认操作的登录号'}).fill('another_user');assert(await page.getByRole('button',{name:'确认重置'}).isDisabled());
 await page.getByRole('textbox',{name:'确认操作的登录号'}).fill(target.loginId);await page.getByRole('button',{name:'确认重置'}).click();await page.getByText('密码已重置，原登录已失效',{exact:true}).waitFor();assert.equal(writes.length,1);
 assert(!/123456|scrypt|password_hash/.test(await page.locator('body').innerText()));
 await lookup('admin');assert(await page.getByRole('button',{name:'删除账号 admin',exact:true}).isDisabled());assert(await page.getByRole('button',{name:'重置 admin 的密码',exact:true}).isDisabled());
 await lookup(target.loginId);await page.getByRole('button',{name:'删除账号 target_user'}).click();await page.getByRole('dialog',{name:'删除账号',exact:true}).waitFor();await page.keyboard.press('Escape');assert.equal(await page.getByRole('dialog').count(),0);assert.equal(writes.length,1);
 for(const width of [960,430])for(const theme of ['dark','light']){
  await page.setViewportSize({width,height:850});await page.evaluate(theme=>document.documentElement.dataset.theme=theme,theme);
  await page.getByRole('button',{name:'删除账号 target_user'}).click();await page.getByRole('dialog',{name:'删除账号',exact:true}).waitFor();
  const box=await page.getByRole('dialog').boundingBox();assert(box&&box.x>=0&&box.x+box.width<=width);assert(await noOverflow());
  await page.screenshot({path:path.join(out,`confirm-${width}-${theme}.png`),fullPage:true});report.geometry.push({width,theme,box});await page.getByRole('button',{name:'取消',exact:true}).click();
 }
 await page.getByRole('button',{name:'删除账号 target_user'}).click();await page.getByRole('textbox',{name:'确认操作的登录号'}).fill(target.loginId);await page.getByRole('button',{name:'确认删除',exact:true}).click();await page.getByText('账号已删除',{exact:true}).waitFor();assert.equal(writes.length,2);
 await lookup('unknown_user');await page.getByText('没有找到账号',{exact:true}).waitFor();
 failSearch=true;await lookup(target.loginId);await page.getByRole('alert').getByText('隔离服务暂不可用',{exact:true}).waitFor();assert.equal(await page.getByRole('button',{name:'删除账号 target_user'}).count(),0);
 await page.getByRole('button',{name:'退出管理账号'}).click();await page.getByRole('button',{name:'登录管理账号'}).waitFor();assert.equal(await page.getByRole('region',{name:'账号维护'}).count(),0);
 assert.deepEqual(errors,[]);assert.deepEqual(unknown,[]);
 Object.assign(report,{ok:true,localControls:true,achievementToggle:true,authenticatedOnly:true,typedConfirmation:true,cancelAndEscape:true,protectedAdmin:true,noSecretDisplay:true,exactTargetWrites:true,errorsAndLogout:true});
 console.log(JSON.stringify({ok:true,geometry:report.geometry.length,isolatedAccountWrites:writes.length}));
}catch(error){report.failure=error.message;await page.screenshot({path:path.join(out,'failure.png'),fullPage:true}).catch(()=>{});throw error;}
finally{await writeFile(path.join(out,'report.json'),JSON.stringify({...report,errors,unknown,requests,writes},null,2));await browser.close();await vite.close();}
