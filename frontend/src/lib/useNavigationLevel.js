import {useEffect,useState} from 'react';

const valid=level=>Number.isInteger(level)&&level>=1&&level<=100;
const key=owner=>`tb.navigation-level.v1.${owner}`;
function remembered(owner) {
 if(!owner)return null;
 try {const value=JSON.parse(localStorage.getItem(key(owner))||'null');return value?.owner===owner&&valid(value.level)?value.level:null;}
 catch {return null;}
}
export default function useNavigationLevel(owner,confirmed) {
 const [saved,setSaved]=useState(()=>({owner,level:remembered(owner)}));
 const known=valid(confirmed)?confirmed:saved.owner===owner?saved.level:remembered(owner);
 useEffect(()=>{
  if(!owner||!valid(confirmed))return;
  const value={owner,level:confirmed};setSaved(value);
  try {localStorage.setItem(key(owner),JSON.stringify(value));}catch{/* Confirmed session data still works. */}
 },[owner,confirmed]);
 return {level:owner?known:Infinity,pending:Boolean(owner&&known==null)};
}
