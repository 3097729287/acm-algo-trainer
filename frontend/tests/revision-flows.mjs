import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {createServer} from 'vite';
const vite=await createServer({server:{host:'127.0.0.1',port:18832,strictPort:true}});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[];
page.on('pageerror',issue=>errors.push(issue.message));
try{
 await page.goto('http://127.0.0.1:18832/tests/revision-fixture.html');
 for(const [label,min,max] of [['简单',1000,1400],['普通',1300,1700],['困难',1600,2000],['极难',1900,2200]]){
  await page.getByRole('radio',{name:new RegExp('^'+label)}).click();await page.getByRole('button',{name:'生成试卷',exact:true}).click();
  const body=await page.evaluate(()=>revisionFixture.calls.filter(item=>item.path==='contests/preview').at(-1).body);assert.equal(body.min,min);assert.equal(body.max,max);
 }
 await page.getByRole('radio',{name:/^简单/}).click();
 for(const [mode,label] of [['comprehensive','综合训练'],['topic','专项训练'],['single','随机单题'],['replay','重现赛']]){
  await page.getByRole('button',{name:label,exact:true}).click();
  if(mode==='topic'){await page.getByRole('combobox',{name:'专项训练知识点'}).click();await page.getByRole('listbox').getByRole('option',{name:'基础技巧 / 前缀和',exact:true}).click();}
  if(mode==='replay'){await page.getByLabel('搜索重现赛比赛',{exact:true}).fill('区域');await page.getByRole('combobox',{name:'重现赛比赛'}).click();await page.getByRole('listbox').getByRole('option',{name:'区域赛测试 · 2 题',exact:true}).click();}
  assert.equal(await page.getByRole('button',{name:'生成试卷',exact:true}).count(),1);
  await page.getByRole('button',{name:'生成试卷',exact:true}).click();await page.getByRole('button',{name:'开始训练',exact:true}).click();
  assert.equal(await page.evaluate(()=>revisionFixture.started.at(-1).previewId),'preview-'+mode);
 }
 const topic=await page.evaluate(()=>revisionFixture.calls.find(item=>item.path==='contests/preview'&&item.body.mode==='topic').body);assert.deepEqual(topic.tags,['前缀和']);
 await page.getByRole('button',{name:'账号测试',exact:true}).click();
 await page.getByText('快速账号',{exact:true}).waitFor({timeout:1000});assert.equal(await page.evaluate(()=>revisionFixture.profileReady),false);
 await page.evaluate(()=>revisionFixture.resolveProfile());
 await page.getByRole('button',{name:'恢复测试',exact:true}).click();await page.getByRole('button',{name:'触发渲染异常',exact:true}).click();
 await page.getByRole('button',{name:'恢复界面',exact:true}).waitFor();await page.evaluate(()=>revisionFixture.fail=false);await page.getByRole('button',{name:'恢复界面',exact:true}).click();await page.getByText('已恢复',{exact:true}).waitFor();
 assert(errors.every(message=>message==='Fixture render failure'));
 console.log('PASS: four training modes generate and start, presets, topic aliases, replay selection, immediate account identity and recoverable render failures');
}finally{await browser.close();await vite.close();}
