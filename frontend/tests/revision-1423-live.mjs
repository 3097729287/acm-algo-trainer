// Disposable offline backend required: .backups/local-1423/start_ui.py.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {chromium} from 'playwright';
const endpoint=process.env.TB_TEST_URL||'http://127.0.0.1:7347',output='../.backups/local-1423/ui';
fs.mkdirSync(output,{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});
const context=await browser.newContext({viewport:{width:1440,height:900},permissions:['clipboard-read','clipboard-write']});
const page=await context.newPage(),errors=[],official=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('request',request=>{if(request.url().includes('/api/official/'))official.push(request.url());});
try {
 await page.goto(endpoint);await page.getByRole('navigation',{name:'主导航'}).waitFor();
 await page.getByRole('button',{name:'模板',exact:true}).click();
 const card=page.getByRole('region',{name:'并查集：路径压缩与按大小合并',exact:true});
 await card.waitFor();assert.equal(await page.locator('.template-catalog .catalog-card').count(),24);
 assert.equal(await page.locator('.template-catalog .catalog-card p').count(),0);
 assert.equal(await page.locator('.template-catalog .catalog-card .lucide-book-open').count(),0);
 const aligned=await card.locator('h3').evaluate(node=>{const icon=node.querySelector('svg').getBoundingClientRect(),title=node.querySelector('span').getBoundingClientRect();return Math.abs((icon.top+icon.bottom-title.top-title.bottom)/2)<4;});assert(aligned);
 await card.getByRole('button',{name:'复制模板 并查集：路径压缩与按大小合并',exact:true}).click();
 assert.equal(await page.locator('.template-detail').count(),0,'copy must not open the card');
 assert.match(await page.evaluate(()=>navigator.clipboard.readText()),/struct DSU/);
 await card.click({position:{x:20,y:20}});
 await page.getByRole('button',{name:'讲解版',exact:true}).waitFor();
 assert.equal(await page.locator('.sidebar').isVisible(),false);assert.equal(await page.locator('.topbar').isVisible(),false);assert.equal(await page.locator('.app-statusbar').isVisible(),false);
 assert(await page.locator('.template-code').evaluate(node=>node.getBoundingClientRect().width>innerWidth*.9));
 assert.match(await page.getByLabel('模板代码',{exact:true}).innerText(),/路径压缩|根/);
 await page.getByRole('button',{name:'讲解版',exact:true}).click();
 await page.getByRole('button',{name:'竞赛版',exact:true}).waitFor();
 const concise=await page.getByLabel('模板代码',{exact:true}).innerText();assert.match(concise,/vector<int> p, sz/);assert(!concise.includes('//'));
 await page.getByRole('button',{name:'复制模板',exact:true}).click();const copied=await page.evaluate(()=>navigator.clipboard.readText());assert(!copied.includes('//'));assert.match(copied,/int find\(int u\)/);
 for(const theme of ['dark','light']){await page.evaluate(v=>document.documentElement.dataset.theme=v,theme);await page.screenshot({path:`${output}/template-focus-${theme}.png`});}
 await page.getByRole('button',{name:'模板练习 1',exact:true}).click();
 await page.getByRole('textbox',{name:'C++ 代码',exact:true}).waitFor();
 await page.waitForFunction(()=>document.querySelector('.cm-content')?.getAttribute('contenteditable')==='true');
 const code=fs.readFileSync('../.backups/local-1423/drill-code-check/dsu-1.cpp','utf8');
 const editor=page.getByRole('textbox',{name:'C++ 代码',exact:true});await editor.focus();await page.keyboard.press('Control+A');await page.keyboard.insertText(code);
 await page.getByRole('button',{name:'提交',exact:true}).click();
 await page.getByText('模板题通过',{exact:true}).first().waitFor({timeout:45000});
 assert.equal(official.length,0,'template submit must not open the browser adapter');
 await page.screenshot({path:output+'/template-local-pass.png'});
 const response=await context.request.get(endpoint+'/api/workspace');const workspace=await response.json();
 assert.equal(workspace.summary.accepted||0,0,'template pass must not grant an official AC');
 await page.getByRole('button',{name:'返回列表',exact:true}).click();
 await page.getByRole('button',{name:'返回模板',exact:true}).click();assert.equal(await page.locator('.sidebar').isVisible(),true);
 await page.getByRole('button',{name:'算法实验室',exact:true}).click();
 await page.getByRole('button',{name:'打开算法 并查集',exact:true}).waitFor();
 assert.equal(await page.locator('.catalog-card p,.catalog-card .lab-course-meta').count(),0);
 await page.getByRole('button',{name:'打开算法 并查集',exact:true}).click();
 await page.getByRole('button',{name:'返回算法实验室',exact:true}).waitFor();
 await page.getByRole('button',{name:'返回算法实验室',exact:true}).click();
 assert.deepEqual(errors,[]);console.log('PASS real App: whole-card entry, independent copy, two editions, full template area, direct template judging, no official request, preserved navigation, unified lab cards.');
} catch(error) {await page.screenshot({path:output+'/debug-failure.png'});throw error;}
finally{await context.close();await browser.close();}
