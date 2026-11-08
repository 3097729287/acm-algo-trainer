// Reviewed optional links remain visible external links, never fake downloads.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createServer} from 'vite';
import {chromium} from 'playwright';

const [input,output]=process.argv.slice(2);
if(!input||!output)throw new Error('Supply isolated public fixtures and a result file');
const rows=JSON.parse(await fs.readFile(input,'utf8')).filter(row=>row.optionalExternalResources?.length);
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const port=Number(process.env.TB_REVIEW_PORT||18831),base=`http://127.0.0.1:${port}`;
const server=await createServer({root,optimizeDeps:{entries:['tests/statement-pdf-fixture.html']},server:{host:'127.0.0.1',port,strictPort:true,hmr:false}});
await server.listen();let browser;const checked=[],errors=[],external=[];
try{
 browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
 const context=await browser.newContext({viewport:{width:1280,height:800}});
 await context.route('**/*',route=>{
  const url=new URL(route.request().url());
  if(url.origin===base||['blob:','data:'].includes(url.protocol))return route.continue();
  external.push(url.href);return route.abort();
 });
 for(const row of rows){
  const page=await context.newPage();page.on('pageerror',error=>errors.push(error.message));
  await page.addInitScript(value=>window.pdfFixtureData=value,row);await page.goto(base+'/tests/statement-pdf-fixture.html');
  await page.locator('.wb-code-pane').waitFor();
  for(const language of row.translation?['original','chinese']:['original']){
   if(language==='chinese')await page.getByRole('button',{name:'原文',exact:true}).click();
   const statement=page.locator('.wb-statement');await statement.waitFor();
   const links=await statement.locator('a[href]').evaluateAll(nodes=>nodes.map(node=>({href:node.getAttribute('href'),download:node.hasAttribute('download'),label:node.textContent})));
   const text=await statement.textContent();
   for(const optional of row.optionalExternalResources){
    const matching=links.filter(link=>link.href===optional.url);
    assert(matching.length>0,row.originalId+' original optional source link retained');
    assert(matching.every(link=>!link.download&&link.label.trim()),row.originalId+' uncached link must remain an honest external link');
    assert(!row.attachments?.[optional.url]?.data,row.originalId+' no fabricated cache payload');
    assert(text.includes(optional.availability.httpStatus===403?'403':'99,667,903'),row.originalId+' visible availability/size notice');
    checked.push({id:row.originalId,language,url:optional.url,originalLinkRetained:true,fakeCachedDownload:false,availabilityNoticeVisible:true});
   }
  }
  await page.close();
 }
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 const result={checked,browserErrors:0,externalRequests:0};
 await fs.writeFile(output,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
}finally{await browser?.close();await server.close();}
