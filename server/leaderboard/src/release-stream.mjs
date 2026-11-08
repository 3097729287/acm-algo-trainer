// Relay fixed, locally approved public releases. No requester URL, credential,
// account header or file cache participates in upstream downloads.
import {readFile,stat} from 'node:fs/promises';
import {Readable,Transform} from 'node:stream';
import {pipeline} from 'node:stream/promises';
import {createHash} from 'node:crypto';

const ROOT='https://github.com/3097729287/acm-algo-trainer/releases/download/';
const REDIRECT_HOSTS=new Set(['github.com','release-assets.githubusercontent.com','objects.githubusercontent.com','objects.github.com']);
const filePattern=/^(?:ToBe|TB)-(?:(?:Full-)?Setup-\d+\.\d+\.\d+-win64\.exe|(?:Compact-)?Update-\d+\.\d+\.\d+-to-\d+\.\d+\.\d+-win64\.zip)$/;
export const RELEASE_CHUNK_BYTES=1024*1024;
const TAIL=65536,MAX_INDEX=1024*1024,MAX_ASSETS=256;
const hex=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
class InvalidRelease extends Error{}

export function validateReleaseIndex(value){
 if(value?.schema!==1||!Array.isArray(value.assets)||value.assets.length>MAX_ASSETS)throw new InvalidRelease('Invalid public asset index');
 const next=new Map();
 for(const item of value.assets){
  if(!/^\d+\.\d+\.\d+$/.test(item.version)||!filePattern.test(item.name)||!filePattern.test(item.sourceName||item.name)||!Number.isSafeInteger(item.size)||item.size<=0||item.size>2*1024**3||!hex(item.sha256))throw new InvalidRelease('Invalid public asset');
  if(item.chunkBytes!==undefined||item.chunkSha256!==undefined){
   if(item.chunkBytes!==RELEASE_CHUNK_BYTES||!Array.isArray(item.chunkSha256)||item.chunkSha256.length!==Math.ceil(item.size/RELEASE_CHUNK_BYTES)||!item.chunkSha256.every(hex)||item.githubDigest!=='sha256:'+item.sha256)throw new InvalidRelease('Invalid reviewed release range proofs');
  }
  const key='/assets/'+item.version+'/'+item.name;if(next.has(key))throw new InvalidRelease('Duplicate asset');
  next.set(key,{...item,url:ROOT+'v'+item.version+'/'+(item.sourceName||item.name)});
 }
 return next;
}

function abortable(value,signal){
 if(signal.aborted){Promise.resolve(value).catch(()=>{});return Promise.reject(signal.reason||Error('Transfer canceled'));}
 return new Promise((resolve,reject)=>{
  const cancel=()=>reject(signal.reason||Error('Transfer canceled'));
  signal.addEventListener('abort',cancel,{once:true});
  Promise.resolve(value).then(result=>{signal.removeEventListener('abort',cancel);resolve(result);},error=>{signal.removeEventListener('abort',cancel);reject(error);});
 });
}
function cancelBody(response){try{response?.body?.cancel().catch(()=>{});}catch{/* A reader or canceled body owns it. */}}
async function approvedResponse(item,fetcher,signal,range){
 let upstream,target=item.url;
 for(let redirects=0;redirects<5;redirects++){
  const pending=Promise.resolve(fetcher(target,{redirect:'manual',signal,headers:{
   'User-Agent':'ToBe-public-release-relay/2','Accept':'application/octet-stream','Accept-Encoding':'identity',
   ...(range?{Range:range}:{})}}));
  pending.then(value=>{if(signal.aborted)cancelBody(value);},()=>{});
  upstream=await abortable(pending,signal);
  if(![301,302,303,307,308].includes(upstream.status))return upstream;
  let next;try{next=new URL(upstream.headers.get('location')||'',target);}catch{cancelBody(upstream);throw new InvalidRelease('Invalid asset redirect');}
  cancelBody(upstream);
  if(next.protocol!=='https:'||!REDIRECT_HOSTS.has(next.hostname)||next.username||next.password||next.hash||next.port&&next.port!=='443')throw new InvalidRelease('Invalid asset redirect');
  target=next.href;
 }
 throw new InvalidRelease('Too many asset redirects');
}

async function verifiedChunk(item,number,buffer,{fetcher,signal,chunkRetries,chunkTimeoutMs}){
 const start=number*RELEASE_CHUNK_BYTES,end=Math.min(start+RELEASE_CHUNK_BYTES,item.size)-1,count=end-start+1;
 for(let attempt=0;attempt<=chunkRetries;attempt++){
  const controller=new AbortController(),cancel=()=>controller.abort(signal.reason);
  signal.addEventListener('abort',cancel,{once:true});if(signal.aborted)cancel();
  const timeout=setTimeout(()=>controller.abort(Error('Release chunk timed out')),chunkTimeoutMs);timeout.unref();
  let response,reader;
  try{
   response=await approvedResponse(item,fetcher,controller.signal,`bytes=${start}-${end}`);
   if([408,429,500,502,503,504].includes(response.status))throw Error('Public release temporarily unavailable');
   const whole=response.status===200&&start===0&&end===item.size-1;
   if((!whole&&(response.status!==206||response.headers.get('content-range')!==`bytes ${start}-${end}/${item.size}`))
    ||!response.body||Number(response.headers.get('content-length'))!==count
    ||!['identity',''].includes((response.headers.get('content-encoding')||'identity').toLowerCase()))throw new InvalidRelease('Public release range mismatch');
   reader=response.body.getReader();let received=0;
   while(true){
    const {done,value}=await abortable(reader.read(),controller.signal);if(done)break;
    if(!(value instanceof Uint8Array)||!value.length||value.length>count-received)throw new InvalidRelease('Public release range overflow');
    buffer.set(value,received);received+=value.length;
   }
   if(received!==count)throw Error('Public release range interrupted');
   if(createHash('sha256').update(buffer.subarray(0,count)).digest('hex')!==item.chunkSha256[number])throw new InvalidRelease('Public release block checksum mismatch');
   return count;
  }catch(error){
   if(signal.aborted||error instanceof InvalidRelease||attempt===chunkRetries)throw error;
  }finally{
   clearTimeout(timeout);signal.removeEventListener('abort',cancel);controller.abort();
   if(reader){try{reader.cancel().catch(()=>{});reader.releaseLock();}catch{/* Aborted pending read. */}}
   else cancelBody(response);
  }
 }
}

async function* prefetchedChunks(item,start,end,options){
 const first=Math.floor(start/RELEASE_CHUNK_BYTES),last=Math.floor(end/RELEASE_CHUNK_BYTES),jobs=new Map();
 let next=first,finished=false;
 const schedule=buffer=>{
  const number=next++,job=verifiedChunk(item,number,buffer,options).then(count=>({buffer,count}));
  job.catch(()=>{});jobs.set(number,job);
 };
 // Reuse exactly this many full-chunk buffers. Copy outgoing 64 KiB pieces so
 // backpressure cannot retain a pool buffer while a later fetch overwrites it.
 for(let i=0;i<Math.min(options.prefetch,last-first+1);i++)schedule(Buffer.allocUnsafe(RELEASE_CHUNK_BYTES));
 try{
  for(let number=first;number<=last;number++){
   const {buffer,count}=await jobs.get(number);jobs.delete(number);
   const offset=number*RELEASE_CHUNK_BYTES,left=Math.max(0,start-offset),right=Math.min(count,end-offset+1);
   for(let position=left;position<right;position+=TAIL)yield Buffer.from(buffer.subarray(position,Math.min(position+TAIL,right)));
   if(next<=last)schedule(buffer);
  }
  finished=true;
 }finally{
  if(!finished)options.controller.abort();
  await Promise.allSettled(jobs.values());
 }
}

function verifier(size,sha256){
 let bytes=0,pending=null;const hash=sha256?createHash('sha256'):null;
 return new Transform({transform(chunk,encoding,callback){
  bytes+=chunk.length;if(bytes>size)return callback(new InvalidRelease('Asset exceeds approved size'));hash?.update(chunk);
  const combined=pending?Buffer.concat([pending,chunk]):chunk,keep=Math.min(combined.length,TAIL);
  if(combined.length>keep)this.push(combined.subarray(0,combined.length-keep));
  pending=combined.subarray(combined.length-keep);callback();
 },flush(callback){
  if(bytes!==size||hash&&hash.digest('hex')!==sha256)return callback(new InvalidRelease('Asset checksum mismatch'));
  if(pending)this.push(pending);callback();
 }});
}

function selectedRange(request,item){
 const etag='"sha256:'+item.sha256+'"';let start=0,end=item.size-1,partial=false;
 if(request.headers.range&&(!request.headers['if-range']||request.headers['if-range']===etag)){
  const match=/^bytes=(\d+)-(\d*)$/.exec(request.headers.range);
  if(!match)throw new InvalidRelease('Invalid release range');
  start=Number(match[1]);end=match[2]?Math.min(Number(match[2]),item.size-1):item.size-1;partial=true;
  if(!Number.isSafeInteger(start)||!Number.isSafeInteger(end)||start>end||start>=item.size)throw new InvalidRelease('Invalid release range');
 }
 return {start,end,partial,etag};
}

export function createReleaseStream(indexFile,{fetcher=fetch,maximumActive=2,transferTimeoutMs=60*60*1000,prefetch=4,chunkRetries=2,chunkTimeoutMs=60000}={}){
 if(!Number.isSafeInteger(transferTimeoutMs)||transferTimeoutMs<1||transferTimeoutMs>60*60*1000
  ||!Number.isSafeInteger(maximumActive)||maximumActive<1||maximumActive>4
  ||!Number.isSafeInteger(prefetch)||prefetch<1||prefetch>4||!Number.isSafeInteger(chunkRetries)||chunkRetries<0||chunkRetries>2
  ||!Number.isSafeInteger(chunkTimeoutMs)||chunkTimeoutMs<1||chunkTimeoutMs>600000)throw Error('Invalid release transfer limits');
 let active=0,cached=null,modified=0;
 async function index(){
  const info=await stat(indexFile);if(info.size>MAX_INDEX)throw new InvalidRelease('Asset index too large');
  if(!cached||info.mtimeMs!==modified){cached=validateReleaseIndex(JSON.parse(await readFile(indexFile,'utf8')));modified=info.mtimeMs;}
  return cached;
 }
 return async function stream(request,response){
  const url=new URL(request.url,'http://localhost'),path=url.pathname.replace(/^\/updates(?=\/assets\/)/,'');
  if(!path.startsWith('/assets/'))return false;
  const answer=(status,headers={})=>{response.writeHead(status,{'Cache-Control':'no-store','Content-Length':'0',...headers});response.end();};
  if(url.search||!['GET','HEAD'].includes(request.method)){answer(404);return true;}
  let item;try{item=(await index()).get(path);}catch(error){answer(error.code==='ENOENT'?404:503);return true;}
  if(!item){answer(404);return true;}
  const chunked=Boolean(item.chunkSha256);let range={start:0,end:item.size-1,partial:false};
  if(chunked){try{range=selectedRange(request,item);}catch{answer(416,{'Content-Range':`bytes */${item.size}`});return true;}}
  const {start,end,partial,etag}=range;
  const headers={'Content-Type':item.name.endsWith('.zip')?'application/zip':'application/octet-stream','Content-Length':String(end-start+1),'Content-Disposition':'attachment; filename="'+item.name+'"','Cache-Control':'public, max-age=31536000, immutable','X-Content-SHA256':item.sha256,'X-Content-Type-Options':'nosniff',
   ...(chunked?{'Accept-Ranges':'bytes',ETag:etag}:{}),...(partial?{'Content-Range':`bytes ${start}-${end}/${item.size}`}:{})};
  if(request.method==='HEAD'){response.writeHead(partial?206:200,headers);response.end();return true;}
  if(active>=maximumActive){answer(429,{'Retry-After':'10'});return true;}
  active++;const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),transferTimeoutMs);timeout.unref();
  const cancel=()=>controller.abort();response.once('close',cancel);let iterator,upstream;
  try{
   let input;
   if(chunked){
    iterator=prefetchedChunks(item,start,end,{fetcher,signal:controller.signal,controller,prefetch,chunkRetries,chunkTimeoutMs});
    const first=await iterator.next();
    async function* output(){if(!first.done)yield first.value;yield*iterator;}
    input=Readable.from(output(),{objectMode:false,highWaterMark:TAIL});
   }else{
    upstream=await approvedResponse(item,fetcher,controller.signal);
    if(upstream.status!==200||!upstream.body||Number(upstream.headers.get('content-length'))!==item.size)throw new InvalidRelease('Asset unavailable');
    input=Readable.fromWeb(upstream.body);
   }
   response.writeHead(partial?206:200,headers);response.flushHeaders();
   // A complete GET still checks the whole original SHA. An isolated Range
   // proves its complete source chunks; the installing client must check its
   // reconstructed whole file too. Both protect their final 64 KiB until flush.
   await pipeline(input,verifier(end-start+1,start===0&&end===item.size-1?item.sha256:null),response,{signal:controller.signal});
  }catch{
   controller.abort();if(!response.headersSent)answer(503,{'Retry-After':'30'});else response.destroy();
  }finally{
   controller.abort();try{await iterator?.return();}catch{/* Incomplete response is closed. */}
   cancelBody(upstream);active--;clearTimeout(timeout);response.removeListener('close',cancel);
  }
  return true;
 };
}
