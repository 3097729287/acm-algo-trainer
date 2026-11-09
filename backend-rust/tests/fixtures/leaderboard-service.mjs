// Disposable local accounts + the real shared HTTP adapter/SQLite protocol.
// stdin is a test-control channel, not a route exposed by the product.
import {createServer} from 'node:http';
import {createHash,randomUUID} from 'node:crypto';
import {createInterface} from 'node:readline';
import {readFileSync} from 'node:fs';
import {createApiServer} from '../../../server/leaderboard/src/server.mjs';
import {SQLiteStore} from '../../../server/leaderboard/tests/sqlite-store.mjs';
import {listenFixture} from '../../../server/leaderboard/tests/listen.mjs';

const now=Date.parse('2026-11-09T07:00:00Z'), STORE=new SQLiteStore();
const env={STORE,RATE_LIMIT_SALT:'native-social-local-only',TEST_NOW:now,REQUESTS_PER_USER_MINUTE:600};
const modes={},counts={},owners=[],password='local-native-fixture-password';
let leakRequests=0;
const leak=createServer((_req,res)=>{leakRequests++;res.end('{}');});
await listenFixture(leak);
const api=createApiServer(env),native=api.listeners('request')[0];
api.removeListener('request',native);
api.on('request',async(req,res)=>{
  if(req.url.startsWith('/mirror/'))req.url=req.url.slice('/mirror'.length);
  const path=new URL(req.url,'http://localhost').pathname;
  counts[req.method+' '+path]=(counts[req.method+' '+path]||0)+1;
  const mode=modes[path];
  if(mode==='delay')await new Promise(resolve=>setTimeout(resolve,250));
  if(mode==='fail'){res.writeHead(503,{'Content-Type':'application/json'});res.end('{"error":"local test unavailable"}');return;}
  if(mode==='redirect'){res.writeHead(307,{Location:`http://127.0.0.1:${leak.address().port}/leak`});res.end();return;}
  if(mode==='oversize'){res.writeHead(200,{'Content-Type':'application/json','Content-Length':20000000});res.end('{}');return;}
  if(mode){
    const end=res.end.bind(res);
    res.end=function(buffer,...rest){
      if(mode==='drop'){req.socket.destroy();return;}
      if(mode==='delay-response'){setTimeout(()=>end(buffer,...rest),250);return this;}
      if(buffer){
        const value=JSON.parse(Buffer.from(buffer).toString('utf8'));
        if(mode==='avatar-hash')value.avatarHash='0'.repeat(64);
        if(mode==='avatar-signature')value.avatarData='data:image/png;base64,AAAA';
        if(mode==='wrong-profile')value.userId=owners[2].owner;
        if(mode==='wrong-recipient'&&value.notifications?.length)value.notifications[0].recipient.userId=owners[2].owner;
        if(mode==='wrong-self')value.self.userId=owners[2].owner;
        if(mode==='wrong-request')value.id=randomUUID();
        if(mode==='wrong-owner')value.owner=owners[2].owner;
        buffer=Buffer.from(JSON.stringify(value));
      }
      return end(buffer,...rest);
    };
  }
  await native(req,res);
});
await listenFixture(api);
const endpoint=`http://127.0.0.1:${api.address().port}`;
async function call(path,body,who,method=body===undefined?'GET':'POST'){
  const r=await fetch(endpoint+path,{method,headers:{'Content-Type':'application/json','X-TB-State-Protocol':'1',...(who?{'X-TB-User':who.owner,Authorization:'Bearer '+who.token}:{})},...(body===undefined?{}:{body:JSON.stringify(body)})});
  const value=await r.json();if(!r.ok)throw new Error(`local fixture protocol ${r.status}`);return value;
}
for(const suffix of ['alice','bob','carol']){
  const loginId='native_'+suffix;
  await call('/v1/accounts/register',{loginId,nickname:loginId,password});
  const value=await call('/v1/accounts/login',{loginId,password});
  owners.push({owner:value.account.userId,token:value.token,loginId});
}
const listId=JSON.parse(readFileSync(new URL('../../../server/leaderboard/src/training-list-ids.json',import.meta.url),'utf8'))[0];
process.stdout.write(JSON.stringify({endpoint,owners,listId})+'\n');
const hash=v=>createHash('sha256').update(v).digest('hex');
const lines=createInterface({input:process.stdin});
for await(const line of lines){
  try{
    const op=JSON.parse(line);let result={ok:true};
    if(op.op==='mode'){if(op.mode)modes[op.path]=op.mode;else delete modes[op.path];}
    else if(op.op==='time')env.TEST_NOW=op.now;
    else if(op.op==='stats')result={counts,leakRequests,eventCount:STORE.database.prepare('SELECT COUNT(*) AS n FROM official_ac_events').get().n,commentCount:STORE.database.prepare("SELECT COUNT(*) AS n FROM social_notifications WHERE kind='comment'").get().n};
    else if(op.op==='ac')await call('/v1/events',{events:[{eventId:hash(owners[op.user].owner+op.name),problemKey:hash(op.name),acceptedAt:op.at||'2026-11-09T06:00:00Z',difficulty:1200,scope:'official'}]},owners[op.user]);
    else if(op.op==='avatar'){await call('/v1/profile',{avatarData:op.value},owners[op.user],'PUT');result={hash:op.value?hash(op.value):null};}
    else if(op.op==='rotate'){
      const old=owners[op.user];const value=await call('/v1/accounts/login',{loginId:old.loginId,password});
      old.token=value.token;result={owner:old.owner,token:old.token};
    }else if(op.op==='stop'){process.stdout.write('{"ok":true}\n');break;}
    else throw new Error('unknown local operation');
    process.stdout.write(JSON.stringify(result)+'\n');
  }catch{process.stdout.write('{"fixtureError":true}\n');}
}
lines.close();process.stdin.destroy();
api.closeAllConnections();leak.closeAllConnections();
await Promise.all([new Promise(r=>api.close(r)),new Promise(r=>leak.close(r))]);
await STORE.close();
