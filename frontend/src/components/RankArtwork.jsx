// Original TB vector artwork. Shared facets keep portrait frames and emblems
// related without tracing the supplied game's wings, crest or ornamentation.
const PALETTES=[
 ['#5a606e','#c4c9d0','#343b48','#aeb7c4'],
 ['#96604b','#cc9b85','#49352f','#b8795d'],
 ['#8ca5bc','#e4f5ff','#455568','#b8e1fc'],
 ['#d4a641','#fff0af','#675023','#ffe28b'],
 ['#31a98f','#b2fae2','#1e4c4d','#71e7c6'],
 ['#529bd9','#d9f5ff','#283c72','#8edaff'],
 ['#9a61c5','#e9c7ff','#49315e','#d5a0ff'],
 ['#d46461','#ffe1c5','#692e40','#ff9582'],
 ['#c3b183','#faf4df','#62615a','#c9e3e9'],
];
export function safeTier(index){return Number.isFinite(Number(index))?Math.max(0,Math.min(8,Math.floor(Number(index)))):0;}

export function RankDefs({id,tier}) {
 const [metal,light,shade,gem]=PALETTES[safeTier(tier)];
 if(safeTier(tier)===8)return <defs>
  <linearGradient id={`${id}-metal`} x1="18" y1="18" x2="103" y2="106" gradientUnits="userSpaceOnUse"><stop stopColor="#fbf8ec"/><stop offset=".22" stopColor="#d8c89f"/><stop offset=".43" stopColor="#ac9b72"/><stop offset=".51" stopColor="#e8dfc6"/><stop offset=".7" stopColor="#c5b58c"/><stop offset="1" stopColor="#81785e"/></linearGradient>
  <linearGradient id={`${id}-facet`} x1="24" y1="25" x2="91" y2="99" gradientUnits="userSpaceOnUse"><stop stopColor="#fffcf1"/><stop offset=".35" stopColor="#ddd1ae"/><stop offset="1" stopColor="#8c8061"/></linearGradient>
  <linearGradient id={`${id}-edge`} x1="0" y1="0" x2="1" y2="1"><stop stopColor="#fefbf0"/><stop offset=".48" stopColor="#a6a391"/><stop offset="1" stopColor="#4e514d"/></linearGradient>
  <linearGradient id={`${id}-gem`} x1="-.6" y1="0" x2="1" y2="1"><stop stopColor="#f4f8f8"/><stop offset=".42" stopColor="#bed6de"/><stop offset=".75" stopColor="#7693a3"/><stop offset="1" stopColor="#354d5b"/></linearGradient>
  <linearGradient id={`${id}-stone-light`} x1="0" y1="0" x2="1" y2="1"><stop stopColor="#fff"/><stop offset="1" stopColor="#c5d9df"/></linearGradient>
  <linearGradient id={`${id}-gold-local`} x1="0" y1="0" x2=".8" y2="1"><stop stopColor="#f8f2df"/><stop offset=".3" stopColor="#d5c398"/><stop offset=".48" stopColor="#f6ebce"/><stop offset=".64" stopColor="#b8a67b"/><stop offset="1" stopColor="#897d60"/></linearGradient>
  <radialGradient id={`${id}-sheen`} cx=".22" cy=".12" r="1"><stop stopColor="#fffdf2" stopOpacity=".24"/><stop offset=".4" stopColor="#fff" stopOpacity="0"/><stop offset="1" stopColor="#333f42" stopOpacity=".24"/></radialGradient>
  <pattern id={`${id}-satin`} width="1.6" height="1.6" patternUnits="userSpaceOnUse" patternTransform="rotate(-25)"><path d="M0 0H1.6" stroke="#fff" strokeOpacity=".075" strokeWidth=".3"/></pattern>
 </defs>;
 return <defs>
  <linearGradient id={`${id}-metal`} x1="0" y1="0" x2="0" y2="1"><stop stopColor={light}/><stop offset=".2" stopColor={metal}/><stop offset=".48" stopColor={shade}/><stop offset=".7" stopColor={metal}/><stop offset="1" stopColor={light}/></linearGradient>
  <linearGradient id={`${id}-facet`} x1="0" y1="0" x2="0" y2="1"><stop stopColor={light}/><stop offset=".45" stopColor={metal}/><stop offset="1" stopColor={shade}/></linearGradient>
  <linearGradient id={`${id}-gem`} x1="0" y1="0" x2="0" y2="1"><stop stopColor="#f1fbff"/><stop offset=".35" stopColor={gem}/><stop offset="1" stopColor={shade}/></linearGradient>
 </defs>;
}

// A broad, bent blade with a single inset facet, mirrored about x=60.
const BLADES=[
 {d:'M18 58 33 68 49 81 36 81 23 70Z',facet:'M18 58 36 73 49 81 33 75Z'},
 {d:'M13 40 31 54 44 74 29 68 18 56Z',facet:'M13 40 31 59 44 74 26 61Z'},
 {d:'M9 24 26 40 38 64 24 56 14 42Z',facet:'M9 24 26 46 38 64 21 48Z'},
 {d:'M4 51 22 61 37 78 20 72 9 64Z',facet:'M4 51 22 65 37 78 17 68Z'},
];
export function RankWings({id,tier,portrait=false}) {
 if(tier===8){
  const feathers=[
   {d:'M38 88C24 85 13 78 6 65c13 7 24 9 37 9l9 17Z',ridge:'M9 67c13 10 24 14 37 16'},
   {d:'M32 78C20 69 13 59 10 45c10 11 21 18 34 22l5 18Z',ridge:'M12 48c9 13 19 21 31 27'},
   {d:'M27 65C18 54 15 42 16 28c8 13 16 22 28 29l2 22Z',ridge:'M18 32c6 16 14 27 24 35'},
  ];
  return <g className="rank-wings rank-wings-precious" strokeLinejoin="round">
   {[false,true].map(mirror=><g key={String(mirror)} transform={mirror?'translate(120 0) scale(-1 1)':undefined}><g transform={portrait?'translate(-1 3)':undefined}>
    {feathers.map(({d,ridge},i)=><g key={i}><path d={d} fill={`url(#${id}-metal)`} stroke="#655f4f" strokeWidth=".65"/><path d={d} fill={`url(#${id}-sheen)`}/><path d={d} fill={`url(#${id}-satin)`}/><path d={ridge} stroke={`url(#${id}-edge)`} strokeWidth=".7" strokeLinecap="round"/><path d={ridge} transform="translate(0 1.2)" stroke="#77705d" strokeOpacity=".45" strokeWidth=".45"/></g>)}
   </g></g>)}
  </g>;
 }
 const count=[1,1,2,2,2,3,3,3,4][tier];
 const lean=[5,0,-2,-4,2,-5,-8,-10,-12][tier];
 return <g className="rank-wings" strokeLinejoin="round" strokeWidth="1.1">
  {[0,1].map(side=><g key={side} transform={side?'translate(120 0) scale(-1 1)':undefined}>
   <g transform={portrait?'translate(-1 5)':undefined}>
    {BLADES.slice(0,count).map((blade,index)=><g key={index} transform={`rotate(${lean} 38 73)`}>
     <path d={blade.d} fill={`url(#${id}-metal)`} stroke={`url(#${id}-facet)`}/>
     <path d={blade.facet} fill={`url(#${id}-facet)`} stroke="none"/>
    </g>)}
   </g>
  </g>)}
 </g>;
}

export function RankGem({id,tier,x=60,y=62,scale=1}) {
 if(tier===8)return <g transform={`translate(${x} ${y}) scale(${scale})`} strokeLinejoin="round">
  <path d="M0-20 13-4 0 20-13-4Z" fill={`url(#${id}-gold-local)`} stroke="#555e60" strokeWidth="1.1"/>
  <path d="M0-17.8 10.8-3.9 0 17.5-10.8-3.9Z" fill={`url(#${id}-gem)`}/>
  <path d="M0-17.8-3.8-4-10.8-3.9Z" fill="#f8fcfb" fillOpacity=".85"/>
  <path d="M0-17.8 10.8-3.9 3.8-4Z" fill="#d9e7e9"/>
  <path d="M-3.8-4 0 17.5-10.8-3.9Z" fill="#9bb5be" fillOpacity=".65"/>
  <path d="M3.8-4 10.8-3.9 0 17.5Z" fill="#476477" fillOpacity=".6"/>
  <path d="M0-17.8 3.8-4 0 17.5-3.8-4Z" fill={`url(#${id}-stone-light)`} fillOpacity=".55"/>
  <path d="M-10.8-3.9H10.8" stroke="#edf4f3" strokeOpacity=".65" strokeWidth=".45"/>
 </g>;
 return <g transform={`translate(${x} ${y}) scale(${scale})`} strokeLinejoin="round">
  <path d="M0-19 14-3 0 20-14-3Z" fill={`url(#${id}-gem)`} stroke={`url(#${id}-metal)`} strokeWidth="2"/>
  <path d="M0-19-5-3 0 20 5-3Z" fill="#eefaff" fillOpacity=".32"/>
  <path d="M-14-3H14M0-19V20" fill="none" stroke="#f4fbff" strokeOpacity=".45" strokeWidth=".8"/>
  {tier>=6&&<path d="M-7-28 0-34 7-28 0-23Z" fill={`url(#${id}-metal)`} stroke="none"/>}
 </g>;
}

export function KingCrown({id,y=28}){
 return <g transform={`translate(60 ${y})`} strokeLinejoin="round">
  <path d="M-11 0-12-9-5-5 0-13 5-5 12-9 11 0 0 3Z" fill={`url(#${id}-gold-local)`} stroke="#6b6556" strokeWidth=".65"/>
  <path d="M-10-.4 0 1.5 10-.4M0-11v8" fill="none" stroke="#fff9e8" strokeOpacity=".8" strokeWidth=".65"/>
  <path d="m0-8.5 1.7 2.2L0-4.2-1.7-6.3Z" fill="#ecf3f2" stroke="#82999c" strokeWidth=".35"/>
 </g>;
}
