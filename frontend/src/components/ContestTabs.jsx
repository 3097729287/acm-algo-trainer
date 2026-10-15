export const CONTEST_SHELVES = [
  ['all', '全部比赛'], ['牛客', '牛客'], ['洛谷', '洛谷'],
  ['Codeforces', 'Codeforces'], ['AtCoder', 'AtCoder'],
  ['xcpc', 'XCPC 历年'], ['lanqiao', '蓝桥杯 B 组历年'],
];

export { isXcpc, matchesShelf } from '@/lib/contestShelves.js';

export default function ContestTabs({ value = 'all', onChange, label = '比赛题库分类' }) {
  return <div className="ranking-tabs contest-shelves" role="tablist" aria-label={label}>
    {CONTEST_SHELVES.map(([key, name]) => <button type="button" role="tab" key={key}
      aria-selected={value === key} className={value === key ? 'active' : ''}
      onClick={() => onChange(key)}>{name}</button>)}
  </div>;
}
