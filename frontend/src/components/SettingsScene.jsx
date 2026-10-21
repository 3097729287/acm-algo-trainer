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
 if(kind==='dino')return <div className="settings-scene scene-dino-stage" aria-hidden="true"><span className="dino-ground"/><div className="dino-traveler"><svg className="dino-model" viewBox="0 0 120 120" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><g className="dino-body"><path d="M67 90C49 96 32 87 17 67l1 18c8 15 19 22 37 22h18l10-24 13-11V56h18V29H81l-7 8v24L60 80Z" fill="currentColor" fillOpacity=".14"/><path d="M81 32h30M96 56v7H79m16-17h17M77 66l-8 14m3 10c-8 4-17 4-25-1" opacity=".55"/><path d="m36 92-2-5 7 3m4 8-1-6 7 4m4-3 1-6 5 4" fill="currentColor" fillOpacity=".2"/><path d="m98 47 2 4 3-4 3 4 3-4" opacity=".7"/><circle cx="103" cy="37" r="2.4" fill="currentColor"/><circle cx="110" cy="40" r=".9" fill="currentColor"/><path d="M97 32h9m-19 40h10v7m-2-1 3 3m-1-9 5 4"/><path className="dino-leg dino-leg-back" d="m58 103-4 11h13m-8-3v3m5-3v3"/><path className="dino-leg dino-leg-front" d="m76 99 4 15h12m-5-3v3m-5-3v3"/></g></svg></div></div>;
 if(kind==='cloud')return <div className="settings-scene scene-cloud-stage" aria-hidden="true">{[0,1].map(index=><svg key={index} {...svgProps} className={`cloud-flight cloud-flight-${index}`} viewBox="0 0 110 65"><path d="M10 38C2 17 25 8 39 24c3-28 39-28 43 1 27-13 37 31 7 31H24C13 56 5 49 10 38Z" fill="currentColor" fillOpacity=".1"/><path d="M23 48h13m10 0h35" opacity=".2"/></svg>)}</div>;
 if(kind==='balloon')return <div className="settings-scene scene-balloon-stage" aria-hidden="true"><svg {...svgProps} className="balloon-flight" viewBox="0 0 90 150"><ellipse cx="45" cy="42" rx="26" ry="32" fill="currentColor" fillOpacity=".13"/><path d="m40 77 5-5 5 5Zm5 1c-22 17 23 26 0 45s9 18 0 23M32 24q-9 7-7 20"/><path d="M60 17c10 10 12 25 6 39" opacity=".35"/></svg></div>;
 return <svg {...svgProps} className={`settings-scene scene-${kind}`}>
 {kind==='coffee'&&<><path className="scene-ground" d="M36 109h104"/><path className="coffee-cup" d="M57 65h52v27q0 16-26 16T57 92Z" fill="currentColor" fillOpacity=".12"/><path d="M109 70h10c18 0 16 24-10 24"/>{[0,1,2].map(i=><path key={i} className="coffee-steam" style={{animationDelay:`${i*.9}s`}} d={`M${69+i*13} 53q-9-10 0-19t0-17`}/>)}</>}
 {kind==='bulb'&&<g className="scene-bulb"><circle className="bulb-halo" cx="90" cy="56" r="43" stroke="none" fill="currentColor"/><path className="bulb-glass" d="M73 83C43 55 66 25 90 26s47 31 17 57l-2 14H75Z" fill="currentColor"/><path className="bulb-filament" d="m80 58 10 9 10-9m-10 9v29"/><path d="m76 104h28m-24 7h20"/><g className="bulb-rays"><path d="m90 12 1-7m39 21 5-5m4 40h8M49 23l-5-5m-1 43h-8"/></g></g>}
 {kind==='orbit'&&<g className="scene-orbit"><ellipse cx="90" cy="70" rx="65" ry="24"/><ellipse cx="90" cy="70" rx="65" ry="24" transform="rotate(60 90 70)" opacity=".4"/><circle cx="90" cy="70" r="17" fill="currentColor" fillOpacity=".1"/><circle cx="31" cy="60" r="5" fill="currentColor"/></g>}
 {kind==='globe'&&<g className="globe-cycle"><g className="globe-planet"><g className="globe-turn"><circle cx="90" cy="73" r="33" fill="currentColor" fillOpacity=".06"/><path d="M68 49l8 7 6-2 4 12-11 8-5 14m32-44-7 10 10 7-2 12 13 2-4 16M66 95l18 2 8 8" opacity=".7"/>{buildings.map((path,index)=><g key={index} transform={`rotate(${index*45} 90 73)`}><g className="globe-building" style={{'--build-delay':`${index*.8}s`}}><path d={path} fill="var(--panel-base)"/></g></g>)}</g></g><g className="globe-burst"><circle className="globe-shockwave" cx="90" cy="73" r="35"/>{Array.from({length:12},(_,i)=><g key={i} transform={`rotate(${i*30} 90 73)`}><g className="globe-fragment" style={{'--fragment-distance':`${-16-i%3*7}px`,'--fragment-turn':`${i%2?32:-28}deg`}}><path d={i%3===0?'m87 30 6-5 3 7-7 4Z':i%3===1?'m88 28 4-5 4 5-4 3Z':'m90 26 0-10m-3 5 6 0'} fill="currentColor" fillOpacity=".08"/></g></g>)}</g></g>}
 {kind==='stars'&&<g className="scene-stars"><path d="m41 68 30-33 44 48 26-45M71 35l18 66-48-33" opacity=".3"/>{[[41,68],[71,35],[115,83],[141,38],[89,101]].map(([x,y],i)=><g key={i} className="scene-star" style={{animationDelay:`${i*.7}s`}}><path d={`m${x} ${y-5} 2 3 4 2-4 1-2 4-1-4-4-1 4-2Z`} fill="currentColor" fillOpacity=".15"/></g>)}</g>}
 {kind==='compass'&&<g className="scene-compass"><circle cx="90" cy="67" r="38"/><path d="m90 19 0 10m0 76v10m-48-48h10m76 0h10" opacity=".45"/><g className="compass-needle"><path d="m90 36 10 31-10 31-10-31Z" fill="currentColor" fillOpacity=".15"/><path d="m80 67 20 0"/></g><circle cx="90" cy="67" r="3" fill="currentColor"/></g>}
 </svg>;
}
