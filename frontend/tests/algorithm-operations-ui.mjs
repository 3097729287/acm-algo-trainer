import assert from 'node:assert/strict';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';
import {ALGORITHM_TOPICS} from '../src/lib/algorithmLearning.js';
import {OPERATION_PRACTICE} from '../src/pages/algorithm-lab/operationPractice.js';

process.env.TB_OFFLINE='1';
const out='../.backups/algorithm-learning-20261030/ui';await mkdir(out,{recursive:true});
const server=await createServer({server:{host:'127.0.0.1',port:0}});await server.listen();
const browser=await chromium.launch({channel:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1366,height:900}}),errors=[];
page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(10000);
const chapter=async i=>{await page.getByRole('button',{name:'目录',exact:true}).click();await page.getByRole('navigation',{name:'课程章节'}).getByRole('button').nth(i).click();};
const open=async id=>{await page.evaluate(id=>window.fixture.openCourse(id),id);await page.locator('.operations-reading').waitFor();};
const noOverflow=async()=>assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
let renders=0,practiceCases=0;
try{
 await page.goto(server.resolvedUrls.local[0]+'tests/algorithm-operations-fixture.html');
 const all=JSON.parse(await readFile('../data/library/lectures.json','utf8')).map(x=>x.content),pick=all.filter(x=>ALGORITHM_TOPICS.some(t=>t.lectures.includes(x.id))||['lecture:foundation-vector','lecture:foundation-lambda'].includes(x.id));
 await page.evaluate(pick=>window.fixture.lectures(pick),pick);
 await page.getByRole('button',{name:'从零讲',exact:true}).click();
 assert.equal(await page.getByRole('navigation',{name:'完整知识讲解'}).getByRole('button').count(),2);
 await page.evaluate(()=>window.fixture.openLecture('lecture:foundation-fenwick'));await page.getByRole('region',{name:'模板讲解'}).waitFor();
 assert.match(await page.getByRole('region',{name:'模板讲解'}).innerText(),/prefix_sum/);
 await page.getByRole('button',{name:'在实验室学习'}).click();await page.getByRole('heading',{name:'树状数组',exact:true}).waitFor();
 for(const topic of ALGORITHM_TOPICS){
  await page.evaluate(id=>window.fixture.seed(old=>({...old,learningPaths:{...old.learningPaths,activePath:id,[id]:{...old.learningPaths?.[id],mode:'learn',labV1:{chapter:'0'}}}})),topic.id);
  await open(topic.id);
  for(let i=0;i<7;i++){
   await chapter(i);await noOverflow();assert.equal(await page.locator('.katex-error,.reading-image-missing').count(),0);renders++;
  }
  await page.getByRole('button',{name:'跟着做五道题'}).click();
  if(topic.id==='dsu'){assert.match(await page.locator('.lab-position').innerText(),/跟做 1 \/ 5/);continue;}
  for(let i=0;i<5;i++){
   await page.getByRole('navigation',{name:'课堂练习'}).getByRole('button').nth(i).click();
   await page.getByLabel('练习答案',{exact:true}).fill('wrong');await page.getByRole('button',{name:'验证结果',exact:true}).click();assert.match(await page.locator('.lab-feedback').innerText(),/还不一致/);
   await page.getByLabel('练习答案',{exact:true}).fill(OPERATION_PRACTICE[topic.id][i].answer);assert.equal(await page.locator('.lab-feedback').count(),0);
   await page.getByRole('button',{name:'验证结果',exact:true}).click();assert((await page.locator('.lab-feedback').innerText()).includes(OPERATION_PRACTICE[topic.id][i].reason));
   await page.getByLabel('我的实现说明').fill('说明保留的信息、操作的输入及边界。');await page.getByRole('checkbox').first().check();practiceCases++;
  }
 }
 await open('linear-basis');await chapter(0);
 await page.getByLabel('线性基原数',{exact:true}).fill('12 10 9');await page.getByRole('button',{name:'应用数据'}).click();await page.getByRole('button',{name:'查看结果'}).click();
 await page.getByLabel('查询异或值',{exact:true}).fill('0');assert.match(await page.locator('.xor-experiment').innerText(),/最大异或为 15/);
 await page.getByLabel('预测不同异或值个数').fill('7');await page.getByRole('button',{name:'核对预测'}).click();assert.match(await page.locator('.lab-feedback').innerText(),/别把/);
 await page.getByLabel('预测不同异或值个数').fill('8');assert.equal(await page.locator('.lab-feedback').count(),0);await page.getByRole('button',{name:'核对预测'}).click();assert.match(await page.locator('.lab-feedback').innerText(),/秩为 3/);
 await page.getByLabel('第 k 小下标').fill('4');assert.equal(await page.getByLabel('第 k 小结果').innerText(),'9');
 await page.getByLabel('线性基原数',{exact:true}).fill('-1 2');await page.getByRole('button',{name:'应用数据'}).click();await page.getByRole('alert').waitFor();assert.equal(await page.evaluate(()=>window.fixture.prefs.learningPaths['linear-basis'].labV1.drafts.experiment.input),'12 10 9');
 await page.getByLabel('线性基原数',{exact:true}).fill('9223372036854775808 1');await page.getByRole('button',{name:'应用数据'}).click();await page.getByRole('button',{name:'查看结果'}).click();assert.match(await page.getByRole('table',{name:'主元与二进制'}).innerText(),/9223372036854775808/);
 await page.reload();await page.evaluate(()=>window.fixture.openCourse('linear-basis'));assert.equal(await page.getByLabel('线性基原数',{exact:true}).inputValue(),'9223372036854775808 1');
 await page.getByRole('button',{name:'重置实验'}).click();await page.getByLabel('待合并线性基').fill('1');await page.getByRole('button',{name:'合并线性基'}).click();assert.equal(await page.getByLabel('线性基原数',{exact:true}).inputValue(),'6 5 3 1');
 await open('fenwick');await chapter(0);await page.getByLabel('操作类型').selectOption('add');await page.getByLabel('操作参数').fill('0 7');await page.getByRole('button',{name:'执行操作'}).click();assert.match(await page.getByRole('region',{name:'树状数组操作实验'}).innerText(),/外部位置 0 变为 9/);
 await page.getByLabel('操作参数').fill('-1 7');await page.getByRole('button',{name:'执行操作'}).click();await page.getByRole('alert').waitFor();
 for(const theme of ['dark','light'])for(const width of [1366,1024,390]){
  await page.setViewportSize({width,height:900});await page.evaluate(t=>document.documentElement.dataset.theme=t,theme);
  for(const id of ['linear-basis','segment-tree','dinic','li-chao']){await open(id);await chapter(0);await noOverflow();await page.screenshot({path:`${out}/${id}-${theme}-${width}.png`});renders++;}
  await page.evaluate(()=>window.fixture.openTemplate('builtin:linear-basis'));await page.getByRole('region',{name:'模板讲解'}).waitFor();await noOverflow();
  await page.getByRole('button',{name:'讲解版',exact:true}).click();assert.equal(await page.getByRole('region',{name:'模板讲解'}).count(),0);await page.getByRole('button',{name:'竞赛版',exact:true}).click();
  await page.screenshot({path:`${out}/template-${theme}-${width}.png`});
 }
 assert.deepEqual(errors,[]);await writeFile(out+'/report.json',JSON.stringify({ok:true,topics:8,chapters:56,practiceCases,renders,viewports:3,themes:2,errors},null,2));console.log('Algorithm operations UI passed');
}finally{await browser.close();await server.close();}
