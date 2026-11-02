import {useId} from 'react';
import {KingCrown,RankDefs,RankGem,RankWings,safeTier} from './RankArtwork.jsx';

export default function AvatarFrame({index=0}) {
 const tier=safeTier(index),id=`avatar-${useId().replace(/:/g,'')}`;
 return <svg className={`avatar-rank-frame tier-${tier}`} viewBox="0 0 120 120" fill="none" aria-hidden="true">
  <RankDefs id={id} tier={tier}/>
  <defs><mask id={`${id}-outside`}><rect width="120" height="120" fill="white"/><circle cx="60" cy="60" r="33.5" fill="black"/></mask></defs>
  <circle cx="60" cy="60" r="35" stroke={`url(#${id}-metal)`} strokeWidth={tier===8?'3.3':'4'}/>
  <circle cx="60" cy="60" r="37.7" stroke={`url(#${id}-facet)`} strokeWidth={tier===8?'.45':'.7'}/>
  {tier===8&&<><circle cx="60" cy="60" r="33.2" stroke="#686b63" strokeWidth=".55"/><circle cx="60" cy="60" r="36.7" stroke={`url(#${id}-edge)`} strokeWidth=".45"/><path d="M29 43a35 35 0 0 1 42-17" stroke="#fffbed" strokeOpacity=".9" strokeWidth=".65" strokeLinecap="round"/></>}
  <g mask={`url(#${id}-outside)`}>
  <RankWings id={id} tier={tier} portrait/>
  <path d={tier===8?'M31 84Q60 110 89 84L81 94Q60 110 39 94Z':'M29 82 42 90 60 96 78 90 91 82 79 96 60 103 41 96Z'} fill={`url(#${id}-metal)`}/>
  <RankGem id={id} tier={0} y={95} scale={.23}/>
  {tier===8?<KingCrown id={id} y={25}/>:tier>=3&&<path d={tier>=6?'M48 23 50 14 60 20 70 14 72 23 60 27Z':'M51 25 60 18 69 25 60 28Z'} fill={`url(#${id}-metal)`}/>}
  </g>
 </svg>;
}
