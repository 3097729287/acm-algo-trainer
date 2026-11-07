import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const out='../.backups/header-catalogue-audio-20261106/stickers';await mkdir(out,{recursive:true});
const server=await createServer({cacheDir:out+'/vite',optimizeDeps:{entries:['tests/sticker-interactions-fixture.html']},server:{host:'127.0.0.1',port:0,watch:null}});await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1280,height:820}}),errors=[];page.on('pageerror',error=>errors.push(error.message));page.setDefaultTimeout(12000);
await page.addInitScript(()=>{
 const catalogue=['duck','semicolon','rainbow','envelope','orbit','gem','crown','galaxy','phoenix','cloud','leaf','owl','rocket'].map((shape,i)=>({id:'art-'+shape,shape,title:shape,rarity:i<9||shape==='rocket'?'legendary':shape==='owl'?'rare':'common'})),units=catalogue.map((item,i)=>({id:'unit-'+item.shape,stickerId:item.id,revision:0,placement:item.shape==='rocket'?{x:.52,y:.27,angle:78,scale:1.5}:{x:.12+(i%4)*.24,y:.18+Math.floor(i/4)*.3,angle:0,scale:1}}));
 localStorage.setItem('tb.sticker-layout.v1:fixture-a',JSON.stringify({version:1,owner:'fixture-a',revision:1,catalogue,units}));
 window.stickerAudioEvents=[];window.stickerSamples=[];window.duckCodecCalls=0;
 const Audio=window.AudioContext;window.AudioContext=class extends Audio{
  decodeAudioData(){window.duckCodecCalls++;return new Promise(()=>{});}
  createOscillator(){window.stickerAudioEvents.push('oscillator');return super.createOscillator();}
  createBufferSource(){window.stickerAudioEvents.push('sample');const source=super.createBufferSource(),start=source.start.bind(source);source.start=(at,offset=0,duration)=>{if(source.buffer){const data=source.buffer.getChannelData(0),rate=source.buffer.sampleRate,from=Math.floor(offset*rate),to=Math.min(data.length,from+Math.floor(.005*rate));let squares=0;for(let i=from;i<to;i++)squares+=data[i]*data[i];window.stickerSamples.push({offset,duration,bufferDuration:source.buffer.duration,rate:source.playbackRate.value,openingRms:Math.sqrt(squares/(to-from)),scheduledLeadMs:(at-this.currentTime)*1000});}return start(at,offset,duration);};return source;}
 };
});
try{
 const requests=[];page.on('request',request=>{if(/\/stickers\/.*\.svg/.test(request.url()))requests.push(request.url());});
 await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/tests/sticker-interactions-fixture.html`);
 await page.locator('.placed-sticker').first().waitFor();assert.equal(await page.locator('.placed-sticker').count(),13,'Cached placements show before the inventory response');
 assert(await page.locator('.placed-sticker img').evaluateAll(nodes=>nodes.every(node=>node.src.startsWith('data:image/svg+xml;base64,'))));assert.equal(requests.length,0);
 const duck=page.getByRole('button',{name:'传说贴纸 duck',exact:true});
 await duck.click({force:true});
 const quack=await page.evaluate(()=>window.stickerSamples[0]);
 assert(quack.openingRms>.003,'The first 5 ms already contains the original duck call');assert.equal(quack.offset,0);assert.equal(quack.rate,1);assert(quack.scheduledLeadMs<=1);assert.equal(await page.evaluate(()=>window.duckCodecCalls),0,'Cold playback does not wait for asynchronous codec decoding');
 assert.deepEqual(await page.evaluate(()=>window.stickerAudioEvents),['sample']);
 const rapidAt=Date.now();for(let i=0;i<6;i++)await duck.click({force:true});assert(Date.now()-rapidAt<450,'The regression really exercises clicks inside the former throttle');
 assert.equal(await page.evaluate(()=>window.stickerSamples.length),7,'Every rapid duck click starts a separate voice');
 assert(await page.evaluate(()=>window.stickerSamples.every(sample=>sample.rate===1&&Math.abs(sample.bufferDuration-.336)<.001)),'All voices use the same approved source recording, without its silent lead-in');
 const owl=page.getByRole('button',{name:'稀有贴纸 owl',exact:true}),beforeOwl=await page.evaluate(()=>window.stickerAudioEvents.length);
 for(let i=0;i<5;i++)await owl.click({force:true});assert.equal(await page.evaluate(()=>window.stickerAudioEvents.length)-beforeOwl,20,'Every ordinary owl click starts its four original tones');
 const gem=page.getByRole('button',{name:'传说贴纸 gem',exact:true}),beforeGem=await page.evaluate(()=>window.stickerAudioEvents.length);await gem.click({force:true});await gem.click({force:true});assert.equal(await page.evaluate(()=>window.stickerAudioEvents.length)-beforeGem,3,'Special effects retain their original guard');
 for(const shape of ['semicolon','rainbow','envelope','orbit','crown','galaxy','phoenix']){
  const before=await page.evaluate(()=>window.stickerAudioEvents.length);await page.getByRole('button',{name:'传说贴纸 '+shape,exact:true}).click({force:true});
  await page.locator(`[data-sticker-reaction="${shape}"]`).waitFor();assert(await page.evaluate(before=>window.stickerAudioEvents.length>before,before),shape+' has sound and motion');
 }
 const before=await page.evaluate(()=>window.stickerAudioEvents.length);await page.getByRole('button',{name:'普通贴纸 cloud',exact:true}).click({force:true});assert.equal(await page.evaluate(()=>window.stickerAudioEvents.length),before);
 await page.waitForTimeout(1650);assert.equal(await page.locator('[data-sticker-reaction]').count(),0);
 const rocket=page.getByRole('button',{name:'传说贴纸 rocket',exact:true}),origin=await rocket.boundingBox(),saved=await page.evaluate(()=>JSON.stringify(window.stickerFeedbackFixture.state()));
 await rocket.click({force:true});const flight=rocket.locator('.rocket-flight');await flight.locator('[data-sticker-reaction=rocket]').waitFor();
 await flight.evaluate(node=>{window.rocketAnimation=node.getAnimations().find(animation=>animation.effect.getKeyframes().some(frame=>frame.transform));window.rocketAnimation.pause();window.rocketAnimation.currentTime=0;});
 const frames=[];for(const progress of [0,.12,.35,.55,.76,.94,1]){
  await page.evaluate(progress=>window.rocketAnimation.currentTime=3400*progress,progress);await page.waitForTimeout(20);
  frames.push(await flight.evaluate((node,progress)=>({progress,transform:getComputedStyle(node).transform,opacity:getComputedStyle(node).opacity,box:(()=>{const b=node.getBoundingClientRect();return {x:b.x,y:b.y,width:b.width,height:b.height};})()}),progress));
  if(progress===.35)await page.screenshot({path:out+'/rocket-flight.png'});
 }
 assert(Math.hypot(frames[2].box.x-frames[0].box.x,frames[2].box.y-frames[0].box.y)>35,'The actual rocket travels visibly');assert(frames.every(frame=>Number(frame.opacity)===1),'Rocket stays visible for the full loop');
 assert(Math.abs(frames.at(-1).box.x-frames[0].box.x)<.1&&Math.abs(frames.at(-1).box.y-frames[0].box.y)<.1,'It returns exactly to its saved location');
 assert.deepEqual(await rocket.boundingBox(),origin,'The saved placement and hit area remain fixed');
 await duck.click({force:true});assert.equal(await flight.locator('[data-sticker-reaction=rocket]').count(),1,'An ordinary click does not cut short a rocket flight');
 const beforeAgain=await page.evaluate(()=>window.stickerAudioEvents.length);await rocket.click({force:true});assert.equal(await page.evaluate(()=>window.stickerAudioEvents.length),beforeAgain,'Rocket cannot restart midway around its loop');
 assert.equal(await page.evaluate(()=>JSON.stringify(window.stickerFeedbackFixture.state())),saved,'Decorative motion writes no inventory or placement changes');
 await page.evaluate(()=>window.rocketAnimation.finish());await flight.locator('[data-sticker-reaction=rocket]').waitFor({state:'detached'});
 await page.emulateMedia({reducedMotion:'reduce'});await rocket.click({force:true});assert.equal(await flight.evaluate(node=>node.getAnimations().length),0,'Reduced motion does not fly the rocket');
 await page.evaluate(()=>document.documentElement.dataset.theme='light');await page.screenshot({path:out+'/stickers-light.png'});
 await page.evaluate(()=>window.stickerFeedbackFixture.switchOwner());await page.waitForFunction(()=>document.querySelectorAll('.placed-sticker').length===0);
 assert.deepEqual(errors,[]);const result={ok:true,cachedStickers:13,duckLeadInMs:134,coldPlaybackImmediate:true,duckRapidClicks:7,ordinaryRapidClicks:5,specialEffectsGuarded:true,rocketLoop:true,rocketNoseAligned:true,rocketPlacementUnchanged:true,reducedMotion:true,ownerIsolation:true,frames,errors};await writeFile(out+'/result.json',JSON.stringify(result,null,2));console.log(JSON.stringify({...result,frames:undefined}));
}catch(error){await page.screenshot({path:out+'/failure.png'});throw error;}finally{await browser.close();await server.close();}
