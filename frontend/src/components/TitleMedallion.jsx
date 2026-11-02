// Restrained enamel, engraved metal and a thin relief edge; no glossy face.
export default function TitleMedallion({tier,size,variant,label,id}) {
 const silver=variant==='ac',achievementGold=variant==='difficulty',metal=silver?['#e0e2e4','#aab1b9','#57616c']:achievementGold?['#fff1ce','#c1a261','#61523b']:['#e5d5b6','#b29a6e','#6c5839'];
 const enamel=variant==='streak'?['#344d49','#1d302e']:achievementGold?['#e3ce96','#a58b50']:['#344350','#1b2936'];
 const prefix=`engraved-${id}`,gold=`url(#${prefix}-metal)`,face=`url(#${prefix}-face)`;
 const leaves=['M31 92C19 94 13 88 11 80c10 0 16 4 20 12Z','M24 82C12 81 8 75 8 67c10 2 15 7 16 15Z','M20 70C9 66 7 59 9 52c9 4 13 10 11 18Z','M20 57C11 51 11 44 15 37c8 6 9 13 5 20Z','M24 45C18 38 20 31 26 25c5 7 5 14-2 20Z'];
 return <svg className={`medal-emblem medal-engraved tier-${tier} medal-${variant}`} width={size} height={size*1.15} viewBox="0 0 120 138" role={label?'img':undefined} aria-label={label} aria-hidden={label?undefined:true} fill="none">
  <defs>
   <linearGradient id={`${prefix}-metal`} x1="18" y1="20" x2="99" y2="108" gradientUnits="userSpaceOnUse"><stop stopColor={metal[0]}/><stop offset=".38" stopColor={metal[1]}/><stop offset=".58" stopColor={metal[0]}/><stop offset="1" stopColor={metal[2]}/></linearGradient>
   <linearGradient id={`${prefix}-face`} x1="35" y1="28" x2="83" y2="95" gradientUnits="userSpaceOnUse"><stop stopColor={enamel[0]}/>{achievementGold&&<><stop offset=".34" stopColor="#c9ae70"/><stop offset=".48" stopColor="#f1dfae"/><stop offset=".63" stopColor="#c3a667"/></>}<stop offset="1" stopColor={enamel[1]}/></linearGradient>
   <pattern id={`${prefix}-grain`} width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(-28)"><path d="M0 0v4" stroke="#fff" strokeOpacity=".08" strokeWidth=".65"/></pattern>
  </defs>
  <path d="m34 94-4 34 15-10 12 13 5-34M86 94l4 34-15-10-12 13-5-34" fill="#792e3d" stroke="#411d2a" strokeWidth="1.2"/>
  <path d="m37 99-3 20 10-6m39-14 3 20-10-6" stroke="#bb6673" strokeOpacity=".55" strokeWidth="1"/>
  {[false,true].map(mirror=><g key={String(mirror)} transform={mirror?'translate(120 0) scale(-1 1)':undefined}>
   <path d="M39 104C17 92 10 65 23 37" stroke={metal[2]} strokeWidth="3"/>
   <path d="M39 103C18 91 12 65 24 37" stroke={gold} strokeWidth="1.4"/>
   {leaves.map(d=><path key={d} d={d} fill={gold} stroke={metal[2]} strokeWidth=".65"/>)}
  </g>)}
  <circle cx="60" cy="63" r="42" fill="#252731" stroke={metal[2]} strokeWidth="1.5"/>
  <circle cx="60" cy="62" r="40.5" fill={gold}/>
  <circle cx="60" cy="62" r="36.5" fill={face} stroke={metal[2]} strokeWidth="1.1"/>
  <circle cx="60" cy="62" r="37.8" stroke={metal[0]} strokeWidth=".7" strokeOpacity=".9"/>
  <circle cx="60" cy="62" r="34" stroke={metal[1]} strokeWidth=".7" strokeOpacity=".6"/>
  <circle cx="60" cy="62" r="35.5" fill={`url(#${prefix}-grain)`}/>
  <path d="M27 45a39 39 0 0 1 49-19" stroke={metal[0]} strokeWidth="1" strokeLinecap="round" strokeOpacity=".8"/>
  {variant==='streak'?<path d="M61 40c1 10-9 15-8 24 4-1 7-4 8-8 10 10 9 27-2 28-14 1-19-12-12-24-1 8 2 11 4 12-4-12 7-19 10-32Z" fill={gold} stroke={metal[2]} strokeWidth=".8"/>:variant==='difficulty'?<g fill={gold} stroke={metal[2]} strokeWidth=".8"><path d="m60 37 17 10v20L60 84 43 67V47Z"/><path d="m49 64 11-11 11 11M49 72l11-11 11 11" fill="none" stroke="#6b5839" strokeWidth="3" strokeLinejoin="miter"/><path d="m49 62.8 11-11 11 11" fill="none" stroke="#fff0c8" strokeOpacity=".7" strokeWidth=".7"/></g>:<path d="m60 40 6 15 16 7-16 6-6 16-6-16-16-6 16-7Z" fill={gold} stroke={metal[2]} strokeWidth="1"/>}
  {tier>=4&&<path d="m49 21 1-10 10 6 10-6 1 10-11 3Z" fill={gold} stroke={metal[2]} strokeWidth=".8"/>}
  {tier>=7&&<path d="m60 7 3 4-3 4-3-4Z" fill="#8a3345" stroke={metal[1]} strokeWidth=".8"/>}
 </svg>;
}
