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

export default function RankingMedal({ period, rank }) {
  if (!names[period] || !Number.isInteger(rank) || rank < 1 || rank > 3) return null;
  const label = names[period] + places[rank - 1] + '奖牌';
  const grade = (period === 'total' ? 9 : period === 'weekly' ? 6 : 3) - rank + 1;
  return <svg className={`ranking-medal ranking-medal-${period} ranking-medal-${period}-${rank}`}
    viewBox="0 0 40 44" role="img" aria-label={label} data-grade={grade} data-rank={rank}
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
  </svg>;
}
