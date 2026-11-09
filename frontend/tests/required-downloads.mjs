// Real backend/library/HTTP data through the production Workbench/ReadingLink.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {createServer} from 'vite';
import {chromium} from 'playwright';

const backend=process.env.TB_REQUIRED_FIXTURE_ORIGIN,token=process.env.TB_REQUIRED_FIXTURE_TOKEN;
assert.match(backend||'',/^http:\/\/127\.0\.0\.1:\d+$/);assert(token);
if(!process.argv[2])throw Error('Supply an isolated browser proof result path');
const output=path.resolve(process.argv[2]),root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
await fs.mkdir(path.dirname(output),{recursive:true});
const identity='luogu-training-P7351',sha='500178587e4c656cf2ef1b5ab009a1ce5d47d48a356a2004e7b65364052129b6';
async function api(route){const response=await fetch(backend+'/api/'+route,{headers:{'X-TB-Token':token}});assert.equal(response.status,200);return response.json();}
const problem=await api('problem?id='+identity);assert.equal(problem.id,identity);assert.equal(problem.problemType,'output-only');assert.equal(problem.localJudgeSupported,false);
const beforeDraft=problem.draft,beforeHistory=problem.submissions;
const original='https://gitee.com/w33z8kqrqk8zzzx33/dream-oi-extra/raw/master/down.zip';
assert.equal(problem.attachments[original].data,'/api/required-downloads/'+sha);
assert.equal(problem.attachments[original].bytes,42049784);
assert(!JSON.stringify(problem).includes('data:application/zip;base64,'));
assert(Buffer.byteLength(JSON.stringify(problem))<128*1024);
process.env.TB_API_URL=backend;
const port=Number(process.env.TB_REVIEW_PORT||18831),origin=`http://127.0.0.1:${port}`;
const server=await createServer({root,cacheDir:path.join(path.dirname(output),'vite-review'),optimizeDeps:{entries:['tests/statement-pdf-fixture.html']},server:{host:'127.0.0.1',port,strictPort:true,hmr:false}});
await server.listen();let browser;const errors=[],external=[];
try{
 browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:900}});
 page.on('pageerror',error=>errors.push(error.message));page.on('request',request=>{if(/^https?:/.test(request.url())&&!request.url().startsWith(origin+'/'))external.push(request.url());});
 await page.addInitScript(value=>{window.pdfFixtureData=value;window.pdfFixtureProblemId=value.id;},problem);
 await page.goto(origin+'/tests/statement-pdf-fixture.html');await page.locator('.wb-statement').waitFor();
 assert.equal(await page.locator('.wb-statement .katex-error').count(),0);
 const link=page.getByRole('link',{name:'点击下载输入数据。',exact:true});assert.equal(await link.getAttribute('href'),'/api/required-downloads/'+sha);assert.equal(await link.getAttribute('download'),'down.zip');
 const promised=page.waitForEvent('download');await link.scrollIntoViewIfNeeded();await link.click();
 const download=await promised,stream=await download.createReadStream();const hash=createHash('sha256');let bytes=0;
 for await(const chunk of stream){hash.update(chunk);bytes+=chunk.length;}
 assert.equal(await download.failure(),null);assert.equal(bytes,42049784);assert.equal(hash.digest('hex'),sha);assert.equal(download.suggestedFilename(),'down.zip');
 const after=await api('problem?id='+identity);assert.equal(after.id,identity);assert.equal(after.draft,beforeDraft);assert.deepEqual(after.submissions,beforeHistory);
 const status=await api('required-downloads/'+sha+'/status');assert.equal(status.cached,true);assert.equal(status.verifiedBytes,42049784);
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 await page.screenshot({path:output.replace(/\.json$/,'.png')});
 const result={realBackendProblemEndpoint:true,realWorkbench:true,realReadingLink:true,originalId:identity,originalDraftAndHistoryPreserved:true,downloadedBytes:bytes,sha256:sha,cached:status.cached,verifiedBytes:status.verifiedBytes,problemJsonBytes:Buffer.byteLength(JSON.stringify(problem)),archiveBase64InJson:false,browserErrors:0,formulaErrors:0,externalRequests:0};
 await fs.writeFile(output,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
}finally{await browser?.close();await server.close();}
