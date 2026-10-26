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
  <div className="dino-traveler"><svg className="dino-model" viewBox="0 0 370 330" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
   <g className="dino-body">
    <path className="dino-spines" d="m33 205 10-15 11 22m4 2 11-15 10 21m9 2 12-16 11 20m7 1 12-17 12 19m7-1 13-19 12 16m5-4 10-22 13 12m1-8-17-14 22-7m1-5-18-15 21-6m1-4-16-17 20-3m1-5-17-16 22-4m2-4-16-17 24-3m4-5-14-17 26-5m6-3-10-20 25 6" fill="currentColor" fillOpacity=".09"/>
    <path className="dino-outline" d="M17 199C52 219 122 234 167 222C199 214 204 179 207 137C210 99 216 65 239 42C266 15 309 29 347 58L273 79C295 88 321 97 336 108C338 119 305 119 286 119L289 222C289 252 279 271 253 281C220 294 185 283 155 275C92 259 40 243 17 199Z" fill="var(--panel-base)"/>
    <path className="dino-arm" d="M288 150q17 1 23-11m-10 9 12 4m-11-4 10-6M274 172q22 5 36-2m-8 1 11-8m-11 9 11 7" strokeWidth="7"/>
    <path className="dino-foot dino-foot-back" d="M244 279l-4 25m0-9-10 17m11-10 10 11m-11-10 0 11" strokeWidth="7"/>
    <path className="dino-foot dino-foot-front" d="M192 275l-9 27m3-9-18 13m17-7 1 13m0-13 15 6" strokeWidth="7"/>
    <g className="dino-eyes"><circle cx="253" cy="53" r="12" fill="var(--panel-raised-base)"/><circle cx="283" cy="47" r="11" fill="var(--panel-raised-base)"/><circle cx="254" cy="54" r="5.5" fill="var(--text)" stroke="none"/><circle cx="284" cy="48" r="5" fill="var(--text)" stroke="none"/><circle cx="256" cy="52" r="1.7" fill="var(--panel-raised-base)" stroke="none"/><circle cx="286" cy="46" r="1.5" fill="var(--panel-raised-base)" stroke="none"/></g>
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
