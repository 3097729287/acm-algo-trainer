import test, {after} from 'node:test';
import assert from 'node:assert/strict';
import {createServer} from 'node:https';
import * as tls from 'node:tls';
import {once} from 'node:events';
import {constants as cryptoConstants} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {mkdtempSync,readFileSync,writeFileSync,rmSync,realpathSync} from 'node:fs';
import {join,dirname,basename} from 'node:path';
import {tmpdir} from 'node:os';
import {createAIJudge} from '../src/pk-judge.mjs';
import {createJudgeHttpsFetch,validateJudgeHttpsEnvironment,MAX_REQUEST_BYTES,MAX_RESPONSE_BYTES} from '../src/pk-https.mjs';

// All keys below are newly generated fixture keys. No existing key, account,
// provider configuration or OS trust store is read or changed.
const parent=realpathSync(tmpdir()),pki=mkdtempSync(join(parent,'tb-pk-https-'));
const openssl=process.platform==='win32'?'D:/Work/Msys64/ucrt64/bin/openssl.exe':'openssl';
const config=join(pki,'test.cnf');writeFileSync(config,'[req]\nprompt=no\ndistinguished_name=dn\n[dn]\nCN=synthetic loopback only\n');
const cert=(...args)=>execFileSync(openssl,args,{cwd:pki,env:{OPENSSL_CONF:config,...(process.platform==='win32'?{SYSTEMROOT:'C:\\Windows'}:{})},stdio:'pipe'});
for(const name of ['ca','other-ca','leaf'])cert('genpkey','-algorithm','EC','-pkeyopt','ec_paramgen_curve:P-256','-out',name+'-key.pem');
for(const name of ['ca','other-ca'])cert('req','-x509','-new','-key',name+'-key.pem','-out',name+'.pem','-days','1','-subj','/CN=synthetic '+name,'-addext','basicConstraints=critical,CA:TRUE','-addext','keyUsage=critical,keyCertSign,cRLSign');
cert('req','-new','-key','leaf-key.pem','-out','leaf.csr','-subj','/CN=loopback fixture');
for(const [name,issuer,san,serial] of [['valid','ca','IP:127.0.0.1','11'],['mismatch','ca','DNS:wrong.invalid','12'],['untrusted','other-ca','IP:127.0.0.1','13']]){
 writeFileSync(join(pki,name+'.ext'),'basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature\nextendedKeyUsage=serverAuth\nsubjectAltName='+san+'\n');
 cert('x509','-req','-in','leaf.csr','-CA',issuer+'.pem','-CAkey',issuer+'-key.pem','-set_serial',serial,'-days','1','-sha256','-extfile',name+'.ext','-out',name+'.pem');
}
// Trust just this synthetic CA in this test process through Node's normal TLS
// API. Production has no fixture flag, alternate CA or TLS bypass interface.
const originalCAs=tls.getCACertificates('default'),originalFetch=globalThis.fetch;
tls.setDefaultCACertificates([...originalCAs,readFileSync(join(pki,'ca.pem'),'utf8')]);
globalThis.fetch=()=>{throw Error('DEFAULT_GLOBAL_FETCH_MUST_NOT_BE_USED');};
after(()=>{
 globalThis.fetch=originalFetch;tls.setDefaultCACertificates(originalCAs);
 assert.equal(dirname(realpathSync(pki)),parent);assert(basename(pki).startsWith('tb-pk-https-'));
 rmSync(pki,{recursive:true});
});
const options=(body='{}',signal=new AbortController().signal)=>({method:'POST',redirect:'error',signal,headers:{Authorization:'Bearer synthetic-only','Content-Type':'application/json'},body});
const judge=url=>createAIJudge({endpoint:url,model:'synthetic',key:'synthetic-only'});
const problem={title:'Synthetic fixture',markdown:'No real problem or answer'};
const send=(response,status,body,headers={})=>{response.writeHead(status,{'Content-Type':'application/json',...headers});response.end(body);};
const envelope=JSON.stringify({choices:[{finish_reason:'stop',message:{content:'{"fixture":true}'}}]});
async function fixture(handler,run,certificate='valid'){
 let hits=0;
 const server=createServer({key:readFileSync(join(pki,'leaf-key.pem')),cert:readFileSync(join(pki,certificate+'.pem'))},(request,response)=>{hits++;handler(request,response);});
 server.on('tlsClientError',()=>{});server.listen(0,'127.0.0.1');await once(server,'listening');
 try{await run('https://127.0.0.1:'+server.address().port+'/v1/chat/completions',()=>hits);}
 finally{server.closeAllConnections();await new Promise(resolve=>server.close(resolve));}
}

test('formal default uses node:https, normal TLS, one POST and the real judge envelope parser',async()=>{
 await fixture(async(request,response)=>{
  assert.equal(request.method,'POST');assert.equal(request.headers.authorization,'Bearer synthetic-only');assert.equal(request.headers['accept-encoding'],'identity');
  let raw='';for await(const part of request)raw+=part;
  assert.equal(Buffer.byteLength(raw),Number(request.headers['content-length']));assert.equal(JSON.parse(raw).model,'synthetic');send(response,200,envelope);
 },async(url,hits)=>{assert.deepEqual(await judge(url)(problem,['A','B']),{fixture:true});assert.equal(hits(),1);});
});
test('default HTTP failures retain status and never retry',async()=>{
 await fixture((_,response)=>send(response,429,'{}'),async(url,hits)=>{await assert.rejects(judge(url)(problem,['A','B']),e=>e.code==='PK_AI_HTTP'&&e.status===429);assert.equal(hits(),1);});
});
test('default redirects are rejected without following Location',async()=>{
 await fixture((_,response)=>send(response,302,'',{Location:'https://example.invalid/'}),async(url,hits)=>{await assert.rejects(judge(url)(problem,['A','B']),e=>e.code==='PK_AI_HTTP'&&e.status===302);assert.equal(hits(),1);});
});
for(const certificate of ['untrusted','mismatch'])test('default rejects '+certificate+' TLS before an HTTP request',async()=>{
 await fixture((_,response)=>send(response,200,envelope),async(url,hits)=>{await assert.rejects(judge(url)(problem,['A','B']),e=>e.code==='PK_AI_CONNECTION');assert.equal(hits(),0);},certificate);
});
test('default cancellation before dispatch sends nothing; mid-body cancellation destroys the request',async()=>{
 await fixture((_,response)=>{response.writeHead(200);response.write('{');},async(url,hits)=>{
  const before=new AbortController();before.abort();await assert.rejects(judge(url)(problem,['A','B'],{signal:before.signal}),e=>e.code==='PK_AI_CANCELLED');assert.equal(hits(),0);
  const control=new AbortController(),pending=judge(url)(problem,['A','B'],{signal:control.signal});
  while(!hits())await new Promise(resolve=>setTimeout(resolve,2));control.abort();await assert.rejects(pending,e=>e.code==='PK_AI_CANCELLED');assert.equal(hits(),1);
 });
});
test('default total deadline also bounds a continually dripping body',async()=>{
 await fixture((_,response)=>{response.writeHead(200);response.write('{');const timer=setInterval(()=>response.write(' '),10);response.once('close',()=>clearInterval(timer));},async(url,hits)=>{
  const call=createAIJudge({endpoint:url,model:'synthetic',key:'synthetic-only',timeoutMs:120});
  await assert.rejects(call(problem,['A','B']),e=>e.code==='PK_AI_TIMEOUT');assert.equal(hits(),1);
 });
});
test('default rejects an oversized stream with the existing PK_AI_SIZE code',async()=>{
 await fixture((_,response)=>send(response,200,'x'.repeat(MAX_RESPONSE_BYTES+1)),async(url,hits)=>{await assert.rejects(judge(url)(problem,['A','B']),e=>e.code==='PK_AI_SIZE');assert.equal(hits(),1);});
});
test('transport binds its configured target and existing request byte limit before dispatch',async()=>{
 await fixture(async(request,response)=>{let n=0;for await(const part of request)n+=part.length;assert.equal(n,MAX_REQUEST_BYTES);send(response,200,'{}');},async(url,hits)=>{
  const transport=createJudgeHttpsFetch(url);assert.equal(await(await transport(new URL(url),options('x'.repeat(MAX_REQUEST_BYTES)))).text(),'{}');
  await assert.rejects(transport(url,options('x'.repeat(MAX_REQUEST_BYTES+1))),e=>e.safeCode==='HTTPS_REQUEST_SIZE');
  await assert.rejects(transport(url+'/other',options()),e=>e.safeCode==='HTTPS_TARGET_CHANGED');
  await assert.rejects(transport(url,{...options(),rejectUnauthorized:false}),e=>e.safeCode==='HTTPS_OPTIONS_UNSUPPORTED');assert.equal(hits(),1);
 });
});
test('memory flags are permitted without permitting proxy, preload or TLS environment changes',()=>{
 assert.doesNotThrow(()=>validateJudgeHttpsEnvironment({NODE_OPTIONS:'--max-old-space-size=96 --max-semi-space-size=4'},['--max-old-space-size=96']));
 assert.doesNotThrow(()=>validateJudgeHttpsEnvironment({},['--tls-cipher-list='+cryptoConstants.defaultCoreCipherList]));
 for(const env of [{HTTPS_PROXY:'http://127.0.0.1:1'},{NODE_TLS_REJECT_UNAUTHORIZED:'0'},{NODE_OPTIONS:'--require=somewhere'},{NODE_EXTRA_CA_CERTS:'somewhere'}])assert.throws(()=>validateJudgeHttpsEnvironment(env,[]));
 assert.throws(()=>validateJudgeHttpsEnvironment({},['--tls-min-v1.0']));
 assert.throws(()=>validateJudgeHttpsEnvironment({},['--tls-cipher-list=DEFAULT:!ALL']));
});
