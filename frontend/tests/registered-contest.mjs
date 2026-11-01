import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import path from 'node:path';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const root=path.resolve('..'),env={...process.env,PYTHONPATH:['backend','backend/common','desktop'].map(p=>path.join(root,p)).join(path.delimiter)};
const script=JSON.parse(execFileSync(process.env.TB_PYTHON||(process.platform==='win32'?'python':'python3'),['-c','import json;from contest_reading import READ_SCRIPT;print(json.dumps(READ_SCRIPT))'],{cwd:root,env,encoding:'utf8',windowsHide:true}));
const vite=await createServer({server:{host:'127.0.0.1',port:0}});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/calendar-fixture.html`);
 await page.getByRole('button',{name:'比赛日历',exact:true}).click();
 await page.evaluate(()=>{const f=window.calendarFixture;f.sourceBrowser=true;f.events[0]={...f.events[0],platform:'nowcoder',url:'https://ac.nowcoder.com/acm/contest/142559',import:{status:'partial',ready:0,total:7,accessRequired:true,accessMessage:'请先在原站报名，再重试题面'}};f.setNow(Date.parse('2026-10-26T19:20:00+08:00'));f.refresh();});
 await page.getByText('请先在原站报名，再重试题面',{exact:true}).waitFor();
 await page.getByRole('link',{name:'前往原站 Contest 0',exact:true}).click();
 await page.waitForFunction(()=>window.calendarFixture.originals?.length===1);
 assert.deepEqual(await page.evaluate(()=>window.calendarFixture.originals),['https://ac.nowcoder.com/acm/contest/142559']);
 assert.equal(await page.getByText('题面暂不可用，稍后重试',{exact:true}).count(),0);
 const source=await browser.newPage();
 await source.route('**/*',route=>route.fulfill({contentType:'text/html',body:'<!doctype html><script>window.globalInfo={ownerId:12345};</script><div class="subject-describe">Registered fixture statement</div>'}));
 await source.goto('https://ac.nowcoder.com/acm/contest/142559/A');
 const value=await source.evaluate(script);
 assert.equal(value.identity.owner,'12345');assert.equal(value.identity.state,'logged_in');assert.equal(value.identity.platform,'牛客');
 assert.match(value.html,/Registered fixture statement/);assert.equal(value.url,'https://ac.nowcoder.com/acm/contest/142559/A');
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({ok:true,registrationPrompt:true,sameBrowserOriginalLink:true,actualBrowserReadScript:true,rawHtmlFixtureOnly:true,realOfficialSubmissions:0}));
}finally{await browser.close();await vite.close();}
