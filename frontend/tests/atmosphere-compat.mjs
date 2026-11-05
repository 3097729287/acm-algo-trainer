import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const out='../.backups/atmosphere-20261105/inventory-checks';await mkdir(out,{recursive:true});
const server=await createServer({server:{host:'127.0.0.1',port:0,watch:null}});await server.listen();
const browser=await chromium.launch({channel:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];page.on('pageerror',error=>errors.push(error.message));
try{
 await page.goto(server.resolvedUrls.local[0]+'tests/atmosphere-compat-fixture.html');await page.locator('.scene-background-layer [data-background-theme=room]').waitFor();
 await page.getByRole('button',{name:'打开窗户',exact:true}).click();await page.getByRole('button',{name:'关闭窗户',exact:true}).waitFor();
 assert.equal(await page.evaluate(()=>atmosphereFixture.writes.length),0,'Cosmetic interactions do not change inventory');
 await page.getByRole('button',{name:'贴纸',exact:true}).click();assert.equal(await page.getByRole('button',{name:'关闭窗户',exact:true}).count(),0,'Editing leaves the blank canvas available');
 await page.getByRole('region',{name:'贴纸区域',exact:true}).click({position:{x:250,y:260}});await page.getByRole('button',{name:'背景',exact:true}).click();
 const picker=page.getByRole('dialog',{name:'选择背景',exact:true});assert.equal(await picker.locator('.sticker-choice').count(),13,'52 old rarity aliases become 13 owned theme choices');
 assert.equal(await picker.getByRole('button',{name:'传说 background-room，库存 4',exact:true}).count(),1,'Four owned copies remain owned');
 await picker.getByRole('button',{name:'普通 background-coast，库存 4',exact:true}).click();await page.locator('.scene-background-layer [data-background-theme=coast]').waitFor();
 assert.equal(await page.evaluate(()=>atmosphereFixture.raw.units.length),52);assert.equal(await page.evaluate(()=>atmosphereFixture.raw.units.filter(unit=>unit.placement).length),1);assert.equal(await page.evaluate(()=>atmosphereFixture.writes.length),1);
 assert(!await page.evaluate(()=>atmosphereFixture.raw.units.some(unit=>unit.stickerId.includes('galaxy'))),'No cosmetic preview invents an owned reward');
 await page.screenshot({path:out+'/legacy-background-applied.png'});assert.deepEqual(errors,[]);
 const result={ok:true,legacyOwnedUnits:52,visibleOwnedThemes:13,copiesPreserved:true,windowClickable:true,editCanvasClickable:true,onePlacementWrite:true,noInventedReward:true,errors};await writeFile(out+'/result.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));
}catch(error){await page.screenshot({path:out+'/failure.png'});throw error;}finally{await browser.close();await server.close();}
