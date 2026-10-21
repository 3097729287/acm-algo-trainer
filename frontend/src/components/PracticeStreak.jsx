import Tooltip from './Tooltip.jsx';
export const FLAME_STAGES=[1,2,4,7,15,30,60];
export default function PracticeStreak({days=0}) {
 const count=Math.max(0,Math.floor(Number(days)||0)),stage=Math.max(0,FLAME_STAGES.findLastIndex(value=>count>=value));
 return <Tooltip text={`连续练习 ${count} 天 · 每天至少完成一次正式提交，按北京时间统计。`}><span className={`practice-streak flame-stage-${stage}${count?'':' flame-inactive'}`} tabIndex={0} aria-label={`连续练习 ${count} 天`} data-stage={stage+1}>
 <svg className="streak-flame sketch-flame" viewBox="0 0 48 56" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M26 5c2 10-4 15-8 20-3-2-3-5-3-9C8 24 5 31 7 40c2 10 9 12 17 12 10 0 17-5 17-15 0-8-6-15-10-18 1 6-1 9-4 11-5-7 4-13-1-25Z" fill="currentColor" fillOpacity=".1"/><path d="M23 32c0 5-7 8-7 13s4 7 8 7 9-3 8-8c-1-3-5-5-5-9-1 4-2 5-4 6" strokeWidth="1.8"/>{stage>=3&&<path d="m8 10-2-4m32 9 3-4"/>}{stage>=5&&<path d="m36 4 1-3M3 24l-2-1"/>}</svg><b>{count}</b></span></Tooltip>;
}
