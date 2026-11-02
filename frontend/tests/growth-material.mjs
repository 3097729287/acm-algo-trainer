import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const vite=await createServer({server:{host:'127.0.0.1',port:0}});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:2048,height:1152}}),errors=[];
page.on('pageerror',error=>errors.push(error.message));
const output='../.backups/next-150/growth-material-browser';await mkdir(output,{recursive:true});
const report={ok:false,layouts:[],originalSubmissions:0,productionOperations:0};
try{
 await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/growth-material-fixture.html`);
 for(const width of [2048,1440,960,430])for(const theme of ['dark','light']){
  await page.setViewportSize({width,height:1152});await page.evaluate(theme=>growthCheck.theme(theme),theme);
  await page.locator('.account-hero-identity').waitFor();
  const geometry=await page.evaluate(()=>{
   const rect=selector=>{const r=document.querySelector(selector).getBoundingClientRect();return {top:r.top,bottom:r.bottom,height:r.height,width:r.width};};
   return {identityDocumentTop:rect('.account-hero-identity').top+scrollY,identity:rect('.account-hero-identity'),level:rect('.account-hero-level'),stats:rect('.account-hero-statistics'),controls:rect('.sticker-mode-toolbar'),content:rect('.sticker-content'),statTops:[...document.querySelectorAll('.account-hero-statistics>div')].map(node=>node.getBoundingClientRect().top),horizontalOverflow:document.documentElement.scrollWidth>innerWidth};
  });
  report.currentLayout={width,theme,...geometry};assert(geometry.identity.bottom<=geometry.level.top+1);assert(geometry.level.bottom<=geometry.stats.top+1);assert(geometry.stats.bottom<=geometry.controls.top+1);
  assert(!geometry.horizontalOverflow,JSON.stringify({width,geometry}));
  if(width>=960)assert(Math.max(...geometry.statTops)-Math.min(...geometry.statTops)<1,'Six compact statistics share one row');
  assert(geometry.content.height>=330);
  assert.equal(await page.locator('#growth-goals').count(),0,'Goals appear only after the target button');
  await page.getByRole('button',{name:'目标',exact:true}).click();await page.getByRole('button',{name:'新建目标',exact:true}).waitFor();
  const position=await page.locator('.account-hero-identity').boundingBox();assert(Math.abs(await page.locator('.account-hero-identity').evaluate(node=>node.getBoundingClientRect().top+scrollY)-geometry.identityDocumentTop)<1,'Opening goals preserves the portrait position');
  await page.getByRole('button',{name:'目标',exact:true}).click();assert.equal(await page.locator('#growth-goals').count(),0);
  await page.getByRole('button',{name:'贴纸',exact:true}).click();assert.equal(await page.locator('.sticker-mode').count(),1);
  const rank=await page.locator('.account-hero-rank').boundingBox();assert(rank&&rank.y<=geometry.level.top);
  assert.equal(await page.locator('.account-hero-rank>strong').evaluate(node=>getComputedStyle(node).visibility),'hidden');
  await page.keyboard.press('Escape');assert.equal(await page.locator('.sticker-mode').count(),0);
  report.layouts.push({width,theme,...geometry});
  if(width===2048)await page.screenshot({path:`${output}/growth-${theme}.png`});
 }
 await page.setViewportSize({width:1200,height:1000});await page.evaluate(()=>{growthCheck.theme('dark');growthCheck.setPanel('art');});await page.locator('.material-gallery').waitFor();
 await page.screenshot({path:output+'/materials-dark.png'});
 await page.evaluate(()=>growthCheck.theme('light'));await page.screenshot({path:output+'/materials-light.png'});
 await page.evaluate(()=>growthCheck.setPanel('rankings'));await page.getByLabel('admin 密码',{exact:true}).waitFor();
 await page.getByLabel('admin 密码',{exact:true}).fill('fixture-password');await page.getByRole('button',{name:'登录管理账号',exact:true}).click();
 await page.getByText('其他训练者',{exact:true}).waitFor();assert.equal(await page.locator('.ranking-self').count(),0);
 await page.getByRole('tab',{name:'本周',exact:true}).click();await page.getByText('其他训练者',{exact:true}).waitFor();
 const calls=await page.evaluate(()=>growthCheck.calls);
 assert.equal(calls.filter(call=>call.method==='POST').length,1,'The only write is the deliberate administrator login; no score upload');
 assert.deepEqual(errors,[]);report.ok=true;report.adminCanReadOthers=true;report.adminHidden=true;
 console.log(JSON.stringify({ok:true,layouts:report.layouts.length,adminReadOnly:true,output}));
}catch(error){report.failure=error.message;await page.screenshot({path:output+'/failure.png'}).catch(()=>{});throw error;}
finally{await writeFile(output+'/report.json',JSON.stringify({...report,errors},null,2)+'\n');await browser.close();await vite.close();}
