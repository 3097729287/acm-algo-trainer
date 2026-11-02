import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';

process.env.TB_OFFLINE='1';
const out='../.backups/learning-browser/ui';await mkdir(out,{recursive:true});
const server=await createServer({cacheDir:'../.backups/learning-browser/vite',server:{host:'127.0.0.1',port:0}});await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[];
page.on('pageerror',issue=>errors.push(issue.message));page.setDefaultTimeout(15000);
const open=tab=>page.evaluate(tab=>window.studyFixture.open(tab),tab);
const state=()=>page.evaluate(()=>window.studyFixture.state());
const pane=kind=>page.locator('.study-'+kind+':not([hidden])');
const search=async query=>{await page.getByRole('button',{name:'新建学习标签页',exact:true}).click();await page.getByRole('combobox',{name:'搜索学习内容'}).fill(query);};
const result=(source,title)=>page.getByRole('option').filter({has:page.locator('small',{hasText:source})}).filter({hasText:title});
try{
 await page.goto(server.resolvedUrls.local[0]+'tests/learning-browser-fixture.html');
 await page.getByRole('button',{name:'实验室入口',exact:true}).click();
 await pane('lab').getByRole('textbox',{name:'排序实验数组'}).waitFor();
 assert.equal(await page.locator('.app-shell').evaluate(node=>node.inert),true);
 assert.deepEqual(await page.locator('.study-browser').evaluate(node=>{const r=node.getBoundingClientRect();return [r.x,r.y,r.width,r.height];}),[0,0,1600,1000]);
 const sorting=pane('lab').locator('.sorting-experiment');
 await sorting.getByLabel('排序实验数组').fill('9 3 9 1');await sorting.getByRole('button',{name:'应用',exact:true}).click();
 await sorting.getByRole('button',{name:'下一步',exact:true}).click();await sorting.getByRole('button',{name:'下一步',exact:true}).click();
 const step=await sorting.locator('nav[aria-label="实验步骤"]').innerText();
 await search('并查集');await result('维基百科','并查集').waitFor();
 assert(await result('模板','并查集').count()>0);assert(await result('实验室','并查集').count()>0);assert(await result('题目','小月的数组').count()>0);assert(await result('题解','小月的数组').count()>0);
 const searchRect=await page.getByRole('combobox',{name:'搜索学习内容'}).boundingBox();assert(searchRect.y<44);
 await result('维基百科','并查集').click();await pane('wiki').frameLocator('iframe.wiki-reader').getByRole('heading',{name:'并查集',exact:true}).waitFor();
 await open({kind:'wiki',id:'ds/dsu',title:'并查集'});assert.equal((await state()).tabs.length,2);
 await page.getByRole('button',{name:'左右分屏',exact:true}).click();assert.equal((await state()).left,'lab:sorting-basics');assert.equal((await state()).right,'wiki:ds/dsu');
 assert.equal(await sorting.getByLabel('排序实验数组').inputValue(),'9 3 9 1');assert.equal(await sorting.locator('nav[aria-label="实验步骤"]').innerText(),step);
 const divider=page.getByRole('separator',{name:'调整左右分屏宽度'});await divider.focus();await divider.press('ArrowRight');assert.equal((await state()).ratio,52);
 await page.getByRole('button',{name:'退出分屏',exact:true}).click();
 await search('模板');await page.waitForFunction(()=>[...document.querySelectorAll('.study-result small')].every(node=>node.textContent==='模板'));
 assert(await page.getByRole('option').count()>10);
 await result('模板','并查集').first().click();await pane('template').getByRole('region',{name:'模板讲解'}).waitFor();
 // Exercise the actual HTML drag lifecycle and the right-edge drop preview.
 const dragged=page.getByRole('tab').filter({hasText:'并查集'}).last();
 const transfer=await page.evaluateHandle(()=>new DataTransfer());
 await dragged.dispatchEvent('dragstart',{dataTransfer:transfer});
 await page.locator('.study-browser').dispatchEvent('dragover',{dataTransfer:transfer,clientX:1595,clientY:300});
 await page.locator('.study-drop-preview').waitFor();
 await page.locator('.study-browser').dispatchEvent('drop',{dataTransfer:transfer,clientX:1595,clientY:300});
 assert.equal((await state()).left,null);assert((await state()).right.startsWith('template:'));
 await page.getByRole('button',{name:'退出分屏',exact:true}).click();
 await page.getByRole('button',{name:'左右分屏',exact:true}).click();
 assert.equal((await state()).left,null);assert.equal(await page.getByLabel('选择左侧标签页').getByRole('button').count(),2);
 await page.getByLabel('选择左侧标签页').getByRole('button',{name:/排序基础/}).click();
 await sorting.getByLabel('排序实验数组').waitFor();
 await page.reload();await sorting.getByLabel('排序实验数组').waitFor();assert.equal(await sorting.getByLabel('排序实验数组').inputValue(),'9 3 9 1');assert.equal(await sorting.locator('nav[aria-label="实验步骤"]').innerText(),step);
 assert.equal((await state()).left,'lab:sorting-basics');assert((await state()).right.startsWith('template:'));
 // Both panes keep independent keyboard focus; a chapter key affects one lab.
 const lab=pane('lab');await lab.locator('.lab-lesson').focus();const before=await lab.locator('.lab-position').innerText();await page.keyboard.press('ArrowRight');assert.notEqual(await lab.locator('.lab-position').innerText(),before);
 await page.keyboard.press('ArrowLeft');assert.equal(await sorting.getByLabel('排序实验数组').inputValue(),'9 3 9 1');
 await page.getByRole('button',{name:'退出分屏',exact:true}).click();
 await open({kind:'problem',id:'fixture:A',title:'小月的数组'});const editor=pane('problem').locator('.cm-content');await editor.waitFor();await editor.fill('#include <bits/stdc++.h>\nint main(){return 42;}');
 await page.waitForFunction(()=>window.studyFixture.calls.some(call=>call.path==='draft'&&call.body.code.includes('return 42')));
 await open({kind:'wiki',id:'ds/dsu',title:'并查集'});await page.getByRole('tab',{name:'小月的数组',exact:true}).click();assert.match(await editor.innerText(),/return 42/);
 await pane('problem').getByLabel('题面内容').evaluate(node=>{node.scrollTop=700;});
 await page.waitForFunction(()=>window.studyFixture.state().tabs.find(tab=>tab.kind==='problem').scroll.some(item=>item[0].startsWith('.wb-statement')&&item[1]>600));
 await page.reload();await editor.waitFor();assert.match(await editor.innerText(),/return 42/);await page.waitForFunction(()=>document.querySelector('.study-problem:not([hidden]) .wb-statement')?.scrollTop>600);
 // Closing the native application waits for both drafts and navigation.
 assert.equal(await page.evaluate(async()=>{const pending=[];window.dispatchEvent(new CustomEvent('tb-before-update',{detail:{waitUntil:promise=>pending.push(promise)}}));return (await Promise.all(pending)).every(value=>value!==false);}),true);
 for(const theme of ['dark','light'])for(const width of [1600,1024,800]){
  await page.setViewportSize({width,height:900});await page.evaluate(theme=>document.documentElement.dataset.theme=theme,theme);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
  const metrics=await page.locator('.study-bar').boundingBox();assert.equal(metrics.height,44);
  await page.screenshot({path:`${out}/browser-${theme}-${width}.png`});
 }
 await page.setViewportSize({width:1600,height:1000});
 await page.evaluate(()=>window.studyFixture.account('fixture-B'));await page.waitForFunction(()=>!document.querySelector('.study-browser'));assert.equal((await state()).tabs.length,0);
 await page.getByRole('button',{name:'实验室入口',exact:true}).click();assert.equal((await state()).tabs.length,1);
 await page.evaluate(()=>window.studyFixture.account('fixture-A'));await editor.waitFor();assert((await state()).tabs.length>=4);assert.match(await editor.innerText(),/return 42/);
 await search('模板 并查集');await result('模板','并查集').first().click();
 await pane('template').getByRole('button',{name:'另存为我的模板',exact:true}).click();
 await pane('template').getByRole('textbox',{name:'模板名称',exact:true}).fill('我的并查集草稿');
 await pane('template').getByRole('button',{name:'保存模板',exact:true}).click();
 await page.getByRole('tab',{name:'我的并查集草稿',exact:true}).waitFor();
 const savedTemplate=(await state()).tabs.find(tab=>tab.title==='我的并查集草稿'),savedCount=(await state()).tabs.length;
 assert(savedTemplate.id.startsWith('own:'));
 await open({kind:'template',id:savedTemplate.id,title:'我的并查集草稿'});assert.equal((await state()).tabs.length,savedCount);
 await page.reload();await pane('template').getByRole('textbox',{name:'模板名称',exact:true}).waitFor();
 assert.equal(await pane('template').getByRole('textbox',{name:'模板名称',exact:true}).inputValue(),'我的并查集草稿');
 await search('不存在的学习内容');await page.getByText('没有匹配的内容',{exact:true}).waitFor();await page.getByRole('combobox',{name:'搜索学习内容'}).press('Escape');assert.equal(await page.getByRole('combobox',{name:'搜索学习内容'}).count(),0);
 await page.getByRole('button',{name:'返回列表',exact:true}).click();assert.equal(await page.locator('.app-shell').evaluate(node=>node.inert),false);
 assert.deepEqual(errors,[]);await writeFile(`${out}/result.json`,JSON.stringify({passed:true,errors,scenarios:['cross-source search','source-only search','duplicate tabs','two-tab split','left chooser','split resize','experiment and draft preservation','reload and scroll restoration','native close flush','account isolation','themes and widths']},null,2));
 console.log('Learning browser UI passed: search, duplicate tabs, split/chooser/resize, live state, restart, drafts, scroll, native-close flush, account isolation and six layouts.');
}catch(issue){await page.screenshot({path:`${out}/failure.png`});await writeFile(`${out}/failure.json`,JSON.stringify({message:issue.message,errors,state:await state().catch(()=>null)},null,2));throw issue;}
finally{await browser.close();await server.close();}
