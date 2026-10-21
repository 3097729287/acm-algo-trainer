import { useId } from 'react';
const COLORS=['#929ba8','#c88e62','#cdd8e8','#f2c564','#8bdad5','#60d19c','#7fbfff','#bd93f7','#f197ae','#ffc367'];
function star(cx,cy,radius=10,inner=4.5){return Array.from({length:10},(_,index)=>{const angle=-Math.PI/2+index*Math.PI/5,r=index%2?inner:radius;return `${cx+Math.cos(angle)*r},${cy+Math.sin(angle)*r}`;}).join(' ');}
export function titleMedalIndex(title){const targets=title?.category==='streak'?[30,90,180,365,730]:[500,750,1000,1500,2000];return Math.max(0,targets.indexOf(Number(title?.target)))*2+1;}
export default function MedalEmblem({ index=0, size=30, variant='rank', label }){
  const id=useId().replaceAll(':',''),tier=Math.max(0,Math.min(9,index)),color=COLORS[tier],streak=variant==='streak',title=variant!=='rank';
  return <svg className={`medal-emblem tier-${tier} medal-${variant}`} width={size} height={Math.round(size*1.15)} viewBox="0 0 64 74" role={label?'img':undefined} aria-label={label} aria-hidden={label?undefined:true}>
    <defs><linearGradient id={`medal-${id}`} x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#fff7db"/><stop offset=".33" stopColor={color}/><stop offset="1" stopColor={color} stopOpacity=".6"/></linearGradient></defs>
    <path d="m16 43-5 28 13-7 8 8 7-29M33 45l8 27 8-9 12 5-9-28" fill={color} opacity=".65"/>
    {tier>=4&&<path d="M16 20 2 13l4 13-5 4 14 13M48 20l14-7-4 13 5 4-14 13" fill={color} opacity=".75"/>}
    <path d={title?'M32 6 41 10l10 1 1 10 6 9-6 9-1 10-10 1-9 6-9-6-10-1-1-10-6-9 6-9 1-10 10-1Z':'M32 5 54 13v21c0 15-22 26-22 26S10 49 10 34V13Z'} fill={`url(#medal-${id})`} stroke={color} strokeWidth="2"/>
    <path d={title?'M32 13a19 19 0 1 1 0 38 19 19 0 1 1 0-38':'M32 13 47 19v15c0 10-15 18-15 18s-15-8-15-18V19Z'} fill="var(--panel-base,#18202b)" opacity=".85"/>
    <path className="medal-highlight" d="M12 15 32 7l18 7-18 5Z"/>
    {streak?<path d="M33 19c5 10-5 12-2 18 3-1 5-5 5-7 12 13 3 22-5 21-14-1-13-12-7-20 2 4 3 5 4 6-1-7 5-10 5-18Z" fill={color}/>:<polygon points={star(32,32,tier>=7?13:11,tier>=7?6:5)} fill={color}/>}
    {tier>=2&&<g fill={color}>{Array.from({length:Math.min(5,1+Math.floor(tier/2))},(_,i)=><circle key={i} cx={24+i*4} cy="53" r="1.4"/>)}</g>}
    {tier>=7&&<path d="m21 17 3-8 8 5 8-5 3 8Z" fill={color} stroke="var(--panel-base,#18202b)" strokeWidth="1"/>}
    {tier>=8&&<path d="m8 40 3 6 5 2m-9-1 4 5 6 1m40-13-3 6-5 2m9-1-4 5-6 1" stroke={color} strokeWidth="2" fill="none"/>}
  </svg>;
}
