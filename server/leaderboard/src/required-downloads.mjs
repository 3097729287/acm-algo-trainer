// Locally staged, reviewed mandatory input archives. Ordinary library-assets
// keeps its separate 32 MiB rule and never delegates to this category.
import {readFile,stat,lstat,open} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {Readable} from 'node:stream';
import {pipeline} from 'node:stream/promises';

const CHUNK=65536,MAXIMUM=128*1024**2;
const hex=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
export function validateRequiredDownloadIndex(value){
 if(value?.schema!==1||!Array.isArray(value.downloads)||value.downloads.length>32)throw Error('Invalid reviewed required-download index');
 const items=new Map();
 for(const item of value.downloads){
  if(!hex(item?.sha256)||items.has(item.sha256)||!Number.isSafeInteger(item.bytes)||item.bytes<1||item.bytes>MAXIMUM
   ||item.mime!=='application/zip'||item.problemType!=='output-only'||item.role!=='required-output-only-inputs'
   ||item.manuallyReviewed!==true||item.requiredForStatement!==true||item.optional!==false||!hex(item.reviewSha256)
   ||typeof item.problemId!=='string'||!item.problemId.length||item.problemId.length>512
   ||!Array.isArray(item.statementSha256)||item.statementSha256.length<1||item.statementSha256.length>8||!item.statementSha256.every(hex)
   ||!Array.isArray(item.chunkSha256)||item.chunkBytes!==CHUNK||item.chunkSha256.length!==Math.ceil(item.bytes/CHUNK)||!item.chunkSha256.every(hex)
   ||typeof item.fileName!=='string'||!/^[A-Za-z0-9][A-Za-z0-9_.-]{0,119}\.zip$/.test(item.fileName))throw Error('Invalid reviewed required download');
  for(const name of ['sourceUrl','originalDownloadUrl']){
   let url;try{url=new URL(item[name]);}catch{throw Error('Invalid required-download provenance');}
   if(url.protocol!=='https:'||url.username||url.password||url.hash)throw Error('Invalid required-download provenance');
  }
  const names=new Set();
  if(!Array.isArray(item.members)||!item.members.length||item.members.length>1000)throw Error('Missing required input inventory');
  for(const member of item.members){
   if(typeof member?.name!=='string'||!/^[A-Za-z0-9][A-Za-z0-9_.-]{0,119}$/.test(member.name)||names.has(member.name)
    ||!hex(member.sha256)||!Number.isSafeInteger(member.bytes)||member.bytes<1)throw Error('Invalid required input inventory');
   names.add(member.name);
  }
  items.set(item.sha256,item);
 }
 return items;
}

export function createRequiredDownloadStream(indexFile,{directory=path.join(path.dirname(indexFile),'required-downloads'),maximumActive=4,transferTimeoutMs=600000}={}){
 if(!Number.isSafeInteger(maximumActive)||maximumActive<1||maximumActive>16||!Number.isSafeInteger(transferTimeoutMs)||transferTimeoutMs<1||transferTimeoutMs>600000)throw Error('Invalid required-download limits');
 let active=0,cached=null,modified=0;
 const root=path.resolve(directory);
 async function index(){
  const info=await stat(indexFile);if(info.size>2*1024**2)throw Error('Required-download index too large');
  if(!cached||info.mtimeMs!==modified){cached=validateRequiredDownloadIndex(JSON.parse(await readFile(indexFile,'utf8')));modified=info.mtimeMs;}
  return cached;
 }
 return async function stream(request,response){
  const url=new URL(request.url,'http://localhost'),pathname=url.pathname.replace(/^\/updates(?=\/required-downloads\/)/,'');
  if(!pathname.startsWith('/required-downloads/'))return false;
  const answer=(status,headers={})=>{response.writeHead(status,{'Cache-Control':'no-store','Content-Length':'0',...headers});response.end();};
  const match=/^\/required-downloads\/([a-f0-9]{64})\.zip$/.exec(pathname);
  if(!match||url.search||!['GET','HEAD'].includes(request.method)){answer(404);return true;}
  let item;try{item=(await index()).get(match[1]);}catch(error){answer(error.code==='ENOENT'?404:503);return true;}
  if(!item){answer(404);return true;}
  const filename=path.join(root,item.sha256+'.zip');
  if(path.dirname(filename)!==root){answer(404);return true;}
  let info;try{info=await lstat(filename);}catch{answer(503,{'Retry-After':'5'});return true;}
  if(!info.isFile()||info.isSymbolicLink()||info.size!==item.bytes){answer(503);return true;}
  const etag='"sha256:'+item.sha256+'"';let start=0,end=item.bytes-1,partial=false;
  if(request.headers.range&&(!request.headers['if-range']||request.headers['if-range']===etag)){
   const range=/^bytes=(\d+)-(\d*)$/.exec(request.headers.range);
   if(!range){answer(416,{'Content-Range':`bytes */${item.bytes}`});return true;}
   start=Number(range[1]);end=range[2]?Math.min(Number(range[2]),item.bytes-1):item.bytes-1;partial=true;
   if(!Number.isSafeInteger(start)||!Number.isSafeInteger(end)||start<0||start>end||start>=item.bytes){answer(416,{'Content-Range':`bytes */${item.bytes}`});return true;}
  }
  const headers={'Content-Type':item.mime,'Content-Length':String(end-start+1),'Content-Disposition':'attachment; filename="'+item.fileName+'"',
   'Accept-Ranges':'bytes',ETag:etag,'X-Content-SHA256':item.sha256,'X-Content-Type-Options':'nosniff',
   'Cache-Control':'public, max-age=31536000, immutable',...(partial?{'Content-Range':`bytes ${start}-${end}/${item.bytes}`}:{})};
  if(request.method==='HEAD'){response.writeHead(partial?206:200,headers);response.end();return true;}
  if(active>=maximumActive){answer(429,{'Retry-After':'2'});return true;}
  active++;const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),transferTimeoutMs);timeout.unref();
  const cancel=()=>controller.abort();response.once('close',cancel);let handle,iterator;
  async function* verified(){
   let pending=null;const hash=createHash('sha256');
   try{
    const first=Math.floor(start/CHUNK),last=Math.floor(end/CHUNK);
    for(let number=first;number<=last;number++){
     if(controller.signal.aborted)throw Error('Required download canceled');
     const offset=number*CHUNK,count=Math.min(CHUNK,item.bytes-offset),buffer=Buffer.allocUnsafe(count);
     const {bytesRead}=await handle.read(buffer,0,count,offset);
     if(bytesRead!==count||createHash('sha256').update(buffer).digest('hex')!==item.chunkSha256[number])throw Error('Required input checksum mismatch');
     if(number===0&&!['504b0304','504b0506'].includes(buffer.subarray(0,4).toString('hex')))throw Error('Required input archive is not a ZIP');
     if(start===0&&end===item.bytes-1)hash.update(buffer);
     const selected=buffer.subarray(Math.max(0,start-offset),Math.min(count,end-offset+1));
     if(pending)yield pending;pending=selected;
    }
    if(start===0&&end===item.bytes-1&&hash.digest('hex')!==item.sha256)throw Error('Whole required input checksum mismatch');
    if(pending)yield pending;
   }finally{await handle?.close();handle=null;}
  }
  try{
   handle=await open(filename,'r');iterator=verified();const first=await iterator.next();
   response.writeHead(partial?206:200,headers);response.flushHeaders();
   async function* output(){if(!first.done)yield first.value;yield*iterator;}
   await pipeline(Readable.from(output(),{objectMode:false,highWaterMark:CHUNK}),response,{signal:controller.signal});
  }catch{
   controller.abort();if(!response.headersSent)answer(503,{'Retry-After':'5'});else response.destroy();
  }finally{
   try{await iterator?.return();}catch{/* The incomplete response is already closed. */}
   await handle?.close();active--;clearTimeout(timeout);response.removeListener('close',cancel);
  }
  return true;
 };
}
