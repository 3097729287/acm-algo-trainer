import {useId} from 'react';

export function RoundedDinosaur() {
 return <div className="settings-scene scene-dino-stage" aria-hidden="true">
  <svg className="dino-landscape" viewBox="0 0 600 260" preserveAspectRatio="none" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
   <path d="M5 245H595"/>
   <path d="M355 245Q388 193 417 138Q428 132 440 140Q452 133 460 138Q486 195 524 245M417 138Q439 151 460 138" fill="currentColor" fillOpacity=".035"/>
   <g className="volcano-vapor">{[0,1,2].map(index=><path key={index} className="volcano-steam" style={{animationDelay:`${index*1.2}s`}} d={`M${426+index*12} 125q-12-13-2-26t-2-24`}/>)}</g>
   {[[58,185,1],[125,202,.72],[550,193,.9]].map(([x,y,scale],index)=><g key={index} transform={`translate(${x} ${y}) scale(${scale})`}><path d="M0 58V26M-19 42C-36 38-32 21-20 18C-24-5 9-10 16 8C36 4 42 31 26 39Q9 49-19 42Z" fill="currentColor" fillOpacity=".03"/></g>)}
  </svg>
  <div className="dino-traveler"><svg className="dino-model" viewBox="0 0 140 128" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
   <g className="dino-body">
    <path d="M38 89Q26 79 38 75Q25 64 40 60Q29 48 46 46Q39 31 56 33Q55 19 69 29" fill="currentColor" fillOpacity=".12"/>
    <path d="M42 62C35 49 39 29 55 25C65 16 85 18 94 30C114 29 126 38 123 49C121 61 103 63 91 59L91 77C103 88 101 104 85 111C66 119 43 111 36 101C22 103 13 97 10 87Q8 82 13 85C29 93 39 83 42 76Z" fill="currentColor" fillOpacity=".10"/>
    <path d="M102 50Q109 55 117 50" opacity=".8"/>
    <circle cx="82" cy="35" r="3.1" fill="currentColor" stroke="none"/>
    <circle cx="113" cy="41" r="1.3" fill="currentColor" stroke="none" opacity=".55"/>
    <path d="M88 73Q104 72 104 80Q102 86 94 82" fill="var(--panel-base)"/>
    <path d="M69 87Q65 99 78 103" opacity=".3"/>
    <path className="dino-leg dino-leg-back" d="M50 108L49 116Q48 121 55 121H65Q70 120 65 116L65 112" fill="var(--panel-base)"/>
    <path className="dino-leg dino-leg-front" d="M77 111L78 117Q78 122 85 122H95Q100 120 94 116L91 109" fill="var(--panel-base)"/>
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
