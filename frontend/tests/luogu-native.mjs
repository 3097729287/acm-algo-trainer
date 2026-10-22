// Real CodeMirror 6 model and delayed native mounting; all site traffic is intercepted.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {build} from 'vite';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';
import {luoguComboFixture} from './luogu-combo-fixture.mjs';

const bundled = await build({configFile:false,root:fileURLToPath(new URL('../',import.meta.url)),logLevel:'error',build:{write:false,minify:false,lib:{entry:fileURLToPath(new URL('./luogu-editor-fixture.js',import.meta.url)),name:'LuoguEditorFixture',formats:['iife']}}});
const outputs = Array.isArray(bundled) ? bundled.flatMap(result=>result.output) : bundled.output;
const editorSource = outputs.find(item=>item.type==='chunk').code.replace(/<\/script/gi,'<\\/script');
let adapter = await readFile(new URL('../../desktop/official_page.js',import.meta.url),'utf8');
for(const [marker,name] of [['COMPILER_SELECTION','official_languages.js'],['NOWCODER_RECEIPTS','official_nowcoder.js'],['LUOGU_RECEIPTS','official_luogu.js']])adapter=adapter.replace(marker,await readFile(new URL('../../desktop/'+name,import.meta.url),'utf8'));
const browser = await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page = await browser.newPage(),posts=[];
const code = '#include <iostream>\nint main() { std::cout << 42 << "\\n"; }\n';
const combo=luoguComboFixture();
try {
  await page.route('**/*',async route=>{
    const request=route.request(),url=new URL(request.url());
    if(request.method()==='POST'){
      assert.equal(url.pathname,'/fe/api/problem/submit/P17727');
      posts.push(request.postDataJSON());
      return route.fulfill({json:{rid:44001}});
    }
    if(url.pathname.startsWith('/record/'))return route.fulfill({json:{data:{record:{id:44001,problem:{pid:'P17727'},user:{uid:123},status:12}}}});
    assert.equal(url.pathname,'/problem/P17727');
    return route.fulfill({contentType:'text/html; charset=utf-8',body:`<script id="lentille-context" type="application/json">{"user":{"uid":123},"data":{"problem":{"pid":"P17727"}}}</script><div class="body">${combo.html}<div id="native-editor"></div><button id="native-submit" class="solid lform-size-middle" type="button">提交评测</button></div><script>${editorSource}</script><script>${combo.script}window.nativeClicks=0;document.querySelector('#native-submit').onclick=()=>{window.nativeClicks++;fetch('/fe/api/problem/submit/P17727',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-TOKEN':'fixture-native-token'},body:JSON.stringify({code:fixtureView.state.doc.toString(),lang:fixtureLang})})};</script>`});
  });
  await page.goto('https://www.luogu.com.cn/problem/P17727#submit');
  await page.addScriptTag({content:adapter});
  await page.evaluate(code=>{
    window.ctx={sessionId:'luogu-delayed',platform:'洛谷',originalUrl:location.href.split('#')[0],problem:'',code,language:'cpp17',nativeFormOnly:true,attempted:false};
    window.messages=[];window.report=value=>{messages.push(value);for(const field of ['attempted','submissionId','baseline','baselineKnown','baselineOwner'])if(field in value)ctx[field]=value[field];return Promise.resolve()};
  },code);
  assert.equal(await page.evaluate(()=>tbOfficialPage(ctx,'inspect',report).status),'loading','API context must not mark an unmounted native editor ready');
  await page.evaluate(()=>tbOfficialPage(ctx,'submit',report));
  await page.waitForTimeout(40);
  assert.equal(posts.length,0);
  assert.equal(await page.evaluate(()=>messages.some(value=>value.status==='error')),false,'waiting for mount is not a terminal failure');
  await page.evaluate(()=>mountLuoguEditor());
  assert.equal(await page.locator('.cm-content').evaluate(node=>!!node.cmTile&&!node.cmView),true,'exercise the actual current CodeMirror DOM structure');
  assert.equal(await page.evaluate(()=>tbOfficialPage(ctx,'inspect',report).status),'ready');
  await page.evaluate(()=>tbOfficialPage(ctx,'submit',report));
  await page.waitForFunction(()=>nativeClicks===1||messages.some(value=>value.status==='error'));
  assert.deepEqual(await page.evaluate(()=>messages.filter(value=>value.status==='error')),[]);
  await page.waitForFunction(()=>messages.some(value=>value.status==='judging'));
  assert.equal(await page.evaluate(()=>fixtureView.state.doc.toString()),code);
  assert.equal(posts.length,1);assert.equal(posts[0].code,code);assert.equal(posts[0].lang,28);
  assert.equal(await page.evaluate(()=>fixtureLanguageClicks),0,'Keep a compatible native C++23 choice');
  assert.equal(await page.locator('form,select,[role=combobox]').count(),0,'Use actual Luogu custom controls and a button outside any form');
  await page.evaluate(()=>{for(let index=0;index<25;index++)tbOfficialPage(ctx,'inspect',report)});
  await page.waitForTimeout(40);assert.equal(posts.length,1,'receipt inspection must not click twice');
  console.log(JSON.stringify({ok:true,delayedMountWaits:true,currentCodeMirrorModelFilled:true,actualLuoguComboBox:true,nativeButtonOutsideForm:true,nativeFormPosts:posts.length,realAccountSubmission:false}));
} catch(error) {
  console.error(JSON.stringify(await page.evaluate(()=>({messages:window.messages,clicks:window.nativeClicks,language:window.fixtureLang,handler:typeof document.querySelector('#native-submit')?.onclick}))));
  throw error;
} finally {await browser.close()}
