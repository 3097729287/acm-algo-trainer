import assert from 'node:assert/strict';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {mkdir} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const output=path.resolve(root,'../.backups/interaction-1433/reward-visuals');
const vite=await createServer({root,server:{host:'127.0.0.1',port:0}});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1280,height:900}}),errors=[];
page.on('pageerror',error=>errors.push(error.message));
try {
 await mkdir(output,{recursive:true});
 await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/achievement-layout.html`);
 await page.locator('[data-achievement-id="morning"]').waitFor();
 assert.equal(await page.getByText('已发放',{exact:false}).count(),0);
 assert.equal(await page.locator('.progress-achievement').getByText('已达成',{exact:false}).count(),0);
 for(const width of [1280,740,420]){
  await page.setViewportSize({width,height:900});
  const rows=await page.locator('.progress-achievement-name:has(time)').evaluateAll(nodes=>nodes.map(node=>{const name=node.children[0].getBoundingClientRect(),time=node.children[1].getBoundingClientRect();return {name:name.toJSON(),time:time.toJSON()};}));
  assert(rows.every(({name,time})=>name.right<=time.left&&Math.abs(name.bottom-time.bottom)<7),JSON.stringify(rows));
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 }
 await page.setViewportSize({width:1280,height:900});
 for(const period of ['daily','weekly','total']){
  const medals=page.locator(`[data-period="${period}"] .ranking-medal`);
  assert.equal(await medals.count(),6);
  for(const days of [1,2,3,8,9,30])assert.match(await page.locator(`[data-period="${period}"] .ranking-medal[data-days="${days}"]`).getAttribute('aria-label'),new RegExp(`连续第一 ${days} 天`));
  assert.equal(await page.locator(`[data-period="${period}"] [data-days="9"] .ranking-dominance text`).textContent(),'9');
 }
 await page.screenshot({path:path.join(output,'light.png')});
 await page.evaluate(()=>rewardFixture.setTheme('dark'));await page.waitForTimeout(300);
 await page.screenshot({path:path.join(output,'dark.png')});
 const claim=page.getByRole('button',{name:'领取晨光第一行奖励',exact:true});
 await claim.dblclick({delay:10});
 await page.waitForFunction(()=>rewardFixture.claims===1);
 await claim.waitFor({state:'detached'});
 assert.equal(await page.locator('[data-achievement-id="morning"] time').count(),1);
 assert.deepEqual(errors,[]);
 console.log('Achievements: title/date alignment, responsive layout, one manual claim, no paid-status row, three dominance medal series passed.');
} finally {await browser.close();await vite.close();}
