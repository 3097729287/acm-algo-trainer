// Observe the actual frozen desktop WebView. Never launch a replacement page.
import {createRequire} from 'node:module';
import {resolve} from 'node:path';
const require=createRequire(import.meta.url),{chromium}=require('playwright');
const [port,profile,screenshot]=process.argv.slice(2);
const normalized=value=>value.replaceAll('\\','/').toLowerCase();
const deadline=Date.now()+45000;
let browser;
while(Date.now()<deadline&&!browser){
 try{browser=await chromium.connectOverCDP('http://127.0.0.1:'+Number(port),{timeout:800});}
 catch{await new Promise(resolve=>setTimeout(resolve,25));}
}
if(!browser)throw Error('Isolated WebView debugging endpoint did not appear');
const session=await browser.newBrowserCDPSession();
const command=await session.send('Browser.getBrowserCommandLine');
if(!command.arguments.some(value=>normalized(value).includes(normalized(resolve(profile)))))
 throw Error('Refusing to inspect a browser outside this isolated profile');
let state,page;
while(Date.now()<deadline){
 page=browser.contexts().flatMap(context=>context.pages()).find(page=>page.url().startsWith('http://127.0.0.1:'));
 if(page){
  try{
   state=await page.evaluate(()=>({shell:!!document.querySelector('.app-shell'),
    titles:[...document.querySelectorAll('.problem-title')].map(node=>node.textContent),
    login:!!document.querySelector('.account-form'),error:document.querySelector('[role=alert]')?.textContent||''}));
   if(state.shell&&state.titles.some(title=>title.includes('A+B'))){
    // Flush at the observation point. Parent timing includes this IPC cost.
    process.stdout.write(JSON.stringify({ok:true,...state})+'\n');
    if(screenshot)await page.screenshot({path:screenshot});
    process.exit(0);
   }
  }catch(error){if(error.message.includes('outside this isolated'))throw error;}
 }
 await new Promise(resolve=>setTimeout(resolve,25));
}
process.stdout.write(JSON.stringify({ok:false,lastDom:state})+'\n');
process.exit(1);
