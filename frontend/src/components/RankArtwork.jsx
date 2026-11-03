// Faceted wing crests. Each tier has a distinct silhouette and matching portrait trim.
const PALETTES=[
 ['#655855','#b5a59a','#191a21','#cab5a4'],
 ['#b47b68','#ffd2b6','#301d22','#ffac84'],
 ['#7a98bb','#e8f6ff','#152638','#acd7ff'],
 ['#bb8b32','#ffe6a0','#302014','#ffd265'],
 ['#178e85','#c8fff1','#071f27','#47efdb'],
 ['#407dd1','#d4f9ff','#131e52','#63dfff'],
 ['#9643c8','#f8cdff','#27113d','#d878ff'],
 ['#cd4c2e','#ffdbad','#27141f','#ff7c42'],
 ['#c89939','#fff0b5','#102439','#66e6ff'],
];
export function safeTier(value){return Number.isFinite(Number(value))?Math.max(0,Math.min(8,Math.floor(Number(value)))):0;}
export function RankDefs({id,tier}){
 const [metal,light,dark,gem]=PALETTES[safeTier(tier)];
 return <defs>
  <linearGradient id={`${id}-metal`} x1="23" y1="20" x2="82" y2="108" gradientUnits="userSpaceOnUse"><stop stopColor={light}/><stop offset=".18" stopColor={metal}/><stop offset=".4" stopColor={dark}/><stop offset=".51" stopColor={light}/><stop offset=".58" stopColor={metal}/><stop offset=".83" stopColor={dark}/><stop offset="1" stopColor={metal}/></linearGradient>
  <linearGradient id={`${id}-facet`} x1="23" y1="27" x2="55" y2="91" gradientUnits="userSpaceOnUse"><stop stopColor={light}/><stop offset=".22" stopColor={metal}/><stop offset=".57" stopColor={dark}/><stop offset="1" stopColor={metal}/></linearGradient>
  <linearGradient id={`${id}-edge`} x1="12" y1="17" x2="61" y2="110" gradientUnits="userSpaceOnUse"><stop stopColor={light}/><stop offset=".28" stopColor={metal}/><stop offset=".55" stopColor={light}/><stop offset=".75" stopColor={dark}/><stop offset="1" stopColor={light}/></linearGradient>
  <linearGradient id={`${id}-inlay`} x1="19" y1="25" x2="61" y2="105" gradientUnits="userSpaceOnUse"><stop stopColor={tier===8?'#d0fcff':gem}/><stop offset=".4" stopColor={tier===8?'#47c9ff':metal}/><stop offset="1" stopColor={dark}/></linearGradient>
  <linearGradient id={`${id}-gem`} x1="0" y1="0" x2=".8" y2="1"><stop stopColor="#f5fcff"/><stop offset=".32" stopColor={gem}/><stop offset="1" stopColor={dark}/></linearGradient>
 </defs>;
}
// Outer wing, inset armor face, ridge, lower blade. Higher tiers split into tall horns.
const WINGS=[
 ['M60 104C51 81 26 76 11 56L7 31c12 19 35 18 43 39l10 34Z','M53 91C43 72 22 68 14 49l10 8c17 8 23 18 29 34Z','M10 35c12 24 32 21 46 59','M53 96c-12-12-22-22-32-15l-1 11c8-7 15-1 21 7Z'],
 ['M60 109C46 89 22 89 13 66L6 54l9 1-3-31c12 17 21 12 26 30 8 9 16 18 22 55Z','M53 96C44 77 26 77 21 55l5 5c11 6 19 17 27 36Z','M15 29c9 25 28 31 41 69','M50 99 25 91 18 78c12 8 19 5 32 21Z'],
 ['M60 109C43 93 23 93 15 75L5 60l10 4L9 28c12 20 24 17 31 39l20 42Z','M54 99C42 79 27 81 21 56l7 7c12 4 18 16 26 36Z','M12 32c10 24 26 29 43 67','M50 103 26 94 18 82c13 7 23 7 32 21Z'],
 ['M60 111C46 98 20 98 14 78L4 63l11 5L10 23c13 19 30 24 32 46l18 42Z','M53 100C41 79 26 84 22 55l8 11c12 2 17 18 23 34Z','M13 29c9 27 24 31 43 72','M48 104C35 96 25 103 19 88c11 5 21 3 29 16Z'],
 ['M60 112C41 98 23 99 17 81L5 67l11 3L11 21c17 18 18 15 22 33l6-28 3 43 18 43Z','M52 99 27 81 22 49l11 16 4-15 4 26Z','M13 26 26 68l30 36','M51 105 24 97 18 83l18 7Z'],
 ['M60 113C44 99 20 99 15 79L3 59l14 11L8 20c22 17 12 26 30 37l4-32 4 52 14 36Z','M53 101 28 83 21 49l13 18 5-10 4 24Z','M11 26 27 72l28 33','M49 105 25 98 17 83l18 8Z'],
 ['M60 113C42 102 24 104 17 87L4 66l13 7L10 37l15 12C20 28 28 19 30 8c12 20 1 37 13 55l17 50Z','M52 100 29 86 22 60l13 13C29 46 39 37 32 22c14 21 1 45 14 64Z','M30 14c8 26-8 40 12 72l14 20','M51 106 26 102 19 88l15 7Z'],
 ['M60 114C45 103 24 106 17 87L3 66l15 9L12 38l16 13C22 29 27 19 27 7c16 15 6 36 17 55l16 52Z','M53 103 27 88 22 60l14 13C29 49 40 37 30 22c15 18 6 47 15 62Z','M27 13c13 25-1 42 17 75l12 20','M50 108 25 102 18 89l17 8Z'],
 ['M60 114 45 104 27 100 16 86 3 61 17 71 7 13 22 34 35 51 41 73 38 43 29 9C46 28 42 51 49 67Z','M54 105 31 88 20 54 13 30 26 46 36 56 42 78Z','M10 19 23 47 37 62 55 106','M51 108 25 102 18 86l17 9Z'],
];
export function RankWings({id,tier,portrait=false}){
 tier=safeTier(tier);const [outer,inset,ridge,lower]=WINGS[tier];
 return <g className="rank-wings" strokeLinejoin="miter" strokeMiterlimit="3">
  {[0,1].map(side=><g key={side} transform={side?'translate(120 0) scale(-1 1)':undefined}><g transform={portrait?'translate(0 0)':undefined}>
   <path d={outer} fill={`url(#${id}-metal)`} stroke={`url(#${id}-edge)`} strokeWidth="1.2"/>
   <path d={inset} fill={`url(#${id}-${tier===8?'inlay':'facet'})`} stroke={PALETTES[tier][2]} strokeWidth=".7"/>
   <path d={lower} fill={`url(#${id}-metal)`} stroke={`url(#${id}-edge)`} strokeWidth=".7"/>
   <path d={ridge} fill="none" stroke={`url(#${id}-edge)`} strokeWidth="1.2"/>
   {tier>=4&&tier<8&&<path d={tier>=6?'M29 21c12 22-3 43 16 65l11 18-16-14C23 68 35 46 29 21Z':'M15 31 26 67 55 104 41 77Z'} fill={`url(#${id}-inlay)`} stroke={`url(#${id}-edge)`} strokeWidth=".55"/>}
   {tier===8&&<path d="M23 51 34 64 41 83 53 105 33 87Z" fill={`url(#${id}-metal)`} stroke="#ffdf86" strokeWidth=".8"/>}
  </g></g>)}
 </g>;
}
export function RankGem({id,tier,x=60,y=64,scale=1}){
 tier=safeTier(tier);
 return <g transform={`translate(${x} ${y}) scale(${scale})`} strokeLinejoin="miter">
  <path d={tier<2?'M-9-23 0-18 9-23 0-6Z':'M-11-21 0-29 11-21 5-9 0-3-5-9Z'} fill={`url(#${id}-gem)`} stroke={PALETTES[tier][0]} strokeWidth="1"/>
  <path d={tier>=6?'M-15-4 0 6 15-4 9 17 0 43-9 17Z':'M-11 0 0 10 11 0 6 18 0 40-6 18Z'} fill={`url(#${id}-gem)`} stroke={`url(#${id}-edge)`} strokeWidth=".8"/>
  <path d="M0 11V39L-5 16Z" fill="#f3fcff" fillOpacity=".55"/>
  {tier>=3&&<path d="m0-24 4 5-4 7-4-7Z" fill={`url(#${id}-gem)`}/>}
 </g>;
}
export function KingCrown({id,y=28}){
 return <path d={`M60 ${y-10} 65 ${y+1} 60 ${y+8} 55 ${y+1}Z`} fill={`url(#${id}-gem)`} stroke={`url(#${id}-edge)`} strokeWidth=".8"/>;
}
