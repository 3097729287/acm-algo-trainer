import assert from 'node:assert/strict';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const vite=await createServer({server:{host:'127.0.0.1',port:0}});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage();
try{
 await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/lectures-lifecycle-fixture.html`);
 await page.locator('.lectures-list button').click();
 await page.locator('.lecture-markdown .katex').waitFor();
 await page.getByRole('button',{name:'从零讲全屏',exact:true}).click();
 await page.locator('.lecture-reading-full').waitFor();
 await page.getByRole('button',{name:'退出从零讲全屏',exact:true}).click();
 assert.equal(await page.locator('.lecture-reading-full').count(),0);
 console.log('Lecture selection and fullscreen remain responsive.');
}finally{await browser.close();await vite.close();}
