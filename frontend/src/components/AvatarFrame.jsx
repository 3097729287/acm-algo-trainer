import {useId} from 'react';
import {RankDefs,RankGem,RankWings,safeTier} from './RankArtwork.jsx';

export default function AvatarFrame({index=0}) {
 const tier=safeTier(index),id=`avatar-${useId().replace(/:/g,'')}`;
 return <svg className={`avatar-rank-frame tier-${tier}`} viewBox="0 0 120 120" fill="none" aria-hidden="true">
  <RankDefs id={id} tier={tier}/>
  <circle cx="60" cy="60" r="35" stroke={`url(#${id}-metal)`} strokeWidth="4"/>
  <circle cx="60" cy="60" r="37.7" stroke={`url(#${id}-facet)`} strokeWidth=".7"/>
  <RankWings id={id} tier={tier} portrait/>
  <path d="M29 82 42 90 60 96 78 90 91 82 79 96 60 103 41 96Z" fill={`url(#${id}-metal)`}/>
  <RankGem id={id} tier={0} y={95} scale={.23}/>
  {tier>=3&&<path d={tier>=6?'M48 23 50 14 60 20 70 14 72 23 60 27Z':'M51 25 60 18 69 25 60 28Z'} fill={`url(#${id}-metal)`}/>}
  {tier===8&&<path d="M40 26 38 17 48 22M80 26 82 17 72 22" stroke={`url(#${id}-gem)`} strokeWidth="2"/>}
 </svg>;
}
