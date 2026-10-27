import assert from 'node:assert/strict';import fs from 'node:fs';import {createServer} from 'vite';import {chromium} from 'playwright';
import {difficultyPresentation} from '../src/lib/difficultyPresentation.js';
for(const row of [{difficulty:900,difficultyEstimated:true},{difficulty:1200,platform:'AtCoder'},{difficulty:1700,platform:'Codeforces',difficultySource:'官方 rating'},{difficulty:900,platform:'洛谷',source:'luogu-training',nativeDifficultyLabel:'入门'}]){
 assert.match(difficultyPresentation(row).label,/^\d+$/);assert.doesNotMatch(difficultyPresentation(row,'text').label,/\d|·/);
}
assert.equal(difficultyPresentation({difficulty:null}).label,'—');assert.equal(difficultyPresentation({difficulty:1200,difficultyHidden:true},'text').label,'—');
const out='../.backups/local-1421/ui';fs.mkdirSync(out,{recursive:true});
const vite=await createServer({server:{host:'127.0.0.1',port:0,fs:{allow:[process.cwd(),fs.realpathSync('node_modules')]}}});await vite.listen();
const browser=await chromium.launch({channel:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/revision-1420.html`);await page.getByRole('button',{name:'新建题单',exact:true}).waitFor();
 await page.evaluate(()=>fixture.screen('difficulty'));
 const labels=()=>page.getByTestId('difficulty-preview').locator('.difficulty').allTextContents();assert.deepEqual(await labels(),['900','1200']);
 const choose=async name=>{await page.getByRole('combobox',{name:'难度显示',exact:true}).click();await page.getByRole('listbox',{name:'难度显示',exact:true}).getByRole('option',{name,exact:true}).click();};
 await choose('文字');assert.deepEqual(await labels(),['入门','基础']);
 await page.reload();await page.getByRole('button',{name:'新建题单',exact:true}).waitFor();await page.evaluate(()=>fixture.screen('difficulty'));assert.deepEqual(await labels(),['入门','基础']);
 await choose('数字');assert.deepEqual(await labels(),['900','1200']);await page.screenshot({path:out+'/difficulty-number.png'});
 await page.evaluate(()=>fixture.add(['p0']));await page.getByRole('dialog',{name:'加入题单',exact:true}).waitFor();await page.mouse.click(5,5);await page.getByRole('dialog',{name:'加入题单',exact:true}).waitFor({state:'detached'});
 await page.evaluate(()=>fixture.screen('activity'));await page.getByRole('gridcell').first().waitFor();
 assert.equal(await page.locator('.activity-selected-summary [role="meter"]').getAttribute('aria-valuemax'),'10');
 assert.equal(await page.locator('.activity-selected-summary .activity-progress-segment').count(),5);
 assert.deepEqual(await page.locator('.activity-month-marker').allTextContents(),['+14','+9','+6','+3']);
 assert(await page.locator('.activity-day:not([data-band="0"])').evaluateAll(nodes=>nodes.every(node=>getComputedStyle(node).borderTopWidth==='0px')));
 for(const accent of ['#9d8df1','#6fa5e8','#5bbda4','#d7a45e']){
  await page.evaluate(color=>document.documentElement.style.setProperty('--accent',color),accent);
  assert.equal(await page.locator('.activity-day[data-shade="1"]').first().evaluate(node=>getComputedStyle(node).getPropertyValue('--activity-strength').trim()),'48%');
 }
 await page.screenshot({path:out+'/calendar-brighter.png'});assert.deepEqual(errors,[]);console.log('PASS 1.4.21: numeric default, exclusive text choice, saved selection, 10-problem/5-level brighter borderless calendar.');
}finally{await browser.close();await vite.close();}
