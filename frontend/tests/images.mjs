import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import { chromium } from 'playwright';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const server=await createServer({root,server:{host:'127.0.0.1',port:18774,strictPort:true}});
await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1120,height:850}});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
try {
  await page.goto('http://127.0.0.1:18774/tests/images-fixture.html');
  await page.getByRole('button',{name:'放大图片：树结构'}).first().waitFor();
  for(const summary of await page.locator('.lecture-disclosure summary').all()) await summary.click();
  await page.getByRole('button',{name:'放大图片：引用式配图'}).waitFor();
  assert.equal(await page.evaluate(()=>window.inlineLectureRequests),0);
  assert.equal(await page.getByText('不应重复的完整上下文').count(),0);
  assert.equal(await page.getByText('原题思路只出现一次。',{exact:true}).count(),1);
  const buttons=page.locator('.reading-image-open');
  for(let i=0;i<await buttons.count();i++){
    await buttons.nth(i).scrollIntoViewIfNeeded();
    await buttons.nth(i).locator('img').evaluate(img=>img.decode());
  }
  const decoded=await page.locator('.reading-image-open img').evaluateAll(nodes=>nodes.map(n=>({alt:n.alt,width:n.naturalWidth,height:n.naturalHeight})));
  assert.ok(decoded.length>=20);
  assert.ok(decoded.every(n=>n.width>0&&n.height>0));
  assert.equal(await page.getByRole('status').filter({hasText:'图片未能加载：缺图'}).count(),1);
  assert.ok(!await page.getByRole('link',{name:'不安全链接'}).getAttribute('href'));
  const trigger=page.getByRole('button',{name:'放大图片：树结构'}).first();
  await trigger.click();
  await page.getByRole('dialog',{name:'树结构',exact:true}).waitFor({state:'visible'});
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('dialog[open]').count(),0);
  assert.ok(await trigger.evaluate(node=>node===document.activeElement));
  await trigger.click();await page.getByRole('button',{name:'关闭',exact:true}).click();
  await page.setViewportSize({width:390,height:844});
  await trigger.scrollIntoViewIfNeeded();
  assert.ok(await trigger.evaluate(n=>n.getBoundingClientRect().width<=390));
  await trigger.click();
  assert.ok(await page.locator('dialog[open] .reading-image-full').evaluate(n=>n.scrollWidth>n.clientWidth));
  await page.keyboard.press('Escape');
  await page.setViewportSize({width:1120,height:850});await page.evaluate(()=>window.scrollTo(0,0));
  fs.mkdirSync(path.join(root,'tests/screenshots'),{recursive:true});
  await page.screenshot({path:path.join(root,'tests/screenshots/illustrated-reading.png')});
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({decoded:decoded.length,formats:[...new Set(decoded.map(d=>d.alt))],zoom:true,keyboard:true,mobile:true,errors}));
} finally {await browser.close();await server.close();}
