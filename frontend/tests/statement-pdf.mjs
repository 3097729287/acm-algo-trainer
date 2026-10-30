import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const objects=['<< /Type /Catalog /Pages 2 0 R >>','<< /Type /Pages /Kids [3 0 R 5 0 R 7 0 R] /Count 3 >>'];
for(let page=1;page<=3;page++){
  const stream=`BT /F1 16 Tf 20 240 Td (Original PDF page ${page}) Tj ET`;
  objects.push(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 220 300] /Resources << /Font << /F1 9 0 R >> >> /Contents ${page*2+2} 0 R >>`,`<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`);
}
objects.push('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>');
let pdf='%PDF-1.4\n';const offsets=[0];
objects.forEach((object,index)=>{offsets.push(pdf.length);pdf+=`${index+1} 0 obj\n${object}\nendobj\n`;});
const start=pdf.length;pdf+=`xref\n0 ${objects.length+1}\n0000000000 65535 f \n`+offsets.slice(1).map(offset=>String(offset).padStart(10,'0')+' 00000 n \n').join('')+`trailer\n<< /Size ${objects.length+1} /Root 1 0 R >>\nstartxref\n${start}\n%%EOF`;
const base64=Buffer.from(pdf).toString('base64');
const fixture={id:'pdf-fixture',title:'Original PDF',url:'https://qoj.ac/problem/18307',markdown:'# Original PDF\n\nAn English problem statement.',statementAvailable:true,
  statementPdf:{data:'data:application/pdf;base64,'+base64,sha256:createHash('sha256').update(pdf).digest('hex'),pageCount:3},
  samples:[{input:'1\n2',output:'3'}],limits:{timeMs:2000,memoryMb:256},judge:{scope:'samples',cases:1},draft:'// preserve this draft',submissions:[],
  translation:{kind:'site',markdown:'# 中文\n\n保留已有中文题面。'}};
const server=await createServer({root,server:{host:'127.0.0.1',port:18794,strictPort:true,hmr:false}});await server.listen();
let browser;
try {
  browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
  const context=await browser.newContext({viewport:{width:1440,height:900}});
  const external=[],errors=[];
  await context.route('**/*',route=>{
    const u=new URL(route.request().url());
    if(u.origin==='http://127.0.0.1:18794'||['data:','blob:','chrome-extension:','extension:'].includes(u.protocol))return route.continue();
    external.push(u.href);return route.abort();
  });
  await context.addInitScript(value=>window.pdfFixtureData=value,fixture);
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:18794/tests/statement-pdf-fixture.html');
  const frame=page.locator('.wb-statement-pane iframe.wb-statement-pdf');await frame.waitFor();
  const left=await frame.boundingBox();const editor=await page.locator('.wb-code-pane').boundingBox();
  assert.ok(left.height>550&&left.width>300,'native PDF fills the left statement pane');
  assert.ok(left.x+left.width<=editor.x+1,'PDF and editable code remain side by side');
  assert.equal(await page.locator('.wb-statement img').count(),0,'PDF reading does not use PNG pages');
  const actual=await frame.evaluate(async node=>{
    const blob=await(await fetch(node.src.split('#')[0])).blob();
    return {mime:blob.type,base64:btoa(String.fromCharCode(...new Uint8Array(await blob.arrayBuffer())))};
  });
  assert.equal(actual.mime,'application/pdf');assert.equal(actual.base64,base64,'all three original pages reach the native viewer unchanged');
  await page.getByRole('group',{name:'题面语言',exact:true}).getByRole('button').click();
  await page.getByText('保留已有中文题面。',{exact:true}).waitFor();
  assert.equal(await frame.count(),0);
  await page.getByRole('group',{name:'题面语言',exact:true}).getByRole('button').click();await frame.waitFor();
  assert.ok((await page.locator('.cm-content').innerText()).includes('preserve this draft'));
  assert.deepEqual(external,[]);assert.deepEqual(errors,[]);
  console.log('PASS: native three-page PDF fills the left pane, exact original bytes load offline, Chinese toggles both ways, and the right editor draft survives.');
} finally {await browser?.close();await server.close();}
