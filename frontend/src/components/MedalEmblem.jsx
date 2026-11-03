import {useId} from 'react';
import {KingCrown,RankDefs,RankGem,RankWings,safeTier} from './RankArtwork.jsx';
import './TierIcon.css';
import TitleMedallion from './TitleMedallion.jsx';

export function titleMedalIndex(title){const difficulty=title?.category==='difficulty',targets=difficulty?[1500,1600,1700,1800,1900,2000,2150,2300]:title?.category==='streak'?[30,90,180,365,730]:[500,750,1000,1500,2000],index=Math.max(0,targets.findLastIndex(target=>Number(title?.target)>=target));return difficulty?Math.round(index*9/7):index*2+1;}
export default function MedalEmblem({index=0,size=30,variant='rank',label}){
 const tier=Math.max(0,Math.min(9,index)),title=variant!=='rank',id=useId().replace(/:/g,'');
 if(!title){
  const rank=safeTier(index),rankId=`rank-${id}`;
  return <svg className={`medal-emblem tier-${rank} medal-rank`} width={size} height={size} viewBox="0 0 120 120" role={label?'img':undefined} aria-label={label} aria-hidden={label?undefined:true} fill="none">
   <RankDefs id={rankId} tier={rank}/>
   <g>
    <RankWings id={rankId} tier={rank}/>
    <RankGem id={rankId} tier={rank} y={68} scale={1}/>
   </g>
  </svg>;
 }
 return <TitleMedallion tier={tier} size={size} variant={variant} label={label} id={id}/>;
}
