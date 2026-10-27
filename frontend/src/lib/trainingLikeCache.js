const entries=new Map();
const pending=new Map(),generations=new Map();
const key=owner=>`tb:list-likes:v2:${owner}`;
export function readTrainingLikes(owner){
 if(entries.has(owner))return entries.get(owner);
 let value={available:true,likes:{}};
 try{const saved=JSON.parse(localStorage.getItem(key(owner))||'null');if(saved?.likes)value=saved;}catch{}
 entries.set(owner,value);return value;
}
export function saveTrainingLikes(owner,value){entries.set(owner,value);try{localStorage.setItem(key(owner),JSON.stringify(value));}catch{}return value;}
export function beginTrainingLikeWrite(owner){generations.set(owner,(generations.get(owner)||0)+1);}
export function prefetchTrainingLikes(owner,api){
 if(pending.has(owner))return pending.get(owner);
 const generation=generations.get(owner)||0;
 const request=api('training-list-likes').then(value=>generation===(generations.get(owner)||0)?saveTrainingLikes(owner,value):readTrainingLikes(owner)).finally(()=>pending.delete(owner));
 pending.set(owner,request);return request;
}
