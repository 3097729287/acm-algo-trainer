import {useEffect,useState} from 'react';
import {isAvatarData} from '@/components/ProfileBadge.jsx';

// The API callback belongs to one mounted authenticated workspace. Weak keys
// isolate endpoints/accounts and release retired sessions; content hashes make
// a changed avatar a different entry. Never cache failures or mismatched data.
const stores=new WeakMap(),LIMIT=96,DISK_LIMIT=24,DISK_CHARS=2*1024*1024,DISK_KEY='tb.public-avatars.v1';
const ownerId=()=>String(window.__tbAccountUserId||'');
const validOwner=value=>typeof value==='string'&&/^[a-zA-Z0-9_-]{1,80}$/.test(value);
const validHash=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
function diskEntries() {
 try {
  const raw=localStorage.getItem(DISK_KEY);
  if(!raw||raw.length>DISK_CHARS)return [];
  const value=JSON.parse(raw);
  if(value?.version!==1||!Array.isArray(value.entries)||value.entries.length>DISK_LIMIT)return [];
  return value.entries.filter(item=>item&&Object.keys(item).every(key=>['owner','userId','hash','data'].includes(key))&&validOwner(item.owner)&&validOwner(item.userId)&&validHash(item.hash)&&isAvatarData(item.data));
 } catch { return []; }
}
function persist(owner,userId,hash,data) {
 if(!validOwner(owner)||!validOwner(userId))return;
 let entries=diskEntries().filter(item=>item.owner!==owner||item.userId!==userId);
 if(hash&&data)entries.push({owner,userId,hash,data});
 entries=entries.slice(-DISK_LIMIT);
 while(entries.length) {
  const raw=JSON.stringify({version:1,entries});
  if(raw.length>DISK_CHARS){entries.shift();continue;}
  try {localStorage.setItem(DISK_KEY,raw);return;}
  catch(issue) {
   if(issue.name!=='QuotaExceededError')return;
   // Only reduce our public cache. Browser drafts/settings remain untouched.
   if(entries.length===1)return;
   entries=entries.slice(Math.ceil(entries.length/2));
  }
 }
 try {localStorage.setItem(DISK_KEY,JSON.stringify({version:1,entries:[]}));}catch{/* Memory cache still works. */}
}
function storeFor(api,owner) {
 let store=stores.get(api);
 if(!store||store.owner!==owner){
  store={owner,images:new Map(),pending:new Map()};
  for(const item of diskEntries())if(item.owner===owner)store.images.set(`${item.userId}:${item.hash}`,item.data);
  stores.set(api,store);
 }
 return store;
}
function cached(store,key) {
 const value=store.images.get(key);
 if(value){store.images.delete(key);store.images.set(key,value);}
 return value||null;
}
function load(store,api,userId,hash,key) {
 if(store.pending.has(key))return store.pending.get(key);
 const pending=api(`leaderboard/avatar?${new URLSearchParams({userId,hash})}`).then(value=>{
  if(value.avatarHash!==hash||!isAvatarData(value.avatarData))throw new Error('Avatar version not available');
  store.images.set(key,value.avatarData);
  while(store.images.size>LIMIT)store.images.delete(store.images.keys().next().value);
  persist(store.owner,userId,hash,value.avatarData);
  return value.avatarData;
 }).finally(()=>{if(store.pending.get(key)===pending)store.pending.delete(key);});
 store.pending.set(key,pending);
 return pending;
}
export default function usePublicAvatar(api,userId,hash) {
 const store=storeFor(api,ownerId()),key=`${userId}:${hash}`;
 const [saved,setSaved]=useState(()=>({store,key,data:cached(store,key)}));
 useEffect(()=>{
  if(!hash){
   for(const old of store.images.keys())if(old.startsWith(`${userId}:`))store.images.delete(old);
   persist(store.owner,userId,null,null);
   return;
  }
  let active=true,timer,attempt=0;
  const hit=cached(store,key);
  if(hit){setSaved({store,key,data:hit});return;}
  const fetchAvatar=()=>load(store,api,userId,hash,key).then(data=>{
   if(active)setSaved({store,key,data});
  }).catch(()=>{
   if(!active)return;
   setSaved({store,key,data:null});
   if(attempt<2)timer=setTimeout(fetchAvatar,++attempt*3000);
  });
  fetchAvatar();
  return()=>{active=false;clearTimeout(timer);};
 },[api,userId,hash,key,store]);
 return hash?(cached(store,key)||(saved?.store===store&&saved?.key===key?saved.data:null)):null;
}
