import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const out='../.backups/atmosphere-20261105/inventory-checks';await mkdir(out,{recursive:true});
const server=await createServer({server:{host:'127.0.0.1',port:0,watch:null}});await server.listen();
const browser=await chromium.launch({channel:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];page.on('pageerror',error=>errors.push(error.message));
try{
 await page.goto(server.resolvedUrls.local[0]+'tests/atmosphere-compat-fixture.html');await page.locator('.workspace-background-layer[data-background-id=room]').waitFor();
 assert.equal(await page.locator('.scene-background-layer').count(),0,'The growth canvas no longer owns a background');
 assert.equal(await page.evaluate(()=>atmosphereFixture.writes.length),0);
 await page.getByRole('button',{name:'背景选择',exact:true}).click();
 const picker=page.getByRole('dialog',{name:'背景选择',exact:true});await picker.locator('.background-choice').first().waitFor();assert.equal(await picker.locator('.background-choice').count(),13,'Old rarity aliases become unique owned choices');
 assert.equal(await picker.getByRole('button',{name:'使用背景 窗边小屋',exact:true}).locator('em').textContent(),'4');
 await picker.getByRole('button',{name:'使用背景 海边远眺',exact:true}).click();await page.locator('.workspace-background-layer[data-background-id=coast]').waitFor();
 assert.equal(await page.evaluate(()=>atmosphereFixture.raw.units.length),52);assert.equal(await page.evaluate(()=>atmosphereFixture.raw.units.filter(unit=>unit.placement).length),1);assert.equal(await page.evaluate(()=>atmosphereFixture.writes.length),0);
 assert(!await page.evaluate(()=>atmosphereFixture.raw.units.some(unit=>unit.stickerId.includes('galaxy'))));
 await page.getByRole('button',{name:'背景选择',exact:true}).click();const images=page.getByRole('dialog',{name:'背景选择',exact:true});await images.getByRole('button',{name:'我的背景',exact:true}).click();await images.getByRole('button',{name:'使用背景 原有背景',exact:true}).waitFor();assert.equal(await page.evaluate(()=>localStorage.getItem('tb.appearance.background')),null);await images.getByRole('button',{name:'使用背景 原有背景',exact:true}).click();await page.locator('.workspace-background-layer[data-background-source=image]').waitFor();
 await page.screenshot({path:out+'/legacy-background-applied.png'});assert.deepEqual(errors,[]);
 const result={ok:true,legacyOwnedUnits:52,visibleOwnedThemes:13,copiesPreserved:true,globalSelection:true,legacyImageSelectable:true,inventoryWrites:0,noInventedReward:true,errors};await writeFile(out+'/result.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));
}catch(error){await page.screenshot({path:out+'/failure.png'});throw error;}finally{await browser.close();await server.close();}
