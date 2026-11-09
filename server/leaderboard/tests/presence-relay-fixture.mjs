// Private parent/child fixture IPC: no login token is ever returned to stdout.
import {createInterface} from 'node:readline';
import {startFixture} from './local-server.mjs';
const f=await startFixture(),actors=[];
async function call(path,body,auth){
 const response=await fetch(f.endpoint+path,{method:body===undefined?'GET':'POST',headers:{'content-type':'application/json',...(auth?{'X-TB-User':auth.account.userId,Authorization:'Bearer '+auth.token}:{})},...(body===undefined?{}:{body:JSON.stringify(body)})});
 return {status:response.status,value:await response.json()};
}
for(const name of ['relay_lease_a','relay_lease_b']){
 await call('/v1/accounts/register',{loginId:name,nickname:name,password:'relay-fixture-only'});
 actors.push((await call('/v1/accounts/login',{loginId:name,password:'relay-fixture-only'})).value);
}
console.log(JSON.stringify({ready:true,ids:actors.map(auth=>auth.account.userId)}));
try{
 for await(const line of createInterface({input:process.stdin})){
  const packet=JSON.parse(line),auth=actors[packet.actor];
  if(packet.kind==='row'){
   const [rows]=await f.STORE.gameplay.db.execute('SELECT activity,last_seen FROM account_presence WHERE user_id=?',[auth.account.userId]);console.log(JSON.stringify(rows[0]||null));
  }else console.log(JSON.stringify(await call(packet.path,packet.value,auth)));
 }
}finally{await f.close();}
