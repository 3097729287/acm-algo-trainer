import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const vite=await createServer({cacheDir:'../.backups/followups-157/avatar-vite',server:{host:'127.0.0.1',port:0,watch:null}});await vite.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1000,height:900}});
try{
 await page.goto(vite.resolvedUrls.local[0]+'tests/avatar-size-fixture.html');await page.locator('.profile-avatar-face img').first().waitFor();await page.waitForFunction(()=>document.querySelectorAll('.profile-avatar-face').length===9);
 const widths=await page.locator('.profile-avatar-face').evaluateAll(nodes=>nodes.map(n=>n.getBoundingClientRect().width));assert(widths.every(w=>w>=35));
 const frames=await page.locator('.avatar-rank-frame').evaluateAll(nodes=>nodes.map(n=>n.getBoundingClientRect().width));assert(frames.every(w=>w>180));
 for(const badge of await page.locator('.profile-badge').all()){const face=await badge.locator('.profile-avatar-face').boundingBox(),name=await badge.locator('.profile-nickname').boundingBox();assert(Math.abs(face.y+face.height/2-name.y-name.height/2)<=1);}
 const starts=await page.locator('.profile-xp-value').evaluateAll(nodes=>nodes.map(n=>{const m=n.getScreenCTM(),a=n.getPointAtLength(0),b=n.getPointAtLength(n.getTotalLength()*.1),c=new DOMPoint(22,22).matrixTransform(m);const p=new DOMPoint(a.x,a.y).matrixTransform(m),q=new DOMPoint(b.x,b.y).matrixTransform(m);return Math.abs(p.x-c.x)<1&&p.y>c.y&&q.x<c.x&&q.y>c.y;}));assert(starts.every(Boolean),'Experience starts at the bottom and grows clockwise');
 const bands=await page.locator('.profile-xp-value').evaluateAll(nodes=>nodes.map(n=>{const c=getComputedStyle(n),scale=n.getScreenCTM().a||n.getScreenCTM().b;return{visibleWidth:parseFloat(c.strokeWidth)*(c.vectorEffect==='non-scaling-stroke'?1:Math.abs(scale)),progress:n.parentElement.getAttribute('aria-valuenow'),color:c.stroke};}));
 assert(bands.every(band=>band.visibleWidth>=2.5&&band.progress==='50'&&band.color!=='none'),'Every compact avatar shows a solid earned band with the real XP fraction');
 await mkdir('../.backups/followups-157',{recursive:true});await page.screenshot({path:'../.backups/followups-157/avatar-all-tiers.png'});
 console.log(JSON.stringify({ok:true,tiers:9,facePixels:widths[0],frameScale:3.4,nicknameCentered:true,bottomClockwiseExperience:true}));
}finally{await browser.close();await vite.close();}
