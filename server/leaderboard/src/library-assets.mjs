// Relay only immutable public statement resources from a pinned source commit.
// No account headers, credentials, user URLs or on-disk cache are involved.
import {readFile,stat} from 'node:fs/promises';
import {Readable,Transform} from 'node:stream';
import {pipeline} from 'node:stream/promises';
import {createHash} from 'node:crypto';

const ROOT='https://raw.githubusercontent.com/3097729287/acm-algo-trainer/';
export function createLibraryAssetStream(indexFile,{fetcher=fetch,maximumActive=4,transferTimeoutMs=600000}={}){
 if(!Number.isSafeInteger(maximumActive)||maximumActive<1||maximumActive>16||!Number.isSafeInteger(transferTimeoutMs)||transferTimeoutMs<1||transferTimeoutMs>600000)throw Error('Invalid resource limits');
 let active=0,cached=null,modified=0;
 async function index(){
  const info=await stat(indexFile);if(info.size>4*1024**2)throw Error('Resource index too large');
  if(!cached||info.mtimeMs!==modified){
   const value=JSON.parse(await readFile(indexFile,'utf8'));
   if(value.schema!==1||!/^[a-f0-9]{40}$/.test(value.commit)||!Array.isArray(value.assets)||value.assets.length>10000)throw Error('Invalid resource index');
   const next=new Map();
   for(const item of value.assets){
    if(!/^[a-f0-9]{64}$/.test(item.sha256)||!Number.isSafeInteger(item.bytes)||item.bytes<1||item.bytes>32*1024**2||next.has(item.sha256))throw Error('Invalid resource');
    next.set(item.sha256,{...item,url:ROOT+value.commit+'/'+item.sha256+'.bin'});
   }
   cached=next;modified=info.mtimeMs;
  }
  return cached;
 }
 return async function stream(request,response){
  const url=new URL(request.url,'http://localhost');
  const path=url.pathname.replace(/^\/updates(?=\/library-assets\/)/,'');
  if(!path.startsWith('/library-assets/'))return false;
  const answer=(status,headers={})=>{response.writeHead(status,{'Cache-Control':'no-store',...headers});response.end();};
  const match=path.match(/^\/library-assets\/([a-f0-9]{64})\.bin$/);
  if(!match||url.search||!['GET','HEAD'].includes(request.method)){answer(404);return true;}
  let item;try{item=(await index()).get(match[1]);}catch(error){answer(error.code==='ENOENT'?404:503);return true;}
  if(!item){answer(404);return true;}
  const headers={'Content-Type':'application/octet-stream','Content-Length':String(item.bytes),'Cache-Control':'public, max-age=31536000, immutable','X-Content-Type-Options':'nosniff','X-Content-SHA256':item.sha256};
  if(request.method==='HEAD'){response.writeHead(200,headers);response.end();return true;}
  if(active>=maximumActive){answer(429,{'Retry-After':'2'});return true;}
  active++;const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),transferTimeoutMs);timeout.unref();
  const cancel=()=>controller.abort();response.once('close',cancel);
  try{
   const upstream=await fetcher(item.url,{redirect:'manual',signal:controller.signal,headers:{'User-Agent':'ToBe-public-statement-relay/1','Accept':'application/octet-stream','Accept-Encoding':'identity'}});
   const length=upstream.headers.get('content-length');
   if(upstream.status!==200||!upstream.body||length!==null&&Number(length)!==item.bytes)throw Error('Resource unavailable');
   let bytes=0,pending=null;const hash=createHash('sha256');
   // Keep the final bytes until the whole digest has matched. Corruption can
   // never finish a response with the advertised Content-Length.
   const verify=new Transform({transform(chunk,encoding,callback){bytes+=chunk.length;if(bytes>item.bytes)return callback(Error('Resource exceeds declared size'));hash.update(chunk);if(pending)this.push(pending);const keep=Math.min(chunk.length,65536);if(chunk.length>keep)this.push(chunk.subarray(0,chunk.length-keep));pending=chunk.subarray(chunk.length-keep);callback();},flush(callback){if(bytes!==item.bytes||hash.digest('hex')!==item.sha256)return callback(Error('Resource checksum mismatch'));if(pending)this.push(pending);callback();}});
   response.writeHead(200,headers);response.flushHeaders();
   await pipeline(Readable.fromWeb(upstream.body),verify,response,{signal:controller.signal});
  }catch{
   controller.abort();if(!response.headersSent)answer(503,{'Retry-After':'5'});else response.destroy();
  }finally{active--;clearTimeout(timeout);response.removeListener('close',cancel);}
  return true;
 };
}
