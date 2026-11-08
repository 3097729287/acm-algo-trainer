import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';

const out='../.backups/review-bookmark-context-20261109';await mkdir(out,{recursive:true});
const server=await createServer({cacheDir:out+'/vite',optimizeDeps:{entries:['tests/learning-browser-fixture.html']},server:{host:'127.0.0.1',port:0}});await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[],checks=[];page.on('pageerror',error=>errors.push(error.message));page.setDefaultTimeout(15000);
const id='fixture:A',reviewA='0123456789abcdef0123456789abcdef',reviewB='fedcba9876543210fedcba9876543210';
const ordinaryA='// ordinary A remains intact\nint originalA = 1;',ordinaryB='// ordinary B is private\nint originalB = 2;',rewrittenA='// A independent rewrite 😀\nint answerA = 3;',rewrittenB='// B independent rewrite\nint answerB = 4;';
const open=source=>page.evaluate(source=>studyFixture.open(source),source);
const editor=()=>page.locator('.study-problem:not([hidden]) .cm-content[contenteditable=true]');
const waitCode=code=>page.waitForFunction(code=>document.querySelector('.study-problem:not([hidden]) .cm-content')?.innerText.trimEnd()===code.trimEnd(),code);
const readOwner=owner=>page.evaluate(owner=>JSON.parse(localStorage.getItem('learning-fixture.'+owner+'.drafts')||'{}'),owner);
async function save(code,owner,reviewId){await editor().fill(code);await editor().press('Control+s');await page.waitForFunction(({owner,key,code})=>JSON.parse(localStorage.getItem('learning-fixture.'+owner+'.drafts')||'{}')[key]?.code===code,{owner,key:id+(reviewId?'::review:'+reviewId:''),code});}
try{
 await page.goto(server.resolvedUrls.local[0]+'tests/learning-browser-fixture.html');await page.waitForFunction(()=>window.studyFixture);
 await open({kind:'problem',id});await editor().waitFor();await save(ordinaryA,'fixture-A');
 await open({kind:'problem',id,reviewTask:{id:reviewA},visit:{practiceFlow:{stage:'review'}}});await page.waitForFunction(reviewId=>studyFixture.state().tabs.find(tab=>tab.kind==='problem')?.reviewTask?.id===reviewId,reviewA);await page.waitForFunction(()=>!document.querySelector('.study-problem:not([hidden]) .cm-content')?.textContent.includes('ordinary A'));
 await save(rewrittenA,'fixture-A',reviewA);assert.equal((await readOwner('fixture-A'))[id].code,ordinaryA);checks.push('same problem switches to a separately saved review draft');
 await page.reload();await editor().waitFor();await waitCode(rewrittenA);assert.equal((await readOwner('fixture-A'))[id].code,ordinaryA);checks.push('refresh restores review identity and keeps ordinary code');
 await page.evaluate(()=>studyFixture.hide());await open({kind:'problem',id,reviewTask:{id:reviewA}});await waitCode(rewrittenA);checks.push('close and reopen retains the review draft');
 await open({kind:'wiki',id:'ds/dsu'});await page.locator('.study-wiki:not([hidden]) .wiki-reader').waitFor();
 const saved=await page.evaluate(()=>studyFixture.state().documents['problem:fixture:A']);assert.equal(saved.visit.reviewId,reviewA);await open(saved);await waitCode(rewrittenA);checks.push('archived tab reopening retains its review context');
 await page.evaluate(()=>studyFixture.account('fixture-B'));await page.waitForFunction(()=>studyFixture.state().tabs.length===0);
 await open({kind:'problem',id});await editor().waitFor();await save(ordinaryB,'fixture-B');
 await open({kind:'problem',id,reviewTask:{id:reviewB}});await page.waitForFunction(()=>!document.querySelector('.study-problem:not([hidden]) .cm-content')?.textContent.includes('ordinary B'));await save(rewrittenB,'fixture-B',reviewB);
 const a=await readOwner('fixture-A');assert.equal(a[id].code,ordinaryA);assert.equal(a[id+'::review:'+reviewA].code,rewrittenA);assert(!a[id+'::review:'+reviewB]);checks.push('another account has its own ordinary and review drafts');
 await page.evaluate(()=>studyFixture.account('fixture-A'));await editor().waitFor();await waitCode(rewrittenA);checks.push('switching back restores the original account review');
 await open({kind:'problem',id,reviewTask:null});await waitCode(ordinaryA);assert.equal((await readOwner('fixture-A'))[id+'::review:'+reviewA].code,rewrittenA);
 await open({kind:'problem',id,reviewTask:{id:reviewA}});await waitCode(rewrittenA);checks.push('switching ordinary and review contexts preserves both stored versions');
 const b=await readOwner('fixture-B');assert.equal(b[id].code,ordinaryB);assert.equal(b[id+'::review:'+reviewB].code,rewrittenB);assert(!b[id+'::review:'+reviewA]);
 await page.evaluate(({id})=>{studyFixture.holdFlush=true;window.pendingScopeChange=studyFixture.open({kind:'problem',id,reviewTask:null});},{id});
 await page.waitForFunction(()=>typeof studyFixture.releaseFlush==='function');await waitCode(rewrittenA);
 await page.evaluate(async()=>{studyFixture.failFlush=true;studyFixture.holdFlush=false;studyFixture.releaseFlush();await window.pendingScopeChange;});
 await waitCode(rewrittenA);assert.equal((await readOwner('fixture-A'))[id].code,ordinaryA);checks.push('failed navigation commit retains the current review and both drafts');
 await page.evaluate(()=>{studyFixture.failFlush=false;});await open({kind:'problem',id,reviewTask:null});await waitCode(ordinaryA);
 await page.reload();await editor().waitFor();await waitCode(ordinaryA);checks.push('immediate refresh after leaving a review restores the committed ordinary scope');
 await page.evaluate(({id,reviewA})=>{studyFixture.holdFlush=true;window.pendingScopeChange=studyFixture.open({kind:'problem',id,reviewTask:{id:reviewA}});},{id,reviewA});
 await page.waitForFunction(()=>typeof studyFixture.releaseFlush==='function');await page.evaluate(()=>studyFixture.account('fixture-B'));await waitCode(rewrittenB);
 await page.evaluate(async()=>{studyFixture.holdFlush=false;studyFixture.releaseFlush();await window.pendingScopeChange;});await waitCode(rewrittenB);
 assert.equal(await page.evaluate(()=>JSON.parse(localStorage.getItem('learning-fixture.fixture-A.prefs')).learningPaths.browserV1.tabs.find(tab=>tab.id==='fixture:A')?.visit?.reviewId||null),null);
 assert.equal(await page.evaluate(()=>studyFixture.state().tabs.find(tab=>tab.id==='fixture:A')?.reviewTask?.id),reviewB);checks.push('an account switch cancels the pending scope commit without changing either account manifest');
 await page.evaluate(()=>studyFixture.account('fixture-A'));await waitCode(ordinaryA);await open({kind:'problem',id,reviewTask:{id:reviewA}});await waitCode(rewrittenA);
 assert.deepEqual(errors,[]);await page.screenshot({path:out+'/review-restored.png'});await writeFile(out+'/result.json',JSON.stringify({ok:true,checks,pageErrors:errors,backendScope:'Shared React navigation with isolated account-owned draft fixtures; actual native backend is checked separately'},null,2)+'\n');console.log('PASS '+checks.join('; '));
}catch(error){await page.screenshot({path:out+'/failure.png'});await writeFile(out+'/failure.txt',String(error)+'\n'+await page.locator('body').innerText());await writeFile(out+'/failure-state.json',JSON.stringify(await page.evaluate(()=>({state:studyFixture.state(),prefs:studyFixture.prefs(),calls:studyFixture.calls})),null,2));throw error;}
finally{await browser.close();await server.close();}
