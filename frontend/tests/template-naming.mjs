import assert from 'node:assert/strict';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const vite=await createServer({server:{host:'127.0.0.1',port:0}});await vite.listen();
const browser=await chromium.launch({channel:'msedge',headless:true});const page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/template-naming-fixture.html`);
 const editor=page.getByRole('textbox',{name:'初始代码模板内容'});await editor.waitFor();
 assert.equal(await page.getByRole('textbox',{name:'初始代码模板名称'}).count(),0);
 assert.equal(await page.getByLabel('当前初始代码模板',{exact:true}).count(),0);
 for(const size of[13,18,22]){
  await page.evaluate(value=>document.documentElement.style.setProperty('--ui-font-size',value+'px'),size);
  const rows=await page.locator('.initial-code-settings-toolbar select,.initial-code-settings-actions>button').evaluateAll(nodes=>nodes.map(node=>{const r=node.getBoundingClientRect(),s=getComputedStyle(node);return{height:r.height,center:r.y+r.height/2,content:parseFloat(s.fontSize)*1.2+parseFloat(s.paddingTop)+parseFloat(s.paddingBottom)+2};}));
  assert(rows.every(row=>row.height>=36&&row.content<=row.height),JSON.stringify({size,rows}));assert(Math.max(...rows.map(r=>r.center))-Math.min(...rows.map(r=>r.center))<1);
 }
 await page.getByRole('button',{name:'新建初始代码模板'}).click();let dialog=page.getByRole('dialog',{name:'新建模板'});await dialog.waitFor();
 await dialog.getByRole('textbox',{name:'模板名称'}).fill('双指针练习');await dialog.getByRole('textbox',{name:'模板名称'}).press('Enter');await dialog.waitFor({state:'hidden'});
 assert.equal(await page.evaluate(()=>templateFixture.state.templates.filter(r=>r.title==='双指针练习').length),1);
 await editor.fill('int main() { return 7; }');await page.getByRole('button',{name:'保存初始代码模板'}).click();await page.getByRole('status').filter({hasText:'代码已保存'}).waitFor();
 const toast=await page.locator('.initial-code-save-notice').boundingBox(),plus=await page.getByRole('button',{name:'新建初始代码模板'}).boundingBox();assert(toast.x+toast.width<plus.x&&Math.abs(toast.y+toast.height/2-plus.y-plus.height/2)<1);
 const id=await page.evaluate(()=>templateFixture.state.selection.cpp17);
 await page.getByRole('button',{name:'重命名初始代码模板'}).click();dialog=page.getByRole('dialog',{name:'重命名模板'});await dialog.getByRole('textbox',{name:'模板名称'}).fill('窗口模板');await dialog.getByRole('textbox',{name:'模板名称'}).press('Enter');await dialog.waitFor({state:'hidden'});
 const renamed=await page.evaluate(id=>templateFixture.state.templates.find(r=>r.id===id),id);assert.equal(renamed.title,'窗口模板');assert.equal(renamed.code,'int main() { return 7; }');
 await page.getByRole('status').waitFor({state:'hidden'});
 await page.getByRole('button',{name:'新建初始代码模板'}).click();await page.getByRole('dialog').getByRole('textbox',{name:'模板名称'}).fill('取消');await page.keyboard.press('Escape');assert.equal(await page.getByRole('dialog').count(),0);assert.equal(await page.evaluate(()=>templateFixture.state.templates.filter(r=>r.title==='取消').length),0);
 assert.deepEqual(errors,[]);console.log('PASS template naming dialog, same-ID rename and code retention, no inline name/checkmark, save toast before actions, no clipped labels at 13/18/22px, aligned control centers, cancel without creation.');
}finally{await browser.close();await vite.close();}
