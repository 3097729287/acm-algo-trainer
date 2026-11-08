// A bounded relay for the exact public assets in a locally approved index.
// Large releases stay on GitHub; the account server never caches their bytes.
import {readFile,stat} from 'node:fs/promises';
import {Readable,Transform} from 'node:stream';
import {pipeline} from 'node:stream/promises';
import {createHash} from 'node:crypto';

const ROOT='https://github.com/3097729287/acm-algo-trainer/releases/download/';
const REDIRECT_HOSTS=new Set(['github.com','release-assets.githubusercontent.com','objects.githubusercontent.com','objects.github.com']);
const filePattern=/^(?:ToBe|TB)-(?:(?:Full-)?Setup-\d+\.\d+\.\d+-win64\.exe|(?:Compact-)?Update-\d+\.\d+\.\d+-to-\d+\.\d+\.\d+-win64\.zip)$/;
export function createReleaseStream(indexFile,{fetcher=fetch,maximumActive=2,transferTimeoutMs=60*60*1000}={}){
 if(!Number.isSafeInteger(transferTimeoutMs)||transferTimeoutMs<1||transferTimeoutMs>60*60*1000)throw Error('Invalid transfer timeout');
 let active=0,cached=null,modified=0;
 async function index(){
  const info=await stat(indexFile);if(info.size>1024*1024)throw Error('Asset index too large');
  if(!cached||info.mtimeMs!==modified){
   const value=JSON.parse(await readFile(indexFile,'utf8'));
   if(value.schema!==1||!Array.isArray(value.assets)||value.assets.length>256)throw Error('Invalid public asset index');
   const next=new Map();
   for(const item of value.assets){
    if(!/^\d+\.\d+\.\d+$/.test(item.version)||!filePattern.test(item.name)||!filePattern.test(item.sourceName||item.name)||!Number.isSafeInteger(item.size)||item.size<=0||item.size>2*1024**3||!/^[a-f0-9]{64}$/.test(item.sha256))throw Error('Invalid public asset');
    const key='/assets/'+item.version+'/'+item.name;if(next.has(key))throw Error('Duplicate asset');
    // No user URL, request headers, cookies, or credentials reach the upstream.
    next.set(key,{...item,url:ROOT+'v'+item.version+'/'+(item.sourceName||item.name)});
   }
   cached=next;modified=info.mtimeMs;
  }
  return cached;
 }
 return async function stream(request,response){
  const url=new URL(request.url,'http://localhost');
  const path=url.pathname.replace(/^\/updates(?=\/assets\/)/,'');
  if(!path.startsWith('/assets/'))return false;
  const answer=(status,headers={})=>{response.writeHead(status,{'Cache-Control':'no-store',...headers});response.end();};
  if(url.search||!['GET','HEAD'].includes(request.method)){answer(404);return true;}
  let item;try{item=(await index()).get(path);}catch(error){answer(error.code==='ENOENT'?404:503);return true;}
  if(!item){answer(404);return true;}
  const headers={'Content-Type':item.name.endsWith('.zip')?'application/zip':'application/octet-stream','Content-Length':String(item.size),'Content-Disposition':'attachment; filename="'+item.name+'"','Cache-Control':'public, max-age=31536000, immutable','X-Content-SHA256':item.sha256};
  if(request.method==='HEAD'){response.writeHead(200,headers);response.end();return true;}
  if(active>=maximumActive){answer(429,{'Retry-After':'10'});return true;}
  active++;const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),transferTimeoutMs);timeout.unref();
  const cancel=()=>controller.abort();response.once('close',cancel);
  try{
   let upstream,target=item.url;
   for(let redirects=0;redirects<5;redirects++){
    upstream=await fetcher(target,{redirect:'manual',signal:controller.signal,headers:{'User-Agent':'ToBe-public-release-relay/1','Accept':'application/octet-stream','Accept-Encoding':'identity'}});
    if(![301,302,303,307,308].includes(upstream.status))break;
    const next=new URL(upstream.headers.get('location')||'',target);await upstream.body?.cancel();
    if(next.protocol!=='https:'||!REDIRECT_HOSTS.has(next.hostname)||next.username||next.password||next.port&&next.port!=='443')throw Error('Invalid asset redirect');
    target=next.href;upstream=null;
   }
   if(!upstream||upstream.status!==200||!upstream.body||Number(upstream.headers.get('content-length'))!==item.size)throw Error('Asset unavailable');
   let bytes=0,pending=null;const hash=createHash('sha256');
   // Hold at most the final 64 KiB until the digest is verified. Otherwise a
   // client could consider Content-Length satisfied before a corrupt stream's
   // final verification destroys the connection.
   const verify=new Transform({transform(chunk,encoding,callback){bytes+=chunk.length;if(bytes>item.size)return callback(Error('Asset exceeds approved size'));hash.update(chunk);if(pending)this.push(pending);const keep=Math.min(chunk.length,65536);if(chunk.length>keep)this.push(chunk.subarray(0,chunk.length-keep));pending=chunk.subarray(chunk.length-keep);callback();},flush(callback){if(bytes!==item.size||hash.digest('hex')!==item.sha256)return callback(Error('Asset checksum mismatch'));if(pending)this.push(pending);callback();}});
   response.writeHead(200,headers);
   response.flushHeaders();
   await pipeline(Readable.fromWeb(upstream.body),verify,response,{signal:controller.signal});
  }catch{
   controller.abort();if(!response.headersSent)answer(503,{'Retry-After':'30'});else response.destroy();
  }finally{active--;clearTimeout(timeout);response.removeListener('close',cancel);}
  return true;
 };
}
