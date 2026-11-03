import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const out=path.resolve(root,'../.backups/next-152/chinese-pdf-ui');await mkdir(out,{recursive:true});
const pdf=await readFile(path.resolve(root,'../backend/fixtures/gym-chinese-booklet.pdf'));
const fixture=process.env.TB_REAL_PDF_FIXTURE?JSON.parse(await readFile(process.env.TB_REAL_PDF_FIXTURE,'utf8')):{
  id:'pdf-fixture',title:'Addition',url:'https://codeforces.com/gym/123456/problem/A',
  markdown:'# Addition\n\nGiven two integers, print their sum.',statementAvailable:true,
  samples:[{input:'1 2',output:'3'}],limits:{timeMs:1000,memoryMb:256},
  translation:{kind:'site',sourceLanguage:'en',targetLanguage:'zh-CN',markdown:'中文原版题面。',
    statementPdf:{data:'data:application/pdf;base64,'+pdf.toString('base64'),sha256:createHash('sha256').update(pdf).digest('hex'),pageCount:5}}
};
fixture.judge={scope:'samples',cases:fixture.samples.length};fixture.draft='// retained draft';fixture.submissions=[];
const expected=fixture.translation.statementPdf.sha256;
const server=await createServer({root,cacheDir:path.join(out,'vite'),server:{host:'127.0.0.1',port:0,hmr:false}});await server.listen();
const origin=server.resolvedUrls.local[0];let context;const report={ok:false,sourceSha256:expected,checks:[]};
try{
  context=await chromium.launchPersistentContext(path.join(out,'profiles',String(Date.now())),{
    channel:process.env.CI?undefined:'msedge',headless:process.env.TB_PDF_HEADFUL!=='1',viewport:{width:1440,height:960}});
  const external=[],errors=[];
  await context.route('**/*',route=>{
    const url=new URL(route.request().url());
    if(url.origin===new URL(origin).origin||['blob:','data:','chrome-extension:','extension:'].includes(url.protocol))return route.continue();
    external.push(url.href);return route.abort();
  });
  await context.addInitScript(value=>window.pdfFixtureData=value,fixture);
  const page=await context.newPage();page.on('pageerror',error=>errors.push(error.message));
  await page.goto(origin+'tests/statement-pdf-fixture.html');
  const editor=page.locator('.cm-content'),frame=page.locator('.wb-statement-pdf');
  await editor.waitFor();assert.equal(await frame.count(),0,'English remains the default');
  await editor.fill('// personal draft survives the PDF switch\nint main(){return 42;}');
  const toggle=page.getByRole('group',{name:'题面语言',exact:true}).getByRole('button');
  for(const width of [1440,960]){
    await page.setViewportSize({width,height:960});await toggle.click();await page.locator('.wb-pdf-page[data-ready="true"]').first().waitFor();
    const actual=await frame.getByRole('link',{name:'下载 PDF',exact:true}).evaluate(async node=>{
      const response=await fetch(node.href),blob=await response.blob();
      const bytes=new Uint8Array(await crypto.subtle.digest('SHA-256',await blob.arrayBuffer()));
      return {mime:blob.type,sha256:[...bytes].map(x=>x.toString(16).padStart(2,'0')).join('')};
    });
    assert.deepEqual(actual,{mime:'application/pdf',sha256:expected});
    assert.equal(await page.locator('.wb-statement img').count(),0);
    const paper=page.locator('.wb-pdf-page').first(),pane=page.locator('.wb-statement');
    assert.equal(await page.locator('.wb-pdf-page').count(),fixture.translation.statementPdf.pageCount);
    assert.ok((await paper.boundingBox()).width<=(await pane.boundingBox()).width,'the entire PDF page fits the reading column');
    assert.ok((await paper.locator('.wb-pdf-text-layer').innerText()).length>15,'original PDF text can be selected');
    const ink=await paper.locator('canvas').evaluate(canvas=>{const data=canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height).data;let total=0;for(let i=0;i<data.length;i+=4)if(data[i]<180&&data[i+1]<180&&data[i+2]<180&&data[i+3]>0)total++;return total;});
    assert.ok(ink>100,'the page contains painted original content');
    assert.ok((await editor.innerText()).includes('personal draft survives'));
    await page.screenshot({path:path.join(out,`chinese-${width}.png`)});
    await toggle.click();await frame.waitFor({state:'detached'});
    assert.ok((await editor.innerText()).includes('return 42'));
  }
  assert.deepEqual(external,[]);assert.deepEqual(errors,[]);
  report.ok=true;report.checks=['English default retained','original PDF bytes retained',
    'PDF pages painted at both reading widths without clipping','selectable original text',
    'offline switching without AI or original-site request','personal code preserved'];
  console.log('PASS: '+report.checks.join('; '));
}catch(error){report.error=error.stack;throw error;}
finally{await writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2));await context?.close();await server.close();}
