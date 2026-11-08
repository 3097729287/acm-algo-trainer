import assert from 'node:assert/strict';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';

const output='../.backups/editorial-format-all-20261108/ui';
const data=await readFile('../.backups/editorial-format-all-20261108/reader-cases.json','utf8'),cases=JSON.parse(data);
await mkdir(output,{recursive:true});
const server=await createServer({optimizeDeps:{entries:['tests/legacy-editorial-fixture.html','tests/editorial-code-fixture.html']},server:{host:'127.0.0.1',port:0}});await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage(),errors=[],checks=[];
page.on('pageerror',error=>errors.push(error.message));
await page.route('**/tests/legacy-editorial-data.json',route=>route.fulfill({contentType:'application/json',body:data}));
await page.addInitScript(()=>Object.defineProperty(navigator,'clipboard',{value:{writeText:async value=>{window.copied=value;}},configurable:true}));
const base=`http://127.0.0.1:${server.httpServer.address().port}`;
try{
 for(const sample of [0,1,2])for(const width of [1260,430])for(const theme of ['dark','light']){
  await page.setViewportSize({width,height:900});
  await page.goto(`${base}/tests/legacy-editorial-fixture.html?sample=${sample}&theme=${theme}${sample===0?'&legacy':''}`);
  const reference=page.locator('.editorial-code').last();await reference.locator('.tok-keyword').first().waitFor();
  assert.equal(await reference.locator('code').textContent(),cases[sample].reference);
  assert(await reference.locator('.tok-number,.tok-string,.tok-comment').count()>0);
  await reference.getByRole('button',{name:'复制',exact:true}).click();
  assert.equal(await page.evaluate(()=>window.copied),cases[sample].reference);
  const bounds=await reference.locator('pre').evaluate(node=>({width:node.clientWidth,scroll:node.scrollWidth,windowWidth:innerWidth,bodyWidth:document.body.scrollWidth}));
  assert(bounds.bodyWidth<=width+1,JSON.stringify(bounds));
  const color=await reference.locator('.tok-keyword').first().evaluate(node=>({keyword:getComputedStyle(node).color,plain:getComputedStyle(node.closest('code')).color}));assert.notEqual(color.keyword,color.plain);
  if(sample===0){
   await reference.scrollIntoViewIfNeeded();await page.screenshot({path:`${output}/isbn-${width}-${theme}.png`});
   await page.getByRole('button',{name:'切换为详细题解',exact:true}).click();
   assert.equal(await page.locator('.editorial-code code').last().textContent(),cases[sample].detailedReference);
   await page.locator('.editorial-code .copy-code').last().click();assert.equal(await page.evaluate(()=>window.copied),cases[sample].detailedReference);
  }
  checks.push({sample:cases[sample].id,width,theme,storedFormatting:true,highlight:true,exactCopy:true,noPageOverflow:true});
 }
 // The legacy cxx alias must also participate in on-demand formatting of imports.
 await page.goto(base+'/tests/editorial-code-fixture.html?legacy');
 await page.waitForFunction(()=>document.querySelector('.editorial-code code')?.textContent===referenceFixture.expected);
 assert.equal(await page.evaluate(()=>referenceFixture.calls.length),1);
 assert(await page.locator('.editorial-code .tok-keyword').count()>0);
 assert.deepEqual(errors,[]);
 await writeFile(output+'/checks.json',JSON.stringify({checks,legacyAlias:true,errors},null,2));
 console.log(JSON.stringify({ok:true,scenarios:checks.length,defaultAndDetailed:true,legacyCxx:true,offlineStoredFormatting:true,exactCopy:true,errors}));
}finally{await browser.close();await server.close();}
