import test from 'node:test';
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {mkdtemp,writeFile,rm} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {createHash} from 'node:crypto';
import {setTimeout as pause} from 'node:timers/promises';
import {createReleaseStream,validateReleaseIndex,RELEASE_CHUNK_BYTES as CHUNK} from '../src/release-stream.mjs';
import {listenFixture} from './listen.mjs';

const hash=data=>createHash('sha256').update(data).digest('hex');
const name='ToBe-Full-Setup-1.6.10-win64.exe',fixed='https://github.com/3097729287/acm-algo-trainer/releases/download/v1.6.10/'+name;
async function fixture(options={}){
 const root=await mkdtemp(path.join(os.tmpdir(),'tb-release-ranges-')),raw=Buffer.alloc(7*CHUNK+12345);
 for(let i=0;i<raw.length;i++)raw[i]=(i*17+Math.floor(i/CHUNK)*31)%251;
 const sha=hash(raw),item={version:'1.6.10',name,size:raw.length,sha256:sha,githubDigest:'sha256:'+sha,chunkBytes:CHUNK,chunkSha256:Array.from({length:Math.ceil(raw.length/CHUNK)},(_,i)=>hash(raw.subarray(i*CHUNK,(i+1)*CHUNK))),...options.item};
 const index=path.join(root,'index.json');await writeFile(index,JSON.stringify({schema:1,assets:[item]}));
 const state={requests:[],active:0,maximum:0,disconnectOnce:null,corrupt:null,stall:false,bodyStall:false,delayMs:1,badRange:false,badEncoding:false};
 const source=createServer(async(req,res)=>{
  const range=/^bytes=(\d+)-(\d+)$/.exec(req.headers.range||'');
  if(!range){res.writeHead(400);res.end();return;}
  const start=Number(range[1]),end=Number(range[2]),number=Math.floor(start/CHUNK);
  state.requests.push({range:req.headers.range,authorization:req.headers.authorization||'',cookie:req.headers.cookie||''});
  state.active++;state.maximum=Math.max(state.maximum,state.active);let closed=false;
  res.once('close',()=>{closed=true;state.active--;});
  if(state.stall)return;
  const headers={'Content-Length':String(end-start+1),'Content-Range':state.badRange?'bytes 0-1/2':`bytes ${start}-${end}/${raw.length}`};
  if(state.badEncoding)headers['Content-Encoding']='gzip';
  res.writeHead(206,headers);res.flushHeaders();
  if(state.bodyStall){res.write(raw.subarray(start,start+16));return;}
  for(let offset=start;offset<=end&&!closed;offset+=65536){
   const part=Buffer.from(raw.subarray(offset,Math.min(offset+65536,end+1)));
   if(state.corrupt===number&&offset===start)part[5]^=1;
   res.write(part);
   if(state.disconnectOnce===number){state.disconnectOnce=null;await pause(5);res.destroy();return;}
   if(state.delayMs)await pause(state.delayMs);
  }
  if(!closed)res.end();
 });
 await listenFixture(source);const sourceOrigin='http://127.0.0.1:'+source.address().port;
 const fetcher=options.fetcher||((url,settings)=>{assert.equal(url,fixed);return fetch(sourceOrigin+'/original',settings);});
 const stream=createReleaseStream(index,{fetcher,...options.stream}),server=createServer((req,res)=>stream(req,res));await listenFixture(server);
 const url='http://127.0.0.1:'+server.address().port+'/updates/assets/1.6.10/'+item.name;
 return {root,raw,item,index,state,url,async close(){server.closeAllConnections();source.closeAllConnections();await Promise.all([new Promise(resolve=>server.close(resolve)),new Promise(resolve=>source.close(resolve))]);assert.equal(path.dirname(root),os.tmpdir());assert(path.basename(root).startsWith('tb-release-ranges-'));await rm(root,{recursive:true,force:true});}};
}
async function until(condition){for(let i=0;i<300;i++){if(condition())return;await pause(5);}assert.fail('Fixture state deadline exceeded');}
async function incomplete(url,options){
 const response=await fetch(url,options);let count=0,failed=false;
 try{for await(const part of response.body)count+=part.length;}catch{failed=true;}
 return {status:response.status,count,failed};
}

test('loopback full installer uses four reusable verified buffers and preserves exact ordered bytes',async()=>{
 const f=await fixture();const original=Buffer.allocUnsafe;let pools=0;
 try{
  Buffer.allocUnsafe=function(size,...args){if(size===CHUNK)pools++;return original.call(this,size,...args);};
  const response=await fetch(f.url,{headers:{Authorization:'never-forward',Cookie:'never-forward','X-User-Url':'https://untrusted.example'}});
  assert.equal(response.status,200);assert.equal(response.headers.get('accept-ranges'),'bytes');
  const h=createHash('sha256');let count=0;for await(const block of response.body){h.update(block);count+=block.length;}
  assert.equal(count,f.raw.length);assert.equal(h.digest('hex'),f.item.sha256);
  assert.equal(pools,4,'One reusable 1 MiB buffer per prefetch slot; no file-size allocation');
  assert(f.state.maximum>=2&&f.state.maximum<=4);assert.equal(f.state.requests.length,8);
  assert(f.state.requests.every(r=>!r.authorization&&!r.cookie));
 }finally{Buffer.allocUnsafe=original;await f.close();}
});

test('loopback interrupted source retries only the same one-MiB range then completes',async()=>{
 const f=await fixture();f.state.disconnectOnce=1;
 try{
  const response=await fetch(f.url);assert.equal(hash(Buffer.from(await response.arrayBuffer())),f.item.sha256);
  const attempts=f.state.requests.filter(r=>r.range===`bytes=${CHUNK}-${2*CHUNK-1}`);
  assert.equal(attempts.length,2);assert.equal(f.state.requests.filter(r=>r.range===`bytes=0-${CHUNK-1}`).length,1);
 }finally{await f.close();}
});

test('each configured prefetch width1 through4 remains bounded and a public filename alias keeps the fixed original',async()=>{
 for(const width of [1,2,3,4]){
  const alias='ToBe-Setup-1.6.10-win64.exe';
  const f=await fixture({item:{name:alias,sourceName:name},stream:{prefetch:width}});
  try{
   const response=await fetch(f.url);assert.equal(response.headers.get('content-disposition'),'attachment; filename="'+alias+'"');
   assert.equal(hash(Buffer.from(await response.arrayBuffer())),f.item.sha256);
   assert(f.state.maximum>=1&&f.state.maximum<=width);
  }finally{await f.close();}
 }
});

test('loopback arbitrary-offset Range and If-Range reconstruct exactly without fetching an unrelated prefix',async()=>{
 const f=await fixture();
 try{
  const start=CHUNK+123,end=2*CHUNK+777;
  const head=await fetch(f.url,{method:'HEAD',headers:{Range:`bytes=${start}-${end}`}});
  assert.equal(head.status,206);assert.equal(Number(head.headers.get('content-length')),end-start+1);assert.equal(f.state.requests.length,0);
  const response=await fetch(f.url,{headers:{Range:`bytes=${start}-${end}`,'If-Range':'"sha256:'+f.item.sha256+'"'}});
  assert.equal(response.status,206);assert.equal(response.headers.get('content-range'),`bytes ${start}-${end}/${f.raw.length}`);
  assert.deepEqual(Buffer.from(await response.arrayBuffer()),f.raw.subarray(start,end+1));
  assert.deepEqual(f.state.requests.map(r=>r.range).sort(),[`bytes=${CHUNK}-${2*CHUNK-1}`,`bytes=${2*CHUNK}-${3*CHUNK-1}`].sort());
  const tail=await fetch(f.url,{headers:{Range:`bytes=${end+1}-`}});const remainder=Buffer.from(await tail.arrayBuffer());
  assert.equal(hash(Buffer.concat([f.raw.subarray(0,start),f.raw.subarray(start,end+1),remainder])),f.item.sha256);
  const reset=await fetch(f.url,{headers:{Range:'bytes=1-3','If-Range':'"wrong"'}});assert.equal(reset.status,200);assert.equal(hash(Buffer.from(await reset.arrayBuffer())),f.item.sha256);
 }finally{await f.close();}
});

test('tampered source chunks never complete a response and are not silently retried',async()=>{
 const f=await fixture();f.state.corrupt=6;
 try{
  const result=await incomplete(f.url);assert.equal(result.status,200);assert(result.failed);assert(result.count<f.raw.length-65536);
  assert.equal(f.state.requests.filter(r=>r.range===`bytes=${6*CHUNK}-${7*CHUNK-1}`).length,1);
  f.state.corrupt=null;assert.equal(hash(Buffer.from(await(await fetch(f.url)).arrayBuffer())),f.item.sha256);
 }finally{await f.close();}
});

test('even matching chunk proofs cannot bypass the whole-file SHA or release its final64KiB',async()=>{
 const f=await fixture({item:{sha256:'a'.repeat(64),githubDigest:'sha256:'+'a'.repeat(64)}});
 try{
  for(const headers of [{},{Range:'bytes=0-'}]){
   const result=await incomplete(f.url,{headers});assert(result.failed);assert(result.count>CHUNK);assert(result.count<=f.raw.length-65536);
  }
 }finally{await f.close();}
});

test('unknown paths, queries and invalid ranges fail before any approved upstream is used',async()=>{
 const f=await fixture();
 try{
  for(const url of [f.url+'?url=https://untrusted.example',f.url.replace(name,'ToBe-Admin-Setup-1.6.10-win64.exe')])assert.equal((await fetch(url)).status,404);
  for(const Range of ['bytes=0-1,4-5','bytes=-9','bytes=99999999999999999-','bytes=99-1'])assert.equal((await fetch(f.url,{headers:{Range}})).status,416);
  assert.equal(f.state.requests.length,0);
 }finally{await f.close();}
});

test('wrong upstream range or encoding is rejected without a successful body',async()=>{
 for(const mode of ['badRange','badEncoding']){
  const f=await fixture();f.state[mode]=true;
  try{assert.equal((await fetch(f.url)).status,503);assert(f.state.requests.length<=4);}finally{await f.close();}
 }
});

test('canceling a blocked download frees its active slot and all prefetched requests',async()=>{
 const f=await fixture({stream:{maximumActive:1,prefetch:2}});f.state.stall=true;
 const cancel=new AbortController();const first=fetch(f.url,{signal:cancel.signal});first.catch(()=>{});
 try{
  await until(()=>f.state.active===2);assert.equal((await fetch(f.url)).status,429);
  cancel.abort();await assert.rejects(first);await until(()=>f.state.active===0);
  f.state.stall=false;const again=await fetch(f.url);assert.equal(again.status,200);assert.equal(hash(Buffer.from(await again.arrayBuffer())),f.item.sha256);
  assert(f.state.maximum<=2);
 }finally{cancel.abort();await f.close();}
});

test('a stalled source body has bounded retries and a later request can recover',async()=>{
 const f=await fixture({stream:{prefetch:1,chunkRetries:1,chunkTimeoutMs:40}});f.state.bodyStall=true;
 try{
  assert.equal((await fetch(f.url)).status,503);assert.equal(f.state.requests.length,2);
  await until(()=>f.state.active===0);f.state.bodyStall=false;f.state.delayMs=0;
  assert.equal(hash(Buffer.from(await(await fetch(f.url)).arrayBuffer())),f.item.sha256);
 }finally{await f.close();}
});

test('every chunk redirect remains in the strict public HTTPS host set',async()=>{
 for(const target of ['https://127.0.0.1/private','http://github.com/file','https://github.com:444/file','https://user:pass@github.com/file','https://release-assets.githubusercontent.com.untrusted.example/file']){
  let calls=0;const f=await fixture({fetcher:async()=>{calls++;return new Response(null,{status:302,headers:{location:target}});}});
  try{assert.equal((await fetch(f.url)).status,503);assert(calls<=4);}finally{await f.close();}
 }
});

test('chunk authority and concurrency limits must be explicit and bounded',async()=>{
 const f=await fixture();
 try{
  for(const changed of [{githubDigest:'sha256:'+'0'.repeat(64)},{chunkBytes:65536},{chunkSha256:[]},{chunkSha256:['not-a-sha']},{sourceName:'../private.exe'}])assert.throws(()=>validateReleaseIndex({schema:1,assets:[{...f.item,...changed}]}));
  for(const options of [{prefetch:0},{prefetch:5},{maximumActive:0},{maximumActive:5},{chunkRetries:3},{chunkTimeoutMs:0}])assert.throws(()=>createReleaseStream(f.index,options));
 }finally{await f.close();}
});
