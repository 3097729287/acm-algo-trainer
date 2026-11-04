import test from 'node:test';
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {createHash,randomUUID} from 'node:crypto';
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {listenFixture} from './listen.mjs';
import {createLibraryAssetStream} from '../src/library-assets.mjs';
const bytes=Buffer.from('Original public PDF/image resource\n');
const sha=createHash('sha256').update(bytes).digest('hex'),commit='a'.repeat(40);
const response=data=>new Response(data,{headers:{'content-length':String(data.length)}});
async function fixture(fetcher,change=value=>value,limits={}){
 const directory=resolve('../../.backups/next-local/library-relay-tests',randomUUID());await mkdir(directory,{recursive:true});
 const file=directory+'/index.json';await writeFile(file,JSON.stringify(change({schema:1,commit,assets:[{sha256:sha,bytes:bytes.length}]})));
 const stream=createLibraryAssetStream(file,{fetcher,...limits}),server=createServer((request,response)=>stream(request,response));await listenFixture(server);
 return {url:'http://127.0.0.1:'+server.address().port,async close(){server.closeAllConnections();await new Promise(resolve=>server.close(resolve));}};
}
test('exact source commit, original bytes, offline-compatible metadata and no account information upstream',async()=>{
 const calls=[];const f=await fixture(async(url,options)=>{calls.push({url,options});return response(bytes);});
 try{
  const path='/library-assets/'+sha+'.bin';
  const head=await fetch(f.url+path,{method:'HEAD'});assert.equal(head.status,200);assert.equal(calls.length,0);assert.equal(head.headers.get('x-content-sha256'),sha);
  const result=await fetch(f.url+'/updates'+path,{headers:{Authorization:'private',Cookie:'private','X-TB-Client-IP':'private'}});
  assert.deepEqual(Buffer.from(await result.arrayBuffer()),bytes);assert.match(result.headers.get('cache-control'),/immutable/);
  assert.equal(calls[0].url,'https://raw.githubusercontent.com/3097729287/acm-algo-trainer/'+commit+'/'+sha+'.bin');
  assert.equal(calls[0].options.redirect,'manual');assert(!Object.keys(calls[0].options.headers).some(key=>/authorization|cookie|client-ip/i.test(key)));
  for(const suffix of ['?url=https://evil.invalid','.exe','/extra'])assert.equal((await fetch(f.url+path+suffix)).status,404);
  assert.equal((await fetch(f.url+path,{method:'POST'})).status,404);
  assert.equal((await fetch(f.url+'/library-assets/'+'b'.repeat(64)+'.bin')).status,404);assert.equal(calls.length,1);
 }finally{await f.close();}
});
test('redirects, truncation, overflow and digest corruption cannot complete a resource download',async()=>{
 for(const mode of ['redirect','size','hash','truncated','overflow']){
  const f=await fixture(async()=>mode==='redirect'?new Response(null,{status:302,headers:{location:'https://127.0.0.1/private'}}):mode==='size'?response(Buffer.alloc(1)):mode==='hash'?response(Buffer.alloc(bytes.length)):new Response(mode==='truncated'?bytes.subarray(1):Buffer.concat([bytes,bytes])));
  try{
   if(['redirect','size'].includes(mode))assert.equal((await fetch(f.url+'/library-assets/'+sha+'.bin')).status,503);
   else await assert.rejects(async()=>{const result=await fetch(f.url+'/library-assets/'+sha+'.bin');await result.arrayBuffer();});
  }finally{await f.close();}
 }
});
test('index rejects arbitrary origins, duplicate digests and oversized resources before fetching',async()=>{
 for(const change of [v=>({...v,commit:'main'}),v=>({...v,assets:[...v.assets,...v.assets]}),v=>({...v,assets:[{sha256:sha,bytes:32*1024**2+1}]})]){
  const f=await fixture(()=>{throw Error('must not fetch');},change);
  try{assert.equal((await fetch(f.url+'/library-assets/'+sha+'.bin')).status,503);}finally{await f.close();}
 }
});
test('slow resource streams have bounded concurrency and release their slot after timeout',async()=>{
 let attempts=0,signal;
 const f=await fixture(async(url,options)=>{
  if(++attempts>1)return response(bytes);
  signal=options.signal;
  return new Response(new ReadableStream({start(controller){signal.addEventListener('abort',()=>controller.error(Error('expired')),{once:true});}}));
 },v=>v,{maximumActive:1,transferTimeoutMs:100});
 try{
  const first=await fetch(f.url+'/library-assets/'+sha+'.bin');
  assert.equal((await fetch(f.url+'/library-assets/'+sha+'.bin')).status,429);
  await assert.rejects(()=>first.arrayBuffer());assert(signal.aborted);
  const next=await fetch(f.url+'/library-assets/'+sha+'.bin');assert.deepEqual(Buffer.from(await next.arrayBuffer()),bytes);
 }finally{await f.close();}
});
