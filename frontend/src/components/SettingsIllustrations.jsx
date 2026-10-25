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
  <div className="dino-traveler"><svg className="dino-model" viewBox="0 0 160 160" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
   <g className="dino-body">
    <path className="dino-foot dino-foot-back" d="M91 119v16q0 5 5 5h9q4-1 1-5l-6-4v-14" fill="var(--panel-base)" opacity=".6"/>
    <path d="M43 92q-8-9-11 1l-1 7M58 80q-7-13-12-3l-2 13M78 77q-1-13-10-8l-4 9M88 64q-8-9-12 0l2 12" fill="currentColor" fillOpacity=".16"/>
    <path className="dino-outline" d="M43 92C34 101 23 103 12 97C20 113 33 119 48 113C54 123 65 128 78 128C97 128 110 117 112 101L114 84H128C142 84 150 75 148 63C146 49 133 42 120 42C104 42 91 51 88 64L82 80C70 75 53 78 43 92Z" fill="var(--panel-base)"/>
    <path d="M43 92C34 101 23 103 12 97C20 113 33 119 48 113C54 123 65 128 78 128C97 128 110 117 112 101L114 84H128C142 84 150 75 148 63C146 49 133 42 120 42C104 42 91 51 88 64L82 80C70 75 53 78 43 92Z" fill="currentColor" fillOpacity=".09" stroke="none"/>
    <path className="dino-foot dino-foot-front" d="M67 118v17q0 6 6 6h12q4-1 1-5l-8-4v-10" fill="var(--panel-base)"/>
    <path d="M105 95q-2 9-10 11q-5 1-5-4l3-4"/>
    <circle className="dino-eye" cx="116" cy="59" r="2.9" fill="currentColor" stroke="none"/>
    <circle cx="138" cy="65" r="1.2" fill="currentColor" stroke="none" opacity=".65"/>
    <path d="M126 74q8 5 14-1" strokeWidth="1.8"/>
    <ellipse cx="116" cy="72" rx="4" ry="2.5" fill="currentColor" fillOpacity=".19" stroke="none"/>
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
