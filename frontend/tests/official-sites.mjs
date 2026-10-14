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
  return {page,requests,setPosted:()=>{posted=true},setList:value=>{list=value}};
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
  const pending=await fixture('AtCoder');
  await pending.page.evaluate(()=>{document.querySelector('form').insertAdjacentHTML('beforeend','<div class="cf-challenge" data-sitekey="fixture"><iframe src="/challenge-fixture"></iframe><input type="hidden" name="cf-turnstile-response" value=""></div>');tbOfficialPage(ctx,'submit',report);});
  await pending.page.waitForFunction(()=>messages.some(m=>m.status==='loading'&&m.attempted===false));
  assert.equal(await pending.page.evaluate(()=>posts.length),0);
  await pending.page.evaluate(()=>{window.__tbSubmissionWork.verifyingAt=Date.now()-31000;tbOfficialPage(ctx,'submit',report);});
  await pending.page.waitForFunction(()=>messages.some(m=>m.status==='needs_verification'&&m.attempted===false));
  assert.equal(await pending.page.evaluate(()=>posts.length),0);
  await pending.page.evaluate(()=>{document.querySelector('[name="cf-turnstile-response"]').value='fixture-site-token';tbOfficialPage(ctx,'submit',report);});
  await pending.page.waitForFunction(()=>posts.length===1);
  assert.equal(await pending.page.evaluate(()=>posts[0]['cf-turnstile-response']),'fixture-site-token');
  await pending.page.close();result.atcoderVerificationBeforeDispatch=true;
  const expiring=await fixture('AtCoder',empty,400);
  await expiring.page.evaluate(()=>{
    document.querySelector('form').insertAdjacentHTML('beforeend','<div class="cf-turnstile"><iframe src="/challenge-fixture"></iframe><input type="hidden" name="cf-turnstile-response" value="fixture-site-token"></div>');
    document.querySelectorAll('select').forEach(e=>e.addEventListener('change',()=>{throw new Error('Already selected AtCoder task/language must not be reset')}));
    tbOfficialPage(ctx,'submit',report);
    setTimeout(()=>{document.querySelector('[name="cf-turnstile-response"]').value=''},50);
  });
  await expiring.page.waitForFunction(()=>messages.some(m=>m.status==='loading'&&m.attempted===false));
  assert.equal(await expiring.page.evaluate(()=>posts.length),0);
  await expiring.page.evaluate(()=>{document.querySelector('[name="cf-turnstile-response"]').value='fixture-renewed-token';tbOfficialPage(ctx,'submit',report)});
  await expiring.page.waitForFunction(()=>posts.length===1);
  assert.equal(await expiring.page.evaluate(()=>posts[0]['cf-turnstile-response']),'fixture-renewed-token');
  await expiring.page.close();result.atcoderExpiredTokenWaitsForRenewal=true;
  const recover=await fixture('AtCoder','Temporary upstream error');
  await recover.page.evaluate(()=>tbOfficialPage(ctx,'submit',report));
  await recover.page.waitForFunction(()=>messages.some(m=>m.status==='error'));
  recover.setList(empty);
  await recover.page.evaluate(()=>tbOfficialPage(ctx,'submit',report));
  await recover.page.waitForFunction(()=>posts.length===1);
  await recover.page.close();result.atcoderFailedSnapshotCanRecover=true;
  const invalidForm=await fixture('AtCoder');
  await invalidForm.page.evaluate(()=>{document.querySelector('form').insertAdjacentHTML('beforeend','<input name="required-field" required>');tbOfficialPage(ctx,'submit',report);});
  await invalidForm.page.waitForFunction(()=>messages.some(m=>m.status==='error'&&m.attempted===false&&m.message.includes('表单未通过校验')));
  assert.equal(await invalidForm.page.evaluate(()=>posts.length),0);await invalidForm.page.close();result.atcoderInvalidFormNoPost=true;
  const rejected=await fixture('AtCoder');
  await rejected.page.evaluate(()=>{ctx.attempted=true;ctx.baselineKnown=true;ctx.baseline=[];document.querySelector('form').insertAdjacentHTML('beforeend','<div class="alert alert-danger">Invalid submission verification</div>');window.rejection=tbOfficialPage(ctx,'inspect',report);});
  assert.equal(await rejected.page.evaluate(()=>rejection.status),'error');
  assert.equal(await rejected.page.evaluate(()=>rejection.attempted),false);
  assert.match(await rejected.page.evaluate(()=>rejection.message),/Invalid submission verification/);
  await rejected.page.close();result.atcoderRejectionDisplayed=true;
  const existingError=await fixture('AtCoder');
  await existingError.page.evaluate(()=>{document.querySelector('form').insertAdjacentHTML('beforeend','<div class="alert alert-danger">Submission is unavailable</div>');tbOfficialPage(ctx,'submit',report);});
  await existingError.page.waitForFunction(()=>messages.some(m=>m.status==='error'&&m.attempted===false));
  assert.equal(await existingError.page.evaluate(()=>posts.length),0);
  await existingError.page.close();result.atcoderExistingRejectionNoPost=true;
  const fast=await fixture('Codeforces','<table class="status-frame-datatable"><tr><th>Submission</th></tr></table>',1200);
  const started=performance.now();
  await fast.page.evaluate(()=>tbOfficialPage(ctx,'inspect',report));
  await fast.page.evaluate(()=>tbOfficialPage(ctx,'submit',report));
  await fast.page.waitForFunction(()=>posts.length===1);
  result.cfFixturePrepareMs=Math.round(performance.now()-started);
  assert.ok(result.cfFixturePrepareMs<900,JSON.stringify(result));
  assert.ok(fast.requests.includes('/api/user.status'));await fast.page.close();
  for (const variant of ['default-button','cf-input-button','external-owner','unrelated-form']) {
    const f=await fixture('Codeforces','<table class="status-frame-datatable"><tr><th>Submission</th></tr></table>');
    await f.page.evaluate(variant=>{
      const form=document.querySelector('form'),button=form.querySelector('button');form.id='submitForm';
      if(variant==='default-button')button.removeAttribute('type');
      if(variant==='cf-input-button') { button.outerHTML='<input type="button" class="submit" value="Submit">';form.querySelector('.submit').onclick=()=>form.requestSubmit(); }
      if(variant==='external-owner') { const textarea=form.querySelector('textarea');textarea.setAttribute('form','submitForm');form.before(textarea); }
      if(variant==='unrelated-form')form.insertAdjacentHTML('beforebegin','<form id="search"><textarea id="code-search"></textarea><button type="button">Search</button></form>');
      tbOfficialPage(ctx,'submit',report);
    },variant);
    await f.page.waitForFunction(()=>posts.length===1);
    assert.equal(await f.page.evaluate(()=>posts[0].sourceCode),'int main(){}');
    assert.equal(await f.page.evaluate(()=>messages.filter(m=>m.attempted===true).length),1);
    await f.page.close();
  }
  result.cfNativeButtonsAndFormOwnership=true;
  const locked=await fixture('Codeforces','<table class="status-frame-datatable"><tr><th>Submission</th></tr></table>');
  const lockStarted=performance.now();
  await locked.page.evaluate(()=>{
    const button=document.querySelector('button');button.id='singlePageSubmitButton';button.disabled=true;
    window.lockRequests=1;
    document.querySelectorAll('select').forEach(e=>e.addEventListener('change',()=>{window.lockRequests++;throw new Error('Selected CF task/language must not restart problemLock')}));
    setTimeout(()=>{button.disabled=false},500);
    tbOfficialPage(ctx,'submit',report);
  });
  await locked.page.waitForFunction(()=>posts.length===1);
  assert.ok(performance.now()-lockStarted>=450);
  assert.equal(await locked.page.evaluate(()=>lockRequests),1);
  assert.equal(await locked.page.evaluate(()=>messages.filter(m=>m.attempted===true).length),1);
  await locked.page.close();result.cfWaitsForOriginalProblemLock=true;
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
