import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const out='../.backups/deepseek-ui-'+Date.now();await mkdir(out,{recursive:true});
const vite=await createServer({cacheDir:'../.backups/deepseek-ui-vite',optimizeDeps:{entries:['tests/deepseek-embedded-fixture.html']},server:{host:'127.0.0.1',port:0,watch:null}});await vite.listen();
const browser=await chromium.launchPersistentContext(out+'/profile',{channel:process.env.CI?undefined:'msedge',headless:true,viewport:{width:1440,height:960}});
const page=browser.pages()[0],errors=[];page.on('pageerror',error=>errors.push(error.message));page.setDefaultTimeout(12000);
await page.route('**/*',route=>new URL(route.request().url()).hostname==='127.0.0.1'?route.continue():route.abort('blockedbyclient'));
const lastVisible=()=>page.evaluate(()=>window.deepseekFixture.calls.filter(item=>item.path==='desktop/deepseek'&&item.body).at(-1)?.body.visible);
const waitFrame=async visible=>{await page.waitForFunction(visible=>window.deepseekFixture.calls.filter(item=>item.path==='desktop/deepseek'&&item.body).at(-1)?.body.visible===visible,visible);};
let result={ok:false,actualWorkbench:true,nativeApiExplicitlyMocked:true,realDeepSeekRenderClaimedFromThisTest:false};
try{
 await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/deepseek-embedded-fixture.html`);
 const editor=page.locator('.cm-content[contenteditable=true]');await editor.waitFor();
 const toggle=page.getByRole('button',{name:'切换到DeepSeek',exact:true});await toggle.waitFor();await page.waitForFunction(()=>!document.querySelector('.wb-deepseek-toggle')?.disabled);
 const placement=await page.evaluate(()=>{const toggle=document.querySelector('.wb-deepseek-toggle').getBoundingClientRect(),font=document.querySelector('.wb-font-controls').getBoundingClientRect();return {toggleRight:toggle.right,fontLeft:font.left};});assert(placement.toggleRight<=placement.fontLeft,'The toggle belongs to the left of statement font size');
 await editor.fill('int main(){return 42;} // preserve this draft');
 await page.getByRole('button',{name:'原文',exact:true}).click();await page.getByRole('button',{name:'中文',exact:true}).waitFor();
 await page.locator('.wb-statement').evaluate(node=>{node.scrollTop=420;window.savedStatement=node;window.savedEditor=document.querySelector('.cm-content');window.savedEditorView=window.deepseekFixture.editor();});
 const before=await page.locator('.wb-statement').evaluate(node=>({top:node.scrollTop,html:node.innerHTML}));assert(before.top>100);
 await toggle.click();await waitFrame(true);
 assert.equal(await page.locator('.wb-deepseek-surface').count(),1);assert.equal(await page.locator('.wb-deepseek-surface iframe').count(),0);
 assert(await page.locator('.wb-statement').isHidden());
 assert(await page.evaluate(()=>window.savedEditor===document.querySelector('.cm-content')&&window.savedEditorView===window.deepseekFixture.editor()));
 const geometry=await page.evaluate(()=>({message:window.deepseekFixture.calls.filter(c=>c.path==='desktop/deepseek'&&c.body?.visible).at(-1).body,box:document.querySelector('.wb-deepseek-surface').getBoundingClientRect().toJSON(),code:document.querySelector('.wb-code-pane').getBoundingClientRect().toJSON()}));
 assert(Math.abs(geometry.message.rect.x-geometry.box.x)<1);assert(geometry.message.rect.x+geometry.message.rect.width<=geometry.code.left+1);
 await page.getByRole('button',{name:'切回题面',exact:true}).click();await waitFrame(false);
 assert(await page.locator('.wb-statement').isVisible());
 const after=await page.locator('.wb-statement').evaluate(node=>({top:node.scrollTop,html:node.innerHTML,same:node===window.savedStatement}));
 assert(after.same);assert.equal(after.html,before.html);assert.equal(after.top,before.top);
 assert(await page.getByRole('button',{name:'中文',exact:true}).isVisible());assert.equal(await editor.innerText(),'int main(){return 42;} // preserve this draft');
 await page.getByRole('button',{name:'切换到DeepSeek',exact:true}).click();await waitFrame(true);
 await page.evaluate(()=>window.deepseekFixture.modal(true));await waitFrame(false);assert.equal(await lastVisible(),false);
 await page.evaluate(()=>window.deepseekFixture.modal(false));await waitFrame(true);
 for(const role of ['alertdialog','listbox','tooltip']){await page.evaluate(role=>window.deepseekFixture.overlay(role),role);await waitFrame(false);await page.evaluate(()=>window.deepseekFixture.overlay(null));await waitFrame(true);}
 await page.evaluate(()=>window.deepseekFixture.search(true));await waitFrame(false);
 await page.evaluate(()=>window.deepseekFixture.search(false));await waitFrame(true);
 await page.evaluate(()=>window.deepseekFixture.active(false));await waitFrame(false);
 await page.evaluate(()=>window.deepseekFixture.active(true));await waitFrame(true);
 await page.evaluate(()=>{window.deepseekFixture.state.status='error';});
 const retry=page.getByRole('region',{name:'DeepSeek',exact:true}).getByRole('button',{name:'重试',exact:true});await retry.waitFor();await retry.click();
 await page.waitForFunction(()=>window.deepseekFixture.calls.some(c=>c.path==='desktop/deepseek'&&c.body?.retry===true));
 await retry.waitFor({state:'hidden'});
 await page.evaluate(()=>{window.deepseekFixture.state.ownerKey='b'.repeat(64);});
 await page.getByRole('button',{name:'切换到DeepSeek',exact:true}).waitFor();
 await page.getByRole('button',{name:'切换到DeepSeek',exact:true}).click();
 await page.waitForFunction(()=>window.deepseekFixture.calls.filter(c=>c.path==='desktop/deepseek'&&c.body?.visible).at(-1)?.body.ownerKey==='b'.repeat(64));
 assert(await page.evaluate(()=>window.deepseekFixture.calls.filter(c=>c.path==='desktop/deepseek'&&c.body?.visible).at(-1).body.ownerKey==='b'.repeat(64)));
 const originalWidth=await page.evaluate(()=>window.deepseekFixture.calls.filter(c=>c.path==='desktop/deepseek'&&c.body?.visible).at(-1).body.rect.width);
 const splitter=page.getByRole('separator',{name:'调整题面与代码宽度',exact:true});await splitter.focus();await page.keyboard.press('ArrowRight');
 await page.waitForFunction(width=>Math.abs(window.deepseekFixture.calls.filter(c=>c.path==='desktop/deepseek'&&c.body?.visible).at(-1).body.rect.width-width)>1,originalWidth);
 for(const width of [1120,1440]){await page.setViewportSize({width,height:900});await waitFrame(true);}
 const frames=await page.evaluate(()=>window.deepseekFixture.calls.filter(c=>c.path==='desktop/deepseek'&&c.body).map(c=>c.body));
 const allowed=new Set(['viewId','sequence','ownerKey','visible','rect','viewport','retry','shortcuts']);assert(frames.every(frame=>Object.keys(frame).every(key=>allowed.has(key))));
 assert(!JSON.stringify(frames).includes('preserve this draft'),'No statement or code is sent to the native page');
 assert(await page.evaluate(()=>window.savedEditor===document.querySelector('.cm-content')&&window.savedEditorView===window.deepseekFixture.editor()));
 const advanceCount=()=>page.evaluate(()=>window.deepseekFixture.nextCalls);
 let next=await advanceCount();
 for(const focus of [()=>editor.focus(),()=>page.locator('input[aria-label="题面字号"]').focus(),()=>page.getByRole('button',{name:'切回题面',exact:true}).focus(),()=>page.evaluate(()=>{document.body.tabIndex=-1;document.body.focus();})]){
  await focus();await page.keyboard.press('Control+ArrowRight');await page.waitForFunction(expected=>window.deepseekFixture.nextCalls===expected,++next);await page.waitForTimeout(220);
 }
 await page.getByRole('button',{name:'切回题面',exact:true}).click();await waitFrame(false);await page.locator('.wb-statement').focus();
 await page.keyboard.press('Control+ArrowRight');await page.waitForFunction(expected=>window.deepseekFixture.nextCalls===expected,++next);await page.waitForTimeout(220);
 await editor.focus();await page.keyboard.down('Control');await page.keyboard.down('ArrowRight');await page.keyboard.down('ArrowRight');await page.keyboard.down('ArrowRight');await page.keyboard.up('ArrowRight');await page.keyboard.up('Control');
 await page.waitForFunction(expected=>window.deepseekFixture.nextCalls===expected,++next);await page.waitForTimeout(220);assert.equal(await advanceCount(),next);
 await page.evaluate(()=>window.deepseekFixture.failDraft=true);await editor.fill('int main(){return 43;} // keep failed-save draft');
 await page.keyboard.press('Control+ArrowRight');await page.waitForTimeout(280);assert.equal(await advanceCount(),next,'Save failure must block navigation');
 await page.evaluate(()=>window.deepseekFixture.failDraft=false);await page.keyboard.press('Control+ArrowRight');await page.waitForFunction(expected=>window.deepseekFixture.nextCalls===expected,++next);await page.waitForTimeout(220);
 await page.getByRole('button',{name:'切换到DeepSeek',exact:true}).click();await waitFrame(true);
 await page.evaluate(()=>{window.dispatchEvent(new CustomEvent('tb:native-shortcut',{detail:{id:'workbench-next'}}));window.postMessage({id:'workbench-next'},'*');});
 await page.waitForTimeout(180);assert.equal(await advanceCount(),next,'Webpage messages must not enqueue a native command');
 await page.evaluate(()=>window.deepseekFixture.queueNative('workbench-next'));await page.waitForFunction(expected=>window.deepseekFixture.nextCalls===expected,++next);
 await page.waitForTimeout(350);assert.equal(await advanceCount(),next,'Repeated native reads must not repeat navigation');
 await page.evaluate(()=>window.deepseekFixture.queueNative('workbench-next',true));await page.waitForTimeout(350);assert.equal(await advanceCount(),next,'A stale native registration must be rejected');
 assert.deepEqual(errors,[]);await page.screenshot({path:out+'/deepseek-position.png',animations:'disabled'});
 result={...result,ok:true,buttonBeforeFont:true,statementDomScrollAndLanguagePreserved:true,sameEditorDomAndView:true,codeDraftPreserved:true,noIframeOrExternalWindow:true,modalPopupSearchHiddenPaneAndResizeHandled:true,lateNativeInitializationRecovered:true,explicitNativeRetry:true,staleSessionExplicitlyReopenedWithFreshBinding:true,splitterFrameUpdated:true,geometryAndRegisteredBindingsOnly:true,shortcutIgnoresEditorInputButtonBodyAndStatementFocus:true,singleFlightAndRepeatSuppressed:true,failedSaveBlocksNext:true,nativeReadDeduplicatedAndStaleRegistrationRejected:true,webpageCannotEnqueueNativeAction:true,errors};
}catch(error){result={...result,errorClass:error.name,error:error.message,errors,diagnostics:await page.evaluate(()=>{const node=document.querySelector('.wb-deepseek-surface'),chain=[];for(let n=node;n;n=n.parentElement){const r=n.getBoundingClientRect(),s=getComputedStyle(n);chain.push({tag:n.tagName,class:n.className,rect:r.toJSON(),display:s.display,visibility:s.visibility,overflowX:s.overflowX,overflowY:s.overflowY});}const r=node?.getBoundingClientRect();return {hidden:document.hidden,chain,blockers:[...document.querySelectorAll('dialog[open],[role="dialog"],.modal-overlay,.modal-backdrop,.workspace-search-results,.tour-overlay,.next-actions-flyout,.recommendation-dialog')].map(n=>({tag:n.tagName,class:n.className,rect:n.getBoundingClientRect().toJSON()})),hits:r?[[r.left+1,r.top+1],[r.right-1,r.top+1],[r.left+1,r.bottom-1],[r.right-1,r.bottom-1],[(r.left+r.right)/2,(r.top+r.bottom)/2]].map(([x,y])=>{const hit=document.elementFromPoint(x,y);return {x,y,tag:hit?.tagName,id:hit?.id,class:hit?.className,inside:node.contains(hit)};}):[],bodyPreview:document.body?.innerText.slice(0,1800),lastCalls:(window.deepseekFixture?.calls||[]).filter(c=>c.path==='desktop/deepseek').slice(-3)};})};await page.screenshot({path:out+'/failure.png'});throw error;}
finally{await writeFile(out+'/result.json',JSON.stringify(result,null,2));console.log(JSON.stringify({...result,receipt:out+'/result.json'}));await browser.close();await vite.close();}
