import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {createServer} from 'vite';
import {openMockSelection} from './mock-mode-selection.mjs';
const vite=await createServer({server:{host:'127.0.0.1',port:18832,strictPort:true}});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[];
page.on('pageerror',issue=>errors.push(issue.message));
try{
 await page.goto('http://127.0.0.1:18832/tests/revision-fixture.html');
 const range=async(min,max)=>{await page.getByRole('button',{name:'训练筛选',exact:true}).click();await page.getByLabel('训练最低难度',{exact:true}).fill(String(min));await page.getByLabel('训练最高难度',{exact:true}).fill(String(max));await page.getByRole('button',{name:'关闭筛选',exact:true}).click();};
 for(const [label,min,max,duration] of [['简单',1000,1400,120],['普通',1300,1700,150],['困难',1600,2000,180],['极难',1900,2200,210]]){
  await range(min,max);await page.getByRole('button',{name:'生成试卷',exact:true}).click();
  const body=await page.evaluate(()=>revisionFixture.calls.filter(item=>item.path==='contests/preview').at(-1).body);assert.equal(body.min,min);assert.equal(body.max,max);assert.equal(body.duration,duration);
 }
 await range(1000,1400);
 for(const [mode,label] of [['comprehensive','综合训练'],['topic','专项训练'],['replay','重现赛']]){
  await page.getByRole('button',{name:label,exact:true}).click();
  if(mode==='topic'){
   const picker=()=>openMockSelection(page,'专项训练');
   await picker();assert.equal(await page.getByRole('listbox').getByText(/\//).count(),0);await page.getByRole('listbox').getByRole('option',{name:'基础技巧',exact:true}).click();
   await page.getByRole('listbox').getByRole('option',{name:'选择「基础技巧」',exact:true}).click();await page.getByRole('button',{name:'生成试卷',exact:true}).click();
   const broad=await page.evaluate(()=>revisionFixture.calls.filter(item=>item.path==='contests/preview').at(-1).body);assert.equal(broad.tags.length,34);assert(broad.tags.includes('前缀和'));assert(broad.tags.includes('二分查找'));
   await picker();await page.getByRole('listbox').getByRole('option',{name:'基础技巧',exact:true}).click();await page.getByRole('listbox').getByRole('option',{name:'前缀和',exact:true}).click();
  }
  if(mode==='replay'){
   assert.equal(await page.getByLabel('搜索重现赛比赛',{exact:true}).count(),0);await openMockSelection(page,'重现赛');
   for(const name of ['XCPC','CCPC 区域赛','2025年','CCPC 2025 郑州区域赛 · 2 题'])await page.getByRole('listbox').getByRole('option',{name,exact:true}).click();
  }
  assert.equal(await page.getByRole('button',{name:'生成试卷',exact:true}).count(),1);
  await page.getByRole('button',{name:'生成试卷',exact:true}).click();await page.getByRole('button',{name:'开始训练',exact:true}).click();
  assert.equal(await page.evaluate(()=>revisionFixture.started.at(-1).previewId),'preview-'+mode);
  assert.equal(await page.evaluate(()=>revisionFixture.started.at(-1).duration),{comprehensive:120,topic:90,replay:300}[mode]);
 }
 await page.getByRole('button',{name:'综合训练',exact:true}).click();
 await range(1000,2000);
 await page.getByRole('button',{name:'训练筛选',exact:true}).click();await page.getByLabel('模拟赛时长',{exact:true}).fill('50');await page.keyboard.press('Escape');
 await page.getByRole('button',{name:'专项训练',exact:true}).click();await page.getByRole('button',{name:'综合训练',exact:true}).click();
 await page.getByRole('button',{name:'生成试卷',exact:true}).click();assert.equal(await page.evaluate(()=>revisionFixture.calls.filter(item=>item.path==='contests/preview').at(-1).body.duration),50);
 assert.equal(await page.getByRole('button',{name:'随机单题',exact:true}).count(),0);
 const topic=await page.evaluate(()=>revisionFixture.calls.findLast(item=>item.path==='contests/preview'&&item.body.mode==='topic').body);assert.deepEqual(topic.tags,['前缀和']);
 await page.getByRole('button',{name:'账号测试',exact:true}).click();
 await page.getByText('快速账号',{exact:true}).waitFor({timeout:1000});assert.equal(await page.evaluate(()=>revisionFixture.profileReady),false);
 await page.evaluate(()=>revisionFixture.resolveProfile());
 await page.getByRole('button',{name:'恢复测试',exact:true}).click();await page.getByRole('button',{name:'触发渲染异常',exact:true}).click();
 await page.getByRole('button',{name:'恢复界面',exact:true}).waitFor();await page.evaluate(()=>revisionFixture.fail=false);await page.getByRole('button',{name:'恢复界面',exact:true}).click();await page.getByText('已恢复',{exact:true}).waitFor();
 assert(errors.every(message=>message==='Fixture render failure'));
 console.log('PASS: three training modes generate and start, shared range sliders, topic aliases, replay selection, immediate account identity and recoverable render failures');
}finally{await browser.close();await vite.close();}
