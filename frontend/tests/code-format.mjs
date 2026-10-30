import assert from 'node:assert/strict';
import {mkdtemp} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const front=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const temporary=await mkdtemp(path.join(tmpdir(),'tb-format-ui-'));
const server=await createServer({root:front,cacheDir:path.join(temporary,'vite'),server:{host:'127.0.0.1',port:0,watch:null}});await server.listen();
const base='http://127.0.0.1:'+server.httpServer.address().port;
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const prefix='// 中文 😀\n',source=prefix+'int x=1;\n',formatted=prefix+'int x = 1;\n';
const response={language:'cpp17',source,code:formatted,changes:[{from:prefix.length+5,to:prefix.length+5,insert:' '},{from:prefix.length+6,to:prefix.length+6,insert:' '}]};
const python={language:'python3',source:'x=1\n',code:'x = 1\n',changes:[{from:1,to:1,insert:' '},{from:2,to:2,insert:' '}]};
const errors=[];
async function open(extra={}){
 const page=await browser.newPage({viewport:{width:1440,height:900}});page.on('pageerror',e=>errors.push(e.message));
 await page.addInitScript(format=>{window.__tbAccountUserId='format-owner';window.formattingFixture=format;},{available:true,delay:250,responses:[response,python],...extra});
 await page.goto(base+'/tests/workbench-fixture.html');
 await page.locator('.cm-content[contenteditable=true]').waitFor();
 return {page,editor:page.getByRole('textbox',{name:'C++ 代码',exact:true})};
}
const formatCalls=page=>page.evaluate(()=>workbenchFixture.calls.filter(c=>c.path==='code/format').length);
try{
 const first=await open();await first.editor.fill(source);await first.page.evaluate(offset=>workbenchFixture.selectCode(offset+7,offset+4),prefix.length);
 await first.editor.press('Control+s');await first.editor.press('Control+s');
 await first.page.waitForFunction(expected=>workbenchFixture.readCode()===expected,formatted);
 assert.equal(await formatCalls(first.page),1,'Repeated Ctrl+S on the same pending version is single-flight');
 assert.deepEqual(await first.page.evaluate(()=>workbenchFixture.readSelection()),{anchor:prefix.length+9,head:prefix.length+4},'UTF16 Chinese/emoji and reversed selection map through the formatting edits');
 await first.page.waitForFunction(expected=>workbenchFixture.drafts['solo:A']===expected,formatted);
 await first.editor.press('Control+z');assert.equal(await first.page.evaluate(()=>workbenchFixture.readCode()),source,'One undo restores the exact pre-format document');await first.page.close();
 const moving=await open();await moving.editor.fill(source);await moving.editor.press('Control+s');
 await moving.page.waitForFunction(()=>workbenchFixture.calls.some(c=>c.path==='code/format'));
 await moving.page.evaluate(position=>workbenchFixture.selectCode(position),prefix.length+7);
 await moving.page.waitForFunction(expected=>workbenchFixture.readCode()===expected,formatted);
 assert.equal((await moving.page.evaluate(()=>workbenchFixture.readSelection())).head,prefix.length+9,'The current cursor is mapped, rather than restoring a stale captured selection');await moving.page.close();
 for(const kind of ['typing','problem','language','account']){
  const {page,editor}=await open({delay:450});await editor.fill(source);await editor.press('Control+s');
  await page.waitForFunction(()=>workbenchFixture.calls.some(c=>c.path==='code/format'));
  if(kind==='typing')await editor.fill(source+'// newer input');
  if(kind==='problem'){await page.evaluate(()=>workbenchFixture.changeProblem('B'));await page.locator('.cm-content[contenteditable=true]').waitFor();}
  if(kind==='language'){
   await page.getByRole('combobox',{name:'编程语言',exact:true}).click();await page.getByRole('listbox',{name:'编程语言',exact:true}).getByRole('option',{name:/Python 3/}).click();
   await page.getByRole('textbox',{name:'Python 代码',exact:true}).waitFor();
  }
  if(kind==='account')await page.evaluate(()=>{window.__tbAccountUserId='other-format-owner'});
  await page.waitForTimeout(650);
  const code=await page.evaluate(()=>workbenchFixture.readCode());assert.notEqual(code,formatted,kind+' invalidates the old reply');
  if(kind==='typing')assert.equal(code,source+'// newer input');
  if(kind==='account')assert.equal(code,source);
  await page.close();
 }
 for(const mode of ['mock','formal']){
  const {page,editor}=await open();
  await page.evaluate(mode=>workbenchFixture.changeContest({id:'fixture-'+mode,status:'running',slots:[{id:'A'}],config:{strategy:mode==='mock'?'balanced':'replay'}}),mode);
  await page.getByRole('button',{name:'返回工作台',exact:true}).waitFor();await page.locator('.cm-content[contenteditable=true]').waitFor();
  await editor.fill(source);await editor.press('Control+s');
  await page.waitForFunction(({mode,source})=>workbenchFixture.drafts['fixture-'+mode+':A']===source,{mode,source});
  assert.equal(await formatCalls(page),0,mode+' only saves, without a formatter API request');await page.close();
 }
 const legacy=await open({available:false});await legacy.editor.fill(source);await legacy.editor.press('Control+s');
 await legacy.page.waitForFunction(expected=>workbenchFixture.drafts['solo:A']===expected,source);assert.equal(await formatCalls(legacy.page),0);await legacy.page.close();
 const failed=await open({error:'Fixture formatter failure'});await failed.editor.fill(source);await failed.editor.press('Control+s');
 await failed.page.getByText('Fixture formatter failure',{exact:true}).waitFor();
 assert.equal(await failed.page.evaluate(()=>workbenchFixture.readCode()),source);await failed.page.waitForFunction(expected=>workbenchFixture.drafts['solo:A']===expected,source);await failed.page.close();
 const py=await open();await py.page.getByRole('combobox',{name:'编程语言',exact:true}).click();await py.page.getByRole('listbox',{name:'编程语言',exact:true}).getByRole('option',{name:/Python 3/}).click();
 const pyEditor=py.page.getByRole('textbox',{name:'Python 代码',exact:true});await pyEditor.fill(python.source);await pyEditor.press('Control+s');
 await py.page.waitForFunction(expected=>workbenchFixture.readCode()===expected,python.code);assert.equal(await py.page.evaluate(()=>workbenchFixture.calls.find(c=>c.path==='code/format').body.language),'python3');await py.page.close();
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({ok:true,formatsAndSaves:true,reversedUtf16Selection:true,currentSelectionMapped:true,singleUndo:true,singleFlight:true,staleReplyGuards:4,contestModesNeverRequestFormatting:2,legacyCapabilityFallback:true,errorPreservesSource:true,python:true,realAccountSubmission:false}));
}finally{
 await browser.close();await server.close();
 // Keep the small isolated cache available for inspection and authorized
 // Recycle Bin cleanup; workspace policy does not permit permanent deletion.
 console.log(JSON.stringify({retainedTestArtifacts:temporary}));
}
