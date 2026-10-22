import assert from 'node:assert/strict';
import {createServer} from 'vite';
import {chromium} from 'playwright';
const server=await createServer({server:{host:'127.0.0.1',port:18835,strictPort:true}});
await server.listen();
const browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[];
page.on('pageerror',error=>errors.push(error.message));
try{
 await page.goto('http://127.0.0.1:18835/tests/ui-feedback-fixture.html?view=radar-performance');
 await page.waitForFunction(()=>window.radarReady);
 const first=await page.evaluate(()=>window.radarReady-window.radarStarted);
 const times=[];
 for(let i=0;i<15;i++){
  const result=await page.evaluate(async()=>{
   const started=performance.now();document.querySelector('.radar-node').dispatchEvent(new MouseEvent('click',{bubbles:true}));
   await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
   return {ms:performance.now()-started,secondary:!!document.querySelector('[aria-label$="二级雷达"]'),available:[...document.querySelectorAll('.radar-detail-row')].map(row=>row.children[2].textContent)};
  });
  assert.equal(result.secondary,true);assert(result.available.some(value=>!value.endsWith('/ 0')));
  times.push(result.ms);await page.getByRole('button',{name:'返回一级雷达',exact:true}).click();
 }
 assert(first<1500,`6000-row first render took ${first} ms`);assert(Math.max(...times)<500,JSON.stringify(times));assert.deepEqual(errors,[]);
 console.log(JSON.stringify({rows:6000,firstRenderMs:Math.round(first),secondaryMedianMs:Math.round([...times].sort((a,b)=>a-b)[7]),secondaryMaxMs:Math.round(Math.max(...times)),switches:times.length}));
}finally{await browser.close();await server.close();}
