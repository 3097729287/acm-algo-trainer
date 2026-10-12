// Current empty/redirected official pages, bounded preparation and single-flight
// receipt polling. Every request is intercepted; these are fixture timings.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {chromium} from 'playwright';

let source=await readFile(new URL('../../desktop/official_page.js',import.meta.url),'utf8');
for(const [marker,file] of [['COMPILER_SELECTION','official_languages.js'],['NOWCODER_RECEIPTS','official_nowcoder.js'],['LUOGU_RECEIPTS','official_luogu.js']])source=source.replace(marker,await readFile(new URL('../../desktop/'+file,import.meta.url),'utf8'));
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const account='<nav class="navbar"><a href="/users/fixture">fixture</a></nav>';
const empty='<title>My Submissions - Contest</title>'+account+'<div class="panel-body">No Submissions</div>';
const acRow=id=>`<tr><td><a href="/contests/abc100/submissions/${id}">${id}</a><a href="/contests/abc100/tasks/abc100_a">A</a><a href="/users/fixture">fixture</a></td><td><span class="label">AC</span></td></tr>`;
const result={ok:false,realAccountSubmission:false};
async function fixture(platform, list=empty, delay=0){
  const page=await browser.newPage();const requests=[];let posted=false;
  const cf=platform==='Codeforces',origin=cf?'https://codeforces.com':'https://atcoder.jp';
  const original=origin+(cf?'/contest/123/problem/A':'/contests/abc100/tasks/abc100_a');
  const target=origin+(cf?'/contest/123/submit':'/contests/abc100/submit');
  await page.route('**/*',async route=>{
    const url=new URL(route.request().url());requests.push(url.pathname);
    if(url.pathname.endsWith('/submit'))return route.fulfill({contentType:'text/html',body:(cf?'<header id="header"><a href="/profile/fixture">fixture</a></header>':account)+`<form><input type="hidden" name="csrf_token" value="fixture-csrf"><select name="${cf?'submittedProblemIndex':'data.TaskScreenName'}"><option value="${cf?'A':'abc100_a'}">A</option></select><select name="${cf?'programTypeId':'data.LanguageId'}"><option value="54">GNU C++17</option></select><textarea name="sourceCode"></textarea><button type="submit">Submit</button></form><script>window.posts=[];document.querySelector('form').onsubmit=e=>{e.preventDefault();window.posts.push(Object.fromEntries(new FormData(e.target)))}</script>`});
    if(url.pathname==='/api/user.status'){
      await new Promise(r=>setTimeout(r,40));
      return route.fulfill({contentType:'application/json',body:JSON.stringify({status:'OK',result:[{id:110,author:{members:[{handle:'fixture'}]}}]})});
    }
    await new Promise(r=>setTimeout(r,delay));
    if(url.pathname==='/login')return route.fulfill({contentType:'text/html',body:'<input type="password">'});
    if(list==='redirect')return route.fulfill({status:302,headers:{location:origin+'/login'},body:''});
    return route.fulfill({contentType:'text/html',body:posted&&!cf?'<title>My Submissions</title>'+account+'<table><tr><th>Submission</th><th>Status</th></tr>'+acRow(2002)+'</table>':list});
  });
  await page.goto(target);await page.addScriptTag({content:source});
  await page.evaluate(({platform,original})=>{
    window.ctx={sessionId:'fixture',platform,originalUrl:original,problem:platform==='Codeforces'?'A':'abc100_a',code:'int main(){}',attempted:false};
    window.messages=[];window.report=value=>{window.messages.push(value);Object.assign(window.ctx,...['attempted','baseline','baselineKnown','baselineOwner','submissionId'].filter(k=>k in value).map(k=>({[k]:value[k]})));return Promise.resolve()};
  },{platform,original});
  return {page,requests,setPosted:()=>{posted=true}};
}
try{
  const first=await fixture('AtCoder');
  await first.page.evaluate(()=>tbOfficialPage(ctx,'inspect',report));
  await first.page.evaluate(()=>tbOfficialPage(ctx,'submit',report));
  await first.page.waitForFunction(()=>posts.length===1);
  assert.equal(await first.page.evaluate(()=>ctx.baselineKnown),true);
  assert.equal(await first.page.evaluate(()=>posts[0].csrf_token),'fixture-csrf');
  assert.equal(await first.page.evaluate(()=>posts[0].sourceCode),'int main(){}');
  first.setPosted();await first.page.evaluate(()=>tbOfficialPage(ctx,'inspect',report));
  await first.page.waitForFunction(()=>messages.some(m=>m.submissionId==='2002'&&m.verdict==='AC'));
  result.atcoderEmptyHistoryAndExactReceipt=true;await first.page.close();
  for(const invalid of [empty.replace('/users/fixture','/users/other'),empty.replace('My Submissions','All Submissions'),empty.replace('No Submissions','Unrecognized page'),'redirect']){
    const f=await fixture('AtCoder',invalid);
    await f.page.evaluate(()=>tbOfficialPage(ctx,'submit',report));
    await f.page.waitForFunction(()=>messages.some(m=>m.status==='error'));
    assert.equal(await f.page.evaluate(()=>posts.length),0);await f.page.close();
  }
  result.unknownOwnerPublicListAndLoginNeverSubmit=true;
  const fast=await fixture('Codeforces','<table class="status-frame-datatable"><tr><th>Submission</th></tr></table>',1200);
  const started=performance.now();
  await fast.page.evaluate(()=>tbOfficialPage(ctx,'inspect',report));
  await fast.page.evaluate(()=>tbOfficialPage(ctx,'submit',report));
  await fast.page.waitForFunction(()=>posts.length===1);
  result.cfFixturePrepareMs=Math.round(performance.now()-started);
  assert.ok(result.cfFixturePrepareMs<900,JSON.stringify(result));
  assert.ok(fast.requests.includes('/api/user.status'));await fast.page.close();
  const single=await fixture('AtCoder',empty,500);
  await single.page.evaluate(()=>{ctx.attempted=true;ctx.baselineKnown=true;ctx.baseline=[];ctx.baselineOwner='fixture';for(let i=0;i<25;i++)tbOfficialPage(ctx,'inspect',report)});
  await new Promise(r=>setTimeout(r,100));
  assert.equal(single.requests.filter(p=>p.endsWith('/submissions/me')).length,1);
  result.singleFlightPolls=true;await single.page.close();
  const loggedOut=await browser.newPage();await loggedOut.route('**/*',r=>r.fulfill({contentType:'text/html',body:'<header id="header"><a href="/enter">Enter</a><a href="/register">Register</a></header>'}));
  await loggedOut.goto('https://codeforces.com/');await loggedOut.addScriptTag({content:source});
  assert.equal(await loggedOut.evaluate(()=>tbOfficialPage({sessionId:'guest',platform:'Codeforces',originalUrl:'https://codeforces.com/contest/123/problem/A'},'inspect',()=>{}).status),'needs_login');
  result.cfHomepageRedirectDetected=true;result.ok=true;
  console.log(JSON.stringify(result));
}finally{await browser.close()}
