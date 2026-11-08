import assert from 'node:assert/strict';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const server=await createServer({cacheDir:'../.backups/next-150/vite-solution-inline',optimizeDeps:{entries:['tests/learning-browser-fixture.html']},server:{host:'127.0.0.1',port:0,watch:null}});await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1800,height:1100}}),errors=[];page.on('pageerror',error=>errors.push(error.message));page.setDefaultTimeout(12000);
const state=()=>page.evaluate(()=>window.studyFixture.state());
const open=tab=>page.evaluate(tab=>window.studyFixture.open(tab),tab);
try{
 await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/tests/learning-browser-fixture.html`);await page.getByRole('button',{name:'题目入口',exact:true}).click();
 const pane=page.locator('.study-problem:not([hidden])'),editor=pane.locator('.cm-content'),book=pane.getByRole('button',{name:'题解',exact:true});await editor.waitFor();
 await editor.fill('#include <bits/stdc++.h>\nint main(){\n  return 42;\n}\n');await editor.press('Control+End');
 const cursor=await pane.locator('.wb-cursor-position').innerText();await pane.getByLabel('题面内容').evaluate(node=>node.scrollTop=650);
 await page.evaluate(()=>window.heldToggleEditor=document.querySelector('.cm-content'));const text=await editor.innerText();
 for(let i=0;i<2;i++){
  await book.click();await page.getByRole('complementary',{name:'单题题解'}).waitFor();assert.equal((await state()).tabs.length,1);assert.equal((await state()).groups.length,1);assert.equal(await book.getAttribute('aria-pressed'),'true');
  await book.click();await page.getByRole('complementary',{name:'单题题解'}).waitFor({state:'hidden'});assert.equal(await page.locator('.study-group-header').count(),0);
  assert.equal(await editor.innerText(),text);assert.equal(await pane.locator('.wb-cursor-position').innerText(),cursor);
  assert(await page.evaluate(()=>window.heldToggleEditor===document.querySelector('.cm-content')),'Toggling retains the live editor');
  assert(Math.abs(await pane.getByLabel('题面内容').evaluate(node=>node.scrollTop)-650)<3);
 }
 await pane.getByRole('button',{name:'下一题'}).click();await page.waitForFunction(()=>window.studyFixture.state().tabs.some(tab=>tab.id==='fixture:B'));await editor.waitFor();
 assert.equal((await state()).tabs.filter(tab=>tab.kind==='problem').length,1);assert.equal((await state()).tabs.some(tab=>tab.id==='fixture:A'),false);
 assert(!(await editor.innerText()).includes('return 42'),'The next problem gets its own editor buffer');
 await open({kind:'problem',id:'fixture:A',title:'小月的数组'});await editor.waitFor();await page.waitForFunction(()=>document.querySelector('.cm-content')?.textContent.includes('return 42'));
 assert.equal(await editor.innerText(),text,'Old saved draft can be reopened without leaving its tab behind');
 await editor.fill('int main(){return 43;}');
 await open({kind:'wiki',id:'ds/dsu',title:'并查集'});await page.locator('iframe.wiki-reader').waitFor();
 await open({kind:'problem',id:'fixture:B',title:'并查集合并查询'});await editor.waitFor();
 const current=await state();assert.equal(current.tabs.length,1);assert.equal(current.tabs[0].kind,'problem');assert(current.documents['wiki:ds/dsu']);
 assert(await page.evaluate(()=>window.studyFixture.calls.some(call=>call.path==='draft'&&call.body.id==='fixture:A'&&call.body.code.includes('return 43'))),'Entering another problem flushes the unsaved previous draft');
 await page.reload();await editor.waitFor();assert.equal((await state()).tabs.filter(tab=>tab.kind==='problem').length,1);
 assert.deepEqual(errors,[]);console.log('PASS inline solution toggle retains editor/caret/scroll; next and direct practice replace one slot, preserve archived Wiki state and flush/restore the previous draft');
}catch(error){console.log(JSON.stringify(await page.locator('.study-problem').evaluateAll(nodes=>nodes.map(n=>({hidden:n.hidden,classes:n.className,text:n.innerText.slice(0,150),buttons:[...n.querySelectorAll('button')].map(b=>({text:b.innerText,label:b.getAttribute('aria-label'),hidden:!b.getClientRects().length})).filter(b=>b.label?.includes('题解'))})))));await page.screenshot({path:'../.backups/next-150/inline-debug.png'});throw error;}finally{await browser.close();await server.close();}
