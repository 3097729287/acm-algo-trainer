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
 ['#d7aa55','#fff2bc','#5b4662','#8fe2fa'],
];
export function safeTier(index){return Number.isFinite(Number(index))?Math.max(0,Math.min(8,Math.floor(Number(index)))):0;}

export function RankDefs({id,tier}) {
 const [metal,light,shade,gem]=PALETTES[safeTier(tier)];
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
 return <g transform={`translate(${x} ${y}) scale(${scale})`} strokeLinejoin="round">
  <path d="M0-19 14-3 0 20-14-3Z" fill={`url(#${id}-gem)`} stroke={`url(#${id}-metal)`} strokeWidth="2"/>
  <path d="M0-19-5-3 0 20 5-3Z" fill="#eefaff" fillOpacity=".32"/>
  <path d="M-14-3H14M0-19V20" fill="none" stroke="#f4fbff" strokeOpacity=".45" strokeWidth=".8"/>
  {tier>=6&&<path d="M-7-28 0-34 7-28 0-23Z" fill={`url(#${id}-metal)`} stroke="none"/>}
 </g>;
}
