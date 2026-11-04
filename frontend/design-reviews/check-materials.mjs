import assert from 'node:assert/strict';
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {chromium} from 'playwright';
const directory='E:/项目/ToBe/设计预览/贴纸背景与声音-20261105',file='C:/Users/lenovo/Desktop/ToBe-贴纸背景与声音审批.html';
await mkdir(directory+'/检查',{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true}),context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true}),page=await context.newPage(),errors=[],network=[];
page.on('pageerror',error=>errors.push(error.message));page.on('request',request=>{if(/^https?:/.test(request.url()))network.push(request.url());});
await page.addInitScript(()=>{window.reviewAudioEvents=[];const Audio=window.AudioContext;window.AudioContext=class extends Audio{createOscillator(){const node=super.createOscillator(),start=node.start.bind(node);node.start=(...args)=>{window.reviewAudioEvents.push({kind:'tone',frequency:node.frequency.value});return start(...args);};return node;}createBufferSource(){const node=super.createBufferSource(),start=node.start.bind(node);node.start=(...args)=>{window.reviewAudioEvents.push({kind:'buffer',duration:node.buffer?.duration});return start(...args);};return node;}};});
try{
 await page.goto(pathToFileURL(file).href);await page.locator('.material-card').first().waitFor();
 assert.equal(await page.locator('.material-card').count(),62);
 assert.equal(await page.locator('.sound-button').count(),29,'All 15 epic and 14 legendary stickers have a matching sound');
 const sounds=await page.locator('.sound-button').evaluateAll(nodes=>nodes.map(node=>node.getAttribute('aria-label')));
 const auditioned=[];
 for(const label of sounds){const before=await page.evaluate(()=>window.reviewAudioEvents.length);await page.getByRole('button',{name:label,exact:true}).click();await page.waitForFunction(before=>window.reviewAudioEvents.length>before,before);auditioned.push(label);}
 await page.getByLabel('嘴强小黄鸭 稀有度',{exact:true}).selectOption('epic');await page.getByLabel('确认 achievement-duck 稀有度',{exact:true}).click();
 const duck=page.locator('[data-item-id="achievement-duck"]');await duck.getByLabel('外观要修改',{exact:true}).check();await duck.getByLabel('嘴强小黄鸭 修改意见',{exact:true}).fill('鸭嘴改小一点');
 await page.screenshot({path:directory+'/检查/01-贴纸审批.png',fullPage:false});
 await page.getByRole('button',{name:'背景 52',exact:true}).click();assert.equal(await page.locator('.material-card').count(),52);
 await page.getByRole('button',{name:'放大 background-night-common',exact:true}).click();const modal=page.getByRole('dialog');await modal.waitFor();assert(await modal.locator('[data-background-theme="night"]').isVisible());await modal.getByLabel('外观要修改',{exact:true}).check();await modal.getByLabel('安静夜晚 修改意见',{exact:true}).fill('星星更亮');await modal.getByRole('button',{name:'关闭预览',exact:true}).click();
 await page.screenshot({path:directory+'/检查/02-背景审批.png',fullPage:false});
 await page.getByRole('button',{name:'小黄鸭叫声 2 选 1',exact:true}).click();
 const calls=await page.locator('audio').evaluateAll(async nodes=>{const ctx=new AudioContext();const info=[];for(const node of nodes){const response=await fetch(node.src),buffer=await ctx.decodeAudioData(await response.arrayBuffer());const data=buffer.getChannelData(0);let squares=0;for(const sample of data)squares+=sample*sample;info.push({duration:buffer.duration,rms:Math.sqrt(squares/data.length)});}await ctx.close();return info;});
 assert(Math.abs(calls[0].duration-.47)<.001);assert(Math.abs(calls[1].duration-.53)<.001);assert(calls.every(call=>call.rms>.01));
 await page.getByRole('radio').nth(1).check();assert.equal(await page.getByRole('radio').first().isChecked(),false);assert.equal(await page.getByRole('radio').nth(1).isChecked(),true);
 await page.screenshot({path:directory+'/检查/03-鸭声二选一.png'});
 const pending=page.waitForEvent('download');await page.getByRole('button',{name:'导出这个选择',exact:true}).click();const download=await pending;const exportedPath=directory+'/检查/测试审批结果.json';await download.saveAs(exportedPath);const exported=JSON.parse(await readFile(exportedPath,'utf8'));
 assert.equal(exported.duckSound.keepCall,2);assert.equal(exported.duckSound.removeOtherCall,true);assert.equal(exported.items.find(item=>item.id==='achievement-duck').requestedRarity,'epic');assert.equal(exported.items.find(item=>item.id==='achievement-duck').notes,'鸭嘴改小一点');assert.equal(exported.items.find(item=>item.id==='background-night-common').notes,'星星更亮');
 assert.equal(exported.sourceVersion,(await readFile(new URL('../../VERSION',import.meta.url),'utf8')).trim());
 await page.reload();await page.getByRole('radio').nth(1).waitFor();assert.equal(await page.getByRole('radio').nth(1).isChecked(),true,'Selection persists across reopening');
 await page.goto(pathToFileURL(file).href+'#backgrounds');await page.locator('.material-card').first().waitFor();
 for(const width of [1440,900,390]){await page.setViewportSize({width,height:900});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,'No horizontal overflow at '+width);}
 await page.screenshot({path:directory+'/检查/04-窄屏背景.png'});
 await page.goto(pathToFileURL('C:/Users/lenovo/Desktop/ToBe-小黄鸭叫声选择.html').href);await page.getByRole('radio').first().waitFor();assert.equal(await page.getByRole('radio').count(),2);
 await page.goto(pathToFileURL('C:/Users/lenovo/Desktop/ToBe-背景审批.html').href);await page.locator('.background-grid .material-card').first().waitFor();assert.equal(await page.locator('.material-card').count(),52);
 assert.deepEqual(errors,[]);assert.deepEqual(network,[]);
 // Tests use their own browser profile. No sample approvals reach the user's file profile.
 const result={passed:true,stickers:62,backgrounds:52,soundsAuditioned:auditioned.length,duckCalls:calls,exportVerified:true,viewports:[1440,900,390],externalRequests:network,errors};await writeFile(directory+'/检查/result.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
}catch(error){await page.screenshot({path:directory+'/检查/failure.png'});throw error;}finally{await browser.close();}
