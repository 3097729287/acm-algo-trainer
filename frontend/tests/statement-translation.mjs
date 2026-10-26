import assert from 'node:assert/strict';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const server=await createServer({server:{host:'127.0.0.1',port:0}});await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];
page.on('pageerror',error=>errors.push(error.message));
const original='# Polyline\n\nGiven an array of integers, print the number of points.\n\n## Sample Output 1\n\n```text\n3\n```\n\nThe red points satisfy the condition.\n\n![Polyline](https://img.atcoder.jp/fixture.png)';
const chinese=original.replace('Given an array of integers, print the number of points.','给定整数数组，求符合条件的点数。').replace('The red points satisfy the condition.','图中的红点符合条件。');
const embedded='data:image/svg+xml;base64,'+Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" width="360" height="200"><path d="M20 180L100 80L180 180L260 20L340 180" stroke="black" fill="none"/></svg>').toString('base64');
try{
  await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/tests/workbench-fixture.html`);await page.locator('.cm-content').waitFor();
  await page.evaluate(({original,chinese,embedded})=>{
    const f=window.workbenchFixture;
    f.problemOverrides.P={title:'Polyline',markdown:original,images:{'https://img.atcoder.jp/fixture.png':embedded},translation:{kind:'bundled',targetLanguage:'zh-CN',markdown:chinese}};
    f.changeProblem('P');
  },{original,chinese,embedded});
  await page.getByText('图中的红点符合条件。',{exact:true}).waitFor();
  await page.waitForFunction(()=>{const image=document.querySelector('.wb-statement img');return image?.complete&&image.naturalWidth===360;});
  assert.equal(await page.getByRole('button',{name:'中文',exact:true}).getAttribute('aria-pressed'),'true');
  assert.equal(await page.evaluate(()=>window.workbenchFixture.calls.filter(call=>call.path==='problem/translate').length),0);
  await page.getByRole('button',{name:'原文',exact:true}).click();await page.getByText('The red points satisfy the condition.',{exact:true}).waitFor();
  assert.equal(await page.locator('.wb-statement img').count(),1);
  await page.evaluate(original=>{const f=window.workbenchFixture;f.problemOverrides.Q={markdown:original,autoTranslate:true};f.changeProblem('Q');},original);
  await page.waitForFunction(()=>document.querySelector('.wb-statement')?.textContent.includes('Q 的中文题面'));
  assert.equal(await page.evaluate(()=>window.workbenchFixture.calls.filter(call=>call.path==='problem/translate'&&call.body.id==='Q').length),1);
  await page.evaluate(original=>{const f=window.workbenchFixture;f.translationDelay=600;f.problemOverrides.R={markdown:original,autoTranslate:true};f.changeProblem('R');},original);
  await page.getByRole('button',{name:'翻译中…',exact:true}).waitFor();await page.getByRole('button',{name:'原文',exact:true}).click();await page.waitForTimeout(800);
  assert.equal(await page.getByRole('button',{name:'原文',exact:true}).getAttribute('aria-pressed'),'true');
  await page.evaluate(original=>{const f=window.workbenchFixture;f.problemOverrides.S={markdown:original,autoTranslate:true};f.changeProblem('S');},original);
  await page.getByRole('button',{name:'翻译中…',exact:true}).waitFor();await page.evaluate(()=>window.workbenchFixture.changeProblem('A'));await page.waitForTimeout(800);
  assert.equal(await page.getByRole('button',{name:'原文',exact:true}).getAttribute('aria-pressed'),'true');assert.doesNotMatch(await page.locator('.wb-statement').innerText(),/S 的中文题面/);
  assert.deepEqual(errors,[]);console.log('PASS: bundled Chinese and embedded diagram, future English auto-translation, manual original preference and late response isolation.');
}finally{await browser.close();await server.close();}
