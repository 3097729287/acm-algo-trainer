import assert from 'node:assert/strict';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const vite=await createServer({cacheDir:'../.backups/followups-158/instant-vite',server:{host:'127.0.0.1',port:0,watch:null}});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[],rankRequests=[];page.on('pageerror',e=>errors.push(e.message));
page.on('request',r=>{if(r.url().includes('/ranks/'))rankRequests.push(r.url());});
try{
 await page.goto(vite.resolvedUrls.local[0]+'tests/instant-display-fixture.html');await page.waitForFunction(()=>window.instant?.show);
 await page.evaluate(async()=>{await instant.seed();instant.holdBoard=true;instant.holdTemplates=true;instant.holdWiki=true;instant.show('board');});
 await page.getByText('已确认玩家',{exact:true}).waitFor();await page.waitForFunction(()=>instant.paint?.text.includes('已确认玩家'));
 const board=await page.evaluate(()=>instant.paint);assert(board.ms<200,JSON.stringify(board));assert.equal(await page.locator('.user-presence').getAttribute('data-cached'),'true');
 assert.equal(await page.locator('.avatar-rank-frame image').getAttribute('href').then(v=>v.startsWith('data:image/png;base64,')),true);assert.equal(rankRequests.length,0);
 await page.evaluate(()=>instant.owner('perf-B'));assert.equal(await page.getByText('已确认玩家',{exact:true}).count(),0,'Never initialize a different account from the previous owner snapshot');
 await page.evaluate(()=>{instant.release();});await page.getByText('新账号玩家',{exact:true}).waitFor();
 await page.evaluate(()=>{instant.owner('perf-A');instant.show('templates');});await page.getByText('已经缓存的模板',{exact:true}).waitFor();
 await page.evaluate(()=>instant.show('wiki'));await page.frameLocator('iframe.wiki-reader').getByRole('heading',{name:'正文已经读取'}).waitFor();
 assert(await page.evaluate(()=>instant.pending.length>0),'Wiki metadata is still waiting while its article is already visible');
 await page.evaluate(()=>instant.release());assert.deepEqual(errors,[]);
 // An unloaded empty tab is safe to close; real unsaved changes still block.
 await page.goto(vite.resolvedUrls.local[0]+'tests/learning-browser-fixture.html');
 await page.evaluate(()=>{window.holdProblemRead=true;});await page.getByRole('button',{name:'题目入口',exact:true}).click();
 await page.waitForFunction(()=>window.releaseProblemRead);
 const drain=()=>page.evaluate(async()=>{const waits=[];window.dispatchEvent(new CustomEvent('tb-before-update',{detail:{waitUntil:p=>waits.push(p)}}));return Promise.all(waits);});
 assert((await drain()).every(v=>v!==false),'The empty pending read must not block native close');
 await page.evaluate(()=>{window.holdProblemRead=false;window.releaseProblemRead();});await page.locator('.cm-content[contenteditable=true]').waitFor();
 await page.evaluate(()=>{window.failDraft=true;});await page.locator('.cm-content[contenteditable=true]').fill('int keep_unsaved = 7;');assert((await drain()).some(v=>v===false),'An actual failed edit save must still block close');
 await page.evaluate(()=>{window.failDraft=false;});assert((await drain()).every(v=>v!==false));assert.deepEqual(errors,[]);
 console.log(JSON.stringify({ok:true,cachedBoardFirstPaintMs:Math.round(board.ms),rankImageHttpRequests:rankRequests.length,templateSnapshotBeforeNetwork:true,wikiArticleBeforeSlowCatalogue:true,accountSwitchNoStaleData:true,emptyPendingReadCloseAndRealSaveFailureGuard:true}));
}finally{await browser.close();await vite.close();}
