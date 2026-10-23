import './SettingsScene.css';

const svgProps={viewBox:'0 0 180 130','aria-hidden':true,fill:'none',stroke:'currentColor',strokeWidth:2,strokeLinecap:'round',strokeLinejoin:'round'};
const buildings=[
 'M85 40V23h10v17M88 28h4m-4 5h4',
 'M82 40V28l8-9 8 9v12M87 32h6',
 'M84 40V13h12v27M87 18h6m-6 6h6m-6 6h6',
 'M81 40V27h7V17h9v23M91 23h3m-10 9h3',
 'M84 40V25h3V11h6v14h3v15M87 30h6',
 'M81 40V29l9-4 9 4v11M85 33h10',
 'M84 40V19l6-6 6 6v21M87 24h6m-6 6h6',
 'M82 40V22h9v7h7v11M85 27h3m5 7h2',
];

export default function SettingsScene({kind}) {
 if(kind==='dino')return <div className="settings-scene scene-dino-stage" aria-hidden="true"><span className="dino-ground"/><div className="dino-traveler"><svg className="dino-model" viewBox="0 0 120 120" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><g className="dino-body"><path d="M30 83C18 81 12 72 10 62c9 7 16 9 24 8 0-11 6-18 17-23l9-9V27c0-8 5-13 13-13h20c8 0 12 5 12 12v16c0 6-4 10-10 10H82v15c0 10-5 17-15 21l-6 9H46l-2-11c-5 1-9 0-14-3Z" fill="currentColor" fillOpacity=".11"/><path d="M83 41h17M82 61h9v6M45 60l5 3m-8 5 5 3" opacity=".65"/><circle cx="92" cy="27" r="2.7" fill="currentColor" stroke="none"/><path d="M78 20h9" opacity=".3"/><path className="dino-leg dino-leg-back" d="m52 87-4 15h11"/><path className="dino-leg dino-leg-front" d="m68 85 5 17h11"/></g></svg></div></div>;
 if(kind==='cloud')return <div className="settings-scene scene-cloud-stage" aria-hidden="true">{[0,1].map(index=><svg key={index} {...svgProps} className={`cloud-flight cloud-flight-${index}`} viewBox="0 0 110 65"><path d="M10 38C2 17 25 8 39 24c3-28 39-28 43 1 27-13 37 31 7 31H24C13 56 5 49 10 38Z" fill="currentColor" fillOpacity=".1"/><path d="M23 48h13m10 0h35" opacity=".2"/></svg>)}</div>;
 if(kind==='balloon')return <div className="settings-scene scene-balloon-stage" aria-hidden="true"><svg {...svgProps} className="balloon-flight" viewBox="0 0 90 150"><ellipse cx="45" cy="42" rx="26" ry="32" fill="currentColor" fillOpacity=".13"/><path d="m40 77 5-5 5 5Zm5 1c-22 17 23 26 0 45s9 18 0 23M32 24q-9 7-7 20"/><path d="M60 17c10 10 12 25 6 39" opacity=".35"/></svg></div>;
 return <svg {...svgProps} className={`settings-scene scene-${kind}`}>
 {kind==='coffee'&&<><path className="scene-ground" d="M36 109h104"/><path className="coffee-cup" d="M57 65h52v27q0 16-26 16T57 92Z" fill="currentColor" fillOpacity=".12"/><path d="M109 70h10c18 0 16 24-10 24"/>{[0,1,2].map(i=><path key={i} className="coffee-steam" style={{animationDelay:`${i*.9}s`}} d={`M${69+i*13} 53q-9-10 0-19t0-17`}/>)}</>}
 {kind==='bulb'&&<g className="scene-bulb"><circle className="bulb-halo" cx="90" cy="56" r="43" stroke="none" fill="currentColor"/><path className="bulb-glass" d="M73 83C43 55 66 25 90 26s47 31 17 57l-2 14H75Z" fill="currentColor"/><path className="bulb-filament" d="m80 58 10 9 10-9m-10 9v29"/><path d="m76 104h28m-24 7h20"/><g className="bulb-rays"><path d="m90 12 1-7m39 21 5-5m4 40h8M49 23l-5-5m-1 43h-8"/></g></g>}
 {kind==='orbit'&&<g className="scene-orbit"><g transform="rotate(-22 90 70)"><ellipse className="orbit-ring-back" cx="90" cy="70" rx="65" ry="23" opacity=".35"/></g><circle cx="90" cy="70" r="25" fill="var(--panel-base)"/><circle cx="90" cy="70" r="25" fill="currentColor" fillOpacity=".13"/><path className="orbit-planet-lines" d="M72 53c14 0 28 9 39 20M66 71c14 0 28 7 40 16m-31-6 9 6" opacity=".3"/><g transform="rotate(-22 90 70)"><path className="orbit-ring-front" d="M25 70a65 23 0 0 0 130 0"/><ellipse className="orbit-ring-drift" cx="90" cy="70" rx="65" ry="23" strokeDasharray="8 16 2 20" opacity=".7"/><circle className="orbit-satellite" r="3.5" fill="currentColor" stroke="var(--panel-base)" strokeWidth="1.5"/></g></g>}
 {kind==='globe'&&<g className="globe-cycle"><g className="globe-planet"><g className="globe-turn"><circle cx="90" cy="73" r="33" fill="currentColor" fillOpacity=".06"/><path d="M68 49l8 7 6-2 4 12-11 8-5 14m32-44-7 10 10 7-2 12 13 2-4 16M66 95l18 2 8 8" opacity=".7"/>{buildings.map((path,index)=><g key={index} transform={`rotate(${index*45} 90 73)`}><g className="globe-building" style={{'--build-delay':`${index*.8}s`}}><path d={path} fill="var(--panel-base)"/></g></g>)}</g></g><g className="globe-burst"><circle className="globe-shockwave" cx="90" cy="73" r="35"/>{Array.from({length:12},(_,i)=><g key={i} transform={`rotate(${i*30} 90 73)`}><g className="globe-fragment" style={{'--fragment-distance':`${-16-i%3*7}px`,'--fragment-turn':`${i%2?32:-28}deg`}}><path d={i%3===0?'m87 30 6-5 3 7-7 4Z':i%3===1?'m88 28 4-5 4 5-4 3Z':'m90 26 0-10m-3 5 6 0'} fill="currentColor" fillOpacity=".08"/></g></g>)}</g></g>}
 {kind==='stars'&&<g className="scene-stars"><path d="m41 68 30-33 44 48 26-45M71 35l18 66-48-33" opacity=".3"/>{[[41,68],[71,35],[115,83],[141,38],[89,101]].map(([x,y],i)=><g key={i} className="scene-star" style={{animationDelay:`${i*.7}s`}}><path d={`m${x} ${y-5} 2 3 4 2-4 1-2 4-1-4-4-1 4-2Z`} fill="currentColor" fillOpacity=".15"/></g>)}</g>}
 {kind==='compass'&&<g className="scene-compass"><circle cx="90" cy="67" r="38"/><path d="m90 19 0 10m0 76v10m-48-48h10m76 0h10" opacity=".45"/><g className="compass-needle"><path d="m90 36 10 31-10 31-10-31Z" fill="currentColor" fillOpacity=".15"/><path d="m80 67 20 0"/></g><circle cx="90" cy="67" r="3" fill="currentColor"/></g>}
 </svg>;
}
