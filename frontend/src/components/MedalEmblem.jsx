import {useId} from 'react';
import {safeTier} from './RankArtwork.jsx';
import assets from '@/lib/rankAssets.json';
import inline from '@/lib/rankArtworkInline.json';
import './TierIcon.css';
import TitleMedallion from './TitleMedallion.jsx';

export function titleMedalIndex(title){const difficulty=title?.category==='difficulty',targets=difficulty?[1500,1600,1700,1800,1900,2000,2150,2300]:title?.category==='streak'?[30,90,180,365,730]:[500,750,1000,1500,2000],index=Math.max(0,targets.findLastIndex(target=>Number(title?.target)>=target));return difficulty?Math.round(index*9/7):index*2+1;}
export default function MedalEmblem({index=0,size=30,variant='rank',label}){
 const tier=Math.max(0,Math.min(9,index)),title=variant!=='rank',id=useId().replace(/:/g,'');
 if(!title){
  const rank=safeTier(index),asset=assets[rank],[x,y,x2,y2]=asset.emblemBounds;
  return <svg className={`medal-emblem tier-${rank} medal-rank`} width={size} height={size*1.15} viewBox={`${x-4} ${y-4} ${x2-x+8} ${y2-y+8}`} role={label?'img':undefined} aria-label={label} aria-hidden={label?undefined:true} data-rank-art={asset.name}>
   <image href={inline[asset.name].emblem} width={asset.emblemSize[0]} height={asset.emblemSize[1]}/>
  </svg>;
 }
 return <TitleMedallion tier={tier} size={size} variant={variant} label={label} id={id}/>;
}
