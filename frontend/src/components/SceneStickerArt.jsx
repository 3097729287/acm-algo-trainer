import {memo} from 'react';

const ink='#494454',cream='#fff3d9',mint='#9bd9bd',wood='#c28d65';
const colours={mint:'#96d4be',cream:'#ffe6b7',rose:'#f3acc1',blue:'#9ebfe6',striped:'#cee8e1',navy:'#687b9c',brown:'#a18170',white:'#fff8e7',red:'#d88b89'};
export function PersonArt({appearance={},friend=false}){
 const a={hat:'none',accessory:'none',top:friend?'rose':'mint',trousers:'navy',shoes:'brown',...appearance};
 return <g data-person-outfit={JSON.stringify(a)}>
  <path d="M38 66 33 86 44 87 51 69 58 87 69 85 63 65" fill={colours[a.trousers]||'#8d9cbd'}/>
  {a.trousers==='skirt'&&<path d="m39 64-9 19h42l-9-19" fill="#bfa4d8"/>}
  {a.trousers==='shorts'&&<path d="m39 64-3 14 12 2 4-9 4 9 12-2-4-14" fill="#d1ab78"/>}
  <path d="M32 84q-7 0-8 8h22l-1-6M58 86l-1 6h22q-1-8-11-8" fill={a.shoes==='boots'?'#ad8063':colours[a.shoes]}/>
  <path d="m34 43-12 17 8 6 8-11v15h27V55l8 11 8-6-13-17-13-5h-9Z" fill={colours[a.top]}/>
  {a.top==='striped'&&<path d="M39 52h25M39 59h25" stroke="#80b7a8" strokeWidth="4"/>}
  <circle cx="51" cy="27" r="17" fill="#f8d6b5"/>
  <path d={friend?'M33 27q-6-24 18-23 24 0 18 25l-5-13-13 2-9-6-4 17':'M33 25Q30 5 48 6q24-6 21 23l-8-14-8 6-13-6Z'} fill={friend?'#a77861':'#675660'}/>
  <path d="M44 29v1m14-1v1m-11 7q4 3 8-1" fill="none" strokeWidth="2" strokeLinecap="round"/>
  {a.accessory==='scarf'&&<path d="M38 42q14 6 28 0l-3 8-11-1-2 13-8-2 3-13" fill="#edb580"/>}
  {a.accessory==='bow'&&<path d="m47 45-10-6v13l10-6h7l10 6V39l-10 6" fill="#e8a2bb"/>}
  {a.accessory==='glasses'&&<g fill="#d9eff250"><circle cx="43" cy="29" r="7"/><circle cx="59" cy="29" r="7"/><path d="M50 28h2"/></g>}
  {a.accessory==='bag'&&<g><path d="m64 46-24 24" fill="none"/><rect x="28" y="58" width="17" height="16" rx="4" fill="#d9ad78"/></g>}
  {a.hat==='cap'&&<path d="M33 17q1-18 19-16 15 1 17 16H29m25-1h22q4 7-6 6H53" fill="#9bbad7"/>}
  {a.hat==='sunhat'&&<path d="m37 15 3-13h23l4 13q22 8-14 9-38-1-16-9Z" fill="#eed594"/>}
  {a.hat==='beanie'&&<g fill="#d9b0cd"><path d="M33 16q-1-16 19-16 19 0 18 16Z"/><rect x="32" y="12" width="39" height="8" rx="3"/></g>}
  {a.hat==='crown'&&<path d="m35 16-3-15 12 7 9-11 8 11 12-7-5 15Z" fill="#f7d27c"/>}
 </g>;
}
export const SCENE_SHAPES=new Set(['tree','pine','flower','grass','rock','mushroom','house','cottage','tower','person','person-friend','chair','stool','table','sofa','bed','lamp','bookshelf','window','boat','bird','fish','mountain','bridge']);
function Drawing({shape,appearance}){
 switch(shape){
 case 'tree':return <><path d="M45 93V50h12v43" fill={wood}/><path d="M26 65Q6 60 15 43q-8-22 16-25Q43-2 61 14q28-5 27 20 19 25-7 32-13 16-29 4-15 13-26-5Z" fill={mint}/><path d="m51 57-15-9m15 15 19-17" fill="none" stroke="#71ac8d"/></>;
 case 'pine':return <><path d="M44 95V66h12v29" fill={wood}/><path d="m50 4-26 32h12L14 63h15L8 85h84L71 63h15L64 36h12Z" fill="#94cbb1"/><path d="M39 38h23M32 66h36" stroke="#76ae94"/></>;
 case 'flower':return <><path d="M50 92V43" fill="none" stroke="#7aaf8c" strokeWidth="6"/><path d="M48 73Q21 47 23 69q3 16 25 12m5-4q27-27 24-5-3 13-23 13" fill={mint}/><g fill="#f2c0cc">{[0,60,120,180,240,300].map(angle=><ellipse key={angle} cx="50" cy="15" rx="10" ry="14" transform={`rotate(${angle} 50 34)`}/>)}</g><circle cx="50" cy="34" r="12" fill="#f9d780"/></>;
 case 'grass':return <path d="M7 87Q14 41 30 60l4 17Q32 22 51 40l3 34q10-45 25-28l-7 35 21-9-5 15Z" fill="#a9d5a0"/>;
 case 'rock':return <><path d="m8 77 15-29 28-16 27 16 15 30-13 10H24Z" fill="#b5c2cb"/><path d="m24 74 16-27 22 12 15 20" fill="none" stroke="#94a5b0"/></>;
 case 'mushroom':return <><path d="m40 54-5 34q15 15 31-1l-7-35" fill={cream}/><path d="M8 56Q15 9 51 9q38 1 43 46-44 20-86 1Z" fill="#e9a9a5"/><g fill="#fff1db" stroke="none"><circle cx="32" cy="37" r="7"/><circle cx="60" cy="24" r="6"/><circle cx="75" cy="45" r="6"/></g></>;
 case 'house':case 'cottage':return <><rect x="20" y="39" width="62" height="53" rx="3" fill={shape==='cottage'?'#dcb490':cream}/><path d="M10 43 50 8l42 35Z" fill={shape==='cottage'?'#a4c3ad':'#dba2a1'}/><path d="M68 22V11h11v21" fill="#d5aa8d"/><rect x="43" y="65" width="17" height="27" rx="4" fill="#b28f7a"/><rect x="27" y="52" width="13" height="14" rx="2" fill="#b4dce2"/><rect x="65" y="52" width="11" height="14" rx="2" fill="#b4dce2"/><circle cx="55" cy="80" r="1" fill={ink}/></>;
 case 'tower':return <><path d="M29 91V38h43v53Z" fill="#ded3e9"/><path d="M19 40 50 3l33 37Z" fill="#acb8df"/><rect x="43" y="70" width="16" height="22" rx="7" fill="#b79fca"/><rect x="44" y="45" width="14" height="16" rx="7" fill="#f8dfaa"/><path d="M24 92h54"/></>;
 case 'person':case 'person-friend':return <PersonArt appearance={appearance} friend={shape==='person-friend'}/>;
 case 'chair':return <><path d="M23 88V17q25-10 51 0v71M23 55h51M30 74v18m36-18v18" fill="none" stroke={wood} strokeWidth="10"/><path d="M18 61h61v13H18Z" fill="#d9ae7e"/><path d="M33 24v24m14-24v24m15-24v24" stroke="#dcb48b" strokeWidth="6"/></>;
 case 'stool':return <><path d="m32 52-8 41m42-41 10 41" stroke={wood} strokeWidth="10"/><ellipse cx="50" cy="46" rx="38" ry="14" fill="#dfb78b"/></>;
 case 'table':return <><path d="m29 43-7 49m46-49 9 49M50 45v48" fill="none" stroke={wood} strokeWidth="9"/><ellipse cx="50" cy="35" rx="44" ry="18" fill="#e1ba8c"/></>;
 case 'sofa':return <><path d="M19 82v9m63-9v9" stroke={wood} strokeWidth="7"/><rect x="13" y="27" width="75" height="50" rx="13" fill="#b8b1d8"/><rect x="6" y="47" width="88" height="36" rx="10" fill="#d0c5e5"/><path d="M20 60h60M49 34v24M18 49v21m64-21v21" stroke="#a69ac2" fill="none"/></>;
 case 'bed':return <><path d="M11 26v64m78-27v27M12 77h77" stroke={wood} strokeWidth="8"/><path d="M15 45h57q18 0 17 26H15Z" fill="#a9c9dc"/><rect x="17" y="38" width="24" height="14" rx="6" fill={cream}/><path d="M46 47v23" stroke="#8caec5"/></>;
 case 'lamp':return <><path d="M50 41v47m-20 3h40" stroke={wood} strokeWidth="6"/><path d="m24 10-9 36h70l-10-36Z" fill="#f1dbab"/><path d="M33 14 28 42m39-28 5 28" stroke="#dfc38b"/></>;
 case 'bookshelf':return <><rect x="13" y="8" width="75" height="83" rx="3" fill="#e0b98f"/><g fill="none"><path d="M18 35h65M18 64h65" stroke={wood} strokeWidth="5"/></g><path d="M23 16h10v18H23Zm14 2h8v16h-8Zm15-3 9-2 5 20-10 1ZM24 43h12v19H24Zm17 0h9v19h-9Zm18 4h15v15H59ZM26 74h48v8H26Z" fill="#abcbbd"/><path d="M39 74h35v8H39Z" fill="#d7a8be"/></>;
 case 'window':return <><rect x="11" y="9" width="78" height="78" rx="5" fill="#dfbc97"/><rect x="18" y="16" width="64" height="64" rx="2" fill="#b8dbe8"/><circle cx="65" cy="32" r="11" fill="#fff0af" stroke="none"/><path d="M20 65q13-19 29-1 18-13 31-2v16H20Z" fill="#b3d6b8"/><path d="M50 15v64M17 48h66" stroke="#e6c7a4" strokeWidth="5"/><path d="M6 88h88" stroke={wood} strokeWidth="6"/></>;
 case 'boat':return <><path d="M50 73V9"/><path d="M46 13 17 62h29Z" fill={cream}/><path d="M55 21 84 63H55Z" fill="#b6cde4"/><path d="m8 72 18 19h50l17-19Z" fill="#d6ab84"/><path d="M13 95q17-7 34 0 20-7 39 0" stroke="#93c5d2" fill="none"/></>;
 case 'bird':return <><path d="M18 58Q5 27 39 35q20-29 40-7 17 31-10 47-36 19-51-17Z" fill="#b3cee5"/><path d="m77 40 19 9-19 7" fill="#edcc8d"/><path d="M27 54q15-5 21 13" fill="none"/><circle cx="68" cy="39" r="2.4" fill={ink}/><path d="M16 50 4 45l5 20 16-1" fill="#a1bdd8"/></>;
 case 'fish':return <><path d="M24 51 7 28v45l17-17q35 37 69-5-34-42-69 0Z" fill="#efb997"/><path d="M48 37q-4 14 0 28" stroke="#dc9c80" fill="none"/><circle cx="75" cy="48" r="3" fill={ink}/></>;
 case 'mountain':return <><path d="M3 87 39 17l17 30 13-15 29 55Z" fill="#aabdc9"/><path d="m39 17-13 25 12-6 8 9 8-4Z" fill={cream}/><path d="m69 32-9 15 10-4 7 6Z" fill="#eaf1ed"/></>;
 case 'bridge':return <><path d="M6 81V50q43-39 88 0v31h-9V57q-35-25-70 0v24Z" fill="#d2bca5"/><path d="M5 43q44-40 90 0M17 33v20m16-28v18m16-22v18m17-14v18m16-10v19" stroke={wood} fill="none" strokeWidth="4"/></>;
 default:return null;
 }
}
export const SceneStickerArt=memo(function SceneStickerArt({item,size=64,appearance}){
 return <svg className="sticker-art scene-sticker-art" data-shape={item.shape} data-sticker-style="cartoon-paper-v1" viewBox="-6 -8 112 112" width={size} height={size} aria-hidden="true"><g stroke={ink} strokeWidth="2.2" strokeLinejoin="round" strokeLinecap="round"><Drawing shape={item.shape} appearance={appearance}/></g></svg>;
});

export {default as BackgroundArt} from './BackgroundArt.jsx';
export function WeatherArt({type='rain'}){
 return <svg className="sticker-art weather-sticker" data-weather={type} viewBox="0 0 100 112" width="100%" height="100%" aria-hidden="true"><g stroke="#494454" strokeWidth="2.2" strokeLinejoin="round"><path d="M14 62q-20-14-4-29 5-7 15-7 3-26 29-17 13 4 15 18 25-5 27 17 5 24-24 25H27Z" fill={type==='thunder'?'#a8a8c2':'#b1c3d4'}/><path d="M39 47v2m22-2v2m-17 9q6 3 12-1" fill="none" strokeLinecap="round"/>{type==='thunder'&&<path d="m54 64-16 27h13l-6 19 29-32H60l10-14Z" fill="#f6d788"/>}{type!=='thunder'&&<g className="weather-rain" stroke="#97cde1" strokeWidth="4" strokeLinecap="round"><path d="m25 80-4 10m28-10-4 10m28-10-4 10"/></g>}{type==='rainbow'&&<g fill="none" strokeWidth="4"><path d="M11 38Q26 0 66 17" stroke="#edb7b9"/><path d="M16 41Q30 6 65 22" stroke="#f2d795"/><path d="M21 43Q34 13 64 27" stroke="#bad8b3"/></g>}</g></svg>;
}
