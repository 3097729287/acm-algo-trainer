import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
if(!process.argv[2]||!process.argv[3])throw new Error('Supply isolated PDF corpus JSON and result path');
const rows=JSON.parse(await fs.readFile(process.argv[2],'utf8'));
const server=await createServer({root,server:{host:'127.0.0.1',port:18794,strictPort:true,hmr:false}});await server.listen();
let browser;const verified=[],external=[];
try{
  browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
  const context=await browser.newContext({viewport:{width:1440,height:900}});
  await context.route('**/*',route=>{
    const u=new URL(route.request().url());
    if(u.origin==='http://127.0.0.1:18794'||['data:','blob:','chrome-extension:','extension:'].includes(u.protocol))return route.continue();
    external.push(u.href);return route.abort();
  });
  for(const row of rows){
    const page=await context.newPage();await page.addInitScript(value=>window.pdfFixtureData=value,row);
    await page.goto('http://127.0.0.1:18794/tests/statement-pdf-fixture.html');
    const frame=page.locator('.wb-statement-pane iframe.wb-statement-pdf');await frame.waitFor();
    const box=await frame.boundingBox(),editor=await page.locator('.wb-code-pane').boundingBox();
    assert.ok(box.height>550&&box.x+box.width<=editor.x+1,row.originalId);
    const actual=await frame.evaluate(async node=>{
      const response=await fetch(node.src.split('#')[0]);const bytes=await response.arrayBuffer();
      return {mime:response.headers.get('content-type'),sha256:[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('')};
    });
    assert.equal(actual.mime,'application/pdf');assert.equal(actual.sha256,row.statementPdf.sha256,row.originalId);
    verified.push({id:row.originalId,sha256:actual.sha256,pages:row.statementPdf.pageCount});await page.close();
  }
  assert.deepEqual(external,[]);await fs.writeFile(process.argv[3],JSON.stringify({verified,externalRequests:external.length},null,2));
  console.log(JSON.stringify({verified:verified.length,externalRequests:0}));
}finally{await browser?.close();await server.close();}
