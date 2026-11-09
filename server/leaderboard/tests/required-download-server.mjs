// Disposable real HTTP adapter for the native-archive end-to-end proof.
import fs from 'node:fs';
import path from 'node:path';
import {startFixture} from './local-server.mjs';
const directory=path.resolve(process.argv[2]||''),metricsFile=path.resolve(process.argv[3]||'');
if(!process.argv[2]||!process.argv[3])throw Error('Supply isolated staged inputs and a fixture metrics file');
const fixture=await startFixture({serverOptions:{requiredDownloadsFile:path.join(directory,'public-required-downloads.json'),requiredDownloadsDir:path.join(directory,'required-downloads')}});
const original=fixture.server.listeners('request')[0],requests=[];let interrupt=process.argv.includes('--interrupt-once');
fixture.server.removeListener('request',original);
fixture.server.on('request',(request,response)=>{
 if(request.url.startsWith('/updates/required-downloads/')){
  requests.push({method:request.method,path:request.url,range:request.headers.range||null,authorizationForwarded:Boolean(request.headers.authorization),cookieForwarded:Boolean(request.headers.cookie)});
  fs.writeFileSync(metricsFile,JSON.stringify({requests},null,2)+'\n');
  if(interrupt&&request.method==='GET'){
   interrupt=false;let sent=0,paused=false;const write=response.write.bind(response);
   response.write=(chunk,...args)=>{
    if(paused)return false;
    sent+=Buffer.byteLength(chunk);const result=write(chunk,...args);
    if(sent>=2*65536){paused=true;setTimeout(()=>response.destroy(),20).unref();return false;}
    return result;
   };
  }
 }
 return original(request,response);
});
process.stdout.write(JSON.stringify({endpoint:fixture.endpoint})+'\n');
const close=async()=>{fixture.server.closeAllConnections();await fixture.close();process.exit(0);};
process.on('SIGTERM',close);process.on('SIGINT',close);
