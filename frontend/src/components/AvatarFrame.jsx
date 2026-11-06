import {safeTier} from './RankArtwork.jsx';
import assets from '@/lib/rankAssets.json';
import inline from '@/lib/rankArtworkInline.json';
import {useId} from 'react';

export default function AvatarFrame({index=0}) {
 const tier=safeTier(index),asset=assets[tier],id=useId().replaceAll(':',''),trim=tier<6;
 const rim=['#92989c','#c79a62','#bcc9d4','#dfc878','#86cfc2','#9ebcdb'][tier];
 return <svg className={`avatar-rank-frame rank-reference-art tier-${tier}`} viewBox="0 0 512 512" fill="none" aria-hidden="true" data-rank-art={asset.name}>
  {trim&&<defs><clipPath id={'rank-trim-'+id} clipPathUnits="userSpaceOnUse"><path clipRule="evenodd" d="M0 0H512V512H0Z M233 184V214H279V184Z"/></clipPath><linearGradient id={'rank-rim-'+id} x1="232" y1="196" x2="280" y2="207" gradientUnits="userSpaceOnUse"><stop stopColor={rim}/><stop offset=".5" stopColor="#f5e7b7"/><stop offset="1" stopColor={rim}/></linearGradient></defs>}
  {tier===8?<><defs><clipPath id={'rank-body-'+id}><path d="M0 192H512V512H0Z"/></clipPath></defs><svg x="0" y="164" width="512" height="28" viewBox="0 0 512 192" preserveAspectRatio="none" overflow="hidden"><image href={inline[asset.name].avatar} width="512" height="512"/></svg><image href={inline[asset.name].avatar} width="512" height="512" clipPath={`url(#rank-body-${id})`}/></>:<image href={inline[asset.name].avatar} width="512" height="512" clipPath={trim?`url(#rank-trim-${id})`:undefined}/>}
  {trim&&<path d="M232 201 A60 60 0 0 1 280 201" stroke={`url(#rank-rim-${id})`} strokeWidth="3.4" strokeLinecap="round"/>}
 </svg>;
}
