import assert from 'node:assert/strict';
import {readFile,mkdir} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';
import {templateForDisplay} from '../src/lib/insertTemplate.js';
const templates=JSON.parse(await readFile('../backend/resources/code-templates.json','utf8')).templates.map(templateForDisplay);
const vite=await createServer({server:{host:'127.0.0.1',port:0}});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const context=await browser.newContext({viewport:{width:1440,height:900},permissions:['clipboard-read','clipboard-write']});
const page=await context.newPage(),errors=[];page.on('pageerror',error=>errors.push(error.message));
const output='tests/screenshots/unified-controls';await mkdir(output,{recursive:true});
try{
 await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/revision-1422.html`);
 await page.evaluate(()=>fixture.screen('templates'));
 const openTemplate=async item=>{await page.getByRole('button',{name:`打开模板 ${item.title}`,exact:true}).click();await page.locator('.template-code .cm-content').waitFor();};
 const toggle=page.locator('.template-edition-toggle');
 const item=templates.find(item=>item.id==='dsu')||templates.find(item=>item.contestCode&&item.code!==item.contestCode);
 assert(item,'a real builtin has independently provided teaching/contest bodies');await openTemplate(item);
 assert.equal(await toggle.count(),1);assert.equal(await toggle.innerText(),'讲解版');
 assert.equal(await page.evaluate(()=>fixture.templateValue()),item.code);
 await toggle.click();assert.equal(await toggle.innerText(),'竞赛版');assert.equal(await page.evaluate(()=>fixture.templateValue()),item.contestCode);
 await page.getByRole('button',{name:'复制模板',exact:true}).click();assert.equal((await page.evaluate(()=>navigator.clipboard.readText())).replaceAll('\r\n','\n'),item.contestCode);
 await toggle.focus();await toggle.press('Enter');assert.equal(await toggle.innerText(),'讲解版');assert.equal(await page.evaluate(()=>fixture.templateValue()),item.code);
 await page.getByRole('button',{name:'复制模板',exact:true}).click();assert.equal((await page.evaluate(()=>navigator.clipboard.readText())).replaceAll('\r\n','\n'),item.code);
 await page.getByRole('button',{name:'返回模板',exact:true}).click();await openTemplate(item);
 assert.equal(await toggle.innerText(),'讲解版','new entry defaults to the teaching version');
 let geometryCases=0;
 for(const width of [2048,1294,960,430])for(const theme of ['dark','light']){
   await page.setViewportSize({width,height:900});await page.evaluate(theme=>{document.documentElement.dataset.theme=theme;document.documentElement.style.setProperty('--ui-font-size','22px');},theme);
   for(const expected of ['讲解版','竞赛版']){
     if(await toggle.innerText()!==expected)await toggle.click();
     assert.equal(await page.evaluate(()=>fixture.templateValue()),expected==='讲解版'?item.code:item.contestCode);
     const metrics=await page.locator('.template-heading').evaluate(node=>{const parent=node.getBoundingClientRect(),button=node.querySelector('.template-edition-toggle').getBoundingClientRect();return {height:parent.height,buttonHeight:button.height,left:button.left,right:button.right,width:innerWidth,overflow:document.documentElement.scrollWidth-innerWidth};});
     assert(metrics.buttonHeight>=30&&metrics.left>=0&&metrics.right<=metrics.width&&metrics.overflow<=1,JSON.stringify({width,theme,expected,...metrics}));
   }
   await page.screenshot({path:`${output}/template-${width}-${theme}.png`});geometryCases++;
 }
 await page.setViewportSize({width:1440,height:900});await page.evaluate(()=>fixture.screen('lectures'));
 const back=page.getByRole('button',{name:'返回上篇',exact:true}),train=page.getByRole('button',{name:'练习来源题',exact:true});
 await train.waitFor();assert.equal(await train.innerText(),'');assert.equal(await train.locator('.lucide-external-link').count(),1);assert.equal(await train.getAttribute('title'),'练习来源题');
 assert.equal(await back.innerText(),'');assert.equal(await back.isDisabled(),true);
 await train.click();assert.equal(await page.evaluate(()=>fixture.trained),'p1');
 await page.getByRole('button',{name:'从零讲：双指针',exact:true}).click();await page.getByRole('heading',{name:'双指针',exact:true}).waitFor();
 assert.equal(await back.isDisabled(),false);await back.click();await train.waitFor();
 assert.equal(await back.isDisabled(),true,'icon-only return preserves real history navigation');
 for(const width of [2048,1294,960,430]){
   await page.setViewportSize({width,height:900});await train.waitFor();
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   const sizes=await page.locator('.lectures-detail-bar>.icon-button').evaluateAll(nodes=>nodes.map(n=>n.getBoundingClientRect().height));assert(sizes.every(height=>height===34),JSON.stringify({width,sizes}));
 }
 assert.deepEqual(errors,[]);console.log(JSON.stringify({ok:true,templateEditions:2,geometryCases,iconOnlyLectureActions:true,actualSourceTraining:true,historyReturn:true}));
}finally{await context.close();await browser.close();await vite.close();}
