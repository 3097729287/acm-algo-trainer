// Native-form contract fixtures. No real login, account or site POST is used.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
const folder='../desktop/';
let source=fs.readFileSync(folder+'official_page.js','utf8');
for(const [marker,file] of [['QOJ_ADAPTER','official_qoj.js'],['COMPILER_SELECTION','official_languages.js'],['NOWCODER_RECEIPTS','official_nowcoder.js'],['LUOGU_RECEIPTS','official_luogu.js']])source=source.replace(marker,fs.readFileSync(folder+file,'utf8'));
const nav='<div class="navbar"><a href="/user/profile/fixture">fixture</a><a href="/logout">Logout</a></div>';
const head='<table><thead><tr><th>ID</th><th>Problem</th><th>Submitter</th><th>Score</th></tr></thead><tbody>';
const row=(id,score='100',owner='fixture',problem='15032')=>`<tr><td><a href="/submission/${id}">${id}</a></td><td><a href="/problem/${problem}">Cipher</a></td><td><a href="/user/profile/${owner}">${owner}</a></td><td>${score}</td></tr>`;
const list=(rows,extra='')=>nav+head+rows+'</tbody></table>'+extra;
const fields=`<select name="answer_answer_language"><option>C++ 14</option><option>C++ 17</option><option>C++ 20</option><option>Python 3 (CPython 3.13)</option></select><input type="radio" name="answer_answer_upload_type" value="editor" checked><input type="radio" name="answer_answer_upload_type" value="file"><textarea name="answer_answer_editor">old draft</textarea><input type="hidden" name="_token" value="synthetic-native-token"><button type="submit" id="button-submit-answer">Submit</button>`;
const task=nav+`<a href="#tab-submit">Submit</a><form id="form-custom_test"><textarea name="custom_test_answer_editor">custom untouched</textarea><button id="button-submit-custom_test">Run</button></form><form id="form-answer" action="/problem/15032" method="post">${fields}</form>`;
const browser=await chromium.launch({channel:'msedge',headless:true});
let checks=0;
async function scenario(name,{pageHtml=task,baseline=list(row('10')+row('99','100','someone-else')),after=list(row('11')+row('10')),detail='',expect='AC',blocked=false,language='cpp17',code='#include <bits/stdc++.h>\nint main(){}',manual=false}={}){
 const context=await browser.newContext(),page=await context.newPage(),reports=[];let posts=0,formData='',current;
 const ctx={sessionId:name,platform:'QOJ',problem:'15032',originalUrl:'https://qoj.ac/problem/15032',code,language,attempted:false};
 await page.exposeFunction('report',value=>{reports.push(value);for(const key of ['attempted','baseline','baselineKnown','baselineOwner','submissionId'])if(key in value)ctx[key]=value[key];});
 await page.route('https://qoj.ac/**',route=>{
  const request=route.request(),url=new URL(request.url());
  if(request.method()==='POST'){posts++;formData=request.postData()||'';return route.fulfill({contentType:'text/html',body:after});}
  if(url.pathname==='/submissions')return route.fulfill(blocked?{status:403,body:'blocked'}:{contentType:'text/html',body:posts?after:baseline});
  if(url.pathname.startsWith('/submission/'))return route.fulfill({contentType:'text/html',body:detail||after});
  return route.fulfill({contentType:'text/html',body:pageHtml});
 });
 try{
  await page.goto('https://qoj.ac/problem/15032');await page.addScriptTag({content:source});
  await page.evaluate(({ctx,manual})=>tbOfficialPage(ctx,manual?'prepare':'submit',value=>window.report(value)),{ctx,manual});
  if(blocked||expect==='needs_login'||expect==='error'){
   await page.waitForFunction(()=>window.__tbQoj&&!window.__tbQoj.busy);assert.equal(posts,0,name);assert(reports.some(r=>r.status===(expect==='AC'?'error':expect)),JSON.stringify(reports));
  }else if(manual){
   await page.waitForFunction(()=>window.__tbQoj?.manualFilled);assert.equal(posts,0);assert(reports.some(r=>r.status==='awaiting_submit'));
   assert.equal(await page.locator('#form-custom_test textarea').inputValue(),'custom untouched');
   assert.equal(await page.locator('#form-answer textarea').inputValue(),code);
   await page.locator('#form-answer textarea').fill('manually edited');
   await page.evaluate(ctx=>tbOfficialPage(ctx,'prepare',value=>window.report(value)),ctx);
   await page.waitForFunction(()=>!window.__tbQoj.busy);
   assert.equal(await page.locator('#form-answer textarea').inputValue(),'manually edited','repeated preparation must preserve native edits');
  }else{
   await page.waitForFunction(()=>!document.querySelector('#form-answer'));
   assert.equal(posts,1,name);const params=new URLSearchParams(formData);
   assert.equal(params.get('_token'),'synthetic-native-token');assert.equal(params.get('answer_answer_editor').replaceAll('\r\n','\n'),code);
   assert.equal(params.get('answer_answer_language'),language==='python3'?'Python 3 (CPython 3.13)':code.includes('std::ranges')?'C++ 20':'C++ 17');
   assert.equal(params.get('custom_test_answer_editor'),null);
   await page.addScriptTag({content:source});
   await page.evaluate(ctx=>tbOfficialPage(ctx,'inspect',value=>window.report(value)),ctx);
   if(expect){
    const deadline=Date.now()+5000;while(!reports.some(r=>r.status==='finished')&&Date.now()<deadline)await page.waitForTimeout(30);
    assert(reports.some(r=>r.status==='finished'&&r.verdict===expect&&r.submissionId==='11'),JSON.stringify(reports));
   }else{await page.waitForTimeout(250);assert(!reports.some(r=>r.status==='finished'),JSON.stringify(reports));}
   await page.evaluate(ctx=>tbOfficialPage(ctx,'submit',value=>window.report(value)),ctx);await page.waitForTimeout(80);assert.equal(posts,1,'inspection/repeated commands cannot resubmit');
  }
  checks++;console.log('PASS',name);
 }finally{await page.unrouteAll({behavior:'wait'});await context.close();}
}
try{
 await scenario('native QOJ form and fresh owned AC');
 await scenario('C++20 chosen from own form',{code:'#include <ranges>\nint main(){ std::ranges::sort; }'});
 await scenario('Python3 chosen from own form',{language:'python3',code:'print(1)'});
 await scenario('manual prepare does not click native submit',{manual:true});
 await scenario('old AC is never a fresh result',{after:list(row('10')),expect:null});
 await scenario('another owner cannot supply receipt',{after:list(row('11','100','someone-else')),expect:null});
 await scenario('another task cannot supply receipt',{after:list(row('11','100','fixture','999')),expect:null});
 await scenario('numeric partial score reads actual failure',{after:list(row('11','50')),detail:list(row('11','50'),'<table><thead><tr><th>Status</th></tr></thead><tbody><tr><td>Time Limit Exceeded</td></tr></tbody></table>'),expect:'TLE'});
 await scenario('source and test-output text cannot invent WA',{after:list(row('11','0')),detail:list(row('11','0'),'<table><tr><td><pre>Wrong Answer</pre></td></tr></table>'),expect:null});
 await scenario('unknown numeric score never invents WA',{after:list(row('11','50')),expect:null});
 await scenario('unreadable baseline stops before submit',{blocked:true,expect:'error'});
 await scenario('footer author is not logged-in owner',{pageHtml:'<div class="navbar"><a href="/login">Login</a></div><footer><a href="/user/profile/fixture">fixture</a></footer>',expect:'needs_login'});
 console.log('PASS',checks,'QOJ contract fixtures; no original-site account or submission used.');
}finally{await browser.close();}
