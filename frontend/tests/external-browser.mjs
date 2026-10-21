import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdtemp,rm} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const profile=await mkdtemp(path.join(os.tmpdir(),'tb-external-fixture-'));
let browser,server;
const counts={cf:0,ac:0,nc:0,lg:0}, reads={cf:0,ac:0};
const cfHeader='<header id="header"><a href="/profile/fixture">fixture</a></header>';
const acHeader='<nav class="navbar"><a href="/users/fixture">fixture</a></nav>';
const row=(key,id,verdict)=>`<table class="status-frame-datatable"><tr><th>Submission</th><th>Status</th></tr><tr><td><a href="${key==='cf'?'/contest/123/submission/':'/contests/abc100/submissions/'}${id}">${id}</a><a href="${key==='cf'?'/contest/123/problem/A':'/contests/abc100/tasks/abc100_a'}">A</a><a href="${key==='cf'?'/profile/fixture':'/users/fixture'}">fixture</a><span class="${key==='cf'?'submissionVerdictWrapper':'label'}">${verdict}</span></td></tr></table>`;
async function until(read,accept,timeout=30000){const deadline=Date.now()+timeout;let last;while(Date.now()<deadline){last=await read();if(accept(last))return last;await new Promise(r=>setTimeout(r,150));}throw new Error('Condition timed out: '+JSON.stringify(last));}
try{
 browser=await chromium.launchPersistentContext(profile,{channel:'msedge',headless:true,args:['--remote-debugging-port=0']});
 await browser.route('**/*',async route=>{
  const request=route.request(),url=new URL(request.url());
  const key=url.hostname==='codeforces.com'?'cf':url.hostname==='atcoder.jp'?'ac':url.hostname==='ac.nowcoder.com'?'nc':url.hostname==='www.luogu.com.cn'?'lg':null;
  if(!key)return route.fulfill({status:503,body:'Fixture denies external network'});
  if(request.method()==='POST'){
   counts[key]++;
   const body=request.postData();assert.ok(body.includes('int+main')||body.includes('int main')||body.includes('int%20main'));
   if(key==='cf'||key==='ac')return route.fulfill({contentType:'text/html',body:(key==='cf'?cfHeader:acHeader)+row(key,key==='cf'?1002:2002,'TESTING')});
   return route.fulfill({contentType:'application/json',body:JSON.stringify(key==='nc'?{code:0,data:{submissionId:3001}}:{rid:4001})});
  }
  if(key==='cf'&&url.pathname==='/api/user.status')return route.fulfill({contentType:'application/json',body:JSON.stringify({status:'OK',result:counts.cf?[{id:1002,verdict:++reads.cf>1?'OK':'TESTING',problem:{contestId:123,index:'A'},author:{members:[{handle:'fixture'}]}}]:[]})});
  if((key==='cf'&&url.pathname.endsWith('/my'))||(key==='ac'&&url.pathname.endsWith('/submissions/me')))return route.fulfill({contentType:'text/html',body:(key==='cf'?cfHeader:acHeader)+(counts[key]?row(key,key==='cf'?1002:2002,++reads[key]>1?'AC':'TESTING'):'<table><tr><th>Submission</th><th>Status</th></tr></table>')});
  if(key==='nc'&&url.pathname==='/status')return route.fulfill({contentType:'application/json',body:JSON.stringify({code:0,data:{submissionId:3001,status:5}})});
  if(key==='lg'&&url.pathname.startsWith('/record/'))return route.fulfill({contentType:'application/json',body:JSON.stringify({data:{record:{id:4001,problem:{pid:'P1000'},user:{uid:123},status:12}}})});
  const task=key==='ac'?'abc100_a':'A';
  const metadata=key==='nc'?'<script>window.globalInfo={ownerId:123};window.pageInfo={contestId:100,questionId:1001}</script>':key==='lg'?'<script id="lentille-context" type="application/json">{"user":{"uid":123},"data":{"problem":{"pid":"P1000"}}}</script>':'';
  const nativeScript=['nc','lg'].includes(key)?`<script>document.querySelector('form').onsubmit=e=>{e.preventDefault();fetch('${key==='nc'?'/submit_cd':'/fe/api/problem/submit/P1000'}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(${key==='nc'?'{questionId:1001,userId:123,content:document.querySelector("textarea").value}':'{lang:12,code:document.querySelector("textarea").value}'})});}</script>`:'';
  return route.fulfill({contentType:'text/html',body:(key==='cf'?cfHeader:key==='ac'?acHeader:'')+metadata+`<form method="post"><input type="hidden" name="csrf_token" value="site-native-token"><select name="${key==='ac'?'data.TaskScreenName':'submittedProblemIndex'}"><option value="${task}">${task}</option></select><select name="${key==='cf'?'programTypeId':'language'}"><option value="54">GNU C++17</option></select><textarea name="source"></textarea><button type="submit">${['nc','lg'].includes(key)?'提交':'Submit'}</button></form>`+nativeScript});
 });
 server=spawn(process.env.TB_PYTHON||(process.platform==='win32'?'python':'python3'),['desktop/tests/external_server.py'],{cwd:root,env:{...process.env,TB_OFFLINE:'1',TB_EXTERNAL_FIXTURE_PROFILE:profile,PYTHONIOENCODING:'utf-8'},windowsHide:true});
 let stderr='';server.stderr.on('data',b=>stderr+=b);
 const port=await new Promise((resolve,reject)=>{let text='';server.stdout.on('data',b=>{text+=b;if(text.includes('\n'))resolve(JSON.parse(text.split('\n')[0]).port);});server.on('exit',code=>reject(new Error('Fixture exited '+code+' '+stderr)));});
 const base='http://127.0.0.1:'+port;
 for(const [key,url]of Object.entries({cf:'https://codeforces.com/contest/123/problem/A',ac:'https://atcoder.jp/contests/abc100/tasks/abc100_a',nc:'https://ac.nowcoder.com/acm/contest/100/A',lg:'https://www.luogu.com.cn/problem/P1000'})){
  const tab=await browser.newPage();await tab.goto('about:blank');
  const connection=await browser.newCDPSession(tab);const {targetInfo}=await connection.send('Target.getTargetInfo');await connection.detach();
  await fetch(base+'/prepare?'+new URLSearchParams({id:targetInfo.targetId}));
  const value=await(await fetch(base+'/create?'+new URLSearchParams({url}))).json();assert.equal(value.transport,'external');
  const repeated=await(await fetch(base+'/create?'+new URLSearchParams({url}))).json();assert.equal(repeated.sessionId,value.sessionId,'An in-flight request reuses the same intent');
  const saved=await until(async()=>({saved:await(await fetch(base+'/saved')).json(),status:await(await fetch(base+'/status')).json(),diagnostic:stderr,counts}),v=>v.saved.some(item=>item.sessionId===value.sessionId));
  assert.equal(saved.saved.find(item=>item.sessionId===value.sessionId).verdict,'AC');assert.equal(counts[key],1,'one native click per TB intent');
  assert.equal(tab.isClosed(),false,'result window stays open before display acknowledgment');
  const closed=await(await fetch(base+'/ack?'+new URLSearchParams({id:value.sessionId}))).json();assert.equal(closed.closed,true);
  await until(()=>tab.isClosed(),Boolean);
  const repeatedAck=await(await fetch(base+'/ack?'+new URLSearchParams({id:value.sessionId}))).json();assert.equal(repeatedAck.closed,true,'close is idempotent');

 }
 assert.equal(browser.serviceWorkers().length,0,'No browser extension is installed');
 console.log(JSON.stringify({ok:true,nativeFormPosts:counts,receiptSavedForAllFour:true,browserExtension:false,realAccountSubmission:false}));
}finally{server?.kill();await browser?.close();assert.ok(path.basename(profile).startsWith('tb-external-fixture-'));await rm(profile,{recursive:true,force:true});}
