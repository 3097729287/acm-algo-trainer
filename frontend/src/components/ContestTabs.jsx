import {PLATFORM_REGISTRY,platformNames} from '@/lib/platformRegistry.js';
export const CONTEST_SHELVES = [
  ['all', '全部比赛'], ['牛客', '牛客'], ['洛谷', '洛谷'],
  ['Codeforces', 'CF'], ['AtCoder', 'AC'],
  ['QOJ','QOJ'], ['xcpc', 'XCPC'], ['lanqiao', '蓝桥杯'],
];
export const contestShelvesFor=(rows=[])=>[['all','全部比赛'],...platformNames(rows.length?rows:PLATFORM_REGISTRY.map(platform=>platform.id)).map(platform=>[platform,platform==='Codeforces'?'CF':platform==='AtCoder'?'AC':platform]),['xcpc','XCPC'],['lanqiao','蓝桥杯']];

export { isXcpc, matchesShelf } from '@/lib/contestShelves.js';

export default function ContestTabs({ value = 'all', onChange, rows=[], label = '比赛题库分类' }) {
  return <div className="ranking-tabs contest-shelves" role="tablist" aria-label={label}>
    {contestShelvesFor(rows).map(([key, name]) => <button type="button" role="tab" key={key}
      aria-selected={value === key} className={value === key ? 'active' : ''}
      onClick={() => onChange(key)}>{name}</button>)}
  </div>;
}
