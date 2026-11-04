import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import {chromium} from 'playwright';
const directory='E:/项目/ToBe/设计预览/学习进度UI-20261105/检查',desktop='C:/Users/lenovo/Desktop/ToBe-学习进度与周计划-UI方案';await mkdir(directory,{recursive:true});
const files=['A-清晰工作台','B-轻量学习清单','C-紧凑训练面板','D-随行学习面板'],views=['overview','today','week','progress','feedback','time','history','floating','recommend'];
const browser=await chromium.launch({channel:'msedge',headless:true}),context=await browser.newContext(),page=await context.newPage(),errors=[],network=[],checked=[];
page.on('pageerror',error=>errors.push(error.message));page.on('request',request=>{if(/^https?:/.test(request.url()))network.push(request.url());});
try{
 for(const name of files){
  await page.setViewportSize({width:1440,height:1040});await page.goto(pathToFileURL(desktop+'/'+name+'.html').href);await page.locator('.next-card').first().waitFor();await page.screenshot({path:directory+'/'+name+'-概览.png'});
  for(const width of [1440,900,390]){await page.setViewportSize({width,height:980});for(const view of views){await page.evaluate(view=>{location.hash=view;},view);await page.locator('.view-'+view).waitFor();assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,name+' '+view+' '+width+' overflow');checked.push({name,view,width});}if(width===390){await page.evaluate(()=>location.hash='overview');await page.locator('.view-overview').waitFor();await page.screenshot({path:directory+'/'+name+'-窄屏.png'});}}
  await page.setViewportSize({width:1440,height:1040});await page.evaluate(()=>location.hash='feedback');await page.locator('.view-feedback').waitFor();await page.locator('.feedback-options>button').first().click();await page.getByRole('button',{name:'就按这个调整',exact:true}).click();assert.match(await page.locator('.top-next').innerText(),/窗口怎样向右移动/);
  await page.evaluate(()=>location.hash='week');await page.locator('.view-week').waitFor();assert.match(await page.locator('.day-agenda').innerText(),/窗口怎样向右移动/);await page.screenshot({path:directory+'/'+name+'-周计划.png'});
  await page.evaluate(()=>location.hash='time');await page.locator('.view-time').waitFor();await page.locator('.time-choices>button').first().click();await page.getByRole('button',{name:'按这个安排',exact:true}).click();await page.locator('.view-week').waitFor();assert.match(await page.locator('.top-next').innerText(),/窗口边界小测/);assert.match(await page.locator('.day-agenda').innerText(),/窗口边界小测/);
  await page.getByRole('button',{name:'展开顶部推荐',exact:true}).click();await page.locator('.top-recommend-menu').waitFor();assert.match(await page.locator('.top-recommend-menu').innerText(),/窗口边界小测/);
  await page.evaluate(()=>location.hash='floating');await page.locator('.learning-floating').waitFor();await page.screenshot({path:directory+'/'+name+'-浮窗.png'});
 }
 await page.goto(pathToFileURL(desktop+'/index.html').href);await page.locator('.scheme').first().waitFor();assert.equal(await page.locator('.scheme').count(),4);assert.equal(await page.locator('.scheme-links>a').count(),36);await page.screenshot({path:directory+'/00-全部方案.png',fullPage:true});
 assert.deepEqual(errors,[]);assert.deepEqual(network,[]);const result={passed:true,schemes:files.length,viewsPerScheme:views.length,layoutChecks:checked.length,sharedRecommendationVerified:true,feedbackVerified:true,timeRescheduleVerified:true,externalRequests:network,errors};await writeFile(directory+'/result.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
}catch(error){await page.screenshot({path:directory+'/failure.png'});console.log(JSON.stringify({errors,network}));throw error;}finally{await browser.close();}
