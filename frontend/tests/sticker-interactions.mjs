import assert from 'node:assert/strict';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const server=await createServer({cacheDir:'../.backups/next-150/vite-sticker-interactions',server:{host:'127.0.0.1',port:0,watch:null}});await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true}),page=await browser.newPage({viewport:{width:1280,height:820}}),errors=[];page.on('pageerror',error=>errors.push(error.message));page.setDefaultTimeout(12000);
await page.addInitScript(()=>{
 const catalogue=['duck','semicolon','rainbow','envelope','orbit','gem','crown','galaxy','phoenix','cloud','leaf'].map((shape,i)=>({id:'art-'+shape,shape,title:shape,rarity:i<9?'legendary':'common'})),units=catalogue.map((item,i)=>({id:'unit-'+item.shape,stickerId:item.id,revision:0,placement:{x:.12+(i%4)*.24,y:.18+Math.floor(i/4)*.3,angle:0,scale:1}}));
 localStorage.setItem('tb.sticker-layout.v1:fixture-a',JSON.stringify({version:1,owner:'fixture-a',revision:1,catalogue,units}));
 window.stickerAudioEvents=[];window.stickerSamples=[];
 const decodeGate=new Promise(resolve=>{window.releaseDuckDecode=resolve;});
 const Audio=window.AudioContext;window.AudioContext=class extends Audio{
  decodeAudioData(bytes){return super.decodeAudioData(bytes).then(async buffer=>{await decodeGate;return buffer;});}
  createOscillator(){window.stickerAudioEvents.push('oscillator');return super.createOscillator();}
  createBufferSource(){window.stickerAudioEvents.push('sample');const source=super.createBufferSource(),start=source.start.bind(source);source.start=(at,offset=0,duration)=>{if(source.buffer){const data=source.buffer.getChannelData(0),rate=source.buffer.sampleRate,from=Math.floor(offset*rate),to=Math.min(data.length,from+Math.floor(.25*rate));let squares=0;for(let i=from;i<to;i++)squares+=data[i]*data[i];window.stickerSamples.push({offset,duration,openingRms:Math.sqrt(squares/(to-from))});}return start(at,offset,duration);};return source;}
 };
});
try{
 const requests=[];page.on('request',request=>{if(/\/stickers\/.*\.svg/.test(request.url()))requests.push(request.url());});
 await page.goto(`http://127.0.0.1:${server.httpServer.address().port}/tests/sticker-interactions-fixture.html`);
 await page.locator('.placed-sticker').first().waitFor();assert.equal(await page.locator('.placed-sticker').count(),11,'Confirmed cached stickers show before the 1.4-second inventory response');
 assert(await page.locator('.placed-sticker img').evaluateAll(nodes=>nodes.every(node=>node.src.startsWith('data:image/svg+xml;base64,'))));
 assert.equal(requests.length,0,'No per-sticker network load');
 await page.screenshot({path:'../.backups/next-150/sticker-material-dark.png'});
 await page.getByRole('button',{name:'传说贴纸 duck',exact:true}).click();
 assert.deepEqual(await page.evaluate(()=>window.stickerAudioEvents),[],'First click never substitutes a synthetic duck');
 await page.evaluate(()=>window.releaseDuckDecode());
 await page.waitForFunction(()=>window.stickerSamples.length===1);
 const quack=await page.evaluate(()=>window.stickerSamples[0]);
 assert(quack.openingRms>.045,'Selected recording begins with an audible quack, not its quiet opening');
 assert.deepEqual(await page.evaluate(()=>window.stickerAudioEvents),['sample']);
 await page.evaluate(()=>window.stickerFeedbackFixture.audioReady());
 for(const shape of ['semicolon','rainbow','envelope','orbit','gem','crown','galaxy','phoenix']){
  const before=await page.evaluate(()=>window.stickerAudioEvents.length);await page.getByRole('button',{name:'传说贴纸 '+shape,exact:true}).click();
  await page.locator(`[data-sticker-reaction="${shape}"]`).waitFor();assert(await page.evaluate(before=>window.stickerAudioEvents.length>before,before),shape+' has a sound');
 }
 const before=await page.evaluate(()=>window.stickerAudioEvents.length);await page.getByRole('button',{name:'普通贴纸 cloud',exact:true}).click();assert.equal(await page.evaluate(()=>window.stickerAudioEvents.length),before);
 await page.locator('[data-sticker-reaction]').waitFor({state:'detached'});
 await page.evaluate(()=>document.documentElement.dataset.theme='light');await page.screenshot({path:'../.backups/next-150/sticker-material-light.png'});
 await page.evaluate(()=>window.stickerFeedbackFixture.switchOwner());await page.waitForFunction(()=>document.querySelectorAll('.placed-sticker').length===0);assert.equal(await page.locator('.placed-sticker').count(),0,'Another owner never sees the previous account cache');
 assert.deepEqual(errors,[]);console.log('PASS eleven cached placements before inventory; embedded vectors; all nine legendary sounds/effects; first-click natural duck recording with audible onset; no synthetic duck; quiet ordinary stickers; fade cleanup; account isolation');
}catch(error){await page.screenshot({path:'../.backups/next-150/sticker-interactions-error.png'});throw error;}finally{await browser.close();await server.close();}
