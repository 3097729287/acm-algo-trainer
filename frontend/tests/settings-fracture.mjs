import assert from 'node:assert/strict';
import {createServer} from 'vite';
import {chromium} from 'playwright';
import {mkdir,writeFile} from 'node:fs/promises';

const out='../.backups/fracture-physics-20261105';await mkdir(out,{recursive:true});
const vite=await createServer({cacheDir:out+'/vite',optimizeDeps:{entries:['tests/settings-interactions-fixture.html']},server:{host:'127.0.0.1',port:0,watch:null}});await vite.listen();
const base=`http://127.0.0.1:${vite.httpServer.address().port}`;
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const errors=[],proof=[];let ok=false;
const median=values=>values.sort((a,b)=>a-b)[Math.floor(values.length/2)];
async function sample(page,selector){return page.locator(selector).evaluate(svg=>({
 time:Number(svg.dataset.fractureTime||0),phase:svg.dataset.fracturePhase,
 pieces:[...svg.querySelectorAll('[data-fracture-piece]')].map(piece=>{
  const cx=Number(piece.dataset.sourceX),cy=Number(piece.dataset.sourceY),m=piece.transform.baseVal.consolidate()?.matrix;
  return {mode:piece.dataset.fractureMode,state:piece.dataset.fractureState,x:m?m.a*cx+m.c*cy+m.e:cx,y:m?m.b*cx+m.d*cy+m.f:cy,cx,cy};
 })
}));}
async function capture(page,selector,kind,name){
 const tile=page.locator(selector).locator('..');
 await tile.evaluate(node=>node.scrollIntoView({block:'center'}));
 const box=await tile.boundingBox();
 const viewport=page.viewportSize(),x=Math.max(0,box.x),y=Math.max(0,box.y);
 await page.screenshot({path:`${out}/${name}-${kind}.png`,clip:{x,y,width:Math.min(box.width,viewport.width-x),height:Math.min(box.height,viewport.height-y)}});
}
try{
 for(const width of [2048,1294,800,430])for(const theme of ['dark','light']){
  const page=await browser.newPage({viewport:{width,height:1152}});page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>{let state=713;Math.random=()=>((state=Math.imul(state,1664525)+1013904223>>>0)/4294967296);});
  await page.clock.install();
  await page.goto(base+'/tests/settings-interactions-fixture.html');
  await page.locator('[data-scene-interactive=bulb]').waitFor();
  await page.evaluate(theme=>{document.documentElement.dataset.theme=theme;document.documentElement.dataset.motion='on';},theme);
  await page.clock.pauseAt(await page.evaluate(()=>Date.now()+100));
  const bulb=page.locator('[data-scene-interactive=bulb]');
  for(let i=0;i<6;i++)await bulb.dispatchEvent('click');
  const glass='.bulb-glass-fragments';
  assert.equal(await page.locator(glass).getAttribute('data-fracture-phase'),'separating','No crack hold or slow separation ramp');
  const first=await sample(page,glass);assert(first.pieces.length>=22);
  assert.equal(await page.locator(glass+' [data-fracture-piece] .bulb-glass').count(),first.pieces.length);
  await page.clock.runFor(64);const early=await sample(page,glass);
  const local=early.pieces.filter(p=>p.mode==='collapse').map(p=>Math.hypot(p.x-p.cx,p.y-p.cy));
  const eject=early.pieces.filter(p=>p.mode==='eject').map(p=>Math.hypot(p.x-p.cx,p.y-p.cy));
  assert(Math.max(...eject)>5&&Math.max(...eject)>median(local)*1.6,'Immediate mixed local collapse and outward flight');
  if(width===2048)await capture(page,glass,'bulb-064ms',theme);
  await page.clock.runFor(176);if(width===2048)await capture(page,glass,'bulb-240ms',theme);
  await page.clock.runFor(660);const late=await sample(page,glass);
  if(width===2048||width===430)await capture(page,glass,'bulb-900ms',`${width}-${theme}`);
  assert(late.pieces.filter(p=>p.state==='resting').length>=late.pieces.length*.4,`Glass settles after contact: ${late.pieces.filter(p=>p.state==='resting').length}/${late.pieces.length}, t=${late.time}`);
  assert.equal(await page.locator('svg.scene-bulb>.scene-bulb').evaluate(node=>getComputedStyle(node).visibility),'visible');
  await page.clock.runFor(600);assert.equal(await page.locator(glass).count(),0);assert.equal(await page.locator('svg.scene-bulb').getAttribute('data-scene-state'),null);

  const coffee=page.locator('[data-scene-interactive=coffee]');
  await coffee.evaluate(node=>node.scrollIntoView({block:'center'}));
  const cup=coffee.locator('.coffee-cup'),box=await cup.boundingBox(),cx=box.x+box.width/2,cy=box.y+box.height/2;
  await page.mouse.move(cx,cy);await page.mouse.down();await page.mouse.move(cx+8,cy-95,{steps:8});await page.mouse.up();
  for(let i=0;i<60&&await page.locator('.coffee-shards').count()===0;i++)await page.clock.runFor(16);
  const ceramic='.coffee-shards';assert.equal(await page.locator(ceramic).count(),1,'A real cup drag and ground impact triggers fracture');
  const cupFirst=await sample(page,ceramic);assert(cupFirst.pieces.length>=20);assert.equal(await page.locator(ceramic+' .coffee-steam').count(),0);
  assert(cupFirst.time>=1/60-.001,'The contact frame already advances and renders the fracture');
  assert(await page.locator(ceramic+' [data-fracture-piece]').evaluateAll(pieces=>pieces.every(piece=>piece.hasAttribute('transform'))),'No complete, stationary cup pose is presented on contact');
  assert(Math.max(...cupFirst.pieces.filter(p=>p.mode==='eject').map(p=>Math.hypot(p.x-p.cx,p.y-p.cy)))>2,'Ejected fragments are visibly separate on the contact frame');
  assert(median(cupFirst.pieces.filter(p=>p.mode==='collapse').map(p=>Math.hypot(p.x-p.cx,p.y-p.cy)))>1,'The main cup wall already collapses on the first contact frame');
  assert.equal(await page.locator(ceramic).getAttribute('data-material'),'ceramic');
  await page.clock.runFor(64);const cupEarly=await sample(page,ceramic);
  const cupSpread=Math.max(...cupEarly.pieces.filter(p=>p.mode==='eject').map(p=>Math.hypot(p.x-p.cx,p.y-p.cy)));
  assert(cupSpread>8,'Ceramic separates immediately on impact');
  if(width===2048)await capture(page,ceramic,'cup-064ms',theme);
  await page.clock.runFor(176);if(width===2048)await capture(page,ceramic,'cup-240ms',theme);
  await page.clock.runFor(660);const cupLate=await sample(page,ceramic);
  if(width===2048||width===430)await capture(page,ceramic,'cup-900ms',`${width}-${theme}`);
  assert(cupLate.pieces.filter(p=>p.state==='resting').length>=cupLate.pieces.length*.4,`Ceramic settles after contact: ${cupLate.pieces.filter(p=>p.state==='resting').length}/${cupLate.pieces.length}, t=${cupLate.time}`);
  assert.equal(await page.evaluate(()=>window.sceneEntered),undefined,'Decorative gestures keep their settings tile open');
  await page.clock.runFor(600);assert.equal(await page.locator(ceramic).count(),0);assert.equal(await coffee.getAttribute('transform'),null);
  assert.equal(await coffee.evaluate(node=>getComputedStyle(node).visibility),'visible');
  proof.push({width,theme,glassPieces:first.pieces.length,ceramicPieces:cupFirst.pieces.length,earlyEjectedDistance:Math.max(...eject),earlyCollapseDistance:median(local),glassResting:late.pieces.filter(p=>p.state==='resting').length,ceramicResting:cupLate.pieces.filter(p=>p.state==='resting').length,ceramicEarlySpread:cupSpread,restored:true});
  await page.close();
 }
 // Explicit reduced motion settings skip the burst and still restore both items.
 for(const preference of ['os','app']){
  const page=await browser.newPage({viewport:{width:1294,height:960}});page.on('pageerror',e=>errors.push(e.message));
  await page.emulateMedia({reducedMotion:preference==='os'?'reduce':'no-preference'});
  await page.goto(base+'/tests/settings-interactions-fixture.html');await page.locator('[data-scene-interactive=bulb]').waitFor();
  if(preference==='app')await page.evaluate(()=>document.documentElement.dataset.motion='off');
  for(let i=0;i<6;i++)await page.locator('[data-scene-interactive=bulb]').dispatchEvent('click');
  assert.equal(await page.locator('.bulb-glass-fragments').count(),0);
  await page.waitForTimeout(150);assert.equal(await page.locator('svg.scene-bulb').getAttribute('data-scene-state'),null);
  const coffee=page.locator('[data-scene-interactive=coffee]');await coffee.evaluate(node=>node.scrollIntoView({block:'center'}));
  const box=await coffee.locator('.coffee-cup').boundingBox();
  await page.mouse.move(box.x+box.width/2,box.y+box.height/2);await page.mouse.down();await page.mouse.move(box.x+box.width/2,box.y+box.height/2-80,{steps:5});await page.mouse.up();
  await page.waitForTimeout(180);assert.equal(await page.locator('.coffee-shards').count(),0);assert.equal(await coffee.getAttribute('transform'),null);
  proof.push({reducedMotion:preference,noBurst:true,restored:true});await page.close();
 }
 // Real time, with both fracture simulations running alongside the other
 // settings decorations. Virtual time above establishes reproducible poses.
 const realtime=await browser.newPage({viewport:{width:2048,height:1152}});realtime.on('pageerror',e=>errors.push(e.message));
 await realtime.goto(base+'/tests/settings-interactions-fixture.html');await realtime.locator('[data-scene-interactive=bulb]').waitFor();
 await realtime.evaluate(()=>{window.fractureFrameTimes=[];const start=performance.now();let previous=start;const frame=now=>{window.fractureFrameTimes.push(now-previous);previous=now;if(now-start<1700)requestAnimationFrame(frame);};requestAnimationFrame(frame);});
 for(let i=0;i<6;i++)await realtime.locator('[data-scene-interactive=bulb]').dispatchEvent('click');
 const realCup=await realtime.locator('.coffee-vessel .coffee-cup').boundingBox();
 await realtime.mouse.move(realCup.x+realCup.width/2,realCup.y+realCup.height/2);await realtime.mouse.down();await realtime.mouse.move(realCup.x+realCup.width/2,realCup.y+realCup.height/2-100,{steps:8});await realtime.mouse.up();
 await realtime.waitForTimeout(1800);
 const intervals=await realtime.evaluate(()=>window.fractureFrameTimes.filter(dt=>dt>0));intervals.sort((a,b)=>a-b);
 const performanceProof={realtime:true,frames:intervals.length,medianFrameMs:median([...intervals]),p95FrameMs:intervals[Math.floor(intervals.length*.95)],longestFrameMs:intervals.at(-1)};
 assert(intervals.length>=45,'Both effects make steady progress in real time');
 assert.equal(await realtime.locator('.bulb-glass-fragments,.coffee-shards').count(),0,'Effects finish in real time and leave no overlays');
 proof.push(performanceProof);await realtime.close();
 assert.deepEqual(errors,[]);ok=true;console.log(JSON.stringify({ok,proof,errors}));
}finally{
 await writeFile(out+'/verification.json',JSON.stringify({ok,proof,errors},null,2));
 await browser.close();await vite.close();
}
