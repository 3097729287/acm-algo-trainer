import {useSyncExternalStore} from 'react';

export const PLAYBACK_SPEEDS=Object.freeze([.25,.5,.75,1,1.25,1.5,2,3]);
const changed='tb:editorial-playback-speed',memory=new Map();
const key=()=>`tb.editorial-playback.v1.${window.__tbAccountUserId||window.__tbAccount?.userId||'local'}`;
const valid=value=>PLAYBACK_SPEEDS.includes(Number(value))?Number(value):1;
function read(){const name=key();try{return valid(localStorage.getItem(name)??memory.get(name));}catch{return memory.get(name)||1;}}
function subscribe(callback){window.addEventListener(changed,callback);window.addEventListener('storage',callback);window.addEventListener('tb:account-state',callback);return()=>{window.removeEventListener(changed,callback);window.removeEventListener('storage',callback);window.removeEventListener('tb:account-state',callback);};}
export function useEditorialPlaybackSpeed(){
 const speed=useSyncExternalStore(subscribe,read,()=>1);
 const setSpeed=value=>{const speed=valid(value),name=key();memory.set(name,speed);try{localStorage.setItem(name,String(speed));}catch{/* Keep this session usable if device storage is unavailable. */}window.dispatchEvent(new Event(changed));};
 return [speed,setSpeed];
}
