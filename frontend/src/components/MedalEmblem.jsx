const COLORS=['#9aa4b1','#bd967b','#b6c4d5','#d1b974','#91bdb8','#7fbd9c','#91b9d6','#b3a0d0','#cf9eac','#d8b57d'];
export function titleMedalIndex(title){const targets=title?.category==='streak'?[30,90,180,365,730]:[500,750,1000,1500,2000];return Math.max(0,targets.indexOf(Number(title?.target)))*2+1;}
export default function MedalEmblem({index=0,size=30,variant='rank',label}){
 const tier=Math.max(0,Math.min(9,index)),title=variant!=='rank';
 return <svg className={`medal-emblem sketch-medal tier-${tier} medal-${variant}`} width={size} height={size*1.15} viewBox="0 0 80 92" role={label?'img':undefined} aria-label={label} aria-hidden={label?undefined:true} style={{color:COLORS[tier]}} fill="none" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round">
 <path d="m24 57-5 27 13-7 8 9 5-26m1-2 11 25 5-13 11 2-13-25" fill="currentColor" fillOpacity=".07"/>
 {tier>=3&&<path d="M20 27C6 20 9 44 19 51M60 27c14-7 11 17 1 24M14 32l6 6m-7 2 8 5m45-13-6 6m7 2-8 5"/>}
 <path d={title?'M39 8c7 0 10 5 16 7s12 0 15 7-2 12-1 18 5 11 1 17-11 5-16 9-8 9-15 8-9-7-15-10-13-2-16-9 2-11 1-18-3-10 1-16 11-5 16-9 7-5 13-4Z':'M40 10 65 20l-2 27c-1 14-13 24-24 28C27 69 16 59 15 46l1-26Z'} fill="currentColor" fillOpacity=".055"/>
 <path d={title?'M39 17c30-1 36 45 7 49-38 6-41-48-7-49Z':'m40 18 17 7-1 22c-1 10-9 18-17 22-10-6-17-14-17-24V25Z'} opacity=".5" strokeWidth="1.2"/>
 {variant==='streak'?<path d="M42 28c2 9-7 11-5 20 3 0 6-3 7-7 10 10 7 20-4 20-14 0-17-11-10-21 0 5 3 6 4 7-2-8 7-11 8-19Z" fill="currentColor" fillOpacity=".12"/>:tier%3===0?<path d="m40 29 4 10 11 1-9 7 2 11-9-6-10 5 3-11-8-7 11-1Z" fill="currentColor" fillOpacity=".1"/>:tier%3===1?<><path d="m27 42 9 10 17-23" strokeWidth="3"/><path d="m28 58 23-1" opacity=".5"/></>:<><path d="m28 47 12-19 12 19-12 13Z" fill="currentColor" fillOpacity=".1"/><path d="m40 29 1 30m-12-12h23" opacity=".45"/></>}
 {tier>=5&&<path d="m27 18 1-12 11 8 11-8 2 12M31 7l-1-4m20 3 1-3"/>}
 {tier>=7&&<path d="M15 57C3 51 4 40 7 36m2 11-5-2m8 8-5 1m57 3c12-6 11-17 8-21m-2 11 5-2m-8 8 5 1"/>}
 {tier>=8&&<path d="m40 1 1-1m-36 28-3-1m74 0 2-2"/>}
 </svg>;
}
