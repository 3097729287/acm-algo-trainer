// Static MAIN-world boundary with the production dispatcher. No browser/OJ.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
const source=await readFile(new URL('../browser_extension/main.js',import.meta.url),'utf8');
const location=new URL('https://codeforces.com/contest/123/virtual');
let owner='other',starts=0;const listeners=[],messages=[];
const window={addEventListener:(name,callback)=>{if(name==='message')listeners.push(callback)},postMessage:value=>messages.push(value)};window.top=window;
const box={window,location,URL,Map,crypto,setTimeout,clearTimeout,
 tbOfficialPage:()=>null,tbConnectedRead:()=>({ready:'complete'}),
 tbConnectedIdentity:()=>({platform:'Codeforces',url:location.href,state:'logged_in',owner}),
 tbVirtualContest:()=>{starts++;return {state:'dispatched'}}};
vm.runInNewContext(source,box);
function start(command){for(const listener of listeners)listener({source:window,origin:location.origin,data:{tbBrowserCommand:'fixture',action:'control',context:{platform:'Codeforces',sessionId:'page-fixture',expectedOwner:'fixture',controlCommand:command,control:{kind:'virtual',context:{action:'start'}}}}})}
start(1);assert.equal(starts,0);assert.equal(messages.at(-1).value.value.state,'login');
owner='fixture';start(1);assert.equal(starts,0,'An already refused command is not replayed');
start(2);start(2);assert.equal(starts,1,'The exact native command is called once');
owner='other';start(3);assert.equal(starts,1,'Changed original-site owner is checked again immediately before VP start');
console.log('PASS static MAIN v4 owner boundary and at-most-once native VP dispatch');
