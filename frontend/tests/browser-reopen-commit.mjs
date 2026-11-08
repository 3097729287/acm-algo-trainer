import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';

const out='../.backups/browser-reopen-commit-20261109';await mkdir(out,{recursive:true});
const server=await createServer({cacheDir:out+'/vite',optimizeDeps:{entries:['tests/learning-browser-fixture.html']},server:{host:'127.0.0.1',port:0}});await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[],checks=[];page.on('pageerror',error=>errors.push(error.message));page.setDefaultTimeout(15000);
const id='fixture:A',code='// ordinary reopening stays in this account 😀\nint answer=42;';
const editor=page.locator('.study-problem:not([hidden]) .cm-content[contenteditable=true]');
const waitCode=()=>page.waitForFunction(code=>document.querySelector('.study-problem:not([hidden]) .cm-content')?.innerText.trimEnd()===code.trimEnd(),code);
const manifest=owner=>page.evaluate(owner=>JSON.parse(localStorage.getItem('learning-fixture.'+owner+'.prefs')||'{}').learningPaths?.browserV1,owner);
const hide=async()=>{
 await page.evaluate(()=>studyFixture.hide());await page.locator('.study-browser').waitFor({state:'hidden'});
 await page.waitForFunction(()=>JSON.parse(localStorage.getItem('learning-fixture.fixture-A.prefs')||'{}').learningPaths?.browserV1?.open===false);
};
try{
 await page.goto(server.resolvedUrls.local[0]+'tests/learning-browser-fixture.html');await page.waitForFunction(()=>window.studyFixture);
 await page.evaluate(({id})=>{studyFixture.holdFlush=true;window.opening=studyFixture.open({kind:'problem',id});},{id});
 await page.waitForFunction(()=>typeof studyFixture.releaseFlush==='function');assert.equal(await page.locator('.study-browser').count(),0);
 await page.evaluate(async()=>{studyFixture.holdFlush=false;studyFixture.releaseFlush();await window.opening;});await editor.waitFor();
 assert.equal((await manifest('fixture-A')).open,true);checks.push('first ordinary editor is shown only after its navigation commit');
 await editor.fill(code);await editor.press('Control+s');await page.waitForFunction(({id,code})=>JSON.parse(localStorage.getItem('learning-fixture.fixture-A.drafts')||'{}')[id]?.code===code,{id,code});
 await hide();await page.evaluate(({id})=>studyFixture.open({kind:'problem',id}),{id});await waitCode();
 assert.equal((await manifest('fixture-A')).open,true);await page.reload();await editor.waitFor();await waitCode();checks.push('reopening the same ordinary problem survives an immediate refresh with unchanged code');
 await hide();const before=await manifest('fixture-A');
 await page.evaluate(async({id})=>{studyFixture.failFlush=true;await studyFixture.open({kind:'problem',id});},{id});
 assert.equal(await page.locator('.study-browser').count(),0);assert.deepEqual(await manifest('fixture-A'),before);
 assert.equal(await page.evaluate(id=>JSON.parse(localStorage.getItem('learning-fixture.fixture-A.drafts'))[id].code,id),code);checks.push('failed reopening keeps the browser closed and preserves its manifest and draft');
 await page.evaluate(({id})=>{studyFixture.failFlush=false;studyFixture.holdFlush=true;studyFixture.releaseFlush=null;window.opening=studyFixture.open({kind:'problem',id});},{id});
 await page.waitForFunction(()=>typeof studyFixture.releaseFlush==='function');await page.evaluate(()=>studyFixture.account('fixture-B'));
 await page.waitForFunction(()=>studyFixture.state().tabs.length===0);await page.evaluate(async()=>{studyFixture.holdFlush=false;studyFixture.releaseFlush();await window.opening;});
 assert.equal(await page.locator('.study-browser').count(),0);assert.deepEqual(await manifest('fixture-A'),before);
 assert.equal(await page.evaluate(()=>localStorage.getItem('learning-fixture.fixture-B.drafts')),null);checks.push('changing accounts while reopening commits neither the old tab nor its code into the new account');
 await page.evaluate(()=>studyFixture.account('fixture-A'));await page.waitForFunction(()=>studyFixture.state().tabs.some(tab=>tab.id==='fixture:A'));
 await page.evaluate(({id})=>studyFixture.open({kind:'problem',id}),{id});await editor.waitFor();await waitCode();
 await page.reload();await editor.waitFor();await waitCode();assert.equal((await manifest('fixture-A')).tabs.find(tab=>tab.id===id).visit?.reviewId||null,null);checks.push('returning to the original account reopens its ordinary context and exact draft');
 assert.deepEqual(errors,[]);await page.screenshot({path:out+'/ordinary-reopened.png'});await writeFile(out+'/result.json',JSON.stringify({ok:true,checks,pageErrors:errors,scope:'Shared React with generated account-owned fixtures; no real user state or account grants'},null,2)+'\n');console.log('PASS '+checks.join('; '));
}catch(error){await page.screenshot({path:out+'/failure.png'});await writeFile(out+'/failure.txt',String(error)+'\n'+await page.locator('body').innerText());throw error;}
finally{await browser.close();await server.close();}
