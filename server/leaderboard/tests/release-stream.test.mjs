import test from 'node:test';
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {listenFixture} from './listen.mjs';
import {createHash,randomUUID} from 'node:crypto';
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {createReleaseStream} from '../src/release-stream.mjs';
import {releaseStreamProxy,RELEASE_STREAM_PROXY} from '../scripts/prepare-release-stream-proxy.mjs';
import {readFile} from 'node:fs/promises';
const bytes=Buffer.from('verified public release fixture');
const name='TB-Update-1.4.0-to-1.5.2-win64.zip';
test('release forwarding changes only the missing-asset route and preserves the account proxy',async()=>{
 const current=await readFile(new URL('../Caddyfile',import.meta.url),'utf8');
 const previous=current.replace(RELEASE_STREAM_PROXY,'');
 assert.notEqual(previous,current);assert.equal(releaseStreamProxy(previous),current);assert.equal(releaseStreamProxy(current),current);
 assert.throws(()=>releaseStreamProxy(previous+previous));assert.throws(()=>releaseStreamProxy(previous.replace('header @assets','header @other')));
});
async function fixture(fetcher,overrides={},streamOptions={}){
 const directory=resolve('../../.backups/cleanup-startup/release-stream-tests',randomUUID());await mkdir(directory,{recursive:true});
 const file=directory+'/index.json';await writeFile(file,JSON.stringify({schema:1,assets:[{version:'1.5.2',name,size:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex'),...overrides}]}));
 const stream=createReleaseStream(file,{...streamOptions,fetcher}),server=createServer((request,response)=>stream(request,response));await listenFixture(server);
 return {url:'http://127.0.0.1:'+server.address().port+'/assets/1.5.2/',async close(){server.closeAllConnections();await new Promise(resolve=>server.close(resolve));}};
}
const response=data=>new Response(data,{headers:{'content-length':String(data.length)}});

test('retained release history may exceed one hundred entries but the index remains bounded',async()=>{
 for(const count of [128,256,257]){
  const directory=resolve('../../.backups/cleanup-startup/release-stream-tests',randomUUID());await mkdir(directory,{recursive:true});
  const entries=Array.from({length:count},(_,i)=>({version:`1.0.${i}`,name:`TB-Setup-1.0.${i}-win64.exe`,size:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')}));
  const file=directory+'/index.json';await writeFile(file,JSON.stringify({schema:1,assets:entries}));
  const stream=createReleaseStream(file,{fetcher:async()=>{throw Error('HEAD must not fetch upstream');}}),server=createServer((request,response)=>stream(request,response));await listenFixture(server);
  try{
   const item=entries.at(-1),url=`http://127.0.0.1:${server.address().port}/assets/${item.version}/${item.name}`;
   const head=await fetch(url,{method:'HEAD'});assert.equal(head.status,count<=256?200:503);
   if(count<=256)assert.equal(head.headers.get('x-content-sha256'),item.sha256);
  }finally{server.closeAllConnections();await new Promise(resolve=>server.close(resolve));}
 }
});
test('approved public files stream intact; HEAD uses the index and request secrets are never forwarded',async()=>{
 const calls=[];const f=await fixture(async(url,options)=>{calls.push({url,options});return response(bytes);});
 try{
  const head=await fetch(f.url+name,{method:'HEAD'});assert.equal(head.status,200);assert.equal(Number(head.headers.get('content-length')),bytes.length);assert.equal(calls.length,0);
  const result=await fetch(f.url+name,{headers:{Authorization:'must-not-forward',Cookie:'must-not-forward'}});assert.equal(result.status,200);assert.deepEqual(Buffer.from(await result.arrayBuffer()),bytes);
  assert.equal(calls[0].url,'https://github.com/3097729287/acm-algo-trainer/releases/download/v1.5.2/'+name);assert.equal(calls[0].options.redirect,'manual');assert(!Object.keys(calls[0].options.headers).some(key=>/authorization|cookie/i.test(key)));
  for(const path of ['ToBe-Admin-Setup-1.5.2-win64.exe',name+'?url=https://evil.invalid','not-published.zip'])assert.equal((await fetch(f.url+path)).status,404);
  assert.equal(calls.length,1);
 }finally{await f.close();}
});
test('private redirects, wrong sizes and corrupt bytes never complete an accepted download',async()=>{
 for(const mode of ['redirect','size','hash']){
  const f=await fixture(async()=>mode==='redirect'?new Response(null,{status:302,headers:{location:'https://127.0.0.1/private'}}):mode==='size'?response(Buffer.alloc(1)):response(Buffer.alloc(bytes.length)));
  try{if(mode==='hash')await assert.rejects(async()=>{const result=await fetch(f.url+name);await result.arrayBuffer();});else assert.equal((await fetch(f.url+name)).status,503);}finally{await f.close();}
 }
});
test('a bounded number of slow streams leave the account service with backpressure and recover their slots',async()=>{
 const producers=[];let aborts=0;
 const f=await fixture(async(url,{signal})=>new Response(new ReadableStream({start(controller){producers.push(controller);controller.enqueue(bytes.subarray(0,1));signal.addEventListener('abort',()=>{aborts++;try{controller.error(Error('cancelled'));}catch{}});}}),{headers:{'content-length':String(bytes.length)}}));
 try{
  const a=await fetch(f.url+name),b=await fetch(f.url+name);assert.equal(a.status,200);assert.equal(b.status,200);
  assert.equal((await fetch(f.url+name)).status,429);
  for(const controller of producers){controller.enqueue(bytes.subarray(1));controller.close();}
  assert.deepEqual(Buffer.from(await a.arrayBuffer()),bytes);assert.deepEqual(Buffer.from(await b.arrayBuffer()),bytes);
  const c=await fetch(f.url+name);assert.equal(c.status,200);await c.body.cancel();
 }finally{await f.close();}
});


test('a stalled upstream expires and releases its slot for a later verified download',async()=>{
 let attempts=0,expired;
 const f=await fixture(async(url,{signal})=>{
  if(++attempts>1)return response(bytes);
  expired=signal;
  return new Promise((resolve,reject)=>signal.addEventListener('abort',()=>reject(signal.reason),{once:true}));
 },{},{maximumActive:1,transferTimeoutMs:30});
 try{
  assert.equal((await fetch(f.url+name)).status,503);assert(expired.aborted);
  const next=await fetch(f.url+name);assert.equal(next.status,200);assert.deepEqual(Buffer.from(await next.arrayBuffer()),bytes);
 }finally{await f.close();}
});
