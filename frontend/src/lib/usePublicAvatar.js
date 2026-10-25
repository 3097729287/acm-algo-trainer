import {useEffect,useState} from 'react';
import {isAvatarData} from '@/components/ProfileBadge.jsx';
export default function usePublicAvatar(api,userId,hash) {
 const [saved,setSaved]=useState(null),key=`${userId}:${hash}`;
 useEffect(()=>{
  if(!hash)return;
  let active=true;
  api(`leaderboard/avatar?${new URLSearchParams({userId,hash})}`).then(value=>{
   if(active)setSaved({key,data:isAvatarData(value.avatarData)?value.avatarData:null});
  }).catch(()=>{if(active)setSaved({key,data:null});});
  return()=>{active=false;};
 },[api,userId,hash,key]);
 return saved?.key===key?saved.data:null;
}
