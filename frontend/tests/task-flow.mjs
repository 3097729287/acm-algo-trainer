import assert from 'node:assert/strict';
import {createServer} from 'vite';
import {chromium} from 'playwright';
import {mkdir,writeFile} from 'node:fs/promises';
const out='../.backups/navigation-correction-20261105/task-flow';await mkdir(out,{recursive:true});
const vite=await createServer({cacheDir:'../.backups/background-review-20261105/vite-task-flow',optimizeDeps:{entries:['tests/task-flow-fixture.html']},server:{host:'127.0.0.1',port:0,watch:null}});await vite.listen();
const browser=await chromium.launch({channel:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1400,height:1100}}),errors=[];page.on('pageerror',error=>errors.push(error.message));
try{
 await page.goto(vite.resolvedUrls.local[0]+'tests/task-flow-fixture.html');await page.getByRole('heading',{name:'学习概览',exact:true}).waitFor();assert.equal(await page.getByRole('region',{name:'接续学习'}).count(),0,'No historical completion prompt on startup');
 await page.evaluate(()=>flow.read());await page.getByRole('region',{name:'接续学习'}).getByRole('button',{name:'完成并继续',exact:true}).click();await page.waitForFunction(()=>flowOpened.length===1);assert.equal(await page.evaluate(()=>flowOpened[0].id),'practice');assert.equal(await page.evaluate(()=>flowCalls[0].action),'complete');
 assert.equal(await page.locator('.summary-floating').count(),0);assert.equal(await page.getByRole('region',{name:'接续学习'}).count(),0,'No duplicate prompt after directly continuing');
 await page.evaluate(()=>flow.accept());const continuation=page.getByRole('region',{name:'接续学习'});await continuation.getByRole('button',{name:'下一项：选择一场重现赛'}).click();assert.equal(await page.evaluate(()=>flowOpened.at(-1).kind),'replay');
 await page.evaluate(()=>flow.switchOwner());assert.equal(await continuation.count(),0,'Account switch clears the previous continuation');
 const team=page.getByRole('region',{name:'团队训练排行榜'});assert.deepEqual(await team.locator('tbody tr').evaluateAll(nodes=>nodes.map(node=>[...node.cells].map(cell=>cell.textContent))),[['1','甲队','120'],['2','乙队','60'],['2','丙队','60']]);
 await page.reload();await page.getByRole('heading',{name:'学习概览',exact:true}).waitFor();await page.getByRole('tabpanel',{name:'学习概览',exact:true}).getByRole('button',{name:'完成并继续',exact:true}).click();await page.waitForFunction(()=>flowOpened.length===1);assert.equal(await page.evaluate(()=>flowOpened[0].id),'practice','The necessary completion control is available in the overview');
 assert.deepEqual(errors,[]);const result={ok:true,manualCompleteAndContinue:true,automaticCompletionNextChoice:true,replayHandoff:true,noFloatingWindow:true,ownerIsolation:true,teamTotalScoreAndTies:true,errors};await writeFile(out+'/result.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));
}finally{await browser.close();await vite.close();}
