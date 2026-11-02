import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {createInterface} from 'node:readline';
import {chromium} from 'playwright';
import {startFixture} from '../../server/leaderboard/tests/local-server.mjs';

const shared=await startFixture();
const output=resolve('../.backups/next-150/navigation-bootstrap-browser-'+Date.now());await mkdir(output,{recursive:true});
const server=spawn(process.env.TB_PYTHON||'python',['tests/admin-server.py',shared.endpoint],{
 cwd:process.cwd(),env:{...process.env,TB_OFFLINE:'1',TB_STATE_DIR:output,TB_UI_DIST:resolve('dist')},stdio:['pipe','pipe','pipe']});
let stderr='';server.stderr.on('data',chunk=>{stderr+=chunk.toString();});
const line=createInterface({input:server.stdout});
const ready=new Promise((resolve,reject)=>{
 line.once('line',text=>{try{resolve(JSON.parse(text));}catch(error){reject(error);}});
 server.once('exit',code=>reject(new Error('Fixture closed '+code+' '+stderr)));
});
let browser,release;const blocked=new Promise(resolve=>{release=resolve;});let pending=0;
const report={ok:false,fullInsightsHeld:true,originalSiteSubmissions:0,productionChanges:0};
try{
 const {baseUrl}=await ready;
 browser=await chromium.launch({channel:process.env.CI?undefined:'msedge',headless:true,args:['--explicitly-allowed-ports='+new URL(baseUrl).port]});
 const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];
 page.on('pageerror',error=>errors.push(error.message));
 await page.route('**/api/insights',async route=>{pending++;await blocked;await route.continue();});
 await page.goto(baseUrl,{waitUntil:'domcontentloaded'});
 await page.locator('.problem-table').waitFor();
 await page.locator('.sidebar .nav-item').filter({hasText:'维基百科'}).waitFor();
 assert(await page.locator('.sidebar .nav-item').count()>=13,'Confirmed level exposes actual navigation while insights is held');
 assert.equal(await page.locator('.navigation-pending').count(),0);
 assert(pending>0,'The slow statistics response is still blocked');
 assert.equal(await page.locator('.account-form').count(),0,'Normal authenticated administrator entry');
 report.navigationItems=await page.locator('.sidebar .nav-item').allTextContents();
 report.confirmed=await page.evaluate(async()=>{const result=await fetch('/api/navigation');return result.json();});
 assert.equal(report.confirmed.level,100);assert.equal(report.confirmed.confirmed,true);
 assert.equal(report.confirmed.authority.owner,await page.evaluate(()=>window.__tbAccountUserId));
 await page.screenshot({path:output+'/navigation-without-full-insights.png'});
 assert.deepEqual(errors,[]);report.ok=true;release();
}finally{
 release();if(browser)await browser.close();server.stdin.end();
 await new Promise(resolve=>{if(server.exitCode!==null)return resolve();server.once('exit',resolve);});
 await shared.close();await writeFile(output+'/report.json',JSON.stringify(report,null,2)+'\n');
}
console.log(JSON.stringify({ok:report.ok,navigationItems:report.navigationItems?.length,evidence:output}));
