import {useId} from 'react';
import {rankIndex,TIER_NAMES} from '@/lib/rankTiers.js';

const metals=[
 ['#c8bbad','#75645c','#322d33','#bcb1a0'],
 ['#edc7a7','#a87358','#432e2e','#d2a384'],
 ['#e3edff','#8397c2','#30394e','#b5d4ff'],
 ['#ffe7ad','#bb8b3c','#4f3820','#ffcf71'],
 ['#b1ffec','#26ad96','#123d3e','#46ead0'],
 ['#e3e5ff','#678ce9','#222851','#66d6ff'],
 ['#f1caff','#a255d3','#3b1c54','#dc80ff'],
 ['#ffb9a6','#c7444c','#481b29','#ff7758'],
 ['#fff0b7','#bd9754','#35324c','#6be1ff'],
];

// The frame is ornamental: rank identity continues to come from the same
// authoritative tier mapping used by the portrait and the badge.
export default function DuelBannerFrame({rank}){
 const tier=rankIndex(rank),id='banner-'+useId().replace(/:/g,''),[light,metal,dark,gem]=metals[tier],high=tier>=4;
 return <svg className={'duel-banner-frame banner-tier-'+tier} viewBox="0 0 320 520" aria-hidden="true" data-tier={tier} data-tier-name={TIER_NAMES[tier]} fill="none" preserveAspectRatio="none">
  <defs>
   <linearGradient id={id+'-edge'} x1="20" y1="0" x2="286" y2="510" gradientUnits="userSpaceOnUse"><stop stopColor={light}/><stop offset=".19" stopColor={dark}/><stop offset=".46" stopColor={metal}/><stop offset=".68" stopColor={dark}/><stop offset="1" stopColor={light}/></linearGradient>
   <linearGradient id={id+'-crest'} x1="160" y1="7" x2="160" y2="43" gradientUnits="userSpaceOnUse"><stop stopColor={light}/><stop offset=".26" stopColor={metal}/><stop offset=".57" stopColor={dark}/><stop offset=".8" stopColor={light}/><stop offset="1" stopColor={metal}/></linearGradient>
   <linearGradient id={id+'-gem'} x1="153" y1="5" x2="168" y2="33" gradientUnits="userSpaceOnUse"><stop stopColor="white"/><stop offset=".36" stopColor={gem}/><stop offset="1" stopColor={dark}/></linearGradient>
   <radialGradient id={id+'-cloth'} cx=".5" cy=".28" r=".85"><stop stopColor="#202c3a"/><stop offset="1" stopColor="#111820"/></radialGradient>
  </defs>
  <path d="M22 15H298Q307 15 307 26V497Q307 506 298 506H22Q13 506 13 497V26Q13 15 22 15Z" fill={'url(#'+id+'-cloth)'} stroke={'url(#'+id+'-edge)'} strokeWidth="3"/>
  <path d="M24 20H296Q301 20 301 27V494Q301 500 295 500H25Q19 500 19 494V27Q19 20 24 20Z" stroke={metal} strokeOpacity=".32" strokeWidth=".8"/>
  <path d="M14 52V26Q14 15 25 15H82M238 15H295Q306 15 306 26V52" stroke={light} strokeOpacity=".5" strokeWidth="1"/>
  {tier>=2&&<g fill={'url(#'+id+'-crest)'} stroke={light} strokeOpacity=".3" strokeWidth=".7">
   <path d={high?'M14 15 53 20 37 27 17 53 22 29Z':'M14 15 40 18 23 25 17 43Z'}/>
   <path d={high?'M306 15 267 20 283 27 303 53 298 29Z':'M306 15 280 18 297 25 303 43Z'}/>
   <path d={high?'M14 506 59 500 34 490 18 468 22 492Z':'M14 506 44 501 24 495 17 479Z'}/>
   <path d={high?'M306 506 261 500 286 490 302 468 298 492Z':'M306 506 276 501 296 495 303 479Z'}/>
  </g>}
  <g fill={'url(#'+id+'-crest)'} stroke={light} strokeOpacity=".4" strokeWidth=".6">
   <path d={tier<2?'M79 15 129 14 145 21 160 13 175 21 191 14 241 15 202 22 177 25 160 37 143 25 118 22Z':high?'M57 14 114 17 98 7 137 16 145 10 160 23 175 10 183 16 222 7 206 17 263 14 226 24 189 28 176 35 160 43 144 35 131 28 94 24Z':'M70 14 122 16 111 8 144 17 160 8 176 17 209 8 198 16 250 14 211 24 179 27 160 39 141 27 109 24Z'}/>
   <path d="M114 16 142 23 160 36 178 23 206 16 177 20 160 27 143 20Z" fill={dark}/>
  </g>
  <path d={tier===8?'M160 4 166 16 176 20 166 24 160 38 154 24 144 20 154 16Z':'M160 10 169 20 160 31 151 20Z'} fill={'url(#'+id+'-gem)'} stroke={light} strokeWidth=".9"/>
  {high&&<path d="M31 24 110 20M210 20 289 24" stroke={gem} strokeOpacity=".55" strokeWidth="1.2"/>}
 </svg>;
}
