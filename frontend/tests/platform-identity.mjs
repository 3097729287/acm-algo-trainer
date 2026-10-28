// Pure read-only DOM inspection against fulfilled fixture pages; never login.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {chromium} from 'playwright';
const source=fs.readFileSync('../desktop/platform_login.py','utf8').match(/LOGIN_SCRIPT = r"""([\s\S]*?)"""/)[1];
const browser=await chromium.launch({channel:'msedge',headless:true}),context=await browser.newContext();
try{
  const cases=[
    ['https://codeforces.com/','<div id="header"><a href="/profile/owner">Owner</a><a href="/logout?csrf=fixture">Logout</a></div>',{},'owner'],
    ['https://codeforces.com/blog/entry/1','<div id="header"><a href="/enter">Login</a></div><article><a href="/profile/not_me">author</a></article>',{},''],
    ['https://atcoder.jp/','<nav class="navbar"><a href="/users/owner_at">Owner</a><a href="/logout">Logout</a></nav>',{},'owner_at'],
    ['https://atcoder.jp/users/other','<nav class="navbar"><a href="/login">Login</a></nav><a href="/users/other">Other</a>',{},''],
    ['https://ac.nowcoder.com/','<p>Fixture</p>',{globalInfo:{ownerId:42}},'42'],
    ['https://ac.nowcoder.com/acm/contest/1/A','<a href="https://www.nowcoder.com/profile/999">Author</a>',{globalInfo:{ownerId:0}},''],
    ['https://www.luogu.com.cn/','<script id="lentille-context" type="application/json">{"user":{"uid":43},"data":{"user":{"uid":999}}}</script>',{},'43'],
    ['https://www.luogu.com.cn/user/999','<script id="lentille-context" type="application/json">{"user":null,"data":{"user":{"uid":999}}}</script>',{},''],
    ['https://codeforces.com/','<title>Just a moment</title><div id="header"><a href="/profile/owner">Owner</a><a href="/logout">Logout</a></div>',{},''],
    ['https://unrelated.invalid/','<header><a href="/profile/owner">Owner</a><a href="/logout">Logout</a></header>',{},null],
  ];
  for(const [url,html,globals,expected] of cases){
    const page=await context.newPage();await page.route('**/*',route=>route.fulfill({contentType:'text/html',body:html}));
    await page.goto(url);await page.evaluate(values=>Object.assign(window,values),globals);
    const result=await page.evaluate(source);assert.equal(result?.owner??null,expected,url);await page.close();
  }
  console.log('PASS 10 authenticated-owner DOM fixtures: four sites, guest profiles, challenge pages and unrelated hosts. No real site requests.');
}finally{await context.close();await browser.close();}
