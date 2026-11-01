const names = { daily: '每日过题', weekly: '本周过题', total: '累计过题' };
const places = ['第一名', '第二名', '第三名'];
const ribbons = [
  'M12 13 10 3h7l3 8 3-8h7l-2 10',
  'M14 13 12 4h6l2 7 2-7h6l-2 9',
  'M16 13 14 5h12l-2 8',
];
const weeklyDetails = [
  'M13 33 11 40l9-4 9 4-2-7 M15 10h10',
  'M14 33 13 39l7-3 7 3-1-6 M17 10h6',
  'M16 34 15 38l5-2 5 2-1-4 M18 10h4',
];
const crowns = [
  'M12 11 10 4l6 3 4-5 4 5 6-3-2 7Z',
  'M13 11 12 5l5 3 3-4 3 4 5-3-1 6Z',
  'M15 11 14 7l4 2 2-3 2 3 4-2-1 4Z',
];

export default function RankingMedal({ period, rank, dominance }) {
  const days=rank===1?Math.max(0,Math.min(100000,Math.floor(Number(dominance?.days)||0))):0;
  if (!names[period] || !Number.isInteger(rank) || rank < 1 || rank > 3) return null;
  const label = names[period] + places[rank - 1] + '奖牌';
  const grade = (period === 'total' ? 9 : period === 'weekly' ? 6 : 3) - rank + 1;
  return <svg className={`ranking-medal ranking-medal-${period} ranking-medal-${period}-${rank}`}
    viewBox={days?"0 0 40 60":"0 0 40 44"} data-days={days||undefined} role="img" aria-label={label+(days?` · 连续第一 ${days} 天`:'')} data-grade={grade} data-rank={rank}
    fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
    <title>{label}</title>
    {period === 'daily' && <>
      <path d={ribbons[rank - 1]} className="ranking-medal-detail"/>
      <circle cx="20" cy="25" r="12" className="ranking-medal-face"/>
      <circle cx="20" cy="25" r="8.5" className="ranking-medal-inset"/>
    </>}
    {period === 'weekly' && <>
      <path d={weeklyDetails[rank - 1]} className="ranking-medal-detail"/>
      <path d="M20 7 32 12v10c0 7-4 12-12 16C12 34 8 29 8 22V12Z" className="ranking-medal-face"/>
      <path d="M12 15v7c0 5 3 9 8 12 5-3 8-7 8-12v-7" className="ranking-medal-inset"/>
    </>}
    {period === 'total' && <>
      <path d="M13 11h14l8 8v11l-8 9H13l-8-9V19Z" className="ranking-medal-face"/>
      <circle cx="20" cy="25" r="9" className="ranking-medal-inset"/>
      <path d={crowns[rank - 1]} className="ranking-medal-crown"/>
    </>}
    <text x="20" y={period === 'weekly' ? '26.5' : '29.5'} textAnchor="middle" className="ranking-medal-number">{rank}</text>
    {days>0&&<Dominance days={days}/>}
  </svg>;
}

function Dominance({days}) {
  if(days>=9)return <g className="ranking-dominance" aria-hidden="true"><path d="M10 46h20l-1 10-9 4-9-4Z" fill="currentColor" fillOpacity=".14"/><text x="20" y="55" textAnchor="middle" fontSize={days>=1000?6:8} fontWeight="700" fill="currentColor" stroke="none">{days}</text></g>;
  const crowns=Math.floor(days/3),stars=days%3,items=[...Array(crowns).fill('crown'),...Array(stars).fill('star')],width=items.length*9-1;
  return <g className="ranking-dominance" aria-hidden="true">{items.map((kind,index)=><g key={index} transform={`translate(${20-width/2+index*9} 47)`}>{kind==='crown'?<path d="m0 2 2 2 2-4 2 4 2-2-1 6H1Z" fill="currentColor" fillOpacity=".65" strokeWidth=".7"/>:<path d="m4 0 1.2 2.7L8 3l-2.1 2 0.6 3L4 6.5 1.5 8l.6-3L0 3l2.8-.3Z" fill="currentColor" fillOpacity=".7" strokeWidth=".6"/>}</g>)}</g>;
}
