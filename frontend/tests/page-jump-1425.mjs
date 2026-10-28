import assert from 'node:assert/strict';
import fs from 'node:fs';
import {chromium} from 'playwright';
const work='../.backups/local-1425',endpoint=process.env.TB_TEST_URL||`http://127.0.0.1:${JSON.parse(fs.readFileSync(work+'/ui-port.json','utf8')).port}`;
fs.mkdirSync(work+'/ui',{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];
page.on('pageerror',e=>errors.push(e.message));
const nav=name=>page.getByRole('navigation',{name:'主导航'}).getByRole('button',{name,exact:true});
const waitValue=async(input,value)=>page.waitForFunction(({label,value})=>document.querySelector(`[aria-label="${label}"]`)?.value===value,{label:await input.getAttribute('aria-label'),value:String(value)});
try {
 await page.goto(endpoint);await nav('题库').click();
 const footer=page.getByRole('navigation',{name:'题库分页',exact:true}),jump=footer.getByRole('textbox',{name:'跳转页码',exact:true});
 await jump.waitFor();await page.waitForFunction(()=>!document.querySelector('.pagination-page-input').disabled);
 const first=await page.locator('tbody tr[data-id]').first().getAttribute('data-id');
 await jump.fill('400');await jump.press('Enter');await waitValue(jump,400);
 assert.notEqual(await page.locator('tbody tr[data-id]').first().getAttribute('data-id'),first);
 await footer.getByRole('button',{name:'题库下一页',exact:true}).click();await waitValue(jump,401);
 await footer.getByRole('button',{name:'题库上一页',exact:true}).click();await waitValue(jump,400);
 await jump.fill('23');await jump.press('Escape');await waitValue(jump,400);assert(await footer.isVisible());
 await jump.fill('');await jump.press('Enter');await waitValue(jump,400);
 await jump.fill('0');await jump.press('Enter');await waitValue(jump,1);assert.equal(await footer.getByRole('button',{name:'题库上一页',exact:true}).isEnabled(),false);
 await jump.fill('9999999999');await jump.press('Enter');await page.waitForTimeout(80);
 let pages=Number((await footer.locator('.pagination-position').innerText()).match(/\/\s*(\d+)/)[1]);await waitValue(jump,pages);assert.equal(await footer.getByRole('button',{name:'题库下一页',exact:true}).isEnabled(),false);
 const before=await page.locator('tbody tr[data-id]').first().getAttribute('data-id');
 await jump.focus();await jump.press('ArrowLeft');await jump.press('ArrowRight');assert.equal(await page.locator('tbody tr[data-id]').first().getAttribute('data-id'),before,'editing arrows must not flip pages');
 await jump.fill('1e2');assert.equal(await jump.inputValue(),String(pages),'non-digit paste must not become a different page');
 await jump.fill('5');await jump.dispatchEvent('keydown',{key:'Enter',code:'Enter',isComposing:true});assert.equal(await page.locator('tbody tr[data-id]').first().getAttribute('data-id'),before);
 await jump.press('Enter');await waitValue(jump,5);
 const search=page.getByRole('textbox',{name:'搜索题目',exact:true});await search.fill('Polyline');await page.waitForTimeout(450);await waitValue(jump,1);assert.equal(await page.locator('tbody tr[data-id]').count(),1);assert(await jump.isDisabled());
 await search.fill('');await page.waitForTimeout(450);
 for(const [theme,width] of [['dark',1440],['light',800],['dark',640]]){
  await page.setViewportSize({width,height:800});await page.evaluate(v=>document.documentElement.dataset.theme=v,theme);await page.waitForTimeout(100);
  await jump.fill('9999999999');await jump.press('Enter');await page.waitForTimeout(80);
  const visible=await footer.evaluate(n=>{const r=n.getBoundingClientRect(),i=n.querySelector('input').getBoundingClientRect();return i.left>=r.left&&i.right<=r.right&&r.right<=innerWidth&&document.documentElement.scrollWidth<=innerWidth+1;});assert(visible,`${theme}/${width} clipped footer`);
  await page.screenshot({path:`${work}/ui/page-jump-${theme}-${width}.png`});
 }
 await page.setViewportSize({width:1440,height:900});await page.evaluate(()=>document.documentElement.dataset.theme='dark');
 await nav('比赛').click();await page.getByRole('button',{name:'比赛文件夹浏览',exact:true}).click();
 const explorer=page.getByRole('region',{name:'比赛层级浏览'});
 await explorer.getByRole('button',{name:/^ACM/}).click();await explorer.getByRole('button',{name:/^CCPC/}).click();
 await explorer.getByRole('button',{name:/^2026年/}).click();
 await page.getByRole('button',{name:/查看 Codeforces CCPC 2026 黑龙江/}).waitFor();
 assert((await page.locator('.competition-card').allTextContents()).some(s=>s.includes('福建')));
 await page.screenshot({path:work+'/ui/ccpc-2026.png'});
 const titles=await page.locator('.competition-card-title strong').allTextContents();assert.equal(new Set(titles).size,titles.length);
 const crumb=page.getByRole('navigation',{name:'题目浏览路径'});await crumb.getByRole('button',{name:'ACM',exact:true}).click();
 await explorer.getByRole('button',{name:/^省赛/}).click();await explorer.getByRole('button',{name:/^2026年/}).click();
 assert((await page.locator('.competition-card').allTextContents()).some(s=>s.includes('贵州')));
 const directoryJump=page.getByRole('navigation',{name:'目录分页'}).getByRole('textbox',{name:'跳转页码'});
 await directoryJump.fill('2');await directoryJump.press('Enter');await waitValue(directoryJump,2);
 await page.getByRole('button',{name:/查看 Codeforces CCPC 2026 黑龙江/}).waitFor();
 await crumb.getByRole('button',{name:'ACM',exact:true}).click();await explorer.getByRole('button',{name:/^邀请赛/}).click();await explorer.getByRole('button',{name:/^2026年/}).click();
 await page.getByRole('button',{name:/查看 Codeforces CCPC 2026 福建/}).waitFor();
 assert.deepEqual(errors,[]);
 fs.writeFileSync(work+'/page-jump-ui.json',JSON.stringify({ok:true,realApi:true,inputJump:true,rangeClamp:true,cancelAndEmpty:true,compositionAndArrowGuard:true,filterReset:true,narrowLayouts:true,ccpc2026:true,province2026:true,invitational2026:true,duplicateCards:false},null,2));
 console.log('PASS real App: direct page jump/clamps/cancel/filter resize; keyboard and IME guards; three viewports/two themes; CCPC, provincial and invitational 2026 navigation.');
}catch(error){await page.screenshot({path:work+'/ui/failure.png'});throw error;}
finally{await browser.close();}
