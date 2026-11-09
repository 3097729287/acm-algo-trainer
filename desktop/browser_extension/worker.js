// Pure protocol-4 tabs. Session values never leave the browser's own pages.
importScripts('connection_config.js');
const hosts=new Set(['codeforces.com','www.codeforces.com','atcoder.jp','ac.nowcoder.com','www.nowcoder.com','nowcoder.com','www.luogu.com.cn','luogu.com.cn','login.luogu.com.cn','qoj.ac']);
const platformHosts={'codeforces.com':'Codeforces','www.codeforces.com':'Codeforces','atcoder.jp':'AtCoder','ac.nowcoder.com':'牛客','www.nowcoder.com':'牛客','nowcoder.com':'牛客','www.luogu.com.cn':'洛谷','luogu.com.cn':'洛谷','login.luogu.com.cn':'洛谷','qoj.ac':'QOJ'};
const patterns=Object.keys(platformHosts).map(host=>'https://'+host+'/*');
const connections=new Map(),seen=new Map(),serial=new Map();let polling=false;
const localBase=value=>{try{const u=new URL(value);return u.protocol==='http:'&&u.hostname==='127.0.0.1'&&u.origin===value}catch{return false}};
async function request(base,path,body,key=''){
 if(!localBase(base))throw Error('Invalid local endpoint');
 const response=await fetch(base+'/api/browser/'+path,{method:'POST',headers:{'Content-Type':'application/json','X-TB-Browser':key,'X-TB-Browser-Client':chrome.runtime.id},body:JSON.stringify(body),signal:AbortSignal.timeout(10000)});
 if(!response.ok){if([401,403,410,426].includes(response.status)){connections.delete(base);seen.delete(base)}throw Error('ToBe connection unavailable')}
 return response.json();
}
async function exchange(job,body){return request(job.base,'exchange',{sessionId:job.sessionId,clientId:job.clientId,...body},job.key)}
async function identities(tabs){
 const result={};
 await Promise.all(tabs.filter(t=>!t.incognito).slice(0,12).map(async tab=>{
  const platform=platformHosts[new URL(tab.url).hostname];if(!platform)return;
  try{const value=await Promise.race([chrome.tabs.sendMessage(tab.id,{type:'identity',platform}),new Promise(r=>setTimeout(()=>r(null),1800))]);
   if(value?.platform===platform&&(value.state==='logged_in'||!result[platform]))result[platform]=value;
  }catch{}
 }));
 return result;
}
async function createJob(item,base,clientId,windows,tabs){
 const saved=(await chrome.storage.session.get('jobs')).jobs||{};
 const previous=Object.values(saved).find(j=>j.base===base&&j.sessionId===item.sessionId);
 if(previous){
  if(previous.key!==item.key){previous.key=item.key;previous.clientId=clientId;saved[previous.tabId]=previous;await chrome.storage.session.set({jobs:saved})}
  try{await chrome.tabs.get(previous.tabId);await chrome.tabs.sendMessage(previous.tabId,{type:'wake'}).catch(()=>{})}
  catch{delete saved[previous.tabId];await chrome.storage.session.set({jobs:saved})}
  return;
 }
 const regular=windows.filter(w=>!w.incognito);if(!regular.length)return;
 const job={...item,base,clientId,owned:true};const claim=await exchange(job,{claim:true});
 if(['closed','error','finished'].includes(claim.status))return;
 const target=new URL(claim.url);if(target.protocol!=='https:'||!hosts.has(target.hostname))return;
 const matching=tabs.find(t=>!t.incognito&&new URL(t.url).hostname===target.hostname);
 const tab=await chrome.tabs.create({windowId:matching?.windowId||(regular.find(w=>w.focused)||regular[0]).id,url:'about:blank',active:false});
 job.tabId=tab.id;job.targetHost=target.hostname;if(claim.manual)job.manual=true;
 saved[tab.id]=job;await chrome.storage.session.set({jobs:saved});
 // Mute this owned tab before navigating; other browser audio is untouched.
 await chrome.tabs.update(tab.id,{muted:true,url:target.href});
}
async function poll(){
 if(polling)return;polling=true;
 try{
  const settings=await chrome.storage.local.get(['clientId','bases']);const clientId=settings.clientId||crypto.randomUUID();
  if(!settings.clientId)await chrome.storage.local.set({clientId});
  const bases=(settings.bases||[TB_CONNECTION_BASE]).filter(localBase).slice(0,4);
  const [windows,tabs]=await Promise.all([chrome.windows.getAll({windowTypes:['normal']}),chrome.tabs.query({url:patterns})]);
  const hints=await identities(tabs);
  for(const base of bases){try{
   if(!connections.has(base))connections.set(base,(await request(base,'register',{clientId,protocol:4,extensionVersion:chrome.runtime.getManifest().version,browser:navigator.userAgent.includes('Edg/')?'edge':'chrome'})).key);
   const answer=await request(base,'queue',{clientId,hasWindow:windows.some(w=>!w.incognito),identities:hints},connections.get(base));
   seen.set(base,Date.now());
   for(const item of answer.jobs||[])await createJob(item,base,clientId,windows,tabs);
  }catch{}}
 }finally{polling=false}
}
async function handle(message,sender){
 if(sender.id!==chrome.runtime.id||sender.frameId!==0||!sender.tab?.id)return {};
 const page=new URL(sender.url);if(page.protocol!=='https:'||!hosts.has(page.hostname))return {};
 const jobs=(await chrome.storage.session.get('jobs')).jobs||{},job=jobs[sender.tab.id];
 if(!job)return {idle:true};
 if(!['tick','event'].includes(message.type)||message.type==='event'&&message.value?.sessionId!==job.sessionId)return {};
 let answer;
 if(message.type==='event'&&typeof message.value?.value?.html==='string'){
  const html=message.value.value.html;
  if(new TextEncoder().encode(html).length>4000000)throw Error('Statement exceeds limit');
  const value={...message.value.value};delete value.html;
  const parts=[];
  for(let start=0;start<html.length;){let end=Math.min(start+32000,html.length);if(end<html.length&&/[\uD800-\uDBFF]/.test(html[end-1]))end--;parts.push(html.slice(start,end));start=end}
  if(!parts.length)parts.push('');
  for(let index=0;index<parts.length;index++)answer=await exchange(job,{pageUrl:page.href,event:{...message.value,value,htmlPart:{index,total:parts.length,text:parts[index]}}});
 }else answer=await exchange(job,{pageUrl:page.href,...(message.type==='event'?{event:message.value,inspection:message.inspection===true}:{})});
 if(answer.navigate){const target=new URL(answer.navigate);if(target.protocol==='https:'&&target.hostname===job.targetHost&&target.href!==page.href)await chrome.tabs.update(job.tabId,{url:target.href})}
 if(answer.reveal&&['needs_login','needs_verification'].includes(answer.status)){
  if(job.revealedFor!==answer.status){job.revealedFor=answer.status;jobs[job.tabId]=job;await chrome.storage.session.set({jobs});
   await chrome.tabs.update(job.tabId,{active:true});await chrome.windows.update(sender.tab.windowId,{focused:true});}
 }else if(job.revealedFor){delete job.revealedFor;jobs[job.tabId]=job;await chrome.storage.session.set({jobs})}
 if(answer.stop){
  const latest=(await chrome.storage.session.get('jobs')).jobs||{};
  if(answer.closeOwned&&job.owned&&!job.manual){
   let tab;
   try{tab=await chrome.tabs.get(job.tabId)}catch{}
   if(tab&&(!tab.incognito&&new URL(tab.url).protocol==='https:'&&new URL(tab.url).hostname===job.targetHost)){
    // Keep the mapping on a failed close, so reconnect can finish the same job.
    await chrome.tabs.remove(job.tabId);
   }else if(tab)return {...answer,stop:false};
   await exchange(job,{closed:true});
  }else await exchange(job,{released:true});
  delete latest[job.tabId];await chrome.storage.session.set({jobs:latest});
 }
 return answer;
}
chrome.runtime.onMessage.addListener((message,sender,reply)=>{
 if(message.type==='connection-status'&&sender.id===chrome.runtime.id&&sender.url===chrome.runtime.getURL('connection.html')){
  poll().then(()=>reply({connected:[...seen.values()].some(at=>Date.now()-at<=6000),protocol:4,version:chrome.runtime.getManifest().version}));return true;
 }
 const id=sender.tab?.id,previous=serial.get(id)||Promise.resolve();
 const next=previous.catch(()=>{}).then(()=>handle(message,sender));serial.set(id,next);
 next.then(reply,()=>reply({error:'原连接暂时中断，原提交会继续保留；不会重发。'})).finally(()=>{if(serial.get(id)===next)serial.delete(id)});return true;
});
chrome.alarms.create('tb-browser-heartbeat',{periodInMinutes:.5});
chrome.alarms.onAlarm.addListener(async alarm=>{if(alarm.name!=='tb-browser-heartbeat')return;await poll();const jobs=(await chrome.storage.session.get('jobs')).jobs||{};for(const job of Object.values(jobs))await chrome.tabs.sendMessage(job.tabId,{type:'wake'}).catch(()=>{})});
chrome.runtime.onStartup.addListener(poll);chrome.runtime.onInstalled.addListener(poll);
setInterval(poll,1000);poll();
