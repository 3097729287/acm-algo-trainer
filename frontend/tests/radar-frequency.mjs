import assert from 'node:assert/strict';
import {createServer} from 'vite';
import {chromium} from 'playwright';

const server=await createServer({server:{host:'127.0.0.1',port:0}});
await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const errors=[],results=[];
try{
 for(const width of [960,1440]){
  const page=await browser.newPage({viewport:{width,height:1000}});
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/tests/ui-feedback-fixture.html?view=radar-frequency`);
  await page.getByRole('button',{name:/基础技巧，掌握/}).click();
  const expected=await page.evaluate(()=>window.radarFrequencyExpected),seen=[];
  for(let number=1;number<=3;number++){
   const visible=await page.locator('.radar-detail-row').evaluateAll(nodes=>nodes.map(node=>({name:node.children[0].firstChild.textContent,count:Number(node.children[2].textContent.split('/')[1].trim())})));
   const labels=await page.locator('svg [data-knowledge-name]').evaluateAll(nodes=>nodes.map(node=>node.dataset.knowledgeName));
   assert.deepEqual(visible,expected.slice((number-1)*12,number*12),'Each page follows distinct availability, not original taxonomy or progress');
   assert.deepEqual(labels,visible.map(node=>node.name),'Radar and table share exactly the same page order');
   seen.push(...visible);
   if(number<3)await page.getByRole('navigation',{name:'知识点分页'}).getByRole('button',{name:'下一页',exact:true}).click();
  }
  assert.equal(new Set(seen.map(node=>node.name)).size,27);
  assert.deepEqual(seen,expected);
  await page.getByRole('textbox',{name:'搜索知识点'}).fill('罕见');
  await page.waitForFunction(()=>document.querySelectorAll('.radar-detail-row').length===1);
  assert.equal(await page.locator('.radar-detail-row>button').first().textContent(),'杂项');
  assert.equal(await page.locator('.radar-detail-row').count(),1,'Search resets pagination and retains rare-member matching');
  await page.getByRole('textbox',{name:'搜索知识点'}).fill('');
  assert.equal((await page.locator('.radar-detail-row>button').first().textContent()).startsWith(expected[0].name),true);
  assert.equal(await page.getByRole('textbox',{name:'跳转页码'}).inputValue(),'1');
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
  results.push({width,pages:3,topics:seen.length,rareUnion:2});
  await page.close();
 }
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({ok:true,results,errors}));
}finally{await browser.close();await server.close();}
