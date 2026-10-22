import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';



const detector = {URL};
vm.runInNewContext(await readFile('../desktop/browser_extension/login_state.js','utf8'), detector);
assert.equal(detector.tbCookieLoginState('Codeforces',[]), 'unknown');
assert.equal(detector.tbCookieLoginState('AtCoder',[]), 'unknown');
assert.equal(detector.tbCookieLoginState('AtCoder',[{name:'REVEL_SESSION',value:encodeURIComponent('signed-\x00csrf_token:test\x00\x00UserScreenName:fixture\x00')}]), 'logged_in');
assert.equal(detector.tbCookieLoginState('AtCoder',[{name:'REVEL_SESSION',value:encodeURIComponent('signed-\x00csrf_token:test\x00')}]), 'logged_out');
assert.equal(detector.tbCookieLoginState('AtCoder',[{name:'REVEL_SESSION',value:'%malformed'}]), 'unknown');
assert.equal(detector.tbCookieLoginState('AtCoder',[{name:'REVEL_SESSION',value:encodeURIComponent('signed-\x00UserScreenName:fixture\x00'),expirationDate:1}]), 'unknown');
for (const [platform,domain] of Object.entries({Codeforces:'codeforces.com',AtCoder:'atcoder.jp','牛客':'nowcoder.com','洛谷':'luogu.com.cn'})) {
  assert.equal(detector.tbFirstPartyCookie(platform,{domain,partitionKey:{topLevelSite:'https://'+domain,hasCrossSiteAncestor:false}}),true);
  assert.equal(detector.tbFirstPartyCookie(platform,{domain,partitionKey:{topLevelSite:'https://'+domain,hasCrossSiteAncestor:true}}),false);
  assert.equal(detector.tbFirstPartyCookie(platform,{domain,partitionKey:{topLevelSite:'https://evil.test'}}),false);
}
assert.equal(detector.tbCookieLoginState('Codeforces',[{name:'JSESSIONID',value:'anonymous'}]), 'unknown');
assert.equal(detector.tbPageLoginState('Codeforces','<div id="header"><a href="/enter">Enter</a></div>'), 'logged_out');
assert.equal(detector.tbPageLoginState('Codeforces','<div id="header"><a href="/profile/fixture">Fixture</a></div>'), 'logged_in');
assert.equal(detector.tbPageLoginState('Codeforces','<title>Just a moment</title>'), 'unknown');
assert.equal(detector.tbPageLoginState('Codeforces','<div id = "header"><div><a href="/profile/fixture">Fixture</a></div></div><a href="/enter">Article login prompt</a>'), 'logged_in');
assert.equal(detector.tbPageLoginState('Codeforces','<div id="header"><a href="/enter">Enter</a></div><a href="/profile/author">Article author</a>'), 'logged_out');
assert.equal(detector.tbPageLoginState('AtCoder','var userScreenName = "fixture";'), 'logged_in');
assert.equal(detector.tbPageLoginState('AtCoder','var userScreenName = "";'), 'logged_out');
assert.equal(detector.tbPageLoginState('牛客','window.globalInfo={"ownerId":123};'), 'logged_in');
assert.equal(detector.tbPageLoginState('洛谷','<script id="lentille-context">{"user":null}</script>'), 'logged_out');
assert.equal(detector.tbPageLoginState('洛谷','<script id="lentille-context">{"user":{"uid":123}}</script>'), 'logged_in');

console.log('PASS: first-party login detection and cookie isolation compatibility.');
