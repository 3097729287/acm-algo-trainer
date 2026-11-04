import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
import {mkdir,writeFile} from 'node:fs/promises';
import {chromium} from 'playwright';
import {studyClock,planActions} from '../src/lib/learningSummaryModel.js';

const clock=studyClock();assert.equal(clock.interact(0),null);assert.deepEqual(clock.interact(299),[0,299]);assert.equal(clock.interact(599),null);assert.equal(clock.interact(600,false),null);assert.equal(clock.interact(601),null);assert.deepEqual(clock.interact(603),[601,603]);
const out='../.backups/learning-summary/browser-ui';await mkdir(out,{recursive:true});
const command=process.env.TB_PYTHON||'python';
const args=['../scripts/serve_learning_summary_check.py','--seed',process.env.TB_TEST_SEED||'E:/项目/ToBe/版本/最新版/程序/data/library.sqlite3'];
const child=spawn(command,args,{env:{...process.env,TB_OFFLINE:'1',PYTHONIOENCODING:'utf-8'},stdio:['pipe','pipe','pipe']});
let stderr='';child.stderr.on('data',chunk=>stderr+=chunk);
const config=await new Promise((resolve,reject)=>{const timeout=setTimeout(()=>reject(new Error('Server startup timed out: '+stderr)),90000);createInterface({input:child.stdout}).on('line',line=>{try{const value=JSON.parse(line);if(value.url){clearTimeout(timeout);resolve(value);}}catch{}});child.on('exit',code=>{clearTimeout(timeout);reject(new Error('Server exited '+code+': '+stderr));});});
const context=await chromium.launchPersistentContext(out+'/profile-'+Date.now(),{channel:'msedge',headless:true,viewport:{width:1440,height:1000}}),page=context.pages()[0],errors=[];
page.on('pageerror',issue=>errors.push(issue.message));page.setDefaultTimeout(20000);
const api=async(path,body)=>page.evaluate(async({path,body})=>{const catalog=await fetch('/api/data?compact=1').then(r=>r.json());const response=await fetch('/api/'+path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json','X-TB-Token':catalog.token},body:JSON.stringify(body)});const value=await response.json();if(!response.ok)throw new Error(value.error);return value;},{path,body});
try{
 await page.goto(config.url);await page.getByRole('button',{name:'学习进度与周计划',exact:true}).first().waitFor();
 await page.getByRole('button',{name:'学习进度与周计划',exact:true}).first().click();
 const panel=page.getByRole('dialog',{name:'学习进度与周计划',exact:true});await panel.locator('.summary-article section').first().waitFor();
 assert.equal((await api('learning-summary')).config.weekdayMinutes,null);
 await panel.getByRole('button',{name:'目标与时间设置',exact:true}).click();
 await panel.getByLabel('工作日每日分钟',{exact:true}).fill('60');await panel.getByLabel('周末每日分钟',{exact:true}).fill('120');
 await panel.getByLabel('输入输出',{exact:true}).check();await panel.getByLabel('分支与循环',{exact:true}).check();
 await panel.getByRole('button',{name:'生成安排',exact:true}).click();await panel.getByRole('button',{name:'采纳并开始',exact:true}).waitFor();
 let saved=await api('learning-summary');assert.equal(saved.plan,null);assert(saved.proposal.tasks.length>0);
 await panel.getByRole('button',{name:'采纳并开始',exact:true}).click();await panel.getByRole('region',{name:'本周学习任务'}).waitFor().catch(()=>{});
 await page.waitForFunction(async()=>!!(await fetch('/api/learning-summary').then(r=>r.json())).plan);
 saved=await api('learning-summary');assert.equal(saved.plan.tracks.length,2);assert(saved.plan.days.every(d=>d.used<=d.minutes));
 const pending=planActions(saved);assert(pending.every(t=>t.summaryTask));
 await panel.getByRole('button',{name:'全屏阅读规划',exact:true}).click();assert.equal((await panel.boundingBox()).width,1440);
 await panel.getByRole('button',{name:'恢复浮窗',exact:true}).click();assert((await panel.boundingBox()).width<1440);
 await panel.getByRole('button',{name:'收起为标题条',exact:true}).click();assert.equal((await panel.boundingBox()).height,44);
 await panel.getByRole('button',{name:'展开规划',exact:true}).click();
 const title=panel.locator('.summary-header').first(),before=await panel.boundingBox(),r=await title.boundingBox();await page.mouse.move(r.x+180,r.y+20);await page.mouse.down();await page.mouse.move(r.x+250,r.y+60);await page.mouse.up();const after=await panel.boundingBox();assert(after.x>before.x&&after.y>before.y);
 await panel.getByRole('checkbox',{name:'详细',exact:true}).check();await panel.getByRole('combobox',{name:'规划语气',exact:true}).selectOption('鼓励');
 await page.screenshot({path:out+'/planning.png'});
 const task=saved.plan.tasks.find(t=>t.kind==='lecture'&&t.topicId==='basic-control');assert(task);
 await panel.getByRole('button',{name:new RegExp('阅读：分支与循环')}).first().click();
 await panel.getByRole('button',{name:'关闭学习规划',exact:true}).click();
 await page.locator('.lecture-prerequisites>button').first().waitFor();
 for(const selector of ['.lecture-prerequisites>button','.lecture-next']){
  const values=await page.locator(selector).evaluateAll(nodes=>nodes.map(n=>({border:getComputedStyle(n).borderTopWidth,shadow:getComputedStyle(n).boxShadow})));
  assert(values.length>0);assert(values.every(v=>v.border==='0px'&&v.shadow==='none'));
 }
 await page.screenshot({path:out+'/flat-reading-links.png'});
 await page.keyboard.press('Control+Shift+P');await panel.waitFor();
 assert.equal(await panel.getByRole('checkbox',{name:'详细',exact:true}).isChecked(),true);
 assert.equal(await panel.getByRole('combobox',{name:'规划语气',exact:true}).inputValue(),'鼓励');
 assert.deepEqual(errors,[]);await writeFile(out+'/result.json',JSON.stringify({ok:true,fullApp:true,config:config.state,checks:['time-required','adoption','shared-budget','fullscreen','floating','collapse','drag','article','reading-flat-links','global-shortcut','view-restoration'],errors},null,2));
 console.log('Learning summary browser checks passed');
}catch(issue){
 console.error('Browser errors:',errors);console.error('Panel:',await page.locator('.learning-summary').innerText().catch(()=>''));console.error('Backend:',stderr.slice(-5000));
 await page.screenshot({path:out+'/failure.png'});throw issue;
}finally{await context.close();child.stdin.end('\n');}
