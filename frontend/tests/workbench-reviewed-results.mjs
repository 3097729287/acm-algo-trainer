import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
import {createServer} from 'vite';
import {chromium} from 'playwright';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const server=await createServer({root,cacheDir:'../.backups/native-reviewed-result-vite',optimizeDeps:{entries:['tests/workbench-fixture.html']},server:{host:'127.0.0.1',port:0}});
await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1200,height:800}}),errors=[];
page.on('pageerror',error=>errors.push(error.message));
try{
 await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/tests/workbench-fixture.html`);
 await page.locator('.cm-content[contenteditable=true]').waitFor();
 const select=async(id,mode,scope,expected,verdict)=>{
  await page.evaluate(({id,mode,scope,expected,verdict})=>{
   const fixture=window.workbenchFixture;
   fixture.submissions=[{id:`receipt-${id}`,problemId:id,contestId:null,mode,scope,verdict,
    code:'int main(){return 0;}',language:'cpp17',submittedAt:'2026-11-09T00:00:00Z',finishedAt:'2026-11-09T00:00:01Z',
    passed:1,total:1,message:'',output:'',stderr:'',caseResults:[{name:'核验用例',input:expected===null?'':'1\n',expected,actual:expected===null?'':'2\n',verdict,timeMs:1,exitCode:0}]}];
   fixture.changeProblem(id);
  },{id,mode,scope,expected,verdict});
  await page.locator(`.tb-workbench[data-problem-id="${id}"] .cm-content[contenteditable=true]`).waitFor();
  if(!await page.locator('.wb-result-summary:visible').isVisible())await page.getByRole('button',{name:'运行结果',exact:true}).click();
  await page.locator('.wb-case').first().waitFor();
 };
 await select('B','submit','local',null,'SAMPLE_PASS');
 assert.equal(await page.locator('.wb-result-summary .wb-verdict').innerText(),'本地通过');
 assert(await page.getByText('本地审核测试已通过，暂不计入原站 AC。',{exact:true}).isVisible());
 assert(await page.getByText('已按审核用例判定；测试输入和标准输出不展示。',{exact:true}).isVisible());
 assert.equal(await page.getByText('自定义输入没有预期答案，仅检查程序是否正常运行。',{exact:true}).count(),0);
 assert.equal(await page.getByText('仅通过公开样例，暂不计入已 AC。',{exact:true}).count(),0);
 assert.equal(await page.locator('.wb-case-input').count(),0);
 await select('C','submit','samples','2\n','SAMPLE_PASS');
 assert(await page.getByText('仅通过公开样例，暂不计入已 AC。',{exact:true}).isVisible());
 assert.equal(await page.locator('.wb-case-input').count(),1);
 assert.equal(await page.getByText('已按审核用例判定；测试输入和标准输出不展示。',{exact:true}).count(),0);
 await select('D','run','samples',null,'RUN_OK');
 assert(await page.getByText('自定义输入没有预期答案，仅检查程序是否正常运行。',{exact:true}).isVisible());
 assert.equal(await page.locator('.wb-sample-note').count(),0);
 await select('E','run','local','2\n','SAMPLE_PASS');
 assert.equal(await page.locator('.wb-result-summary .wb-verdict').innerText(),'样例通过');
 assert.equal(await page.locator('.wb-case-input').count(),1);
 await select('F','submit','template',null,'AC');
 assert(await page.getByText('已按审核用例判定；测试输入和标准输出不展示。',{exact:true}).isVisible());
 assert.equal(await page.getByText('自定义输入没有预期答案，仅检查程序是否正常运行。',{exact:true}).count(),0);
 assert.deepEqual(errors,[]);
 console.log('Workbench reviewed/local, sample, custom-run and template result semantics passed in actual React');
}finally{await browser.close();await server.close();}
