import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {DatabaseSync} from 'node:sqlite';
import {createServer} from 'vite';
import {chromium} from 'playwright';
import {NAVIGATION_ORDER} from '../src/lib/navigationDefaults.js';

const wiki=new DatabaseSync('../backend/resources/oi-wiki.sqlite3',{readOnly:true});
const server=await createServer({cacheDir:'../.backups/next-150/vite-feedback-adaptation',server:{host:'127.0.0.1',port:0,watch:null},plugins:[{name:'isolated-feedback',configureServer(vite){vite.middlewares.use('/feedback',(req,res)=>{const u=new URL(req.url,'http://fixture'),id=u.searchParams.get('id');res.setHeader('Content-Type','application/json; charset=utf-8');res.end(JSON.stringify(id?{article:wiki.prepare('SELECT id,title,html,url FROM articles WHERE id=?').get(id)}:{articles:wiki.prepare('SELECT id,title,category,url FROM articles').all()}));});}}]});
await server.listen();const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:2048,height:1152}}),errors=[];page.on('pageerror',error=>errors.push(error.message));
const out='../.backups/next-150/feedback-adaptation-browser';await mkdir(out,{recursive:true});const results=[];
try{
 await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/tests/feedback-adaptation-fixture.html`);
 for(const width of [2048,960,430])for(const view of ['templates','lab','wiki']){
  await page.setViewportSize({width,height:1000});await page.getByRole('button',{name:view,exact:true}).click();await page.locator('.learning-catalogue-entry').first().waitFor();
  const geometry=await page.locator('.learning-catalogue').evaluate(node=>({columns:getComputedStyle(node).gridTemplateColumns.split(' ').length,entries:[...node.querySelectorAll('.learning-catalogue-entry')].map(button=>({height:button.getBoundingClientRect().height,border:getComputedStyle(button).borderTopWidth,radius:getComputedStyle(button).borderRadius,arrow:Boolean(button.querySelector('.lucide-chevron-right'))})),overflow:document.documentElement.scrollWidth>innerWidth}));
  assert(!geometry.overflow);assert(geometry.entries.every(item=>item.height>=43&&item.radius==='0px'&&item.border==='0px'&&item.arrow));if(width===2048)assert(geometry.columns>=5);
  results.push({width,view,...geometry});await page.screenshot({path:`${out}/${view}-${width}.png`});
 }
 await page.getByRole('button',{name:'navigation',exact:true}).click();const previous=await page.evaluate(()=>structuredClone(window.feedbackPrefs));await page.getByRole('button',{name:'重置板块顺序'}).click();
 const reset=await page.evaluate(()=>window.feedbackPrefs);assert.deepEqual(reset.navOrder,[...NAVIGATION_ORDER]);assert.deepEqual({...reset,navOrder:previous.navOrder},previous,'Only the relative order is reset');
 await page.getByRole('button',{name:'diagram',exact:true}).click();
 for(const theme of ['dark','light']){
  if(await page.evaluate(()=>document.documentElement.dataset.theme)!==theme)await page.getByRole('button',{name:'theme',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('img[alt="黑色线条"]')?.dataset.imageSurface==='paper');
  assert.equal(await page.locator('img[alt="白色线条"]').first().getAttribute('data-image-surface'),'ink');
  const frame=page.frameLocator('.wiki-reader');await frame.locator('img[data-image-surface=paper]').first().waitFor();
  assert(await frame.locator('img[data-image-surface=paper]').count()>0,'Actual bundled DSU diagrams remain legible');
  await page.screenshot({path:`${out}/diagrams-${theme}.png`});
 }
 for(const width of [960,430]){
  await page.setViewportSize({width,height:1000});await page.getByRole('button',{name:'rewards',exact:true}).click();await page.locator('.achievement-reward').first().waitFor();
  assert(await page.locator('.achievement-reward').evaluateAll(nodes=>nodes.every(node=>{const r=node.getBoundingClientRect(),card=node.closest('.progress-achievement').getBoundingClientRect();return r.left>=card.left-1&&r.right<=card.right+1&&node.scrollWidth<=node.clientWidth+1;})),'Sticker/badge and XP reward rows wrap within each card');
  await page.screenshot({path:`${out}/rewards-${width}.png`});
 }
 await page.getByRole('button',{name:'language',exact:true}).click();
 for(const value of ['cpp17','python3'])for(const large of [false,true]){
  if((await page.evaluate(()=>parseFloat(document.documentElement.style.fontSize)))===(large?18:26))await page.getByRole('button',{name:'font',exact:true}).click();
  const select=page.getByRole('combobox',{name:'编程语言'});await select.selectOption(value);await page.waitForTimeout(50);
  assert(await select.evaluate(node=>{const style=getComputedStyle(node),canvas=document.createElement('canvas'),context=canvas.getContext('2d');context.font=style.font;return node.clientWidth-parseFloat(style.paddingLeft)-parseFloat(style.paddingRight)>=context.measureText(node.selectedOptions[0].text).width;}),'The complete selected language fits, including Python3 at enlarged UI sizes');
 }
 assert.deepEqual(errors,[]);await writeFile(out+'/report.json',JSON.stringify({ok:true,results,diagramThemes:2,rewardWidths:2,languageCases:4,resetPreservesPreferences:true},null,2));
 console.log('PASS three shared list catalogues at 3 widths; navigation order reset; real Wiki diagram contrast in both themes; rewards wrap; complete language labels');
}finally{await browser.close();await server.close();wiki.close();}
