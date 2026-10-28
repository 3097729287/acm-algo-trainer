import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const vite=await createServer({server:{host:'127.0.0.1',port:0,fs:{allow:[process.cwd(),fs.realpathSync('node_modules')]}}});await vite.listen();
const browser=await chromium.launch({channel:'msedge',headless:true}),context=await browser.newContext({permissions:['clipboard-read','clipboard-write']}),page=await context.newPage(),errors=[];
page.on('pageerror',error=>errors.push(error.message));
try{
 await page.goto(vite.resolvedUrls.local[0]+'tests/history-code-fixture.html');await page.waitForFunction(()=>window.fixture);
 await page.evaluate(()=>fixture.show({id:'first',code:'',codePending:true}));await page.getByRole('status',{name:'正在读取历史代码'}).waitFor();
 assert(await page.getByRole('button',{name:'复制本次代码'}).isDisabled());
 await page.evaluate(()=>fixture.show({id:'second',code:'',codePending:true}));await page.waitForFunction(()=>fixture.calls.length===2);
 await page.evaluate(()=>fixture.resolve('first','obsolete source'));assert.equal(await page.locator('pre').count(),0);
 await page.evaluate(()=>fixture.reject('second'));await page.getByRole('alert').waitFor();
 await page.getByRole('button',{name:'重新读取提交代码'}).click();await page.waitForFunction(()=>fixture.calls.length===3);
 await page.evaluate(()=>fixture.resolve('second','int answer = 42;'));await page.getByText('int answer = 42;',{exact:true}).waitFor();
 await page.getByRole('button',{name:'复制本次代码'}).click();assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),'int answer = 42;');
 await page.evaluate(()=>fixture.show({id:'local',code:'retained local source',codePending:false}));await page.getByText('retained local source',{exact:true}).waitFor();assert.equal(await page.evaluate(()=>fixture.calls.length),3);
 await page.evaluate(()=>fixture.show({id:'closed',code:'',codePending:true}));await page.waitForFunction(()=>fixture.calls.length===4);
 await page.evaluate(()=>fixture.show(null));await page.evaluate(()=>fixture.resolve('closed','late response'));assert.equal(await page.locator('pre').count(),0);
 assert.deepEqual(errors,[]);console.log('PASS lazy history: loading, no stale source, cancellation, failure/retry, exact copy and local reuse.');
}finally{await context.close();await browser.close();await vite.close();}
