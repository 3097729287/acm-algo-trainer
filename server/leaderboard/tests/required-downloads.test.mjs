import assert from 'node:assert/strict';
import {test} from 'node:test';
import {createServer} from 'node:http';
import {mkdtemp,mkdir,writeFile,rm,readFile} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {createRequiredDownloadStream,validateRequiredDownloadIndex} from '../src/required-downloads.mjs';
import {createLibraryAssetStream} from '../src/library-assets.mjs';
import {listenFixture} from './listen.mjs';

const hash=data=>createHash('sha256').update(data).digest('hex');
test('domestic required-input links reach the reviewed service through the stripped updates path',async()=>{
 const config=await readFile(new URL('../Caddyfile',import.meta.url),'utf8');
 assert.match(config,/handle_path \/updates\/\* \{/);
 assert.match(config,/@required_inputs path \/required-downloads\/\*\s+reverse_proxy @required_inputs api:8080/);
 assert.equal(config.split('reverse_proxy @required_inputs api:8080').length,2);
});
async function fixture(){
 const folder=await mkdtemp(path.join(os.tmpdir(),'tb-required-downloads-'));
 const directory=path.join(folder,'required-downloads');await mkdir(directory);
 // Opaque, synthetic transfer-fixture bytes; native ZIP content is separately
 // validated by the authoring/deployment script and the real P7351 E2E suite.
 const raw=Buffer.alloc(5*65536+17,7);raw.write('PK\x03\x04',0,'binary');const sha=hash(raw);
 const item={sha256:sha,bytes:raw.length,mime:'application/zip',fileName:'down.zip',problemId:'fixture::required',problemType:'output-only',role:'required-output-only-inputs',manuallyReviewed:true,requiredForStatement:true,optional:false,reviewSha256:'a'.repeat(64),sourceUrl:'https://fixture.example/problem/1',originalDownloadUrl:'https://fixture.example/down.zip',statementSha256:['b'.repeat(64)],chunkBytes:65536,chunkSha256:Array.from({length:Math.ceil(raw.length/65536)},(_,i)=>hash(raw.subarray(i*65536,(i+1)*65536))),members:[{name:'fixture.in',bytes:100,sha256:'c'.repeat(64)}]};
 const index=path.join(folder,'public-required-downloads.json'),filename=path.join(directory,sha+'.zip');
 await writeFile(filename,raw);await writeFile(index,JSON.stringify({schema:1,downloads:[item]}));
 const stream=createRequiredDownloadStream(index,{directory});
 const server=createServer(async(req,res)=>{if(!await stream(req,res)){res.writeHead(404);res.end();}});await listenFixture(server);
 const origin='http://127.0.0.1:'+server.address().port;
 return {folder,index,directory,filename,item,raw,sha,origin,url:origin+'/updates/required-downloads/'+sha+'.zip',async close(){server.closeAllConnections();await new Promise(resolve=>server.close(resolve));assert.equal(path.dirname(folder),os.tmpdir());assert(path.basename(folder).startsWith('tb-required-downloads-'));await rm(folder,{recursive:true,force:true});}};
}

test('reviewed mandatory inputs preserve exact bytes, metadata and range downloads',async()=>{
 const f=await fixture();try{
  const head=await fetch(f.url,{method:'HEAD'});assert.equal(head.status,200);assert.equal(head.headers.get('content-length'),String(f.raw.length));assert.equal(head.headers.get('content-disposition'),'attachment; filename="down.zip"');assert.equal((await head.arrayBuffer()).byteLength,0);
  const response=await fetch(f.url);assert.equal(response.status,200);assert.equal(hash(Buffer.from(await response.arrayBuffer())),f.sha);
  const part=await fetch(f.url,{headers:{Range:'bytes=123456-','If-Range':'"sha256:'+f.sha+'"'}});assert.equal(part.status,206);assert.equal(part.headers.get('content-range'),`bytes 123456-${f.raw.length-1}/${f.raw.length}`);assert.deepEqual(Buffer.from(await part.arrayBuffer()),f.raw.subarray(123456));
  const reset=await fetch(f.url,{headers:{Range:'bytes=123456-','If-Range':'"different"'}});assert.equal(reset.status,200);assert.equal(hash(Buffer.from(await reset.arrayBuffer())),f.sha);
 }finally{await f.close();}
});

test('unknown hashes, arbitrary URLs, paths and malformed ranges are refused',async()=>{
 const f=await fixture();try{
  for(const url of [f.origin+'/updates/required-downloads/'+'a'.repeat(64)+'.zip',f.url+'?url=https://untrusted.example',f.url+'/extra'])assert.equal((await fetch(url)).status,404);
  assert.equal((await fetch(f.url,{method:'POST'})).status,404);
  for(const Range of ['bytes=0-1,3-4','bytes=-5','bytes=9999999-'])assert.equal((await fetch(f.url,{headers:{Range}})).status,416);
 }finally{await f.close();}
});

test('a corrupt staged block cannot complete the advertised HTTP archive',async()=>{
 const f=await fixture();try{
  const corrupt=Buffer.from(f.raw);corrupt[3*65536+5]^=1;await writeFile(f.filename,corrupt);
  const response=await fetch(f.url);assert.equal(response.status,200);
  await assert.rejects(response.arrayBuffer());
  await writeFile(f.filename,f.raw);
  const retry=await fetch(f.url);assert.equal(hash(Buffer.from(await retry.arrayBuffer())),f.sha);
 }finally{await f.close();}
});

test('missing or truncated staged files never advertise a successful archive',async()=>{
 const f=await fixture();try{
  await writeFile(f.filename,f.raw.subarray(0,123));assert.equal((await fetch(f.url)).status,503);
  await rm(f.filename);assert.equal((await fetch(f.url,{method:'HEAD'})).status,503);
 }finally{await f.close();}
});

test('only manually reviewed mandatory output-only ZIPs enter the independent category',async()=>{
 const f=await fixture();try{
  for(const [key,value]of [['optional',true],['requiredForStatement',false],['manuallyReviewed',false],['problemType','standard'],['mime','image/png'],['role','optional-tests'],['bytes',128*1024**2+1],['fileName','../other.zip']])assert.throws(()=>validateRequiredDownloadIndex({schema:1,downloads:[{...f.item,[key]:value}]}));
  const ordinary=path.join(f.folder,'ordinary-assets.json');await writeFile(ordinary,JSON.stringify({schema:1,commit:'a'.repeat(40),assets:[{sha256:f.sha,bytes:32*1024**2+1}]}));
  const handler=createLibraryAssetStream(ordinary),server=createServer((req,res)=>handler(req,res));await listenFixture(server);
  try{assert.equal((await fetch('http://127.0.0.1:'+server.address().port+'/updates/library-assets/'+f.sha+'.bin')).status,503);}finally{server.closeAllConnections();await new Promise(resolve=>server.close(resolve));}
 }finally{await f.close();}
});

test('a canceled response releases its slot and the source is unchanged',async()=>{
 const f=await fixture();try{
  const controller=new AbortController();const response=await fetch(f.url,{signal:controller.signal});await response.body.getReader().read();controller.abort();
  const retry=await fetch(f.url);assert.equal(hash(Buffer.from(await retry.arrayBuffer())),f.sha);
  assert.equal(hash(await readFile(f.filename)),f.sha);
 }finally{await f.close();}
});
