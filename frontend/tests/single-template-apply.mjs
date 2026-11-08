import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';

const out='../.backups/single-template-doubleclick-20261108';await mkdir(out,{recursive:true});
const vite=await createServer({cacheDir:out+'/vite',optimizeDeps:{entries:['tests/workbench-fixture.html']},server:{host:'127.0.0.1',port:0}});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];page.on('pageerror',error=>errors.push(error.message));
const cpp='// saved C++ starter\nint main() { return 19; }\n',python='# saved Python starter\nprint(19)\n';
await page.addInitScript(({cpp,python})=>{
 window.__tbAccountUserId='template-fixture-owner';
 window.initialCodeFixture={selection:{cpp17:'default',python3:'default'},revisions:{cpp17:'cpp-r1',python3:'py-r1'},templates:[{id:'default',title:'默认',builtin:true,customized:true,language:'cpp17',code:cpp},{id:'default',title:'默认',builtin:true,customized:true,language:'python3',code:python}]};
 if(new URLSearchParams(location.search).has('multi'))window.initialCodeFixture.templates.push({id:'own',title:'比赛模板',language:'cpp17',code:'// alternative\nint main() { return 23; }\n'});
},{cpp,python});
const base=`http://127.0.0.1:${vite.httpServer.address().port}/tests/workbench-fixture.html`;
const select=()=>page.getByRole('combobox',{name:'选择初始代码模板',exact:true});
const ready=async(query='')=>{await page.goto(base+query);await page.waitForFunction(()=>document.querySelector('.cm-content')?.getAttribute('contenteditable')==='true'&&!document.querySelector('[aria-label="选择初始代码模板"]')?.disabled);};
const code=()=>page.evaluate(()=>workbenchFixture.readCode());
const edit=async(value,label='C++ 代码')=>{await page.getByRole('textbox',{name:label,exact:true}).focus();await page.keyboard.press('Control+A');if(value)await page.keyboard.insertText(value);else await page.keyboard.press('Backspace');};
const saved=async value=>page.waitForFunction(value=>workbenchFixture.drafts['solo:A']===value,value);
const count=()=>page.evaluate(()=>workbenchFixture.calls.filter(call=>call.path==='initial-code/select').length);
const checks=[];
try{
 await ready();const original='// current solution\nint main() { return 42; }\n';await edit(original);await page.keyboard.press('Control+S');await saved(original);
 await select().click();assert.equal(await code(),original);assert.equal(await count(),0);assert.equal(await page.getByRole('listbox',{name:'选择初始代码模板'}).count(),0);
 await select().dblclick();await page.waitForFunction(expected=>workbenchFixture.readCode()===expected,cpp);await saved(cpp);assert.equal(await count(),1);checks.push('Double-click replaces and saves; single-click leaves the solution intact');
 await page.getByRole('button',{name:'撤销载入代码',exact:true}).click();assert.equal(await code(),original);await saved(original);checks.push('The existing restore action recovers the original solution');
 await edit('');await page.keyboard.press('Control+S');await saved('');await select().dblclick();await page.waitForFunction(expected=>workbenchFixture.readCode()===expected,cpp);await page.getByRole('button',{name:'撤销载入代码',exact:true}).click();assert.equal(await code(),'');checks.push('An intentionally empty buffer can be restored');
 await select().focus();await select().press('Enter');await page.waitForFunction(expected=>workbenchFixture.readCode()===expected,cpp);checks.push('Enter provides the same explicit activation');
 await page.getByRole('combobox',{name:'编程语言',exact:true}).selectOption('python3');await page.waitForFunction(()=>!document.querySelector('[aria-label="选择初始代码模板"]')?.disabled);
 const pyWork='# current Python solution\nprint(42)\n';await edit(pyWork,'Python 代码');await select().dblclick();await page.waitForFunction(expected=>workbenchFixture.readCode()===expected,python);await saved(python);
 const last=await page.evaluate(()=>workbenchFixture.calls.filter(call=>call.path==='initial-code/select').at(-1).body);assert.equal(last.language,'python3');assert.equal(last.revision,'py-r1');checks.push('Only the current language is counted and its saved starter is loaded');
 await ready();await edit(original);const latest=cpp.replace('19','29');await page.evaluate(latest=>{workbenchFixture.initialCode.templates.find(row=>row.language==='cpp17').code=latest;},latest);await select().dblclick();await page.waitForFunction(expected=>workbenchFixture.readCode()===expected,latest);checks.push('A starter edited elsewhere is loaded from the latest server response');
 await ready('?multi');await edit(original);await select().dblclick();assert.equal(await count(),0);assert.equal(await code(),original);await select().press('Escape');await select().click();await page.getByRole('listbox',{name:'选择初始代码模板',exact:true}).getByRole('option',{name:'比赛模板',exact:true}).click();await page.waitForFunction(()=>workbenchFixture.readCode().includes('return 23'));checks.push('Multiple starters retain normal dropdown selection');
 await ready();await edit(original);await page.evaluate(()=>{workbenchFixture.initialSelectDelay=350;workbenchFixture.initialSelectError='模板读取失败，请重试';});
 await select().evaluate(node=>{node.dispatchEvent(new MouseEvent('dblclick',{bubbles:true}));node.dispatchEvent(new MouseEvent('dblclick',{bubbles:true}));});
 await page.waitForFunction(()=>document.querySelector('[aria-label="选择初始代码模板"]')?.disabled);assert.equal(await count(),1);await page.waitForFunction(()=>!document.querySelector('[aria-label="选择初始代码模板"]')?.disabled);assert.equal(await code(),original);assert((await page.locator('.tb-workbench').innerText()).includes('模板读取失败，请重试'));
 await page.evaluate(()=>{workbenchFixture.initialSelectError='';workbenchFixture.initialSelectDelay=0;});await select().dblclick();await page.waitForFunction(expected=>workbenchFixture.readCode()===expected,cpp);checks.push('Repeated activation is bounded; errors keep code intact and can be retried');
 await ready();await edit(original);await page.evaluate(()=>{workbenchFixture.initialSelectDelay=750;});await select().evaluate(node=>node.dispatchEvent(new MouseEvent('dblclick',{bubbles:true})));await page.evaluate(()=>workbenchFixture.changeProblem('B'));await page.waitForFunction(()=>document.querySelector('.tb-workbench')?.dataset.problemId==='B'&&document.querySelector('.cm-content')?.getAttribute('contenteditable')==='true');
 const other='// independent B solution\nint main() { return 88; }\n';await edit(other);await page.waitForTimeout(900);assert.equal(await code(),other);checks.push('A late selection response cannot replace the next problem buffer');
 await ready();await page.evaluate(()=>{workbenchFixture.problemOverrides.B={locked:true};workbenchFixture.changeProblem('B');});await page.waitForFunction(()=>document.querySelector('.tb-workbench')?.dataset.problemId==='B'&&document.querySelector('[aria-label="选择初始代码模板"]')?.disabled);
 const locked=await code();await select().evaluate(node=>node.dispatchEvent(new MouseEvent('dblclick',{bubbles:true})));assert.equal(await count(),0);assert.equal(await code(),locked);checks.push('Locked problems do not apply a starter');
 await ready();await page.evaluate(()=>workbenchFixture.settings(true));await page.getByRole('textbox',{name:'初始代码模板内容',exact:true}).waitFor();await edit('// unsaved starter edit','初始代码模板内容');await select().dblclick();assert.equal(await count(),0);assert.equal(await page.getByRole('textbox',{name:'初始代码模板内容',exact:true}).innerText(),'// unsaved starter edit');checks.push('Settings preserves its unsaved starter edits');
 assert.deepEqual(errors,[]);const report={ok:true,checks,errors};await writeFile(out+'/ui.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}finally{await browser.close();await vite.close();}
