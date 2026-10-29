import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {createServer} from 'vite';
const vite=await createServer({server:{host:'127.0.0.1',port:0}});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1280,height:800}}),errors=[];
page.on('pageerror',issue=>errors.push(issue.message));
try{
 await page.goto(vite.resolvedUrls.local[0]+'tests/replay-fixture.html');
 await page.getByRole('textbox',{name:'C++ 代码'}).waitFor();
 await page.getByRole('button',{name:'提交',exact:true}).click();
 await page.getByLabel('原站提交状态').waitFor();
 const calls=await page.evaluate(()=>replayFixture.calls);
 assert.equal(calls.filter(call=>call.path==='official/submit').length,1);
 assert.equal(calls.find(call=>call.path==='official/submit').body.contestId,'replay');
 assert.equal(calls.filter(call=>call.path==='submissions').length,0,'Replay never queues a local submit');
 for(const width of [2048,1280,800]){
  await page.setViewportSize({width,height:800});
  await page.getByRole('button',{name:'选择比赛题目，当前 P13089'}).click();
  const row=page.getByRole('menuitemradio').first();
  const [number,title]=await Promise.all([row.locator('.mock-picker-letter').boundingBox(),row.locator('.mock-picker-title').boundingBox()]);
  assert.ok(number.x+number.width<=title.x,'Long problem ID does not overlap title');
  assert.ok(await row.evaluate(node=>node.scrollWidth<=node.clientWidth));
  await page.keyboard.press('Escape');
 }
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({ok:true,longProblemIds:true,replayNativeSubmit:true,contestBound:true,noLocalQueue:true,realAccountSubmission:false}));
}finally{await browser.close();await vite.close();}
