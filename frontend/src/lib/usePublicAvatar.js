import {useCallback,useEffect,useSyncExternalStore} from 'react';
import {isAvatarData} from '@/components/ProfileBadge.jsx';

// The API callback belongs to one mounted authenticated workspace. Weak keys
// isolate endpoints/accounts and release retired sessions; content hashes make
// a changed avatar a different entry. A validated target response can be newer
// than a cached period's hash; remember that redirect without caching failures.
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
  store={owner,images:new Map(),pending:new Map(),aliases:new Map(),epochs:new Map(),listeners:new Set()};
  for(const item of diskEntries())if(item.owner===owner)store.images.set(`${item.userId}:${item.hash}`,item.data);
  stores.set(api,store);
 }
 return store;
}
function cached(store,key) {
 const target=store.aliases.has(key)?store.aliases.get(key):key;
 return target?store.images.get(target)||null:null;
}
function notify(store) { for(const listener of store.listeners)listener(); }
function clearTarget(store,userId) {
 store.epochs.set(userId,(store.epochs.get(userId)||0)+1);
 for(const key of store.images.keys())if(key.startsWith(`${userId}:`))store.images.delete(key);
 for(const key of store.aliases.keys())if(key.startsWith(`${userId}:`))store.aliases.set(key,null);
 persist(store.owner,userId,null,null);
 notify(store);
}
function load(store,api,userId,hash,key) {
 if(store.pending.has(key))return store.pending.get(key);
 const epoch=store.epochs.get(userId)||0;
 const pending=api(`leaderboard/avatar?${new URLSearchParams({userId,hash})}`).then(value=>{
  if(ownerId()!==store.owner||(store.epochs.get(userId)||0)!==epoch)throw new Error('Avatar request retired');
  if(value.avatarHash==null&&value.avatarData===''){clearTarget(store,userId);return null;}
  if(!validHash(value.avatarHash)||!isAvatarData(value.avatarData))throw new Error('Avatar version not available');
  const current=`${userId}:${value.avatarHash}`;
  // The local API has verified the returned image and digest for this target.
  // Retire old versions so switching back to a cached board cannot restore one.
  for(const old of store.images.keys())if(old.startsWith(`${userId}:`)&&old!==current){store.images.delete(old);store.aliases.set(old,current);}
  for(const old of store.aliases.keys())if(old.startsWith(`${userId}:`))store.aliases.set(old,current);
  store.aliases.delete(current);
  if(key!==current)store.aliases.set(key,current);
  store.images.delete(current);store.images.set(current,value.avatarData);
  while(store.images.size>LIMIT)store.images.delete(store.images.keys().next().value);
  while(store.aliases.size>LIMIT)store.aliases.delete(store.aliases.keys().next().value);
  persist(store.owner,userId,value.avatarHash,value.avatarData);
  notify(store);
  return value.avatarData;
 }).finally(()=>{if(store.pending.get(key)===pending)store.pending.delete(key);});
 store.pending.set(key,pending);
 return pending;
}
export default function usePublicAvatar(api,userId,hash) {
 const store=storeFor(api,ownerId()),key=`${userId}:${hash}`;
 const subscribe=useCallback(listener=>{store.listeners.add(listener);return()=>store.listeners.delete(listener);},[store]);
 const snapshot=useCallback(()=>hash?cached(store,key):null,[store,key,hash]);
 const image=useSyncExternalStore(subscribe,snapshot,snapshot);
 useEffect(()=>{
  if(!hash){
   clearTarget(store,userId);
   return;
  }
  let active=true,timer,attempt=0;
  const hit=cached(store,key);
  if(hit)return;
  const fetchAvatar=()=>load(store,api,userId,hash,key).catch(()=>{
   if(!active||ownerId()!==store.owner)return;
   // Recover automatically after a transient failure, even after the first
   // three attempts. Back off to thirty seconds and pause hidden-page work.
   const delay=Math.min(30000,3000*2**Math.min(attempt++,4));
   timer=setTimeout(()=>{if(!document.hidden)fetchAvatar();},delay);
  });
  const wake=()=>{if(active&&!document.hidden){clearTimeout(timer);fetchAvatar();}};
  window.addEventListener('online',wake);document.addEventListener('visibilitychange',wake);
  fetchAvatar();
  return()=>{active=false;clearTimeout(timer);window.removeEventListener('online',wake);document.removeEventListener('visibilitychange',wake);};
 },[api,userId,hash,key,store]);
 return image;
}
