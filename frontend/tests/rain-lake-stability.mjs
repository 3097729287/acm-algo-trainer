import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {createServer} from 'vite';
import {chromium} from 'playwright';

const out=resolve('../.backups/rain-rebuild-20261107/checks');await mkdir(out,{recursive:true});
const server=await createServer({server:{host:'127.0.0.1',port:0,hmr:false},optimizeDeps:{entries:['tests/library-backgrounds-fixture.html']}});await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[],remote=[],checks=[];
page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url())&&!['127.0.0.1','localhost'].includes(new URL(r.url()).hostname))remote.push(r.url());});
try{
 await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/tests/library-backgrounds-fixture.html`);await page.waitForFunction(()=>window.MotionScene);
 await page.evaluate(()=>{const host=document.createElement('div');host.id='capture';host.style.cssText='position:fixed;inset:0;z-index:99999';document.body.append(host);window.engine=new MotionScene(host,{id:'rainfall'});});
 await page.waitForFunction(()=>engine.host.dataset.ready==='true');await page.waitForTimeout(2500);
 await page.evaluate(()=>engine.setPaused(true));
 const propagation=await page.evaluate(()=>{
  const r=engine.rain,w=r.water,sky=r.weather,state=w.glState;
  state.sim.clear();w.drops=[];w.accumulator=0;w.render();
  const gl=state.gl,canvas=w.canvas,W=canvas.width,H=canvas.height;
  const pixels=()=>{w.render();const data=new Uint8Array(W*H*4);gl.readPixels(0,0,W,H,gl.RGBA,gl.UNSIGNED_BYTE,data);return data;};
  const baseline=pixels(),count=r.impactCount,system=sky.systems.get('rain'),drop={...system.particles[0]};
  Object.assign(drop,{x:800,y:648,landY:650,vy:650,phase:650,depth:.65});
  const survived=system.step(drop,.02,sky.context),impact=r.lastImpact;
  const marker=document.createElement('i');marker.style.cssText=`position:absolute;left:${impact.local.x}px;top:${impact.local.y}px;width:0;height:0`;r.surface.append(marker);
  const point=marker.getBoundingClientRect();marker.remove();
  const readings=[];
  for(let i=0;i<360;i++){
   w.frame(1/60);
   if([59,179,299,359].includes(i)){
    const data=pixels(),radii=[];let peak=0;
    const cx=impact.local.x/W*W,cy=H-impact.local.y/H*H;
    for(let y=0;y<H;y++)for(let x=0;x<W;x++){
     const k=(y*W+x)*4,d=Math.max(Math.abs(data[k]-baseline[k]),Math.abs(data[k+1]-baseline[k+1]),Math.abs(data[k+2]-baseline[k+2]));
     peak=Math.max(peak,d);if(d>=2)radii.push(Math.hypot(x-cx,y-cy));
    }
    radii.sort((a,b)=>a-b);readings.push({seconds:(i+1)/60,pixels:radii.length,radius95:radii[Math.floor(radii.length*.95)]||0,peak});
   }
  }
  return{survived,impacts:r.impactCount-count,projectionError:Math.hypot(point.x-impact.screen.x,point.y-impact.screen.y),readings};
 });
 assert.equal(propagation.survived,false);assert.equal(propagation.impacts,1,'One actual rain particle crossing the lake stamps one wave, without a random discard');
 assert(propagation.projectionError<.1,JSON.stringify(propagation));
 assert(propagation.readings[2].pixels>20,'A single impact remains visible five seconds later: '+JSON.stringify(propagation));
 assert(propagation.readings[2].radius95>propagation.readings[0].radius95+25,'The same wave actually travels outwards: '+JSON.stringify(propagation));
 checks.push({causalImpactAndPropagation:propagation});

 const stress=await page.evaluate(()=>{
  const r=engine.rain,w=r.water,sky=r.weather;w.glState.sim.clear();w.drops=[];w.accumulator=0;
  sky.set({rain:{density:.8}});const sim=w.glState.sim,gl=w.glState.gl;
  const sample=()=>{w.render();const W=w.canvas.width,H=w.canvas.height,parts=[];for(const [x,y]of [[.2,.2],[.5,.2],[.8,.2],[.2,.65],[.5,.65],[.8,.65]]){const p=new Uint8Array(64*64*4);gl.readPixels(Math.floor((W-64)*x),Math.floor((H-64)*y),64,64,gl.RGBA,gl.UNSIGNED_BYTE,p);parts.push(p);}return parts;};
  const start=r.impactCount;let maximumQueued=0,elapsed=0;
  for(let i=0;i<2400;i++){sky.frame(1/60,elapsed+=1000/60);maximumQueued=Math.max(maximumQueued,w.drops.length/4);w.frame(1/60);}
  let previous=sample(),maxDelta=0,maxMeanDelta=0,brightFlashes=0;const means=[];
  for(let f=0;f<45;f++){
   sky.frame(1/60,elapsed+=1000/60);w.frame(1/60);const next=sample();let deltaSum=0,total=0,mean=0;
   for(let p=0;p<next.length;p++)for(let k=0;k<next[p].length;k+=4){
    for(let c=0;c<3;c++){const delta=Math.abs(next[p][k+c]-previous[p][k+c]);maxDelta=Math.max(maxDelta,delta);deltaSum+=delta;total++;mean+=next[p][k+c];if(delta>32)brightFlashes++;}
   }
   means.push(mean/total);maxMeanDelta=Math.max(maxMeanDelta,deltaSum/total);previous=next;
  }
  const glError=gl.getError();return{seconds:elapsed/1000,impacts:r.impactCount-start,maximumQueued,maxDelta,maxMeanDelta,brightnessRange:Math.max(...means)-Math.min(...means),brightFlashes,glError,sameSimulation:sim===w.glState.sim,randomWaterRain:w.options.rain,flash:sky.stats().flash};
 });
 assert(stress.impacts>1500,JSON.stringify(stress));assert(stress.sameSimulation,'Dense rain retains the same bounded GPU height field');assert.equal(stress.randomWaterRain,null);assert.equal(stress.flash,0);assert.equal(stress.glError,0);
 assert.equal(stress.brightFlashes,0,'Dense ripples must not produce high-contrast per-frame flashes: '+JSON.stringify(stress));
 assert(stress.maxMeanDelta<2&&stress.brightnessRange<1,'Water brightness stays stable under dense impacts: '+JSON.stringify(stress));checks.push({denseRainStability:stress});
 await page.screenshot({path:resolve(out,'dense-rain.png')});

 for(const width of [2048,1200,640,390]){
  await page.setViewportSize({width,height:900});await page.waitForTimeout(120);
  const mapping=await page.evaluate(()=>{
   const r=engine.rain,errors=[];
   for(const x of [r.width*.1,r.width*.5,r.width*.9])for(const y of [r.height*.3,r.height*.6,r.height*.95]){
    const p=r.lakePoint(x,y),marker=document.createElement('i');marker.style.cssText=`position:absolute;left:${p.x}px;top:${p.y}px;width:0;height:0`;r.surface.append(marker);const b=marker.getBoundingClientRect();marker.remove();errors.push(Math.hypot(b.x-x,b.y-y));
   }
   return{maxError:Math.max(...errors),canvasWidth:r.canvas.width,hostWidth:r.width};
  });assert(mapping.maxError<.1,JSON.stringify({width,mapping}));assert(mapping.canvasWidth<=width*1.05);checks.push({width,mapping});
 }
 await page.setViewportSize({width:1600,height:1000});await page.waitForTimeout(100);
 await page.evaluate(async()=>{await engine.setScene('rainfall');engine.setPaused(false);});await page.waitForTimeout(1800);
 await page.screenshot({path:resolve(out,'rain-lake-dark.png')});
 const before=await page.evaluate(()=>{engine.setPaused(true);return{frames:engine.frames,picture:engine.snapshot()};});await page.waitForTimeout(120);assert(await page.evaluate(()=>engine.snapshot())===before.picture,'Paused water must preserve the exact frame');assert.equal(await page.evaluate(()=>engine.frames),before.frames);
 await page.evaluate(()=>engine.setLightning(true));assert.equal(await page.evaluate(()=>engine.rain.weather.options.effects.has('lightning')),true);await page.evaluate(()=>engine.setLightning(false));assert.equal(await page.evaluate(()=>engine.rain.weather.options.effects.has('lightning')),false);
 await page.evaluate(()=>{document.documentElement.dataset.theme='light';});await page.waitForFunction(()=>engine.host.dataset.ready==='true'&&engine.rain!==undefined);await page.waitForTimeout(150);await page.screenshot({path:resolve(out,'rain-lake-light.png')});
 await page.emulateMedia({reducedMotion:'reduce'});await page.waitForFunction(()=>engine.host.dataset.paused==='true');const reduced=await page.evaluate(()=>engine.frames);await page.waitForTimeout(100);assert.equal(await page.evaluate(()=>engine.frames),reduced);
 await page.evaluate(()=>engine.destroy());const callbacks=await page.evaluate(async()=>(await import('/src/vendor/elementalfx/packages/core/src/ticker.ts')).activeFrameCallbacks());assert.equal(callbacks,0,'Switching away releases both public effects and their shared animation loop');
 assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);
 const result={ok:true,library:'https://github.com/iyerav42/elementalfx',checks,pauseAndReducedMotion:true,lightningOptional:true,offline:true,errors};await writeFile(resolve(out,'result.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
}catch(error){await page.screenshot({path:resolve(out,'failure.png')});throw error;}finally{await browser.close();await server.close();}
