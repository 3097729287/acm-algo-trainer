import {useEffect,useState} from 'react';
import {isAvatarData} from '@/components/ProfileBadge.jsx';
export default function usePublicAvatar(api,userId,hash) {
 const [saved,setSaved]=useState(null),key=`${userId}:${hash}`;
 useEffect(()=>{
  if(!hash)return;
  let active=true,timer,attempt=0;
  const fetchAvatar=()=>api(`leaderboard/avatar?${new URLSearchParams({userId,hash})}`).then(value=>{
   if(!isAvatarData(value.avatarData))throw new Error('Avatar not available');
   if(active)setSaved({key,data:value.avatarData});
  }).catch(()=>{
   if(!active)return;
   setSaved({key,data:null});
   if(attempt<2)timer=setTimeout(fetchAvatar,++attempt*3000);
  });
  fetchAvatar();
  return()=>{active=false;clearTimeout(timer);};
 },[api,userId,hash,key]);
 return saved?.key===key?saved.data:null;
}
