// Exercise the production worker against browser API doubles; no site/network.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';

const source=await readFile(new URL('../browser_extension/worker.js',import.meta.url),'utf8');
const base='http://127.0.0.1:12345',url='https://ac.nowcoder.com/acm/problem/21992';
const plain=value=>JSON.parse(JSON.stringify(value));

function fixture(existing=false){
 const state={windows:existing?[{id:7,incognito:false,focused:false}]:[],tabs:existing?[{id:70,windowId:7,incognito:false,url:'https://example.com/'}]:[],local:{},session:{},calls:[],answer:{ack:true},nextTab:100};
 const storage=kind=>({get:async key=>typeof key==='string'?{[key]:structuredClone(state[kind][key])}:structuredClone(state[kind]),set:async value=>Object.assign(state[kind],structuredClone(value))});
 const chrome={
  storage:{local:storage('local'),session:storage('session')},
  runtime:{id:'fixture-extension',getManifest:()=>({version:'1.6.14'}),getURL:path=>'chrome-extension://fixture-extension/'+path,onMessage:{addListener(){}},onStartup:{addListener(){}},onInstalled:{addListener(){}}},
  alarms:{create(){},onAlarm:{addListener(){}}},
  windows:{getAll:async()=>structuredClone(state.windows),create:async options=>{
   state.calls.push(['window.create',options]);
   const window={id:10,incognito:false,focused:false},tab={id:state.nextTab++,windowId:10,incognito:false,url:options.url};
   state.windows.push(window);state.tabs.push(tab);return {...window,tabs:[tab]};
  },update:async(id,options)=>{state.calls.push(['window.update',id,options]);return {id,...options}}},
  tabs:{query:async query=>state.tabs.filter(tab=>query.windowId===undefined||tab.windowId===query.windowId).filter(tab=>!query.url||tab.url.startsWith('https://ac.nowcoder.com/')),
   create:async options=>{state.calls.push(['tab.create',options]);const tab={id:state.nextTab++,windowId:options.windowId,incognito:false,url:options.url};state.tabs.push(tab);return tab},
   get:async id=>{const tab=state.tabs.find(tab=>tab.id===id);if(!tab)throw Error('gone');return tab},
   update:async(id,options)=>{state.calls.push(['tab.update',id,options]);Object.assign(state.tabs.find(tab=>tab.id===id),options)},
   remove:async id=>{state.calls.push(['tab.remove',id]);state.tabs=state.tabs.filter(tab=>tab.id!==id)},sendMessage:async()=>({state:'unknown'})},
 };
 const context=vm.createContext({chrome,TB_CONNECTION_BASE:base,importScripts(){},setInterval(){},setTimeout(){},clearTimeout(){},URL,Map,crypto,Date,TextEncoder,AbortSignal,navigator:{userAgent:'Edg/fixture'},
  fetch:async(address,options)=>{
   const body=JSON.parse(options.body);state.calls.push(['request',address,body]);
   const answer=address.endsWith('/register')?{key:'local-capability'}:address.endsWith('/queue')?{jobs:[]}:body.claim?{url,status:'loading'}:state.answer;
   return {ok:true,json:async()=>structuredClone(answer)};
  }});
 vm.runInContext(source,context);
 return {state,context,create:async()=>context.createJob({sessionId:'official-fixture',key:'job-capability'},base,'client-fixture',structuredClone(state.windows),state.tabs.filter(tab=>tab.url===url)),
  tick:async()=>{const job=Object.values(state.session.jobs||{})[0];return context.handle({type:'tick'},{id:'fixture-extension',frameId:0,url,tab:{id:job.tabId,windowId:state.tabs.find(tab=>tab.id===job.tabId).windowId}})}};
}

const closed=fixture();await closed.create();
assert.deepEqual(plain(closed.state.calls.find(call=>call[0]==='window.create')[1]),{url:'about:blank',type:'normal',state:'minimized',focused:false});
let job=Object.values(closed.state.session.jobs)[0];
assert.equal(job.ownedWindowId,10);
assert(closed.state.calls.some(call=>call[0]==='tab.update'&&call[1]===job.tabId&&call[2].muted===true&&call[2].url===url));
assert(closed.state.calls.filter(call=>call[0]==='window.update').every(call=>call[2].state==='minimized'&&call[2].focused===false),'Normal submit can only minimize its own window');
await closed.create();assert.equal(closed.state.calls.filter(call=>call[0]==='window.create').length,1,'Reconnect reuses the same job tab');
closed.state.answer={reveal:true,status:'needs_login'};await closed.tick();
assert.deepEqual(plain(closed.state.calls.filter(call=>call[0]==='window.update').at(-1).slice(1)),[10,{state:'normal',focused:true}]);
closed.state.answer={status:'judging'};await closed.tick();
assert.deepEqual(plain(closed.state.calls.filter(call=>call[0]==='window.update').at(-1).slice(1)),[10,{state:'minimized',focused:false}]);
closed.state.answer={reveal:true,status:'needs_verification'};await closed.tick();
closed.state.tabs.push({id:999,windowId:10,incognito:false,url:'https://example.com/keep'});
const before=closed.state.calls.filter(call=>call[0]==='window.update').length;
closed.state.answer={status:'judging'};await closed.tick();
assert.equal(closed.state.calls.filter(call=>call[0]==='window.update').length,before,'Do not minimize a window containing a new user tab');
closed.state.answer={stop:true,closeOwned:true,status:'finished'};await closed.tick();
assert.deepEqual(closed.state.tabs.map(tab=>tab.id),[999],'After the visible-result ACK, close only the owned tab');

const open=fixture(true);await open.create();
job=Object.values(open.state.session.jobs)[0];
assert.equal(open.state.calls.filter(call=>call[0]==='window.create').length,0);
assert(open.state.calls.some(call=>call[0]==='tab.create'&&call[1].windowId===7&&call[1].active===false));
assert(!open.state.calls.some(call=>call[0]==='tab.update'&&call[1]===70),'Other tabs keep their audio and selection');
open.state.answer={reveal:true,status:'needs_login'};await open.tick();open.state.answer={status:'judging'};
const frontCount=open.state.calls.filter(call=>call[0]==='window.update').length;await open.tick();
assert.equal(open.state.calls.filter(call=>call[0]==='window.update').length,frontCount,'Never minimize the existing user browser');
await new Promise(resolve=>setImmediate(resolve));
assert(closed.state.calls.some(call=>call[0]==='request'&&call[1].endsWith('/register')&&call[2].backgroundWindows===true));
console.log('PASS background connector: no-window startup, quiet reuse, login/captcha reveal, return to background and exact tab cleanup.');
