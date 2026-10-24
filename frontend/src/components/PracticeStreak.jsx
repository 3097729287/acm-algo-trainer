import Tooltip from './Tooltip.jsx';
export const FLAME_STAGES=[1,2,4,7,15,30,60];
// Mirror every control point about x=16, including the rounded lower bowl.
// Stages grow in breadth while keeping the same height and optical center.
const FLAME_SHAPES=FLAME_STAGES.map((_,stage)=>{
 const width=9+stage*.65,peak=width-3,notch=3+stage*.15,tipY=14-stage;
 return `M16 2C22 8 21 13 ${16+notch} 18C${16+peak} 17 ${16+peak+1} ${tipY+3} ${16+peak} ${tipY}C${16+width} 16 ${16+width} 19 ${16+width} 22C${16+width} 29 ${16+width*.55} 34 16 34C${16-width*.55} 34 ${16-width} 29 ${16-width} 22C${16-width} 19 ${16-width} 16 ${16-peak} ${tipY}C${16-peak-1} ${tipY+3} ${16-peak} 17 ${16-notch} 18C11 13 10 8 16 2Z`;
});

export default function PracticeStreak({days=0,completedToday=false}) {
 const numericDays=Number(days),count=Number.isFinite(numericDays)?Math.max(0,Math.floor(numericDays)):0;
 const stage=Math.max(0,FLAME_STAGES.findLastIndex(value=>count>=value));
 const lit=completedToday===true;
 const today=lit?'今日已通过题目，火焰已点亮':'今日通过一道题即可点亮火焰';
 return <Tooltip text={`连续练习 ${count} 天 · ${today}，按北京时间统计。`}><span className={`practice-streak flame-stage-${stage}${lit?' flame-lit':' flame-unlit'}`} tabIndex={0} aria-label={`连续练习 ${count} 天，${lit?'今日已点亮':'今日待点亮'}`} data-stage={stage+1} data-lit={lit}>
  <svg className="streak-flame" width="20" height="20" viewBox="-2 0 36 36" aria-hidden="true">
   <path className="flame-shell" d={FLAME_SHAPES[stage]}/>
   {lit&&<>
    <path className="flame-body" d="M16 14C19 19 23 22 23 26C23 30 20 33 16 33C12 33 9 30 9 26C9 22 13 19 16 14Z"/>
    <path className="flame-core" d="M16 23C18 26 20 28 20 30C20 32 18 33 16 33C14 33 12 32 12 30C12 28 14 26 16 23Z"/>
    {stage>=4&&<path className="flame-embers" d={stage>=5?'M4 3Q0 9 4 9Q8 9 4 3ZM28 3Q24 9 28 9Q32 9 28 3Z':'M4 5Q1 9 4 9Q7 9 4 5ZM28 5Q25 9 28 9Q31 9 28 5Z'}/>}
   </>}
  </svg><span className="metric-separator" aria-hidden="true">:</span><b>{count}</b>
 </span></Tooltip>;
}
