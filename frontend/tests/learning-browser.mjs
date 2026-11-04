import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';

process.env.TB_OFFLINE='1';
const out='../.backups/next-152/browser-ui';await mkdir(out,{recursive:true});
const server=await createServer({cacheDir:'../.backups/next-152/browser-vite',server:{host:'127.0.0.1',port:0}});await server.listen();
const browser=await chromium.launchPersistentContext(out+'/profile-'+Date.now(),{channel:process.env.CI?undefined:'msedge',headless:true,viewport:{width:1600,height:1000}}),page=browser.pages()[0],errors=[];
page.on('pageerror',issue=>errors.push(issue.message));page.setDefaultTimeout(15000);
const open=tab=>page.evaluate(tab=>window.studyFixture.open({...tab,newTab:true}),tab);
const state=()=>page.evaluate(()=>window.studyFixture.state());
const pane=kind=>page.locator('.study-'+kind+':not([hidden])');
const search=async query=>{await page.getByRole('button',{name:'新建学习标签页',exact:true}).last().click();await page.getByRole('combobox',{name:'搜索学习内容'}).fill(query);};
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
 // Single content uses its original toolbar; + alone reveals the browser row.
 assert.equal(await page.locator('.study-group-header').count(),0);
 assert.equal((await pane('lab').boundingBox()).y,0);
 const controls=await page.locator('.study-single-controls').boundingBox();assert.equal(controls.y,0);assert.equal(controls.height,44);
 await search('');await page.waitForFunction(()=>document.querySelectorAll('.study-folder').length===5);
 await page.getByRole('button',{name:'关闭搜索',exact:true}).click();
 assert.equal(await page.locator('.study-group-header').count(),0,'Closing an unused search restores the compact single-content header');
 assert.equal((await pane('lab').boundingBox()).y,0);assert.equal(await sorting.locator('nav[aria-label="实验步骤"]').innerText(),step);
 await search('');await page.waitForFunction(()=>document.querySelectorAll('.study-folder').length===5);
 assert.deepEqual(await page.getByRole('option').locator('span').allTextContents(),['题目','维基百科','模板','实验室','从零讲']);
 const searchRect=await page.locator('.study-search-box').boundingBox();assert.equal(searchRect.height,32);assert(searchRect.width<=280);assert(Math.abs(searchRect.y-6)<=.5);
 await page.getByRole('combobox').fill('并查集');await page.getByRole('option').filter({hasText:'维基百科'}).click();
 await result('维基百科','并查集').click();await pane('wiki').frameLocator('iframe.wiki-reader').getByRole('heading',{name:'并查集',exact:true}).waitFor();
 await open({kind:'wiki',id:'ds/dsu',title:'并查集'});assert.equal((await state()).tabs.length,2);
 const transfer=await page.evaluateHandle(()=>new DataTransfer());
 const dragTo=async(key,target,x,y)=>{
  await page.locator(`[data-tab-key="${key}"] [role=tab]`).dispatchEvent('dragstart',{dataTransfer:transfer});
  await target.dispatchEvent('dragover',{dataTransfer:transfer,clientX:x,clientY:y});await page.locator('.study-drop-preview').waitFor();
  await target.dispatchEvent('drop',{dataTransfer:transfer,clientX:x,clientY:y});
 };
 await dragTo('wiki:ds/dsu',pane('wiki'),1590,300);
 assert.equal((await state()).groups.length,2);assert.equal((await state()).right,'wiki:ds/dsu');
 assert.equal(await page.getByRole('button',{name:/^(左右分屏|退出分屏)$/}).count(),0);
 assert.equal(await sorting.getByLabel('排序实验数组').inputValue(),'9 3 9 1');assert.equal(await sorting.locator('nav[aria-label="实验步骤"]').innerText(),step);
 await page.evaluate(()=>window.heldSorting=document.querySelector('.sorting-experiment input'));
 const divider=page.getByRole('separator',{name:'调整左右分屏宽度'});await divider.press('ArrowRight');assert(Math.abs((await state()).ratio-52)<.01);
 const d=await divider.boundingBox();await page.mouse.move(d.x,d.y+150);await page.mouse.down();await page.mouse.move(812,350);assert.equal((await state()).ratio,50);
 await page.mouse.move(840,350);assert.equal((await state()).ratio,50);await page.mouse.move(920,350);assert((await state()).ratio>55);await page.mouse.up();
 await divider.press('Home');assert.equal((await state()).ratio,50);
 const rightHeader=await page.locator('.study-group-header').nth(1).boundingBox(),rightContent=await pane('wiki').boundingBox();assert(Math.abs(rightHeader.x-rightContent.x)<1);
 const external=pane('wiki').getByRole('link',{name:'OI Wiki 原文'}),externalRect=await external.boundingBox();assert(rightContent.x+rightContent.width-externalRect.x-externalRect.width>=10);assert.equal(externalRect.width,32);assert.equal(await pane('wiki').getByRole('button',{name:'返回维基目录'}).count(),1);
 await search('模板');await result('模板','并查集').first().click();await pane('template').getByRole('region',{name:'模板讲解'}).waitFor();
 const templateKey=(await state()).active;await dragTo(templateKey,pane('lab'),10,300);assert.equal((await state()).groups.length,3);
 const groupRects=await page.locator('.study-group-header').evaluateAll(nodes=>nodes.map(node=>({id:node.dataset.groupId,x:node.getBoundingClientRect().x})));
 for(const r of groupRects){const x=await page.locator(`.study-pane[data-group-id="${r.id}"]:not([hidden])`).evaluate(node=>node.getBoundingClientRect().x);assert(Math.abs(x-r.x)<1);}
 for(const toolbar of [pane('template').locator('.template-heading'),pane('wiki').locator('.wiki-reader-toolbar'),pane('lab').locator('.lab-course-header')]){const r=await toolbar.boundingBox();assert.equal(r.y,44);assert.equal(r.height,44);}
 await page.screenshot({path:`${out}/three-groups.png`});
 // Move a tab into the middle of another pane, automatically removing its empty group.
 const labRect=await pane('lab').boundingBox();await dragTo(templateKey,pane('lab'),labRect.x+labRect.width/2,300);assert.equal((await state()).groups.length,2);
 const templateRect=await pane('template').boundingBox();await dragTo('wiki:ds/dsu',pane('template'),templateRect.x+templateRect.width/2,300);assert.equal((await state()).groups.length,1);
 await page.getByRole('tab',{name:'排序基础',exact:true}).click();assert.equal(await page.evaluate(()=>window.heldSorting===document.querySelector('.sorting-experiment input')),true);
 // Real mouse drag, including reverse (left-edge) splitting across wiki iframe content.
 await page.getByRole('tab',{name:'并查集',exact:true}).first().click();const tabRect=await page.getByRole('tab',{name:'并查集',exact:true}).first().boundingBox();
 await page.mouse.move(tabRect.x+30,tabRect.y+20);await page.mouse.down();await page.mouse.move(700,300,{steps:12});await page.mouse.move(10,320,{steps:12});await page.mouse.up();
 assert.equal((await state()).groups.length,2);
 // Restore by dragging back to the other group's tab bar, with no mode toggle.
 const wikiKey='wiki:ds/dsu',targetHeader=page.locator('.study-group-header').filter({has:page.locator('[data-tab-key="lab:sorting-basics"]')});
 const headerRect=await targetHeader.boundingBox();await dragTo(wikiKey,targetHeader,headerRect.x+headerRect.width-15,20);assert.equal((await state()).groups.length,1);
 await page.getByRole('tab',{name:'排序基础',exact:true}).click();await page.reload();await sorting.getByLabel('排序实验数组').waitFor();
 assert.equal(await sorting.getByLabel('排序实验数组').inputValue(),'9 3 9 1');assert.equal(await sorting.locator('nav[aria-label="实验步骤"]').innerText(),step);
 const lab=pane('lab');await lab.locator('.lab-lesson').focus();const before=await lab.locator('.lab-position').innerText();await page.keyboard.press('ArrowRight');assert.notEqual(await lab.locator('.lab-position').innerText(),before);
 await page.keyboard.press('ArrowLeft');assert.equal(await sorting.getByLabel('排序实验数组').inputValue(),'9 3 9 1');
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
  const metrics=await page.locator('.study-bar').first().boundingBox();assert.equal(metrics.height,44);
  await page.screenshot({path:`${out}/browser-${theme}-${width}.png`});
 }
 await page.setViewportSize({width:1600,height:1000});
 await page.evaluate(()=>window.studyFixture.account('fixture-B'));await page.waitForFunction(()=>!document.querySelector('.study-browser'));assert.equal((await state()).tabs.length,0);
 await page.getByRole('button',{name:'实验室入口',exact:true}).click();assert.equal((await state()).tabs.length,1);
 assert.equal(await page.locator('.study-group-header').count(),0);
 await open({kind:'wiki',id:'basic/complexity',title:'复杂度简介'});await pane('wiki').locator('iframe.wiki-reader').waitFor();await page.getByRole('button',{name:'关闭 排序基础',exact:true}).click();
 assert.equal(await page.locator('.study-group-header').count(),0);assert.equal((await pane('wiki').boundingBox()).y,0);
 await page.getByRole('button',{name:'新建学习标签页',exact:true}).click();await page.getByRole('option').filter({hasText:'维基百科'}).click();await page.getByRole('option').filter({hasText:'数据结构'}).click();await result('维基百科','并查集').click();
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
 await page.getByRole('button',{name:'返回主界面',exact:true}).click();assert.equal(await page.locator('.app-shell').evaluate(node=>node.inert),false);
 await open({kind:'wiki',id:'ds/dsu',title:'并查集'});const beforeExample=await state();
 await pane('wiki').frameLocator('iframe.wiki-reader').getByRole('link',{name:'Luogu P1706 全排列问题'}).waitFor();
 // Explicit manual tabs are exercised above; this source link performs ordinary navigation.
 await pane('wiki').frameLocator('iframe.wiki-reader').getByRole('link',{name:'Luogu P1706 全排列问题'}).click();await pane('problem').locator('.cm-content').waitFor();
 assert.equal((await state()).tabs.length,beforeExample.tabs.length);assert.equal((await state()).tabs.filter(tab=>tab.kind==='problem').length,beforeExample.tabs.filter(tab=>tab.kind==='problem').length+1);assert((await state()).tabs.some(tab=>tab.kind==='problem'&&tab.id==='fixture:P1706'));assert((await state()).documents['wiki:ds/dsu']);
 assert.equal(page.context().pages().length,1,'Wiki problems replace their learning slot');
 await open({kind:'wiki',id:'ds/dsu',title:'并查集'});await pane('wiki').frameLocator('iframe.wiki-reader').getByRole('heading',{name:'并查集',exact:true}).waitFor();
 assert.deepEqual(errors,[]);await writeFile(`${out}/result.json`,JSON.stringify({passed:true,errors,scenarios:['cross-source search','source-only search','duplicate tabs','left/right splits','three editor groups','drag-to-merge','header alignment','center snap','experiment and draft preservation','reload and scroll restoration','native close flush','account isolation','themes and widths','compact search close','Wiki example replaces current tab']},null,2));
 console.log('Learning browser UI passed: search, duplicate tabs, independent groups/left-right drag/merge/resize, live state, restart, drafts, scroll, native-close flush, account isolation and six layouts.');
}catch(issue){await page.screenshot({path:`${out}/failure.png`});await writeFile(`${out}/failure.json`,JSON.stringify({message:issue.message,errors,state:await state().catch(()=>null)},null,2));throw issue;}
finally{await browser.close();await server.close();}
