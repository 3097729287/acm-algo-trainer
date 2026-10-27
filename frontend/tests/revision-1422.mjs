import assert from 'node:assert/strict';import fs from 'node:fs';import {createServer} from 'vite';import {chromium} from 'playwright';
import {contestOptions,catalogSegments} from '../src/lib/contestCatalog.js';
const events=[{name:'CCPC 2025 哈尔滨区域赛',platform:'Codeforces',series:'XCPC',count:13,expectedCount:13},{name:'教育赛 193',platform:'Codeforces',series:'教育赛',count:6},{name:'AGC 070',platform:'AtCoder',series:'AGC',count:6}];
const options=contestOptions(events),acm=options.find(item=>item.label==='ACM');assert(acm.children.find(item=>item.label==='CCPC').children.some(item=>item.label==='2025年'));
assert(options.find(item=>item.label==='Codeforces').children.find(item=>item.label==='教育赛').children[0].label.includes('6 题'));
assert.equal(catalogSegments({labTopic:'并查集',platform:'Codeforces',name:'算法实验室 · 并查集'})[0],'算法实验室');
const output='../.backups/local-1422/ui';fs.mkdirSync(output,{recursive:true});
const vite=await createServer({server:{host:'127.0.0.1',port:0,fs:{allow:[process.cwd(),fs.realpathSync('node_modules')]}}});await vite.listen();
const browser=await chromium.launch({channel:'msedge',headless:true}),context=await browser.newContext({viewport:{width:1440,height:900},permissions:['clipboard-read','clipboard-write']}),page=await context.newPage(),errors=[];page.on('pageerror',error=>errors.push(error.message));
try{
 await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/revision-1422.html`);await page.getByText('差分默认',{exact:true}).waitFor();
 assert.equal(await page.getByRole('button',{name:'默认题解',exact:true}).count(),0);
 await page.getByRole('button',{name:'切换为详细题解'}).click();await page.getByText('差分详细',{exact:true}).waitFor();
 await page.evaluate(()=>fixture.method('binary'));await page.getByText('二分默认',{exact:true}).waitFor();
 await page.evaluate(()=>fixture.method('difference'));await page.getByText('差分详细',{exact:true}).waitFor();
 const body=page.getByLabel('题解正文',{exact:true});await body.evaluate(node=>{node.scrollTop=node.scrollHeight;});
 await page.getByRole('button',{name:'线段树入门',exact:true}).click();await page.getByLabel('从零讲正文',{exact:true}).waitFor();
 const lessonBody=page.getByLabel('从零讲正文',{exact:true});await lessonBody.evaluate(node=>{node.scrollTop=220;});
 await page.getByRole('button',{name:'双指针入门',exact:true}).evaluate(node=>node.click());await page.getByRole('button',{name:'枚举入门',exact:true}).waitFor();
 await page.getByRole('button',{name:'枚举入门',exact:true}).click();await page.getByRole('button',{name:'返回上一级',exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('.solution-reader-header strong').textContent==='双指针入门');
 await lessonBody.focus();await page.keyboard.press('Backspace');await page.waitForFunction(()=>document.querySelector('.solution-reader-header strong').textContent==='线段树入门');
 await page.waitForFunction(()=>document.querySelector('[aria-label="从零讲正文"]').scrollTop>=200);await page.getByRole('button',{name:'返回题解',exact:true}).click();await page.getByText('差分详细',{exact:true}).waitFor();
 await page.getByRole('button',{name:'标记已学会 线段树入门',exact:true}).click();assert.equal(await page.getByRole('button',{name:'线段树入门',exact:true}).count(),0);assert.deepEqual(await page.evaluate(()=>fixture.prefs().learnedLectures),['lesson-a']);
 assert(!/题解引用|展开讲解/.test(await page.locator('.solution-reader').innerText()));
 await page.evaluate(()=>fixture.screen('workbench'));await page.getByRole('button',{name:'题解1',exact:true}).waitFor();assert.equal(await page.locator('.wb-solution-button').count(),2);const colors=await page.locator('.wb-solution-button').evaluateAll(nodes=>nodes.map(node=>getComputedStyle(node).color));assert.notEqual(colors[0],colors[1]);
 await page.getByRole('button',{name:'打开模板',exact:true}).click();await page.getByRole('dialog',{name:'模板',exact:true}).waitFor();await page.getByRole('button',{name:'插入模板 并查集：路径压缩与按大小合并',exact:true}).click();await page.getByRole('dialog',{name:'模板',exact:true}).waitFor({state:'detached'});assert.match(await page.evaluate(()=>fixture.editorValue()),/struct DSU[\s\S]*int main/);
 await page.getByRole('button',{name:'打开模板',exact:true}).click();await page.keyboard.press('Escape');assert.equal(await page.getByRole('dialog',{name:'模板',exact:true}).count(),0);
 await page.evaluate(()=>fixture.screen('templates'));await page.getByRole('button',{name:'新建模板',exact:true}).click();await page.getByLabel('模板名称',{exact:true}).fill('自己的测试模板');await page.evaluate(()=>fixture.edit('int custom_answer = 42;\n'));await page.getByRole('button',{name:'保存模板',exact:true}).click();await page.waitForFunction(()=>fixture.calls.some(call=>call.path==='templates/save'));
 await page.getByRole('button',{name:'返回模板',exact:true}).click();await page.getByRole('button',{name:'打开模板 自己的测试模板',exact:true}).click();assert.equal(await page.evaluate(()=>fixture.templateValue()),'int custom_answer = 42;\n');
 for(const theme of ['dark','light']){await page.evaluate(value=>document.documentElement.dataset.theme=value,theme);await page.screenshot({path:`${output}/custom-template-${theme}.png`});}
 await page.evaluate(()=>fixture.screen('competition'));await page.locator('.competition-question-meta').waitFor();assert(await page.locator('.competition-question').first().evaluate(node=>node.querySelector('.competition-question-meta').getBoundingClientRect().left>node.querySelector('.competition-question-main').getBoundingClientRect().left+150));
 await page.evaluate(()=>fixture.screen('lectures'));await page.getByRole('button',{name:'从零讲全屏',exact:true}).click();await page.waitForFunction(()=>document.querySelector('.lecture-reading-full'));assert.equal(await page.locator('.lectures-list').isVisible(),false);await page.getByRole('button',{name:'从零讲：双指针',exact:true}).click();await page.getByRole('heading',{name:'双指针',exact:true}).waitFor();assert.equal(await page.locator('.lecture-reading-full').count(),1);await page.getByRole('button',{name:'返回上篇',exact:true}).click();assert.equal(await page.locator('.lecture-reading-full').count(),1);await page.getByRole('button',{name:'退出从零讲全屏',exact:true}).click();assert.equal(await page.locator('.lectures-list').isVisible(),true);
 assert.deepEqual(errors,[]);console.log('PASS: method selection/variants, nested reader/back/root/scroll, learned hiding, colored books, templates CRUD/editor insert, Escape and contest knowledge column.');
}catch(error){await page.screenshot({path:output+'/debug-failure.png'});throw error;}finally{await context.close();await browser.close();await vite.close();}
