import assert from 'node:assert/strict';
import {createServer} from 'vite';
import {chromium} from 'playwright';
import {mkdir} from 'node:fs/promises';
const output=process.env.TB_VERIFY_OUTPUT||'../.backups/presence-idle-open-20261109';
const server=await createServer({cacheDir:'../.backups/completion-followup-20261108/presence-vite',optimizeDeps:{entries:['tests/presence-fixture.html'],include:['react','react-dom/client','react/jsx-runtime']},resolve:{dedupe:['react','react-dom']},server:{host:'127.0.0.1',port:18797,strictPort:true,hmr:false}});await server.listen();
const browser=await chromium.launch({channel:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];
page.on('pageerror',issue=>errors.push(issue.message));
try{
 await page.clock.install();
 await page.goto('http://127.0.0.1:18797/tests/presence-fixture.html');await page.waitForFunction(()=>window.presenceFixture?.owner);
 await page.getByLabel('在线人数',{exact:true}).getByText('在线 · —人',{exact:true}).waitFor();
 await page.evaluate(()=>presenceFixture.owner(presenceFixture.ids[0]));await page.getByLabel('在线人数',{exact:true}).getByText('在线 · 5人',{exact:true}).waitFor();
 const ranking=page.getByRole('region',{name:'排位排行榜与对战记录'});
 for(const label of ['做题中','重现赛中','从零讲中','实验室中'])await ranking.getByText(label,{exact:true}).waitFor();
 await ranking.getByText('甲 胜',{exact:true}).waitFor();assert.equal(await ranking.locator('section').count(),2);
 assert.equal(await ranking.locator('.duel-public-record').count(),1);
 for(const activity of ['replay','lecture','lab']){
  await page.evaluate(activity=>presenceFixture.activity(activity),activity);
  await page.waitForFunction(activity=>presenceFixture.calls.some(call=>call.path==='presence'&&call.body.activity===activity),activity);
 }
 const connected=await page.locator('.rankings-page .user-presence[data-online=true]').first().evaluate(node=>getComputedStyle(node).color);
 const closed=page.locator('.rankings-page .user-presence[data-online=false]:not([data-idle=true])');
 await closed.getByText('离线',{exact:true}).waitFor();
 const grey=await closed.evaluate(node=>getComputedStyle(node).color);
 assert.notEqual(grey,connected);
 await page.clock.fastForward(300001);
 await page.getByLabel('在线人数',{exact:true}).getByText('在线 · 4人',{exact:true}).waitFor();
 const idle=page.locator('.rankings-page .user-presence[data-idle=true]');
 await idle.getByText('离线',{exact:true}).waitFor();
 assert.notEqual(await idle.evaluate(node=>getComputedStyle(node).color),connected);
 assert.equal(await idle.evaluate(node=>getComputedStyle(node).color),await page.evaluate(()=>{const n=document.createElement('i');n.style.color='var(--danger,#ed657d)';document.body.append(n);const color=getComputedStyle(n).color;n.remove();return color;}));
 assert.notEqual(await idle.evaluate(node=>getComputedStyle(node).color),grey,'An open idle application is distinct from an unopened one');
 assert.equal(await closed.evaluate(node=>getComputedStyle(node).color),grey);
 await mkdir(output,{recursive:true});await page.screenshot({path:output+'/idle-red-closed-grey.png'});
 await page.evaluate(()=>{document.dispatchEvent(new KeyboardEvent('keydown',{key:'a',bubbles:true}));window.dispatchEvent(new Event('focus'));});
 await page.clock.runFor(25001);
 await page.getByLabel('在线人数',{exact:true}).getByText('在线 · 4人',{exact:true}).waitFor();
 await page.keyboard.press('Control+ArrowRight');
 await page.getByLabel('在线人数',{exact:true}).getByText('在线 · 5人',{exact:true}).waitFor();
 assert.equal(await page.evaluate(()=>presenceFixture.shortcutsHandled),1,'A captured application command executes once and restores genuine activity');
 await page.clock.fastForward(300001);
 await page.getByLabel('在线人数',{exact:true}).getByText('在线 · 4人',{exact:true}).waitFor();
 await page.mouse.move(640,400);
 await page.getByLabel('在线人数',{exact:true}).getByText('在线 · 5人',{exact:true}).waitFor();
 await page.evaluate(()=>{const frame=document.createElement('iframe');frame.title='Presence reading frame';frame.srcdoc='<button>继续阅读</button>';document.body.append(frame);});
 await page.frameLocator('iframe[title="Presence reading frame"]').getByRole('button').waitFor();
 await page.clock.fastForward(300001);
 await page.getByLabel('在线人数',{exact:true}).getByText('在线 · 4人',{exact:true}).waitFor();
 await page.frameLocator('iframe[title="Presence reading frame"]').getByRole('button').click();
 await page.getByLabel('在线人数',{exact:true}).getByText('在线 · 5人',{exact:true}).waitFor();
 await page.evaluate(()=>document.querySelector('iframe[title="Presence reading frame"]').remove());
 // Model the read-only native sampler: only a new process-owned revision
 // reports real input. A repeated value, focus or a synthetic DOM event does
 // not advance the five-minute clock.
 await page.evaluate(()=>{presenceFixture.native={available:true,session:'native-fixture-process',revision:0,observed:false,ageSeconds:null};});
 await page.clock.runFor(1001);
 await page.clock.fastForward(150000);
 await page.evaluate(()=>{presenceFixture.native={available:true,session:'native-fixture-process',revision:1,observed:true,at:performance.now()};});
 await page.clock.runFor(1001);
 await page.clock.fastForward(170000);
 await page.getByLabel('在线人数',{exact:true}).getByText('在线 · 5人',{exact:true}).waitFor();
 await page.clock.fastForward(130001);
 await page.getByLabel('在线人数',{exact:true}).getByText('在线 · 4人',{exact:true}).waitFor();
 await page.evaluate(()=>{window.dispatchEvent(new CustomEvent('tb-native-user-input'));window.dispatchEvent(new Event('focus'));});
 await page.clock.runFor(1001);
 await page.getByLabel('在线人数',{exact:true}).getByText('在线 · 4人',{exact:true}).waitFor();
 await page.evaluate(()=>{presenceFixture.native={available:true,session:'native-fixture-process',revision:0,observed:true,ageSeconds:0};});
 await page.clock.runFor(1001);
 await page.getByLabel('在线人数',{exact:true}).getByText('在线 · 4人',{exact:true}).waitFor();
 await page.evaluate(()=>{presenceFixture.native={available:true,session:'native-fixture-process',revision:2,observed:true,ageSeconds:-1};});
 await page.clock.runFor(1001);
 await page.getByLabel('在线人数',{exact:true}).getByText('在线 · 4人',{exact:true}).waitFor();
 await page.evaluate(()=>{presenceFixture.native={available:true,session:'native-fixture-process',revision:2,observed:true,at:performance.now()};});
 await page.clock.runFor(1001);
 await page.getByLabel('在线人数',{exact:true}).getByText('在线 · 5人',{exact:true}).waitFor();
 const beforeClose=await page.evaluate(()=>presenceFixture.calls.filter(call=>call.path==='presence'&&call.body.activity==='offline').length);
 await page.evaluate(()=>window.dispatchEvent(new CustomEvent('tb-before-update',{detail:{waitUntil:()=>{}}})));
 assert.equal(await page.evaluate(()=>presenceFixture.calls.filter(call=>call.path==='presence'&&call.body.activity==='offline').length),beforeClose,'Ordinary update-save does not declare the application closed');
 await page.evaluate(()=>window.dispatchEvent(new Event('tb-desktop-closing')));
 await page.getByLabel('在线人数',{exact:true}).getByText('在线 · 4人',{exact:true}).waitFor();
 assert.equal(await page.locator('.rankings-page .user-presence[data-idle=true]').count(),0);
 assert(await page.locator('.rankings-page .user-presence[data-online=false]').evaluateAll(nodes=>nodes.every(node=>getComputedStyle(node).color===getComputedStyle(nodes[0]).color)));
 await page.evaluate(()=>window.dispatchEvent(new Event('pageshow')));
 await page.getByLabel('在线人数',{exact:true}).getByText('在线 · 5人',{exact:true}).waitFor();
 const closeTransport=await page.evaluate(async()=>{
  const {request}=await import('/src/api/client.js'),original=window.fetch,captured=[];
  window.fetch=async(url,options)=>{captured.push({url,keepalive:options.keepalive===true,body:JSON.parse(options.body)});return new Response(JSON.stringify({owner:presenceFixture.ids[0]}),{status:200});};
  try{await request('presence',{activity:'offline'},'isolated-fixture-only');await request('presence',{activity:'problem'},'isolated-fixture-only');}
  finally{window.fetch=original;}
  return captured;
 });
 assert.equal(closeTransport[0].keepalive,true);assert.deepEqual(closeTransport[0].body,{activity:'offline'});
 assert.equal(closeTransport[1].keepalive,false,'Only the small final offline request survives page unload');
 await page.evaluate(()=>{presenceFixture.hold=presenceFixture.ids[0];window.dispatchEvent(new Event('focus'));});
 await page.waitForFunction(()=>presenceFixture.pending.length===1);
 await page.evaluate(()=>presenceFixture.owner(presenceFixture.ids[1],'replay'));await page.getByLabel('在线人数',{exact:true}).getByText('在线 · 2人',{exact:true}).waitFor();
 await page.evaluate(()=>presenceFixture.pending[0]({owner:presenceFixture.ids[0],available:true,count:99,users:[]}));
 await page.waitForTimeout(100);assert.equal(await page.getByLabel('在线人数',{exact:true}).innerText(),'在线 · 2人');
 await page.evaluate(()=>presenceFixture.mode('thought'));await page.waitForFunction(()=>presenceFixture.calls.some(call=>call.path==='duel/board?mode=thought'));
 await ranking.getByText('甲 胜',{exact:true}).waitFor();
 await page.setViewportSize({width:360,height:900});assert(await ranking.evaluate(node=>node.scrollWidth<=node.clientWidth+1));
 await page.evaluate(()=>{presenceFixture.fail=true;window.dispatchEvent(new Event('focus'));});await page.getByLabel('在线人数',{exact:true}).getByText('在线 · —人',{exact:true}).waitFor();
 assert.deepEqual(errors,[]);console.log('PASS presence idle-open red / closed grey, active-only counts, five-minute trusted DOM/native input and reading-frame recovery, repeated/invalid native snapshots rejected, close/save separation, owner/late reply, thought mode, narrow layout and unknown count');
}finally{await browser.close();await server.close();}
