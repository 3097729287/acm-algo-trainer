import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const out='../.backups/cleanup-startup/banner-growth';await mkdir(out,{recursive:true});
const vite=await createServer({cacheDir:out+'/vite',server:{host:'127.0.0.1',port:0,watch:null}});await vite.listen();
const browser=await chromium.launch({channel:'msedge',headless:true}),page=await browser.newPage({viewport:{width:2048,height:1152}}),errors=[],layouts=[];
page.on('pageerror',error=>errors.push(error.message));page.setDefaultTimeout(10000);
try{
 await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/growth-material-fixture.html`);await page.locator('.account-hero-person').waitFor();
 for(const width of [2048,1440,960,430]){
  await page.setViewportSize({width,height:1152});
  const layout=await page.evaluate(()=>{const portrait=document.querySelector('.growth-dashboard .profile-avatar-button').getBoundingClientRect(),content=document.querySelector('.sticker-content').getBoundingClientRect();return {portraitCenter:(portrait.left+portrait.right)/2,contentCenter:(content.left+content.right)/2,overflow:document.documentElement.scrollWidth>innerWidth};});
  assert(!layout.overflow);assert(Math.abs(layout.portraitCenter-layout.contentCenter)<1,'Growth portrait is centred after removing the standalone rank');assert.equal(await page.locator('.account-hero-rank').count(),0);layouts.push({width,...layout});
  if(width===2048)await page.screenshot({path:out+'/growth-centred.png'});
 }
 await page.setViewportSize({width:2048,height:1152});await page.evaluate(()=>growthCheck.setPanel('duel'));await page.locator('.duel-banner-frame').waitFor();
 const flag=await page.locator('.duel-lobby-identity').boundingBox(),portrait=await page.locator('.profile-avatar-button').boundingBox(),badge=await page.locator('.duel-lobby-rank>svg').boundingBox();
 assert(flag.width>=370&&flag.height>=510);assert(portrait.width>=180);assert(badge.width>=90);await page.screenshot({path:out+'/duel-large.png'});
 for(let tier=0;tier<9;tier++){
  await page.evaluate(value=>growthCheck.setTier(value),tier);await page.waitForFunction(value=>document.querySelector('.duel-banner-frame')?.dataset.tier===String(value),tier);
  assert.equal(await page.locator('.duel-lobby-rank>svg').count(),1,'Duel rank badge remains present');
 }
 await page.evaluate(()=>growthCheck.setPanel('banners'));await page.locator('.banner-gallery').waitFor();assert.equal(await page.locator('.duel-banner-frame').count(),9);
 const uniqueness=await page.locator('.duel-banner-frame').evaluateAll(nodes=>({tiers:new Set(nodes.map(n=>n.dataset.tier)).size,colours:new Set(nodes.map(n=>n.querySelector('linearGradient stop').getAttribute('stop-color'))).size,ids:[...document.querySelectorAll('svg defs [id]')].map(n=>n.id)}));
 assert.equal(uniqueness.tiers,9);assert.equal(uniqueness.colours,9);assert.equal(new Set(uniqueness.ids).size,uniqueness.ids.length);
 await page.screenshot({path:out+'/nine-tier-frames.png',fullPage:true});
 await page.evaluate(()=>growthCheck.setPanel('duel'));await page.setViewportSize({width:430,height:850});await page.locator('.duel-banner-frame').waitFor();assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 await page.screenshot({path:out+'/duel-narrow.png'});assert.deepEqual(errors,[]);
 await writeFile(out+'/result.json',JSON.stringify({ok:true,layouts,largeFlag:flag,largePortrait:portrait,largeRankBadge:badge,nineMatchingFrames:true,narrowNoHorizontalOverflow:true,errors,realMatchJoins:0},null,2));
 console.log('PASS centred growth avatar, removed growth rank, enlarged duel banner/portrait/badge, nine corresponding frames and narrow layout.');
}catch(error){await page.screenshot({path:out+'/failure.png'});throw error;}finally{await browser.close();await vite.close();}
