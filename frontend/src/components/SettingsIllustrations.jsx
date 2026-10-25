import {useId} from 'react';

function AncientTree({x,y,scale=1}) {
 return <g transform={`translate(${x} ${y}) scale(${scale})`}>
  <path d="M-6 91Q-2 57-8 31L6 28Q3 61 10 91M-2 64L-24 44M5 53L25 32" fill="currentColor" fillOpacity=".07"/>
  <path d="M-33 51C-51 49-49 29-35 23C-41 10-28-3-14 1C-10-16 13-17 20-2C37-8 51 7 44 20C60 28 54 49 39 50C27 65 9 62 1 57C-11 68-30 64-33 51Z" fill="currentColor" fillOpacity=".075"/>
  <path d="M-33 31Q-20 20-9 32M-13 11Q-2 3 11 12M15 39Q31 27 41 34M-20 49Q-10 43-2 48M-6 89L-16 93M8 89L18 93" opacity=".55"/>
 </g>;
}

export function RoundedDinosaur() {
 return <div className="settings-scene scene-dino-stage" aria-hidden="true">
  <svg className="dino-landscape" viewBox="0 0 640 310" preserveAspectRatio="xMidYMax meet" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
   <g opacity=".22"><path d="M145 289Q184 231 214 209Q239 236 268 285M465 284Q509 224 538 209Q571 246 602 289"/><path d="M184 250L214 209L229 246M509 248L538 209L555 245"/></g>
   <g className="scene-volcano">
    <path d="M290 287C332 260 343 212 368 177L395 133C406 124 440 125 451 135L478 183C500 220 515 263 548 287Z" fill="currentColor" fillOpacity=".065"/>
    <ellipse cx="423" cy="135" rx="28" ry="9" fill="currentColor" fillOpacity=".09"/>
    <path d="M395 136Q403 154 408 171L420 159L432 186Q441 163 451 138" fill="currentColor" fillOpacity=".12"/>
    <path d="M408 171L392 205L398 216L367 263M432 186L422 216L434 245L426 275M451 164L467 214L482 228L495 271M369 202L356 235L339 252M396 145L380 182M456 218L462 246M382 233L375 247" opacity=".65"/>
    <path d="M317 282L329 268L342 274L347 287M493 287L507 277L520 281M398 285L410 279L420 286" opacity=".7"/>
    <g className="volcano-vapor">{[0,1,2].map(index=><path key={index} className="volcano-steam" style={{animationDelay:`${index*1.25}s`}} d={`M${410+index*13} 120c-15-20 12-28 2-43s-17-21-4-36`}/>)}</g>
   </g>
   <AncientTree x={66} y={195} scale={1}/><AncientTree x={146} y={224} scale={.7}/><AncientTree x={580} y={205} scale={.9}/>
   <path d="M8 289H632" opacity=".65"/>
   <g opacity=".6"><path d="M26 288Q21 275 15 272M26 288Q27 274 35 271M24 282L16 279M29 280L35 277M204 289Q201 277 194 274M204 289Q207 275 213 273M556 290Q549 278 542 278M556 290Q558 280 566 275"/><path d="M91 289q4-8 10-7q7 0 11 7M241 289q8-12 17-1M469 288q6-9 12 0"/></g>
  </svg>
  <div className="dino-traveler"><svg className="dino-model" viewBox="0 0 164 140" fill="none" stroke="currentColor" strokeWidth="2.25" strokeLinecap="round" strokeLinejoin="round">
   <ellipse cx="82" cy="133" rx="47" ry="3" fill="currentColor" fillOpacity=".07" stroke="none"/>
   <g className="dino-body">
    <path className="dino-leg dino-leg-back" d="M72 107Q68 116 72 128Q76 132 91 129Q94 125 86 123L86 111" fill="var(--panel-base)" opacity=".65"/>
    <path d="M40 89Q29 80 25 86Q21 91 36 98M48 72Q34 62 32 70Q30 77 43 80M63 55Q51 42 47 50Q42 57 55 62M79 36Q71 21 65 30L65 44" fill="currentColor" fillOpacity=".18"/>
    <path d="M53 74C54 57 63 51 69 40C70 22 87 15 103 19C119 20 122 30 124 34C144 31 154 40 151 52C148 66 129 66 117 63L112 79C123 89 124 103 113 113C97 128 64 124 49 112C32 115 17 108 10 98Q7 93 12 95C30 101 46 99 53 74Z" fill="var(--panel-base)"/>
    <path d="M53 74C54 57 63 51 69 40C70 22 87 15 103 19C119 20 122 30 124 34C144 31 154 40 151 52C148 66 129 66 117 63L112 79C123 89 124 103 113 113C97 128 64 124 49 112C32 115 17 108 10 98Q7 93 12 95C30 101 46 99 53 74Z" fill="currentColor" fillOpacity=".13"/>
    <path d="M105 78C91 82 83 94 88 107Q91 114 104 115" fill="currentColor" fillOpacity=".06" strokeOpacity=".35"/>
    <path d="M120 53Q132 59 143 52"/>
    <ellipse className="dino-eye" cx="105" cy="37" rx="3.5" ry="4.5" fill="currentColor" stroke="none"/>
    <circle cx="106" cy="35.5" r="1.1" fill="var(--panel-base)" stroke="none"/>
    <circle cx="142" cy="44" r="1.6" fill="currentColor" stroke="none" opacity=".7"/>
    <ellipse cx="115" cy="50" rx="4.5" ry="2.5" fill="currentColor" fillOpacity=".18" stroke="none"/>
    <path d="M111 77Q126 77 125 85Q123 91 116 86M122 85L119 82" fill="var(--panel-base)"/>
    <path className="dino-leg dino-leg-front" d="M87 108Q80 117 83 129Q87 133 102 131Q107 127 97 124L100 113M89 127V130M94 128V131" fill="var(--panel-base)"/>
    <g fill="currentColor" fillOpacity=".2" stroke="none"><ellipse cx="65" cy="76" rx="3" ry="4"/><ellipse cx="60" cy="88" rx="2.6" ry="3.6"/><ellipse cx="56" cy="99" rx="2" ry="2.8"/></g>
   </g>
  </svg></div>
 </div>;
}

export function SpinningPlanet() {
 const clip=useId();
 return <g className="orbit-system">
  <defs><clipPath id={clip}><circle cx="90" cy="70" r="24"/></clipPath></defs>
  <g transform="rotate(-22 90 70)"><ellipse className="orbit-ring-back" cx="90" cy="70" rx="65" ry="23" opacity=".35"/></g>
  <circle cx="90" cy="70" r="25" fill="var(--panel-base)"/>
  <circle cx="90" cy="70" r="25" fill="currentColor" fillOpacity=".09"/>
  <g clipPath={`url(#${clip})`}><g className="orbit-planet-surface" opacity=".55">
   {[0,50,100].map(offset=><g key={offset} transform={`translate(${offset} 0)`}><path d="M46 48Q63 39 68 52L62 59Q79 60 78 70L67 78Q68 92 58 98L48 88Q55 78 48 70L42 60Z" fill="currentColor" fillOpacity=".15"/><path d="M49 43Q68 70 49 97M74 43Q93 70 74 97" opacity=".3"/></g>)}
  </g></g>
  <g transform="rotate(-22 90 70)"><path className="orbit-ring-front" d="M25 70a65 23 0 0 0 130 0"/><ellipse className="orbit-ring-drift" cx="90" cy="70" rx="65" ry="23" strokeDasharray="8 16 2 20" opacity=".7"/><circle className="orbit-satellite" r="3.5" fill="currentColor" stroke="var(--panel-base)" strokeWidth="1.5"/></g>
 </g>;
}
