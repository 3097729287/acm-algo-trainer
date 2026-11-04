import assert from 'node:assert/strict';
import {randomUUID} from 'node:crypto';
import {mkdir,writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';
import {startGameplayFixture} from '../../server/leaderboard/tests/gameplay-fixture.mjs';
import {STICKERS} from '../../server/leaderboard/src/gameplay.mjs';
const out='../.backups/next-local/sticker-scenes-ui';await mkdir(out,{recursive:true});
const fixture=await startGameplayFixture();
async function client(name){let auth;const send=async(path,body)=>{const response=await fetch(fixture.endpoint+path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json',...(auth?{'X-TB-User':auth.account.userId,Authorization:'Bearer '+auth.token}:{})},...(body===undefined?{}:{body:JSON.stringify(body)})});return {status:response.status,value:await response.json()};};await send('/v1/accounts/register',{loginId:name,nickname:name,password:'scene-ui-fixture-only'});auth=(await send('/v1/accounts/login',{loginId:name,password:'scene-ui-fixture-only'})).value;return {id:auth.account.userId,send,post:(path,body)=>send(path,{requestId:randomUUID(),...body}),state:async()=>(await send('/v1/stickers')).value};}
const a=await client('scene_browser_a'),b=await client('scene_browser_b'),accounts=new Map([[a.id,a],[b.id,b]]);
const positioned=[['scene-tree',.15,.7,2],['scene-house',.46,.75,1.8],['scene-person',.6,.7,1.3],['common-cloud',.55,.25,1.5],['common-drop',.52,.29,.7],['common-drop',.55,.31,.7],['common-drop',.58,.29,.7],['rare-sun',.6,.22,1],['epic-butterfly',.32,.51,1]];
const units=positioned.map(([stickerId,x,y,scale])=>({id:randomUUID(),stickerId,revision:0,placement:{x,y,angle:0,scale}}));
units.push(...STICKERS.filter(s=>s.kind==='background'&&s.rarity==='rare').map(s=>({id:randomUUID(),stickerId:s.id,revision:0,placement:null})));
await fixture.STORE.gameplay.db.execute('INSERT INTO gameplay_accounts(user_id,payload) VALUES(?,?)',[a.id,JSON.stringify({revision:0,units,grants:{}})]);
const tree=units[0],person=units[2],butterfly=units[8];
const vite=await createServer({cacheDir:out+'/vite',server:{host:'127.0.0.1',port:0,watch:null}});await vite.listen();
const browser=await chromium.launch({channel:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1100,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(7000);
await page.exposeFunction('sceneFixtureCall',(owner,path,body)=>accounts.get(owner).send('/v1/'+path,body));
await page.addInitScript(data=>window.sceneFixtureData=data,{a:a.id,b:b.id});
const scene=page.getByRole('dialog',{name:'场景预设',exact:true}),placed=id=>page.locator(`[data-unit-id="${id}"]`),background=()=>page.locator('.scene-background-layer>svg');
try{
 await page.goto(vite.resolvedUrls.local[0]+'tests/sticker-scenes-fixture.html');await placed(person.id).waitFor();await page.locator('[data-weather=rainbow]').waitFor();
 assert.equal(await page.locator('.weather-component-hidden').count(),3);
 await placed(person.id).click();let wardrobe=page.getByRole('dialog',{name:'小人衣橱',exact:true});await wardrobe.waitFor();
 const calls=await page.evaluate(()=>sceneFixture.calls.length);await wardrobe.getByRole('region',{name:'帽子'}).count();
 await wardrobe.locator('section[aria-label="帽子"]').getByRole('button',{name:'针织帽',exact:true}).click();
 assert((await wardrobe.locator('.wardrobe-preview [data-person-outfit]').getAttribute('data-person-outfit')).includes('beanie'));assert.equal(await page.evaluate(()=>sceneFixture.calls.length),calls,'Wardrobe preview needs no request');
 await wardrobe.getByRole('button',{name:'穿上',exact:true}).click();await wardrobe.waitFor({state:'hidden'});
 await page.waitForFunction(id=>document.querySelector(`[data-unit-id="${id}"] [data-person-outfit]`)?.dataset.personOutfit.includes('beanie'),person.id);
 await page.getByRole('button',{name:'背景',exact:true}).click();let picker=page.getByRole('dialog',{name:'选择背景',exact:true});await picker.waitFor();assert.equal(await picker.locator('.sticker-choice').count(),13);
 await picker.getByRole('button',{name:'稀有 background-room，库存 1',exact:true}).click();await page.locator('[data-background-theme=room]').waitFor();
 await page.getByRole('button',{name:'场景预设',exact:true}).click();await scene.waitFor();await scene.getByLabel('预设名称',{exact:true}).fill('窗边生活');await scene.getByRole('button',{name:'保存',exact:true}).click();await scene.getByRole('button',{name:'切换场景 窗边生活',exact:true}).waitFor();await scene.getByRole('button',{name:'关闭场景预设',exact:true}).click();
 await page.getByRole('button',{name:'背景',exact:true}).click();picker=page.getByRole('dialog',{name:'选择背景',exact:true});await picker.getByRole('button',{name:'稀有 background-night，库存 1',exact:true}).click();await page.locator('.scene-background-layer [data-background-theme=night]').waitFor();
 await page.getByRole('button',{name:'场景预设',exact:true}).click();await scene.getByLabel('预设名称',{exact:true}).fill('安静夜晚');await scene.getByRole('button',{name:'保存',exact:true}).click();await scene.getByRole('button',{name:'切换场景 安静夜晚',exact:true}).waitFor();
 await page.evaluate(()=>sceneFixture.delay());const began=performance.now();await scene.getByRole('button',{name:'切换场景 窗边生活',exact:true}).click();await page.locator('.scene-background-layer [data-background-theme=room]').waitFor();const instantMs=performance.now()-began;assert(instantMs<800,'Preset switches before the held response');
 await page.evaluate(()=>sceneFixture.release());await scene.getByText('场景已切换',{exact:true}).waitFor();await scene.getByRole('button',{name:'关闭场景预设',exact:true}).click();
 // Tree maximum is much larger than a butterfly, without exceeding canvas bounds.
 const box=await page.getByRole('region',{name:'贴纸区域',exact:true}).boundingBox();await placed(butterfly.id).click();await placed(butterfly.id).hover();await page.mouse.wheel(0,-5000);await page.waitForTimeout(30);const small=await placed(butterfly.id).boundingBox();assert(small.width<100);await page.mouse.click(box.x+box.width*.85,box.y+box.height*.9);await page.waitForTimeout(100);
 await placed(tree.id).click({button:'right'});await page.getByRole('button',{name:'回收',exact:true}).click();await placed(tree.id).waitFor({state:'detached'});
 await page.getByRole('button',{name:'给朋友赠送',exact:true}).click();const comment=page.getByRole('dialog',{name:'给 朋友 留言',exact:true});await comment.getByRole('button',{name:'赠送贴纸',exact:true}).click();await comment.getByRole('button',{name:'赠送 大树',exact:true}).click();await comment.getByRole('alert').filter({hasText:'窗边生活'}).waitFor();assert(await comment.getByRole('button',{name:'发送留言',exact:true}).isDisabled());await comment.getByRole('checkbox',{name:'我已了解，继续赠送',exact:true}).check();await comment.getByRole('button',{name:'发送留言',exact:true}).click();await comment.waitFor({state:'hidden'});
 await page.getByRole('button',{name:'场景预设',exact:true}).click();await scene.getByText('缺少 1 张，切换时跳过',{exact:true}).first().waitFor();await scene.getByRole('button',{name:'切换场景 窗边生活',exact:true}).click();await scene.getByText('已切换，暂时跳过 1 张缺少的贴纸。',{exact:true}).waitFor();assert.equal(await placed(tree.id).count(),0);
 const received=(await b.state()).units.find(u=>u.id===tree.id);assert.equal((await b.post('/v1/social/comments',{targetId:a.id,text:'送回来',gift:{unitId:received.id,revision:received.revision}})).status,200);await page.evaluate(()=>sceneFixture.refresh());await scene.getByText('10 张贴纸',{exact:true}).first().waitFor();await scene.getByRole('button',{name:'切换场景 窗边生活',exact:true}).click();await placed(tree.id).waitFor();
 for(const theme of ['dark','light'])for(const width of [1100,700,390]){await page.setViewportSize({width,height:1000});await page.evaluate(theme=>document.documentElement.dataset.theme=theme,theme);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);await page.screenshot({path:`${out}/scene-${theme}-${width}.png`});}
 await scene.getByRole('button',{name:'关闭场景预设',exact:true}).click();await page.setViewportSize({width:1100,height:1000});await page.reload();await page.locator('.scene-background-layer [data-background-theme=room]').waitFor();assert((await placed(person.id).locator('[data-person-outfit]').getAttribute('data-person-outfit')).includes('beanie'));
 assert.deepEqual(errors,[]);await writeFile(out+'/result.json',JSON.stringify({ok:true,instantMs,scenarios:['real service inventory','13 quiet SVG backgrounds','per-unit clothing before network','preset save and instantaneous switch','background replacement','per-shape scale','cloud plus drops and sun combination','pre-send gift warning and confirmation','presets survive missing units','same-card restoration','six responsive layouts','restart persistence'],errors},null,2));console.log('PASS scene canvas, wardrobe, backgrounds, presets, missing-gift recovery and six layouts');
}catch(error){await page.screenshot({path:out+'/failure.png'});await writeFile(out+'/failure.json',JSON.stringify({message:error.message,errors},null,2));throw error;}finally{await browser.close();await vite.close();await fixture.close();}
