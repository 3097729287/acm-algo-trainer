import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const out='../.backups/cleanup-startup/banner-growth';await mkdir(out,{recursive:true});
const vite=await createServer({cacheDir:out+'/vite',server:{host:'127.0.0.1',port:0,watch:null}});await vite.listen();
const browser=await chromium.launch({channel:'msedge',headless:true}),page=await browser.newPage({viewport:{width:2048,height:1152}}),errors=[],layouts=[];
page.on('pageerror',error=>errors.push(error.message));page.setDefaultTimeout(10000);
try{
 await page.goto(`http://127.0.0.1:${vite.httpServer.address().port}/tests/growth-material-fixture.html`);await page.locator('.sticker-content').waitFor();
 for(const width of [2048,1440,960,430]){
  await page.setViewportSize({width,height:1152});
  const layout=await page.evaluate(()=>{const content=document.querySelector('.sticker-content').getBoundingClientRect();return {contentWidth:content.width,overflow:document.documentElement.scrollWidth>innerWidth};});
  assert(!layout.overflow);assert(layout.contentWidth>200);assert.equal(await page.locator('.growth-dashboard .profile-badge,.account-hero-identity').count(),0,'Growth leaves the sticker area free of the moved profile');layouts.push({width,...layout});
  if(width===2048)await page.screenshot({path:out+'/growth-centred.png'});
 }
 await page.setViewportSize({width:2048,height:1152});await page.evaluate(()=>growthCheck.setPanel('duel'));await page.locator('.duel-banner-frame').waitFor();
 const flag=await page.locator('.duel-lobby-identity').boundingBox(),portrait=await page.locator('.profile-avatar-button').boundingBox(),badge=await page.locator('.duel-lobby-rank>svg').boundingBox();
 assert(flag.width>=370&&flag.height>=510);assert(portrait.width>=180);assert(badge.width>=90);await page.screenshot({path:out+'/duel-large.png'});
 assert.equal(await page.locator('.duel-profile-titles .title-medal').count(),3);assert.equal(await page.locator('.duel-lobby-identity .profile-xp-ring').count(),1);
 await page.getByRole('tab',{name:'思维对决',exact:true}).click();await page.locator('.thought-rating').waitFor();assert.equal(await page.locator('.duel-profile-titles .title-medal').count(),3);await page.getByRole('tab',{name:'排位',exact:true}).click();await page.locator('.duel-banner-frame').waitFor();
 for(let tier=0;tier<9;tier++){
  await page.evaluate(value=>growthCheck.setTier(value),tier);await page.waitForFunction(value=>document.querySelector('.duel-banner-frame')?.dataset.tier===String(value),tier);
  assert.equal(await page.locator('.duel-lobby-rank>svg').count(),1,'Duel rank badge remains present');
  assert.equal(await page.locator('.duel-lobby-identity .avatar-rank-frame').getAttribute('data-rank-art'),await page.locator('.duel-banner-frame').getAttribute('data-rank-art'));
  assert.equal(await page.locator('.duel-lobby-rank>svg').getAttribute('data-rank-art'),await page.locator('.duel-banner-frame').getAttribute('data-rank-art'));
 }
 await page.screenshot({path:out+'/challenger-reference.png'});
 await page.evaluate(()=>growthCheck.setPanel('banners'));await page.locator('.banner-gallery').waitFor();assert.equal(await page.locator('.duel-banner-frame').count(),9);
 const uniqueness=await page.locator('.duel-banner-frame').evaluateAll(nodes=>({tiers:new Set(nodes.map(n=>n.dataset.tier)).size,artworks:new Set(nodes.map(n=>n.dataset.rankArt)).size,ids:[...document.querySelectorAll('svg defs [id]')].map(n=>n.id)}));
 assert.equal(uniqueness.tiers,9);assert.equal(uniqueness.artworks,9);assert.equal(new Set(uniqueness.ids).size,uniqueness.ids.length);
 const assets=await page.locator('svg image').evaluateAll(async nodes=>await Promise.all([...new Set(nodes.map(n=>n.getAttribute('href')))].map(src=>new Promise(resolve=>{const image=new Image();image.onload=()=>resolve({src,ok:image.naturalWidth>0});image.onerror=()=>resolve({src,ok:false});image.src=src;}))));
 assert(assets.every(asset=>asset.ok),'Every original rank sprite must load');
 await page.screenshot({path:out+'/nine-tier-frames.png',fullPage:true});
 await page.evaluate(()=>growthCheck.setPanel('duel'));await page.setViewportSize({width:430,height:850});await page.locator('.duel-banner-frame').waitFor();assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 await page.screenshot({path:out+'/duel-narrow.png'});
 await page.evaluate(()=>growthCheck.setPanel('topbar'));await page.setViewportSize({width:2048,height:1152});await page.locator('.live-contest').waitFor();
 for(const theme of ['dark','light']){
  await page.evaluate(value=>growthCheck.theme(value),theme);
  const metric=await page.locator('.live-contest').evaluate(node=>{const style=getComputedStyle(node),a=node.getBoundingClientRect(),b=document.querySelector('.topbar-status-chip').getBoundingClientRect();return {border:style.borderTopWidth,background:style.backgroundColor,shadow:style.boxShadow,centreDelta:Math.abs(a.top+a.height/2-b.top-b.height/2),height:a.height};});
  assert.equal(metric.border,'0px');assert.equal(metric.shadow,'none');assert.equal(metric.background,'rgba(0, 0, 0, 0)');assert(metric.centreDelta<1&&metric.height===40);
 }
 await page.screenshot({path:out+'/aligned-timer.png'});assert.deepEqual(errors,[]);
 await writeFile(out+'/result.json',JSON.stringify({ok:true,layouts,largeFlag:flag,largePortrait:portrait,largeRankBadge:badge,nineMatchingFrames:true,narrowNoHorizontalOverflow:true,errors,realMatchJoins:0},null,2));
 console.log('PASS empty growth sticker area, moved profile/medals in both duel modes, enlarged duel banner/portrait/badge, nine corresponding frames and narrow layout.');
}catch(error){await page.screenshot({path:out+'/failure.png'});throw error;}finally{await browser.close();await vite.close();}
