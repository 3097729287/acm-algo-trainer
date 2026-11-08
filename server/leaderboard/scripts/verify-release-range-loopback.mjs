// Verify a complete local installer against an authored public index, through
// real source HTTP + production account-server routing. Never deploy or fetch
// Internet resources; no installer-sized buffer or copied binary is created.
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,stat,mkdir,writeFile} from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {Transform} from 'node:stream';
import {pipeline} from 'node:stream/promises';
import {performance} from 'node:perf_hooks';
import {validateReleaseIndex,RELEASE_CHUNK_BYTES as CHUNK} from '../src/release-stream.mjs';
import {startFixture} from '../tests/local-server.mjs';
import {listenFixture} from '../tests/listen.mjs';

const args=new Map();for(let i=2;i<process.argv.length;i+=2)args.set(process.argv[i],process.argv[i+1]);
for(const key of ['--index','--asset','--output'])assert(args.get(key),'Required '+key);
const indexFile=path.resolve(args.get('--index')),asset=path.resolve(args.get('--asset')),output=path.resolve(args.get('--output'));
try{await stat(output);throw Error('Choose a new receipt path');}catch(error){if(error.code!=='ENOENT')throw error;}
const rawIndex=await readFile(indexFile),approved=validateReleaseIndex(JSON.parse(rawIndex));
const matches=[...approved.values()].filter(item=>(item.sourceName||item.name)===path.basename(asset));
assert.equal(matches.length,1);const item=matches[0];assert(item.chunkSha256,'An authored one-MiB proof index is required');
const originalInfo=await stat(asset);assert.equal(originalInfo.size,item.size);
const whole=createHash('sha256');let count=0,part=createHash('sha256'),partBytes=0,partNumber=0;
for await(const block of createReadStream(asset,{highWaterMark:65536})){
 whole.update(block);count+=block.length;let offset=0;
 while(offset<block.length){const size=Math.min(CHUNK-partBytes,block.length-offset);part.update(block.subarray(offset,offset+size));partBytes+=size;offset+=size;
  if(partBytes===CHUNK){assert.equal(part.digest('hex'),item.chunkSha256[partNumber++]);part=createHash('sha256');partBytes=0;}}
}
if(partBytes)assert.equal(part.digest('hex'),item.chunkSha256[partNumber++]);
assert.equal(partNumber,item.chunkSha256.length);assert.equal(count,item.size);assert.equal(whole.digest('hex'),item.sha256);assert.equal(item.githubDigest,'sha256:'+item.sha256);

const metrics={requests:[],maximumActive:0,active:0};let disconnectOnce=Math.min(1,item.chunkSha256.length-1),corrupt=null;
const source=createServer(async(req,res)=>{
 const range=/^bytes=(\d+)-(\d+)$/.exec(req.headers.range||'');
 if(req.url!=='/original'||!range){res.writeHead(404);res.end();return;}
 const start=Number(range[1]),end=Number(range[2]),number=Math.floor(start/CHUNK);
 metrics.requests.push({range:req.headers.range,authorizationForwarded:Boolean(req.headers.authorization),cookieForwarded:Boolean(req.headers.cookie)});
 metrics.active++;metrics.maximumActive=Math.max(metrics.maximumActive,metrics.active);res.once('close',()=>metrics.active--);
 res.writeHead(206,{'Content-Length':String(end-start+1),'Content-Range':`bytes ${start}-${end}/${item.size}`});res.flushHeaders();
 const interrupt=disconnectOnce===number;if(interrupt)disconnectOnce=null;let delivered=0;
 const fault=new Transform({transform(block,encoding,callback){
  if(interrupt&&delivered){callback(Error('Deliberate loopback source disconnect'));return;}
  if(corrupt===number&&!delivered){block=Buffer.from(block);block[0]^=1;}
  delivered+=block.length;callback(null,block);
 }});
 try{await pipeline(createReadStream(asset,{start,end,highWaterMark:65536}),fault,res);}catch{res.destroy();}
});
await listenFixture(source);const sourceOrigin='http://127.0.0.1:'+source.address().port;
const calls=[];const server=await startFixture({serverOptions:{releaseAssetsFile:indexFile,releaseFetch:(url,options)=>{
 assert.equal(url,item.url);calls.push({fixedUrl:url,range:options.headers.Range});return fetch(sourceOrigin+'/original',options);
}}});
const url=server.endpoint+'/updates/assets/'+item.version+'/'+item.name;
async function responseDigest(response){const h=createHash('sha256');let bytes=0;for await(const block of response.body){h.update(block);bytes+=block.length;}return {bytes,sha256:h.digest('hex')};}
const savedAllocator=Buffer.allocUnsafe;let poolAllocations=0;
try{
 const before=await fetch(server.endpoint+'/v1/health');assert.equal(before.status,200);
 const head=await fetch(url,{method:'HEAD'});assert.equal(head.status,200);assert.equal(Number(head.headers.get('content-length')),item.size);assert.equal(metrics.requests.length,0);
 Buffer.allocUnsafe=function(size,...other){if(size===CHUNK)poolAllocations++;return savedAllocator.call(this,size,...other);};
 const started=performance.now(),full=await responseDigest(await fetch(url,{headers:{Authorization:'fixture-must-not-forward',Cookie:'fixture-must-not-forward'}}));
 const seconds=(performance.now()-started)/1000;Buffer.allocUnsafe=savedAllocator;
 assert.equal(full.bytes,item.size);assert.equal(full.sha256,item.sha256);assert.equal(poolAllocations,Math.min(4,item.chunkSha256.length));
 const fullRequests=metrics.requests.length;
 assert.equal(fullRequests,item.chunkSha256.length+1,'Only the interrupted block is fetched again');
 assert(metrics.maximumActive<=4);assert(metrics.requests.every(item=>!item.authorizationForwarded&&!item.cookieForwarded));
 const start=Math.min(CHUNK+123,item.size-2),end=Math.min(start+CHUNK+111,item.size-1),rangeBefore=metrics.requests.length;
 const range=await fetch(url,{headers:{Range:`bytes=${start}-${end}`,'If-Range':'"sha256:'+item.sha256+'"'}});assert.equal(range.status,206);
 const downloaded=await responseDigest(range),local=createHash('sha256');for await(const block of createReadStream(asset,{start,end,highWaterMark:65536}))local.update(block);
 assert.equal(downloaded.bytes,end-start+1);assert.equal(downloaded.sha256,local.digest('hex'));
 const rangeRequests=metrics.requests.slice(rangeBefore);assert(rangeRequests.every(req=>Number(req.range.split('=')[1].split('-')[0])>=Math.floor(start/CHUNK)*CHUNK));
 corrupt=Math.min(2,item.chunkSha256.length-1);const corruptStart=corrupt*CHUNK,corruptEnd=Math.min(corruptStart+CHUNK,item.size)-1;
 assert.equal((await fetch(url,{headers:{Range:`bytes=${corruptStart}-${corruptEnd}`}})).status,503);
 corrupt=null;const repaired=await fetch(url,{headers:{Range:`bytes=${corruptStart}-${corruptEnd}`}});assert.equal(repaired.status,206);await responseDigest(repaired);
 assert.equal((await fetch(url+'?url=https://untrusted.example')).status,404);assert.equal((await fetch(url.replace(item.name,'not-approved.exe'))).status,404);
 assert.equal((await fetch(server.endpoint+'/v1/health')).status,200);assert.equal(await server.countEvents(),0);
 const after=await stat(asset);assert.equal(after.size,originalInfo.size);assert.equal(after.mtimeMs,originalInfo.mtimeMs);
 const receipt={schema:1,loopbackOnly:true,domesticDeploymentClaimed:false,realProductionApiServer:true,localOriginalNotCopiedOrChanged:true,
  artifact:{name:item.name,sourceName:item.sourceName||item.name,bytes:item.size,sha256:item.sha256,githubDigest:item.githubDigest},
  indexSha256:createHash('sha256').update(rawIndex).digest('hex'),sourceChunkBytes:CHUNK,chunkProofCount:item.chunkSha256.length,
  fullDownload:{...full,seconds:Number(seconds.toFixed(3)),upstreamRequests:fullRequests,interruptedBlockRetriedWithoutRestart:true,wholeSha256Verified:true},
  range:{start,end,bytes:downloaded.bytes,sha256:downloaded.sha256,unrelatedPrefixNotFetched:true,sourceRanges:rangeRequests.map(item=>item.range)},
  reusableOneMiBBuffers:poolAllocations,maximumObservedUpstreamRequests:metrics.maximumActive,sourceTamperingRejected:true,nextVerifiedRangeRecovered:true,
  unknownPathsAndRequesterUrlsRefused:true,accountHealthAndEventCountUnchanged:true,requesterCredentialsNotForwarded:true,requests:metrics.requests,
  limits:{defaultActiveDownloads:2,maximumConfigurableActiveDownloads:4,prefetchRange:[1,4],defaultFullChunkPoolBytesPerTransfer:4*CHUNK,protectedTailBytes:65536,ordinary32MiBPolicyUnchanged:true},
  speedMeaning:'This is loopback transport and integrity evidence, not a claim about domestic Internet bandwidth or one-minute installation.'};
 await mkdir(path.dirname(output),{recursive:true});await writeFile(output,JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});
 console.log(JSON.stringify({bytes:full.bytes,seconds:Number(seconds.toFixed(3)),sourceRequests:fullRequests,reusableOneMiBBuffers:poolAllocations,sourceTamperingRejected:true,deployed:false}));
}finally{
 Buffer.allocUnsafe=savedAllocator;source.closeAllConnections();server.server.closeAllConnections();
 await server.close();await new Promise(resolve=>source.close(resolve));
}
