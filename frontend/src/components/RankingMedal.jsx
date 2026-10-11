import { useId } from 'react';

const names = { daily: '每日过题', weekly: '本周过题', total: '累计过题' };
const places = ['第一名', '第二名', '第三名'];
const palettes = {
  daily: [['#ffefb0', '#dda438', '#785020'], ['#eaf2ff', '#98aec8', '#526278'], ['#ecc29a', '#b77750', '#68422e']],
  weekly: [['#fff4b7', '#efb84c', '#956222'], ['#f1f4ff', '#acbad9', '#626d91'], ['#f3cbac', '#c38c67', '#855336']],
  total: [['#fffde0', '#ffd46c', '#b48025'], ['#eaffff', '#b2dee4', '#608e99'], ['#ffe3ca', '#d69e78', '#996347']],
};
const star = 'M40 23 44.1 31.4 53.4 32.8 46.7 39.3 48.3 48.5 40 44.2 31.7 48.5 33.3 39.3 26.6 32.8 35.9 31.4Z';

export default function RankingMedal({ period, rank }) {
  const id = useId().replace(/:/g, '');
  if (!palettes[period] || rank < 1 || rank > 3) return null;
  const [shine, metal, edge] = palettes[period][rank - 1];
  const label = names[period] + places[rank - 1] + '奖牌';
  const grade = (period === 'total' ? 9 : period === 'weekly' ? 6 : 3) - rank + 1;
  return <svg className={`ranking-medal ranking-medal-${period} ranking-medal-${period}-${rank}`} viewBox="0 0 80 88" role="img" aria-label={label} data-grade={grade}>
    <title>{label}</title>
    <defs>
      <linearGradient id={`${id}-metal`} x1="0" y1="0" x2="1" y2="1"><stop stopColor={shine}/><stop offset=".32" stopColor={metal}/><stop offset=".52" stopColor={shine}/><stop offset="1" stopColor={edge}/></linearGradient>
      <radialGradient id={`${id}-face`} cx=".35" cy=".22"><stop stopColor={shine}/><stop offset=".65" stopColor={metal}/><stop offset="1" stopColor={edge}/></radialGradient>
    </defs>
    {period === 'daily' && <>
      <path d={rank === 1 ? 'M27 9H38L44 30H32Z M42 9H53L48 30H36Z' : rank === 2 ? 'M29 12H51L47 31H33Z' : 'M32 14H48L45 32H35Z'} fill={rank === 1 ? '#bc6a50' : rank === 2 ? '#6487b3' : '#877568'} stroke={shine} strokeWidth=".7"/>
      <circle cx="40" cy="48" r={rank === 3 ? 22 : 25} fill={`url(#${id}-metal)`} stroke={edge} strokeWidth="1.5"/>
      <circle cx="40" cy="48" r={rank === 3 ? 18 : 21} fill={`url(#${id}-face)`} stroke={shine} strokeWidth="1.1"/>
      {rank === 1 && <g transform="translate(0 10)" fill="none" stroke={shine} strokeWidth="1.2"><path d={star}/><circle cx="40" cy="36" r="16" strokeDasharray="1 3"/></g>}
      {rank === 2 && <path d="M40 29 56 48 40 67 24 48Z" fill="none" stroke={shine} strokeWidth="1.2"/>}
      <text x="40" y="54" textAnchor="middle" fill={edge} fontSize="19" fontWeight="800" fontFamily="Georgia,serif">{rank}</text>
      <path d="M25 38Q29 30 37 28" fill="none" stroke={shine} strokeWidth="2" strokeLinecap="round"/>
    </>}
    {period === 'weekly' && <>
      <path d="M24 48 17 81 30 75 36 83 41 52Z" fill={rank === 1 ? '#6458b4' : rank === 2 ? '#497b9f' : '#97604d'} stroke={shine} strokeWidth=".8"/>
      <path d="M56 48 63 81 50 75 44 83 39 52Z" fill={rank === 1 ? '#8070d0' : rank === 2 ? '#6496b7' : '#b17a61'} stroke={shine} strokeWidth=".8"/>
      <path d={rank === 1 ? 'M40 8 63 21 67 46 51 65 29 65 13 46 17 21Z' : rank === 2 ? 'M28 11H52L66 28V48L52 63H28L14 48V28Z' : 'M40 11 64 23V42Q62 59 40 69 18 59 16 42V23Z'} fill={`url(#${id}-metal)`} stroke={edge} strokeWidth="1.5"/>
      <circle cx="40" cy="37" r="20" fill={`url(#${id}-face)`} stroke={shine} strokeWidth="1.3"/>
      {rank === 1 && <g fill="none" stroke={shine} strokeWidth="1.3"><path d="M31 55Q15 43 23 26M49 55Q65 43 57 26"/><path d="M24 45 19 39M23 39 18 33M24 33 21 27M56 45 61 39M57 39 62 33M56 33 59 27"/><path d={star}/></g>}
      {rank === 2 && <g fill="none" stroke={shine} strokeWidth="1"><circle cx="40" cy="37" r="16" strokeDasharray="2 2"/><path d="M40 20 44 26H36Z M40 54 44 48H36Z"/></g>}
      {rank === 3 && <path d="M28 27H52L48 48 40 54 32 48Z" fill="none" stroke={shine} strokeWidth="1.2"/>}
      <text x="40" y="44" textAnchor="middle" fill={edge} fontSize="20" fontWeight="800" fontFamily="Georgia,serif">{rank}</text>
    </>}
    {period === 'total' && <>
      <path d="M25 56 18 84 31 78 40 85 49 78 62 84 55 56Z" fill={rank === 1 ? '#38497c' : rank === 2 ? '#376c73' : '#683e52'} stroke={metal} strokeWidth="1"/>
      {Array.from({ length: rank === 1 ? 16 : rank === 2 ? 12 : 8 }, (_, i) => <path key={i} d="M40 10 38 23H42Z" transform={`rotate(${i * (rank === 1 ? 22.5 : rank === 2 ? 30 : 45)} 40 43)`} fill={`url(#${id}-metal)`}/>)}
      <g fill={`url(#${id}-metal)`} stroke={edge} strokeWidth=".6">
        <path d="M25 66Q6 56 9 33L14 36Q11 48 17 55L15 43 22 49 19 36 27 44 25 32 32 45Z"/>
        <path d="M55 66Q74 56 71 33L66 36Q69 48 63 55L65 43 58 49 61 36 53 44 55 32 48 45Z"/>
      </g>
      <circle cx="40" cy="44" r="25" fill={`url(#${id}-metal)`} stroke={edge} strokeWidth="1.4"/>
      <circle cx="40" cy="44" r="21" fill={`url(#${id}-face)`} stroke={shine} strokeWidth="1.5"/>
      <circle cx="40" cy="44" r="18" fill="none" stroke={shine} strokeWidth=".8" strokeDasharray={rank === 1 ? '1 2' : rank === 2 ? '3 2' : '6 2'}/>
      <path d={rank === 1 ? 'M24 19 21 8 31 14 40 3 49 14 59 8 56 19Z' : rank === 2 ? 'M26 19 25 10 34 15 40 7 46 15 55 10 54 19Z' : 'M28 21 27 13 35 17 40 10 45 17 53 13 52 21Z'} fill={`url(#${id}-metal)`} stroke={shine} strokeWidth=".9"/>
      <path d="M40 24 43 29 40 34 37 29Z" fill={rank === 1 ? '#6674bb' : rank === 2 ? '#42827e' : '#b65d79'} stroke={shine} strokeWidth=".9"/>
      <text x="40" y="53" textAnchor="middle" fill={edge} fontSize="23" fontWeight="800" fontFamily="Georgia,serif">{rank}</text>
      <path d="M29 60Q40 68 51 60" fill="none" stroke={shine} strokeWidth="1.4"/>
      {rank === 1 && <g fill={shine}><path d="M11 20 13 25 18 27 13 29 11 34 9 29 4 27 9 25Z"/><path d="M68 53 70 57 74 59 70 61 68 65 66 61 62 59 66 57Z"/></g>}
    </>}
  </svg>;
}
