import {useId} from 'react';
import './TierIcon.css';

export function titleMedalIndex(title){const targets=title?.category==='streak'?[30,90,180,365,730]:[500,750,1000,1500,2000];return Math.max(0,targets.indexOf(Number(title?.target)))*2+1;}
export default function MedalEmblem({index=0,size=30,variant='rank',label}){
 const tier=Math.max(0,Math.min(9,index)),title=variant!=='rank',id=useId().replace(/:/g,''),metal=`medal-metal-${id}`,face=`medal-face-${id}`;
 const outline=title?'M40 12 49 17 59 17 63 26 70 33 67 43 67 53 58 58 50 66 40 64 30 66 22 58 13 53 13 43 10 33 17 26 21 17 31 17Z':'M40 11 65 21v21c0 17-11 28-25 35-14-7-25-18-25-35V21Z';
 return <svg className={`medal-emblem tier-${tier} medal-${variant}`} width={size} height={size*1.15} viewBox="0 0 80 92" role={label?'img':undefined} aria-label={label} aria-hidden={label?undefined:true} fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round">
  <defs>
   <linearGradient id={metal} x1="0" y1="0" x2="0" y2="1"><stop stopColor="currentColor" stopOpacity=".95"/><stop offset=".3" stopColor="currentColor" stopOpacity=".5"/><stop offset=".56" stopColor="currentColor" stopOpacity=".85"/><stop offset="1" stopColor="currentColor" stopOpacity=".4"/></linearGradient>
   <linearGradient id={face} x1="0" y1="0" x2="0" y2="1"><stop stopColor="currentColor" stopOpacity=".18"/><stop offset=".55" stopColor="currentColor" stopOpacity=".04"/><stop offset="1" stopColor="currentColor" stopOpacity=".1"/></linearGradient>
  </defs>
  {[0,1].map(side=><g key={side} transform={side?'translate(80 0) scale(-1 1)':undefined}>
   <path d="m24 56-7 28 13-6 9 9 3-23Z" fill={`url(#${face})`} strokeOpacity=".65"/>
   <path d="m25 65-3 12 9-4 4 5" strokeOpacity=".3" strokeWidth=".7"/>
   {tier>=3&&<path d="M17 53C8 49 6 37 10 27l6 5-3 7 4 5Z" fill={`url(#${face})`} strokeOpacity=".55"/>}
   {tier>=7&&<path d="m13 55-8-9 2-8m7 23-8-3" strokeOpacity=".6" strokeWidth=".9"/>}
  </g>)}
  <path d={outline} className="medal-face" fill="var(--panel-base)" stroke={`url(#${metal})`} strokeWidth="2.4"/>
  <path d={outline} fill={`url(#${face})`} stroke="none"/>
  {title?<circle cx="40" cy="39" r="21" strokeOpacity=".4" strokeWidth=".75"/>:<path d="m40 18 18 8v16c0 12-7 21-18 27-11-6-18-15-18-27V26Z" strokeOpacity=".45" strokeWidth=".8"/>}
  {title?(variant==='streak'?<path d="M41 26c2 7-6 10-5 16 3 0 5-2 6-5 8 8 6 17-2 17-10 0-13-8-8-15 0 4 2 5 3 6-1-7 5-10 6-19Z" fill={`url(#${metal})`} strokeWidth=".7"/>:<path d="m28 40 8 8 17-18" strokeWidth="3" strokeLinecap="round"/>):<>
   <path d="m40 27 11 16-11 17-11-17Z" fill={`url(#${metal})`} strokeOpacity=".9"/>
   <path d="m40 27-4 16 4 17 4-17Z" fill="var(--panel-base)" fillOpacity=".55" stroke="none"/>
   <path d="M29 43h22M40 27v33" strokeOpacity=".65" strokeWidth=".65"/>
  </>}
  {tier>=5&&<path d="m29 16 1-10 10 6 10-6 1 10-11 4Z" fill={`url(#${face})`} stroke={`url(#${metal})`} strokeWidth="1"/>}
  {tier>=8&&<path d="m40 3 3 4-3 5-3-5Z" fill={`url(#${metal})`} strokeWidth=".7"/>}
  {tier===9&&<path d="m26 13-3-6 8 3m23 3 3-6-8 3" strokeWidth="1"/>}
 </svg>;
}
