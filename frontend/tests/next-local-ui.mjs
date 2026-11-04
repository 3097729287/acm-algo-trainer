import assert from 'node:assert/strict';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const server=await createServer({server:{host:'127.0.0.1',port:0,watch:null}});await server.listen();
const browser=await chromium.launch({channel:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1500,height:950}}),errors=[];
page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/tests/learning-browser-fixture.html`);await page.waitForFunction(()=>window.studyFixture);
 await page.evaluate(()=>studyFixture.open({kind:'lab',id:'fenwick',title:'树状数组'}));await page.getByRole('button',{name:'区间加与区间和',exact:true}).click();
 const experiment=page.getByRole('region',{name:'双树状数组区间加实验'});await experiment.waitFor();
 await page.getByRole('button',{name:'执行区间加',exact:true}).click();await page.getByText('当前数组：[2, 6, 8, 5, 4]；差分：[2, 4, 2, -3, -1]。',{exact:true}).waitFor();
 await page.getByLabel('区间加参数',{exact:true}).fill('0 5 -2');await page.getByRole('button',{name:'执行区间加',exact:true}).click();
 await page.getByText('当前数组：[0, 4, 6, 3, 2]；差分：[0, 4, 2, -3, -1]。',{exact:true}).waitFor();
 await page.getByRole('button',{name:'撤回区间加',exact:true}).click();await page.getByText('当前数组：[2, 6, 8, 5, 4]；差分：[2, 4, 2, -3, -1]。',{exact:true}).waitFor();
 await page.getByLabel('区间加参数',{exact:true}).fill('4 9 3');await page.getByRole('button',{name:'执行区间加',exact:true}).click();await experiment.getByRole('alert').waitFor();
 await page.getByLabel('查询前缀长度',{exact:true}).fill('0');await page.getByText(/前 k 项之和.*0 × 0 − 0 = 0/).waitFor();
 await page.evaluate(()=>window.dispatchEvent(new Event('tb:study-checkpoint')));await page.reload();await page.getByRole('button',{name:'区间加与区间和',exact:true}).click();await experiment.waitFor();await page.getByText('当前数组：[2, 6, 8, 5, 4]；差分：[2, 4, 2, -3, -1]。',{exact:true}).waitFor();
 assert.deepEqual(errors,[]);console.log('PASS range-update experiment, negative changes, undo, invalid bounds, empty prefix and persisted state');
}finally{await browser.close();await server.close();}
