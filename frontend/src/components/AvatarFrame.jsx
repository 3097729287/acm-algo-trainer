import {useId} from 'react';
import {RankDefs,RankWings,safeTier} from './RankArtwork.jsx';

export default function AvatarFrame({index=0}) {
 const tier=safeTier(index),id=`avatar-${useId().replace(/:/g,'')}`;
 return <svg className={`avatar-rank-frame tier-${tier}`} viewBox="0 0 120 120" fill="none" aria-hidden="true">
  <RankDefs id={id} tier={tier}/>
  <defs><mask id={`${id}-outside`}><rect width="120" height="120" fill="white"/><circle cx="60" cy="60" r="31.4" fill="black"/></mask></defs>
  <g mask={`url(#${id}-outside)`}>
   <RankWings id={id} tier={tier} portrait/>
   <path d="M34 89 48 103 60 110 72 103 86 89 73 98 60 103 47 98Z" fill={`url(#${id}-metal)`} stroke={`url(#${id}-edge)`} strokeWidth=".8"/>
  </g>
  <circle cx="60" cy="60" r="33.2" stroke={`url(#${id}-metal)`} strokeWidth="2.8"/>
  <circle cx="60" cy="60" r="35.2" stroke={`url(#${id}-edge)`} strokeWidth=".65"/>
  <path d="M29 48a33 33 0 0 1 49-16" stroke={`url(#${id}-edge)`} strokeWidth=".8" strokeLinecap="round"/>
 </svg>;
}
