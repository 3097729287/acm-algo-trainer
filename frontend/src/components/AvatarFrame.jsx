export default function AvatarFrame({index=0}) {
 const tier=Math.max(0,Math.min(9,index));
 return <svg className={`avatar-rank-frame tier-${tier}`} viewBox="0 0 100 100" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
 <path d="M50 14c48-2 49 73 1 74C4 89 3 15 50 14Z"/><path d="M51 18c-43-1-44 65-1 66 44 1 43-67 1-66Z" opacity=".38" strokeWidth="1"/>
 {tier>=1&&<><path d="M23 78C9 69 5 46 15 30M77 78c14-9 18-32 8-48"/>{[0,1,2,3].map(i=><g key={i} transform={`translate(0 ${i*10})`}><path d="M14 32c-10-5-10 5 0 9 7-4 8-10 0-9Zm72 0c10-5 10 5 0 9-7-4-8-10 0-9Z" fill="currentColor" fillOpacity=".1"/></g>)}</>}
 {tier>=3&&<path d="m36 18 1-10 12 6 13-6 2 11M28 81l-5 13 14-5m36-8 4 13-15-5" fill="currentColor" fillOpacity=".1"/>}
 {tier>=4&&<path d="m15 43-10-8 2 14-4 5 12 8m70-19 10-8-2 14 4 5-12 8"/>}
 {tier>=6&&<path d="m40 13 10-10 10 10-10 8Z" fill="currentColor" fillOpacity=".15"/>}
 {tier>=7&&<path d="m26 18-8-11 15 6m41 5 8-11-15 6M18 75 9 83l12-2m61-6 9 8-12-2"/>}
 {tier>=8&&<path d="m36 6-8-4 2 12m34-8 8-4-2 12m-48 47-12 7m78-7 12 7"/>}
 {tier===9&&<path d="m50 0 1 2m-16 88 15 8 15-8m-18 3 3 5 3-5"/>}
 </svg>;
}
