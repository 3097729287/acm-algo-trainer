import {useEffect,useState} from 'react';
import {trainingDay} from './trainingDate.js';
const kinds=new Set(['conflicts','login','upgrade','recovery']);
const load=owner=>{try{const rows=JSON.parse(sessionStorage.getItem(`tb.sync-notices.${owner}`)||'[]');return Array.isArray(rows)?rows.filter(row=>row.owner===owner&&trainingDay(row.createdAt)===trainingDay(new Date().toISOString())).slice(-12):[];}catch{return [];}};
export default function useSyncNotices(owner) {
 const [items,setItems]=useState(()=>load(owner));
 useEffect(()=>{
  setItems(load(owner));
  const receive=event=>{
   const value=event.detail;
   if(!owner||value?.owner!==owner||!kinds.has(value.kind)||typeof value.message!=='string')return;
   const id=String(value.id||`${value.kind}:${value.conflictCount||0}`).slice(0,120);
   setItems(previous=>previous.some(row=>row.id===id)?previous:[...previous,{id,owner,kind:value.kind,message:value.message.slice(0,300),createdAt:new Date().toISOString(),read:false}].slice(-12));
  };
  window.addEventListener('tb:account-sync-attention',receive);
  const sync=window.__tbAccountSync;
  if(sync?.attention)receive({detail:{owner,kind:sync.attention,id:`${sync.attention}:${sync.conflictCount||0}`,conflictCount:sync.conflictCount,message:sync.error||'账号同步有需要处理的信息，请检查账号状态。'}});
  return()=>window.removeEventListener('tb:account-sync-attention',receive);
 },[owner]);
 useEffect(()=>{if(owner)try{sessionStorage.setItem(`tb.sync-notices.${owner}`,JSON.stringify(items));}catch{}},[owner,items]);
 return {items,markRead:()=>setItems(previous=>previous.map(row=>({...row,read:true})))};
}
