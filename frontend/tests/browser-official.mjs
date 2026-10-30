import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdtemp, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import { fixtureExtension } from './extension-fixture.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const python = process.env.TB_PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
const server = spawn(python, ['desktop/tests/browser_server.py'], { cwd: root, env: { ...process.env, TB_OFFLINE: '1', PYTHONIOENCODING: 'utf-8' }, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
let serverErrors = '';
server.stderr.on('data', c => { serverErrors += c; });
const { port } = await new Promise((resolve, reject) => {
  let text = '';
  server.stdout.on('data', chunk => { text += chunk; if (text.includes('\n')) resolve(JSON.parse(text.split('\n')[0])); });
  server.on('exit', code => reject(new Error('Fixture server exited: ' + code + ' ' + serverErrors)));
});
const base = `http://127.0.0.1:${port}`;
const profile = await mkdtemp(path.join(os.tmpdir(), 'tb-browser-extension-'));
const extension = await fixtureExtension(process.env.TB_BROWSER_EXTENSION || path.join(root, 'build/browser-extension'), profile, base);
let browser;
const posted = [], cookieChecks = [], errors = [];
const receipts = [];
let cfSubmitted = false, cfUnsupported = false, acSubmitted = false, ncReject = false, luoguLoggedIn = true, ncModern = false, luoguReject = false;
const source = 'int main(){}';
const headers = { 'access-control-allow-origin': 'https://ac.nowcoder.com', 'access-control-allow-credentials': 'true', 'access-control-allow-headers': 'content-type', 'access-control-allow-methods': 'GET, POST, OPTIONS' };
const form = (platform, task = '') => `<select name="${platform === 'AtCoder' ? 'data.TaskScreenName' : 'submittedProblemIndex'}"><option value="${task}">${task}</option></select><select name="${platform === 'AtCoder' ? 'data.LanguageId' : 'programTypeId'}"><option value="2">GNU C++17</option></select><textarea id="sourceCode" name="source"></textarea><button type="submit">提交</button>`;
const row = (platform, submitted) => `<table class="status-frame-datatable"><tr><th>Submission</th><th>Verdict</th></tr>${submitted ? platform === 'Codeforces' ? '<tr><td><a href="/contest/123/submission/1002">1002</a><a href="/contest/123/problem/A">A</a><a href="/profile/fixture">fixture</a></td><td class="submissionVerdictWrapper">Accepted</td></tr>' : '<tr><td><a href="/contests/abc100/submissions/2002">2002</a><a href="/contests/abc100/tasks/abc100_a">A</a></td><td><span class="label">AC</span></td></tr>' : ''}</table>`;
try {
  browser = await chromium.launchPersistentContext(profile, {
    channel: 'msedge', headless: true, ignoreHTTPSErrors: true,
    args: [`--disable-extensions-except=${extension}`, `--load-extension=${extension}`],
  });
  const worker = browser.serviceWorkers()[0] || await browser.waitForEvent('serviceworker', { timeout: 15000 });
  assert.ok(worker.url().includes('blgkmkjbdekeoenepgnajpeafofccbjm'));
  await worker.evaluate(async base => { await chrome.storage.local.set({bases:[base]}); }, base);
  const foreground = browser.pages()[0] || await browser.newPage();
  await foreground.goto(base + '/browser-connect.html');
  const activeTab = await worker.evaluate(async () => (await chrome.tabs.query({active:true,lastFocusedWindow:true}))[0].id);
  browser.on('page', page => page.on('pageerror', error => errors.push(error.message)));
  for (const domain of ['codeforces.com', 'atcoder.jp', 'ac.nowcoder.com', 'www.luogu.com.cn']) {
    await browser.addCookies([{ name: 'fixture_login', value: 'existing-browser-session', domain, path: '/', secure: true, sameSite: 'Lax' }]);
  }
  await browser.route('**/*', async route => {
    const request = route.request(), url = new URL(request.url());
    if (url.hostname === '127.0.0.1') return route.continue();
    if (request.method() === 'OPTIONS') return route.fulfill({ status: 204, headers });
    const json = value => route.fulfill({ contentType: 'application/json', headers, body: JSON.stringify(value) });
    const html = body => route.fulfill({ contentType: 'text/html; charset=utf-8', body: '<!doctype html><html><head><meta charset="utf-8"><title>Fixture official page</title></head><body>' + body + '</body></html>' });
    if (request.method() === 'POST') {
      posted.push(url.hostname + url.pathname);
      if (url.hostname !== 'victorinox.nowcoder.com') cookieChecks.push((await request.allHeaders()).cookie?.includes('fixture_login=existing-browser-session'));
      if (url.hostname === 'codeforces.com') { cfSubmitted = true; assert.equal(new URLSearchParams(request.postData()).get('source'), source); return html('<div id="header"><a href="/profile/fixture">fixture</a></div>'+row('Codeforces',true)); }
      if (url.hostname === 'atcoder.jp') { acSubmitted = true; assert.ok(request.postData().includes('int main()')); return json({ ok: true }); }
      if (url.hostname === 'victorinox.nowcoder.com') {
        assert.equal(JSON.parse(request.postData()).content, source);
        return json(ncReject ? { code: 1125, msg: '验证码错误' } : { code: 0, data: 3002 });
      }
      if (url.hostname === 'ac.nowcoder.com' && url.pathname === '/nccommon/submit_cd') {
        const body = new URLSearchParams(request.postData());
        assert.equal(body.get('content'), source);
        assert.equal(body.get('questionId'), '11604979');
        assert.equal(body.get('doneQuestionId'), '127263');
        assert.equal(body.get('language'), '2');
        return json(ncReject ? {code:1125,msg:'验证码错误'} : {code:0,submissionId:3002});
      }
      if (url.hostname === 'www.luogu.com.cn') {
        const body=JSON.parse(request.postData());
        assert.equal(body.code, source); assert.equal(body.lang,12); assert.equal(body.enableO2,1);
        assert.equal((await request.allHeaders())['x-csrf-token'],'fixture-csrf');
        return json(luoguReject ? {errorType:'CaptchaError',errorMessage:'请完成人机验证'} : { rid: 4002 });
      }
      return route.abort();
    }
    if (url.hostname === 'codeforces.com') {
      if (url.pathname.endsWith('/my')) return html('<div id="header"><a href="/profile/fixture">fixture</a></div>' + row('Codeforces', cfSubmitted));
      if (url.pathname.endsWith('/submit')) return html('<div id="header"><a href="/profile/fixture">fixture</a></div><form method="post" action="/contest/123/submit">' + form('Codeforces', 'A').replace('GNU C++17', cfUnsupported ? 'Python 3' : 'GNU C++17') + '</form>');
    }
    if (url.hostname === 'atcoder.jp') {
      if (url.pathname.endsWith('/submissions/me')) return html(row('AtCoder', acSubmitted));
      if (url.pathname.endsWith('/submit')) return html('<form><input type="hidden" name="csrf_token" value="fixture-atcoder-csrf">' + form('AtCoder', 'abc100_a') + '</form><script>document.querySelector("form").onsubmit=e=>{e.preventDefault();fetch(location.pathname,{method:"POST",body:document.querySelector("textarea").value})}</script>');
    }
    if (url.hostname === 'ac.nowcoder.com' && url.pathname === '/nccommon/status') return json({code:0,id:3002,status:5,isSelfTest:false});
    if (url.hostname === 'ac.nowcoder.com') return html(`<select name="language"><option value="2">C++（clang++18）</option></select><div class="CodeMirror">原站编辑器</div><div style="display:none"><button>保存并提交</button></div><button class="btn-submit">保存并提交</button><script>
      window.pageInfo={contestId:'127263',questionId:'11604979',isNewJudgeEditor:${ncModern},codeJudgeType:'0',tagId:'4',subTagId:'1',doneQuestionId:'127263'};window.globalInfo={ownerId:12345};
      const cachedFetch=window.fetch;let code='';document.querySelector('.CodeMirror').CodeMirror={setValue(value){code=value},getValue(){return code}};
      document.querySelector('.btn-submit').onclick=()=>cachedFetch('https://victorinox.nowcoder.com/api/service/judge/submit',{method:'POST',body:JSON.stringify({questionId:'11604979',content:code,submitType:1,userId:12345,appId:6,tagId:4,token:'page-only-fixture'})});
    </script>`);
    if (url.hostname === 'victorinox.nowcoder.com') return json({ code: 0, data: { status: 5 } });
    if (url.hostname === 'www.luogu.com.cn') {
      if (url.pathname === '/_lfe/config') return json({route:{'api.problem.submit':'/fe/api/problem/submit/{pid}'},CodeLanguage:{12:{id:12,name:'C++17',canO2:true},34:{id:34,name:'C++23',canO2:true}}});
      if (url.pathname.startsWith('/record/')) return json({ data: { record: { id: 4002, problem: { pid: 'P1001' }, user: { uid: 12345 }, status: 12 } } });
      if (url.pathname.startsWith('/auth/login')) return html('<input type="password">');
      return html(`<meta name="csrf-token" content="fixture-csrf"><script id="lentille-context" type="application/json">${JSON.stringify({user:luoguLoggedIn?{uid:12345}:null,data:{problem:{pid:'P1001',acceptLanguages:[12,34]},contest:null}})}</script><p>新版提交页面尚未挂载编辑器。题目描述提到验证码，正常题面不能误判为验证页面。</p>`);
    }
    return route.abort();
  });
  async function submit(key, url) {
    const result = await (await fetch(base + '/fixture/create?' + new URLSearchParams({ key, url }))).json();
    assert.ok(result.sessionId, JSON.stringify(result));
    return result;
  }
  async function state(key, status, timeout = 25000) {
    const until = Date.now() + timeout;
    let value;
    while (Date.now() < until) {
      value = (await (await fetch(base + '/fixture/status')).json())[key];
      if (value?.status === status) return value;
      if (['error', 'unconfirmed'].includes(value?.status)) break;
      await new Promise(resolve => setTimeout(resolve, 200));
    }
    throw new Error(key + ': expected ' + status + ', got ' + JSON.stringify(value));
  }
  const luoguIdle = await browser.newPage();
  await luoguIdle.goto('https://www.luogu.com.cn/problem/P1001');
  await luoguIdle.evaluate(() => window.preservedVerificationPage = 'original-page');
  await foreground.bringToFront();
  for (const [key, url, expectedId] of [
    ['cf', 'https://codeforces.com/contest/123/problem/A', '1002'],
    ['atcoder', 'https://atcoder.jp/contests/abc100/tasks/abc100_a', '2002'],
    ['nowcoder', 'https://ac.nowcoder.com/acm/contest/127263/B', '3002'],
    ['luogu', 'https://www.luogu.com.cn/problem/P1001', '4002'],
  ]) {
    await submit(key, url);
    const result = await state(key, 'finished');
    assert.equal(result.verdict, 'AC');
    assert.equal(result.submissionId, expectedId, key + ' must return the exact receipt for this submission');
    assert.ok(Number.isFinite(Date.parse(result.acceptedAt)), key + ' receipt must carry its acceptance time');
    receipts.push({platform:result.platform,submissionId:result.submissionId,verdict:result.verdict});
    assert.equal(await worker.evaluate(async () => (await chrome.tabs.query({active:true,lastFocusedWindow:true}))[0].id),activeTab,'submission never activates a browser tab');
    assert.ok((await browser.cookies(url)).some(cookie => cookie.name === 'fixture_login'));
  }
  assert.equal(posted.length, 4, 'each platform issues exactly one native submission');
  assert.equal(await luoguIdle.evaluate(() => window.preservedVerificationPage), 'original-page', 'Luogu reuses the existing page without reloading its verification');
  assert.ok(cookieChecks.every(Boolean), 'submissions reuse cookies already in the ordinary browser');
  const saved=await (await fetch(base + '/fixture/saved')).json();
  assert.equal(saved.length, 4, 'all four receipts reach desktop persistence callback');
  assert.deepEqual(saved.map(receipt=>receipt.platform).sort(),receipts.map(receipt=>receipt.platform).sort());
  assert.ok(saved.every(receipt=>receipt.status==='finished'&&receipt.verdict==='AC'));
  assert.deepEqual(await (await fetch(base + '/fixture/opened')).json(), [], 'TB never launches the browser on submit');
  cfUnsupported = true;
  const failed = await submit('unsupported-compiler', 'https://codeforces.com/contest/123/problem/A');
  await state('unsupported-compiler', 'error');
  const cleanupUntil = Date.now() + 5000;
  let retained = true;
  while (retained && Date.now() < cleanupUntil) {
    retained = await worker.evaluate(async sid => Object.values((await chrome.storage.session.get('jobs')).jobs || {}).some(job => job.sessionId === sid), failed.sessionId);
    if (retained) await new Promise(resolve => setTimeout(resolve, 100));
  }
  assert.equal(retained, false, 'failed background jobs release their browser storage entry');
  assert.equal(browser.pages().some(page => page.url().startsWith('https://codeforces.com/contest/123/submit')), false, 'TB closes its own failed background tab');
  assert.equal(posted.length, 4, 'unsupported compiler never sends code');
  cfUnsupported = false;
  const idleTab = await browser.newPage();
  await idleTab.route('https://codeforces.com/contest/123/problem/A', route => route.fulfill({contentType:'text/html',body:'<p>Unbound fixture problem</p>'}));
  await idleTab.goto('https://codeforces.com/contest/123/problem/A');
  const idleId = await worker.evaluate(async () => (await chrome.tabs.query({url:'https://codeforces.com/contest/123/problem/A'}))[0].id);
  await worker.evaluate(id => {
    globalThis.idleFixtureTicks = 0;
    chrome.runtime.onMessage.addListener((message, sender) => { if (message.type === 'tick' && sender.tab?.id === id) globalThis.idleFixtureTicks++; });
  }, idleId);
  await new Promise(resolve => setTimeout(resolve, 3100));
  assert.ok(await worker.evaluate(() => globalThis.idleFixtureTicks <= 1), 'unbound original-site pages no longer poll the connector every second');
  await idleTab.close();
  ncModern = true;
  await submit('modern', 'https://ac.nowcoder.com/acm/contest/127263/B');
  await state('modern','finished');
  await submit('luogu-reused-job', 'https://www.luogu.com.cn/problem/P1001');
  await state('luogu-reused-job','finished');
  assert.equal(await luoguIdle.evaluate(() => window.preservedVerificationPage), 'original-page', 'a finished job cannot poison the next submission on a reused page');
  ncReject = true;
  await submit('captcha', 'https://ac.nowcoder.com/acm/contest/127263/B');
  await state('captcha', 'awaiting_submit');
  assert.equal((await (await fetch(base + '/fixture/saved')).json()).length, 6);
  luoguLoggedIn = false;
  await luoguIdle.reload();
  await submit('login', 'https://www.luogu.com.cn/problem/P1001');
  await state('login', 'needs_login');
  const before = posted.length;
  luoguLoggedIn = true;
  const login = browser.pages().find(page => page.url() === 'https://www.luogu.com.cn/problem/P1001#submit');
  await login.reload();
  await state('login', 'ready');
  assert.equal(posted.length, before, 'logging in does not auto-submit');
  await submit('login', 'https://www.luogu.com.cn/problem/P1001');
  await state('login', 'finished');
  assert.equal(posted.length, before + 1);
  luoguReject = true;
  await submit('luogu-verification', 'https://www.luogu.com.cn/problem/P1001');
  await state('luogu-verification', 'awaiting_submit');
  const rejectedCount = posted.length;
  const verifyPage = browser.pages().find(p => p.url() === 'https://www.luogu.com.cn/problem/P1001#submit');
  await verifyPage.evaluate(() => window.preservedVerificationPage = 'verify-this-page');
  await fetch(base + '/fixture/view?' + new URLSearchParams({url:'https://www.luogu.com.cn/problem/P1001'}));
  const openedLinks = await (await fetch(base + '/fixture/opened')).json();
  const pair = await browser.newPage();
  await pair.goto(openedLinks.at(-1));
  await verifyPage.waitForFunction(() => window.preservedVerificationPage === 'verify-this-page');
  luoguReject = false;
  await new Promise(resolve => setTimeout(resolve, 1500));
  assert.equal(posted.length, rejectedCount, 'opening or completing verification must not replay a rejected POST');
  await submit('luogu-verification', 'https://www.luogu.com.cn/problem/P1001');
  await state('luogu-verification', 'finished');
  assert.equal(posted.length, rejectedCount + 1, 'an explicit retry can clear a stale CaptchaError and submit exactly once');
  await foreground.bringToFront();
  assert.deepEqual(errors, []);
  assert.equal(await worker.evaluate(async () => (await chrome.tabs.query({active:true,lastFocusedWindow:true}))[0].id),activeTab);
  // User submits directly on an unbound site tab; no TB job is created.
  ncReject=false;luoguReject=false;
  const directNC=await browser.newPage();
  await directNC.goto('https://ac.nowcoder.com/acm/contest/127263/B');
  await directNC.evaluate(()=>document.querySelector('.CodeMirror').CodeMirror.setValue('int main(){}'));
  await directNC.locator('.btn-submit').click();
  const directLG=await browser.newPage();
  await directLG.goto('https://www.luogu.com.cn/problem/P1001');
  await directLG.evaluate(()=>{const b=document.createElement('button');b.textContent='Fixture user submit';b.onclick=()=>fetch('/fe/api/problem/submit/P1001',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-TOKEN':'fixture-csrf'},body:JSON.stringify({code:'int main(){}',lang:12,enableO2:1})});document.body.append(b);});
  await directLG.getByRole('button',{name:'Fixture user submit'}).click();
  let passive=[];
  for(let i=0;i<120;i++){passive=await(await fetch(base+'/fixture/public-receipts')).json();if(['牛客','洛谷'].every(p=>passive.some(r=>r.platform===p&&r.owner==='12345'&&r.records.some(v=>v.verdict==='AC'))))break;await new Promise(r=>setTimeout(r,100));}
  assert.ok(['牛客','洛谷'].every(p=>passive.some(r=>r.platform===p&&r.owner==='12345'&&r.records.some(v=>v.verdict==='AC'))),'unbound official user submissions reach TB without a submit job');
  console.log('Direct official submissions without TB jobs: Nowcoder and Luogu AC receipts imported.');
  console.log('Background extension: four platforms; no opened browser or active tab changes; legacy Nowcoder nccommon/top-level receipts; modern cached fetch; Luogu API without editor; original CSRF/cookies; captcha, login retry, no duplicates passed.');
  console.log(JSON.stringify({ok:true,receipts,exactSubmissionIds:true,desktopReceiptsSaved:true,noDuplicatePosts:true,realAccountSubmission:false}));
} finally {
  if (browser) await browser.close();
  server.kill();
  assert.equal(path.dirname(path.resolve(profile)), path.resolve(os.tmpdir()));
  assert.ok(path.basename(profile).startsWith('tb-browser-extension-'));
  await rm(profile, { recursive: true, force: true });
}
