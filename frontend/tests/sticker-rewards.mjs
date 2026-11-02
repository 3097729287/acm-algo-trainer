import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';
import {levelBox} from '../../server/leaderboard/src/sticker-rewards.mjs';
import {STICKERS} from '../../server/leaderboard/src/gameplay.mjs';
process.env.TB_OFFLINE='1';
const out='../.backups/learning-browser/rewards-ui';await mkdir(out,{recursive:true});
const server=await createServer({cacheDir:'../.backups/learning-browser/vite-rewards',server:{host:'127.0.0.1',port:0}});await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1300,height:1000}}),errors=[];
page.on('pageerror',issue=>errors.push(issue.message));page.setDefaultTimeout(12000);
await page.addInitScript(value=>window.rewardFixtureData=value,{catalogue:STICKERS,boxes:[levelBox(5),levelBox(10)]});
try{
 await page.goto(server.resolvedUrls.local[0]+'tests/sticker-rewards-fixture.html');
 await page.getByRole('button',{name:'贴纸宝箱',exact:true}).waitFor();
 assert(await page.getByText('传说贴纸 · 嘴强小黄鸭',{exact:true}).isVisible());assert(await page.getByText('任务奖励 · +35 XP',{exact:true}).isVisible());assert.equal(await page.getByRole('button',{name:/领取.*奖励/}).count(),0);
 await page.getByRole('button',{name:'贴纸宝箱',exact:true}).click();const boxes=page.getByRole('dialog',{name:'贴纸宝箱',exact:true});
 assert.match(await boxes.getByRole('region',{name:'Lv.5 贴纸宝箱'}).innerText(),/2 张贴纸/);
 await boxes.getByRole('button',{name:'开启 Lv.5 宝箱',exact:true}).click();await boxes.getByRole('alert').waitFor();
 await boxes.getByRole('button',{name:'开启 Lv.5 宝箱',exact:true}).click();await boxes.getByLabel('本次获得的贴纸',{exact:true}).waitFor();
 const attempts=await page.evaluate(()=>window.rewardFixture.calls.filter(call=>call.path==='stickers/open-box'));assert.equal(attempts.length,2);assert.equal(attempts[0].body.requestId,attempts[1].body.requestId);
 assert.equal(await page.evaluate(()=>window.rewardFixture.state().units.length),4);
 assert.equal(await boxes.getByRole('button',{name:'开启 Lv.5 宝箱',exact:true}).count(),0);await page.screenshot({path:out+'/opened-box.png'});
 await boxes.getByRole('button',{name:'关闭贴纸宝箱',exact:true}).click();
 const original=page.getByRole('button',{name:'回复 训练者乙 的留言',exact:true});await original.click();
 const message=page.locator('dialog.social-comment-dialog');await message.getByRole('button',{name:'赠送贴纸',exact:true}).click();
 await message.getByRole('button',{name:'赠送 嘴强小黄鸭',exact:true}).click();assert.equal(await message.getByLabel('留言内容',{exact:true}).inputValue(),'送你一张贴纸');
 await message.getByLabel('留言内容',{exact:true}).fill('祝你好运！');await page.screenshot({path:out+'/gift-comment.png'});await message.getByRole('button',{name:'发送留言',exact:true}).click();
 await message.waitFor({state:'hidden'});await original.getByLabel('我的回复',{exact:true}).getByText('祝你好运！',{exact:true}).waitFor();
 assert.match(await original.getByLabel('我的回复',{exact:true}).innerText(),/嘴强小黄鸭/);assert.equal(await page.evaluate(()=>window.rewardFixture.state().units.length),3);
 await page.reload();await page.getByLabel('我的回复',{exact:true}).getByText('祝你好运！',{exact:true}).waitFor();
 for(const theme of ['dark','light'])for(const width of [1300,800,390]){await page.setViewportSize({width,height:1000});await page.evaluate(theme=>document.documentElement.dataset.theme=theme,theme);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);await page.screenshot({path:`${out}/rewards-${theme}-${width}.png`});}
 assert.deepEqual(errors,[]);await writeFile(out+'/result.json',JSON.stringify({passed:true,scenarios:['pending reward preview','earned-level count and odds','lost-response retry','one-time box opening','gift picker and exact recipient','owned inventory transfer','reply display after reload','six layouts'],errors},null,2));
 console.log('Sticker reward UI passed: previews, box odds, response-loss retry, gifting, persisted replies and six layouts.');
}catch(issue){await page.screenshot({path:out+'/failure.png'});await writeFile(out+'/failure.json',JSON.stringify({message:issue.message,errors},null,2));throw issue;}
finally{await browser.close();await server.close();}
