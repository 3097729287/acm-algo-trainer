import Tooltip from './Tooltip.jsx';
export const FLAME_STAGES=[1,2,4,7,15,30,60];
// Each stage changes the silhouette, while the SVG keeps the same layout box.
const FLAME_SHAPES=[
 'M17 3C20 10 12 13 16 19C19 18 21 15 21 12C26 17 28 23 25 28C23 32 19 34 16 34C9 34 5 30 6 24C6 20 9 17 11 15C10 20 11 22 13 23C10 15 18 11 17 3Z',
 'M18 2C23 10 15 13 17 19C21 17 23 13 23 10C29 18 29 25 25 30C22 33 19 34 16 34C9 34 4 30 4 25C4 20 8 18 8 13C13 17 10 22 13 23C10 14 20 11 18 2Z',
 'M17 2C24 8 18 13 19 18C23 17 25 13 24 9C30 17 29 26 25 30C22 33 19 34 16 34C8 34 3 30 3 24C3 19 8 17 7 11C13 14 10 20 13 22C10 15 18 12 15 7C18 8 19 9 20 10C20 7 18 5 17 2Z',
 'M17 2C24 7 20 12 20 17C24 16 27 12 26 8C32 17 29 27 25 30C22 33 19 34 16 34C8 34 3 30 3 24C3 20 6 17 4 12C9 14 9 19 12 21C9 14 15 13 12 7C16 8 17 11 16 14C20 11 20 6 17 2Z',
 'M18 2C25 7 21 12 21 17C25 15 28 11 27 8C32 16 27 23 29 25C30 24 30 23 30 22C32 30 24 34 16 34C8 34 1 30 2 24C2 20 5 18 3 13C9 15 8 20 12 22C8 15 14 13 10 7C15 8 17 11 16 15C21 12 21 6 18 2Z',
 'M17 3C25 7 21 12 22 17C26 15 27 12 27 9C32 16 28 21 28 24L31 21C33 29 25 34 16 34C7 34 0 30 1 24L5 27C2 20 6 18 3 12C9 14 8 20 12 22C8 15 14 13 10 7C15 8 17 11 16 15C22 11 19 7 17 3Z',
 'M18 2C26 7 22 12 22 17C26 15 28 12 27 8C33 15 28 20 28 24L31 20C34 28 27 34 16 34C6 34-1 29 1 22L6 26C2 20 6 17 3 11C10 14 8 19 12 21C8 13 14 12 11 6C16 8 17 11 17 15C22 11 22 6 18 2Z',
];

export default function PracticeStreak({days=0,completedToday=false}) {
 const numericDays=Number(days),count=Number.isFinite(numericDays)?Math.max(0,Math.floor(numericDays)):0;
 const stage=Math.max(0,FLAME_STAGES.findLastIndex(value=>count>=value));
 const lit=completedToday===true;
 const today=lit?'今日已通过题目，火焰已点亮':'今日通过一道题即可点亮火焰';
 return <Tooltip text={`连续练习 ${count} 天 · ${today}，按北京时间统计。`}><span className={`practice-streak flame-stage-${stage}${lit?' flame-lit':' flame-unlit'}`} tabIndex={0} aria-label={`连续练习 ${count} 天，${lit?'今日已点亮':'今日待点亮'}`} data-stage={stage+1} data-lit={lit}>
  <svg className="streak-flame" width="24" height="24" viewBox="-1 0 34 36" aria-hidden="true">
   <path className="flame-shell" d={FLAME_SHAPES[stage]}/>
   {lit&&<>
    <path className="flame-body" d="M17 13C20 18 16 20 19 24C21 23 22 21 22 19C26 25 23 32 16 32C10 32 7 28 8 24C9 21 11 20 11 18C15 20 12 24 15 25C13 20 18 18 17 13Z"/>
    <path className="flame-core" d="M17 23C21 27 21 32 16 33C12 33 11 30 12 28C13 26 15 26 17 23Z"/>
    {stage>=4&&<path className="flame-embers" d={stage>=5?'M4 4C7 7 7 10 4 11C2 10 2 8 4 4ZM29 1C32 4 32 6 29 7C27 6 28 3 29 1Z':'M4 4C7 7 7 10 4 11C2 10 2 8 4 4Z'}/>}
   </>}
  </svg><span className="metric-separator" aria-hidden="true">:</span><b>{count}</b>
 </span></Tooltip>;
}
