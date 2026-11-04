// Short-lived memory only. No private template code is written to browser
// storage, and a late response can never initialize another account's page.
const values=new WeakMap(),requests=new WeakMap(),allowed=new Set(['templates','lectures','wiki']);
const current=owner=>(window.__tbAccountUserId||'local')===owner;
function entries(map,api){let value=map.get(api);if(!value){value=new Map();map.set(api,value);}return value;}
const key=(owner,path)=>owner+'\0'+path;
export function readCatalogue(api,owner,path){
 if(!allowed.has(path)||!current(owner))return null;
 const saved=values.get(api)?.get(key(owner,path)),age=saved?Date.now()-saved.at:Infinity;return saved&&age>=0&&age<60000?saved.value:null;
}
export function cacheCatalogue(api,owner,path,value){
 if(!allowed.has(path)||!current(owner))return;
 const cache=entries(values,api);if(cache.size>=12)cache.delete(cache.keys().next().value);cache.set(key(owner,path),{at:Date.now(),value});
}
export function loadCatalogue(api,owner,path,{refresh=false}={}){
 if(!allowed.has(path)||!current(owner))return Promise.reject(new Error('目录账号已切换'));
 const cache=refresh?null:readCatalogue(api,owner,path);if(cache)return Promise.resolve(cache);
 const pending=entries(requests,api),id=key(owner,path);if(pending.has(id))return pending.get(id);
 const request=Promise.resolve().then(()=>api(path)).then(value=>{if(!current(owner))throw new Error('目录账号已切换');cacheCatalogue(api,owner,path,value);return value;}).finally(()=>{if(pending.get(id)===request)pending.delete(id);});
 pending.set(id,request);return request;
}
