import {safeTier} from './RankArtwork.jsx';
import assets from '@/lib/rankAssets.json';
import inline from '@/lib/rankArtworkInline.json';
import {memo,useId} from 'react';

// Ease the original upper feathers into the untouched body with a matching
// tangent at y=192. Shared image references preserve the original PNG bytes.
const wingStep=.5;
const wingStrips=Array.from({length:384},(_,i)=>{const top=i*wingStep,y=165+27*Math.exp((top-192)/27),bottom=165+27*Math.exp((top+wingStep-192)/27),width=Math.sin(((y+bottom)/2-165)/27*Math.PI/2);return {top,y,height:bottom-y,width};});

export default memo(function AvatarFrame({index=0}) {
 const tier=safeTier(index),asset=assets[tier],id=useId().replaceAll(':',''),trim=tier<6;
 const rim=['#92989c','#c79a62','#bcc9d4','#dfc878','#86cfc2','#9ebcdb'][tier];
 return <svg className={`avatar-rank-frame rank-reference-art tier-${tier}`} viewBox="0 0 512 512" fill="none" aria-hidden="true" data-rank-art={asset.name}>
  {trim&&<defs><clipPath id={'rank-trim-'+id} clipPathUnits="userSpaceOnUse"><path clipRule="evenodd" d="M0 0H512V512H0Z M233 184V214H279V184Z"/></clipPath><linearGradient id={'rank-rim-'+id} x1="232" y1="196" x2="280" y2="207" gradientUnits="userSpaceOnUse"><stop stopColor={rim}/><stop offset=".5" stopColor="#f5e7b7"/><stop offset="1" stopColor={rim}/></linearGradient></defs>}
  {tier===8?<><defs><image id={'rank-original-'+id} href={inline[asset.name].avatar} width="512" height="512"/><clipPath id={'rank-body-'+id}><path d="M0 192H512V512H0Z"/></clipPath><clipPath id={'rank-left-'+id}><path d="M0 0H256V192H0Z"/></clipPath><clipPath id={'rank-right-'+id}><path d="M256 0H512V192H256Z"/></clipPath></defs>{wingStrips.map(({top,y,height,width})=><svg key={top} x="0" y={y} width="512" height={height} viewBox={`0 ${top} 512 ${wingStep}`} preserveAspectRatio="none" overflow="hidden" shapeRendering="geometricPrecision">{[170,342].map((center,index)=><g key={center} transform={`translate(${center*(1-width)} 0) scale(${width} 1)`}><use href={'#rank-original-'+id} clipPath={`url(#rank-${index?'right':'left'}-${id})`}/></g>)}</svg>)}<use href={'#rank-original-'+id} clipPath={`url(#rank-body-${id})`}/></>:<image href={inline[asset.name].avatar} width="512" height="512" clipPath={trim?`url(#rank-trim-${id})`:undefined}/>}
  {trim&&<path d="M232 201 A60 60 0 0 1 280 201" stroke={`url(#rank-rim-${id})`} strokeWidth="3.4" strokeLinecap="round"/>}
 </svg>;
});
