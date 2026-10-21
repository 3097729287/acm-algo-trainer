import {useId} from 'react';

export default function AvatarFrame({index=0}) {
 const tier=Math.max(0,Math.min(9,index)),id=useId().replace(/:/g,''),metal=`avatar-metal-${id}`,inlay=`avatar-inlay-${id}`;
 return <svg className={`avatar-rank-frame tier-${tier}`} viewBox="0 0 100 100" fill="none" stroke="currentColor" strokeWidth="1" strokeLinejoin="round" aria-hidden="true">
  <defs>
   <linearGradient id={metal} x1="0" y1="0" x2="0" y2="1"><stop stopColor="currentColor" stopOpacity=".5"/><stop offset=".22" stopColor="currentColor"/><stop offset=".48" stopColor="currentColor" stopOpacity=".42"/><stop offset=".78" stopColor="currentColor" stopOpacity=".8"/><stop offset="1" stopColor="currentColor" stopOpacity=".45"/></linearGradient>
   <linearGradient id={inlay} x1="0" y1="0" x2="0" y2="1"><stop stopColor="currentColor" stopOpacity=".28"/><stop offset="1" stopColor="currentColor" stopOpacity=".05"/></linearGradient>
  </defs>
  <circle cx="50" cy="50" r="40" strokeOpacity=".23" strokeWidth=".7"/>
  <circle cx="50" cy="50" r="37" stroke={`url(#${metal})`} strokeWidth="4.6"/>
  <circle cx="50" cy="50" r="39.4" strokeOpacity=".75" strokeWidth=".65"/>
  <circle cx="50" cy="50" r="34.5" strokeOpacity=".7" strokeWidth=".65"/>
  {[0,90,180,270].map(angle=><path key={angle} transform={`rotate(${angle} 50 50)`} d="M47 10.6h6l-1.4 4.1h-3.2Z" fill={`url(#${inlay})`} strokeOpacity=".75" strokeWidth=".7"/>)}
  {tier>=1&&[0,1].map(side=><g key={side} transform={side?'translate(100 0) scale(-1 1)':undefined}>
   <path d="M17 27 11 34 7 50l4 16 6 7-4-23Z" fill={`url(#${inlay})`} strokeOpacity=".7" strokeWidth=".8"/>
   <path d="m11 37-3 13 3 13" strokeOpacity=".36" strokeWidth=".6"/>
  </g>)}
  {tier>=3&&<path d="m41 13 3-6 6 4 6-4 3 6-9 5Z" fill={`url(#${metal})`} strokeWidth=".8"/>}
  {tier>=5&&[45,135,225,315].map(angle=><path key={angle} transform={`rotate(${angle} 50 50)`} d="m50 9 2.5 4-2.5 4-2.5-4Z" fill={`url(#${metal})`} strokeWidth=".5"/>)}
  {tier>=7&&<path d="m50 3 4 5-4 5-4-5Z" fill={`url(#${metal})`} strokeWidth=".7"/>}
  {tier>=8&&[0,1].map(side=><path key={side} transform={side?'translate(100 0) scale(-1 1)':undefined} d="m15 28-5-6-2 13m7 37-5 6-2-13" strokeOpacity=".7"/>)}
  {tier===9&&<path d="m35 12 2-7 5 5m23 2-2-7-5 5" strokeWidth="1.2"/>}
 </svg>;
}
