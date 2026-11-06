import assert from 'node:assert/strict';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const server=await createServer({optimizeDeps:{entries:['index.html']},cacheDir:'../.backups/interface-fixes-20261106/vite-keys',plugins:[{name:'keyboard-fixture',configureServer(s){s.middlewares.use('/key-fixture',async(_q,r)=>{r.setHeader('Content-Type','text/html');r.end(await s.transformIndexHtml('/key-fixture','<div id="root"></div><script type="module" src="/tests/bookmark-keys-fixture.jsx"></script>'));});}}],server:{host:'127.0.0.1',port:0}});await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage(),errors=[];page.on('pageerror',e=>{errors.push(e.message);console.error(e.message);});
try{
 await page.goto(server.resolvedUrls.local[0]+'key-fixture');await page.getByRole('tab',{name:'one',exact:true}).waitFor();
 for(const simple of [false,true]){
  if(simple)await page.evaluate(()=>keysFixture.simple());
  const tabs=page.getByRole('tab');await tabs.filter({hasText:'three'}).dragTo(tabs.filter({hasText:'one'}));
  assert.deepEqual(await tabs.allTextContents(),['three','one','two']);
  await page.getByRole('tab',{name:'one',exact:true}).click();
  await page.keyboard.press('ArrowRight');assert.equal(await page.evaluate(()=>keysFixture.page),2);assert.equal(await page.evaluate(()=>keysFixture.active),'one');
  await page.keyboard.press('Alt+ArrowRight');assert.equal(await page.evaluate(()=>keysFixture.active),'two');
  await page.keyboard.press('Alt+ArrowRight');assert.equal(await page.evaluate(()=>keysFixture.active),'three');
  await page.keyboard.press('Alt+ArrowLeft');assert.equal(await page.evaluate(()=>keysFixture.active),'two');
  await page.keyboard.press('ArrowLeft');assert.equal(await page.evaluate(()=>keysFixture.page),1);assert.equal(await page.evaluate(()=>keysFixture.active),'two');
  const search=page.getByRole('textbox',{name:'搜索',exact:true});await search.fill('query');await search.press('ArrowLeft');assert.equal(await page.evaluate(()=>keysFixture.page),1);assert.equal(await search.inputValue(),'query');await search.press('Alt+ArrowRight');assert.equal(await page.evaluate(()=>keysFixture.active),'three');assert.equal(await search.inputValue(),'query');
 }
 assert.deepEqual(errors,[]);console.log('PASS ordinary arrows paginate with bookmark focus; Alt arrows follow dragged SectionWorkspace and TopPageTabs order, wrap both ways, preserve inputs.');
}finally{await browser.close();await server.close();}
