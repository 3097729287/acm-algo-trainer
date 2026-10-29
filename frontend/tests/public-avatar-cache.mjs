import assert from 'node:assert/strict';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const server=await createServer({server:{host:'127.0.0.1',port:0}});await server.listen();
const base=server.resolvedUrls.local[0],browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
try {
 const page=await browser.newPage(),errors=[];page.on('pageerror',issue=>errors.push(issue.message));
 const open=()=>page.goto(base+'tests/public-avatar-cache-fixture.html');
 const images=()=>page.getByAltText('Cached public avatar');
 await open();await images().first().waitFor();assert.equal(await images().count(),2);
 assert.equal((await page.evaluate(()=>window.avatarCalls)).length,1,'Concurrent identities share one request');
 const values=await page.evaluate(()=>window.publicAvatarFixture.assets);
 await page.evaluate(()=>{window.publicAvatarFixture.configure({show:false});window.publicAvatarFixture.fail(true);window.publicAvatarFixture.configure({show:true});});
 assert.equal(await images().count(),2,'A warm remount paints cached images synchronously');
 assert.equal((await page.evaluate(()=>window.avatarCalls)).length,1);
 await page.goto(base+'tests/public-avatar-cache-fixture.html?fail=1');await images().first().waitFor();
 assert.deepEqual(await page.evaluate(()=>window.firstAvatarRenders),[true,true],'A fresh module/application reads verified persisted avatars on its first render');
 assert.equal((await page.evaluate(()=>window.avatarCalls)).length,0,'An offline restart keeps the same-hash image');
 await page.evaluate(()=>{window.publicAvatarFixture.fail(false);window.publicAvatarFixture.configure({asset:'b'});});
 assert.equal(await images().count(),0,'A new hash cannot show the old image');
 await images().first().waitFor();assert.equal(await images().first().getAttribute('src'),values.b.avatarData);
 let disk=await page.evaluate(()=>JSON.parse(localStorage.getItem('tb.public-avatars.v1')));
 assert.equal(disk.entries.length,1);assert.equal(disk.entries[0].hash,values.b.avatarHash);
 await page.evaluate(()=>window.publicAvatarFixture.configure({asset:null}));
 assert.equal(await images().count(),0);disk=await page.evaluate(()=>JSON.parse(localStorage.getItem('tb.public-avatars.v1')));assert.equal(disk.entries.length,0,'Deletion retires cached target versions');
 await page.evaluate(()=>{localStorage.setItem('isolated-private-draft','never remove');const original=Storage.prototype.setItem;Storage.prototype.setItem=function(key,value){if(key==='tb.public-avatars.v1')throw new DOMException('Isolated quota','QuotaExceededError');return original.call(this,key,value);};window.publicAvatarFixture.configure({id:'33333333-3333-4333-8333-333333333333',asset:'a'});});
 await images().first().waitFor();assert.equal(await page.evaluate(()=>localStorage.getItem('isolated-private-draft')),'never remove');
 await page.evaluate(()=>{window.__tbAccountUserId='44444444-4444-4444-8444-444444444444';window.publicAvatarFixture.fail(true);window.publicAvatarFixture.configure({revision:100});});
 assert.equal(await images().count(),0,'Another owner cannot read the previous account cache');
 await open();await images().first().waitFor();
 await page.evaluate(()=>window.publicAvatarFixture.configure({board:true}));
 await page.locator('.ranking-self').waitFor();assert((await page.locator('.ranking-self').innerText()).includes('Original self'));
 await page.evaluate(()=>window.publicAvatarFixture.rename('New confirmed nickname'));
 assert((await page.locator('.ranking-self').innerText()).includes('New confirmed nickname'));
 await page.evaluate(()=>window.publicAvatarFixture.configure({own:window.publicAvatarFixture.assets.b.avatarData}));
 assert.equal(await page.locator('.ranking-self .profile-avatar-face img').getAttribute('src'),values.b.avatarData);
 await page.evaluate(()=>window.publicAvatarFixture.configure({board:false}));
 for(let index=0;index<27;index++) {
  await page.evaluate(id=>window.publicAvatarFixture.configure({id,asset:'a'}),`00000000-0000-4000-8000-${index.toString(16).padStart(12,'0')}`);
  await images().first().waitFor();
 }
 const bounded=await page.evaluate(()=>({raw:localStorage.getItem('tb.public-avatars.v1'),draft:localStorage.getItem('isolated-private-draft')}));
 assert(JSON.parse(bounded.raw).entries.length<=24);assert(bounded.raw.length<=2*1024*1024);
 assert.equal(bounded.draft,'never remove');
 assert(JSON.parse(bounded.raw).entries.every(item=>Object.keys(item).sort().join(',')==='data,hash,owner,userId'));
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({ok:true,concurrentDedup:true,instantRemount:true,firstRenderAcrossRestart:true,offlineCache:true,hashAndDeletionInvalidation:true,quotaSafe:true,persistentCountBound:24,persistentCharacterBound:2*1024*1024,ownerIsolation:true,confirmedNickname:true,ownAvatarChange:true,productionRequests:0}));
} finally {await browser.close();await server.close();}
