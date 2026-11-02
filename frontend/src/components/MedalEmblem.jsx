import {useId} from 'react';
import {KingCrown,RankDefs,RankGem,RankWings,safeTier} from './RankArtwork.jsx';
import './TierIcon.css';
import TitleMedallion from './TitleMedallion.jsx';

export function titleMedalIndex(title){const difficulty=title?.category==='difficulty',targets=difficulty?[1500,1600,1700,1800,1900,2000,2150,2300]:title?.category==='streak'?[30,90,180,365,730]:[500,750,1000,1500,2000],index=Math.max(0,targets.indexOf(Number(title?.target)));return difficulty?Math.round(index*9/7):index*2+1;}
export default function MedalEmblem({index=0,size=30,variant='rank',label}){
 const tier=Math.max(0,Math.min(9,index)),title=variant!=='rank',id=useId().replace(/:/g,'');
 if(!title){
  const rank=safeTier(index),rankId=`rank-${id}`;
  return <svg className={`medal-emblem tier-${rank} medal-rank`} width={size} height={size*1.15} viewBox="0 0 120 138" role={label?'img':undefined} aria-label={label} aria-hidden={label?undefined:true} fill="none">
   <RankDefs id={rankId} tier={rank}/>
   <g transform="translate(0 18)">
    <RankWings id={rankId} tier={rank}/>
    <path d={rank===8?'M28 72Q60 100 92 72L80 89Q60 105 40 89Z':'M30 65 60 87 90 65 78 86 60 103 42 86Z'} fill={`url(#${rankId}-metal)`}/>
    {rank!==8&&<path d="M37 69 60 87 83 69 72 84 60 92 48 84Z" fill={`url(#${rankId}-facet)`}/>}
    <RankGem id={rankId} tier={rank} y={65} scale={rank===8?.92:rank>=4?1.1:.9}/>
    {rank===8?<KingCrown id={rankId} y={36}/>:rank>=3&&<path d={rank>=6?'M44 37 47 24 60 31 73 24 76 37 60 44Z':'M49 41 60 31 71 41 60 45Z'} fill={`url(#${rankId}-metal)`}/>}
   </g>
  </svg>;
 }
 return <TitleMedallion tier={tier} size={size} variant={variant} label={label} id={id}/>;
}
