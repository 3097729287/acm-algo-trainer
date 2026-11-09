import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {mkdir,writeFile} from 'node:fs/promises';
import {readFileSync,realpathSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {createInterface} from 'node:readline';
import {fileURLToPath} from 'node:url';
import {createServer} from 'vite';
import react from '@vitejs/plugin-react';
import {chromium} from 'playwright';

// Real React/CodeMirror -> real loopback HTTP -> real TrainingService/SQLite.
// Only explicit offline native receipts are injected. No actual OJ is visited.
const frontend=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const root=resolve(frontend,'..');
const out=resolve(root,'.backups/review-latest-ac-20261109/browser',String(Date.now()));
await mkdir(out,{recursive:true});
let native,nativeOrigin='',nativeErrors='',restarts=0;const unexpectedApi=[];
async function startNative(){
 native=spawn(process.env.TB_PYTHON||'python',['-B',resolve(frontend,'tests/review-editor-api.py')],{
  cwd:root,windowsHide:true,env:{...process.env,TB_OFFLINE:'1',PYTHONDONTWRITEBYTECODE:'1',PYTHONIOENCODING:'utf-8',TB_REVIEW_TEST_STATE:resolve(out,'state')},stdio:['pipe','pipe','pipe']});
 native.stderr.on('data',value=>nativeErrors+=value.toString());
 const lines=createInterface({input:native.stdout});
 const first=await Promise.race([once(lines,'line').then(([line])=>JSON.parse(line)),once(native,'exit').then(([code])=>{throw Error('Native fixture exited before readiness: '+code);})]);
 assert.match(first.endpoint,/^http:\/\/127\.0\.0\.1:\d+$/);nativeOrigin=first.endpoint;
}
async function stopNative(){
 if(!native||native.exitCode!==null)return;
 const ended=once(native,'exit');native.stdin.end('stop\n');await ended;
}
async function call(path,body){
 const response=await fetch(nativeOrigin+'/'+path,{method:body?'POST':'GET',...(body?{headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{})});
 const value=await response.json();assert.equal(response.status,200,JSON.stringify(value));return value;
}
await startNative();
const vite=await createServer({configFile:false,root:frontend,
 cacheDir:resolve(out,'vite'),optimizeDeps:{entries:['tests/review-editor-fixture.html']},
 define:{__TB_VERSION__:JSON.stringify(readFileSync(resolve(root,'VERSION'),'utf8').trim())},
 resolve:{alias:{'@':resolve(frontend,'src')}},
 plugins:[react(),{name:'isolated-native-review-api',configureServer(server){server.middlewares.use(async(request,response,next)=>{
  if(!request.url?.startsWith('/api/'))return next();
  // No default /api proxy exists: this route can only reach our current child.
  try{const chunks=[];for await(const chunk of request)chunks.push(chunk);const body=Buffer.concat(chunks);
   const upstream=await fetch(nativeOrigin+request.url.slice(4),{method:request.method,headers:{'Content-Type':'application/json'},...(body.length?{body}:{})});
   if(upstream.status>=400&&!(request.url==='/api/draft'&&upstream.status===503))unexpectedApi.push({path:request.url,status:upstream.status});
   response.writeHead(upstream.status,{'Content-Type':'application/json'});response.end(await upstream.text());
  }catch{response.writeHead(502,{'Content-Type':'application/json'});response.end(JSON.stringify({error:'Isolated native transport unavailable'}));}
 });}}],server:{host:'127.0.0.1',port:0,fs:{allow:[frontend,realpathSync(resolve(frontend,'node_modules'))]}}});
await vite.listen();
const origin=`http://127.0.0.1:${vite.httpServer.address().port}`;
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:960}});page.setDefaultTimeout(15000);
const errors=[],checks=[];page.on('pageerror',error=>errors.push(error.message));
await page.route('**/*',route=>{const url=new URL(route.request().url());return url.origin===origin||['data:','blob:'].includes(url.protocol)?route.continue():route.abort('blockedbyclient');});
const editor=()=>page.locator('.cm-content[contenteditable=true]');
const waitCode=code=>page.waitForFunction(code=>document.querySelector('.cm-content')?.innerText.trimEnd()===code.trimEnd(),code);
const open=task=>page.evaluate(task=>reviewEditorFixture.open(task),task);
async function save(code,task){
 await editor().fill(code);await editor().press('Control+s');
 for(let i=0;i<100;i++){const state=await call('fixture/state');if(state.drafts.some(d=>d.context==='review:'+task.id&&d.code===code))return;await page.waitForTimeout(40);}
 throw Error('Review draft did not reach real SQLite');
}
async function accept(code,task,language){
 await save(code,task);await page.getByRole('button',{name:'提交',exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('.wb-result-summary')?.textContent.includes('AC'));
 const state=await call('fixture/state'),receipt=state.submissions.findLast(s=>s.code===code&&s.scope==='official'&&s.verdict==='AC');
 assert(receipt);assert.equal(receipt.language,language);return receipt;
}
let result={ok:false,realEditor:true,realNativeHttp:true,realSqlite:true,syntheticNativeReceipts:true,liveOjSubmissions:0,normalAccountOrInstallTouched:false};
try{
 await page.goto(origin+'/tests/review-editor-fixture.html');await waitCode('int main() {} // previous ordinary template');
 const one=await call('fixture/next-review',{});await open(one);await editor().waitFor();
 await page.waitForFunction(()=>!document.querySelector('.cm-content')?.textContent.includes('previous ordinary template'));
 const cpp='int main() { return 42; } // first accepted review';
 const first=await accept(cpp,one,'cpp17');await open(null);await waitCode(cpp);
 assert.equal(await page.getByRole('combobox',{name:'编程语言',exact:true}).inputValue(),'cpp17');
 const oldProblem=await call('problem?id=fixture%3A%3AA');assert.equal(oldProblem.draft,cpp);
 checks.push('first official rewrite replaces the old ordinary editor projection');
 await page.screenshot({path:resolve(out,'first-cpp.png')});

 const two=await call('fixture/next-review',{});await open(two);
 await page.waitForFunction(()=>!document.querySelector('.cm-content')?.textContent.includes('first accepted review'));
 await page.getByRole('combobox',{name:'编程语言',exact:true}).selectOption('python3');
 const python='print(42)  # second accepted review\n';
 const second=await accept(python,two,'python3');await open(null);await waitCode(python);
 assert.equal(await page.getByRole('combobox',{name:'编程语言',exact:true}).inputValue(),'python3');
 checks.push('second rewrite restores the latest actual accepted source and Python language');
 const physical=await call('fixture/state');
 assert.equal(physical.drafts.find(d=>d.context==='').code,'int main() {} // previous ordinary template');
 assert.equal(physical.drafts.find(d=>d.context==='review:'+one.id).code,cpp);
 assert.equal(physical.drafts.find(d=>d.context==='review:'+two.id).code,python);

 await stopNative();await startNative();restarts++;await page.reload();await waitCode(python);
 assert.equal(await page.getByRole('combobox',{name:'编程语言',exact:true}).inputValue(),'python3');
 await call('fixture/late',{code:cpp,language:'cpp17',reviewId:one.id,submittedAt:first.submittedAt,remote:'990001'});
 assert.equal((await call('problem?id=fixture%3A%3AA')).draftSubmissionId,second.id);
 checks.push('Python process restart and a late older official receipt preserve the newest code');
 await page.screenshot({path:resolve(out,'restored-python-after-process-restart.png')});

 // A captured old ordinary response resolves after a fresh editor mounted.
 await open(one);await waitCode(cpp);
 let releaseOld,seenOld;const captured=new Promise(resolve=>seenOld=resolve),held=new Promise(resolve=>releaseOld=resolve);let firstRead=true;
 const stale=async route=>{if(firstRead){firstRead=false;seenOld();await held;await route.fulfill({json:oldProblem});}else await route.continue();};
 await page.route('**/api/problem?*',stale);await open(null);await captured;
 await open(two);await waitCode(python);await open(null);await waitCode(python);
 await call('fixture/fail-drafts',{enabled:true});
 const privateDraft='print("private unsent experiment")\n';await editor().fill(privateDraft);await editor().press('Control+s');
 const key='tb.draft.v3.review-editor-isolated-owner.solo.fixture%3A%3AA';
 await page.waitForFunction(key=>JSON.parse(localStorage.getItem(key)||'{}').dirty===true,key);
 releaseOld();await page.waitForTimeout(150);await waitCode(privateDraft);
 assert.equal(await page.getByRole('combobox',{name:'编程语言',exact:true}).inputValue(),'python3');
 await page.unroute('**/api/problem?*',stale);
 checks.push('a late older problem response cannot replace current input or language');

 await page.reload();await waitCode(privateDraft);
 const dirty=await page.evaluate(key=>JSON.parse(localStorage.getItem(key)),key);
 assert(dirty.dirty&&dirty.modifiedAt<Date.parse(second.submittedAt),'The older unsent input wins specifically over an accepted-code projection');
 assert.equal((await call('fixture/state')).drafts.find(d=>d.context==='').code,'int main() {} // previous ordinary template');
 checks.push('unsent ordinary input survives reload while all physical draft contexts remain intact');
 assert.deepEqual(errors,[]);assert.deepEqual(unexpectedApi,[]);
 result={...result,ok:true,checks,pythonProcessRestarts:restarts,errors,unexpectedApi};
 await page.screenshot({path:resolve(out,'dirty-input-preserved.png')});
}catch(error){result={...result,error:error.message,errorClass:error.name,checks,errors};await page.screenshot({path:resolve(out,'failure.png')});throw error;}
finally{
 await writeFile(resolve(out,'result.log'),JSON.stringify(result,null,2)+'\n');
 await writeFile(resolve(out,'native-stderr.log'),nativeErrors);
 console.log(JSON.stringify({...result,receipt:resolve(out,'result.log')}));
 await browser.close();await vite.close();await stopNative();
}
